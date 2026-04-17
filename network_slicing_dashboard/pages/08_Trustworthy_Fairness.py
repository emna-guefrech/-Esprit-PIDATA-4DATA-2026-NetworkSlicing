import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from utils.fairness import create_bias_detection_report

# Page config
st.set_page_config(
    page_title="Trustworthy AI - Bias & Fairness",
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
    .fairness-good {
        background-color: #D1FAE5;
        border-left: 4px solid #10B981;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 0.5rem;
    }
    .fairness-moderate {
        background-color: #FEF3C7;
        border-left: 4px solid #F59E0B;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 0.5rem;
    }
    .fairness-poor {
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
st.title("Bias & Fairness Detection")

# CRISP-DM Phase indicator
st.markdown('<div class="crisp-dm-phase">CRISP-DM Phase: Evaluation - Fairness Assessment</div>', unsafe_allow_html=True)

st.markdown("""
**Business Objective:** Detect and analyze potential bias in the 6G network congestion classification model 
across different slice types. This implements the Trustworthy AI principle of **Fairness** by ensuring 
the model treats all slice types equitably and doesn't favor or discriminate against any particular network slice.
""")

# Load dataset and create report
dataset_path = "C:/Users/EYA/PI/network_slicing_dataset_6G_final.csv"
fairness_report = create_bias_detection_report(dataset_path)

if not fairness_report:
    st.error("Could not load fairness analysis data. Please ensure the dataset is available.")
    st.stop()

# Fairness verdict
verdict = fairness_report['fairness_verdict']
color = fairness_report['fairness_color']
recommendations = fairness_report['recommendations']

# Display fairness verdict
st.header(" Fairness Assessment")

if verdict == "Fair":
    st.markdown(f'<div class="fairness-good">', unsafe_allow_html=True)
    st.markdown(f"###  Fair Model")
    st.markdown("The model shows fair behavior across all slice types.")
    st.markdown('</div>', unsafe_allow_html=True)
elif verdict == "Moderately Fair":
    st.markdown(f'<div class="fairness-moderate">', unsafe_allow_html=True)
    st.markdown(f"###  Moderately Fair Model")
    st.markdown("The model shows some bias but is generally acceptable.")
    st.markdown('</div>', unsafe_allow_html=True)
else:
    st.markdown(f'<div class="fairness-poor">', unsafe_allow_html=True)
    st.markdown(f"###  Biased Model")
    st.markdown("The model shows significant bias across slice types.")
    st.markdown('</div>', unsafe_allow_html=True)

# Key metrics
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Samples", fairness_report['total_samples'])

with col2:
    st.metric("Slice Types", len(fairness_report['slice_types']))

with col3:
    parity_diff = fairness_report['parity_metrics']['parity_difference']
    st.metric("Parity Difference", f"{parity_diff:.3f}")

with col4:
    st.metric("Fairness Verdict", verdict)

# Detailed analysis
st.header(" Detailed Fairness Analysis")

tab1, tab2, tab3, tab4 = st.tabs([" Class Distribution", " Statistical Parity", " Performance Metrics", " Recommendations"])

with tab1:
    st.subheader("Class Distribution Across Slice Types")
    st.markdown("""
    This chart shows how the predicted classes are distributed across different 6G slice types:
    - **Equal distribution** indicates fairness
    - **Imbalanced distribution** may indicate bias
    """)
    
    st.plotly_chart(fairness_report['class_distribution'], use_container_width=True)
    
    st.markdown("**Analysis:**")
    slice_counts = pd.Series({
        slice_type: (fairness_report['parity_metrics']['slice_rates'].get(slice_type, 0) * 
                     fairness_report['total_samples'] / len(fairness_report['slice_types']))
        for slice_type in fairness_report['slice_types']
    })
    
    st.write("**Sample counts per slice type:**")
    for slice_type, count in slice_counts.items():
        st.write(f"- {slice_type}: {count:.0f} samples")

with tab2:
    st.subheader("Statistical Parity Analysis")
    st.markdown("""
    Statistical parity measures whether different slice types receive similar outcomes:
    - **Low difference (< 0.1):** Good fairness
    - **Moderate difference (0.1-0.2):** Acceptable fairness
    - **High difference (> 0.2):** Potential bias
    """)
    
    # Create parity comparison chart
    slice_rates = fairness_report['parity_metrics']['slice_rates']
    slice_names = list(slice_rates.keys())
    rate_values = list(slice_rates.values())
    
    fig = go.Figure(data=[
        go.Bar(
            x=slice_names,
            y=rate_values,
            marker_color=['green' if abs(r - np.mean(rate_values)) < 0.1 else 'orange' if abs(r - np.mean(rate_values)) < 0.2 else 'red' for r in rate_values],
            hovertemplate='<b>%{x}</b><br>Rate: %{y:.3f}<extra></extra>'
        )
    ])
    
    fig.add_hline(y=np.mean(rate_values), line_dash="dash", line_color="gray", 
                  annotation_text=f"Mean Rate: {np.mean(rate_values):.3f}")
    
    fig.update_layout(
        title="Critical Prediction Rate by Slice Type",
        xaxis_title="Slice Types",
        yaxis_title="Critical Prediction Rate",
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Parity metrics
    st.markdown("**Statistical Parity Metrics:**")
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Maximum Rate", f"{fairness_report['parity_metrics']['max_rate']:.3f}")
        st.metric("Minimum Rate", f"{fairness_report['parity_metrics']['min_rate']:.3f}")
    
    with col2:
        st.metric("Parity Difference", f"{parity_diff:.3f}")
        st.metric("Fairness Level", "Good" if parity_diff < 0.1 else "Moderate" if parity_diff < 0.2 else "Poor")

with tab3:
    st.subheader("Performance Metrics by Slice Type")
    st.markdown("""
    This heatmap shows how model performance varies across different slice types:
    - **Consistent performance** indicates fairness
    - **Variable performance** may indicate bias
    """)
    
    st.plotly_chart(fairness_report['fairness_heatmap'], use_container_width=True)
    
    # Detailed metrics table
    st.markdown("**Detailed Performance Metrics:**")
    
    metrics_data = []
    for slice_type, metrics in fairness_report['per_class_metrics'].items():
        metrics_data.append({
            'Slice Type': slice_type,
            'Precision': f"{metrics['precision']:.3f}",
            'Recall': f"{metrics['recall']:.3f}",
            'F1-Score': f"{metrics['f1_score']:.3f}",
            'Accuracy': f"{metrics['accuracy']:.3f}",
            'Support': metrics['support']
        })
    
    metrics_df = pd.DataFrame(metrics_data)
    st.dataframe(metrics_df, use_container_width=True)
    
    # Performance variation analysis
    f1_scores = [metrics['f1_score'] for metrics in fairness_report['per_class_metrics'].values()]
    f1_std = np.std(f1_scores)
    f1_mean = np.mean(f1_scores)
    
    st.markdown("**Performance Variation:**")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Mean F1-Score", f"{f1_mean:.3f}")
    
    with col2:
        st.metric("F1-Score Std Dev", f"{f1_std:.3f}")
    
    with col3:
        variation_level = "Low" if f1_std < 0.05 else "Moderate" if f1_std < 0.1 else "High"
        st.metric("Variation Level", variation_level)

with tab4:
    st.subheader("Fairness Recommendations")
    st.markdown("""
    Based on the fairness analysis, here are the recommendations for improving model fairness:
    """)
    
    if recommendations:
        for i, rec in enumerate(recommendations, 1):
            st.markdown(f"**{i}.** {rec}")
    else:
        st.markdown("No specific recommendations - the model appears to be fair.")
    
    # Additional fairness techniques
    st.markdown("**Additional Fairness Techniques:**")
    st.markdown("""
    - **Re-weighting:** Adjust sample weights to balance slice type representation
    - **Re-sampling:** Over-sample or under-sample to balance the dataset
    - **Fairness Constraints:** Add fairness constraints to the model training process
    - **Adversarial Debiasing:** Use adversarial training to reduce bias
    - **Post-processing:** Adjust predictions to improve fairness
    """)
    
    # Implementation suggestions
    st.markdown("**Implementation Suggestions:**")
    st.markdown("""
    1. **Data Collection:** Ensure balanced representation of all slice types
    2. **Model Training:** Use fairness-aware training algorithms
    3. **Regular Monitoring:** Continuously monitor fairness metrics
    4. **Documentation:** Document fairness considerations and decisions
    5. **Stakeholder Communication:** Communicate fairness results to stakeholders
    """)

# Trustworthy AI Principles
st.header(" Trustworthy AI Principles")

col1, col2 = st.columns(2)

with col1:
    st.markdown("**Fairness Benefits:**")
    st.markdown("- **Equitable Treatment:** All slice types receive fair treatment")
    st.markdown("- **Regulatory Compliance:** Meet fairness regulations and standards")
    st.markdown("- **User Trust:** Build confidence in AI systems")
    st.markdown("- **Social Responsibility:** Ensure ethical AI deployment")

with col2:
    st.markdown("**Bias Detection Methods:**")
    st.markdown("- **Statistical Parity:** Equal outcomes across groups")
    st.markdown("- **Performance Metrics:** Consistent performance across slice types")
    st.markdown("- **Distribution Analysis:** Balanced class distributions")
    st.markdown("- **Continuous Monitoring:** Ongoing fairness assessment")

# Technical Details
with st.expander(" Technical Details"):
    st.markdown("**Fairness Metrics:**")
    st.markdown("- **Statistical Parity Difference:** Maximum difference in positive prediction rates")
    st.markdown("- **Performance Consistency:** Standard deviation of F1-scores across slice types")
    st.markdown("- **Distribution Balance:** Equal representation of classes across slice types")
    
    st.markdown("**Analysis Method:**")
    st.markdown("- **Dataset:** 10K samples from 6G network slicing dataset")
    st.markdown("- **Slice Types:** ERLLC, umMTC, MBRLLC, mURLLC, feMBB")
    st.markdown("- **Classes:** Normal, Light, Critical")
    st.markdown("- **Fairness Threshold:** Parity difference < 0.1 for good fairness")

# Footer
st.markdown("---")
st.markdown("""
**Note:** Fairness analysis helps ensure that the AI model treats all 6G network slice types equitably. 
Regular fairness monitoring is essential for maintaining trust and ensuring ethical AI deployment 
in telecommunications networks.
""")
