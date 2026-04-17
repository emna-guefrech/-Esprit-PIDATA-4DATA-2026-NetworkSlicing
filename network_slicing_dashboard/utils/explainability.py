import streamlit as st
import pandas as pd
import numpy as np
import joblib
import shap
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, Any, List, Tuple
import warnings
warnings.filterwarnings('ignore')

def load_shap_explainer(model_path: str, background_data_path: str) -> Tuple[shap.Explainer, pd.DataFrame, List[str]]:
    """
    Load SHAP explainer with background data.
    
    Args:
        model_path: Path to the trained model
        background_data_path: Path to background dataset
        
    Returns:
        Tuple of (explainer, background_data, feature_names)
    """
    try:
        # Load model
        model = joblib.load(model_path)
        
        # Load background data
        df = pd.read_csv(background_data_path, sep=';')
        
        # Handle encoding issues - create column mapping
        column_mapping = {
            'Latency Budget (µs)': 'Latency Budget (mus)',
            'Jitter Budget (µs)': 'Jitter Budget (mus)',
            'Slice Latency (µs)': 'Slice Latency (mus)',
            'Slice Jitter (µs)': 'Slice Jitter (mus)'
        }
        
        # Apply mapping to fix encoding
        df_fixed = df.copy()
        df_fixed.columns = [column_mapping.get(col, col) for col in df_fixed.columns]
        
        # Use the same features as training
        features = [
            'Packet Loss Budget', 'Latency Budget (mus)', 'Jitter Budget (mus)',
            'Data Rate Budget (Gbps)', 'Required Mobility', 'Required Connectivity',
            'Slice Available Transfer Rate (Gbps)', 'Slice Latency (mus)',
            'Slice Packet Loss', 'Slice Jitter (mus)', 'Slice Type', 'Slice Handover'
        ]
        
        # Prepare background data
        X_background = df_fixed[features].copy()
        
        # Handle categorical features
        categorical_features = ['Required Mobility', 'Required Connectivity', 'Slice Type']
        label_encoders = {}
        
        for cat_feat in categorical_features:
            le = joblib.load(f'models/encoder_classification_eya.joblib')
            if cat_feat in le:
                X_background[cat_feat] = le[cat_feat].transform(X_background[cat_feat].astype(str))
        
        # Scale numerical features
        scaler = joblib.load('models/scaler_classification_eya.joblib')
        numerical_features = [f for f in features if f not in categorical_features]
        X_background[numerical_features] = scaler.transform(X_background[numerical_features])
        
        # Create SHAP explainer
        explainer = shap.TreeExplainer(model)
        
        return explainer, X_background, features
        
    except Exception as e:
        st.error(f"Error loading SHAP explainer: {str(e)}")
        return None, None, None

def generate_shap_summary_plot(explainer: shap.Explainer, background_data: pd.DataFrame, 
                             feature_names: List[str], max_display: int = 12) -> go.Figure:
    """
    Generate SHAP summary plot (beeswarm).
    
    Args:
        explainer: SHAP explainer
        background_data: Background dataset
        feature_names: List of feature names
        max_display: Maximum number of features to display
        
    Returns:
        Plotly figure
    """
    try:
        # Calculate SHAP values
        shap_values = explainer.shap_values(background_data[:100])  # Use subset for performance
        
        # For multi-class, get values for first class
        if isinstance(shap_values, list):
            shap_values = shap_values[0]
        
        # Create summary plot data
        feature_importance = np.abs(shap_values).mean(0)
        feature_names_display = feature_names[:max_display]
        
        # Create plotly beeswarm plot
        fig = go.Figure()
        
        for i, feature in enumerate(feature_names_display):
            # Get SHAP values for this feature
            feature_shap = shap_values[:, i]
            feature_values = background_data[feature].values[:100]
            
            # Add scatter plot
            fig.add_trace(go.Scatter(
                x=feature_shap,
                y=[i] * len(feature_shap),
                mode='markers',
                name=feature,
                marker=dict(
                    color=feature_values,
                    colorscale='RdBu',
                    size=6,
                    colorbar=dict(title="Feature Value")
                ),
                hovertemplate=f'<b>{feature}</b><br>SHAP Value: %{{x:.3f}}<br>Feature Value: %{{marker.color:.3f}}<extra></extra>'
            ))
        
        fig.update_layout(
            title="SHAP Summary Plot (Beeswarm)",
            xaxis_title="SHAP Value (impact on model output)",
            yaxis_title="Features",
            yaxis=dict(
                tickmode='array',
                tickvals=list(range(len(feature_names_display))),
                ticktext=feature_names_display
            ),
            height=max(400, len(feature_names_display) * 30),
            showlegend=False
        )
        
        return fig
        
    except Exception as e:
        st.error(f"Error generating SHAP summary plot: {str(e)}")
        return go.Figure()

