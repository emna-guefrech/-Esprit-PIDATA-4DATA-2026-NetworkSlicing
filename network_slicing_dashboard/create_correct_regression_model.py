#!/usr/bin/env python3
"""
Créer le modèle de régression avec les vraies features du notebook
"""

import pandas as pd
import numpy as np
import joblib
from sklearn.ensemble import RandomForestRegressor

print("🔧 CRÉATION DU MODÈLE AVEC VRAIES FEATURES DU NOTEBOOK")

# Charger les données exactes comme Eya
df_reg = pd.read_csv('network_slicing_dataset_6G_final.csv', sep=';')

# Feature engineering EXACT comme Eya (avec les vraies statistiques)
epsilon = 1e-9

def safe_sigmoid(x):
    x = np.clip(x, -10, 10)
    return 1 / (1 + np.exp(-x))

# Colonnes exactes
cols = df_reg.columns.tolist()
latency_budget_col = [c for c in cols if 'Latency Budget' in c][0]
slice_latency_col = [c for c in cols if 'Slice Latency' in c][0]
packet_loss_budget_col = [c for c in cols if 'Packet Loss Budget' in c][0]
slice_packet_loss_col = [c for c in cols if 'Slice Packet Loss' in c][0]
jitter_budget_col = [c for c in cols if 'Jitter Budget' in c][0]
slice_jitter_col = [c for c in cols if 'Slice Jitter' in c][0]
rate_budget_col = [c for c in cols if 'Data Rate Budget' in c][0]
slice_rate_col = [c for c in cols if 'Slice Available Transfer Rate' in c][0]

# Gaps EXACTS comme Eya (avec les vraies valeurs négatives)
df_reg['Latency_Gap'] = df_reg[latency_budget_col] - df_reg[slice_latency_col]
df_reg['Packet_Loss_Gap'] = df_reg[packet_loss_budget_col] - df_reg[slice_packet_loss_col]
df_reg['Jitter_Gap'] = df_reg[jitter_budget_col] - df_reg[slice_jitter_col]
df_reg['Rate_Gap'] = df_reg[slice_rate_col] - df_reg[rate_budget_col]

# Scores EXACTS comme Eya
df_reg['Latency_Score'] = safe_sigmoid(df_reg['Latency_Gap'] / (df_reg[latency_budget_col] + epsilon))
df_reg['Packet_Loss_Score'] = safe_sigmoid(df_reg['Packet_Loss_Gap'] / (df_reg[packet_loss_budget_col] + epsilon))
df_reg['Jitter_Score'] = safe_sigmoid(df_reg['Jitter_Gap'] / (df_reg[jitter_budget_col] + epsilon))
df_reg['Rate_Score'] = safe_sigmoid(df_reg['Rate_Gap'] / (df_reg[rate_budget_col] + epsilon))

# Target EXACT comme Eya
df_reg['QoS_Probability'] = (
    df_reg['Latency_Score'] + df_reg['Packet_Loss_Score'] +
    df_reg['Jitter_Score'] + df_reg['Rate_Score']
) / 4
df_reg['QoS_Probability'] = df_reg['QoS_Probability'].clip(0, 1).fillna(0)

print(f"📈 Vraies statistiques des gaps:")
print(f"  Latency_Gap: min={df_reg['Latency_Gap'].min():.2f}, max={df_reg['Latency_Gap'].max():.2f}, mean={df_reg['Latency_Gap'].mean():.2f}")
print(f"  Packet_Loss_Gap: min={df_reg['Packet_Loss_Gap'].min():.4f}, max={df_reg['Packet_Loss_Gap'].max():.4f}, mean={df_reg['Packet_Loss_Gap'].mean():.4f}")
print(f"  Jitter_Gap: min={df_reg['Jitter_Gap'].min():.2f}, max={df_reg['Jitter_Gap'].max():.2f}, mean={df_reg['Jitter_Gap'].mean():.2f}")
print(f"  Rate_Gap: min={df_reg['Rate_Gap'].min():.2f}, max={df_reg['Rate_Gap'].max():.2f}, mean={df_reg['Rate_Gap'].mean():.2f}")

print(f"🎯 Vraie QoS_Probability: min={df_reg['QoS_Probability'].min():.4f}, max={df_reg['QoS_Probability'].max():.4f}, mean={df_reg['QoS_Probability'].mean():.4f}")

# Features EXACTES du notebook
X_reg = df_reg[['Latency_Gap', 'Packet_Loss_Gap', 'Jitter_Gap', 'Rate_Gap']]
y_reg = df_reg['QoS_Probability']

# Créer le modèle EXACT du notebook
best_rf_reg = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)

print("Entraînement avec les vraies features du notebook...")
best_rf_reg.fit(X_reg, y_reg)

# Test avec les mêmes paramètres que le dashboard utilise
test_gaps = np.array([[2000, -0.005, 1000, 1.5]])  # Test Low Risk
prediction = best_rf_reg.predict(test_gaps)[0]

print(f"🎯 Prédiction avec vraies features [2000, -0.005, 1000, 1.5]: {prediction:.4f}")

# Sauvegarder le modèle CORRECT
import os
os.makedirs('models', exist_ok=True)
joblib.dump(best_rf_reg, 'models/model_regression_eya_correct.joblib')
joblib.dump(X_reg.columns.tolist(), 'models/features_regression_eya_correct.joblib')

print("✅ MODÈLE CORRECT CRÉÉ ET SAUVEGARDÉ!")
print(f"📁 models/model_regression_eya_correct.joblib")
print(f"📁 models/features_regression_eya_correct.joblib")
