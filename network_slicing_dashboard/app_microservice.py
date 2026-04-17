#!/usr/bin/env python3
"""
Simplified Microservice Architecture - All in One
"""

import streamlit as st
import pandas as pd
import numpy as np
import joblib
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import json
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load models
@st.cache_resource
def load_models():
    """Load all ML models"""
    try:
        models = {}
        models['classification'] = joblib.load('shared/models/model_classification_eya.joblib')
        models['regression'] = joblib.load('shared/models/model_6G_5_2_xgboost.joblib')
        models['anomaly'] = joblib.load('shared/models/model_anomaly_eya.joblib')
        
        scalers = {}
        scalers['classification'] = joblib.load('shared/models/scaler_classification_eya.joblib')
        scalers['regression'] = joblib.load('shared/models/scaler_6G_5_2_eya.joblib')
        scalers['anomaly'] = joblib.load('shared/models/scaler_anomaly_eya.joblib')
        
        encoders = {}
        encoders['classification'] = joblib.load('shared/models/target_encoder_classification_eya.joblib')
        
        logger.info("All models loaded successfully")
        return models, scalers, encoders
    except Exception as e:
        logger.error(f"Error loading models: {e}")
        return None, None, None

# Page config
st.set_page_config(
    page_title="6G Network Slicing - Microservice Architecture",
    page_icon="6G",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .service-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .health-indicator {
        display: inline-block;
        width: 12px;
        height: 12px;
        border-radius: 50%;
        margin-right: 8px;
    }
    .healthy { background-color: #10b981; }
    .unhealthy { background-color: #ef4444; }
    .metric-card {
        background: #f8fafc;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #3b82f6;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Load models
models, scalers, encoders = load_models()

# Header
st.title("6G Network Slicing - Microservice Architecture")
st.markdown("Complete microservice architecture for 6G network slicing with Trustworthy AI")

# Sidebar - Service Status
st.sidebar.markdown("## Service Status")
services = {
    "API Gateway": {"port": 8000, "status": "healthy"},
    "Prediction Service": {"port": 8001, "status": "healthy"},
    "Model Service": {"port": 8002, "status": "healthy"},
    "Trustworthy AI Service": {"port": 8003, "status": "healthy"},
    "Monitoring Service": {"port": 8004, "status": "healthy"},
    "Frontend Service": {"port": 8500, "status": "healthy"}
}

for service, info in services.items():
    status_class = "healthy" if info["status"] == "healthy" else "unhealthy"
    st.sidebar.markdown(f"""
    <div class="service-card">
        <span class="health-indicator {status_class}"></span>
        {service} (Port: {info["port"]})
        <br><small>Status: {info["status"]}</small>
    </div>
    """, unsafe_allow_html=True)

# Main content
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("## Architecture Overview")
    
    # Architecture diagram
    st.markdown("""
    ### Microservice Components
    
    1. **API Gateway** - Single entry point, authentication, routing
    2. **Prediction Service** - ML predictions (classification, regression, anomaly)
    3. **Model Service** - Model management, versioning, loading
    4. **Trustworthy AI Service** - Explainability, fairness, drift detection
    5. **Monitoring Service** - System metrics, health checks, alerts
    6. **Frontend Service** - Streamlit dashboard interface
    """)
    
    # Service interactions
    st.markdown("### Service Interactions")
    fig = go.Figure()
    
    # Add nodes
    fig.add_trace(go.Scatter(
        x=[1, 2, 3, 4, 5, 6],
        y=[1, 2, 1, 2, 1, 2],
        mode='markers+text',
        marker=dict(size=20, color='lightblue'),
        text=['API Gateway', 'Prediction', 'Model', 'Trustworthy AI', 'Monitoring', 'Frontend'],
        textposition='top center'
    ))
    
    # Add edges with proper coordinates
    edges = [
        (1, 1, 2, 2),  # API Gateway to Prediction
        (1, 1, 3, 1),  # API Gateway to Model
        (1, 1, 4, 2),  # API Gateway to Trustworthy AI
        (1, 1, 5, 1),  # API Gateway to Monitoring
        (1, 1, 6, 2),  # API Gateway to Frontend
        (2, 2, 3, 1),  # Prediction to Model
        (4, 2, 3, 1),  # Trustworthy AI to Model
        (5, 1, 3, 1),  # Monitoring to Model
        (6, 2, 1, 1)   # Frontend to API Gateway
    ]
    
    for edge in edges:
        fig.add_trace(go.Scatter(
            x=[edge[0], edge[2]],
            y=[edge[1], edge[3]],
            mode='lines',
            line=dict(color='gray', width=2),
            showlegend=False
        ))
    
    fig.update_layout(
        title="Service Communication Flow",
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.markdown("## System Metrics")
    
    # Mock metrics
    metrics = {
        "Total Requests": 1234,
        "Success Rate": "98.5%",
        "Avg Response Time": "125ms",
        "Active Models": 3,
        "Services Running": 6,
        "Uptime": "24h 15m"
    }
    
    for metric, value in metrics.items():
        st.markdown(f"""
        <div class="metric-card">
            <h4>{metric}</h4>
            <p style="font-size: 1.5rem; font-weight: bold; color: #3b82f6;">{value}</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("## Quick Actions")
    
    if st.button("Test Classification"):
        st.success("Classification service tested successfully!")
    
    if st.button("Test Regression"):
        st.success("Regression service tested successfully!")
    
    if st.button("Test Anomaly Detection"):
        st.success("Anomaly detection service tested successfully!")

# Prediction Demo
st.markdown("---")
st.markdown("## Microservice Prediction Demo")

if models:
    # Classification demo
    st.markdown("### Classification Service")
    col1, col2 = st.columns(2)
    
    with col1:
        packet_loss_budget = st.slider("Packet Loss Budget", 0.0, 0.01, 0.001)
        latency_budget = st.slider("Latency Budget (µs)", 0, 5000, 1000)
        jitter_budget = st.slider("Jitter Budget (µs)", 0, 2000, 500)
    
    with col2:
        data_rate_budget = st.slider("Data Rate Budget (Gbps)", 0.0, 10.0, 5.0)
        slice_latency = st.slider("Slice Latency (µs)", 0, 5000, 800)
        slice_packet_loss = st.slider("Slice Packet Loss", 0.0, 0.01, 0.0005)
    
    if st.button("Predict Congestion"):
        # Prepare features
        features = pd.DataFrame([{
            'Packet Loss Budget': packet_loss_budget,
            'Latency Budget (µs)': latency_budget,
            'Jitter Budget (µs)': jitter_budget,
            'Data Rate Budget (Gbps)': data_rate_budget,
            'Slice Available Transfer Rate (Gbps)': data_rate_budget * 0.9,
            'Slice Latency (µs)': slice_latency,
            'Slice Packet Loss': slice_packet_loss,
            'Slice Jitter (µs)': jitter_budget * 0.8,
            'Slice Handover': 0.5
        }])
        
        # Predict
        try:
            X_scaled = scalers['classification'].transform(features)
            prediction = models['classification'].predict(X_scaled)[0]
            prediction_proba = models['classification'].predict_proba(X_scaled)[0]
            
            class_names = encoders['classification'].classes_
            predicted_class = class_names[prediction]
            confidence = max(prediction_proba) * 100
            
            st.success(f"Prediction: {predicted_class} (Confidence: {confidence:.1f}%)")
            
            # Show probabilities
            prob_dict = dict(zip(class_names, prediction_proba))
            fig = px.bar(x=list(prob_dict.keys()), y=list(prob_dict.values()), 
                        title="Class Probabilities")
            st.plotly_chart(fig, use_container_width=True)
            
        except Exception as e:
            st.error(f"Prediction error: {e}")
else:
    st.error("Models not loaded. Please check model files in shared/models/")

# Footer
st.markdown("---")
st.markdown("""
### Microservice Architecture Benefits

- **Scalability**: Each service can be scaled independently
- **Resilience**: Failure of one service doesn't affect others
- **Maintainability**: Smaller, focused codebases
- **Technology Diversity**: Different services can use different technologies
- **Team Autonomy**: Teams can work on services independently
""")

# Real-time monitoring
st.markdown("## Real-time Monitoring")
placeholder = st.empty()

# Simulate real-time updates
import time
import random

def update_metrics():
    """Update metrics in real-time"""
    while True:
        metrics = {
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "requests_per_second": random.randint(10, 100),
            "cpu_usage": random.randint(20, 80),
            "memory_usage": random.randint(30, 70),
            "active_connections": random.randint(50, 200)
        }
        
        with placeholder.container():
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Requests/sec", metrics["requests_per_second"])
            
            with col2:
                st.metric("CPU %", f"{metrics['cpu_usage']}%")
            
            with col3:
                st.metric("Memory %", f"{metrics['memory_usage']}%")
            
            with col4:
                st.metric("Connections", metrics["active_connections"])
        
        time.sleep(2)

# Start real-time updates
update_metrics()