def generate_shap_bar_plot(explainer: shap.Explainer, background_data: pd.DataFrame,
                           feature_names: List[str], max_display: int = 12) -> go.Figure:
    """
    Generate SHAP bar plot (mean feature importance).
    
    Args:
        explainer: SHAP explainer
        background_data: Background dataset
        feature_names: List of feature names
        max_display: Maximum number of features to display
        
    Returns:
        Plotly figure
    """
    try:
        # Calculate SHAP values
        shap_values = explainer.shap_values(background_data[:100])
        
        # For multi-class, get values for first class
        if isinstance(shap_values, list):
            shap_values = shap_values[0]
        
        # Calculate mean absolute SHAP values
        mean_shap = np.abs(shap_values).mean(0)
        
        # Get top features
        feature_importance = mean_shap[:max_display]
        feature_names_display = feature_names[:max_display]
        
        # Sort by importance
        indices = np.argsort(feature_importance)[::-1]
        sorted_importance = feature_importance[indices]
        sorted_features = [feature_names_display[i] for i in indices]
        
        # Create bar plot
        fig = go.Figure(data=[
            go.Bar(
                x=sorted_importance,
                y=sorted_features,
                orientation='h',
                marker_color='lightblue',
                hovertemplate='<b>%{y}</b><br>Mean |SHAP Value|: %{x:.3f}<extra></extra>'
            )
        ])
        
        fig.update_layout(
            title="SHAP Feature Importance (Mean |SHAP Value|)",
            xaxis_title="Mean |SHAP Value|",
            yaxis_title="Features",
            height=max(400, len(sorted_features) * 30),
            yaxis={'categoryorder': 'total ascending'}
        )
        
        return fig
        
    except Exception as e:
        st.error(f"Error generating SHAP bar plot: {str(e)}")
        return go.Figure()

def generate_shap_waterfall_plot(explainer: shap.Explainer, background_data: pd.DataFrame,
                                feature_names: List[str], sample_idx: int = 0) -> go.Figure:
    """
    Generate SHAP waterfall plot for a single prediction.
    
    Args:
        explainer: SHAP explainer
        background_data: Background dataset
        feature_names: List of feature names
        sample_idx: Index of sample to explain
        
    Returns:
        Plotly figure and explanation text
    """
    try:
        # Get single sample
        sample = background_data.iloc[sample_idx:sample_idx+1]
        
        # Calculate SHAP values
        shap_values = explainer.shap_values(sample)
        
        # For multi-class, get values for first class
        if isinstance(shap_values, list):
            shap_values = shap_values[0]
            base_value = explainer.expected_value[0]
        else:
            shap_values = shap_values[0]
            base_value = explainer.expected_value
        
        # Create waterfall data
        shap_values_flat = shap_values.flatten()
        feature_values = sample.values.flatten()
        
        # Calculate cumulative values
        cumulative = [base_value]
        for val in shap_values_flat:
            cumulative.append(cumulative[-1] + val)
        
        # Create waterfall plot
        fig = go.Figure()
        
        # Add base value
        fig.add_trace(go.Scatter(
            x=[0],
            y=[base_value],
            mode='markers',
            name='Base Value',
            marker=dict(color='gray', size=10)
        ))
        
        # Add SHAP values
        colors = ['red' if val < 0 else 'blue' for val in shap_values_flat]
        
        for i, (shap_val, feat_val, feat_name, color) in enumerate(zip(shap_values_flat, feature_values, feature_names, colors)):
            fig.add_trace(go.Scatter(
                x=[i+1, i+1],
                y=[cumulative[i], cumulative[i+1]],
                mode='lines+markers',
                name=feat_name,
                line=dict(color=color, width=2),
                marker=dict(color=color, size=8),
                hovertemplate=f'<b>{feat_name}</b><br>Feature Value: {feat_val:.3f}<br>SHAP Value: {shap_val:.3f}<extra></extra>'
            ))
        
        # Add final prediction
        fig.add_trace(go.Scatter(
            x=[len(shap_values_flat)+1],
            y=[cumulative[-1]],
            mode='markers',
            name='Prediction',
            marker=dict(color='green', size=10)
        ))
        
        fig.update_layout(
            title=f"SHAP Waterfall Plot - Sample {sample_idx}",
            xaxis_title="Features",
            yaxis_title="Model Output",
            height=400,
            showlegend=True
        )
        
        # Generate explanation
        explanation = f"**Model Prediction Analysis:**\n\n"
        explanation += f"**Base Value:** {base_value:.3f} (average prediction)\n"
        explanation += f"**Final Prediction:** {cumulative[-1]:.3f}\n\n"
        
        # Find most influential features
        abs_shap = np.abs(shap_values_flat)
        top_idx = np.argmax(abs_shap)
        bottom_idx = np.argmin(abs_shap)
        
        explanation += f"**Most Influential Feature:** {feature_names[top_idx]} (SHAP: {shap_values_flat[top_idx]:.3f})\n"
        explanation += f"**Least Influential Feature:** {feature_names[bottom_idx]} (SHAP: {shap_values_flat[bottom_idx]:.3f})\n\n"
        
        explanation += "**Interpretation:**\n"
        if cumulative[-1] > base_value:
            explanation += "The model predicts a higher probability of congestion due to the combined effects of the features shown above."
        else:
            explanation += "The model predicts a lower probability of congestion due to the combined effects of the features shown above."
        
        return fig, explanation
        
    except Exception as e:
        st.error(f"Error generating SHAP waterfall plot: {str(e)}")
        return go.Figure(), "Error generating explanation"

