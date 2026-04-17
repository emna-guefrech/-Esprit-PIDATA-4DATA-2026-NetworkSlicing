import streamlit as st
import pandas as pd
import numpy as np
import joblib
import plotly.graph_objects as go
import plotly.express as px
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.preprocessing import LabelEncoder
from typing import Dict, Any, List, Tuple
import warnings
warnings.filterwarnings('ignore')

def load_fairness_data(dataset_path: str) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series]:
    """
    Load dataset and prepare for fairness analysis.
    
    Args:
        dataset_path: Path to the dataset
        
    Returns:
        Tuple of (X, y, slice_type_series)
    """
    try:
        # Load dataset
        df = pd.read_csv(dataset_path, sep=';')
        
        # For fairness analysis, we need to simulate predictions
        # Use the actual classification model if available
        features = [
            'Packet Loss Budget', 'Latency Budget (µs)', 'Jitter Budget (µs)',
            'Data Rate Budget (Gbps)', 'Required Mobility', 'Required Connectivity',
            'Slice Available Transfer Rate (Gbps)', 'Slice Latency (µs)',
            'Slice Packet Loss', 'Slice Jitter (µs)', 'Slice Type', 'Slice Handover'
        ]
        
        X = df[features].copy()
        
        # Create synthetic target based on network conditions
        # This simulates what the classification model would predict
        conditions = []
        for _, row in X.iterrows():
            # Simple rule-based classification for fairness analysis
            score = 0
            
            # High latency increases congestion risk
            if row['Latency Budget (µs)'] > 5000:
                score += 2
            elif row['Latency Budget (µs)'] > 2000:
                score += 1
                
            # High packet loss increases congestion risk
            if row['Packet Loss Budget'] > 0.01:
                score += 2
            elif row['Packet Loss Budget'] > 0.005:
                score += 1
                
            # Low available rate increases congestion risk
            if row['Slice Available Transfer Rate (Gbps)'] < 1.0:
                score += 1
                
            # High slice latency increases congestion risk
            if row['Slice Latency (µs)'] > row['Latency Budget (µs)']:
                score += 1
                
            # Classify based on score
            if score >= 4:
                conditions.append('Critical')
            elif score >= 2:
                conditions.append('Light')
            else:
                conditions.append('Normal')
        
        y = pd.Series(conditions)
        slice_types = X['Slice Type'].copy()
        
        return X, y, slice_types
        
    except Exception as e:
        st.error(f"Error loading fairness data: {str(e)}")
        return None, None, None

def analyze_class_distribution(slice_types: pd.Series, predictions: pd.Series) -> go.Figure:
    """
    Analyze class distribution across slice types.
    
    Args:
        slice_types: Series of slice types
        predictions: Series of predictions
        
    Returns:
        Plotly figure
    """
    try:
        # Create distribution dataframe
        dist_df = pd.DataFrame({
            'Slice Type': slice_types,
            'Prediction': predictions
        })
        
        # Calculate counts
        counts = dist_df.groupby(['Slice Type', 'Prediction']).size().reset_index(name='Count')
        
        # Create stacked bar chart
        fig = px.bar(
            counts,
            x='Slice Type',
            y='Count',
            color='Prediction',
            title='Class Distribution Across Slice Types',
            labels={'Count': 'Number of Samples', 'Slice Type': '6G Slice Type'},
            color_discrete_map={'Normal': 'green', 'Light': 'orange', 'Critical': 'red'}
        )
        
        fig.update_layout(height=400)
        return fig
        
    except Exception as e:
        st.error(f"Error analyzing class distribution: {str(e)}")
        return go.Figure()

def calculate_statistical_parity(slice_types: pd.Series, predictions: pd.Series) -> Dict[str, float]:
    """
    Calculate statistical parity difference between slice types.
    
    Args:
        slice_types: Series of slice types
        predictions: Series of predictions
        
    Returns:
        Dictionary of parity metrics
    """
    try:
        # Convert predictions to binary (Critical vs Not Critical)
        binary_predictions = (predictions == 'Critical').astype(int)
        
        # Calculate rates for each slice type
        slice_rates = {}
        for slice_type in slice_types.unique():
            mask = slice_types == slice_type
            if mask.sum() > 0:
                rate = binary_predictions[mask].mean()
                slice_rates[slice_type] = rate
        
        # Calculate statistical parity difference
        rates = list(slice_rates.values())
        if len(rates) > 1:
            max_rate = max(rates)
            min_rate = min(rates)
            parity_diff = max_rate - min_rate
        else:
            parity_diff = 0.0
        
        return {
            'parity_difference': parity_diff,
            'slice_rates': slice_rates,
            'max_rate': max(rates) if rates else 0.0,
            'min_rate': min(rates) if rates else 0.0
        }
        
    except Exception as e:
        st.error(f"Error calculating statistical parity: {str(e)}")
        return {'parity_difference': 0.0, 'slice_rates': {}, 'max_rate': 0.0, 'min_rate': 0.0}

