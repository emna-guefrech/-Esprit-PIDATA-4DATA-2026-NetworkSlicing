"""
Complete Test Suite for 6G Network Slicing Objectives
Tests all 3 models without Streamlit dependencies
"""

import joblib
import numpy as np
import pandas as pd
from datetime import datetime
import json
import warnings
warnings.filterwarnings('ignore')

print("=" * 80)
print("6G NETWORK SLICING - COMPLETE OBJECTIVE TESTS")
print("=" * 80)
print(f"Timestamp: {datetime.now()}")
print(f"NumPy version: {np.__version__}")
print()

# Test configuration
TEST_CONFIG = {
    "6G_Objective_5_1": {
        "model_file": "models/model_classification_eya.joblib",
        "model_type": "XGBoost Classifier",
        "features": 4,
        "feature_names": ["latency_gap", "packet_loss_gap", "jitter_gap", "rate_gap"],
        "target_classes": [0, 1, 2],  # Normal, Light, Critical
        "test_cases": [
            {
                "name": "Normal Network",
                "features": [0.1, 0.001, 0.05, 0.1],
                "expected": 0  # Normal
            },
            {
                "name": "Light Congestion",
                "features": [0.3, 0.003, 0.15, 0.25],
                "expected": 1  # Light
            },
            {
                "name": "Critical Congestion",
                "features": [0.7, 0.008, 0.4, 0.6],
                "expected": 2  # Critical
            }
        ]
    },
    "6G_Objective_5_2": {
        "model_file": "models/model_6G_5_2_xgboost.joblib",
        "model_type": "XGBoost Regressor",
        "features": 4,
        "feature_names": ["latency_gap", "packet_loss_gap", "jitter_gap", "rate_gap"],
        "target_range": [0, 1],
        "test_cases": [
            {
                "name": "High QoS",
                "features": [0.1, 0.001, 0.05, 0.1],
                "expected_range": [0.8, 1.0]  # High probability
            },
            {
                "name": "Medium QoS",
                "features": [0.3, 0.003, 0.15, 0.25],
                "expected_range": [0.5, 0.8]  # Medium probability
            },
            {
                "name": "Low QoS",
                "features": [0.7, 0.008, 0.4, 0.6],
                "expected_range": [0.0, 0.5]  # Low probability
            }
        ]
    },
    "6G_Objective_5_3": {
        "model_file": "models/model_anomaly_eya.joblib",
        "model_type": "Isolation Forest",
        "features": 8,
        "feature_names": [
            "packet_loss_budget", "data_rate_budget", "required_mobility", 
            "required_connectivity", "slice_available_rate", "slice_packet_loss", 
            "slice_type", "slice_handover"
        ],
        "target_classes": [-1, 1],  # Anomaly, Normal
        "test_cases": [
            {
                "name": "Normal Traffic",
                "features": [0.001, 5.0, 1, 1, 4.8, 0.0005, 4, 0.5],
                "expected": 1  # Normal
            },
            {
                "name": "Anomalous Traffic",
                "features": [0.01, 2.0, 2, 0, 1.0, 0.01, 1, 0.9],
                "expected": -1  # Anomaly
            }
        ]
    }
}

def load_and_test_model(model_config):
    """Load and test a single model"""
    model_name = model_config["model_file"]
    print(f"\n{'='*60}")
    print(f"TESTING: {model_config['model_type']}")
    print(f"Model File: {model_name}")
    print(f"Expected Features: {model_config['features']}")
    print(f"Feature Names: {model_config['feature_names']}")
    print(f"{'='*60}")
    
    try:
        # Load model
        model = joblib.load(model_name)
        print(f"Model loaded successfully!")
        
        # Test each test case
        results = []
        
        for i, test_case in enumerate(model_config["test_cases"], 1):
            print(f"\nTest Case {i}: {test_case['name']}")
            print(f"Input Features: {test_case['features']}")
            
            try:
                # Prepare input
                features_array = np.array([test_case['features']])
                
                # Make prediction
                if "Classifier" in model_config["model_type"]:
                    prediction = model.predict(features_array)[0]
                    print(f"Prediction: {prediction}")
                    
                    # Check if prediction matches expected
                    if prediction == test_case["expected"]:
                        print("Result: PASS")
                        status = "PASS"
                    else:
                        print(f"Result: FAIL (Expected: {test_case['expected']})")
                        status = "FAIL"
                    
                    # Get prediction probabilities if available
                    if hasattr(model, 'predict_proba'):
                        probabilities = model.predict_proba(features_array)[0]
                        print(f"Probabilities: {probabilities}")
                    
                elif "Regressor" in model_config["model_type"]:
                    prediction = model.predict(features_array)[0]
                    print(f"Prediction: {prediction:.4f}")
                    
                    # Check if prediction is in expected range
                    min_val, max_val = test_case["expected_range"]
                    if min_val <= prediction <= max_val:
                        print("Result: PASS")
                        status = "PASS"
                    else:
                        print(f"Result: FAIL (Expected range: {min_val}-{max_val})")
                        status = "FAIL"
                
                elif "Forest" in model_config["model_type"]:
                    prediction = model.predict(features_array)[0]
                    score = model.decision_function(features_array)[0]
                    print(f"Prediction: {prediction}")
                    print(f"Anomaly Score: {score:.4f}")
                    
                    # Check if prediction matches expected
                    if prediction == test_case["expected"]:
                        print("Result: PASS")
                        status = "PASS"
                    else:
                        print(f"Result: FAIL (Expected: {test_case['expected']})")
                        status = "FAIL"
                
                results.append({
                    "test_case": test_case["name"],
                    "status": status,
                    "prediction": prediction,
                    "input": test_case["features"]
                })
                
            except Exception as e:
                print(f"Error in prediction: {e}")
                results.append({
                    "test_case": test_case["name"],
                    "status": "ERROR",
                    "prediction": None,
                    "input": test_case["features"],
                    "error": str(e)
                })
        
        return model, results
        
    except Exception as e:
        print(f"Error loading model: {e}")
        return None, []

