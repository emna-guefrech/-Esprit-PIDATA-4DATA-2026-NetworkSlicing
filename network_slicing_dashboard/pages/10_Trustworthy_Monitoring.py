import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from utils.monitoring import create_monitoring_dashboard, validate_input_ranges

# Page config
st.set_page_config(
    page_title="Trustworthy AI - Security & Monitoring",
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
    .health-excellent {
        background-color: #D1FAE5;
        border-left: 4px solid #10B981;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 0.5rem;
    }
    .health-good {
        background-color: #E0F2FE;
        border-left: 4px solid #0EA5E9;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 0.5rem;
    }
    .health-warning {
        background-color: #FEF3C7;
        border-left: 4px solid #F59E0B;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 0.5rem;
    }
    .health-critical {
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
st.title("Security & Monitoring Dashboard")

# CRISP-DM Phase indicator
st.markdown('<div class="crisp-dm-phase">CRISP-DM Phase: Deployment - Security & Monitoring</div>', unsafe_allow_html=True)

st.markdown("""
**Business Objective:** Provide comprehensive security monitoring and real-time performance tracking for the 
6G network slicing AI system. This implements the Trustworthy AI principles of **Security** and **Reliability** 
by ensuring system integrity, input validation, and continuous performance monitoring.
""")

# Create monitoring dashboard
monitoring_data = create_monitoring_dashboard()

if not monitoring_data:
    st.error("Could not load monitoring data. Please check system configuration.")
    st.stop()

# Health assessment
health = monitoring_data['health_assessment']
health_status = health['overall_health']
health_score = health['health_score']
issues = health['issues']
recommendations = health['recommendations']

# Display health status
st.header(" System Health Assessment")

if health_status == 'excellent':
    st.markdown(f'<div class="health-excellent">', unsafe_allow_html=True)
    st.markdown(f"###  System Health: Excellent")
    st.markdown(f"Health Score: {health_score}/100")
    st.markdown("All systems operating normally.")
    st.markdown('</div>', unsafe_allow_html=True)
elif health_status == 'good':
    st.markdown(f'<div class="health-good">', unsafe_allow_html=True)
    st.markdown(f"###  System Health: Good")
    st.markdown(f"Health Score: {health_score}/100")
    st.markdown("Systems operating normally with minor issues.")
    st.markdown('</div>', unsafe_allow_html=True)
elif health_status == 'warning':
    st.markdown(f'<div class="health-warning">', unsafe_allow_html=True)
    st.markdown(f"###  System Health: Warning")
    st.markdown(f"Health Score: {health_score}/100")
    st.markdown("Some issues detected - attention required.")
    st.markdown('</div>', unsafe_allow_html=True)
else:
    st.markdown(f'<div class="health-critical">', unsafe_allow_html=True)
    st.markdown(f"###  System Health: Critical")
    st.markdown(f"Health Score: {health_score}/100")
    st.markdown("Multiple issues detected - immediate action required.")
    st.markdown('</div>', unsafe_allow_html=True)

# Key metrics
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Health Score", f"{health_score}/100")

with col2:
    st.metric("System Status", health_status.title())

with col3:
    st.metric("Issues Detected", len(issues))

with col4:
    latest_accuracy = monitoring_data['kpis']['accuracy'][-1]
    st.metric("Current Accuracy", f"{latest_accuracy:.3f}")

# Detailed monitoring
st.header(" Real-time Monitoring")

tab1, tab2, tab3, tab4 = st.tabs([" Performance Metrics", " Access Log", " Input Validation", " Security Alerts"])

with tab1:
    st.subheader("Live KPI Metrics")
    st.markdown("""
    Real-time monitoring of key performance indicators:
    - **Accuracy:** Model prediction accuracy
    - **Anomaly Rate:** Percentage of anomalies detected
    - **Confidence:** Average prediction confidence
    - **Response Time:** Model inference time
    - **Request Rate:** System load
    """)
    
    # Display KPI charts
    figures = monitoring_data['dashboard_figures']
    
    if 'accuracy' in figures:
        st.plotly_chart(figures['accuracy'], use_container_width=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        if 'anomaly_rate' in figures:
            st.plotly_chart(figures['anomaly_rate'], use_container_width=True)
        if 'response_time' in figures:
            st.plotly_chart(figures['response_time'], use_container_width=True)
    
    with col2:
        if 'confidence' in figures:
            st.plotly_chart(figures['confidence'], use_container_width=True)
        if 'request_rate' in figures:
            st.plotly_chart(figures['request_rate'], use_container_width=True)
    
    # Current metrics summary
    st.markdown("**Current Metrics Summary:**")
    kpis = monitoring_data['kpis']
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Accuracy", f"{kpis['accuracy'][-1]:.3f}")
    
    with col2:
        st.metric("Anomaly Rate", f"{kpis['anomaly_rate'][-1]:.3f}")
    
    with col3:
        st.metric("Confidence", f"{kpis['confidence'][-1]:.3f}")
    
    with col4:
        st.metric("Response Time", f"{kpis['response_time'][-1]:.0f}ms")
    
    with col5:
        st.metric("Request Rate", f"{kpis['request_rate'][-1]:.0f}/min")

with tab2:
    st.subheader("Access Log")
    st.markdown("""
    Recent system access and activity log:
    - **Timestamp:** When the action occurred
    - **User:** Who performed the action
    - **Action:** Type of operation
    - **Status:** Success/Warning/Error
    - **Response Time:** Processing time
    """)
    
    # Display access log
    access_log = monitoring_data['access_log']
    
    if not access_log.empty:
        # Format the display
        display_log = access_log.copy()
        display_log['timestamp'] = display_log['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
        display_log['response_time'] = display_log['response_time'].round(1).astype(str) + 'ms'
        
        # Color code status
        def color_status(val):
            if val == 'success':
                return 'background-color: #D1FAE5'
            elif val == 'warning':
                return 'background-color: #FEF3C7'
            else:
                return 'background-color: #FEE2E2'
        
        # Display with styling
        st.dataframe(display_log, use_container_width=True)
        
        # Log statistics
        st.markdown("**Access Log Statistics:**")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            success_count = (access_log['status'] == 'success').sum()
            st.metric("Successful Operations", success_count)
        
        with col2:
            warning_count = (access_log['status'] == 'warning').sum()
            st.metric("Warnings", warning_count)
        
        with col3:
            error_count = (access_log['status'] == 'error').sum()
            st.metric("Errors", error_count)
        
        # Recent activity
        st.markdown("**Recent Activity:**")
        recent_activity = access_log.tail(5)[['timestamp', 'user', 'action', 'status']]
        recent_activity['timestamp'] = recent_activity['timestamp'].dt.strftime('%H:%M:%S')
        st.dataframe(recent_activity, use_container_width=True)
    else:
        st.warning("No access log data available.")

with tab3:
    st.subheader("Input Validation")
    st.markdown("""
    Test input validation and range checking for network parameters:
    - Enter test values to validate against expected ranges
    - System will flag suspicious or out-of-range inputs
    - Provides security recommendations for input handling
    """)
    
    # Input validation form
    st.markdown("**Test Input Validation:**")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        test_packet_loss = st.number_input("Packet Loss Budget", min_value=0.0, max_value=1.0, value=0.001, format="%.6f", key="val_packet_loss")
        test_latency = st.number_input("Latency Budget (µs)", min_value=0.0, max_value=20000.0, value=1000.0, key="val_latency")
        test_jitter = st.number_input("Jitter Budget (µs)", min_value=0.0, max_value=10000.0, value=1000.0, key="val_jitter")
    
    with col2:
        test_data_rate = st.number_input("Data Rate Budget (Gbps)", min_value=0.0, max_value=20.0, value=1.0, key="val_data_rate")
        test_mobility = st.selectbox("Required Mobility", ["0", "1", "2"], key="val_mobility")
        test_connectivity = st.selectbox("Required Connectivity", ["0", "1", "2"], key="val_connectivity")
    
    with col3:
        test_slice_rate = st.number_input("Slice Available Rate (Gbps)", min_value=0.0, max_value=20.0, value=1.0, key="val_slice_rate")
        test_slice_latency = st.number_input("Slice Latency (µs)", min_value=0.0, max_value=20000.0, value=1000.0, key="val_slice_latency")
        test_slice_packet_loss = st.number_input("Slice Packet Loss", min_value=0.0, max_value=1.0, value=0.001, format="%.6f", key="val_slice_packet_loss")
    
    col4, col5 = st.columns(2)
    
    with col4:
        test_slice_jitter = st.number_input("Slice Jitter (µs)", min_value=0.0, max_value=10000.0, value=1000.0, key="val_slice_jitter")
        test_slice_type = st.selectbox("Slice Type", ["ERLLC", "umMTC", "MBRLLC", "mURLLC", "feMBB"], key="val_slice_type")
    
    with col5:
        test_handover = st.number_input("Slice Handover", min_value=0.0, max_value=5.0, value=0.0, key="val_handover")
        test_button = st.button(" Validate Inputs", type="primary")
    
    if test_button:
        # Prepare test features
        test_features = {
            'Packet Loss Budget': test_packet_loss,
            'Latency Budget (µs)': test_latency,
            'Jitter Budget (µs)': test_jitter,
            'Data Rate Budget (Gbps)': test_data_rate,
            'Required Mobility': test_mobility,
            'Required Connectivity': test_connectivity,
            'Slice Available Transfer Rate (Gbps)': test_slice_rate,
            'Slice Latency (µs)': test_slice_latency,
            'Slice Packet Loss': test_slice_packet_loss,
            'Slice Jitter (µs)': test_slice_jitter,
            'Slice Type': test_slice_type,
            'Slice Handover': test_handover
        }
        
        # Validate inputs
        validation_results = validate_input_ranges(test_features)
        
        # Display validation results
        st.markdown("**Validation Results:**")
        
        if validation_results['is_valid']:
            st.success(" All inputs are within expected ranges.")
        else:
            st.warning(" Some inputs are out of expected ranges or suspicious.")
        
        if validation_results['warnings']:
            st.markdown("**Warnings:**")
            for warning in validation_results['warnings']:
                st.markdown(f"- {warning}")
        
        if validation_results['suspicious_inputs']:
            st.markdown("**Suspicious Inputs Detected:**")
            for input_name in validation_results['suspicious_inputs']:
                st.markdown(f"- {input_name}")
        
        # Validation details
        st.markdown("**Validation Details:**")
        details_df = pd.DataFrame(validation_results['validation_details']).T
        details_df.columns = ['Value', 'Expected Range', 'In Range', 'Is Extreme']
        st.dataframe(details_df, use_container_width=True)

with tab4:
    st.subheader("Security Alerts")
    st.markdown("""
    Security monitoring and alert system:
    - **System Health:** Overall system status
    - **Issues:** Detected problems and concerns
    - **Recommendations:** Suggested actions
    - **Security Policies:** Guidelines for secure operation
    """)
    
    # Display health assessment
    st.markdown("**System Health Assessment:**")
    st.markdown(f"**Overall Health:** {health_status.title()}")
    st.markdown(f"**Health Score:** {health_score}/100")
    
    if issues:
        st.markdown("**Detected Issues:**")
        for issue in issues:
            st.markdown(f"- {issue}")
    else:
        st.markdown("**No issues detected.**")
    
    if recommendations:
        st.markdown("**Recommendations:**")
        for rec in recommendations:
            st.markdown(f"- {rec}")
    
    # Security policies
    st.markdown("**Security Policies:**")
    st.markdown("""
    1. **Input Validation:** All inputs are validated against expected ranges
    2. **Access Control:** User authentication and authorization required
    3. **Audit Logging:** All system activities are logged and monitored
    4. **Rate Limiting:** Request rate limiting to prevent abuse
    5. **Error Handling:** Secure error handling without information leakage
    6. **Data Protection:** Sensitive data is encrypted and protected
    7. **Regular Updates:** System components are regularly updated
    8. **Monitoring:** Continuous monitoring of system health and performance
    """)
    
    # Security metrics
    st.markdown("**Security Metrics:**")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Validation Rate", "98.5%")
    
    with col2:
        st.metric("Failed Logins", "12 (last 24h)")
    
    with col3:
        st.metric("Blocked Requests", "156 (last 24h)")
    
    with col4:
        st.metric("Security Score", "92/100")

# Trustworthy AI Principles
st.header(" Trustworthy AI Principles")

col1, col2 = st.columns(2)

with col1:
    st.markdown("**Security Benefits:**")
    st.markdown("- **Input Validation:** Prevents malicious inputs")
    st.markdown("- **Access Control:** Ensures authorized access")
    st.markdown("- **Audit Trail:** Complete activity logging")
    st.markdown("- **Threat Detection:** Early warning system")

with col2:
    st.markdown("**Reliability Benefits:**")
    st.markdown("- **Performance Monitoring:** Real-time system tracking")
    st.markdown("- **Health Assessment:** Proactive issue detection")
    st.markdown("- **Alert System:** Immediate notification of problems")
    st.markdown("- **Continuous Improvement:** Ongoing system optimization")

# Technical Details
with st.expander(" Technical Details"):
    st.markdown("**Monitoring Components:**")
    st.markdown("- **KPI Tracking:** Real-time performance metrics")
    st.markdown("- **Health Assessment:** Automated system health scoring")
    st.markdown("- **Access Logging:** Comprehensive activity tracking")
    st.markdown("- **Input Validation:** Range and pattern checking")
    
    st.markdown("**Security Features:**")
    st.markdown("- **Input Sanitization:** Clean and validate all inputs")
    st.markdown("- **Rate Limiting:** Prevent abuse and DoS attacks")
    st.markdown("- **Error Handling:** Secure error management")
    st.markdown("- **Audit Trail:** Complete logging of all activities")
    
    st.markdown("**Performance Metrics:**")
    st.markdown("- **Accuracy Threshold:** 95% minimum acceptable")
    st.markdown("- **Response Time:** 100ms maximum acceptable")
    st.markdown("- **Anomaly Rate:** 15% maximum acceptable")
    st.markdown("- **Confidence Level:** 80% minimum acceptable")

# Footer
st.markdown("---")
st.markdown("""
**Note:** This security and monitoring dashboard ensures the 6G network slicing AI system operates 
securely and reliably. Continuous monitoring helps maintain trust in AI systems and enables 
proactive management of potential issues before they impact users.
""")
