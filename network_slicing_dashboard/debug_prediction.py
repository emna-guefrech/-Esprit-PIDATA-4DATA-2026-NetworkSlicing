import joblib

# Charger le target encoder pour voir les classes
le = joblib.load('models/target_encoder_6G_5_1.joblib')
print('Classes originales:', le.classes_)
print('Mapping:', dict(zip(le.classes_, range(len(le.classes_))))

# Tester une prédiction simple
import pandas as pd
from sklearn.preprocessing import StandardScaler

# Charger le modèle et les encodeurs
model = joblib.load('models/model_6G_5_1_xgboost.joblib')
label_encoders = joblib.load('models/label_encoders_6G_5_1.joblib')
scaler = joblib.load('models/scaler_6G_5_1.joblib')

# Features de test (bons paramètres)
test_features = {
    'Packet Loss Budget': 0.015,
    'Latency Budget (μs)': 1500,
    'Jitter Budget (μs)': 2000,
    'Data Rate Budget (Gbps)': 2.0,
    'Required Mobility': 'low',
    'Required Connectivity': 'low',
    'Slice Available Transfer Rate (Gbps)': 6.0,
    'Slice Latency (μs)': 300,
    'Slice Packet Loss': 0.001,
    'Slice Jitter (μs)': 80,
    'Slice Type': 'eMBB',
    'Slice Handover': 0.1
}

# Préparer les features
feature_order = [
    'Packet Loss Budget', 'Latency Budget (μs)', 'Jitter Budget (μs)', 
    'Data Rate Budget (Gbps)', 'Required Mobility', 'Required Connectivity',
    'Slice Available Transfer Rate (Gbps)', 'Slice Latency (μs)', 
    'Slice Packet Loss', 'Slice Jitter (μs)', 'Slice Type', 'Slice Handover'
]

feature_values = []
for feature in feature_order:
    value = test_features[feature]
    if feature in ['Required Mobility', 'Required Connectivity', 'Slice Type']:
        if feature in label_encoders:
            if value not in label_encoders[feature].classes_:
                value = label_encoders[feature].classes_[0]
            value = label_encoders[feature].transform([value])[0]
    feature_values.append(value)

X = pd.DataFrame([feature_values], columns=feature_order)
X_scaled = scaler.transform(X)

# Prédire
prediction_encoded = model.predict(X_scaled)[0]
prediction_proba = model.predict_proba(X_scaled)[0]

print('Prédiction encodée:', prediction_encoded)
print('Probabilités:', prediction_proba)
print('Classe mapping:', {0: 'Critical', 1: 'Light', 2: 'Normal'})
