#!/usr/bin/env python3
"""
Create a simple trained model - avoid encoding issues
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

print("=== CRÉATION MODÈLE ENTRAÎNÉ SIMPLE ===")

# Load dataset
df = pd.read_csv('C:/Users/EYA/PI/network_slicing_dataset_6G_final.csv', sep=';')
print(f"Dataset shape: {df.shape}")
print(f"Colonnes: {list(df.columns)}")

# Create realistic target using column indices
def create_realistic_target(df):
    conditions = []
    for _, row in df.iterrows():
        score = 0
        
        # Use column indices to avoid encoding issues
        packet_loss = row.iloc[0]      # Packet Loss Budget
        latency_budget = row.iloc[1]   # Latency Budget (µs)
        jitter_budget = row.iloc[2]    # Jitter Budget (µs)
        data_rate = row.iloc[3]        # Data Rate Budget (Gbps)
        mobility = row.iloc[4]         # Required Mobility
        connectivity = row.iloc[5]     # Required Connectivity
        slice_rate = row.iloc[6]       # Slice Available Transfer Rate (Gbps)
        slice_latency = row.iloc[7]    # Slice Latency (µs)
        slice_packet_loss = row.iloc[8] # Slice Packet Loss
        slice_jitter = row.iloc[9]     # Slice Jitter (µs)
        slice_type = row.iloc[10]       # Slice Type
        slice_handover = row.iloc[11]   # Slice Handover
        
        # Scoring system
        if latency_budget > 5000:
            score += 2
        elif latency_budget > 2000:
            score += 1
        if packet_loss > 0.01:
            score += 2
        elif packet_loss > 0.005:
            score += 1
        if slice_rate < 1.0:
            score += 1
        if slice_latency > latency_budget:
            score += 1
        if jitter_budget > 2000:
            score += 1
        if slice_jitter > 1000:
            score += 1
        
        # Class assignment
        if score >= 5:
            conditions.append('Critical')
        elif score >= 3:
            conditions.append('Light')
        else:
            conditions.append('Normal')
    return pd.Series(conditions)

df['congestion_level'] = create_realistic_target(df)

# Check class distribution
print(f"Class distribution:")
print(df['congestion_level'].value_counts())

# Prepare features using actual column names
features = list(df.columns)[:-1]  # All columns except target
print(f"Features: {features}")

X = df[features].copy()
y = df['congestion_level']

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
print("Le dashboard utilisera maintenant un modèle entraîné optimisé")

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