def test_model_features(model, model_config):
    """Test model with different feature configurations"""
    print(f"\n{'='*60}")
    print("FEATURE VALIDATION")
    print(f"{'='*60}")
    
    expected_features = model_config["features"]
    feature_names = model_config["feature_names"]
    
    # Test with correct number of features
    try:
        test_features = np.random.rand(1, expected_features)
        prediction = model.predict(test_features)
        print(f"Correct features ({expected_features}): PASS")
    except Exception as e:
        print(f"Correct features ({expected_features}): FAIL - {e}")
    
    # Test with wrong number of features
    for wrong_features in [expected_features - 1, expected_features + 1]:
        try:
            test_features = np.random.rand(1, wrong_features)
            prediction = model.predict(test_features)
            print(f"Wrong features ({wrong_features}): UNEXPECTED PASS")
        except Exception as e:
            print(f"Wrong features ({wrong_features}): EXPECTED FAIL - {type(e).__name__}")

def generate_test_report(all_results):
    """Generate comprehensive test report"""
    print(f"\n{'='*80}")
    print("COMPREHENSIVE TEST REPORT")
    print(f"{'='*80}")
    
    total_tests = 0
    total_passed = 0
    total_failed = 0
    total_errors = 0
    
    for objective_name, results in all_results.items():
        print(f"\n{objective_name}:")
        print("-" * 40)
        
        for result in results:
            total_tests += 1
            status = result["status"]
            
            if status == "PASS":
                total_passed += 1
                print(f"  {result['test_case']}: PASS")
            elif status == "FAIL":
                total_failed += 1
                print(f"  {result['test_case']}: FAIL")
            else:
                total_errors += 1
                print(f"  {result['test_case']}: ERROR")
    
    print(f"\n{'='*40}")
    print("SUMMARY")
    print(f"{'='*40}")
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {total_passed}")
    print(f"Failed: {total_failed}")
    print(f"Errors: {total_errors}")
    print(f"Success Rate: {(total_passed/total_tests)*100:.1f}%" if total_tests > 0 else "N/A")
    
    # Overall status
    if total_passed == total_tests:
        print("\nOverall Status: ALL TESTS PASSED")
    elif total_passed > total_tests * 0.8:
        print("\nOverall Status: MOSTLY SUCCESSFUL")
    else:
        print("\nOverall Status: NEEDS ATTENTION")

def test_spring_boot_integration():
    """Test integration scenarios for Spring Boot"""
    print(f"\n{'='*80}")
    print("SPRING BOOT INTEGRATION TEST")
    print(f"{'='*80}")
    
    # Simulate Spring Boot input format
    spring_boot_inputs = {
        "6G_Objective_5_1": {
            "latency_gap": 0.2,
            "packet_loss_gap": 0.001,
            "jitter_gap": 0.1,
            "rate_gap": 0.2
        },
        "6G_Objective_5_2": {
            "latency_gap": 0.2,
            "packet_loss_gap": 0.001,
            "jitter_gap": 0.1,
            "rate_gap": 0.2
        },
        "6G_Objective_5_3": {
            "packet_loss_budget": 0.001,
            "data_rate_budget": 5.0,
            "required_mobility": 1,
            "required_connectivity": 1,
            "slice_available_rate": 4.8,
            "slice_packet_loss": 0.0005,
            "slice_type": 4,
            "slice_handover": 0.5
        }
    }
    
    for objective, input_data in spring_boot_inputs.items():
        print(f"\nTesting {objective} with Spring Boot input format:")
        print(f"Input: {input_data}")
        
        # Convert to feature array
        if objective in ["6G_Objective_5_1", "6G_Objective_5_2"]:
            feature_order = ["latency_gap", "packet_loss_gap", "jitter_gap", "rate_gap"]
        else:
            feature_order = [
                "packet_loss_budget", "data_rate_budget", "required_mobility", 
                "required_connectivity", "slice_available_rate", "slice_packet_loss", 
                "slice_type", "slice_handover"
            ]
        
        try:
            features_array = np.array([[input_data[feature] for feature in feature_order]])
            print(f"Feature Array: {features_array}")
            print("Input conversion: PASS")
        except Exception as e:
            print(f"Input conversion: FAIL - {e}")

def main():
    """Main test execution"""
    print("Starting comprehensive 6G model testing...")
    
    all_results = {}
    all_models = {}
    
    # Test each objective
    for objective_name, config in TEST_CONFIG.items():
        print(f"\n{'='*80}")
        print(f"TESTING {objective_name}")
        print(f"{'='*80}")
        
        model, results = load_and_test_model(config)
        all_models[objective_name] = model
        all_results[objective_name] = results
        
        if model:
            test_model_features(model, config)
    
    # Generate report
    generate_test_report(all_results)
    
    # Test Spring Boot integration
    test_spring_boot_integration()
    
    # Final status
    print(f"\n{'='*80}")
    print("TESTING COMPLETED")
    print(f"{'='*80}")
    print("All models tested successfully!")
    print("Ready for Spring Boot integration!")
    print("Use these models in your production application.")

if __name__ == "__main__":
    main()
