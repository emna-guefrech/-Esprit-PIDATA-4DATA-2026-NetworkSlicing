"""
Fix Model Features - Check and fix feature mismatches
"""

import joblib
import numpy as np
import pandas as pd
from datetime import datetime

print("=" * 60)
print("FIXING MODEL FEATURES")
print("=" * 60)

# Check model requirements
models_info = []

# Check 6G Objective 5.1
try:
    model_51 = joblib.load('models/model_classification_eya.joblib')
    print("6G Objective 5.1 loaded successfully")
    
    # Try to get feature information
    if hasattr(model_51, 'feature_importances_'):
        print(f"Expected features: {len(model_51.feature_importances_)}")
    else:
        print("Cannot determine feature count from model")
    
    # Test with different feature counts
    for n_features in [4, 9, 12]:
        try:
            test_data = np.random.rand(1, n_features)
            prediction = model_51.predict(test_data)
            print(f"  SUCCESS with {n_features} features")
            models_info.append({
                'model': '6G Objective 5.1',
                'expected_features': n_features,
                'status': 'SUCCESS'
            })
            break
        except Exception as e:
            print(f"  FAILED with {n_features} features: {e}")
    
except Exception as e:
    print(f"Error loading 6G Objective 5.1: {e}")

print()

# Check 6G Objective 5.2
try:
    model_52 = joblib.load('models/model_6G_5_2_xgboost.joblib')
    print("6G Objective 5.2 loaded successfully")
    
    # Test with 4 features (gaps)
    test_data = np.array([[0.2, 0.001, 0.1, 0.2]])  # gaps
    prediction = model_52.predict(test_data)[0]
    print(f"  SUCCESS with 4 features: {prediction:.4f}")
    
    models_info.append({
        'model': '6G Objective 5.2',
        'expected_features': 4,
        'status': 'SUCCESS'
    })
    
except Exception as e:
    print(f"Error with 6G Objective 5.2: {e}")

print()

# Check 6G Objective 5.3
try:
    model_53 = joblib.load('models/model_anomaly_eya.joblib')
    print("6G Objective 5.3 loaded successfully")
    
    # Test with 8 features (from our creation)
    test_data = np.array([[0.001, 5.0, 1, 1, 4.8, 0.0005, 4, 0.5]])
    prediction = model_53.predict(test_data)[0]
    score = model_53.decision_function(test_data)[0]
    print(f"  SUCCESS with 8 features: {prediction} (score: {score:.4f})")
    
    models_info.append({
        'model': '6G Objective 5.3',
        'expected_features': 8,
        'status': 'SUCCESS'
    })
    
except Exception as e:
    print(f"Error with 6G Objective 5.3: {e}")

print()
print("=" * 60)
print("MODEL REQUIREMENTS SUMMARY")
print("=" * 60)

for info in models_info:
    print(f"{info['model']}: {info['expected_features']} features - {info['status']}")

print()

# Create correct prediction functions
def predict_6g_51_correct():
    """Correct prediction for 6G Objective 5.1"""
    try:
        model = joblib.load('models/model_classification_eya.joblib')
        
        # Based on our test, it seems to expect 4 features
        # Let's use gap features like 6G Objective 5.2
        test_features = np.array([[0.2, 0.001, 0.1, 0.2]])  # gaps
        prediction = model.predict(test_features)[0]
        
        print(f"6G Objective 5.1 Prediction (gap features): {prediction}")
        return prediction
        
    except Exception as e:
        print(f"Error in 6G Objective 5.1 prediction: {e}")
        return None

def predict_6g_52_correct():
    """Correct prediction for 6G Objective 5.2"""
    try:
        model = joblib.load('models/model_6G_5_2_xgboost.joblib')
        
        # 4 gap features
        test_features = np.array([[0.2, 0.001, 0.1, 0.2]])  # gaps
        prediction = model.predict(test_features)[0]
        
        print(f"6G Objective 5.2 Prediction: {prediction:.4f}")
        return prediction
        
    except Exception as e:
        print(f"Error in 6G Objective 5.2 prediction: {e}")
        return None

def predict_6g_53_correct():
    """Correct prediction for 6G Objective 5.3"""
    try:
        model = joblib.load('models/model_anomaly_eya.joblib')
        
        # 8 features from our creation
        test_features = np.array([[0.001, 5.0, 1, 1, 4.8, 0.0005, 4, 0.5]])
        prediction = model.predict(test_features)[0]
        score = model.decision_function(test_features)[0]
        
        print(f"6G Objective 5.3 Prediction: {prediction} (score: {score:.4f})")
        return prediction
        
    except Exception as e:
        print(f"Error in 6G Objective 5.3 prediction: {e}")
        return None

print("TESTING CORRECTED PREDICTIONS:")
print("-" * 40)

predict_6g_51_correct()
predict_6g_52_correct()
predict_6g_53_correct()

print()
print("=" * 60)
print("FEATURE MAPPINGS FOR SPRING BOOT")
print("=" * 60)

print("""
# 6G Objective 5.1 - Classification (4 features)
FEATURES_6G_51 = [
    'latency_gap',      # Latency Budget - Slice Latency
    'packet_loss_gap',  # Packet Loss Budget - Slice Packet Loss
    'jitter_gap',       # Jitter Budget - Slice Jitter
    'rate_gap'          # Data Rate Budget - Slice Available Transfer Rate
]

# 6G Objective 5.2 - QoS Regression (4 features)
FEATURES_6G_52 = [
    'latency_gap',
    'packet_loss_gap', 
    'jitter_gap',
    'rate_gap'
]

# 6G Objective 5.3 - Anomaly Detection (8 features)
FEATURES_6G_53 = [
    'packet_loss_budget',
    'data_rate_budget',
    'required_mobility',
    'required_connectivity',
    'slice_available_rate',
    'slice_packet_loss',
    'slice_type',
    'slice_handover'
]
""")

print("=" * 60)
print("READY FOR SPRING BOOT INTEGRATION!")
print("=" * 60)
