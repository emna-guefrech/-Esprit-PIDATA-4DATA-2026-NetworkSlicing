import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from utils.explainability import (
    load_shap_explainer, 
    generate_shap_summary_plot, 
    generate_shap_bar_plot,
    generate_shap_waterfall_plot,
    explain_prediction
)
from utils.predict import predict_6g_5_1
from utils.model_loader import load_model_with_fallback

# Page config
st.set_page_config(
    page_title="Trustworthy AI - Explainability",
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
    .crisp-dm-phase {
        background-color: #F3E8FF;
        border-left: 4px solid #7C3AED;
        padding: 0.5rem;
        margin: 0.5rem 0;
        font-size: 0.875rem;
    }
    .explanation-box {
        background-color: #F0F9FF;
        border-left: 4px solid #0EA5E9;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<span class="badge-6g"> Trustworthy AI</span>', unsafe_allow_html=True)
st.title("Model Explainability with SHAP")

# CRISP-DM Phase indicator
st.markdown('<div class="crisp-dm-phase">CRISP-DM Phase: Evaluation - Model Explainability</div>', unsafe_allow_html=True)

st.markdown("""
**Business Objective:** Provide transparent explanations for the 6G network congestion classification model 
using SHAP (SHapley Additive exPlanations). This implements the Trustworthy AI principle of **Explainability** 
by showing how each feature contributes to individual predictions and overall model behavior.
""")

# Load model and explainer
model_path = "models/model_classification_eya.joblib"
background_data_path = "C:/Users/EYA/PI/network_slicing_dataset_6G_final.csv"

explainer, background_data, feature_names = load_shap_explainer(model_path, background_data_path)

if explainer is None:
    st.error("Could not load SHAP explainer. Using simple explainability system.")
    
    # Use simple explainability as fallback
    try:
        from utils.simple_explainability import create_simple_explanation, create_summary_plot
        st.markdown("**Using Simple Explainability System**")
        
        # Test with sample data
        test_features = {
            'Packet Loss Budget': 0.001,
            'Latency Budget (µs)': 1000,
            'Slice Type': 'ERLLC'
        }
        
        result = create_simple_explanation(test_features)
        st.markdown(result['explanation'])
        
        # Create simple plot
        df = pd.read_csv('C:/Users/EYA/PI/network_slicing_dataset_6G_final.csv', sep=';')
        fig = create_summary_plot(df)
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("**Simple system working!**")
        
    except Exception as e:
        st.error(f"Error in simple explainability: {str(e)}")
        
else:
    st.stop()

# Model info
with st.expander(" Model Information"):
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Explainability Method:**")
        st.markdown("- **Algorithm:** SHAP (SHapley Additive exPlanations)")
        st.markdown("- **Explainer Type:** TreeExplainer (for XGBoost)")
        st.markdown("- **Background Data:** 10K samples from 6G dataset")
        st.markdown("- **Features:** 12 network parameters")
    
    with col2:
        st.markdown("**Trustworthy AI Principle:**")
        st.markdown("- **Explainability:** Model decisions are transparent")
        st.markdown("- **Interpretability:** Feature contributions are clear")
        st.markdown("- **Accountability:** Reasoning can be audited")
        st.markdown("- **Transparency:** Black box is opened")

# Navigation tabs
tab1, tab2, tab3, tab4 = st.tabs([" Summary Plot", " Feature Importance", " Single Prediction", " Text Explanation"])

with tab1:
    st.header(" SHAP Summary Plot (Beeswarm)")
    st.markdown("""
    This plot shows how each feature affects the model's predictions across the dataset:
    - **X-axis:** SHAP value (positive = increases probability, negative = decreases)
    - **Y-axis:** Features ordered by importance
    - **Color:** Feature value (red = high, blue = low)
    """)
    
    # Generate summary plot
    fig_summary = generate_shap_summary_plot(explainer, background_data, feature_names)
    st.plotly_chart(fig_summary, use_container_width=True, key="shap_summary_plot")
    
    st.markdown("**Interpretation:**")
    st.markdown("- Features at the top have the most impact on predictions")
    st.markdown("- Points to the right increase the probability of the predicted class")
    st.markdown("- Color indicates whether the feature value is high (red) or low (blue)")

with tab2:
    st.header(" SHAP Feature Importance (Bar Plot)")
    st.markdown("""
    This plot shows the mean absolute SHAP values for each feature:
    - **X-axis:** Mean |SHAP Value| (average impact magnitude)
    - **Y-axis:** Features ordered by importance
    - **Height:** Overall importance of the feature
    """)
    
    # Generate bar plot
    fig_bar = generate_shap_bar_plot(explainer, background_data, feature_names)
    st.plotly_chart(fig_bar, use_container_width=True, key="shap_bar_plot")
    
    st.markdown("**Key Insights:**")
    st.markdown("- The most important features drive most of the model's decisions")
    st.markdown("- Less important features have minimal impact on predictions")
    st.markdown("- This helps identify which network parameters need attention")

with tab3:
    st.header(" Single Prediction Explanation")
    st.markdown("""
    Analyze individual predictions to understand why the model made a specific decision:
    """)
    
    # Sample selection
    col1, col2 = st.columns(2)
    
    with col1:
        sample_idx = st.number_input("Sample Index", min_value=0, max_value=99, value=0, step=1)
    
    with col2:
        st.markdown("**Sample Range:** 0-99 (subset of background data)")
    
    # Generate waterfall plot
    fig_waterfall, explanation = generate_shap_waterfall_plot(explainer, background_data.iloc[sample_idx], feature_names, sample_idx)
    st.plotly_chart(fig_waterfall, use_container_width=True, key="shap_waterfall_plot")
    
    # Display explanation
    st.markdown('<div class="explanation-box">', unsafe_allow_html=True)
    st.markdown(explanation)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Show sample details
    st.subheader("Sample Details")
    sample_data = background_data.iloc[sample_idx]
    st.write(sample_data)

with tab4:
    st.header(" Text Explanation Generator")
    st.markdown("""
    Enter network parameters to get a human-readable explanation of the model's decision:
    """)
    
    # Input form
    col1, col2, col3 = st.columns(3)
    
    with col1:
        packet_loss_budget = st.number_input("Packet Loss Budget", min_value=0.0, max_value=0.1, value=0.001, format="%.6f", step=0.000001, key="exp_packet_loss")
        latency_budget = st.number_input("Latency Budget (µs)", min_value=100.0, max_value=10000.0, value=1000.0, step=100.0, key="exp_latency")
        jitter_budget = st.number_input("Jitter Budget (µs)", min_value=50.0, max_value=5000.0, value=1000.0, step=100.0, key="exp_jitter")
    
    with col2:
        data_rate_budget = st.number_input("Data Rate Budget (Gbps)", min_value=1.0, max_value=10.0, value=1.0, step=0.1, key="exp_data_rate")
        required_mobility = st.selectbox("Required Mobility", ["0", "1", "2"], index=0, key="exp_mobility")
        required_connectivity = st.selectbox("Required Connectivity", ["0", "1", "2"], index=0, key="exp_connectivity")
    
    with col3:
        slice_available_rate = st.number_input("Slice Available Transfer Rate (Gbps)", min_value=0.1, max_value=10.0, value=1.0, step=0.1, key="exp_rate")
        slice_latency = st.number_input("Slice Latency (µs)", min_value=10.0, max_value=10000.0, value=1000.0, step=100.0, key="exp_slice_latency")
        slice_packet_loss = st.number_input("Slice Packet Loss", min_value=0.0, max_value=0.1, value=0.001, format="%.6f", step=0.000001, key="exp_slice_packet_loss")
    
    col4, col5 = st.columns(2)
    
    with col4:
        slice_jitter = st.number_input("Slice Jitter (µs)", min_value=10.0, max_value=5000.0, value=1000.0, step=100.0, key="exp_slice_jitter")
        slice_type = st.selectbox("Slice Type", ["ERLLC", "umMTC", "MBRLLC", "mURLLC", "feMBB"], index=0, key="exp_slice_type")
    
    with col5:
        slice_handover = st.number_input("Slice Handover", min_value=0.0, max_value=2.0, value=0.0, step=0.1, key="exp_handover")
    
    # Generate explanation button
    if st.button(" Generate Explanation", type="primary"):
        # Prepare features
        features = {
            'Packet Loss Budget': packet_loss_budget,
            'Latency Budget (µs)': latency_budget,
            'Jitter Budget (µs)': jitter_budget,
            'Data Rate Budget (Gbps)': data_rate_budget,
            'Required Mobility': required_mobility,
            'Required Connectivity': required_connectivity,
            'Slice Available Transfer Rate (Gbps)': slice_available_rate,
            'Slice Latency (µs)': slice_latency,
            'Slice Packet Loss': slice_packet_loss,
            'Slice Jitter (µs)': slice_jitter,
            'Slice Type': slice_type,
            'Slice Handover': slice_handover
        }
        
        # Generate explanation
        explanation = explain_prediction(model_path, features)
        
        # Display explanation
        st.markdown('<div class="explanation-box">', unsafe_allow_html=True)
        st.markdown(explanation)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Also make prediction to show confidence
        model, is_real_model = load_model_with_fallback(model_path)
        if model is not None:
            result = predict_6g_5_1(model, features, not is_real_model)
            
            st.subheader("Prediction Details")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Predicted Class", result['predicted_class'])
            
            with col2:
                st.metric("Confidence", f"{result['confidence']:.1%}")
            
            with col3:
                if result['class_probabilities']:
                    max_prob = max(result['class_probabilities'].values())
                    st.metric("Max Probability", f"{max_prob:.1%}")

# Trustworthy AI Principles
st.header(" Trustworthy AI Principles")

col1, col2 = st.columns(2)

with col1:
    st.markdown("**Explainability Benefits:**")
    st.markdown("- **Transparency:** Users understand why decisions are made")
    st.markdown("- **Trust:** Clear explanations build confidence in AI systems")
    st.markdown("- **Debugging:** Identify and fix model biases or errors")
    st.markdown("- **Compliance:** Meet regulatory requirements for AI transparency")

with col2:
    st.markdown("**SHAP Advantages:**")
    st.markdown("- **Game Theory:** Based on solid mathematical foundations")
    st.markdown("- **Local Explanations:** Explain individual predictions")
    st.markdown("- **Global Insights:** Understand overall model behavior")
    st.markdown("- **Feature Consistency:** Consistent explanations across predictions")

# Technical Details
with st.expander(" Technical Details"):
    st.markdown("**SHAP Implementation:**")
    st.markdown("- **Library:** SHAP v0.41.0")
    st.markdown("- **Explainer:** TreeExplainer (optimized for tree-based models)")
    st.markdown("- **Background Data:** 100 samples for computational efficiency")
    st.markdown("- **Visualization:** Plotly for interactive charts")
    
    st.markdown("**Computational Considerations:**")
    st.markdown("- **Performance:** Subset of data used for faster computation")
    st.markdown("- **Memory:** Optimized for large datasets")
    st.markdown("- **Interactivity:** Hover tooltips for detailed information")

# Footer
st.markdown("---")
st.markdown("""
**Note:** SHAP explanations help make the AI model's decisions transparent and understandable. 
This builds trust and allows network operators to understand why the system predicts certain 
congestion levels, enabling better decision-making and model improvement.
""")
