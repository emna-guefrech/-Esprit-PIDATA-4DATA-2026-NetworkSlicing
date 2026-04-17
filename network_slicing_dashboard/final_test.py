#!/usr/bin/env python3
"""
Final test - bypass dashboard and test model directly
"""

import joblib
import pandas as pd

print("=== TEST DIRECT DU MODÈLE ===")

# Load the NEW model
model = joblib.load('models/model_classification_eya.joblib')
scaler = joblib.load('models/scaler_classification_eya.joblib')
target_encoder = joblib.load('models/target_encoder_classification_eya.joblib')
features = joblib.load('models/features_classification_eya.joblib')

print(f"Modèle chargé avec {len(features)} features: {features}")

# Your exact test case
test_case = {
    'Latency_Gap': 200,      # +200 (Good)
    'Packet_Loss_Gap': 0.0005, # +0.0005 (Good)
    'Jitter_Gap': 300,       # +300 (Good)
    'Rate_Gap': -0.2         # -0.2 (Bad)
}

print(f"\nTest case: {test_case}")

# Prepare data
X_test = pd.DataFrame([test_case])
X_test_scaled = scaler.transform(X_test)

# Predict
prediction_encoded = model.predict(X_test_scaled)[0]
prediction_proba = model.predict_proba(X_test_scaled)[0]

predicted_class = target_encoder.inverse_transform([prediction_encoded])[0]
confidence = max(prediction_proba) * 100

print(f"\nRésultat:")
print(f"Prédiction: {predicted_class}")
print(f"QoS Probability: {confidence:.1f}%")
print(f"Probabilités: {dict(zip(target_encoder.classes_, prediction_proba.round(3)))}")

# Expected result for this case
# 3 gaps positifs, 1 négatif = Good performance (~75%)

print(f"\nAttendu: Good Performance (~75%)")
print(f"Obtenu: {predicted_class} ({confidence:.1f}%)")

if predicted_class == 'Good' and 70 <= confidence <= 85:
    print("✅ SUCCÈS ! Le modèle fonctionne correctement")
else:
    print("❌ ÉCHEC - Le modèle a encore un problème")
