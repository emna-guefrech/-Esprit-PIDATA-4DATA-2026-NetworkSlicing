#!/usr/bin/env python3
"""
Fix encoders to use consistent column names
"""

import pandas as pd
import numpy as np
import joblib
import os

print("Fixing encoders for consistent column names...")

# Load the dataset
dataset_path = 'C:/Users/EYA/PI/network_slicing_dataset_6G_final.csv'
df = pd.read_csv(dataset_path, sep=';')

# Create column mapping
column_mapping = {
    'Latency Budget (µs)': 'Latency Budget (mus)',
    'Jitter Budget (µs)': 'Jitter Budget (mus)',
    'Slice Latency (µs)': 'Slice Latency (mus)',
    'Slice Jitter (µs)': 'Slice Jitter (mus)'
}

# Apply mapping to data
df_fixed = df.copy()
df_fixed.columns = [column_mapping.get(col, col) for col in df_fixed.columns]

# Re-train the encoders with fixed column names
categorical_features = ['Required Mobility', 'Required Connectivity', 'Slice Type']

from sklearn.preprocessing import LabelEncoder
from sklearn.preprocessing import StandardScaler

# Create new encoders
new_encoders = {}
for cat_feat in categorical_features:
    if cat_feat in df_fixed.columns:
        le = LabelEncoder()
        df_fixed[cat_feat] = le.fit_transform(df_fixed[cat_feat].astype(str))
        new_encoders[cat_feat] = le

# Create new scaler
numerical_features = [f for f in df_fixed.columns if f not in categorical_features]
new_scaler = StandardScaler()
df_fixed[numerical_features] = new_scaler.fit_transform(df_fixed[numerical_features])

# Save the fixed preprocessors
models_dir = 'C:/Users\EYA\PI\network_slicing_dashboard/models'
os.makedirs(models_dir, exist_ok=True)

joblib.dump(new_encoders, f'{models_dir}/encoder_classification_eya_fixed_encoding.joblib')
joblib.dump(new_scaler, f'{models_dir}/scaler_classification_eya_fixed_encoding.joblib')

# Save the fixed features list
features_fixed = list(df_fixed.columns)
joblib.dump(features_fixed, f'{models_dir}/features_classification_eya_fixed_encoding.joblib')

print("Encoders fixed and saved!")
print(f"Features: {features_fixed}")
print(f"Encoders: {list(new_encoders.keys())}")

# Test loading
print("\nTesting fixed encoders...")
test_encoders = joblib.load(f'{models_dir}/encoder_classification_eya_fixed_encoding.joblib')
test_features = joblib.load(f'{models_dir}/features_classification_eya_fixed_encoding.joblib')

print(f"Loaded encoders: {list(test_encoders.keys())}")
print(f"Loaded features: {test_features}")

print("Encoders fix completed!")