def explain_prediction(model_path: str, features: Dict[str, Any]) -> str:
    """
    Generate text explanation for a single prediction.
    
    Args:
        model_path: Path to the trained model
        features: Input features dictionary
        
    Returns:
        Explanation text
    """
    try:
        # Load model and preprocessors
        model = joblib.load(model_path)
        scaler = joblib.load('models/scaler_classification_eya.joblib')
        encoders = joblib.load('models/encoder_classification_eya.joblib')
        
        # Handle encoding issues - create column mapping
        column_mapping = {
            'Latency Budget (µs)': 'Latency Budget (mus)',
            'Jitter Budget (µs)': 'Jitter Budget (mus)',
            'Slice Latency (µs)': 'Slice Latency (mus)',
            'Slice Jitter (µs)': 'Slice Jitter (mus)'
        }
        
        # Apply mapping to input features
        features_mapped = {}
        for key, value in features.items():
            features_mapped[column_mapping.get(key, key)] = value
        
        # Prepare features
        feature_cols = joblib.load('models/features_classification_eya.joblib')
        feature_values = [features_mapped.get(feat, 0.0) for feat in feature_cols]
        X = pd.DataFrame([feature_values], columns=feature_cols)
        
        # Apply preprocessing
        categorical_features = ['Required Mobility', 'Required Connectivity', 'Slice Type']
        for cat_feat in categorical_features:
            if cat_feat in encoders:
                try:
                    X[cat_feat] = encoders[cat_feat].transform(X[cat_feat].astype(str))
                except:
                    X[cat_feat] = 0
        
        numerical_features = [f for f in feature_cols if f not in categorical_features]
        X[numerical_features] = scaler.transform(X[numerical_features])
        
        # Make prediction
        prediction = model.predict(X)[0]
        probabilities = model.predict_proba(X)[0]
        
        # Map prediction to class
        class_mapping = {0: 'Critical', 1: 'Light', 2: 'Normal'}
        predicted_class = class_mapping.get(prediction, 'Unknown')
        
        # Generate explanation
        explanation = f"**Prediction Explanation:**\n\n"
        explanation += f"The model classified the network state as **{predicted_class}** with {max(probabilities):.1%} confidence.\n\n"
        
        # Feature-based explanation
        explanation += "**Key Factors:**\n"
        
        # Check critical features
        latency_value = features_mapped.get('Latency Budget (mus)', 0)
        packet_loss_value = features_mapped.get('Packet Loss Budget', 0)
        slice_type = features_mapped.get('Slice Type', '')
        
        if latency_value > 5000:
            explanation += f"- High latency budget ({latency_value}µs) suggests potential congestion\n"
        
        if packet_loss_value > 0.01:
            explanation += f"- High packet loss budget ({packet_loss_value:.6f}) indicates quality concerns\n"
        
        if slice_type == 'ERLLC':
            explanation += f"- ERLLC slice type requires ultra-reliable low latency, increasing congestion risk\n"
        
        explanation += f"\n**Recommendation:** "
        if predicted_class == 'Critical':
            explanation += "Immediate action required to prevent network degradation."
        elif predicted_class == 'Light':
            explanation += "Monitor closely and consider optimization if conditions worsen."
        else:
            explanation += "Network conditions are normal, continue regular monitoring."
        
        return explanation
        
    except Exception as e:
        return f"Error generating explanation: {str(e)}"
