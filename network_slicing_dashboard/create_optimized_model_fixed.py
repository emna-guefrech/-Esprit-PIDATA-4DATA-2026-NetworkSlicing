#!/usr/bin/env python3
"""
Create the optimized model with exact parameters from the notebook - FIXED VERSION
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

print("=== CRÉATION DU MODÈLE OPTIMISÉ ===")

# Load the dataset
df = pd.read_csv('C:/Users/EYA/PI/network_slicing_dataset_6G_final.csv', sep=';')

print(f"Dataset shape: {df.shape}")
print(f"Colonnes: {list(df.columns)}")

# Create target variable based on network conditions (same as notebook)
def create_target(df):
    conditions = []
    for _, row in df.iterrows():
        score = 0
        # Use the actual column names from the dataset
        if row['Latency Budget (µs)'] > 5000:
            score += 2
        elif row['Latency Budget (µs)'] > 2000:
            score += 1
        if row['Packet Loss Budget'] > 0.01:
            score += 2
        elif row['Packet Loss Budget'] > 0.005:
            score += 1
        if row['Slice Available Transfer Rate (Gbps)'] < 1.0:
            score += 1
        if row['Slice Latency (µs)'] > row['Latency Budget (µs)']:
            score += 1
        
        if score >= 4:
            conditions.append('Critical')
        elif score >= 2:
            conditions.append('Light')
        else:
            conditions.append('Normal')
    return pd.Series(conditions)

df['congestion_level'] = create_target(df)

# Prepare features (use actual column names)
features = [
    'Packet Loss Budget', 'Latency Budget (µs)', 'Jitter Budget (µs)',
    'Data Rate Budget (Gbps)', 'Required Mobility', 'Required Connectivity',
    'Slice Available Transfer Rate (Gbps)', 'Slice Latency (µs)',
    'Slice Packet Loss', 'Slice Jitter (µs)', 'Slice Type', 'Slice Handover'
]

print(f"Features utilisées: {features}")

X = df[features].copy()
y = df['congestion_level']

# Handle categorical features (same as notebook)
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

# Create OPTIMIZED model with exact parameters from notebook
optimized_model = XGBClassifier(
    learning_rate=0.1,
    max_depth=6,
    n_estimators=300,
    random_state=42,
    eval_metric='mlogloss',
    verbosity=0
)

print(f"\nModèle créé avec les paramètres optimisés:")
print(f"  learning_rate: {optimized_model.learning_rate}")
print(f"  max_depth: {optimized_model.max_depth}")
print(f"  n_estimators: {optimized_model.n_estimators}")

# Train the model
print("\nEntraînement du modèle optimisé...")
optimized_model.fit(X_train, y_train)

# Evaluate
y_pred = optimized_model.predict(X_test)
f1 = f1_score(y_test, y_pred, average='weighted')

print(f"\nPerformance du modèle optimisé:")
print(f"F1-Score: {f1:.4f}")
print(f"Attendu: 0.9750")

# Print classification report
print("\nClassification Report:")
print(classification_report(y_test, y_pred, target_names=target_encoder.classes_))

# Save the optimized model
joblib.dump(optimized_model, 'models/model_classification_optimized.joblib')
joblib.dump(scaler, 'models/scaler_classification_optimized.joblib')
joblib.dump(label_encoders, 'models/encoder_classification_optimized.joblib')
joblib.dump(target_encoder, 'models/target_encoder_classification_optimized.joblib')
joblib.dump(features, 'models/features_classification_optimized.joblib')

print("\n=== MODÈLE OPTIMISÉ SAUVEGARDÉ ===")
print("Fichiers créés:")
print("- model_classification_optimized.joblib")
print("- scaler_classification_optimized.joblib")
print("- encoder_classification_optimized.joblib")
print("- target_encoder_classification_optimized.joblib")
print("- features_classification_optimized.joblib")

print(f"\nPerformance finale: F1 = {f1:.4f}")
if f1 >= 0.97:
    print("MODÈLE OPTIMISÉ CRÉÉ AVEC SUCCÈS !")
else:
    print("Performance inférieure à attendue - vérifier les données")

# Test with the first test case
print("\n=== TEST AVEC LE CAS NORMAL ===")
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
prediction = optimized_model.predict(X_test_sample)[0]
probabilities = optimized_model.predict_proba(X_test_sample)[0]

predicted_class = target_encoder.inverse_transform([prediction])[0]
print(f"Prédiction: {predicted_class}")
print(f"Probabilités: {dict(zip(target_encoder.classes_, probabilities))}")
print(f"Attendu: Normal")
