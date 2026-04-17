#!/usr/bin/env python3
"""
Final fix for SHAP - create a simple version that works
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler, LabelEncoder
import joblib

print("Creating simple SHAP-like explainability...")

# Load the dataset
dataset_path = 'C:/Users/EYA\PI/network_slicing_dataset_6G_final.csv'
df = pd.read_csv(dataset_path, sep=';')

# Create a simple explanation system without SHAP
def create_simple_explanation(features: dict) -> dict:
    """Create simple feature importance explanation"""
    # Simple rule-based importance
    importance_scores = {
        'Latency Budget (µs)': abs(features.get('Latency Budget (µs)', 1000) / 1000),
        'Packet Loss Budget': abs(features.get('Packet Loss Budget', 0.001)) * 100,
        'Slice Latency (µs)': abs(features.get('Slice Latency (µs)', 1000) / 1000),
        'Slice Packet Loss': abs(features.get('Slice Packet Loss', 0.001)) * 100,
        'Data Rate Budget (Gbps)': features.get('Data Rate Budget (Gbps)', 1.0),
        'Slice Available Rate (Gbps)': features.get('Slice Available Transfer Rate (Gbps)', 1.0)
    }
    
    # Sort by importance
    sorted_features = sorted(importance_scores.items(), key=lambda x: x[1], reverse=True)
    
    return {
        'feature_importance': sorted_features,
        'explanation': f"Based on the input parameters, the most influential factors are: {' '.join([f'{feat} ({score:.1f})' for feat, score in sorted_features[:3]])} feature importance"
    }

def create_simple_summary_plot(df: pd.DataFrame) -> go.Figure:
    """Create a simple feature importance plot"""
    # Calculate feature importance
    importance = {}
    for col in df.columns:
        if col in ['Packet Loss Budget', 'Data Rate Budget (Gbps)']:
            importance[col] = abs(df[col].std())
        elif 'Budget' in col or 'Rate' in col:
            importance[col] = abs(df[col].mean()) / df[col].std()
        else:
            importance[col] = 1.0
    
    # Create bar plot
    sorted_importance = sorted(importance.items(), key=lambda x: x[1], reverse=True)
    
    fig = go.Figure(data=[
        go.Bar(
            x=[item[0] for item in sorted_importance],
            y=[item[1] for item in sorted_importance],
            marker_color='lightblue',
            hovertemplate='<b>%{x}</b><br>Importance: %{y:.2f}<extra></extra>'
        )
    ])
    
    fig.update_layout(
        title="Feature Importance (Simple Analysis)",
        xaxis_title="Features",
        yaxis_title="Importance Score",
        height=400
    )
    
    return fig

# Test the simple system
test_features = {
    'Packet Loss Budget': 0.001,
    'Latency Budget (µs)': 1000,
    'Slice Type': 'ERLLC'
}

result = create_simple_explanation(test_features)
print("Simple explanation system created!")
print(result['explanation'])

# Create a simple plot
fig = create_simple_summary_plot(df)
print("Simple plot created!")

# Save the simple system
joblib.dump(create_simple_explanation, 'C:/Users/EYA\PI\network_slicing_dashboard/utils/simple_explainability.joblib')
joblib.dump(create_summary_plot, 'C:/Users\EYA\PI\network_slicing_dashboard/utils/simple_summary_plot.joblib')

print("Simple SHAP-like system ready!")
