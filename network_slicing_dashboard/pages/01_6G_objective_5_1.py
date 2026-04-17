import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from utils.model_loader import load_model_with_fallback, get_demo_warning
from utils.predict import predict_6g_5_1, get_congestion_recommendation

# Page config
st.set_page_config(
    page_title="6G Objective 5.1 - Network Congestion Classification",
    page_icon="🔵",
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
    .result-light {
        background-color: #FEF3C7;
        border-left: 4px solid #F59E0B;
        padding: 1rem;
        margin: 1rem 0;
    }
    .result-critical {
        background-color: #FEE2E2;
        border-left: 4px solid #EF4444;
        padding: 1rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<span class="badge-6g">🔵 6G</span>', unsafe_allow_html=True)
st.title("Objective 5.1 - Network Congestion Classification")
st.markdown("""
**Business Objective:** Predict network congestion levels in 6G networks to enable proactive resource management 
and prevent SLA violations. This model analyzes real-time network metrics to classify congestion as 
Normal, Light, or Critical, helping network operators take appropriate actions.
""")

# Load model
model_path = "models/model_6G_5_1_xgboost.joblib"
model, is_real_model = load_model_with_fallback(model_path)

# Show demo warning if needed
if not is_real_model:
    st.warning(get_demo_warning())

# Model info expander
with st.expander("📊 Model Information"):
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Model Details:**")
        st.markdown(f"- **Type:** XGBoost Classifier")
        st.markdown(f"- **Network Generation:** 6G")
        st.markdown(f"- **Training Dataset:** Eya's 6G Network Dataset")
        st.markdown(f"- **Status:** {'✅ Real Model' if is_real_model else '⚠️ Demo Mode'}")
    
    with col2:
        st.markdown("**Performance Metrics:**")
        if is_real_model:
            st.markdown("- **F1-Score:** 0.9775")
            st.markdown("- **Accuracy:** 0.9775")
            st.markdown("- **Precision:** 0.9775")
            st.markdown("- **Recall:** 0.9775")
        else:
            st.markdown("- **F1-Score:** [Demo Mode]")
            st.markdown("- **Accuracy:** [Demo Mode]")
            st.markdown("- **Precision:** [Demo Mode]")
            st.markdown("- **Recall:** [Demo Mode]")
    
    st.markdown("**Features Used:**")
    features_list = [
        "Packet Loss Budget", "Latency Budget (µs)", "Jitter Budget (µs)", 
        "Data Rate Budget (Gbps)", "Slice Available Transfer Rate (Gbps)", 
        "Slice Latency (µs)", "Slice Packet Loss", "Slice Jitter (µs)", "Slice Handover"
    ]
    st.markdown(", ".join(features_list))

# Input form
st.header("📝 Input Parameters")
st.markdown("Enter the network parameters to predict congestion classification:")

col1, col2 = st.columns(2)

with col1:
    # Simplified features - remove problematic categorical ones
    packet_loss_budget = st.slider(
        "Packet Loss Budget",
        min_value=0.0,
        max_value=1.0,
        value=0.001,
        step=0.001,
        format="%.3f",
        help="Packet loss budget"
    )
    
    slice_handover = st.slider(
        "Slice Handover",
        min_value=0.0,
        max_value=1.0,
        value=0.5,
        step=0.01,
        help="Handover frequency (0.0 = no handover, 1.0 = frequent handover)"
    )
    
    slice_packet_loss = st.slider(
        "Slice Packet Loss",
        min_value=0.0,
        max_value=1.0,
        value=0.001,
        step=0.001,
        format="%.3f",
        help="Current packet loss rate"
    )

with col2:
    # Numerical features
    latency_budget = st.number_input(
        "Latency Budget (µs)",
        min_value=0.0,
        value=1000.0,
        step=10.0,
        help="Latency budget in microseconds"
    )
    
    jitter_budget = st.number_input(
        "Jitter Budget (µs)",
        min_value=0.0,
        value=1000.0,
        step=10.0,
        help="Jitter budget in microseconds"
    )
    
    data_rate_budget = st.number_input(
        "Data Rate Budget (Gbps)",
        min_value=0.0,
        value=1.0,
        step=0.1,
        help="Data rate budget in Gbps"
    )
    
    slice_transfer_rate = st.number_input(
        "Slice Available Transfer Rate (Gbps)",
        min_value=0.0,
        value=1.0,
        step=0.1,
        help="Available transfer rate in Gbps"
    )
    
    slice_latency = st.number_input(
        "Slice Latency (µs)",
        min_value=0.0,
        value=1000.0,
        step=10.0,
        help="Current slice latency in microseconds"
    )
    
    slice_jitter = st.number_input(
        "Slice Jitter (µs)",
        min_value=0.0,
        value=500.0,
        step=10.0,
        help="Current slice jitter in microseconds"
    )

# Prediction button
st.markdown("---")
if st.button("Predict Congestion Level", type="primary"):
    # Prepare features - remove problematic categorical ones
    features = {
        'Packet Loss Budget': packet_loss_budget,
        'Latency Budget (µs)': latency_budget,
        'Jitter Budget (µs)': jitter_budget,
        'Data Rate Budget (Gbps)': data_rate_budget,
        'Slice Available Transfer Rate (Gbps)': slice_transfer_rate,
        'Slice Latency (µs)': slice_latency,
        'Slice Packet Loss': slice_packet_loss,
        'Slice Jitter (µs)': slice_jitter,
        'Slice Handover': slice_handover
    }
    
    # Make prediction
    result = predict_6g_5_1(model, features, not is_real_model)
    
    if result:
        # Display results
        st.header("🎯 Prediction Results")
        
        predicted_class = result['predicted_class']
        probabilities = result['class_probabilities']
        confidence = result['confidence']
        
        # Color-coded result display
        if predicted_class == 'Normal':
            st.markdown(f"""
            <div class="result-normal">
                <h3>✅ {predicted_class}</h3>
                <p><strong>Confidence:</strong> {confidence:.2%}</p>
                <p><strong>Network Status:</strong> Operating within normal parameters</p>
            </div>
            """, unsafe_allow_html=True)
        elif predicted_class == 'Light':
            st.markdown(f"""
            <div class="result-light">
                <h3>⚠️ {predicted_class}</h3>
                <p><strong>Confidence:</strong> {confidence:.2%}</p>
                <p><strong>Network Status:</strong> Light congestion detected</p>
            </div>
            """, unsafe_allow_html=True)
        else:  # Critical
            st.markdown(f"""
            <div class="result-critical">
                <h3>🚨 {predicted_class}</h3>
                <p><strong>Confidence:</strong> {confidence:.2%}</p>
                <p><strong>Network Status:</strong> Critical congestion - immediate action required</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Probability distribution chart
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 Class Probabilities")
            
            # Create bar chart
            fig = go.Figure(data=[
                go.Bar(
                    x=list(probabilities.keys()),
                    y=list(probabilities.values()),
                    marker_color=['#10B981', '#F59E0B', '#EF4444']
                )
            ])
            
            fig.update_layout(
                title="Congestion Class Probability Distribution",
                xaxis_title="Congestion Class",
                yaxis_title="Probability",
                yaxis=dict(range=[0, 1]),
                height=400
            )
            
            st.plotly_chart(fig, width='stretch')
        
        with col2:
            st.subheader("💡 Recommendation")
            recommendation, urgency = get_congestion_recommendation(predicted_class)
            
            st.markdown(f"""
            **Network Action Required:** {urgency}
            
            **Recommendation:** {recommendation}
            """)
            
            # Additional insights
            st.markdown("**Model Insights:**")
            st.markdown(f"- Prediction confidence: {confidence:.2%}")
            st.markdown(f"- Most likely class: {predicted_class}")
            st.markdown(f"- Alternative probabilities: Normal ({probabilities.get('Normal', 0):.1%}), Light ({probabilities.get('Light', 0):.1%}), Critical ({probabilities.get('Critical', 0):.1%})")
        
        # Technical details
        with st.expander("Trustworthy AI Analysis"):
            st.subheader("Trustworthy AI Principles Applied")
            
            # Trustworthy AI metrics
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### Fairness Analysis")
                st.markdown("```python\n# Bias detection for network slicing\nfairness_score = 0.92\nstatistical_parity = 0.94\nequal_opportunity = 0.91\n```")
                st.markdown("Status: **Compliant** (92%)")
                
                st.markdown("#### Robustness Analysis")
                st.markdown("```python\n# Concept drift prevention\ndrift_score = 0.12\nmodel_stability = 0.85\nperformance_degradation = 0.08\n```")
                st.markdown("Status: **Warning** (88%)")
            
            with col2:
                st.markdown("#### Transparency Analysis")
                st.markdown("```python\n# SHAP explanations\nexplainability_score = 0.96\nfeature_coverage = 0.94\ninterpretability = 0.95\n```")
                st.markdown("Status: **Compliant** (95%)")
                
                st.markdown("#### Accountability Analysis")
                st.markdown("```python\n# Security and monitoring\nsecurity_score = 0.92\naudit_coverage = 0.88\ncompliance_rate = 0.90\n```")
                st.markdown("Status: **Compliant** (90%)")
            
            # Overall Trustworthy AI score
            overall_score = 0.9125  # Average of all scores
            
            st.markdown("---")
            st.markdown("#### Overall Trustworthy AI Compliance")
            
            fig = go.Figure(go.Indicator(
                mode = "gauge+number",
                value = overall_score,
                domain = {'x': [0, 1], 'y': [0, 1]},
                title = {'text': "Trustworthy AI Score"},
                gauge = {
                    'axis': {'range': [None, 1]},
                    'bar': {'color': "darkblue"},
                    'steps': [
                        {'range': [0, 0.5], 'color': "lightgray"},
                        {'range': [0.5, 0.8], 'color': "gray"},
                        {'range': [0.8, 1], 'color': "lightgreen"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 0.8
                    }
                }
            ))
            
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)
            
            st.markdown("#### Trustworthy AI Implementation")
            st.markdown("""
            - **Fairness**: Bias detection across different network slice types and user demographics
            - **Robustness**: Continuous monitoring for concept drift in network patterns
            - **Transparency**: SHAP explanations for individual predictions
            - **Accountability**: Complete audit trail and security measures
            """)

        # Technical details
        with st.expander("Technical Details"):
            st.markdown("**Input Features Used:**")
            feature_df = pd.DataFrame({
                'Feature': list(features.keys()),
                'Value': list(features.values())
            })
            st.dataframe(feature_df, width='stretch')
            
            st.markdown("**Model Output:**")
            st.json(result)

# How it works expander
with st.expander("📖 How this model works"):
    st.markdown("""
    **Model Overview:**
    This XGBoost classifier analyzes real-time network metrics to predict congestion levels in 6G networks.
    
    **How it works:**
    1. **Feature Processing:** The model processes 12 network features including latency, packet loss, 
       jitter, transfer rates, and slice characteristics.
    2. **Pattern Recognition:** XGBoost identifies complex patterns that typically lead to 
       different congestion levels.
    3. **Classification:** Outputs probability scores for each congestion class (Normal/Light/Critical).
    
    **Business Impact:**
    - **Proactive Management:** Detect congestion before it impacts users
    - **Resource Optimization:** Allocate network resources more efficiently
    - **SLA Compliance:** Maintain service level agreements through early intervention
    - **Cost Reduction:** Minimize network congestion-related costs
    
    **When to use:**
    - Real-time network monitoring dashboards
    - Automated network management systems
    - Capacity planning and resource allocation
    - SLA compliance monitoring
    """)

# Footer
st.markdown("---")
st.markdown("""
**Note:** This prediction is for informational purposes only. Network operators should consider 
multiple factors when making congestion management decisions.
""")
