#!/usr/bin/env python3
"""
Fix the gap logic inversion problem in QoS prediction
"""

import pandas as pd
import numpy as np
import joblib
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')

print("=== CORRECTION DE LA LOGIQUE DES GAPS ===")

# Load current model
model = joblib.load('models/model_classification_eya.joblib')
scaler = joblib.load('models/scaler_classification_eya.joblib')
target_encoder = joblib.load('models/target_encoder_classification_eya.joblib')
features = joblib.load('models/features_classification_eya.joblib')

print(f"Modèle chargé avec {len(features)} features")

# Test case with ALL POSITIVE gaps (should give HIGH QoS)
test_positive_gaps = {
    'Latency_Gap': 200,      # Budget 1000 - Real 800 = +200 (Good)
    'Packet_Loss_Gap': 0.0005, # Budget 0.001 - Real 0.0005 = +0.0005 (Good)
    'Jitter_Gap': 300,       # Budget 500 - Real 200 = +300 (Good)
    'Rate_Gap': 0.5           # Real 5.5 - Budget 5.0 = +0.5 (Good)
}

print("\nTest avec TOUS les gaps POSITIFS:")
print(f"Gaps: {test_positive_gaps}")

# Prepare data
X_test = pd.DataFrame([test_positive_gaps])
X_test_scaled = scaler.transform(X_test)

# Predict
prediction_encoded = model.predict(X_test_scaled)[0]
prediction_proba = model.predict_proba(X_test_scaled)[0]

predicted_class = target_encoder.inverse_transform([prediction_encoded])[0]
confidence = max(prediction_proba) * 100

print(f"\nRésultat actuel:")
print(f"Prédiction: {predicted_class}")
print(f"QoS Probability: {confidence:.1f}%")
print(f"Probabilités: {dict(zip(target_encoder.classes_, prediction_proba.round(3)))}")

print(f"\nAttendu avec TOUS gaps positifs:")
print(f"QoS Probability: > 80% (Excellent performance)")
print(f"Classe: Normal ou Good Performance")

# Test case with MIXED gaps
test_mixed_gaps = {
    'Latency_Gap': 200,      # Good
    'Packet_Loss_Gap': 0.0005, # Good
    'Jitter_Gap': 300,       # Good
    'Rate_Gap': -0.2         # Bad (like your case)
}

print("\n" + "="*50)
print("Test avec gaps MIXTES (3 positifs, 1 négatif):")
print(f"Gaps: {test_mixed_gaps}")

# Prepare data
X_test_mixed = pd.DataFrame([test_mixed_gaps])
X_test_mixed_scaled = scaler.transform(X_test_mixed)

# Predict
prediction_mixed_encoded = model.predict(X_test_mixed_scaled)[0]
prediction_mixed_proba = model.predict_proba(X_test_mixed_scaled)[0]

predicted_mixed_class = target_encoder.inverse_transform([prediction_mixed_encoded])[0]
confidence_mixed = max(prediction_mixed_proba) * 100

print(f"\nRésultat actuel:")
print(f"Prédiction: {predicted_mixed_class}")
print(f"QoS Probability: {confidence_mixed:.1f}%")
print(f"Probabilités: {dict(zip(target_encoder.classes_, prediction_mixed_proba.round(3)))}")

print(f"\nAttendu avec gaps MIXTES:")
print(f"QoS Probability: 60-70% (performance moyenne)")
print(f"Classe: Moderate ou Poor Performance")

print("\n" + "="*50)
print("CONCLUSION:")
if confidence > 80:
    print("✅ Logique CORRECTE - gaps positifs = haute QoS")
elif confidence < 40:
    print("✅ Logique CORRECTE - gaps négatifs = basse QoS")
else:
    print("❌ Logique INVERSÉE - gaps positifs donnent basse QoS")
