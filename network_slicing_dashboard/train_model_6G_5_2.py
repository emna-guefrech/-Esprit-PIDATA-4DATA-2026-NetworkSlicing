import pandas as pd
import numpy as np
import joblib
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
import warnings
warnings.filterwarnings('ignore')

# Charger les données de régression
print("🔄 Chargement des données de régression...")
df_reg = pd.read_csv('network_slicing_dataset_6G_final.csv', sep=';')

# Feature engineering (comme dans vos notebooks)
print("📊 Feature engineering...")
epsilon = 1e-9

def safe_sigmoid(x):
    x = np.clip(x, -10, 10)
    return 1 / (1 + np.exp(-x))

# Calcul des gaps
df_reg['Latency_Gap'] = df_reg['Latency Budget (μs)'] - df_reg['Slice Latency (μs)']
df_reg['Packet_Loss_Gap'] = df_reg['Packet Loss Budget'] - df_reg['Slice Packet Loss']
df_reg['Jitter_Gap'] = df_reg['Jitter Budget (μs)'] - df_reg['Slice Jitter (μs)']
df_reg['Rate_Gap'] = df_reg['Slice Available Transfer Rate (Gbps)'] - df_reg['Data Rate Budget (Gbps)']

# Calcul de la target QoS_Probability
df_reg['Latency_Score'] = safe_sigmoid(df_reg['Latency_Gap'] / (df_reg['Latency Budget (μs)'] + epsilon))
df_reg['Packet_Loss_Score'] = safe_sigmoid(df_reg['Packet_Loss_Gap'] / (df_reg['Packet Loss Budget'] + epsilon))
df_reg['Jitter_Score'] = safe_sigmoid(df_reg['Jitter_Gap'] / (df_reg['Jitter Budget (μs)'] + epsilon))
df_reg['Rate_Score'] = safe_sigmoid(df_reg['Rate_Gap'] / (df_reg['Data Rate Budget (Gbps)'] + epsilon))

df_reg['QoS_Probability'] = (
    df_reg['Latency_Score'] + df_reg['Packet_Loss_Score'] +
    df_reg['Jitter_Score'] + df_reg['Rate_Score']
) / 4
df_reg['QoS_Probability'] = df_reg['QoS_Probability'].clip(0, 1).fillna(0)

print(f"✅ Target QoS_Probability créée")
print(f"📈 Distribution: min={df_reg['QoS_Probability'].min():.3f}, max={df_reg['QoS_Probability'].max():.3f}, mean={df_reg['QoS_Probability'].mean():.3f}")

# Features pour la régression
feature_cols_reg = ['Latency_Gap', 'Packet_Loss_Gap', 'Jitter_Gap', 'Rate_Gap']
X_reg = df_reg[feature_cols_reg]
y_reg = df_reg['QoS_Probability']

# Split train/test
X_train_reg, X_test_reg, y_train_reg, y_test_reg = train_test_split(
    X_reg, y_reg, test_size=0.2, random_state=42
)

# Scaling
scaler_reg = StandardScaler()
X_train_reg_scaled = scaler_reg.fit_transform(X_train_reg)
X_test_reg_scaled = scaler_reg.transform(X_test_reg)

# Entraîner XGBoost Regressor
print("🚀 Entraînement du modèle XGBoost Regressor...")
from xgboost import XGBRegressor

model_reg = XGBRegressor(
    n_estimators=100,
    max_depth=6,
    learning_rate=0.1,
    random_state=42
)

model_reg.fit(X_train_reg_scaled, y_train_reg)

# Évaluation
y_pred_reg = model_reg.predict(X_test_reg_scaled)
r2 = r2_score(y_test_reg, y_pred_reg)
rmse = np.sqrt(mean_squared_error(y_test_reg, y_pred_reg))
mae = mean_absolute_error(y_test_reg, y_pred_reg)

print(f"📈 Performance du modèle de régression:")
print(f"   R² Score: {r2:.4f}")
print(f"   RMSE: {rmse:.4f}")
print(f"   MAE: {mae:.4f}")

# Analyse des prédictions
print(f"📊 Analyse des prédictions:")
print(f"   Valeur réelle min: {y_test_reg.min():.3f}, max: {y_test_reg.max():.3f}")
print(f"   Prédiction min: {y_pred_reg.min():.3f}, max: {y_pred_reg.max():.3f}")

# Sauvegarder le modèle et les préprocesseurs
print("💾 Sauvegarde du modèle de régression...")
joblib.dump(model_reg, 'models/model_6G_5_2_xgboost.joblib')
joblib.dump(scaler_reg, 'models/scaler_6G_5_2.joblib')
joblib.dump(feature_cols_reg, 'models/feature_cols_6G_5_2.joblib')

print("✅ Modèle de régression sauvegardé avec succès!")
print(f"📁 Fichiers créés dans models/")
print(f"🎯 Prêt pour le dashboard!")
