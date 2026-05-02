#!/usr/bin/env python
"""
Script d'initialisation de la base de données
Crée les tables et ajoute des données de test
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
from datetime import datetime, timedelta
from sqlalchemy.engine import make_url
import pymysql
import json
import random

load_dotenv(override=True)

from app import create_app, db
from app.models import Anomaly


def ensure_database_exists():
    """Create the configured MySQL database if it does not already exist."""
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        return

    url = make_url(database_url)
    if not url.drivername.startswith('mysql') or not url.database:
        return

    database_name = url.database
    print(f"Ensuring database exists: {database_name}")
    connection = pymysql.connect(
        host=url.host or 'localhost',
        port=url.port or 3306,
        user=url.username or 'root',
        password=url.password or '',
        charset='utf8mb4',
        autocommit=True
    )
    try:
        with connection.cursor() as cursor:
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{database_name}`")
    finally:
        connection.close()


def init_database():
    """Initialiser la base de données"""
    ensure_database_exists()
    app = create_app()
    
    with app.app_context():
        # Créer les tables
        print("Creating database tables...")
        db.create_all()
        print("✓ Tables created successfully")
        
        # Ajouter des données de test
        print("\nAdding test data...")
        add_test_data(app)
        print("✓ Test data added successfully")
        
        print("\n" + "=" * 60)
        print("Database initialization completed!")
        print("=" * 60)
        print("\nYou can now run the Flask app:")
        print("  python run.py")

def add_test_data(app):
    """Ajouter des données de test"""
    
    # Vérifier si des données existent déjà
    if Anomaly.query.first():
        print("  Database already contains data. Skipping test data insertion.")
        return
    
    slices = ['slice_001', 'slice_002', 'slice_003']
    methods = ['isolation_forest', 'autoencoder']
    
    # Générer 20 enregistrements de test
    base_time = datetime.utcnow() - timedelta(days=7)
    
    for i in range(20):
        slice_id = random.choice(slices)
        method = random.choice(methods)
        
        # 30% de chance d'être une anomalie
        is_anomaly = random.random() < 0.3
        
        # Score plus haut si anomalie
        if is_anomaly:
            score = random.uniform(0.7, 0.95)
        else:
            score = random.uniform(0.1, 0.4)
        
        # Générer des features réalistes
        features = {
            'bandwidth': random.uniform(50, 100) if not is_anomaly else random.uniform(10, 40),
            'latency': random.uniform(5, 15) if not is_anomaly else random.uniform(30, 60),
            'jitter': random.uniform(1, 3) if not is_anomaly else random.uniform(5, 10),
            'packet_loss': random.uniform(0.1, 1) if not is_anomaly else random.uniform(3, 8)
        }
        
        # Isolation Forest score
        if_score = random.uniform(0.6, 0.95) if is_anomaly else random.uniform(0.1, 0.4)
        
        # Autoencoder score
        ae_score = random.uniform(0.6, 0.95) if is_anomaly else random.uniform(0.1, 0.4)
        
        anomaly = Anomaly(
            slice_id=slice_id,
            score=score,
            is_anomaly=is_anomaly,
            method=method,
            isolation_forest_score=if_score,
            autoencoder_score=ae_score,
            features_json=json.dumps(features),
            created_at=base_time + timedelta(hours=i * 8)
        )
        
        db.session.add(anomaly)
        print(f"  ✓ Added: {slice_id} - Anomaly: {is_anomaly} (score: {score:.3f})")
    
    db.session.commit()

if __name__ == "__main__":
    try:
        init_database()
    except Exception as e:
        print(f"\n✗ Error during initialization: {e}")
        sys.exit(1)
