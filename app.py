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
# Try Streamlit Secrets first (for cloud deployment), then environment variables
try:
    if "GOOGLE_API_KEY" in st.secrets:
        API_KEY = st.secrets["GOOGLE_API_KEY"]
    else:
        API_KEY = os.environ.get("GOOGLE_API_KEY")
except:
    API_KEY = os.environ.get("GOOGLE_API_KEY")

if not API_KEY:
    st.error("🚨 API Key is missing! Please set GOOGLE_API_KEY in environment variables or Streamlit secrets.")
    st.info("For local: `set GOOGLE_API_KEY=your_key` (Windows) or `export GOOGLE_API_KEY=your_key` (Mac/Linux)")
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
    """AI Vision Analysis"""
    logs = []
    logs.append(log_trace("Agent-V", "Analyzing image with Gemini 2.0 Vision..."))
    
    # Use the correct stable model name
    vision_model = genai.GenerativeModel('gemini-2.0-flash-exp')
    
    vision_prompt = f"""
    Analyze this {issue_type} infrastructure image. Return strictly valid JSON:
    {{
        "damage_type": "string (e.g. pothole, crack, water leak, broken streetlight)",
        "severity": integer (1-10, where 10 is most severe),
        "metadata": {{
            "near_school": boolean,
            "heavy_traffic": boolean,
            "water_leak": boolean,
            "monsoon_critical": boolean
        }},
        "description": "Detailed assessment of the hazard and its impact"
    }}
    """
    
    try:
        response = vision_model.generate_content(
            [vision_prompt, image], 
            generation_config={"response_mime_type": "application/json"}
        )
        vision_data = json.loads(response.text)
        logs.append(log_trace("Agent-V", f"Identified {vision_data['damage_type']} (Severity: {vision_data['severity']}/10)"))
        return vision_data, logs
    except Exception as e:
        logs.append(log_trace("Agent-V", f"❌ Error: {str(e)}"))
        # Return a default structure for demo purposes
        default_data = {
            "damage_type": issue_type.lower(),
            "severity": 5,
            "metadata": {
                "near_school": False,
                "heavy_traffic": False,
                "water_leak": False,
                "monsoon_critical": False
            },
            "description": f"Manual analysis required for {issue_type}"
        }
        return default_data, logs

def generate_action_plan(vision_data, risk_data, context, location):
    """AI Planning Agent"""
    planner_model = genai.GenerativeModel('gemini-2.0-flash-exp')
    plan_prompt = f"""
    You are a City Municipal Engineer in India.
    
    COMPLAINT DETAILS:
    - Issue Type: {vision_data['damage_type']}
    - Severity: {vision_data['severity']}/10
    - Risk Score: {risk_data['risk_index']}/100
    - Urgency: {risk_data['urgency']}
    - Location: {location}
    - Historical Context: {context}
    
    TASK: Provide a technical remediation plan with:
    1. **Immediate Actions** (within 24 hours)
    2. **Required Resources** (materials, team size)
    3. **Estimated Timeline** (hours/days)
    4. **Budget Estimate** (in ₹)
    
    Keep response under 200 words. Be specific and actionable.
    """
    
    try:
        response = planner_model.generate_content(plan_prompt)
        return response.text
    except Exception as e:
        return f"Action plan generation failed: {str(e)}. Manual assessment required."

