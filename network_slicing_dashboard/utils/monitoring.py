import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import random
from typing import Dict, Any, List
import warnings
warnings.filterwarnings('ignore')

def generate_simulated_kpis(num_samples: int = 100) -> Dict[str, List[float]]:
    """
    Generate simulated KPI metrics for monitoring dashboard.
    
    Args:
        num_samples: Number of time points to generate
        
    Returns:
        Dictionary of KPI time series
    """
    try:
        # Generate time series with realistic patterns
        time_points = pd.date_range(
            start=datetime.now() - timedelta(hours=num_samples),
            end=datetime.now(),
            freq='1H'
        )
        
        # Simulate metrics with some noise and trends
        np.random.seed(42)
        
        # Accuracy (should be high with small variations)
        base_accuracy = 0.974
        accuracy = [base_accuracy + np.random.normal(0, 0.01) for _ in range(num_samples)]
        accuracy = np.clip(accuracy, 0.9, 1.0)
        
        # Anomaly rate (should be low)
        base_anomaly_rate = 0.1
        anomaly_rate = [base_anomaly_rate + np.random.normal(0, 0.02) for _ in range(num_samples)]
        anomaly_rate = np.clip(anomaly_rate, 0.0, 0.3)
        
        # Prediction confidence
        base_confidence = 0.85
        confidence = [base_confidence + np.random.normal(0, 0.05) for _ in range(num_samples)]
        confidence = np.clip(confidence, 0.7, 0.99)
        
        # Response time (in milliseconds)
        base_response_time = 50
        response_time = [base_response_time + np.random.exponential(10) for _ in range(num_samples)]
        response_time = np.clip(response_time, 10, 200)
        
        # Request rate (requests per minute)
        base_request_rate = 100
        request_rate = [base_request_rate + np.random.normal(0, 20) for _ in range(num_samples)]
        request_rate = np.clip(request_rate, 50, 200)
        
        return {
            'timestamps': time_points,
            'accuracy': accuracy,
            'anomaly_rate': anomaly_rate,
            'confidence': confidence,
            'response_time': response_time,
            'request_rate': request_rate
        }
        
    except Exception as e:
        st.error(f"Error generating simulated KPIs: {str(e)}")
        return {}

def create_kpi_dashboard(kpis: Dict[str, List[float]]) -> Dict[str, go.Figure]:
    """
    Create dashboard figures for KPI monitoring.
    
    Args:
        kpis: Dictionary of KPI time series
        
    Returns:
        Dictionary of Plotly figures
    """
    try:
        figures = {}
        
        # Accuracy over time
        fig_accuracy = go.Figure()
        fig_accuracy.add_trace(go.Scatter(
            x=kpis['timestamps'],
            y=kpis['accuracy'],
            mode='lines+markers',
            name='Accuracy',
            line=dict(color='green', width=2),
            hovertemplate='Time: %{x}<br>Accuracy: %{y:.3f}<extra></extra>'
        ))
        fig_accuracy.add_hline(y=0.95, line_dash="dash", line_color="orange", 
                              annotation_text="Min Threshold: 0.95")
        fig_accuracy.update_layout(
            title="Model Accuracy Over Time",
            xaxis_title="Time",
            yaxis_title="Accuracy",
            yaxis=dict(range=[0.9, 1.0]),
            height=300
        )
        figures['accuracy'] = fig_accuracy
        
        # Anomaly rate over time
        fig_anomaly = go.Figure()
        fig_anomaly.add_trace(go.Scatter(
            x=kpis['timestamps'],
            y=kpis['anomaly_rate'],
            mode='lines+markers',
            name='Anomaly Rate',
            line=dict(color='red', width=2),
            hovertemplate='Time: %{x}<br>Anomaly Rate: %{y:.3f}<extra></extra>'
        ))
        fig_anomaly.add_hline(y=0.15, line_dash="dash", line_color="orange", 
                              annotation_text="Max Threshold: 0.15")
        fig_anomaly.update_layout(
            title="Anomaly Detection Rate",
            xaxis_title="Time",
            yaxis_title="Anomaly Rate",
            yaxis=dict(range=[0.0, 0.3]),
            height=300
        )
        figures['anomaly_rate'] = fig_anomaly
        
        # Confidence over time
        fig_confidence = go.Figure()
        fig_confidence.add_trace(go.Scatter(
            x=kpis['timestamps'],
            y=kpis['confidence'],
            mode='lines+markers',
            name='Confidence',
            line=dict(color='blue', width=2),
            hovertemplate='Time: %{x}<br>Confidence: %{y:.3f}<extra></extra>'
        ))
        fig_confidence.add_hline(y=0.8, line_dash="dash", line_color="orange", 
                                annotation_text="Min Threshold: 0.8")
        fig_confidence.update_layout(
            title="Prediction Confidence",
            xaxis_title="Time",
            yaxis_title="Confidence",
            yaxis=dict(range=[0.7, 1.0]),
            height=300
        )
        figures['confidence'] = fig_confidence
        
        # Response time over time
        fig_response = go.Figure()
        fig_response.add_trace(go.Scatter(
            x=kpis['timestamps'],
            y=kpis['response_time'],
            mode='lines+markers',
            name='Response Time',
            line=dict(color='purple', width=2),
            hovertemplate='Time: %{x}<br>Response Time: %{y:.0f}ms<extra></extra>'
        ))
        fig_response.add_hline(y=100, line_dash="dash", line_color="orange", 
                              annotation_text="Max Threshold: 100ms")
        fig_response.update_layout(
            title="Model Response Time",
            xaxis_title="Time",
            yaxis_title="Response Time (ms)",
            height=300
        )
        figures['response_time'] = fig_response
        
        # Request rate over time
        fig_requests = go.Figure()
        fig_requests.add_trace(go.Scatter(
            x=kpis['timestamps'],
            y=kpis['request_rate'],
            mode='lines+markers',
            name='Request Rate',
            line=dict(color='orange', width=2),
            hovertemplate='Time: %{x}<br>Request Rate: %{y:.0f}/min<extra></extra>'
        ))
        fig_requests.update_layout(
            title="System Request Rate",
            xaxis_title="Time",
            yaxis_title="Requests per Minute",
            height=300
        )
        figures['request_rate'] = fig_requests
        
        return figures
        
    except Exception as e:
        st.error(f"Error creating KPI dashboard: {str(e)}")
        return {}

