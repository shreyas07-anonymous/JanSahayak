import streamlit as st
import google.generativeai as genai
import json
import os
import pandas as pd
from PIL import Image
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go

# ==========================================
# 🎨 UI CONFIGURATION
# ==========================================
st.set_page_config(
    page_title="JanSahayak - Civic Complaint Portal", 
    page_icon="🏛️", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# 🔑 SECURITY & SETUP
# ==========================================
if "GOOGLE_API_KEY" in st.secrets:
    API_KEY = st.secrets["GOOGLE_API_KEY"]
else:
    API_KEY = os.environ.get("GOOGLE_API_KEY")

if not API_KEY:
    st.error("🚨 API Key is missing! Please set GOOGLE_API_KEY in Streamlit Secrets or environment variables.")
    st.stop()

genai.configure(api_key=API_KEY)

# ==========================================
# 📊 CONSTANTS
# ==========================================
COMPLAINT_STATUS = {
    "SUBMITTED": {"label": "🟡 Submitted", "color": "#FFA500"},
    "ACKNOWLEDGED": {"label": "🔵 Acknowledged", "color": "#4169E1"},
    "IN_PROGRESS": {"label": "🟠 In Progress", "color": "#FF6347"},
    "RESOLVED": {"label": "🟢 Resolved", "color": "#32CD32"},
    "REJECTED": {"label": "🔴 Rejected", "color": "#DC143C"}
}

ISSUE_TYPES = [
    "Pothole", 
    "Water Leakage", 
    "Streetlight Malfunction",
    "Garbage Accumulation",
    "Drainage Block",
    "Road Damage",
    "Manhole Issue",
    "Other"
]

# ==========================================
# 🧠 CORE FUNCTIONS
# ==========================================
MEMORY_FILE = "civic_memory.json"

def load_memory():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r") as f:
            try:
                return json.load(f)
            except:
                return []
    return []

def save_memory(history):
    with open(MEMORY_FILE, "w") as f:
        json.dump(history, f, indent=2)

def generate_complaint_id():
    return f"PU{datetime.now().strftime('%Y%m%d%H%M%S')}"

def log_trace(agent_name, action):
    timestamp = datetime.now().strftime("%H:%M:%S")
    return f"**[{timestamp}] {agent_name}:** {action}"

def risk_assessment_tool(damage_type, severity, metadata):
    """Deterministic risk calculation"""
    risk_score = int(severity) * 10
    
    if metadata.get("near_school"): risk_score += 20
    if metadata.get("heavy_traffic"): risk_score += 15
    if metadata.get("water_leak"): risk_score += 10
    if metadata.get("monsoon_critical"): risk_score += 25
    
    risk_score = min(100, risk_score)
    
    if risk_score >= 80: urgency = "CRITICAL"
    elif risk_score >= 50: urgency = "HIGH"
    else: urgency = "MODERATE"
    
    return {"risk_index": risk_score, "urgency": urgency}

def get_context_summary(location):
    history = load_memory()
    relevant = [r for r in history if r['location'].lower() == location.lower()]
    if not relevant: 
        return "No prior incidents at this location."
    
    unresolved = [r for r in relevant if r.get('status') != 'RESOLVED']
    if unresolved:
        return f"⚠️ RECURRING ISSUE: {len(unresolved)} unresolved complaints at this location. Last severity: {relevant[-1]['vision_data']['severity']}/10."
    return f"History: {len(relevant)} prior reports. All resolved."

def analyze_image_with_vision(image, issue_type):
    """AI Vision Analysis with JSON cleaning"""
    logs = []
    logs.append(log_trace("Agent-V", "Analyzing image with Gemini 2.0 Flash..."))
    
    vision_model = genai.GenerativeModel('gemini-2.0-flash')
    vision_prompt = f"""
    Analyze this {issue_type} infrastructure image. Return strictly valid JSON:
    {{
        "damage_type": "string (pothole, crack, water leak, etc.)",
        "severity": integer (1-10),
        "metadata": {{
            "near_school": boolean,
            "heavy_traffic": boolean,
            "water_leak": boolean,
            "monsoon_critical": boolean
        }},
        "description": "Assessment of hazard"
    }}
    """
    
    try:
        response = vision_model.generate_content([vision_prompt, image])
        # Clean response to ensure valid JSON parsing
        res_text = response.text.replace("```json", "").replace("```", "").strip()
        vision_data = json.loads(res_text)
        logs.append(log_trace("Agent-V", f"Identified {vision_data['damage_type']} (Severity: {vision_data['severity']}/10)"))
        return vision_data, logs
    except Exception as e:
        logs.append(log_trace("Agent-V", f"❌ Error: {str(e)}"))
        return None, logs

def generate_action_plan(vision_data, risk_data, context, location):
    """AI Planning Agent"""
    planner_model = genai.GenerativeModel('gemini-2.0-flash')
    plan_prompt = f"""
    You are a City Municipal Engineer. Issue: {vision_data['damage_type']}, Sev: {vision_data['severity']}, Risk: {risk_data['risk_index']}.
    Location: {location}. Context: {context}.
    Provide Immediate Actions, Resources, Timeline, and Budget Estimate (₹). Under 200 words.
    """
    try:
        response = planner_model.generate_content(plan_prompt)
        return response.text
    except Exception as e:
        return f"Error generating plan: {str(e)}"

def run_audit_pipeline(image, location, issue_type, citizen_name, citizen_phone):
    logs = []
    
    # Vision Analysis
    vision_data, vision_logs = analyze_image_with_vision(image, issue_type)
    logs.extend(vision_logs)
    if not vision_data: return None, logs
    
    # Risk Assessment
    logs.append(log_trace("Risk-Tool", "Calculating safety metrics..."))
    risk_data = risk_assessment_tool(vision_data['damage_type'], vision_data['severity'], vision_data['metadata'])
    
    # Memory Context
    logs.append(log_trace("Agent-M", f"Checking history for '{location}'..."))
    context = get_context_summary(location)
    
    # Action Planning
    logs.append(log_trace("Agent-P", "Generating remediation plan..."))
    action_plan = generate_action_plan(vision_data, risk_data, context, location)
    
    complaint_id = generate_complaint_id()
    record = {
        "complaint_id": complaint_id,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "location": location,
        "issue_type": issue_type,
        "citizen_name": citizen_name,
        "citizen_phone": citizen_phone,
        "vision_data": vision_data,
        "risk_data": risk_data,
        "action_plan": action_plan,
        "context": context,
        "status": "SUBMITTED",
        "status_history": [{"status": "SUBMITTED", "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}],
        "authority_notes": ""
    }
    
    history = load_memory()
    history.append(record)
    save_memory(history)
    logs.append(log_trace("System", f"✅ Complaint {complaint_id} registered."))
    
    return record, logs

def update_complaint_status(complaint_id, new_status, notes=""):
    history = load_memory()
    updated = False
    for record in history:
        if record.get('complaint_id') == complaint_id:
            record['status'] = new_status
            record['status_history'].append({"status": new_status, "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
            if notes: record['authority_notes'] = notes
            updated = True
            break
    if updated: save_memory(history)
    return updated

# ==========================================
# 🎨 CUSTOM CSS
# ==========================================
st.markdown("""
<style>
    .main-header { background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); padding: 2rem; border-radius: 10px; color: white; text-align: center; margin-bottom: 2rem; }
    .complaint-card { background: white; padding: 1.5rem; border-radius: 10px; border-left: 4px solid #1e3c72; box-shadow: 0 2px 8px rgba(0,0,0,0.1); margin-bottom: 1rem; color: black; }
    .status-badge { display: inline-block; padding: 0.3rem 0.8rem; border-radius: 15px; font-weight: 600; font-size: 0.8rem; color: white; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 🏠 NAVIGATION
# ==========================================
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=80)
    st.title("🏛️ JanSahayak")
    page = st.radio("Nav", ["🏠 Home", "📝 File Complaint", "🔍 Track Complaint", "👮 Authority Dashboard", "📊 Analytics"], label_visibility="collapsed")
    st.divider()
    st.success("✅ AI Agents Online")
    st.info("🧠 Memory Bank Active")
    st.metric("Total Complaints", len(load_memory()))

# ==========================================
# PAGES
# ==========================================

if page == "🏠 Home":
    st.markdown('<div class="main-header"><h1>🏛️ JanSahayak</h1><p>Smart Civic Complaint Management System</p></div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    col1.metric("Response Time", "2.4 Hours")
    col2.metric("Resolution Rate", "89%")
    col3.metric("Critical Alerts", "4")
    
    st.markdown("### 📰 Recent Reports")
    history = load_memory()
    if history:
        for r in list(reversed(history))[:5]:
            s = COMPLAINT_STATUS[r['status']]
            st.markdown(f'<div class="complaint-card"><b>{r["complaint_id"]}</b> - {r["issue_type"]} at {r["location"]} <span class="status-badge" style="background:{s["color"]}">{s["label"]}</span></div>', unsafe_allow_html=True)
    else: st.info("No reports yet.")

elif page == "📝 File Complaint":
    st.markdown("## 📝 Submit Incident")
    with st.form("c_form"):
        c1, c2 = st.columns(2)
        name = c1.text_input("Name")
        phone = c2.text_input("Phone")
        issue = c1.selectbox("Issue", ISSUE_TYPES)
        loc = c2.text_input("Location")
        file = st.file_uploader("Evidence", type=['jpg','png','jpeg'])
        submit = st.form_submit_button("🚀 Submit Complaint", type="primary")

    if submit and file:
        with st.spinner("AI Agents Analyzing..."):
            img = Image.open(file)
            record, logs = run_audit_pipeline(img, loc, issue, name, phone)
            if record:
                st.success(f"Registered! ID: {record['complaint_id']}")
                st.json(record['risk_data'])
                st.write(record['action_plan'])
                with st.expander("AI Trace"):
                    for l in logs: st.markdown(l)
            else: st.error("Processing failed. Please try again.")

elif page == "🔍 Track Complaint":
    st.header("🔍 Track Status")
    cid = st.text_input("Enter Complaint ID")
    if st.button("Search") and cid:
        comp = next((c for c in load_memory() if c['complaint_id'] == cid), None)
        if comp:
            st.markdown(f"### Status: {COMPLAINT_STATUS[comp['status']]['label']}")
            st.info(comp['action_plan'])
        else: st.error("Not found.")

elif page == "👮 Authority Dashboard":
    st.header("👮 Management Console")
    history = load_memory()
    for c in list(reversed(history)):
        with st.expander(f"ID: {c['complaint_id']} | {c['issue_type']} | Risk: {c['risk_data']['risk_index']}"):
            st.write(f"Citizen: {c['citizen_name']} ({c['citizen_phone']})")
            st.write(f"Location: {c['location']}")
            new_s = st.selectbox("Status", list(COMPLAINT_STATUS.keys()), key=c['complaint_id'])
            notes = st.text_area("Notes", key="n"+c['complaint_id'])
            if st.button("Update", key="b"+c['complaint_id']):
                update_complaint_status(c['complaint_id'], new_s, notes)
                st.rerun()

elif page == "📊 Analytics":
    st.header("📊 Insights")
    data = load_memory()
    if data:
        df = pd.DataFrame(data)
        st.plotly_chart(px.pie(df, names='status', title="Status Dist."))
        st.plotly_chart(px.bar(df, x='issue_type', title="Category Dist."))
    else: st.warning("No data.")
