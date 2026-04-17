import streamlit as st
import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple
import random
import joblib
import os

def predict_6g_5_1(model, features: Dict[str, Any], is_demo_mode: bool) -> Dict[str, Any]:
    """
    Predict network congestion classification for 6G Objective 5.1.
    
    Args:
        model: The loaded ML model or None for demo mode
        features: Dictionary of input features
        is_demo_mode: Whether running in demo mode
        
    Returns:
        Dictionary with prediction results
    """
    if is_demo_mode or model is None:
        # Demo mode - generate realistic mock prediction
        classes = ['Normal', 'Light', 'Critical']
        # Weighted probabilities based on typical network distribution
        probabilities = [0.25, 0.55, 0.20]  # Normal, Light, Critical
        predicted_class = random.choices(classes, weights=probabilities)[0]
        
        # Generate confidence scores
        base_confidence = random.uniform(0.85, 0.98)
        class_confidences = {
            'Normal': base_confidence if predicted_class == 'Normal' else random.uniform(0.02, 0.15),
            'Light': base_confidence if predicted_class == 'Light' else random.uniform(0.02, 0.15),
            'Critical': base_confidence if predicted_class == 'Critical' else random.uniform(0.02, 0.15)
        }
        
        # Normalize confidences
        total_conf = sum(class_confidences.values())
        class_confidences = {k: v/total_conf for k, v in class_confidences.items()}
        
        return {
            'predicted_class': predicted_class,
            'class_probabilities': class_confidences,
            'confidence': base_confidence,
            'is_demo': True
        }
    else:
        # Real model prediction
        try:
            # Load Eya's exact preprocessing from her notebook
            label_encoders = joblib.load('models/encoder_classification_eya.joblib')
            scaler = joblib.load('models/scaler_classification_eya.joblib')
            feature_cols = joblib.load('models/features_classification_eya.joblib')
            
            # Prepare features with only 9 features
            feature_order = feature_cols  # Should now be only 9 features
            
            # Create feature array
            feature_values = []
            for feature in feature_order:
                if feature in features:
                    value = features[feature]
                    feature_values.append(value)
                else:
                    feature_values.append(0.0)  # Default value
            
            # Create DataFrame and scale
            X = pd.DataFrame([feature_values], columns=feature_order)
            X_scaled = scaler.transform(X)
            
            # Make prediction
            prediction_encoded = model.predict(X_scaled)[0]
            prediction_proba = model.predict_proba(X_scaled)[0]
            
            # Map encoded classes back to labels using Eya's exact mapping
            # Eya's mapping: {0: 'Critical', 1: 'Light', 2: 'Normal'}
            class_mapping = {0: 'Critical', 1: 'Light', 2: 'Normal'}
            predicted_class = class_mapping.get(prediction_encoded, f'Unknown_{prediction_encoded}')
            
            # Handle probabilities for 3 classes [0, 1, 2]
            if len(prediction_proba) == 3:
                class_probabilities = {
                    'Critical': prediction_proba[0],
                    'Light': prediction_proba[1], 
                    'Normal': prediction_proba[2]
                }
            else:
                # Fallback for unexpected format
                class_probabilities = {
                    'Critical': prediction_proba[0] if len(prediction_proba) > 0 else 0,
                    'Light': prediction_proba[1] if len(prediction_proba) > 1 else 0,
                    'Normal': prediction_proba[2] if len(prediction_proba) > 2 else 0
                }
            
            return {
                'predicted_class': predicted_class,
                'class_probabilities': class_probabilities,
                'confidence': max(prediction_proba),
                'is_demo': False
            }
            
        except Exception as e:
            st.error(f"Error making prediction: {str(e)}")
            return None

def predict_6g_5_2(model, features: Dict[str, Any], is_demo_mode: bool) -> Dict[str, Any]:
    """
    Predict QoS probability for 6G Objective 5.2.
    
    Args:
        model: The loaded ML model or None for demo mode
        features: Dictionary of input features
        is_demo_mode: Whether running in demo mode
        
    Returns:
        Dictionary with prediction results
    """
    if is_demo_mode or model is None:
        # Demo mode - generate realistic mock prediction
        # Generate probability based on gap values (better gaps = higher probability)
        latency_gap = features.get('Latency_Gap', 0)
        packet_loss_gap = features.get('Packet_Loss_Gap', 0)
        jitter_gap = features.get('Jitter_Gap', 0)
        rate_gap = features.get('Rate_Gap', 0)
        
        # Simple heuristic: positive gaps increase probability
        base_probability = 0.5
        if latency_gap > 0:
            base_probability += 0.1
        if packet_loss_gap > 0:
            base_probability += 0.1
        if jitter_gap > 0:
            base_probability += 0.1
        if rate_gap > 0:
            base_probability += 0.1
        
        # Add some randomness and clip to [0,1]
        probability = np.clip(base_probability + random.uniform(-0.1, 0.1), 0, 1)
        
        # Determine risk level
        if probability >= 0.8:
            risk_level = "Low Risk"
            risk_color = "green"
        elif probability >= 0.6:
            risk_level = "Medium Risk"
            risk_color = "orange"
        else:
            risk_level = "High Risk"
            risk_color = "red"
        
        return {
            'qos_probability': probability,
            'risk_level': risk_level,
            'risk_color': risk_color,
            'confidence': random.uniform(0.85, 0.95),
            'is_demo': True
        }
    else:
        # Real model prediction
        try:
            # Load Eya's FIXED regression features from her notebook
            feature_cols = joblib.load('models/features_regression_eya_fixed.joblib')
            
            # Prepare features in Eya's exact order from her notebook
            feature_order = feature_cols  # Use Eya's exact feature order
            feature_values = [features.get(feat, 0.0) for feat in feature_order]
            
            # Create DataFrame (Eya didn't use scaling for regression)
            X = pd.DataFrame([feature_values], columns=feature_order)
            
            # Make prediction
            prediction = model.predict(X)[0]
            
            # Clip to [0,1] range
            prediction = np.clip(prediction, 0, 1)
            
            # Determine risk level with simplified logic
            if prediction >= 0.8:
                risk_level = "Low Risk"
                risk_color = "green"
            elif prediction >= 0.6:
                risk_level = "Medium Risk"
                risk_color = "orange"
            else:
                risk_level = "High Risk"
                risk_color = "red"
            
            return {
                'qos_probability': prediction,
                'risk_level': risk_level,
                'risk_color': risk_color,
                'confidence': 0.95,  # High confidence for real models
                'is_demo': False
            }
            
        except Exception as e:
            st.error(f"Error making prediction: {str(e)}")
            return None

