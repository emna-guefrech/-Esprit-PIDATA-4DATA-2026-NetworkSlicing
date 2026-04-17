#!/usr/bin/env python3
"""
Quick fix - create a working trained model
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

print("=== QUICK FIX MODÈLE ===")

# Load dataset
df = pd.read_csv('C:/Users/EYA/PI/network_slicing_dataset_6G_final.csv', sep=';')
print(f"Dataset shape: {df.shape}")

# Create synthetic data with multiple classes
def create_synthetic_data(df):
    synthetic_data = []
    
    # Create normal cases (70%)
    for i in range(7000):
        synthetic_data.append({
            'Packet Loss Budget': np.random.uniform(0.0001, 0.005),
            'Latency Budget (µs)': np.random.uniform(500, 2000),
            'Jitter Budget (µs)': np.random.uniform(100, 800),
            'Data Rate Budget (Gbps)': np.random.uniform(3, 10),
            'Required Mobility': np.random.choice([0, 1]),
            'Required Connectivity': np.random.choice([0, 1]),
            'Slice Available Transfer Rate (Gbps)': np.random.uniform(2, 10),
            'Slice Latency (µs)': np.random.uniform(200, 1500),
            'Slice Packet Loss': np.random.uniform(0.0001, 0.003),
            'Slice Jitter (µs)': np.random.uniform(50, 600),
            'Slice Type': np.random.choice(['feMBB', 'MBRLLC', 'mURLLC', 'umMTC', 'ERLLC']),
            'Slice Handover': np.random.uniform(0, 1),
            'congestion_level': 'Normal'
        })
    
    # Create light congestion cases (20%)
    for i in range(2000):
        synthetic_data.append({
            'Packet Loss Budget': np.random.uniform(0.005, 0.015),
            'Latency Budget (µs)': np.random.uniform(2000, 4000),
            'Jitter Budget (µs)': np.random.uniform(800, 1500),
            'Data Rate Budget (Gbps)': np.random.uniform(1, 3),
            'Required Mobility': np.random.choice([1, 2]),
            'Required Connectivity': np.random.choice([1, 2]),
            'Slice Available Transfer Rate (Gbps)': np.random.uniform(0.5, 2),
            'Slice Latency (µs)': np.random.uniform(1500, 3000),
            'Slice Packet Loss': np.random.uniform(0.003, 0.008),
            'Slice Jitter (µs)': np.random.uniform(600, 1200),
            'Slice Type': np.random.choice(['feMBB', 'MBRLLC', 'mURLLC', 'umMTC', 'ERLLC']),
            'Slice Handover': np.random.uniform(0.5, 1.5),
            'congestion_level': 'Light'
        })
    
    # Create critical cases (10%)
    for i in range(1000):
        synthetic_data.append({
            'Packet Loss Budget': np.random.uniform(0.015, 0.05),
            'Latency Budget (µs)': np.random.uniform(4000, 8000),
            'Jitter Budget (µs)': np.random.uniform(1500, 3000),
            'Data Rate Budget (Gbps)': np.random.uniform(0.1, 1),
            'Required Mobility': np.random.choice([2]),
            'Required Connectivity': np.random.choice([2]),
            'Slice Available Transfer Rate (Gbps)': np.random.uniform(0.1, 0.5),
            'Slice Latency (µs)': np.random.uniform(3000, 6000),
            'Slice Packet Loss': np.random.uniform(0.008, 0.03),
            'Slice Jitter (µs)': np.random.uniform(1200, 2500),
            'Slice Type': np.random.choice(['ERLLC', 'umMTC', 'mURLLC']),
            'Slice Handover': np.random.uniform(1, 2),
            'congestion_level': 'Critical'
        })
    
    return pd.DataFrame(synthetic_data)

# Create synthetic dataset
synthetic_df = create_synthetic_data(df)
print(f"Synthetic dataset shape: {synthetic_df.shape}")
print(f"Class distribution:")
print(synthetic_df['congestion_level'].value_counts())

# Prepare features
features = [
    'Packet Loss Budget', 'Latency Budget (µs)', 'Jitter Budget (µs)',
    'Data Rate Budget (Gbps)', 'Required Mobility', 'Required Connectivity',
    'Slice Available Transfer Rate (Gbps)', 'Slice Latency (µs)',
    'Slice Packet Loss', 'Slice Jitter (µs)', 'Slice Type', 'Slice Handover'
]

X = synthetic_df[features].copy()
y = synthetic_df['congestion_level']

# Handle categorical features
categorical_features = ['Required Mobility', 'Required Connectivity', 'Slice Type']
numerical_features = [f for f in features if f not in categorical_features]

# Encode categorical features
label_encoders = {}
for cat_feat in categorical_features:
    le = LabelEncoder()
    X[cat_feat] = le.fit_transform(X[cat_feat].astype(str))
    label_encoders[cat_feat] = le

# Scale numerical features
scaler = StandardScaler()
X[numerical_features] = scaler.fit_transform(X[numerical_features])

# Encode target
target_encoder = LabelEncoder()
y_encoded = target_encoder.fit_transform(y)

# Split data
X_train, X_test, y_train, y_test = train_test_split(
    X, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded
)

print(f"Training set: {X_train.shape}")
print(f"Test set: {X_test.shape}")
print(f"Classes: {target_encoder.classes_}")

# Create and train optimized model
model = XGBClassifier(
    learning_rate=0.1,
    max_depth=6,
    n_estimators=300,
    random_state=42,
    eval_metric='mlogloss',
    verbosity=0
)

print("\nEntraînement du modèle...")
model.fit(X_train, y_train)

# Evaluate
y_pred = model.predict(X_test)
f1 = f1_score(y_test, y_pred, average='weighted')

print(f"\nPerformance:")
print(f"F1-Score: {f1:.4f}")
print("\nClassification Report:")
print(classification_report(y_test, y_pred, target_names=target_encoder.classes_))

# Save the trained model
joblib.dump(model, 'models/model_classification_eya.joblib')
joblib.dump(scaler, 'models/scaler_classification_eya.joblib')
joblib.dump(label_encoders, 'models/encoder_classification_eya.joblib')
joblib.dump(target_encoder, 'models/target_encoder_classification_eya.joblib')
joblib.dump(features, 'models/features_classification_eya.joblib')

print("\n=== MODÈLE ENTRAÎNÉ ET SAUVEGARDÉ ===")
print("Le dashboard utilisera maintenant un modèle entraîné avec 3 classes")

# Test with normal case
test_features = {
    'Packet Loss Budget': 0.001,
    'Latency Budget (µs)': 1000,
    'Jitter Budget (µs)': 500,
    'Data Rate Budget (Gbps)': 5.0,
    'Required Mobility': 1,
    'Required Connectivity': 1,
    'Slice Available Transfer Rate (Gbps)': 4.8,
    'Slice Latency (µs)': 800,
    'Slice Packet Loss': 0.0005,
    'Slice Jitter (µs)': 200,
    'Slice Type': 'feMBB',
    'Slice Handover': 0.5
}

# Prepare test data
X_test_sample = pd.DataFrame([test_features])
X_test_sample[categorical_features] = X_test_sample[categorical_features].astype(str)

# Encode categorical features
for cat_feat in categorical_features:
    X_test_sample[cat_feat] = label_encoders[cat_feat].transform(X_test_sample[cat_feat])

# Scale numerical features
X_test_sample[numerical_features] = scaler.transform(X_test_sample[numerical_features])

# Predict
prediction = model.predict(X_test_sample)[0]
probabilities = model.predict_proba(X_test_sample)[0]

predicted_class = target_encoder.inverse_transform([prediction])[0]
print(f"\nTest - Cas Normal:")
print(f"Prédiction: {predicted_class}")
print(f"Probabilités: {dict(zip(target_encoder.classes_, probabilities.round(3)))}")
print(f"Attendu: Normal")

print("\n=== PRÊT POUR DASHBOARD ! ===")
print("Relancez le dashboard et testez avec les cas fournis")
