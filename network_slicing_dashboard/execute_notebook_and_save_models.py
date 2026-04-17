#!/usr/bin/env python3
"""
Script pour exécuter le notebook de Eya et sauvegarder ses modèles automatiquement
"""

import os
import sys
import joblib
import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

# Ajouter le répertoire parent au path pour importer les modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def execute_notebook_and_save_models():
    """
    Exécute le notebook model_evaluation.ipynb et sauvegarde les modèles
    """
    print("=== EXÉCUTION DU NOTEBOOK DE EYA ET SAUVEGARDE DES MODÈLES ===")
    
    try:
        # Importer les modules nécessaires pour exécuter le notebook
        from sklearn.model_selection import train_test_split
        from sklearn.preprocessing import StandardScaler, LabelEncoder
        from sklearn.metrics import f1_score, r2_score, mean_squared_error, mean_absolute_error
        from xgboost import XGBClassifier
        from sklearn.ensemble import RandomForestRegressor
        
        print("1. Chargement des données exactes du notebook de Eya...")
        
        # === PARTIE CLASSIFICATION (Objectif 5.1) ===
        print("\n--- Classification Congestion ---")
        
        # Charger les données exactement comme Eya
        df = pd.read_csv('network_slicing_congestion_final.csv', sep=',')
        print(f"Dataset classification: {df.shape}")
        
        # Features exactes de Eya (sans data leakage)
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
        
        print(f"Features utilisées: {list(X_clean.columns)}")
        
        # Filtrage classe 2 exact comme Eya
        valid_indices = y_clean != 2
        X_clean_filtered = X_clean[valid_indices]
        y_clean_filtered = y_clean[valid_indices]
        
        # Split exact de Eya
        X_train_c, X_test_c, y_train_c, y_test_c = train_test_split(
            X_clean_filtered, y_clean_filtered, test_size=0.2, random_state=42, stratify=y_clean_filtered
        )
        
        # Preprocessing exact de Eya
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train_c)
        X_test_scaled = scaler.transform(X_test_c)
        
        # Encoding exact de Eya
        class_mapping = {0: 'Normal', 1: 'Light', 3: 'Critical'}
        y_train_classes = y_train_c.map(class_mapping)
        y_test_classes = y_test_c.map(class_mapping)
        
        le = LabelEncoder()
        y_train_encoded = le.fit_transform(y_train_classes)
        y_test_encoded = le.transform(y_test_classes)
        
        print(f"Classes encodées: {dict(zip(le.classes_, le.transform(le.classes_)))}")
        
        # XGBoost exact de Eya
        best_xgb_clf = XGBClassifier(
            learning_rate=0.1, 
            max_depth=6, 
            n_estimators=300,
            random_state=42, 
            eval_metric='mlogloss', 
            verbosity=0
        )
        
        print("2. Entraînement du modèle de classification de Eya...")
        best_xgb_clf.fit(X_train_scaled, y_train_encoded)
        
        # Évaluation
        y_pred_tuned_clf = le.inverse_transform(best_xgb_clf.predict(X_test_scaled))
        f1 = f1_score(y_test_classes, y_pred_tuned_clf, average='weighted')
        print(f"F1-Score classification: {f1:.4f}")
        
        # === PARTIE RÉGRESSION (Objectif 5.2) ===
        print("\n--- Régression QoS ---")
        
        # Charger les données de régression exactement comme Eya
        df_reg = pd.read_csv('network_slicing_dataset_6G_final.csv', sep=';')
        print(f"Dataset régression: {df_reg.shape}")
        
        # Feature engineering exact de Eya
        epsilon = 1e-9
        
        def safe_sigmoid(x):
            x = np.clip(x, -10, 10)
            return 1 / (1 + np.exp(-x))
        
        # Gaps exacts de Eya (avec gestion robuste des caractères)
        cols = df_reg.columns.tolist()
        latency_budget_col = [c for c in cols if 'Latency Budget' in c][0]
        slice_latency_col = [c for c in cols if 'Slice Latency' in c][0]
        packet_loss_budget_col = [c for c in cols if 'Packet Loss Budget' in c][0]
        slice_packet_loss_col = [c for c in cols if 'Slice Packet Loss' in c][0]
        jitter_budget_col = [c for c in cols if 'Jitter Budget' in c][0]
        slice_jitter_col = [c for c in cols if 'Slice Jitter' in c][0]
        rate_budget_col = [c for c in cols if 'Data Rate Budget' in c][0]
        slice_rate_col = [c for c in cols if 'Slice Available Transfer Rate' in c][0]
        
        print(f"Colonnes trouvées:")
        print(f"  Latency: {latency_budget_col} - {slice_latency_col}")
        print(f"  Packet Loss: {packet_loss_budget_col} - {slice_packet_loss_col}")
        print(f"  Jitter: {jitter_budget_col} - {slice_jitter_col}")
        print(f"  Rate: {rate_budget_col} - {slice_rate_col}")
        
        df_reg['Latency_Gap'] = df_reg[latency_budget_col] - df_reg[slice_latency_col]
        df_reg['Packet_Loss_Gap'] = df_reg[packet_loss_budget_col] - df_reg[slice_packet_loss_col]
        df_reg['Jitter_Gap'] = df_reg[jitter_budget_col] - df_reg[slice_jitter_col]
        df_reg['Rate_Gap'] = df_reg[slice_rate_col] - df_reg[rate_budget_col]
        
        # Scores exacts de Eya
        df_reg['Latency_Score'] = safe_sigmoid(df_reg['Latency_Gap'] / (df_reg[latency_budget_col] + epsilon))
        df_reg['Packet_Loss_Score'] = safe_sigmoid(df_reg['Packet_Loss_Gap'] / (df_reg[packet_loss_budget_col] + epsilon))
        df_reg['Jitter_Score'] = safe_sigmoid(df_reg['Jitter_Gap'] / (df_reg[jitter_budget_col] + epsilon))
        df_reg['Rate_Score'] = safe_sigmoid(df_reg['Rate_Gap'] / (df_reg[rate_budget_col] + epsilon))
        
        # Target exact de Eya
        df_reg['QoS_Probability'] = (
            df_reg['Latency_Score'] + df_reg['Packet_Loss_Score'] +
            df_reg['Jitter_Score'] + df_reg['Rate_Score']
        ) / 4
        df_reg['QoS_Probability'] = df_reg['QoS_Probability'].clip(0, 1).fillna(0)
        
        print(f"QoS_Probability moyenne: {df_reg['QoS_Probability'].mean():.4f}")
        
        # Features exactes de Eya
        X_reg = df_reg[['Latency_Gap', 'Packet_Loss_Gap', 'Jitter_Gap', 'Rate_Gap']]
        y_reg = df_reg['QoS_Probability']
        
        # Split exact de Eya
        X_train_r, X_test_r, y_train_r, y_test_r = train_test_split(
            X_reg, y_reg, test_size=0.2, random_state=42
        )
        
        # RandomForest exact de Eya
        best_rf_reg = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
        
        print("3. Entraînement du modèle de régression de Eya...")
        best_rf_reg.fit(X_train_r, y_train_r)
        
        # Évaluation
        y_pred_reg = best_rf_reg.predict(X_test_r)
        r2 = r2_score(y_test_r, y_pred_reg)
        rmse = np.sqrt(mean_squared_error(y_test_r, y_pred_reg))
        print(f"R² régression: {r2:.4f}")
        print(f"RMSE régression: {rmse:.4f}")
        
        # === SAUVEGARDE DES MODÈLES DE EYA ===
        print("\n4. Sauvegarde des modèles de Eya...")
        
        # Créer le répertoire models s'il n'existe pas
        os.makedirs('models', exist_ok=True)
        
        # Sauvegarder les modèles exacts de Eya
        joblib.dump(best_xgb_clf, 'models/model_classification_eya.joblib')
        joblib.dump(best_rf_reg, 'models/model_regression_eya.joblib')
        joblib.dump(scaler, 'models/scaler_classification_eya.joblib')
        joblib.dump(le, 'models/encoder_classification_eya.joblib')
        joblib.dump(X_clean.columns.tolist(), 'models/features_classification_eya.joblib')
        joblib.dump(X_reg.columns.tolist(), 'models/features_regression_eya.joblib')
        
        print("=== MODÈLES DE EYA SAUVEGARDÉS AVEC SUCCÈS! ===")
        print("\nFichiers créés:")
        print("  - models/model_classification_eya.joblib")
        print("  - models/model_regression_eya.joblib")
        print("  - models/scaler_classification_eya.joblib")
        print("  - models/encoder_classification_eya.joblib")
        print("  - models/features_classification_eya.joblib")
        print("  - models/features_regression_eya.joblib")
        
        return True
        
    except Exception as e:
        print(f"ERREUR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = execute_notebook_and_save_models()
    if success:
        print("\n**SUCCÈS! Les modèles de Eya sont prêts pour le dashboard!**")
    else:
        print("\n**ERREUR! Vérifiez les logs ci-dessus.**")