def get_congestion_recommendation(predicted_class: str) -> Tuple[str, str]:
    """
    Get network action recommendation based on congestion class.
    
    Args:
        predicted_class: The predicted congestion class
        
    Returns:
        Tuple of (recommendation, urgency_level)
    """
    recommendations = {
        'Normal': ("Continue normal monitoring. Network performance is within acceptable SLA parameters.", "Low"),
        'Light': ("Increase monitoring frequency. Consider proactive traffic rerouting if performance degrades further.", "Medium"),
        'Critical': ("Immediate action required! Initiate emergency traffic rerouting and scale network resources.", "High")
    }
    
    return recommendations.get(predicted_class, ("Unknown recommendation", "Unknown"))

def get_qos_recommendation(probability: float, risk_level: str) -> Tuple[str, str]:
    """
    Get QoS recommendation based on probability and risk level.
    
    Args:
        probability: QoS compliance probability
        risk_level: Current risk level
        
    Returns:
        Tuple of (recommendation, action_required)
    """
    if risk_level == "Low Risk":
        return ("SLA compliance is highly probable. Continue with current network configuration.", "No immediate action")
    elif risk_level == "Medium Risk":
        return ("SLA compliance is uncertain. Consider optimizing network parameters or preparing fallback options.", "Monitor closely")
    else:
        return ("High risk of SLA violation. Immediate network optimization or fallback activation recommended.", "Action required")

def predict_6g_5_3(model, features: Dict[str, Any], is_demo_mode: bool) -> Dict[str, Any]:
    """
    Predict network anomalies for 6G Objective 5.3 using Isolation Forest.
    
    Args:
        model: The loaded anomaly detection model or None for demo mode
        features: Dictionary of input features
        is_demo_mode: Whether running in demo mode
        
    Returns:
        Dictionary with anomaly detection results
    """
    if is_demo_mode or model is None:
        # Demo mode - generate realistic mock anomaly detection
        anomaly_score = random.uniform(-0.2, 0.15)
        is_anomaly = anomaly_score < -0.05
        
        return {
            'anomaly_score': anomaly_score,
            'is_anomaly': is_anomaly,
            'anomaly_label': 'Anomaly' if is_anomaly else 'Normal',
            'confidence': abs(anomaly_score) + 0.5,
            'explanation': 'Demo mode - simulated anomaly detection',
            'is_demo': True
        }
    else:
        # Real model prediction
        try:
            # Load anomaly detection preprocessors
            scaler = joblib.load('models/scaler_anomaly_eya.joblib')
            encoders = joblib.load('models/encoder_anomaly_eya.joblib')
            feature_cols = joblib.load('models/features_anomaly_eya.joblib')
            
            # Prepare features in correct order
            feature_values = []
            for feat in feature_cols:
                value = features.get(feat, 0.0)
                feature_values.append(value)
            
            # Create DataFrame
            X = pd.DataFrame([feature_values], columns=feature_cols)
            
            # Apply encoding for categorical features
            categorical_features = ['Required Mobility', 'Required Connectivity', 'Slice Type']
            for cat_feat in categorical_features:
                if cat_feat in encoders and cat_feat in X.columns:
                    try:
                        X[cat_feat] = encoders[cat_feat].transform(X[cat_feat].astype(str))
                    except:
                        # Handle unseen categories
                        X[cat_feat] = 0
            
            # Apply scaling
            numerical_features = [f for f in feature_cols if f not in categorical_features]
            if numerical_features:
                X[numerical_features] = scaler.transform(X[numerical_features])
            
            # Make prediction
            anomaly_label = model.predict(X)[0]
            anomaly_score = model.decision_function(X)[0]
            
            is_anomaly = anomaly_label == -1
            confidence = abs(anomaly_score) + 0.5
            
            # Generate explanation
            if is_anomaly:
                explanation = "Network parameters show unusual patterns that deviate significantly from normal operation. This could indicate potential issues or exceptional network conditions requiring investigation."
            else:
                explanation = "Network parameters are within expected normal ranges. No anomalous behavior detected."
            
            return {
                'anomaly_score': float(anomaly_score),
                'is_anomaly': bool(is_anomaly),
                'anomaly_label': 'Anomaly' if is_anomaly else 'Normal',
                'confidence': float(confidence),
                'explanation': explanation,
                'is_demo': False
            }
            
        except Exception as e:
            st.error(f"Error in anomaly prediction: {str(e)}")
            return {
                'anomaly_score': 0.0,
                'is_anomaly': False,
                'anomaly_label': 'Error',
                'confidence': 0.0,
                'explanation': f'Prediction error: {str(e)}',
                'is_demo': False
            }
