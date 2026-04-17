#!/usr/bin/env python3
"""
Test the model with real-world data not in the training dataset
"""

import pandas as pd
import numpy as np
import joblib
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')

print("=== TEST DU MODÈLE AVEC DONNÉES RÉELLES ===")

# Load the trained model
model = joblib.load('models/model_classification_eya.joblib')
scaler = joblib.load('models/scaler_classification_eya.joblib')
target_encoder = joblib.load('models/target_encoder_classification_eya.joblib')
features = joblib.load('models/features_classification_eya.joblib')

print(f"Modèle chargé avec {len(features)} features")
print(f"Features: {features}")

# Real-world test cases (not in training dataset)
test_cases = {
    "Edge Computing": {
        'Packet Loss Budget': 0.002,
        'Latency Budget (µs)': 1500,
        'Jitter Budget (µs)': 300,
        'Data Rate Budget (Gbps)': 2.5,
        'Slice Available Transfer Rate (Gbps)': 2.2,
        'Slice Latency (µs)': 1200,
        'Slice Packet Loss': 0.0015,
        'Slice Jitter (µs)': 250,
        'Slice Handover': 0.8,
        'Attendu': 'Light'
    },
    "Disaster Network": {
        'Packet Loss Budget': 0.08,
        'Latency Budget (µs)': 10000,
        'Jitter Budget (µs)': 4000,
        'Data Rate Budget (Gbps)': 0.05,
        'Slice Available Transfer Rate (Gbps)': 0.02,
        'Slice Latency (µs)': 9500,
        'Slice Packet Loss': 0.06,
        'Slice Jitter (µs)': 3500,
        'Slice Handover': 2.5,
        'Attendu': 'Critical'
    },
    "IoT Massif": {
        'Packet Loss Budget': 0.003,
        'Latency Budget (µs)': 3000,
        'Jitter Budget (µs)': 1000,
        'Data Rate Budget (Gbps)': 0.8,
        'Slice Available Transfer Rate (Gbps)': 0.7,
        'Slice Latency (µs)': 2500,
        'Slice Packet Loss': 0.002,
        'Slice Jitter (µs)': 800,
        'Slice Handover': 0.3,
        'Attendu': 'Light'
    },
    "VR/AR 6G": {
        'Packet Loss Budget': 0.0005,
        'Latency Budget (µs)': 500,
        'Jitter Budget (µs)': 100,
        'Data Rate Budget (Gbps)': 8.0,
        'Slice Available Transfer Rate (Gbps)': 7.5,
        'Slice Latency (µs)': 400,
        'Slice Packet Loss': 0.0003,
        'Slice Jitter (µs)': 80,
        'Slice Handover': 0.1,
        'Attendu': 'Normal'
    },
    "Téléchirurgie": {
        'Packet Loss Budget': 0.0001,
        'Latency Budget (µs)': 100,
        'Jitter Budget (µs)': 20,
        'Data Rate Budget (Gbps)': 1.5,
        'Slice Available Transfer Rate (Gbps)': 1.4,
        'Slice Latency (µs)': 80,
        'Slice Packet Loss': 0.00005,
        'Slice Jitter (µs)': 15,
        'Slice Handover': 0.05,
        'Attendu': 'Normal'
    },
    "Zone Rurale": {
        'Packet Loss Budget': 0.02,
        'Latency Budget (µs)': 6000,
        'Jitter Budget (µs)': 2500,
        'Data Rate Budget (Gbps)': 0.3,
        'Slice Available Transfer Rate (Gbps)': 0.2,
        'Slice Latency (µs)': 5500,
        'Slice Packet Loss': 0.015,
        'Slice Jitter (µs)': 2000,
        'Slice Handover': 1.8,
        'Attendu': 'Critical'
    }
}

print("\n=== RÉSULTATS DES TESTS ===")
print("=" * 80)

correct_predictions = 0
total_tests = len(test_cases)

for test_name, test_data in test_cases.items():
    # Extract features (excluding 'Attendu')
    test_features = {k: v for k, v in test_data.items() if k != 'Attendu'}
    expected = test_data['Attendu']
    
    # Prepare data
    X_test = pd.DataFrame([test_features])
    X_test_scaled = scaler.transform(X_test)
    
    # Predict
    prediction_encoded = model.predict(X_test_scaled)[0]
    prediction_proba = model.predict_proba(X_test_scaled)[0]
    predicted_class = target_encoder.inverse_transform([prediction_encoded])[0]
    
    # Calculate confidence
    confidence = max(prediction_proba) * 100
    
    # Check if correct
    is_correct = predicted_class == expected
    if is_correct:
        correct_predictions += 1
        status = "CORRECT"
    else:
        status = "INCORRECT"
    
    # Display results
    print(f"\n{test_name}:")
    print(f"  Attendu: {expected}")
    print(f"  Prédit: {predicted_class}")
    print(f"  Confiance: {confidence:.1f}%")
    print(f"  Statut: {status}")
    
    # Show probabilities
    prob_dict = dict(zip(target_encoder.classes_, prediction_proba.round(3)))
    print(f"  Probabilités: {prob_dict}")

print("\n" + "=" * 80)
print(f"Performance globale: {correct_predictions}/{total_tests} correct ({correct_predictions/total_tests*100:.1f}%)")

if correct_predictions == total_tests:
    print("EXCELLENT ! Le modèle généralise parfaitement !")
elif correct_predictions >= total_tests * 0.8:
    print("BON ! Le modèle généralise bien !")
else:
    print("Le modèle a besoin d'amélioration pour la généralisation.")

print("\n=== ANALYSE DES CAS LIMITES ===")
print("Ces tests simulent des conditions réelles:")
print("- Edge Computing: conditions exigeantes mais gérables")
print("- Disaster Network: conditions catastrophiques")
print("- IoT Massif: nombreux appareils, faible bande passante")
print("- VR/AR 6G: exigences ultra-basses latences")
print("- Téléchirurgie: mission critique, zéro tolérance")
print("- Zone Rurale: infrastructure limitée")
