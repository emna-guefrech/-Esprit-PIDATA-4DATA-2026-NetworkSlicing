# Network Slicing Dashboard - Utils Package

This package contains utility functions for the Network Slicing Intelligence dashboard.

## Files

### model_loader.py
Handles loading of ML models with fallback to demo mode:
- `load_model_with_fallback()` - Loads .joblib files or returns None for demo mode
- `get_demo_warning()` - Standardized demo mode warning message
- `is_demo_mode()` - Checks if running in demo mode

### predict.py
Contains prediction logic for each objective:
- `predict_6g_5_1()` - 6G congestion classification prediction
- `predict_6g_5_2()` - 6G QoS probability regression prediction
- `get_congestion_recommendation()` - Business recommendations for congestion levels
- `get_qos_recommendation()` - Business recommendations for QoS probabilities

## Usage

```python
from utils.model_loader import load_model_with_fallback
from utils.predict import predict_6g_5_1

# Load model with fallback
model, is_real = load_model_with_fallback("models/model_6G_5_1_xgboost.joblib")

# Make prediction
result = predict_6g_5_1(model, features, not is_real)
```