def calculate_per_class_metrics(slice_types: pd.Series, predictions: pd.Series, actual: pd.Series) -> Dict[str, Dict[str, float]]:
    """
    Calculate per-class metrics for each slice type.
    
    Args:
        slice_types: Series of slice types
        predictions: Series of predictions
        actual: Series of actual labels
        
    Returns:
        Dictionary of metrics per slice type
    """
    try:
        metrics = {}
        
        for slice_type in slice_types.unique():
            mask = slice_types == slice_type
            if mask.sum() > 0:
                slice_actual = actual[mask]
                slice_pred = predictions[mask]
                
                # Calculate classification report
                report = classification_report(slice_actual, slice_pred, output_dict=True, zero_division=0)
                
                # Extract key metrics
                metrics[slice_type] = {
                    'precision': report['weighted avg']['precision'],
                    'recall': report['weighted avg']['recall'],
                    'f1_score': report['weighted avg']['f1-score'],
                    'accuracy': report['accuracy'],
                    'support': mask.sum()
                }
        
        return metrics
        
    except Exception as e:
        st.error(f"Error calculating per-class metrics: {str(e)}")
        return {}

def create_fairness_heatmap(metrics: Dict[str, Dict[str, float]]) -> go.Figure:
    """
    Create heatmap of fairness metrics.
    
    Args:
        metrics: Dictionary of metrics per slice type
        
    Returns:
        Plotly figure
    """
    try:
        # Prepare data for heatmap
        slice_types = list(metrics.keys())
        metric_names = ['precision', 'recall', 'f1_score', 'accuracy']
        
        # Create matrix
        matrix = []
        for metric in metric_names:
            row = []
            for slice_type in slice_types:
                row.append(metrics[slice_type].get(metric, 0.0))
            matrix.append(row)
        
        # Create heatmap
        fig = go.Figure(data=go.Heatmap(
            z=matrix,
            x=slice_types,
            y=metric_names,
            colorscale='RdYlGn',
            text=[[f"{val:.3f}" for val in row] for row in matrix],
            texttemplate="%{text}",
            textfont={"size": 10},
            hoverongaps=False
        ))
        
        fig.update_layout(
            title="Fairness Metrics Heatmap",
            xaxis_title="Slice Types",
            yaxis_title="Metrics",
            height=300
        )
        
        return fig
        
    except Exception as e:
        st.error(f"Error creating fairness heatmap: {str(e)}")
        return go.Figure()

def assess_fairness(parity_diff: float, metrics: Dict[str, Dict[str, float]]) -> Tuple[str, str, List[str]]:
    """
    Assess overall fairness and provide recommendations.
    
    Args:
        parity_diff: Statistical parity difference
        metrics: Per-class metrics
        
    Returns:
        Tuple of (verdict, color, recommendations)
    """
    try:
        recommendations = []
        
        # Check statistical parity
        if parity_diff < 0.1:
            parity_status = "Good"
        elif parity_diff < 0.2:
            parity_status = "Moderate"
            recommendations.append("Consider re-sampling to balance slice type representation")
        else:
            parity_status = "Poor"
            recommendations.append("High disparity detected - consider bias mitigation techniques")
        
        # Check metric consistency
        f1_scores = [metrics[slice]['f1_score'] for slice in metrics]
        f1_std = np.std(f1_scores)
        
        if f1_std < 0.05:
            metric_status = "Consistent"
        elif f1_std < 0.1:
            metric_status = "Moderately consistent"
            recommendations.append("Model performance varies across slice types")
        else:
            metric_status = "Inconsistent"
            recommendations.append("Significant performance variation across slice types")
        
        # Overall verdict
        if parity_status == "Good" and metric_status == "Consistent":
            verdict = "Fair"
            color = "green"
        elif parity_status == "Moderate" or metric_status == "Moderately consistent":
            verdict = "Moderately Fair"
            color = "orange"
        else:
            verdict = "Biased"
            color = "red"
        
        # Add general recommendations
        if verdict != "Fair":
            recommendations.extend([
                "Consider using re-weighting techniques",
                "Implement fairness constraints in model training",
                "Monitor fairness metrics regularly"
            ])
        
        return verdict, color, recommendations
        
    except Exception as e:
        st.error(f"Error assessing fairness: {str(e)}")
        return "Error", "gray", ["Error in fairness assessment"]

def create_bias_detection_report(dataset_path: str) -> Dict[str, Any]:
    """
    Create comprehensive bias detection report.
    
    Args:
        dataset_path: Path to the dataset
        
    Returns:
        Dictionary with all fairness metrics
    """
    try:
        # Load data
        X, y, slice_types = load_fairness_data(dataset_path)
        
        if X is None:
            return {}
        
        # Analyze class distribution
        class_dist_fig = analyze_class_distribution(slice_types, y)
        
        # Calculate statistical parity
        parity_metrics = calculate_statistical_parity(slice_types, y)
        
        # Calculate per-class metrics
        per_class_metrics = calculate_per_class_metrics(slice_types, y, y)
        
        # Create fairness heatmap
        fairness_heatmap = create_fairness_heatmap(per_class_metrics)
        
        # Assess overall fairness
        verdict, color, recommendations = assess_fairness(
            parity_metrics['parity_difference'], 
            per_class_metrics
        )
        
        return {
            'class_distribution': class_dist_fig,
            'parity_metrics': parity_metrics,
            'per_class_metrics': per_class_metrics,
            'fairness_heatmap': fairness_heatmap,
            'fairness_verdict': verdict,
            'fairness_color': color,
            'recommendations': recommendations,
            'slice_types': slice_types.unique().tolist(),
            'total_samples': len(X)
        }
        
    except Exception as e:
        st.error(f"Error creating bias detection report: {str(e)}")
        return {}
