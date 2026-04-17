import streamlit as st
import joblib
import os
from typing import Tuple, Any
import warnings
warnings.filterwarnings('ignore')

def load_model_with_fallback(model_path: str) -> Tuple[Any, bool]:
    """
    Load Eya's exact models from her notebook execution.
    
    Args:
        model_path: Path to the .joblib file
        
    Returns:
        Tuple of (model, is_real_model)
        - model: Either the loaded model or None for mock mode
        - is_real_model: True if real model was loaded, False if using mock mode
    """
    try:
        # Force reload the new corrected QoS model for classification
        if '6G_5_1' in model_path:
            # Load the NEW corrected model (4 gap features)
            eya_model_path = 'models/model_classification_eya.joblib'
            if os.path.exists(eya_model_path):
                model = joblib.load(eya_model_path)
                num_features = len(joblib.load('models/features_classification_eya.joblib'))
                print(f"✅ Loading NEW classification model with {num_features} gap features")
                return model, True
        elif '6G_5_2' in model_path:
            # Load Eya's FIXED regression model
            eya_model_path = 'models/model_regression_eya_fixed.joblib'
            if os.path.exists(eya_model_path):
                model = joblib.load(eya_model_path)
                return model, True
        elif '6G_5_3' in model_path:
            # Load Eya's anomaly detection model
            eya_model_path = 'models/model_anomaly_eya.joblib'
            if os.path.exists(eya_model_path):
                model = joblib.load(eya_model_path)
                return model, True
        
        # Try original model as fallback
        if os.path.exists(model_path):
            model = joblib.load(model_path)
            return model, True
        else:
            return None, False
    except Exception as e:
        st.warning(f"Could not load model {model_path}: {str(e)}")
        return None, False

def get_demo_warning() -> str:
    """Return standardized demo mode warning message."""
    return "⚠️ Running in demo mode — model file not found. Replace with real .joblib to activate."

def is_demo_mode(model_path: str) -> bool:
    """Check if running in demo mode for a specific model."""
    _, is_real = load_model_with_fallback(model_path)
    return not is_real