def validate_input_ranges(features: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate input parameter ranges and flag suspicious values.
    
    Args:
        features: Dictionary of input features
        
    Returns:
        Dictionary with validation results
    """
    try:
        validation_results = {
            'is_valid': True,
            'warnings': [],
            'suspicious_inputs': [],
            'validation_details': {}
        }
        
        # Define expected ranges for each feature
        expected_ranges = {
            'Packet Loss Budget': (0.0, 0.1),
            'Latency Budget (µs)': (100.0, 10000.0),
            'Jitter Budget (µs)': (50.0, 5000.0),
            'Data Rate Budget (Gbps)': (1.0, 10.0),
            'Required Mobility': (0, 2),
            'Required Connectivity': (0, 2),
            'Slice Available Transfer Rate (Gbps)': (0.1, 10.0),
            'Slice Latency (µs)': (10.0, 10000.0),
            'Slice Packet Loss': (0.0, 0.1),
            'Slice Jitter (µs)': (10.0, 5000.0),
            'Slice Handover': (0.0, 2.0)
        }
        
        # Validate each feature
        for feature, value in features.items():
            if feature in expected_ranges:
                min_val, max_val = expected_ranges[feature]
                
                # Check if value is in range
                if value < min_val or value > max_val:
                    validation_results['is_valid'] = False
                    validation_results['warnings'].append(f"{feature}: {value} (out of range [{min_val}, {max_val}])")
                    validation_results['suspicious_inputs'].append(feature)
                
                # Check for extreme values (even within range)
                if feature in ['Packet Loss Budget', 'Slice Packet Loss']:
                    if value > 0.05:
                        validation_results['warnings'].append(f"{feature}: {value:.6f} (extremely high)")
                        validation_results['suspicious_inputs'].append(feature)
                
                if feature in ['Latency Budget (µs)', 'Slice Latency (µs)', 'Jitter Budget (µs)', 'Slice Jitter (µs)']:
                    if value > 8000:
                        validation_results['warnings'].append(f"{feature}: {value}µs (very high)")
                        validation_results['suspicious_inputs'].append(feature)
                
                # Store validation details
                validation_results['validation_details'][feature] = {
                    'value': value,
                    'expected_range': expected_ranges[feature],
                    'in_range': min_val <= value <= max_val,
                    'is_extreme': False
                }
        
        return validation_results
        
    except Exception as e:
        st.error(f"Error validating input ranges: {str(e)}")
        return {'is_valid': False, 'warnings': [str(e)], 'suspicious_inputs': [], 'validation_details': {}}

def generate_access_log(num_entries: int = 50) -> pd.DataFrame:
    """
    Generate simulated access log for monitoring dashboard.
    
    Args:
        num_entries: Number of log entries to generate
        
    Returns:
        DataFrame with access log entries
    """
    try:
        np.random.seed(42)
        
        # Generate timestamps
        timestamps = pd.date_range(
            start=datetime.now() - timedelta(hours=num_entries),
            end=datetime.now(),
            freq=f"{3600//num_entries}S"
        )
        
        # Generate users
        users = ['admin', 'operator_1', 'operator_2', 'system', 'api_user', 'monitoring_bot']
        
        # Generate actions
        actions = ['prediction', 'model_load', 'training', 'validation', 'monitoring', 'health_check']
        
        # Generate statuses
        statuses = ['success', 'warning', 'error']
        status_weights = [0.85, 0.10, 0.05]  # Mostly successful
        
        # Generate log entries
        log_entries = []
        for i in range(num_entries):
            timestamp = timestamps[i]
            user = np.random.choice(users)
            action = np.random.choice(actions)
            status = np.random.choice(statuses, p=status_weights)
            
            # Generate details based on action
            if action == 'prediction':
                details = f"Slice type: {np.random.choice(['ERLLC', 'umMTC', 'MBRLLC', 'mURLLC', 'feMBB'])}"
            elif action == 'model_load':
                details = f"Model: {np.random.choice(['classification', 'regression', 'anomaly'])}"
            else:
                details = "System operation completed"
            
            log_entries.append({
                'timestamp': timestamp,
                'user': user,
                'action': action,
                'status': status,
                'details': details,
                'response_time': np.random.exponential(50)  # in ms
            })
        
        return pd.DataFrame(log_entries)
        
    except Exception as e:
        st.error(f"Error generating access log: {str(e)}")
        return pd.DataFrame()

def assess_model_health(kpis: Dict[str, List[float]]) -> Dict[str, Any]:
    """
    Assess overall model health based on KPIs.
    
    Args:
        kpis: Dictionary of KPI time series
        
    Returns:
        Dictionary with health assessment
    """
    try:
        health_status = {
            'overall_health': 'healthy',
            'health_score': 0.0,
            'issues': [],
            'recommendations': []
        }
        
        # Check latest values
        latest_accuracy = kpis['accuracy'][-1]
        latest_anomaly_rate = kpis['anomaly_rate'][-1]
        latest_confidence = kpis['confidence'][-1]
        latest_response_time = kpis['response_time'][-1]
        
        # Calculate health score (0-100)
        health_score = 0.0
        
        # Accuracy (30% weight)
        if latest_accuracy >= 0.95:
            health_score += 30
        elif latest_accuracy >= 0.90:
            health_score += 20
        else:
            health_score += 10
            health_status['issues'].append("Low accuracy detected")
        
        # Anomaly rate (20% weight)
        if latest_anomaly_rate <= 0.1:
            health_score += 20
        elif latest_anomaly_rate <= 0.15:
            health_score += 15
        else:
            health_score += 5
            health_status['issues'].append("High anomaly rate")
        
        # Confidence (20% weight)
        if latest_confidence >= 0.85:
            health_score += 20
        elif latest_confidence >= 0.80:
            health_score += 15
        else:
            health_score += 10
            health_status['issues'].append("Low prediction confidence")
        
        # Response time (20% weight)
        if latest_response_time <= 50:
            health_score += 20
        elif latest_response_time <= 100:
            health_score += 15
        else:
            health_score += 10
            health_status['issues'].append("High response time")
        
        # Stability (10% weight) - based on recent variance
        recent_accuracy = kpis['accuracy'][-10:]
        accuracy_std = np.std(recent_accuracy)
        if accuracy_std <= 0.01:
            health_score += 10
        elif accuracy_std <= 0.02:
            health_score += 7
        else:
            health_score += 3
            health_status['issues'].append("High performance variance")
        
        health_status['health_score'] = health_score
        
        # Determine overall health
        if health_score >= 90:
            health_status['overall_health'] = 'excellent'
        elif health_score >= 75:
            health_status['overall_health'] = 'good'
        elif health_score >= 60:
            health_status['overall_health'] = 'warning'
        else:
            health_status['overall_health'] = 'critical'
            health_status['issues'].append("Multiple performance issues detected")
        
        # Generate recommendations
        if health_score < 75:
            health_status['recommendations'].extend([
                "Monitor system performance closely",
                "Consider model retraining if performance continues to decline",
                "Check system resources and scaling"
            ])
        
        if latest_response_time > 100:
            health_status['recommendations'].append("Optimize model inference pipeline")
        
        if latest_accuracy < 0.90:
            health_status['recommendations'].append("Investigate data quality and model parameters")
        
        return health_status
        
    except Exception as e:
        st.error(f"Error assessing model health: {str(e)}")
        return {'overall_health': 'error', 'health_score': 0, 'issues': [str(e)], 'recommendations': []}

def create_monitoring_dashboard() -> Dict[str, Any]:
    """
    Create comprehensive monitoring dashboard.
    
    Returns:
        Dictionary with all monitoring components
    """
    try:
        # Generate KPIs
        kpis = generate_simulated_kpis(100)
        
        # Create dashboard figures
        dashboard_figures = create_kpi_dashboard(kpis)
        
        # Generate access log
        access_log = generate_access_log(50)
        
        # Assess model health
        health_assessment = assess_model_health(kpis)
        
        return {
            'kpis': kpis,
            'dashboard_figures': dashboard_figures,
            'access_log': access_log,
            'health_assessment': health_assessment
        }
        
    except Exception as e:
        st.error(f"Error creating monitoring dashboard: {str(e)}")
        return {}
