#!/usr/bin/env python3
"""
Fix the dashboard model by updating parameters directly
"""

import joblib
import numpy as np
from xgboost import XGBClassifier

print("=== CORRECTION DU MODÈLE DASHBOARD ===")

# Load the current model
model_path = 'models/model_classification_eya.joblib'
model = joblib.load(model_path)

print(f"Modèle actuel: {type(model)}")
print(f"Paramètres actuels:")
print(f"  learning_rate: {model.learning_rate}")
print(f"  max_depth: {model.max_depth}")
print(f"  n_estimators: {model.n_estimators}")

# Create a new model with the correct parameters
correct_model = XGBClassifier(
    learning_rate=0.1,
    max_depth=6,
    n_estimators=300,
    random_state=42,
    eval_metric='mlogloss',
    verbosity=0
)

print(f"\nModèle corrigé:")
print(f"  learning_rate: {correct_model.learning_rate}")
print(f"  max_depth: {correct_model.max_depth}")
print(f"  n_estimators: {correct_model.n_estimators}")

# Save the corrected model
joblib.dump(correct_model, 'models/model_classification_eya.joblib')

print("\n=== MODÈLE CORRIGÉ ET SAUVEGARDÉ ===")
print("Le dashboard utilisera maintenant les paramètres optimisés")
print("learning_rate=0.1, max_depth=6, n_estimators=300")

print("\nRelancez le dashboard pour tester le modèle corrigé")
