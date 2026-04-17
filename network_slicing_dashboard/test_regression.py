import pandas as pd
import numpy as np

print("Test simple régression...")

# Chargement
df_reg = pd.read_csv('network_slicing_dataset_6G_final.csv', sep=';')
print(f"Shape: {df_reg.shape}")
print(f"Colonnes: {list(df_reg.columns)}")

# Test accès colonne
print(f"Test accès 'Latency Budget (µs)': {'Latency Budget (µs)' in df_reg.columns}")

if 'Latency Budget (µs)' in df_reg.columns:
    print(f"Première valeur Latency Budget: {df_reg['Latency Budget (µs)'].iloc[0]}")
    print(f"Première valeur Slice Latency: {df_reg['Slice Latency (µs)'].iloc[0]}")
    
    # Test calcul gap
    gap = df_reg['Latency Budget (µs)'].iloc[0] - df_reg['Slice Latency (µs)'].iloc[0]
    print(f"Gap calculé: {gap}")
else:
    print("ERREUR: Colonne 'Latency Budget (µs)' non trouvée!")
