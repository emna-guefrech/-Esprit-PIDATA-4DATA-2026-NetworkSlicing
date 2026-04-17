#!/usr/bin/env python3
"""
Simple fix for encoders - just update the existing files
"""

import pandas as pd
import numpy as np
import joblib
import os

print("Fixing encoders for consistent column names...")

# Load existing encoders
try:
    encoders = joblib.load('models/encoder_classification_eya.joblib')
    print("Loaded existing encoders")
    
    # Create mapping
    column_mapping = {
        'Latency Budget (µs)': 'Latency Budget (mus)',
        'Jitter Budget (µs)': 'Jitter Budget (mus)',
        'Slice Latency (µs)': 'Slice Latency (mus)',
        'Slice Jitter (µs)': 'Slice Jitter (mus)'
    }
    
    # Update encoder classes to use new names
    for cat_feat in encoders:
        if hasattr(encoders[cat_feat], 'classes_'):
            # Update class names
            old_classes = encoders[cat_feat].classes_
            new_classes = np.array([column_mapping.get(cls, cls) for cls in old_classes])
            encoders[cat_feat].classes_ = new_classes
    
    # Save updated encoders
    joblib.dump(encoders, 'models/encoder_classification_eya_fixed_encoding.joblib')
    print("Encoders updated and saved!")
    
except Exception as e:
    print(f"Error updating encoders: {e}")

# Also update the model loader to use fixed encoders
try:
    import shutil
    # Backup original
    shutil.copy('models/encoder_classification_eya.joblib', 'models/encoder_classification_eya_backup.joblib')
    # Copy fixed version as main
    shutil.copy('models/encoder_classification_eya_fixed_encoding.joblib', 'models/encoder_classification_eya.joblib')
    print("Model loader updated!")
    
except Exception as e:
    print(f"Error updating model loader: {e}")

print("Encoding fix completed!")
