import streamlit as st
import google.generativeai as genai
import json
import os
import pandas as pd
from PIL import Image
from datetime import datetime
import plotly.express as px

# ==========================================
# 🎨 UI CONFIGURATION
# ==========================================
st.set_page_config(
    page_title="JanSahayak - Civic Portal", 
    page_icon="🏛️", 
    layout="wide"
)

# ==========================================
# 🔑 SECURITY & SETUP (Cloud + Local)
# ==========================================
# Handles both Local (.env) and Streamlit Cloud (Secrets)
if "GOOGLE_API_KEY" in st.secrets:
    API_KEY = st.secrets["GOOGLE_API_KEY"]
else:
    API_KEY = os.environ.get("GOOGLE_API_KEY")

if not API_KEY:
    st.error("🚨 API Key missing! Add 'GOOGLE_API_KEY' to Streamlit Secrets or Environment Variables.")
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

ISSUE_TYPES = ["Pothole", "Water Leakage", "Streetlight Malfunction", "Garbage Accumulation", "Drainage Block", "Road Damage", "Manhole Issue", "Other"]

# ==========================================
# 🧠 CORE FUNCTIONS
# ==========================================
MEMORY_FILE = "civic_memory.json"

def load_memory():
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r") as f:
                return json.load(f)
        except:
            return []
    return []

def save_memory(history):
    with open(MEMORY_FILE, "w") as f:
        json.dump(history, f, indent=2)

def risk_assessment_tool(damage_type, severity, metadata):
    risk_score = int(severity) * 10
    if metadata.get("near_school"): risk_score += 20
    if metadata.get("heavy_traffic"): risk_score += 15
    if metadata.get("water_leak"): risk_score += 10
    if metadata.get("monsoon_critical"): risk_score += 25
    
    risk_score = min(100, risk_score)
    urgency = "CRITICAL" if risk_score >= 80 else "HIGH" if risk_score >= 50 else "MODERATE"
    return {"risk_index": risk_score, "urgency": urgency}

def analyze_image_with_vision(image, issue_type):
    logs = [f"**[{datetime.now().strftime('%H:%M:%S')}] Agent-V:** Initializing Gemini 2.0 Flash..."]
    
    # 2026 Stable Model Name
    vision_model = genai.GenerativeModel('gemini-2.0-flash') 
    
    vision_prompt = f"""
    Analyze this {issue_type} image. Return ONLY a valid JSON object:
    {{
        "damage_type": "{issue_type}",
        "severity": 1-10,
        "metadata": {{"near_school": bool, "heavy_traffic": bool, "water_leak": bool, "monsoon_critical": bool}},
        "description": "Short assessment"
    }}
    """
    
    try:
        response = vision_model.generate_content([vision_prompt, image])
        # Cleaning response from potential markdown blocks
        clean_text = response.text.replace("```json", "").replace("```", "").strip()
        vision_data = json.loads(clean_text)
        logs.append(f"**Agent-V:** Detected {vision_data['damage_type']} (Sev: {vision_data['severity']})")
        return vision_data, logs
    except Exception as e:
        logs.append(f"**Agent-V:** ❌ Vision Error: {str(e)}")
        return None, logs

def generate_action_plan(vision_data, risk_data, location):
    planner_model = genai.GenerativeModel('gemini-2.0-flash')
    plan_prompt = f"Plan for {vision_data['damage_type']} at {location}. Severity {vision_data['severity']}/10, Risk {risk_data['risk_index']}/100. Give Immediate Actions, Resources, and Budget in INR."
    try:
        response = planner_model.generate_content(plan_prompt)
        return response.text
    except:
        return "Manual assessment required by municipal engineer."

def run_audit_pipeline(image, location, issue_type, citizen_name, citizen_phone):
    vision_data, logs = analyze_image_with_vision(image, issue_type)
    if not vision_data: return None, logs
    
    risk_data = risk_assessment_tool(vision_data['damage_type'], vision_data['severity'], vision_data['metadata'])
    action_plan = generate_action_plan(vision_data, risk_data, location)
    
    complaint_id = f"JAN{datetime.now().strftime('%y%m%d%H%M')}"
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
        "status": "SUBMITTED",
        "status_history": [{"status": "SUBMITTED", "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}]
    }
    
    history = load_memory()
    history.append(record)
    save_memory(history)
    return record, logs

# ==========================================
# 🏠 MAIN APP UI
# ==========================================
with st.sidebar:
    st.title("🏛️ JanSahayak")
    page = st.radio("Navigation", ["🏠 Home", "📝 File Complaint", "📊 Analytics"])
    st.divider()
    st.info(f"Total Database: {len(load_memory())} reports")

if page == "🏠 Home":
    st.header("Welcome to the Citizen Portal")
    st.write("Report civic issues instantly using AI-powered visual analysis.")
    # Show last 3 complaints
    for r in list(reversed(load_memory()))[:3]:
        st.info(f"Report #{r['complaint_id']} - {r['issue_type']} at {r['location']} ({r['status']})")

elif page == "📝 File Complaint":
    st.subheader("New Incident Report")
    with st.form("main_form"):
        c1, c2 = st.columns(2)
        name = c1.text_input("Name")
        phone = c2.text_input("Phone")
        issue = c1.selectbox("Type", ISSUE_TYPES)
        loc = c2.text_input("Specific Location")
        file = st.file_uploader("Upload Evidence", type=['jpg', 'png', 'jpeg'])
        submit = st.form_submit_button("Submit to AI Audit")

    if submit and file:
        with st.spinner("Agents Analyzing..."):
            img = Image.open(file)
            record, logs = run_audit_pipeline(img, loc, issue, name, phone)
            if record:
                st.success(f"Complaint Registered: {record['complaint_id']}")
                st.json(record['risk_data'])
                st.markdown(record['action_plan'])
            else:
                st.error("AI Pipeline failed. See logs below.")
                for l in logs: st.write(l)

elif page == "📊 Analytics":
    data = load_memory()
    if data:
        df = pd.DataFrame(data)
        st.plotly_chart(px.pie(df, names='status', title="Current Resolution Status"))
        st.plotly_chart(px.bar(df, x='issue_type', title="Issues by Category"))
    else:
        st.warning("No data found.")
