import streamlit as st
import pandas as pd
import numpy as np
from utils.model_loader import load_model_with_fallback
from utils.predict import predict_6g_5_1, predict_6g_5_2

# Page config
st.set_page_config(
    page_title="Network Slicing Intelligence — 5G & 6G SLA Management Platform",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for 5G/6G color scheme
st.markdown("""
<style>
    .badge-6g {
        background-color: #7C3AED;
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 0.5rem;
        font-size: 0.875rem;
        font-weight: 500;
    }
    .badge-5g {
        background-color: #14B8A6;
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 0.5rem;
        font-size: 0.875rem;
        font-weight: 500;
    }
    .card-6g {
        border-left: 4px solid #7C3AED;
        padding: 1rem;
        margin: 0.5rem 0;
        background-color: #FAF5FF;
    }
    .card-5g {
        border-left: 4px solid #14B8A6;
        padding: 1rem;
        margin: 0.5rem 0;
        background-color: #F0FDFA;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.title("🌐 Network Slicing Intelligence — 5G & 6G SLA Management Platform")
st.markdown("""
Welcome to the Network Slicing Intelligence platform, a comprehensive MLOps solution for managing 
SLA compliance across both 5G and 6G networks. This platform provides real-time predictions 
for network congestion, QoS probability, and other critical metrics to help network operators 
make informed decisions about resource allocation and traffic management.
""")

# Introduction
with st.expander("📖 How it works"):
    st.markdown("""
    **Network Slicing Overview:**
    - **Network slicing** creates virtual networks tailored to specific use cases
    - **5G slices**: eMBB (high bandwidth), URLLC (low latency), mMTC (massive IoT)
    - **6G slices**: Enhanced versions with AI-driven optimization and holographic communications
    
    **Our Platform:**
    - Uses machine learning models trained on real network data
    - Predicts congestion levels and SLA compliance probabilities
    - Provides actionable recommendations for network operators
    - Supports both current 5G deployments and future 6G networks
    
    **Model Integration:**
    - Models are stored as `.joblib` files in the `models/` directory
    - If models are missing, the platform runs in demo mode with mock predictions
    - Easy to update models without changing the application code
    """)

# Main content - Objective cards
st.header("🎯 Available Objectives")

# 6G Objectives Section
st.subheader("🔵 6G Network Slicing — Eya's Dataset")
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div class="card-6g">
        <h4>Objective 5.1</h4>
        <span class="badge-6g">6G</span>
        <p><strong>Congestion Classification</strong></p>
        <p>Multi-class classification predicting network congestion levels (Normal/Light/Critical)</p>
        <p><strong>Best Model:</strong> XGBoost</p>
        <p><strong>Performance:</strong> F1-Score: 0.9775</p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("🚀 Launch 5.1", key="launch_5_1"):
        st.switch_page("pages/01_6G_objective_5_1.py")

with col2:
    st.markdown("""
    <div class="card-6g">
        <h4>Objective 5.2</h4>
        <span class="badge-6g">6G</span>
        <p><strong>QoS Probability Regression</strong></p>
        <p>Predicts SLA compliance probability (0-1 range) for network slices</p>
        <p><strong>Best Model:</strong> XGBoost tuned</p>
        <p><strong>Performance:</strong> R²=0.8537, RMSE=0.0162</p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("🚀 Launch 5.2", key="launch_5_2"):
        st.switch_page("pages/02_6G_objective_5_2.py")

with col3:
    st.markdown("""
    <div class="card-6g">
        <h4>Objective 5.3</h4>
        <span class="badge-6g">6G</span>
        <p><strong>[Coming Soon]</strong></p>
        <p>Additional 6G network slicing objective</p>
        <p><strong>Status:</strong> To be defined by Eya</p>
        <p><strong>Model:</strong> Placeholder</p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("🚀 Launch 5.3", key="launch_5_3"):
        st.switch_page("pages/03_6G_objective_5_3.py")

# 5G Objectives Section
st.subheader("🟢 5G Network Slicing — Friend's Dataset")
col4, col5, col6 = st.columns(3)

with col4:
    st.markdown("""
    <div class="card-5g">
        <h4>Objective A</h4>
        <span class="badge-5g">5G</span>
        <p><strong>[Coming Soon]</strong></p>
        <p>5G network slicing objective</p>
        <p><strong>Status:</strong> To be filled by teammate</p>
        <p><strong>Model:</strong> Placeholder</p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("🚀 Launch A", key="launch_A"):
        st.switch_page("pages/04_5G_objective_A.py")

with col5:
    st.markdown("""
    <div class="card-5g">
        <h4>Objective B</h4>
        <span class="badge-5g">5G</span>
        <p><strong>[Coming Soon]</strong></p>
        <p>5G network slicing objective</p>
        <p><strong>Status:</strong> To be filled by teammate</p>
        <p><strong>Model:</strong> Placeholder</p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("🚀 Launch B", key="launch_B"):
        st.switch_page("pages/05_5G_objective_B.py")

with col6:
    st.markdown("""
    <div class="card-5g">
        <h4>Objective C</h4>
        <span class="badge-5g">5G</span>
        <p><strong>[Coming Soon]</strong></p>
        <p>5G network slicing objective</p>
        <p><strong>Status:</strong> To be filled by teammate</p>
        <p><strong>Model:</strong> Placeholder</p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("🚀 Launch C", key="launch_C"):
        st.switch_page("pages/06_5G_objective_C.py")

# Trustworthy AI Section
st.header("🔒 Trustworthy AI")

st.markdown("""
**Trustworthy AI Principles Implementation:**
Our system incorporates multiple Trustworthy AI principles to ensure reliable, fair, and transparent AI operations.
""")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div class="card-6g">
        <h4>Anomaly Detection</h4>
        <span class="badge-6g">Trustworthy AI</span>
        <p><strong>Principle:</strong> Anomaly Detection</p>
        <p>Detect unusual network patterns using Isolation Forest algorithm</p>
        <p><strong>Model:</strong> Isolation Forest</p>
        <p><strong>Status:</strong> Ready</p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("🚀 Launch Anomaly", key="launch_anomaly"):
        st.switch_page("pages/03_6G_objective_5_3.py")

with col2:
    st.markdown("""
    <div class="card-6g">
        <h4>SHAP Explainability</h4>
        <span class="badge-6g">Trustworthy AI</span>
        <p><strong>Principle:</strong> Explainability</p>
        <p>Model explanations using SHAP values for transparency</p>
        <p><strong>Method:</strong> SHAP TreeExplainer</p>
        <p><strong>Status:</strong> Ready</p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("🚀 SHAP Analysis", key="launch_shap"):
        st.switch_page("pages/07_Trustworthy_Explainability.py")

with col3:
    st.markdown("""
    <div class="card-6g">
        <h4>Bias & Fairness</h4>
        <span class="badge-6g">Trustworthy AI</span>
        <p><strong>Principle:</strong> Fairness</p>
        <p>Bias detection across different slice types</p>
        <p><strong>Method:</strong> Statistical Parity</p>
        <p><strong>Status:</strong> Ready</p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("🚀 Fairness Check", key="launch_fairness"):
        st.switch_page("pages/08_Trustworthy_Fairness.py")

col4, col5, col6 = st.columns(3)

with col4:
    st.markdown("""
    <div class="card-6g">
        <h4>Drift Detection</h4>
        <span class="badge-6g">Trustworthy AI</span>
        <p><strong>Principle:</strong> Reliability</p>
        <p>Concept drift detection using KS tests</p>
        <p><strong>Method:</strong> Kolmogorov-Smirnov</p>
        <p><strong>Status:</strong> Ready</p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("🚀 Drift Monitor", key="launch_drift"):
        st.switch_page("pages/09_Trustworthy_Drift.py")

with col5:
    st.markdown("""
    <div class="card-6g">
        <h4>Security & Monitoring</h4>
        <span class="badge-6g">Trustworthy AI</span>
        <p><strong>Principle:</strong> Security</p>
        <p>Real-time monitoring and input validation</p>
        <p><strong>Features:</strong> KPI tracking</p>
        <p><strong>Status:</strong> Ready</p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("🚀 Security Monitor", key="launch_security"):
        st.switch_page("pages/10_Trustworthy_Monitoring.py")

# Comparison Section
st.header("📊 5G vs 6G Comparison")

comparison_data = {
    "Metric": ["Network Generation", "Dataset Owner", "Number of Objectives", "Models Used", "Key Features", "Best Performance"],
    "6G Network": ["6G", "Eya", "3 objectives", "XGBoost, XGBoost tuned", "12+ network features", "F1: 0.9775, R²: 0.8537"],
    "5G Network": ["5G", "Friend", "3 objectives", "To be defined", "To be defined", "To be defined"]
}

comparison_df = pd.DataFrame(comparison_data)
st.dataframe(comparison_df, width='stretch')

# Footer
st.markdown("---")
st.markdown("""
**Platform Information:**
- Built with Streamlit, scikit-learn, and XGBoost
- Models stored in `models/` directory as `.joblib` files
- Demo mode available when models are not found
- Easy to extend with additional objectives and models
""")

# Sidebar navigation info
st.sidebar.markdown("---")
st.sidebar.markdown("### 🧭 Navigation")
st.sidebar.markdown("""
Use the sidebar to navigate between objectives:
- **6G Objectives** (Purple): Eya's dataset
- **5G Objectives** (Teal): Friend's dataset
""")

st.sidebar.markdown("### 📁 Model Status")
model_status = {
    "6G Obj 5.1": " Ready" if load_model_with_fallback("model_6G_5_1_xgboost.joblib")[1] else " Demo",
    "6G Obj 5.2": " Ready" if load_model_with_fallback("model_6G_5_2_xgboost.joblib")[1] else " Demo",
    "6G Obj 5.3": " Ready" if load_model_with_fallback("model_anomaly_eya.joblib")[1] else " Demo",
    "Trustworthy AI": " Ready"
}

for model, status in model_status.items():
    st.sidebar.markdown(f"**{model}:** {status}")
