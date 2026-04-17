#!/usr/bin/env python3
"""
Extraction EXACTE des modèles du notebook model_evaluation.ipynb
Utilise les mêmes paramètres, prétraitement et logique que Eya
"""

import pandas as pd
import numpy as np
import joblib
import warnings
warnings.filterwarnings('ignore')

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import (classification_report, r2_score, 
                             mean_squared_error, mean_absolute_error, f1_score)
from xgboost import XGBClassifier
from sklearn.ensemble import RandomForestRegressor

print("=== Extraction des modèles de Eya (model_evaluation.ipynb) ===")

# === 1. Classification (Objectif 5.1) ===
print("\n1. Classification Congestion - Exactement comme dans le notebook")

# Chargement données EXACTES comme Eya
df = pd.read_csv('network_slicing_congestion_final.csv', sep=',')
print(f"Dataset chargé: {df.shape}")

# Features EXACTES comme Eya (sans data leakage)
colonnes_a_exclure = [
    'congestion_class',
    'Latency_Gap', 'Packet_Loss_Gap', 'Jitter_Gap', 'Rate_Gap',
    'Latency_Score', 'Packet_Loss_Score', 'Jitter_Score', 'Rate_Score',
    'QoS_Probability', 'Efficiency_Index', 'Aggregated_QoS_Score',
    'SLA_Respected', 'Latency_Stress_Ratio', 'Mobility_Jitter_Impact',
    'Bandwidth_Usage_Ratio',
]
colonnes_a_exclure = [c for c in colonnes_a_exclure if c in df.columns]

X_clean = df.drop(columns=colonnes_a_exclure)
y_clean = df['congestion_class']

print(f"Features utilisées: {X_clean.columns.tolist()}")

# Filtrage classe 2 comme Eya
valid_indices = y_clean != 2
X_clean_filtered = X_clean[valid_indices]
y_clean_filtered = y_clean[valid_indices]

print(f"Distribution après filtrage: {y_clean_filtered.value_counts().sort_index().to_dict()}")

# Split COMME Eya
X_train_c, X_test_c, y_train_c, y_test_c = train_test_split(
    X_clean_filtered, y_clean_filtered, test_size=0.2, random_state=42, stratify=y_clean_filtered
)

# Scaling COMME Eya
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train_c)
X_test_scaled = scaler.transform(X_test_c)

# Encoding COMME Eya
class_mapping = {0: 'Normal', 1: 'Light', 3: 'Critical'}
y_train_classes = y_train_c.map(class_mapping)
y_test_classes = y_test_c.map(class_mapping)

le = LabelEncoder()
y_train_encoded = le.fit_transform(y_train_classes)
y_test_encoded = le.transform(y_test_classes)

print(f"Classes encodées: {dict(zip(le.classes_, le.transform(le.classes_)))}")

# XGBoost tuné COMME Eya
best_xgb_clf = XGBClassifier(
    learning_rate=0.1, 
    max_depth=6, 
    n_estimators=300,
    random_state=42, 
    eval_metric='mlogloss', 
    verbosity=0
)

print("Entraînement XGBoost (paramètres de Eya)...")
best_xgb_clf.fit(X_train_scaled, y_train_encoded)

# Évaluation COMME Eya
y_pred_tuned_clf = le.inverse_transform(best_xgb_clf.predict(X_test_scaled))
f1_score = f1_score(y_test_classes, y_pred_tuned_clf, average='weighted')

print(f"F1-Score obtenu: {f1_score:.4f} (attendu: ~0.9754)")

# Sauvegarde modèle classification
joblib.dump(best_xgb_clf, 'models/model_6G_5_1_eya_exact.joblib')
joblib.dump(scaler, 'models/scaler_6G_5_1_eya_exact.joblib')
joblib.dump(le, 'models/target_encoder_6G_5_1_eya_exact.joblib')
joblib.dump(X_clean.columns.tolist(), 'models/feature_cols_6G_5_1_eya_exact.joblib')

print("=== Classification sauvegardée ===")

# === 2. Régression (Objectif 5.2) ===
print("\n2. Régression QoS - Exactement comme dans le notebook")

# Chargement données EXACTES comme Eya
df_reg = pd.read_csv('network_slicing_dataset_6G_final.csv', sep=';')
print(f"Dataset régression: {df_reg.shape}")
print(f"Colonnes: {list(df_reg.columns)}")

# Feature engineering EXACT comme Eya
epsilon = 1e-9

def safe_sigmoid(x):
    x = np.clip(x, -10, 10)
    return 1 / (1 + np.exp(-x))

# Gaps COMME Eya
df_reg['Latency_Gap']     = df_reg['Latency Budget (µs)']                  - df_reg['Slice Latency (µs)']
df_reg['Packet_Loss_Gap'] = df_reg['Packet Loss Budget']                   - df_reg['Slice Packet Loss']
df_reg['Jitter_Gap']      = df_reg['Jitter Budget (µs)']                  - df_reg['Slice Jitter (µs)']
df_reg['Rate_Gap']        = df_reg['Slice Available Transfer Rate (Gbps)'] - df_reg['Data Rate Budget (Gbps)']

# Scores COMME Eya
df_reg['Latency_Score']     = safe_sigmoid(df_reg['Latency_Gap']     / (df_reg['Latency Budget (µs)'] + epsilon))
df_reg['Packet_Loss_Score'] = safe_sigmoid(df_reg['Packet_Loss_Gap'] / (df_reg['Packet Loss Budget'] + epsilon))
df_reg['Jitter_Score']      = safe_sigmoid(df_reg['Jitter_Gap']      / (df_reg['Jitter Budget (µs)'] + epsilon))
df_reg['Rate_Score']        = safe_sigmoid(df_reg['Rate_Gap']        / (df_reg['Data Rate Budget (Gbps)'] + epsilon))

# Target COMME Eya
df_reg['QoS_Probability'] = (
    df_reg['Latency_Score'] + df_reg['Packet_Loss_Score'] +
    df_reg['Jitter_Score']  + df_reg['Rate_Score']
) / 4
df_reg['QoS_Probability'] = df_reg['QoS_Probability'].clip(0, 1).fillna(0)

print(f"QoS_Probability: mean={df_reg['QoS_Probability'].mean():.4f}")

# Features COMME Eya
X_reg = df_reg[['Latency_Gap', 'Packet_Loss_Gap', 'Jitter_Gap', 'Rate_Gap']]
y_reg = df_reg['QoS_Probability']

# Split COMME Eya
X_train_r, X_test_r, y_train_r, y_test_r = train_test_split(
    X_reg, y_reg, test_size=0.2, random_state=42
)

# RandomForest COMME Eya (meilleur modèle)
best_rf_reg = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)

print("Entraînement RandomForest (paramètres de Eya)...")
best_rf_reg.fit(X_train_r, y_train_r)

# Évaluation COMME Eya
y_pred_reg = best_rf_reg.predict(X_test_r)
r2 = r2_score(y_test_r, y_pred_reg)
rmse = np.sqrt(mean_squared_error(y_test_r, y_pred_reg))

print(f"R² obtenu: {r2:.4f} (attendu: ~0.8451)")
print(f"RMSE obtenu: {rmse:.4f} (attendu: ~0.0167)")

# Sauvegarde modèle régression
joblib.dump(best_rf_reg, 'models/model_6G_5_2_eya_exact.joblib')
joblib.dump(X_reg.columns.tolist(), 'models/feature_cols_6G_5_2_eya_exact.joblib')

print("=== Régression sauvegardée ===")
print("\n=== Tous les modèles de Eya extraits avec succès ! ===")
