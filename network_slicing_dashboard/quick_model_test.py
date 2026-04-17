"""
Quick Model Test - Test all models without Streamlit
"""

import joblib
import numpy as np
import pandas as pd
from datetime import datetime

print("=" * 60)
print("6G NETWORK SLICING - MODEL TESTING")
print("=" * 60)
print(f"Timestamp: {datetime.now()}")
print(f"NumPy version: {np.__version__}")
print()

# Test models
models_to_test = [
    {
        'name': '6G Objective 5.1 - Classification',
        'file': 'models/model_classification_eya.joblib',
        'type': 'XGBoost Classifier'
    },
    {
        'name': '6G Objective 5.2 - QoS Regression',
        'file': 'models/model_6G_5_2_xgboost.joblib',
        'type': 'XGBoost Regressor'
    },
    {
        'name': '6G Objective 5.3 - Anomaly Detection',
        'file': 'models/model_anomaly_eya.joblib',
        'type': 'Isolation Forest'
    }
]

results = []

for model_info in models_to_test:
    print(f"Testing {model_info['name']}...")
    print(f"Model: {model_info['type']}")
    print(f"File: {model_info['file']}")
    
    try:
        # Load model
        model = joblib.load(model_info['file'])
        print(f"  Model loaded successfully!")
        
        # Test with dummy data
        if 'Classification' in model_info['name']:
            # Test classification
            test_features = np.array([[0.001, 1000, 500, 5.0, 4.8, 800, 0.0005, 200, 0.5]])
            prediction = model.predict(test_features)[0]
            print(f"  Test prediction: {prediction}")
            
        elif 'Regression' in model_info['name']:
            # Test regression
            test_features = np.array([[0.2, 0.001, 0.1, 0.2]])  # gaps
            prediction = model.predict(test_features)[0]
            print(f"  Test prediction: {prediction:.4f}")
            
        elif 'Anomaly' in model_info['name']:
            # Test anomaly
            test_features = np.array([[0.001, 5.0, 1, 1, 4.8, 0.0005, 4, 0.5]])
            prediction = model.predict(test_features)[0]
            score = model.decision_function(test_features)[0]
            print(f"  Test prediction: {prediction} (score: {score:.4f})")
        
        results.append({
            'model': model_info['name'],
            'status': 'SUCCESS',
            'error': None
        })
        
    except Exception as e:
        print(f"  ERROR: {str(e)}")
        results.append({
            'model': model_info['name'],
            'status': 'FAILED',
            'error': str(e)
        })
    
    print()

# Summary
print("=" * 60)
print("SUMMARY")
print("=" * 60)

success_count = sum(1 for r in results if r['status'] == 'SUCCESS')
total_count = len(results)

print(f"Total models tested: {total_count}")
print(f"Successful: {success_count}")
print(f"Failed: {total_count - success_count}")
print()

for result in results:
    status_symbol = "  - " if result['status'] == 'SUCCESS' else "  - "
    print(f"{status_symbol}{result['model']}: {result['status']}")
    if result['error']:
        print(f"    Error: {result['error']}")

print()

if success_count == total_count:
    print("All models are working correctly!")
else:
    print("Some models failed. Check the errors above.")

print("=" * 60)

# Test prediction function
print("\nTESTING PREDICTION FUNCTION...")

try:
    # Load classification model
    model_51 = joblib.load('models/model_classification_eya.joblib')
    
    # Create test input
    test_input = {
        'Packet Loss Budget': 0.001,
        'Latency Budget (µs)': 1000,
        'Jitter Budget (µs)': 500,
        'Data Rate Budget (Gbps)': 5.0,
        'Slice Available Transfer Rate (Gbps)': 4.8,
        'Slice Latency (µs)': 800,
        'Slice Packet Loss': 0.0005,
        'Slice Jitter (µs)': 200,
        'Slice Handover': 0.5
    }
    
    # Convert to array
    feature_order = [
        'Packet Loss Budget', 'Latency Budget (µs)', 'Jitter Budget (µs)',
        'Data Rate Budget (Gbps)', 'Slice Available Transfer Rate (Gbps)',
        'Slice Latency (µs)', 'Slice Packet Loss', 'Slice Jitter (µs)', 'Slice Handover'
    ]
    
    features_array = np.array([[test_input[feature] for feature in feature_order]])
    
    # Make prediction
    prediction = model_51.predict(features_array)[0]
    
    print(f"Input features: {test_input}")
    print(f"Prediction: {prediction}")
    print("Prediction function working!")
    
except Exception as e:
    print(f"Prediction test failed: {e}")

print("\n" + "=" * 60)
print("TEST COMPLETED")
print("=" * 60)
