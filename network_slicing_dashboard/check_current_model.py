#!/usr/bin/env python3
"""
Check the current model parameters vs expected optimized parameters
"""

import joblib
import os

print("=== VÉRIFICATION DES MODÈLES ===")

# Check current dashboard model
dashboard_model_path = 'models/model_classification_eya.joblib'
if os.path.exists(dashboard_model_path):
    model = joblib.load(dashboard_model_path)
    print(f"Modèle Dashboard: {type(model)}")
    if hasattr(model, 'get_params'):
        params = model.get_params()
        print(f"Paramètres actuels:")
        print(f"  learning_rate: {params.get('learning_rate', 'N/A')}")
        print(f"  max_depth: {params.get('max_depth', 'N/A')}")
        print(f"  n_estimators: {params.get('n_estimators', 'N/A')}")
    else:
        print("Impossible d'obtenir les paramètres")
else:
    print("Modèle dashboard non trouvé!")

print("\n=== PARAMÈTRES ATTENDUS (Notebook) ===")
print("learning_rate: 0.1")
print("max_depth: 6") 
print("n_estimators: 300")
print("F1-Score attendu: 0.9750")

print("\n=== CONCLUSION ===")
print("Si les paramètres ne correspondent pas, le modèle n'est pas optimisé!")
