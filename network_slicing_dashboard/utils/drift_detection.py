import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from scipy import stats
from sklearn.metrics import accuracy_score, classification_report
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.ensemble import IsolationForest
import joblib
from typing import Dict, Any, List, Tuple
import warnings
warnings.filterwarnings('ignore')

def simulate_drift_split(dataset_path: str, old_ratio: float = 0.7) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Split dataset to simulate concept drift.
    
    Args:
        dataset_path: Path to the dataset
        old_ratio: Ratio of data to consider as "old" (default: 0.7)
        
    Returns:
        Tuple of (old_data, new_data)
    """
    try:
        # Load dataset
        df = pd.read_csv(dataset_path, sep=';')
        
        # Shuffle data
        df_shuffled = df.sample(frac=1, random_state=42).reset_index(drop=True)
        
        # Split into old and new data
        split_idx = int(len(df_shuffled) * old_ratio)
        old_data = df_shuffled.iloc[:split_idx]
        new_data = df_shuffled.iloc[split_idx:]
        
        return old_data, new_data
        
    except Exception as e:
        st.error(f"Error simulating drift split: {str(e)}")
        return pd.DataFrame(), pd.DataFrame()

def perform_ks_test(old_data: pd.DataFrame, new_data: pd.DataFrame, features: List[str]) -> Dict[str, Dict[str, float]]:
    """
    Perform Kolmogorov-Smirnov test for feature drift detection.
    
    Args:
        old_data: Old dataset
        new_data: New dataset
        features: List of features to test
        
    Returns:
        Dictionary of KS test results
    """
    try:
        results = {}
        
        for feature in features:
            if feature in old_data.columns and feature in new_data.columns:
                old_values = old_data[feature].dropna()
                new_values = new_data[feature].dropna()
                
                # Perform KS test
                ks_statistic, p_value = stats.ks_2samp(old_values, new_values)
                
                results[feature] = {
                    'ks_statistic': ks_statistic,
                    'p_value': p_value,
                    'drift_detected': p_value < 0.05,
                    'old_mean': old_values.mean(),
                    'new_mean': new_values.mean(),
                    'old_std': old_values.std(),
                    'new_std': new_values.std()
                }
        
        return results
        
    except Exception as e:
        st.error(f"Error performing KS test: {str(e)}")
        return {}

def create_drift_table(ks_results: Dict[str, Dict[str, float]]) -> pd.DataFrame:
    """
    Create a formatted drift detection table.
    
    Args:
        ks_results: KS test results
        
    Returns:
        Formatted DataFrame
    """
    try:
        drift_data = []
        
        for feature, result in ks_results.items():
            drift_data.append({
                'Feature': feature,
                'KS Statistic': f"{result['ks_statistic']:.4f}",
                'P-Value': f"{result['p_value']:.4f}",
                'Drift Detected': "Yes" if result['drift_detected'] else "No",
                'Old Mean': f"{result['old_mean']:.4f}",
                'New Mean': f"{result['new_mean']:.4f}",
                'Mean Change': f"{result['new_mean'] - result['old_mean']:.4f}",
                'Old Std': f"{result['old_std']:.4f}",
                'New Std': f"{result['new_std']:.4f}"
            })
        
        return pd.DataFrame(drift_data)
        
    except Exception as e:
        st.error(f"Error creating drift table: {str(e)}")
        return pd.DataFrame()

def create_distribution_comparison(old_data: pd.DataFrame, new_data: pd.DataFrame, 
                                feature: str, ks_result: Dict[str, float]) -> go.Figure:
    """
    Create distribution comparison plot for a feature.
    
    Args:
        old_data: Old dataset
        new_data: New dataset
        feature: Feature name
        ks_result: KS test result for this feature
        
    Returns:
        Plotly figure
    """
    try:
        # Create histogram traces
        fig = go.Figure()
        
        # Old data histogram
        fig.add_trace(go.Histogram(
            x=old_data[feature],
            name='Old Data',
            opacity=0.7,
            nbins=30,
            marker_color='blue',
            hovertemplate='Old Data<br>Value: %{x}<br>Count: %{y}<extra></extra>'
        ))
        
        # New data histogram
        fig.add_trace(go.Histogram(
            x=new_data[feature],
            name='New Data',
            opacity=0.7,
            nbins=30,
            marker_color='red',
            hovertemplate='New Data<br>Value: %{x}<br>Count: %{y}<extra></extra>'
        ))
        
        # Update layout
        drift_status = "Detected" if ks_result['drift_detected'] else "Not Detected"
        fig.update_layout(
            title=f"Distribution Comparison: {feature}<br>KS Test: {drift_status} (p={ks_result['p_value']:.4f})",
            xaxis_title=feature,
            yaxis_title="Count",
            barmode='overlay',
            height=400,
            legend=dict(x=0.7, y=0.9)
        )
        
        return fig
        
    except Exception as e:
        st.error(f"Error creating distribution comparison: {str(e)}")
        return go.Figure()

def simulate_model_performance_drift(old_data: pd.DataFrame, new_data: pd.DataFrame) -> Dict[str, float]:
    """
    Simulate model performance drift between old and new data.
    
    Args:
        old_data: Old dataset
        new_data: New dataset
        
    Returns:
        Dictionary of performance metrics
    """
    try:
        # Create synthetic target based on network conditions
        def create_target(df):
            conditions = []
            for _, row in df.iterrows():
                score = 0
                if row['Latency Budget (µs)'] > 5000:
                    score += 2
                elif row['Latency Budget (µs)'] > 2000:
                    score += 1
                if row['Packet Loss Budget'] > 0.01:
                    score += 2
                elif row['Packet Loss Budget'] > 0.005:
                    score += 1
                if row['Slice Available Transfer Rate (Gbps)'] < 1.0:
                    score += 1
                if row['Slice Latency (µs)'] > row['Latency Budget (µs)']:
                    score += 1
                
                if score >= 4:
                    conditions.append('Critical')
                elif score >= 2:
                    conditions.append('Light')
                else:
                    conditions.append('Normal')
            return pd.Series(conditions)
        
        # Create targets
        old_target = create_target(old_data)
        new_target = create_target(new_data)
        
        # Simulate model predictions (with some noise for new data)
        np.random.seed(42)
        old_pred = old_target.copy()
        new_pred = new_target.copy()
        
        # Add noise to new predictions (simulate drift)
        noise_level = 0.15
        for i in range(len(new_pred)):
            if np.random.random() < noise_level:
                classes = ['Normal', 'Light', 'Critical']
                new_pred.iloc[i] = np.random.choice(classes)
        
        # Calculate metrics
        old_accuracy = accuracy_score(old_target, old_pred)
        new_accuracy = accuracy_score(new_target, new_pred)
        
        old_report = classification_report(old_target, old_pred, output_dict=True, zero_division=0)
        new_report = classification_report(new_target, new_pred, output_dict=True, zero_division=0)
        
        return {
            'old_accuracy': old_accuracy,
            'new_accuracy': new_accuracy,
            'accuracy_drift': new_accuracy - old_accuracy,
            'old_f1': old_report['weighted avg']['f1-score'],
            'new_f1': new_report['weighted avg']['f1-score'],
            'f1_drift': new_report['weighted avg']['f1-score'] - old_report['weighted avg']['f1-score']
        }
        
    except Exception as e:
        st.error(f"Error simulating model performance drift: {str(e)}")
        return {
            'old_accuracy': 0.0, 'new_accuracy': 0.0, 'accuracy_drift': 0.0,
            'old_f1': 0.0, 'new_f1': 0.0, 'f1_drift': 0.0
        }

def assess_drift_severity(ks_results: Dict[str, Dict[str, float]], performance_drift: Dict[str, float]) -> Tuple[str, str, List[str]]:
    """
    Assess overall drift severity and provide recommendations.
    
    Args:
        ks_results: KS test results
        performance_drift: Model performance drift metrics
        
    Returns:
        Tuple of (verdict, color, recommendations)
    """
    try:
        recommendations = []
        
        # Count drifted features
        drifted_features = sum(1 for result in ks_results.values() if result['drift_detected'])
        total_features = len(ks_results)
        drift_percentage = (drift_features / total_features) * 100 if total_features > 0 else 0
        
        # Assess feature drift
        if drift_percentage < 20:
            feature_drift_status = "Low"
        elif drift_percentage < 50:
            feature_drift_status = "Moderate"
            recommendations.append("Monitor drifted features closely")
        else:
            feature_drift_status = "High"
            recommendations.append("Significant feature drift detected - consider model retraining")
        
        # Assess performance drift
        acc_drift = abs(performance_drift['accuracy_drift'])
        f1_drift = abs(performance_drift['f1_drift'])
        
        if acc_drift < 0.05 and f1_drift < 0.05:
            performance_drift_status = "Stable"
        elif acc_drift < 0.1 and f1_drift < 0.1:
            performance_drift_status = "Moderate"
            recommendations.append("Model performance is declining - consider retraining")
        else:
            performance_drift_status = "Significant"
            recommendations.append("Significant performance degradation - immediate retraining required")
        
        # Overall verdict
        if feature_drift_status == "Low" and performance_drift_status == "Stable":
            verdict = "Stable"
            color = "green"
        elif feature_drift_status == "Moderate" or performance_drift_status == "Moderate":
            verdict = "Moderate Drift"
            color = "orange"
        else:
            verdict = "High Drift"
            color = "red"
        
        # Add general recommendations
        if verdict != "Stable":
            recommendations.extend([
                "Implement continuous monitoring system",
                "Set up automated drift detection alerts",
                "Create model retraining pipeline",
                "Document drift patterns and triggers"
            ])
        
        return verdict, color, recommendations
        
    except Exception as e:
        st.error(f"Error assessing drift severity: {str(e)}")
        return "Error", "gray", ["Error in drift assessment"]

def create_drift_detection_report(dataset_path: str) -> Dict[str, Any]:
    """
    Create comprehensive drift detection report.
    
    Args:
        dataset_path: Path to the dataset
        
    Returns:
        Dictionary with all drift metrics
    """
    try:
        # Simulate drift split
        old_data, new_data = simulate_drift_split(dataset_path)
        
        if old_data.empty or new_data.empty:
            return {}
        
        # Define features to test
        features = [
            'Packet Loss Budget', 'Latency Budget (µs)', 'Jitter Budget (µs)',
            'Data Rate Budget (Gbps)', 'Required Mobility', 'Required Connectivity',
            'Slice Available Transfer Rate (Gbps)', 'Slice Latency (µs)',
            'Slice Packet Loss', 'Slice Jitter (µs)', 'Slice Handover'
        ]
        
        # Perform KS tests
        ks_results = perform_ks_test(old_data, new_data, features)
        
        # Create drift table
        drift_table = create_drift_table(ks_results)
        
        # Create distribution plots for top drifted features
        drifted_features = [(feat, result) for feat, result in ks_results.items() 
                           if result['drift_detected']]
        drifted_features.sort(key=lambda x: x[1]['p_value'])
        
        distribution_plots = {}
        for feature, result in drifted_features[:3]:  # Top 3 drifted features
            distribution_plots[feature] = create_distribution_comparison(old_data, new_data, feature, result)
        
        # Simulate model performance drift
        performance_drift = simulate_model_performance_drift(old_data, new_data)
        
        # Assess overall drift severity
        verdict, color, recommendations = assess_drift_severity(ks_results, performance_drift)
        
        return {
            'old_data_size': len(old_data),
            'new_data_size': len(new_data),
            'ks_results': ks_results,
            'drift_table': drift_table,
            'distribution_plots': distribution_plots,
            'performance_drift': performance_drift,
            'drift_verdict': verdict,
            'drift_color': color,
            'recommendations': recommendations,
            'total_features': len(features),
            'drifted_features': len(drifted_features)
        }
        
    except Exception as e:
        st.error(f"Error creating drift detection report: {str(e)}")
        return {}
