import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from utils.drift_detection import create_drift_detection_report

# Page config
st.set_page_config(
    page_title="Trustworthy AI - Drift Detection",
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
    .drift-stable {
        background-color: #D1FAE5;
        border-left: 4px solid #10B981;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 0.5rem;
    }
    .drift-moderate {
        background-color: #FEF3C7;
        border-left: 4px solid #F59E0B;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 0.5rem;
    }
    .drift-high {
        background-color: #FEE2E2;
        border-left: 4px solid #EF4444;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<span class="badge-6g"> Trustworthy AI</span>', unsafe_allow_html=True)
st.title("Concept Drift Detection")

# CRISP-DM Phase indicator
st.markdown('<div class="crisp-dm-phase">CRISP-DM Phase: Deployment - Drift Monitoring</div>', unsafe_allow_html=True)

st.markdown("""
**Business Objective:** Detect concept drift in the 6G network congestion classification model by comparing 
data distributions and model performance between different time periods. This implements the Trustworthy AI 
principle of **Reliability** by ensuring the model remains accurate over time as network conditions evolve.
""")

# Load dataset and create report
dataset_path = "C:/Users/EYA/PI/network_slicing_dataset_6G_final.csv"
drift_report = create_drift_detection_report(dataset_path)

if not drift_report:
    st.error("Could not load drift detection data. Please ensure the dataset is available.")
    st.stop()

# Drift verdict
verdict = drift_report['drift_verdict']
color = drift_report['drift_color']
recommendations = drift_report['recommendations']

# Display drift verdict
st.header(" Drift Assessment")

if verdict == "Stable":
    st.markdown(f'<div class="drift-stable">', unsafe_allow_html=True)
    st.markdown(f"###  Stable Model")
    st.markdown("No significant drift detected. Model performance is stable.")
    st.markdown('</div>', unsafe_allow_html=True)
elif verdict == "Moderate Drift":
    st.markdown(f'<div class="drift-moderate">', unsafe_allow_html=True)
    st.markdown(f"###  Moderate Drift")
    st.markdown("Some drift detected. Monitor closely and consider retraining.")
    st.markdown('</div>', unsafe_allow_html=True)
else:
    st.markdown(f'<div class="drift-high">', unsafe_allow_html=True)
    st.markdown(f"###  High Drift")
    st.markdown("Significant drift detected. Immediate model retraining required.")
    st.markdown('</div>', unsafe_allow_html=True)

# Key metrics
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Old Data Size", drift_report['old_data_size'])

with col2:
    st.metric("New Data Size", drift_report['new_data_size'])

with col3:
    drift_percentage = (drift_report['drifted_features'] / drift_report['total_features']) * 100
    st.metric("Features Drifted", f"{drift_report['drifted_features']}/{drift_report['total_features']}")

with col4:
    st.metric("Drift Verdict", verdict)

# Detailed analysis
st.header(" Detailed Drift Analysis")

tab1, tab2, tab3, tab4 = st.tabs([" Feature Drift Table", " Distribution Plots", " Performance Drift", " Recommendations"])

with tab1:
    st.subheader("Feature Drift Detection Table")
    st.markdown("""
    This table shows the results of Kolmogorov-Smirnov tests for each feature:
    - **P-Value < 0.05:** Drift detected (statistically significant distribution change)
    - **KS Statistic:** Magnitude of distribution difference
    - **Mean Change:** Difference in mean values between old and new data
    """)
    
    # Display drift table
    if not drift_report['drift_table'].empty:
        st.dataframe(drift_report['drift_table'], use_container_width=True)
        
        # Summary statistics
        st.markdown("**Drift Summary:**")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Features Tested", drift_report['total_features'])
        
        with col2:
            st.metric("Features Drifted", drift_report['drifted_features'])
        
        with col3:
            st.metric("Drift Percentage", f"{drift_percentage:.1f}%")
    else:
        st.warning("No drift data available.")

with tab2:
    st.subheader("Distribution Comparison Plots")
    st.markdown("""
    These plots compare the distributions of the most drifted features between old and new data:
    - **Blue:** Old data distribution (70% of dataset)
    - **Red:** New data distribution (30% of dataset)
    - **Overlap:** Indicates stability, separation indicates drift
    """)
    
    if drift_report['distribution_plots']:
        for feature, fig in drift_report['distribution_plots'].items():
            st.plotly_chart(fig, use_container_width=True)
            st.markdown(f"**{feature} Distribution Analysis:**")
            if feature in drift_report['ks_results']:
                result = drift_report['ks_results'][feature]
                st.markdown(f"- KS Statistic: {result['ks_statistic']:.4f}")
                st.markdown(f"- P-Value: {result['p_value']:.4f}")
                st.markdown(f"- Mean Change: {result['new_mean'] - result['old_mean']:.4f}")
                st.markdown(f"- Drift Status: {'Detected' if result['drift_detected'] else 'Not Detected'}")
            st.markdown("---")
    else:
        st.warning("No distribution plots available.")

with tab3:
    st.subheader("Model Performance Drift")
    st.markdown("""
    This section shows how model performance changes between old and new data:
    - **Accuracy:** Overall prediction accuracy
    - **F1-Score:** Weighted average F1-score
    - **Drift:** Difference between old and new performance
    """)
    
    # Performance metrics
    perf_drift = drift_report['performance_drift']
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Accuracy Comparison:**")
        st.metric("Old Data Accuracy", f"{perf_drift['old_accuracy']:.3f}")
        st.metric("New Data Accuracy", f"{perf_drift['new_accuracy']:.3f}")
        st.metric("Accuracy Drift", f"{perf_drift['accuracy_drift']:.3f}")
    
    with col2:
        st.markdown("**F1-Score Comparison:**")
        st.metric("Old Data F1-Score", f"{perf_drift['old_f1']:.3f}")
        st.metric("New Data F1-Score", f"{perf_drift['new_f1']:.3f}")
        st.metric("F1-Score Drift", f"{perf_drift['f1_drift']:.3f}")
    
    # Performance drift visualization
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        name='Accuracy',
        x=['Old Data', 'New Data'],
        y=[perf_drift['old_accuracy'], perf_drift['new_accuracy']],
        marker_color='blue'
    ))
    
    fig.add_trace(go.Bar(
        name='F1-Score',
        x=['Old Data', 'New Data'],
        y=[perf_drift['old_f1'], perf_drift['new_f1']],
        marker_color='green'
    ))
    
    fig.update_layout(
        title="Model Performance Comparison",
        xaxis_title="Data Period",
        yaxis_title="Performance Metric",
        barmode='group',
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Performance drift assessment
    acc_drift_abs = abs(perf_drift['accuracy_drift'])
    f1_drift_abs = abs(perf_drift['f1_drift'])
    
    st.markdown("**Performance Drift Assessment:**")
    if acc_drift_abs < 0.05 and f1_drift_abs < 0.05:
        st.markdown(" Performance is stable - no significant drift detected.")
    elif acc_drift_abs < 0.1 and f1_drift_abs < 0.1:
        st.markdown(" Moderate performance drift - consider monitoring and potential retraining.")
    else:
        st.markdown(" Significant performance drift - immediate retraining recommended.")

with tab4:
    st.subheader("Drift Recommendations")
    st.markdown("""
    Based on the drift analysis, here are the recommendations for managing concept drift:
    """)
    
    if recommendations:
        for i, rec in enumerate(recommendations, 1):
            st.markdown(f"**{i}.** {rec}")
    else:
        st.markdown("No specific recommendations - the model appears stable.")
    
    # Additional drift management strategies
    st.markdown("**Drift Management Strategies:**")
    st.markdown("""
    1. **Continuous Monitoring:** Regularly check for drift using automated systems
    2. **Adaptive Learning:** Use online learning to adapt to gradual drift
    3. **Ensemble Methods:** Combine multiple models to handle different drift patterns
    4. **Window-based Training:** Use sliding windows for recent data
    5. **Trigger-based Retraining:** Retrain when drift exceeds thresholds
    """)
    
    # Implementation suggestions
    st.markdown("**Implementation Suggestions:**")
    st.markdown("""
    1. **Set Up Alerts:** Configure automated alerts for drift detection
    2. **Create Retraining Pipeline:** Automate model retraining process
    3. **Version Control:** Maintain multiple model versions for A/B testing
    4. **Documentation:** Track drift patterns and retraining history
    5. **Monitoring Dashboard:** Create real-time drift monitoring interface
    """)

# Trustworthy AI Principles
st.header(" Trustworthy AI Principles")

col1, col2 = st.columns(2)

with col1:
    st.markdown("**Reliability Benefits:**")
    st.markdown("- **Consistent Performance:** Model maintains accuracy over time")
    st.markdown("- **Early Detection:** Identify issues before they impact users")
    st.markdown("- **Proactive Management:** Address drift before failure occurs")
    st.markdown("- **Trust Building:** Demonstrate ongoing model reliability")

with col2:
    st.markdown("**Drift Detection Methods:**")
    st.markdown("- **Statistical Tests:** KS test for distribution changes")
    st.markdown("- **Performance Monitoring:** Track accuracy and F1-score")
    st.markdown("- **Feature Analysis:** Monitor individual feature drift")
    st.markdown("- **Automated Alerts:** Real-time drift notification system")

# Technical Details
with st.expander(" Technical Details"):
    st.markdown("**Drift Detection Methods:**")
    st.markdown("- **Kolmogorov-Smirnov Test:** Statistical test for distribution differences")
    st.markdown("- **P-Value Threshold:** 0.05 for statistical significance")
    st.markdown("- **Data Split:** 70% old data, 30% new data for comparison")
    st.markdown("- **Features Monitored:** 11 key network parameters")
    
    st.markdown("**Performance Metrics:**")
    st.markdown("- **Accuracy:** Overall prediction accuracy")
    st.markdown("- **F1-Score:** Weighted average F1-score across classes")
    st.markdown("- **Drift Threshold:** 5% performance change for moderate drift")
    st.markdown("- **Critical Threshold:** 10% performance change for high drift")
    
    st.markdown("**Simulation Method:**")
    st.markdown("- **Synthetic Targets:** Rule-based classification for comparison")
    st.markdown("- **Noise Injection:** 15% noise in new data to simulate drift")
    st.markdown("- **Random Seed:** Fixed seed for reproducible results")

# Footer
st.markdown("---")
st.markdown("""
**Note:** Concept drift detection helps ensure that the AI model remains accurate and reliable 
as network conditions evolve over time. Regular drift monitoring is essential for maintaining 
trust in AI systems deployed in dynamic telecommunications environments.
""")
