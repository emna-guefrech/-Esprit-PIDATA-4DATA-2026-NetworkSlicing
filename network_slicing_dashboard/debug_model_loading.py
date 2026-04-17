#!/usr/bin/env python3
"""
Debug which model is actually being loaded
"""

import joblib
import os

print("=== VÉRIFICATION DES MODÈLES CHARGÉS ===")

# Check which models exist
models = {
    'classification': 'models/model_classification_eya.joblib',
    'regression': 'models/model_6G_5_2_xgboost.joblib',
    'anomaly': 'models/model_anomaly_eya.joblib'
}

for name, path in models.items():
    if os.path.exists(path):
        model = joblib.load(path)
        print(f"✅ {name}: {type(model)}")
        if hasattr(model, 'n_features_in_'):
            print(f"   Features: {model.n_features_in_}")
        if hasattr(model, 'feature_names_in_'):
            print(f"   Feature names: {model.feature_names_in_}")
    else:
        print(f"❌ {name}: Non trouvé")

print("\n=== VÉRIFICATION DES FEATURES ===")

# Check features files
feature_files = {
    'classification': 'models/features_classification_eya.joblib',
    'regression': 'models/features_6G_5_2_eya.joblib',
    'anomaly': 'models/features_anomaly_eya.joblib'
}

for name, path in feature_files.items():
    if os.path.exists(path):
        features = joblib.load(path)
        print(f"✅ {name} features: {features}")
        print(f"   Nombre: {len(features)}")
    else:
        print(f"❌ {name} features: Non trouvé")

print("\n=== CONCLUSION ===")
print("Si le modèle de classification utilise 9 features au lieu de 4 gaps,")
print("alors il y a un problème de chargement !")
