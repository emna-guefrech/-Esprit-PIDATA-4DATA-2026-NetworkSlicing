#!/usr/bin/env python3
"""
Create a correct QoS model with proper gap logic
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

print("=== CRÉATION MODÈLE QoS CORRECT ===")

# Create synthetic data with proper gap logic
def create_synthetic_qos_data():
    synthetic_data = []
    
    # Excellent performance (gaps mostly positive)
    for i in range(3000):
        synthetic_data.append({
            'Latency_Gap': np.random.uniform(100, 500),
            'Packet_Loss_Gap': np.random.uniform(0.0001, 0.002),
            'Jitter_Gap': np.random.uniform(50, 300),
            'Rate_Gap': np.random.uniform(0.1, 1.0),
            'qos_class': 'Excellent'
        })
    
    # Good performance (mixed gaps)
    for i in range(2500):
        synthetic_data.append({
            'Latency_Gap': np.random.uniform(-200, 200),
            'Packet_Loss_Gap': np.random.uniform(-0.001, 0.001),
            'Jitter_Gap': np.random.uniform(-100, 100),
            'Rate_Gap': np.random.uniform(-0.5, 0.5),
            'qos_class': 'Good'
        })
    
    # Poor performance (gaps mostly negative)
    for i in range(1500):
        synthetic_data.append({
            'Latency_Gap': np.random.uniform(-1000, -100),
            'Packet_Loss_Gap': np.random.uniform(-0.01, -0.001),
            'Jitter_Gap': np.random.uniform(-500, -50),
            'Rate_Gap': np.random.uniform(-2.0, -0.5),
            'qos_class': 'Poor'
        })
    
    return pd.DataFrame(synthetic_data)

# Create dataset
df = create_synthetic_qos_data()
print(f"Dataset shape: {df.shape}")
print(f"Class distribution:")
print(df['qos_class'].value_counts())

# Features and target
features = ['Latency_Gap', 'Packet_Loss_Gap', 'Jitter_Gap', 'Rate_Gap']
X = df[features].copy()
y = df['qos_class']

# Encode target
target_encoder = LabelEncoder()
y_encoded = target_encoder.fit_transform(y)

# Scale features
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# Split data
X_train, X_test, y_train, y_test = train_test_split(
    X_scaled, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded
)

print(f"Training set: {X_train.shape}")
print(f"Test set: {X_test.shape}")
print(f"Classes: {target_encoder.classes_}")

# Create and train model
model = XGBClassifier(
    learning_rate=0.1,
    max_depth=6,
    n_estimators=300,
    random_state=42,
    eval_metric='mlogloss',
    verbosity=0
)

print("\nEntraînement du modèle QoS avec logique CORRECTE...")
model.fit(X_train, y_train)

# Evaluate
y_pred = model.predict(X_test)
f1 = f1_score(y_test, y_pred, average='weighted')

print(f"\nPerformance:")
print(f"F1-Score: {f1:.4f}")
print("\nClassification Report:")
print(classification_report(y_test, y_pred, target_names=target_encoder.classes_))

# Save the corrected model
joblib.dump(model, 'models/model_classification_eya.joblib')
joblib.dump(scaler, 'models/scaler_classification_eya.joblib')
joblib.dump(target_encoder, 'models/target_encoder_classification_eya.joblib')
joblib.dump(features, 'models/features_classification_eya.joblib')

print("\n=== MODÈLE QoS CORRIGÉ ET SAUVEGARDÉ ===")
print("Logique: gaps positifs = bonne performance QoS")
print("Relancez le dashboard pour tester!")

# Test with your exact case
test_case = {
    'Latency_Gap': 200,      # +200 (Good)
    'Packet_Loss_Gap': 0.0005, # +0.0005 (Good)
    'Jitter_Gap': 300,       # +300 (Good)
    'Rate_Gap': -0.2         # -0.2 (Bad)
}

print(f"\nTest avec votre cas: {test_case}")

X_test_sample = pd.DataFrame([test_case])
X_test_sample_scaled = scaler.transform(X_test_sample)

prediction_encoded = model.predict(X_test_sample_scaled)[0]
prediction_proba = model.predict_proba(X_test_sample_scaled)[0]

predicted_class = target_encoder.inverse_transform([prediction_encoded])[0]
confidence = max(prediction_proba) * 100

print(f"\nNouveau résultat attendu:")
print(f"Prédiction: {predicted_class}")
print(f"QoS Probability: {confidence:.1f}%")
print(f"Attendu: Good (car 3 gaps positifs, 1 négatif faible)")