def run_audit_pipeline(image, location, issue_type, citizen_name, citizen_phone):
    """Main orchestration pipeline"""
    logs = []
    
    # Phase 1: Vision Analysis
    vision_data, vision_logs = analyze_image_with_vision(image, issue_type)
    logs.extend(vision_logs)
    
    if not vision_data:
        return None, logs
    
    # Phase 2: Risk Assessment
    logs.append(log_trace("Risk-Tool", "Calculating safety metrics..."))
    risk_data = risk_assessment_tool(
        vision_data['damage_type'], 
        vision_data['severity'], 
        vision_data['metadata']
    )
    logs.append(log_trace("Risk-Tool", f"Risk Index: {risk_data['risk_index']}/100 - {risk_data['urgency']}"))
    
    # Phase 3: Memory & Context
    logs.append(log_trace("Agent-M", f"Querying memory for '{location}'..."))
    context = get_context_summary(location)
    logs.append(log_trace("Agent-M", context))
    
    # Phase 4: Action Planning
    logs.append(log_trace("Agent-P", "Generating remediation plan..."))
    action_plan = generate_action_plan(vision_data, risk_data, context, location)
    
    # Create complaint record
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
        "status_history": [
            {"status": "SUBMITTED", "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        ],
        "authority_notes": ""
    }
    
    # Save to memory
    history = load_memory()
    history.append(record)
    save_memory(history)
    
    logs.append(log_trace("System", f"✅ Complaint {complaint_id} registered successfully"))
    
    return record, logs

def update_complaint_status(complaint_id, new_status, notes=""):
    """Update complaint status"""
    history = load_memory()
    updated = False
    
    for record in history:
        if record.get('complaint_id') == complaint_id:
            record['status'] = new_status
            record['status_history'].append({
                "status": new_status,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            if notes:
                record['authority_notes'] = notes
            updated = True
            break
    
    if updated:
        save_memory(history)
    return updated

# ==========================================
# 🎨 CUSTOM CSS
# ==========================================
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .complaint-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #667eea;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
    }
    .risk-badge {
        display: inline-block;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: bold;
        font-size: 1.2rem;
    }
    .status-badge {
        display: inline-block;
        padding: 0.3rem 0.8rem;
        border-radius: 15px;
        font-weight: 600;
        font-size: 0.9rem;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 🏠 MAIN APP
# ==========================================

# Sidebar Navigation
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=80)
    st.title("🏛️ JanSahayak")
    st.caption("Smart Civic Complaint System")
    st.divider()
    
    page = st.radio(
        "Navigation",
        ["🏠 Home", "📝 File Complaint", "🔍 Track Complaint", "👮 Authority Dashboard", "📊 Analytics"],
        label_visibility="collapsed"
    )
    
    st.divider()
    st.markdown("### 🎯 System Status")
    st.success("✅ AI Agents Online")
    st.info("🧠 Memory Bank Active")
    
    history = load_memory()
    st.metric("Total Complaints", len(history))

# ==========================================
# PAGE: HOME
# ==========================================
if page == "🏠 Home":
    st.markdown("""
    <div class="main-header">
        <h1>🏛️ Welcome to JanSahayak</h1>
        <p style="font-size: 1.2rem;">Empowering Citizens, Enabling Governance</p>
        <p style="font-size: 0.9rem; opacity: 0.9;">AI-Powered Civic Complaint Management for Smart Cities</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### 📸 Instant Reporting")
        st.write("Take a photo, AI analyzes it in seconds. No forms, no waiting.")
    
    with col2:
        st.markdown("### 🔍 Full Transparency")
        st.write("Track your complaint status in real-time. Get notified on every update.")
    
    with col3:
        st.markdown("### 🎯 Smart Prioritization")
        st.write("AI automatically flags critical issues near schools and high-traffic areas.")
    
    st.divider()
    
    # Recent Activity
    st.markdown("### 📰 Recent Complaints")
    history = load_memory()
    if history:
        recent = sorted(history, key=lambda x: x['timestamp'], reverse=True)[:5]
        for r in recent:
            status_info = COMPLAINT_STATUS[r['status']]
            st.markdown(f"""
            <div class="complaint-card">
                <strong>#{r['complaint_id']}</strong> - {r['issue_type']} at {r['location']}
                <br><span class="status-badge" style="background-color: {status_info['color']}; color: white;">
                {status_info['label']}</span>
                <span style="color: #666; font-size: 0.85rem; float: right;">{r['timestamp']}</span>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No complaints filed yet. Be the first to report!")

# ==========================================
# PAGE: FILE COMPLAINT
# ==========================================
elif page == "📝 File Complaint":
    st.markdown("## 📝 File a New Complaint")
    st.markdown("Help us make your city better! Upload a photo and provide details.")
    
    with st.form("complaint_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            citizen_name = st.text_input("👤 Your Name *", placeholder="e.g. Rahul Sharma")
            citizen_phone = st.text_input("📱 Phone Number *", placeholder="e.g. 9876543210")
        
        with col2:
            issue_type = st.selectbox("🏷️ Issue Type *", ISSUE_TYPES)
            location = st.text_input("📍 Location *", placeholder="e.g. MG Road, Near City Hospital")
        
        uploaded_file = st.file_uploader(
            "📸 Upload Photo of the Issue *", 
            type=['jpg', 'jpeg', 'png'],
            help="Clear photos help us assess the problem faster"
        )
        
        if uploaded_file:
            st.image(uploaded_file, caption="Preview", width=400)
        
        st.markdown("*Required fields")
        submitted = st.form_submit_button("🚀 Submit Complaint", type="primary", use_container_width=True)
    
    if submitted:
        if not citizen_name or not citizen_phone or not location or not uploaded_file:
            st.error("⚠️ Please fill all required fields and upload a photo.")
        else:
            with st.spinner("🤖 AI Agents are analyzing your complaint..."):
                image = Image.open(uploaded_file)
                record, logs = run_audit_pipeline(
                    image, location, issue_type, 
                    citizen_name, citizen_phone
                )
                
                if record:
                    st.success(f"✅ Complaint Registered Successfully!")
                    
                    st.markdown(f"""
                    <div style="background: #d4edda; padding: 1.5rem; border-radius: 10px; border-left: 4px solid #28a745;">
                        <h3 style="margin: 0; color: #155724;">Your Complaint ID: {record['complaint_id']}</h3>
                        <p style="margin: 0.5rem 0 0 0; color: #155724;">
                            📋 Save this ID to track your complaint status<br>
                            📱 You will receive SMS updates on: {citizen_phone}
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.divider()
                    
                    # Show analysis results
                    tab1, tab2, tab3 = st.tabs(["🎯 Risk Assessment", "🛠️ Action Plan", "🕵️ AI Analysis Trace"])
                    
                    with tab1:
                        risk_score = record['risk_data']['risk_index']
                        urgency = record['risk_data']['urgency']
                        
                        if risk_score >= 80:
                            bg_color = "#ffebee"
                            text_color = "#c62828"
                        elif risk_score >= 50:
                            bg_color = "#fff3e0"
                            text_color = "#ef6c00"
                        else:
                            bg_color = "#e8f5e9"
                            text_color = "#2e7d32"
                        
                        st.markdown(f"""
                        <div style="background: {bg_color}; padding: 2rem; border-radius: 10px; text-align: center;">
                            <div style="font-size: 0.9rem; color: #666;">CALCULATED RISK INDEX</div>
                            <div style="font-size: 3rem; font-weight: bold; color: {text_color};">{risk_score}/100</div>
                            <div style="font-size: 1.2rem; font-weight: bold; margin-top: 0.5rem;">
                                PRIORITY: {urgency}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        st.write("")
                        
                        v = record['vision_data']
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("🏷️ Damage Type", v['damage_type'].title())
                            st.metric("⚠️ Severity Level", f"{v['severity']}/10")
                        with col2:
                            st.markdown("**🚨 Risk Factors Detected:**")
                            if v['metadata']['near_school']:
                                st.error("🏫 Near School Zone")
                            if v['metadata']['heavy_traffic']:
                                st.warning("🚗 Heavy Traffic Area")
                            if v['metadata']['water_leak']:
                                st.info("💧 Water Leakage Present")
                            if v['metadata'].get('monsoon_critical'):
                                st.error("🌧️ Monsoon Critical")
                    
                    with tab2:
                        st.markdown("### 👷 Recommended Action Plan")
                        st.info(record['action_plan'])
                        
                        st.markdown("### 📍 Location Context")
                        st.warning(record['context'])
                    
                    with tab3:
                        st.markdown("### 🤖 AI Agent Execution Trace")
                        for log in logs:
                            st.markdown(log)
                else:
                    st.error("❌ Failed to process complaint. Please try again.")
                    with st.expander("View Error Logs"):
                        for log in logs:
                            st.write(log)

# ==========================================
# PAGE: TRACK COMPLAINT
# ==========================================
elif page == "🔍 Track Complaint":
    st.markdown("## 🔍 Track Your Complaint")
    
    complaint_id_input = st.text_input(
        "Enter your Complaint ID",
        placeholder="e.g. PU20241228123456",
        help="You received this ID when you filed the complaint"
    )
    
    if st.button("🔎 Search", type="primary"):
        if complaint_id_input:
            history = load_memory()
            complaint = next((c for c in history if c['complaint_id'] == complaint_id_input), None)
            
            if complaint:
                st.success(f"✅ Complaint Found: #{complaint['complaint_id']}")
                
                # Status Timeline
                st.markdown("### 📊 Status Timeline")
                status_info = COMPLAINT_STATUS[complaint['status']]
                st.markdown(f"""
                <div style="background: {status_info['color']}; padding: 1rem; border-radius: 10px; text-align: center;">
                    <h2 style="color: white; margin: 0;">{status_info['label']}</h2>
                </div>
                """, unsafe_allow_html=True)
                
                st.write("")
                
                # Status History
                for i, status_event in enumerate(reversed(complaint['status_history'])):
                    icon = "🔵" if i == 0 else "⚪"
                    st.markdown(f"{icon} **{COMPLAINT_STATUS[status_event['status']]['label']}** - {status_event['timestamp']}")
                
                st.divider()
                
                # Complaint Details
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("### 📋 Complaint Details")
                    st.write(f"**Filed By:** {complaint['citizen_name']}")
                    st.write(f"**Phone:** {complaint['citizen_phone']}")
                    st.write(f"**Location:** {complaint['location']}")
                    st.write(f"**Issue Type:** {complaint['issue_type']}")
                    st.write(f"**Filed On:** {complaint['timestamp']}")
                
                with col2:
                    st.markdown("### 🎯 Risk Assessment")
                    st.write(f"**Risk Score:** {complaint['risk_data']['risk_index']}/100")
                    st.write(f"**Urgency:** {complaint['risk_data']['urgency']}")
                    st.write(f"**Severity:** {complaint['vision_data']['severity']}/10")
                
                if complaint.get('authority_notes'):
                    st.markdown("### 💬 Authority Response")
                    st.info(complaint['authority_notes'])
                
                st.markdown("### 🛠️ Recommended Action Plan")
                st.write(complaint['action_plan'])
                
            else:
                st.error("❌ Complaint ID not found. Please check and try again.")
        else:
            st.warning("⚠️ Please enter a Complaint ID")

# ==========================================
# PAGE: AUTHORITY DASHBOARD
# ==========================================
elif page == "👮 Authority Dashboard":
    st.markdown("## 👮 Authority Control Panel")
    st.caption("Manage and resolve citizen complaints")
    
    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        status_filter = st.selectbox("Filter by Status", ["All"] + list(COMPLAINT_STATUS.keys()))
    with col2:
        urgency_filter = st.selectbox("Filter by Urgency", ["All", "CRITICAL", "HIGH", "MODERATE"])
    with col3:
        sort_by = st.selectbox("Sort by", ["Newest First", "Highest Risk", "Oldest First"])
    
    st.divider()
    
    history = load_memory()
    
    # Apply filters
    filtered = history
    if status_filter != "All":
        filtered = [c for c in filtered if c['status'] == status_filter]
    if urgency_filter != "All":
        filtered = [c for c in filtered if c['risk_data']['urgency'] == urgency_filter]
    
    # Apply sorting
    if sort_by == "Newest First":
        filtered = sorted(filtered, key=lambda x: x['timestamp'], reverse=True)
    elif sort_by == "Highest Risk":
        filtered = sorted(filtered, key=lambda x: x['risk_data']['risk_index'], reverse=True)
    else:
        filtered = sorted(filtered, key=lambda x: x['timestamp'])
    
    st.markdown(f"### 📋 Showing {len(filtered)} Complaint(s)")
    
    for complaint in filtered:
        with st.expander(
            f"🆔 {complaint['complaint_id']} | {complaint['issue_type']} | "
            f"Risk: {complaint['risk_data']['risk_index']} | "
            f"{COMPLAINT_STATUS[complaint['status']]['label']}"
        ):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown("#### 📍 Location & Details")
                st.write(f"**Location:** {complaint['location']}")
                st.write(f"**Citizen:** {complaint['citizen_name']} ({complaint['citizen_phone']})")
                st.write(f"**Filed On:** {complaint['timestamp']}")
                st.write(f"**Issue:** {complaint['vision_data']['damage_type']}")
                st.write(f"**Description:** {complaint['vision_data']['description']}")
                
                st.markdown("#### 🛠️ Action Plan")
                st.info(complaint['action_plan'])
            
            with col2:
                st.markdown("#### 🎯 Risk Metrics")
                st.metric("Risk Score", f"{complaint['risk_data']['risk_index']}/100")
                st.metric("Severity", f"{complaint['vision_data']['severity']}/10")
                st.metric("Urgency", complaint['risk_data']['urgency'])
                
                # Risk factors
                st.markdown("**⚠️ Risk Factors:**")
                meta = complaint['vision_data']['metadata']
                if meta.get('near_school'): st.write("🏫 Near School")
                if meta.get('heavy_traffic'): st.write("🚗 Heavy Traffic")
                if meta.get('water_leak'): st.write("💧 Water Leak")
                if meta.get('monsoon_critical'): st.write("🌧️ Monsoon Risk")
            
            st.divider()
            
            # Status Update Section
            st.markdown("#### 🔄 Update Status")
            new_status = st.selectbox(
                "Change Status",
                list(COMPLAINT_STATUS.keys()),
                index=list(COMPLAINT_STATUS.keys()).index(complaint['status']),
                key=f"status_{complaint['complaint_id']}"
            )
            
            authority_notes = st.text_area(
                "Authority Notes / Response",
                value=complaint.get('authority_notes', ''),
                placeholder="Add notes for the citizen...",
                key=f"notes_{complaint['complaint_id']}"
            )
            
            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("💾 Update Complaint", key=f"update_{complaint['complaint_id']}", type="primary"):
                    if update_complaint_status(complaint['complaint_id'], new_status, authority_notes):
                        st.success(f"✅ Updated to {COMPLAINT_STATUS[new_status]['label']}")
                        st.rerun()
            
            with col_b:
                if complaint['status'] != 'RESOLVED':
                    if st.button("✅ Mark Resolved", key=f"resolve_{complaint['complaint_id']}", type="secondary"):
                        if update_complaint_status(complaint['complaint_id'], 'RESOLVED', authority_notes):
                            st.success("🎉 Complaint marked as RESOLVED!")
                            st.rerun()

# ==========================================
# PAGE: ANALYTICS
# ==========================================
elif page == "📊 Analytics":
    st.markdown("## 📊 System Analytics & Insights")
    
    history = load_memory()
    
    if not history:
        st.info("📭 No data available yet. File some complaints to see analytics!")
    else:
        # Top Metrics
        col1, col2, col3, col4 = st.columns(4)
        
        total = len(history)
        resolved = len([h for h in history if h['status'] == 'RESOLVED'])
        pending = len([h for h in history if h['status'] in ['SUBMITTED', 'ACKNOWLEDGED', 'IN_PROGRESS']])
        critical = len([h for h in history if h['risk_data']['urgency'] == 'CRITICAL'])
        
        with col1:
            st.metric("📋 Total Complaints", total)
        with col2:
            st.metric("✅ Resolved", resolved, delta=f"{(resolved/total*100):.1f}%")
        with col3:
            st.metric("⏳ Pending", pending)
        with col4:
            st.metric("🚨 Critical", critical)
        
        st.divider()
        
        # Charts
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📊 Status Distribution")
            status_counts = pd.DataFrame(history)['status'].value_counts()
            fig = px.pie(
                values=status_counts.values,
                names=[COMPLAINT_STATUS[s]['label'] for s in status_counts.index],
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown("### 🏷️ Issue Type Breakdown")
            issue_counts = pd.DataFrame(history)['issue_type'].value_counts()
            fig = px.bar(
                x=issue_counts.values,
                y=issue_counts.index,
                orientation='h',
                color=issue_counts.values,
                color_continuous_scale='Reds'
            )
            fig.update_layout(showlegend=False, xaxis_title="Count", yaxis_title="Issue Type")
            st.plotly_chart(fig, use_container_width=True)
        
        st.divider()
        
        # Location Analysis
        st.markdown("### 📍 Complaint Hotspots")
        location_counts = pd.DataFrame
