import pandas as pd
import numpy as np
import joblib
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score, f1_score
import warnings
warnings.filterwarnings('ignore')

# Charger les données (utiliser le même dataset que dans vos notebooks)
print("🔄 Chargement des données...")
df = pd.read_csv('network_slicing_congestion_final.csv')

# Vérifier les colonnes
print(f"📊 Colonnes trouvées: {list(df.columns)}")
print(f"📊 Shape initial: {df.shape}")

# Si une seule colonne, essayer avec un autre délimiteur
if len(df.columns) == 1:
    print("🔄 Tentative avec délimiteur point-virgule...")
    df = pd.read_csv('network_slicing_congestion_final.csv', sep=';')
    print(f"📊 Colonnes avec ';': {list(df.columns)}")

# Préparation des données (comme dans vos notebooks)
print("📊 Préparation des données...")
# Supprimer les classes avec trop peu d'échantillons pour éviter les erreurs
df_filtered = df[df['congestion_class'] != 2].copy()  # Garder seulement classes 0 et 1

# Features brutes (sans data leakage)
feature_cols = [
    'Packet Loss Budget', 'Latency Budget (μs)', 'Jitter Budget (μs)', 
    'Data Rate Budget (Gbps)', 'Required Mobility', 'Required Connectivity',
    'Slice Available Transfer Rate (Gbps)', 'Slice Latency (μs)', 
    'Slice Packet Loss', 'Slice Jitter (μs)', 'Slice Type', 'Slice Handover'
]

X = df_filtered[feature_cols].copy()
y = df_filtered['congestion_class'].copy()

# Encodage des features catégorielles
categorical_cols = ['Required Mobility', 'Required Connectivity', 'Slice Type']
label_encoders = {}

for col in categorical_cols:
    le = LabelEncoder()
    X[col] = le.fit_transform(X[col].astype(str))
    label_encoders[col] = le

# Encodage de la target
target_encoder = LabelEncoder()
y_encoded = target_encoder.fit_transform(y)

print(f"✅ Classes encodées: {dict(zip(target_encoder.classes_.astype(str), range(len(target_encoder.classes_))))}")

# Split train/test
X_train, X_test, y_train, y_test = train_test_split(
    X, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded
)

# Scaling
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# Entraîner XGBoost (meilleur modèle selon vos résultats)
print("🚀 Entraînement du modèle XGBoost...")
from xgboost import XGBClassifier

model = XGBClassifier(
    n_estimators=100,
    max_depth=6,
    learning_rate=0.1,
    random_state=42,
    eval_metric='logloss'
)

model.fit(X_train_scaled, y_train)

# Évaluation
y_pred = model.predict(X_test_scaled)
accuracy = accuracy_score(y_test, y_pred)
f1 = f1_score(y_test, y_pred, average='weighted')

print(f"📈 Performance du modèle:")
print(f"   Accuracy: {accuracy:.4f}")
print(f"   F1-Score: {f1:.4f}")

print("\n📊 Rapport de classification:")
print(classification_report(y_test, y_pred, 
                          target_names=[str(cls) for cls in target_encoder.classes_]))

# Sauvegarder le modèle et les préprocesseurs
print("💾 Sauvegarde du modèle...")
joblib.dump(model, 'models/model_6G_5_1_xgboost.joblib')
joblib.dump(scaler, 'models/scaler_6G_5_1.joblib')
joblib.dump(label_encoders, 'models/label_encoders_6G_5_1.joblib')
joblib.dump(target_encoder, 'models/target_encoder_6G_5_1.joblib')
joblib.dump(feature_cols, 'models/feature_cols_6G_5_1.joblib')

print("✅ Modèle de classification sauvegardé avec succès!")
print(f"📁 Fichiers créés dans models/")
print(f"🎯 Prêt pour le dashboard!")
