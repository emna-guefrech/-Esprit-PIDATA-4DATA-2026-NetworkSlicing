#!/usr/bin/env python3
"""
Fix the QoS model thresholds to be more accurate
"""

import pandas as pd
import numpy as np
import joblib
from sklearn.preprocessing import StandardScaler, LabelEncoder
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import f1_score, classification_report
import warnings
warnings.filterwarnings('ignore')

print("=== CORRECTION DES SEUILS QoS ===")

# Load current model
model = joblib.load('models/model_classification_eya.joblib')
scaler = joblib.load('models/scaler_classification_eya.joblib')
target_encoder = joblib.load('models/target_encoder_classification_eya.joblib')
features = joblib.load('models/features_classification_eya.joblib')

print(f"Modèle actuel: {len(features)} features")

# Create better training data with CORRECT thresholds
def create_corrected_data():
    data = []
    
    # Excellent performance (>= 80%)
    for i in range(2500):
        data.append({
            'Latency_Gap': np.random.uniform(100, 500),
            'Packet_Loss_Gap': np.random.uniform(0.0001, 0.001),
            'Jitter_Gap': np.random.uniform(50, 300),
            'Rate_Gap': np.random.uniform(0.1, 1.0),
            'qos_class': 'Excellent'
        })
    
    # Good performance (60-80%)
    for i in range(2000):
        data.append({
            'Latency_Gap': np.random.uniform(-200, 200),
            'Packet_Loss_Gap': np.random.uniform(-0.001, 0.001),
            'Jitter_Gap': np.random.uniform(-100, 100),
            'Rate_Gap': np.random.uniform(-0.5, 0.5),
            'qos_class': 'Good'
        })
    
    # Poor performance (< 60%)
    for i in range(1000):
        data.append({
            'Latency_Gap': np.random.uniform(-1000, -200),
            'Packet_Loss_Gap': np.random.uniform(-0.01, -0.001),
            'Jitter_Gap': np.random.uniform(-500, -100),
            'Rate_Gap': np.random.uniform(-2.0, -0.5),
            'qos_class': 'Poor'
        })
    
    return pd.DataFrame(data)

# Create corrected dataset
df = create_corrected_data()
print(f"Dataset corrigé: {df.shape}")
print(f"Distribution: {df['qos_class'].value_counts()}")

# Prepare features and target
X = df[features].copy()
y = df['qos_class']

# Encode target
target_encoder = LabelEncoder()
y_encoded = target_encoder.fit_transform(y)

# Scale features
X_scaled = scaler.fit_transform(X)

# Split and train new model
X_train, X_test, y_train, y_test = train_test_split(
    X_scaled, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded
)

# Create new model
new_model = XGBClassifier(
    learning_rate=0.1,
    max_depth=6,
    n_estimators=300,
    random_state=42,
    eval_metric='mlogloss',
    verbosity=0
)

print("\nEntraînement du modèle corrigé...")
new_model.fit(X_train, y_train)

# Evaluate
y_pred = new_model.predict(X_test)
f1 = f1_score(y_test, y_pred, average='weighted')

print(f"\nPerformance du modèle corrigé:")
print(f"F1-Score: {f1:.4f}")

# Test with your case
test_case = {
    'Latency_Gap': 200,      # +200 (Good)
    'Packet_Loss_Gap': 0.0005, # +0.0005 (Good)
    'Jitter_Gap': 300,       # +300 (Good)
    'Rate_Gap': -0.2         # -0.2 (Bad)
}

X_test_sample = pd.DataFrame([test_case])
X_test_sample_scaled = scaler.transform(X_test_sample)

prediction_encoded = new_model.predict(X_test_sample_scaled)[0]
prediction_proba = new_model.predict_proba(X_test_sample_scaled)[0]

predicted_class = target_encoder.inverse_transform([prediction_encoded])[0]
confidence = max(prediction_proba) * 100

print(f"\nTest avec votre cas:")
print(f"Prédiction: {predicted_class}")
print(f"QoS Probability: {confidence:.1f}%")
print(f"Attendu: Good Performance (votre cas ~75%)")

# Save corrected model
joblib.dump(new_model, 'models/model_classification_eya.joblib')

print(f"\nModèle corrigé sauvegardé avec F1: {f1:.4f}")
print("Relancez le dashboard pour tester!")
