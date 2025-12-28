# 🏛️ JanSahayak - Smart Civic Complaint System

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](YOUR_DEPLOYED_LINK_HERE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **AI-Powered Civic Complaint Management for Smart Cities**  
> Submitted for **PU Hackathon 3.0** - Track: Civic Issue Reporting & Management

---

## 🎥 Live Demo

### [🚀 **Try the App Live**](YOUR_DEPLOYED_LINK_HERE)

### [📹 **Watch Video Walkthrough**](YOUR_YOUTUBE_LINK_HERE)

---

## 📋 Table of Contents

- [Problem Statement](#-problem-statement)
- [Our Solution](#-our-solution)
- [Key Features](#-key-features)
- [Architecture](#-architecture)
- [Tech Stack](#-tech-stack)
- [Installation](#-installation)
- [Usage](#-usage)
- [Screenshots](#-screenshots)
- [Team](#-team)

---

## 🎯 Problem Statement

### The Challenge

India receives **1.5 crore civic complaints yearly**—potholes, water leaks, streetlights—but resolves only **30%**. 

**Key Issues:**
- ❌ Citizens waste hours on call centers with no follow-up
- ❌ Issues escalate: **12,000+ pothole deaths** annually
- ❌ **25% water wastage** due to unreported leaks
- ❌ Small towns suffer most: **40% complaints remain verbal and forgotten**
- ❌ Monsoon drainage blocks cause **80% flooding**
- ❌ Opacity costs **₹50,000 crore annually** in damages
- ❌ Erodes **70% citizen trust** in governance

### Key Obstacles
1. **Absence** of instant, location-based reporting mechanisms
2. **Poor tracking** of issue resolution status
3. **Lack of communication** between citizens and authorities

---

## 💡 Our Solution

**JanSahayak** is an AI-powered civic complaint management system that transforms a single photo into a **quantified risk assessment** and actionable repair plan.

### Why AI Agents?

A standard script can detect a pothole, but it cannot:
- ❌ Reason about budget constraints
- ❌ Remember context from previous complaints
- ❌ Prioritize based on environmental factors

Our **Multi-Agent Architecture** separates:
- 👁️ **Observation** (Vision Agent)
- 🧮 **Logic** (Risk Assessment Tool)
- 🧠 **Memory** (Context Agent)
- 👷 **Reasoning** (Planning Agent)

This prevents hallucinations and ensures **safety-critical accuracy**.

---

## ✨ Key Features

### 🚀 For Citizens

| Feature | Description |
|---------|-------------|
| 📸 **Instant Reporting** | Upload photo → AI analysis → Complaint ID in <30 seconds |
| 🔍 **Real-time Tracking** | Track complaint status with unique ID |
| 📱 **SMS Notifications** | Get updates on every status change |
| 🗺️ **Location-Based** | GPS-powered location capture |
| 🌐 **Transparent** | Full visibility into complaint lifecycle |

### 👮 For Authorities

| Feature | Description |
|---------|-------------|
| 📊 **Smart Dashboard** | Filter by status, urgency, risk score |
| ⚡ **Priority Queue** | AI-ranked complaints by risk index |
| 🛠️ **Action Plans** | Auto-generated technical remediation plans |
| 💬 **Citizen Communication** | Add notes and responses |
| 📈 **Analytics** | Hotspot detection, trend analysis |

### 🤖 AI Capabilities

| Agent | Function |
|-------|----------|
| 👁️ **Agent-V** | Computer vision analysis (Gemini 2.0) |
| 🧮 **Risk Tool** | Deterministic safety scoring |
| 🧠 **Agent-M** | Memory & recurring issue detection |
| 👷 **Agent-P** | Technical planning & budget estimation |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    CITIZEN INTERFACE                        │
│  📸 Upload Photo + Location → Instant Complaint ID          │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              MULTI-AGENT ORCHESTRATION                      │
│                                                             │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐             │
│  │ Agent-V  │ -> │ Risk Tool│ -> │ Agent-M  │             │
│  │ (Vision) │    │ (Logic)  │    │ (Memory) │             │
│  └──────────┘    └──────────┘    └──────────┘             │
│                                        │                    │
│                                        ▼                    │
│                                  ┌──────────┐              │
│                                  │ Agent-P  │              │
│                                  │(Planner) │              │
│                                  └──────────┘              │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                   PERSISTENT STORAGE                        │
│  📁 civic_memory.json - Long-term complaint database        │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│               AUTHORITY DASHBOARD                           │
│  👮 Manage → Update Status → Resolve → Notify               │
└─────────────────────────────────────────────────────────────┘
```

### 🔄 Workflow

1. **Citizen Uploads Photo** → Location + Issue Type
2. **Agent-V (Vision)** → Analyzes image with Gemini 2.0
   - Extracts: Damage type, Severity (1-10), Risk factors
3. **Risk Tool** → Calculates Risk Index (0-100)
   - Factors: Near school (+20), Heavy traffic (+15), Water leak (+10), Monsoon (+25)
4. **Agent-M (Memory)** → Checks for recurring issues at location
5. **Agent-P (Planner)** → Generates:
   - Immediate actions
   - Required resources
   - Timeline & budget estimate
6. **Complaint Registered** → Unique ID + SMS notification
7. **Authority Reviews** → Updates status → Citizen notified

---

## 🛠️ Tech Stack

### Frontend
- **Streamlit** - Interactive web interface
- **Plotly** - Data visualization & charts

### AI & ML
- **Google Gemini 2.0 Flash** - Vision & planning models
- **Custom Risk Engine** - Deterministic safety scoring
- **Multi-Agent Orchestration** - Sequential pipeline

### Backend
- **Python 3.10+** - Core application
- **JSON Database** - Persistent storage (civic_memory.json)
- **Pandas** - Data processing & analytics

### Deployment
- **Streamlit Cloud** / **Hugging Face Spaces** - Free hosting
- **Git** - Version control

---

## 📦 Installation

### Prerequisites
- Python 3.10 or higher
- Google Gemini API Key ([Get it here](https://aistudio.google.com/))
- Git

### Steps

1. **Clone the repository**
   ```bash
   git clone https://github.com/YOUR_USERNAME/jansahayak.git
   cd jansahayak
   ```

2. **Create virtual environment**
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate

   # Mac/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up API key**
   
   Create a `.env` file in the project root:
   ```env
   GOOGLE_API_KEY=your_api_key_here
   ```

   Or set environment variable:
   ```bash
   # Windows CMD
   set GOOGLE_API_KEY=your_api_key_here

   # Mac/Linux
   export GOOGLE_API_KEY="your_api_key_here"
   ```

5. **Run the application**
   ```bash
   streamlit run app.py
   ```

6. **Open in browser**
   ```
   Local URL: http://localhost:8501
   ```

---

## 🎮 Usage

### For Citizens

1. **Navigate to "File Complaint"**
2. Fill in:
   - Name
   - Phone number
   - Location
   - Issue type
3. **Upload a photo** of the issue
4. Click **"Submit Complaint"**
5. **Save your Complaint ID** for tracking

### For Tracking

1. Go to **"Track Complaint"**
2. Enter your **Complaint ID**
3. View:
   - Current status
   - Status history
   - Risk assessment
   - Action plan
   - Authority responses

### For Authorities

1. Access **"Authority Dashboard"**
2. **Filter** complaints by:
   - Status (Submitted, In Progress, Resolved)
   - Urgency (Critical, High, Moderate)
   - Risk score
3. **Review** complaint details
4. **Update status** and add notes
5. **Mark as resolved** when fixed

### Analytics

- View **overall statistics**
- Analyze **complaint hotspots**
- Track **resolution rates**
- Monitor **risk distribution**

---

## 📸 Screenshots

### Home Page
![Home Page](screenshots/home.png)
*AI-powered civic complaint portal landing page*

### File Complaint
![File Complaint](screenshots/file_complaint.png)
*Simple form with photo upload and instant AI analysis*

### Risk Assessment
![Risk Assessment](screenshots/risk_assessment.png)
*AI-calculated risk index with priority classification*

### Complaint Tracking
![Track Complaint](screenshots/track.png)
*Real-time status updates with full transparency*

### Authority Dashboard
![Authority Dashboard](screenshots/authority.png)
*Manage and resolve complaints with smart filtering*

### Analytics
![Analytics](screenshots/analytics.png)
*Insights, hotspots, and performance metrics*

---

## 🎯 Hackathon Scoring Criteria

### ✅ How We Address the Problem

| Challenge | Our Solution |
|-----------|--------------|
| Instant reporting | Photo → AI → ID in <30 sec |
| Location-based | GPS integration + memory system |
| Poor tracking | Real-time status + SMS notifications |
| No communication | Authority dashboard + citizen notes |
| Recurring issues | Memory agent detects patterns |
| Prioritization | AI risk scoring (0-100) |
| Transparency | Full audit trail + analytics |

### 🏆 Innovation Points

1. **Multi-Agent AI** - Not just detection, but reasoning
2. **Memory System** - Learns from historical data
3. **Deterministic Risk** - No hallucinations in safety scoring
4. **Context Engineering** - Efficient token usage
5. **Observability** - Live agent trace logs

---

## 📊 Impact Metrics

### Problem Scale
- 📈 1.5 crore complaints/year in India
- ❌ Only 30% resolution rate
- 💀 12,000+ pothole-related deaths
- 💧 25% water wastage
- 💰 ₹50,000 crore in damages
- 😞 70% loss in citizen trust

### Our Solution Impact
- ⚡ **<30 second** complaint registration
- 🎯 **100%** transparency in tracking
- 🤖 **Automated** priority classification
- 🧠 **Intelligent** recurring issue detection
- 📊 **Data-driven** governance decisions

---

## 🚀 Future Enhancements

- [ ] **Mobile App** (Android/iOS)
- [ ] **Multilingual Support** (Hindi, Regional languages)
- [ ] **Voice Complaints** (for illiterate citizens)
- [ ] **WhatsApp Integration** (for SMS notifications)
- [ ] **Map Visualization** (hotspot heatmaps)
- [ ] **Blockchain** (tamper-proof audit trail)
- [ ] **Predictive Maintenance** (AI forecasts issues)
- [ ] **Citizen Rewards** (gamification for active reporters)

---

## 👥 Team

**Team Name:** [Obsidian Ops]

| Name | Role | GitHub |
|------|------|--------|
| [Shreyas Patankar] | [@username](https://github.com/username) |
| [Aditya Thakur] | [@username](https://github.com/username) |
| [Dheeraj Mowal] |  [@username](https://github.com/username) |

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **PU Hackathon 3.0** - For the problem statement and platform
- **Google Gemini AI** - For powerful vision and reasoning models
- **Streamlit** - For the amazing web framework
- **Open Source Community** - For the tools and libraries

---

## 📞 Contact

For queries or suggestions:
- 📧 Email: shreyaspatankar300@gmail.com
- 💼 LinkedIn: [Your Name](www.linkedin.com/in/shreyas-patankar-b4585a341)
---

## ⭐ Support

If you like this project, please give it a ⭐ on GitHub!

**Made with ❤️ for PU Hackathon 3.0**

---

<div align="center">

### 🏛️ JanSahayak - Empowering Citizens, Enabling Governance

**[Live Demo](YOUR_DEPLOYED_LINK_HERE)** • **[Video](YOUR_YOUTUBE_LINK_HERE)** • **[Report Bug](https://github.com/YOUR_USERNAME/jansahayak/issues)**

</div>
