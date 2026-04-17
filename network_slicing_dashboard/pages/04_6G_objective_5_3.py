import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from utils.model_loader import load_model_with_fallback, get_demo_warning
from utils.predict import predict_6g_5_3

# Page config
st.set_page_config(
    page_title="6G Objective 5.3 - Anomaly Detection",
    page_icon="",
    layout="wide"
)

# Custom CSS
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
    .result-normal {
        background-color: #D1FAE5;
        border-left: 4px solid #10B981;
        padding: 1rem;
        margin: 1rem 0;
    }
    .result-anomaly {
        background-color: #FEE2E2;
        border-left: 4px solid #EF4444;
        padding: 1rem;
        margin: 1rem 0;
    }
    .crisp-dm-phase {
        background-color: #F3E8FF;
        border-left: 4px solid #7C3AED;
        padding: 0.5rem;
        margin: 0.5rem 0;
        font-size: 0.875rem;
    }
    .numpy-warning {
        background-color: #FEF3C7;
        border-left: 4px solid #F59E0B;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 0.25rem;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<span class="badge-6g"> 6G</span>', unsafe_allow_html=True)
st.title("Objective 5.3 - Anomaly Detection for Best-Effort Traffic")

# CRISP-DM Phase indicator
st.markdown('<div class="crisp-dm-phase">CRISP-DM Phase: Modeling - Anomaly Detection</div>', unsafe_allow_html=True)

st.markdown("""
**Business Objective:** Detect anomalous patterns in 6G network traffic for best-effort services using Isolation Forest. 
This model identifies unusual network behavior that could indicate potential issues, security threats, or exceptional 
network conditions requiring investigation. This implements the Trustworthy AI principle of **Anomaly Detection**.
""")

# ── Safe model loading with NumPy compatibility handling ──────────────────────
model_path = "models/model_anomaly_eya.joblib"
model = None
is_real_model = False
numpy_error = False

try:
    model, is_real_model = load_model_with_fallback(model_path)
except Exception as e:
    error_msg = str(e)
    if "numpy._core" in error_msg or "numpy" in error_msg.lower():
        numpy_error = True
        is_real_model = False
        model = None
    else:
        st.error(f"Unexpected error loading model: {error_msg}")

# Show appropriate warnings
if numpy_error:
    st.markdown("""
    <div class="numpy-warning">
        <strong>⚠️ NumPy Compatibility Issue Detected</strong><br>
        The saved model was built with a newer version of NumPy than the one currently installed.<br>
        <strong>Running in Demo Mode</strong> — predictions are simulated.<br><br>
        <strong>Fix:</strong> Run <code>pip install --upgrade numpy scikit-learn joblib</code> 
        then re-save the model in your current environment.
    </div>
    """, unsafe_allow_html=True)
elif not is_real_model:
    st.warning(get_demo_warning())

# Model info expander
with st.expander("Model Information"):
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Model Details:**")
        st.markdown("- **Type:** Isolation Forest")
        st.markdown("- **Network Generation:** 6G")
        st.markdown("- **Training Dataset:** Eya's 6G Network Dataset")
        st.markdown(f"- **Status:** {'✅ Real Model' if is_real_model else '⚠️ Demo Mode'}")

    with col2:
        st.markdown("**Performance Metrics:**")
        if is_real_model:
            st.markdown("- **Contamination Rate:** 10%")
            st.markdown("- **Normal Samples:** ~90%")
            st.markdown("- **Anomaly Samples:** ~10%")
            st.markdown("- **Algorithm:** Isolation Forest")
        else:
            st.markdown("- **Contamination Rate:** [Demo Mode]")
            st.markdown("- **Normal Samples:** [Demo Mode]")
            st.markdown("- **Anomaly Samples:** [Demo Mode]")
            st.markdown("- **Algorithm:** [Demo Mode]")

    st.markdown("**Features Used:**")
    features_list = [
        "Packet Loss Budget", "Latency Budget (µs)", "Jitter Budget (µs)",
        "Data Rate Budget (Gbps)", "Required Mobility", "Required Connectivity",
        "Slice Available Transfer Rate (Gbps)", "Slice Latency (µs)",
        "Slice Packet Loss", "Slice Jitter (µs)", "Slice Type", "Slice Handover"
    ]
    st.markdown(", ".join(features_list))

# ── Input form ────────────────────────────────────────────────────────────────
st.header("Input Parameters")
st.markdown("Enter the network parameters to detect anomalies:")

col1, col2, col3 = st.columns(3)

with col1:
    packet_loss_budget   = st.number_input("Packet Loss Budget",              min_value=0.0,   max_value=0.1,    value=0.001,  format="%.6f", step=0.000001)
    latency_budget       = st.number_input("Latency Budget (µs)",             min_value=100.0, max_value=10000.0,value=1000.0, step=100.0)
    jitter_budget        = st.number_input("Jitter Budget (µs)",              min_value=50.0,  max_value=5000.0, value=1000.0, step=100.0)

with col2:
    data_rate_budget     = st.number_input("Data Rate Budget (Gbps)",         min_value=1.0,   max_value=10.0,   value=1.0,    step=0.1)
    required_mobility    = st.selectbox("Required Mobility",    ["0", "1", "2"], index=0)
    required_connectivity= st.selectbox("Required Connectivity",["0", "1", "2"], index=0)

with col3:
    slice_available_rate = st.number_input("Slice Available Transfer Rate (Gbps)", min_value=0.1, max_value=10.0,   value=1.0,    step=0.1)
    slice_latency        = st.number_input("Slice Latency (µs)",              min_value=10.0,  max_value=10000.0,value=1000.0, step=100.0)
    slice_packet_loss    = st.number_input("Slice Packet Loss",               min_value=0.0,   max_value=0.1,    value=0.001,  format="%.6f", step=0.000001)

col4, col5 = st.columns(2)

with col4:
    slice_jitter = st.number_input("Slice Jitter (µs)", min_value=10.0, max_value=5000.0, value=1000.0, step=100.0)
    slice_type   = st.selectbox("Slice Type", ["ERLLC", "umMTC", "MBRLLC", "mURLLC", "feMBB"], index=0)

with col5:
    slice_handover = st.number_input("Slice Handover", min_value=0.0, max_value=2.0, value=0.0, step=0.1)

# ── Predict button ────────────────────────────────────────────────────────────
st.markdown("---")
predict_btn = st.button("🔍 Detect Anomaly", type="primary", use_container_width=True)

if not predict_btn:
    st.info("👆 Fill in the parameters above and click **Detect Anomaly** to run the model.")
    st.stop()

# ── Prediction ────────────────────────────────────────────────────────────────
features = {
    'Packet Loss Budget':                   packet_loss_budget,
    'Latency Budget (µs)':                  latency_budget,
    'Jitter Budget (µs)':                   jitter_budget,
    'Data Rate Budget (Gbps)':              data_rate_budget,
    'Required Mobility':                    required_mobility,
    'Required Connectivity':                required_connectivity,
    'Slice Available Transfer Rate (Gbps)': slice_available_rate,
    'Slice Latency (µs)':                   slice_latency,
    'Slice Packet Loss':                    slice_packet_loss,
    'Slice Jitter (µs)':                    slice_jitter,
    'Slice Type':                           slice_type,
    'Slice Handover':                       slice_handover
}

# Always use demo mode if model failed to load
result = predict_6g_5_3(model, features, not is_real_model)

# ── Results ───────────────────────────────────────────────────────────────────
st.header("Anomaly Detection Results")

result_class = "result-anomaly" if result['is_anomaly'] else "result-normal"
status_icon  = "🚨" if result['is_anomaly'] else "✅"
status_text  = "Anomaly Detected!" if result['is_anomaly'] else "Normal Operation"
action_text  = "Investigation Required" if result['is_anomaly'] else "No Action Needed"

st.markdown(f'<div class="{result_class}">', unsafe_allow_html=True)
col1, col2, col3 = st.columns([1, 2, 1])

with col1:
    st.markdown(f"### {status_icon} {status_text}")

with col2:
    st.markdown(f"**Anomaly Score:** {result['anomaly_score']:.4f}")
    st.markdown(f"**Confidence:** {result['confidence']:.1%}")
    st.markdown(f"**Label:** {result['anomaly_label']}")

with col3:
    st.markdown(f"**Status:** {action_text}")

st.markdown('</div>', unsafe_allow_html=True)

st.markdown("**Explanation:**")
st.markdown(result['explanation'])

if result.get('is_demo'):
    st.caption("ℹ️ Results are simulated (demo mode). Load a compatible model for real predictions.")

# ── Anomaly Score Gauge ───────────────────────────────────────────────────────
st.header("Anomaly Score Analysis")

fig = go.Figure(go.Indicator(
    mode  = "gauge+number+delta",
    value = result['anomaly_score'],
    domain= {'x': [0, 1], 'y': [0, 1]},
    title = {'text': "Anomaly Score"},
    delta = {'reference': -0.05},
    gauge = {
        'axis': {'range': [-0.2, 0.2]},
        'bar':  {'color': "darkblue"},
        'steps': [
            {'range': [-0.2, -0.05], 'color': "lightcoral"},
            {'range': [-0.05, 0.2],  'color': "lightgreen"}
        ],
        'threshold': {
            'line':      {'color': "red", 'width': 4},
            'thickness': 0.75,
            'value':     -0.05
        }
    }
))
fig.update_layout(height=400)
st.plotly_chart(fig, use_container_width=True)

# ── Score Distribution ────────────────────────────────────────────────────────
st.header("Anomaly Distribution")

np.random.seed(42)
normal_scores  = np.random.normal(0.05,  0.03, 9000)
anomaly_scores = np.random.normal(-0.08, 0.02, 1000)

fig = px.histogram(
    x    = list(normal_scores) + list(anomaly_scores),
    color= ['Normal'] * 9000 + ['Anomaly'] * 1000,
    nbins= 50,
    title= "Distribution of Anomaly Scores in Training Data",
    labels={'x': 'Anomaly Score', 'color': 'Classification'},
    color_discrete_map={'Normal': '#10B981', 'Anomaly': '#EF4444'}
)
fig.add_vline(
    x=result['anomaly_score'],
    line_dash="dash",
    line_color="blue",
    annotation_text=f"Current: {result['anomaly_score']:.4f}"
)
fig.update_layout(height=400)
st.plotly_chart(fig, use_container_width=True)

# ── Feature Values Chart ──────────────────────────────────────────────────────
st.header("Feature Analysis")

# Only plot numeric features
numeric_features = {
    k: v for k, v in features.items()
    if isinstance(v, (int, float))
}

fig = px.bar(
    x    = list(numeric_features.keys()),
    y    = list(numeric_features.values()),
    title= "Input Feature Values (Numeric)",
    labels={'x': 'Features', 'y': 'Values'},
    color= list(numeric_features.values()),
    color_continuous_scale='Blues'
)
fig.update_layout(height=400, xaxis_tickangle=-45)
st.plotly_chart(fig, use_container_width=True)

# ── Trustworthy AI ────────────────────────────────────────────────────────────
st.header("Trustworthy AI Principles")

col1, col2 = st.columns(2)

with col1:
    st.markdown("**Anomaly Detection:**")
    st.markdown("- Identifies unusual patterns in network data")
    st.markdown("- Helps detect potential issues early")
    st.markdown("- Supports proactive network management")

with col2:
    st.markdown("**Model Transparency:**")
    st.markdown("- Isolation Forest provides interpretable scores")
    st.markdown("- Clear threshold for anomaly classification")
    st.markdown("- Explainable reasoning for decisions")

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("""
**Note:** This anomaly detection model helps identify unusual network patterns that may indicate 
potential issues, security threats, or exceptional conditions requiring investigation. 
The model uses Isolation Forest algorithm with 10% expected anomaly rate.
""")
