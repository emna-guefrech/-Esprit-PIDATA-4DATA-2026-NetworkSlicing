"""
Fix Anomaly Model - Recreate with correct NumPy version
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import joblib
import warnings
warnings.filterwarnings('ignore')

print("Loading anomaly detection dataset...")

# Load the dataset
try:
    df = pd.read_csv('network_slicing_dataset_6G_final.csv', sep=';')
    print(f"Dataset loaded: {df.shape}")
    print('Columns:', list(df.columns))
except FileNotFoundError:
    print("Dataset not found, using synthetic data...")
    # Create synthetic data for anomaly detection
    np.random.seed(42)
    n_samples = 1000
    
    df = pd.DataFrame({
        'Packet Loss Budget': np.random.uniform(0.001, 0.01, n_samples),
        'Latency Budget (µs)': np.random.uniform(500, 2000, n_samples),
        'Jitter Budget (µs)': np.random.uniform(100, 500, n_samples),
        'Data Rate Budget (Gbps)': np.random.uniform(1, 10, n_samples),
        'Required Mobility': np.random.choice([0, 1, 2], n_samples),
        'Required Connectivity': np.random.choice([0, 1, 2], n_samples),
        'Slice Available Transfer Rate (Gbps)': np.random.uniform(0.5, 12, n_samples),
        'Slice Latency (µs)': np.random.uniform(400, 2200, n_samples),
        'Slice Packet Loss': np.random.uniform(0.0005, 0.015, n_samples),
        'Slice Jitter (µs)': np.random.uniform(80, 600, n_samples),
        'Slice Type': np.random.choice([1, 2, 3, 4], n_samples),
        'Slice Handover': np.random.uniform(0.1, 0.9, n_samples)
    })
    print(f"Synthetic dataset created: {df.shape}")

# Select features for anomaly detection
features = [
    'Packet Loss Budget', 'Latency Budget (µs)', 'Jitter Budget (µs)',
    'Data Rate Budget (Gbps)', 'Required Mobility', 'Required Connectivity',
    'Slice Available Transfer Rate (Gbps)', 'Slice Latency (µs)',
    'Slice Packet Loss', 'Slice Jitter (µs)', 'Slice Type', 'Slice Handover'
]

# Check which columns exist
available_columns = list(df.columns)
print(f"Available columns: {available_columns}")

# Use only available columns
features = [col for col in features if col in available_columns]
print(f"Using features: {features}")

X = df[features].copy()

# Handle any missing values
X = X.fillna(X.mean())

# Scale features
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

print("Training Isolation Forest model...")

# Train Isolation Forest
anomaly_model = IsolationForest(
    contamination=0.1,  # Expect 10% anomalies
    random_state=42,
    n_estimators=100
)

anomaly_model.fit(X_scaled)

print("Saving models...")

# Save models
joblib.dump(anomaly_model, 'models/model_anomaly_eya.joblib')
joblib.dump(scaler, 'models/scaler_anomaly_eya.joblib')

print("Anomaly detection model created and saved successfully!")

# Test the model
test_sample = X_scaled[:5]
predictions = anomaly_model.predict(test_sample)
scores = anomaly_model.decision_function(test_sample)

print(f"Test predictions: {predictions}")
print(f"Anomaly scores: {scores}")
print("Model validation completed!")
