"""
Script de test pour l'API Anomaly Detection Service
Utilise des données d'exemple pour tester les 3 endpoints
"""

import requests
import json
from datetime import datetime, timedelta
import time

API_BASE_URL = "http://localhost:5000/api"

def test_api():
    print("=" * 70)
    print("Anomaly Detection Service - API Testing")
    print("=" * 70)
    
    # Test 1: POST /anomaly/detect
    print("\n[TEST 1] POST /api/anomaly/detect")
    print("-" * 70)
    
    test_cases = [
        {
            "slice_id": "slice_001",
            "features": {
                "bandwidth": 85.5,
                "latency": 12.3,
                "jitter": 2.1,
                "packet_loss": 1.0
            }
        },
        {
            "slice_id": "slice_002",
            "features": {
                "bandwidth": 92.1,
                "latency": 8.7,
                "jitter": 1.5,
                "packet_loss": 0.5
            }
        },
        {
            "slice_id": "slice_003",
            "features": {
                "bandwidth": 65.2,
                "latency": 25.8,
                "jitter": 4.3,
                "packet_loss": 2.5
            }
        },
        {
            "slice_id": "slice_001",
            "features": {
                "bandwidth": 15.0,  # Anomalique - très bas
                "latency": 50.0,     # Anomalique - très haut
                "jitter": 8.0,       # Anomalique
                "packet_loss": 5.0   # Anomalique - élevé
            }
        }
    ]
    
    detected_anomalies = []
    
    for i, test_case in enumerate(test_cases):
        try:
            response = requests.post(
                f"{API_BASE_URL}/anomaly/detect",
                json=test_case,
                timeout=5
            )
            
            if response.status_code == 201:
                data = response.json()
                print(f"\n✓ Test case {i+1}: SUCCESS")
                print(f"  Slice ID: {test_case['slice_id']}")
                print(f"  Is Anomaly: {data['data']['is_anomaly']}")
                print(f"  Score: {data['data']['score']}")
                print(f"  Confidence: {data['data']['confidence']}")
                print(f"  Method: {data['data']['method']}")
                
                if data['data']['is_anomaly']:
                    detected_anomalies.append(test_case['slice_id'])
            else:
                print(f"\n✗ Test case {i+1}: FAILED")
                print(f"  Status: {response.status_code}")
                print(f"  Error: {response.text}")
        
        except Exception as e:
            print(f"\n✗ Test case {i+1}: ERROR")
            print(f"  Exception: {str(e)}")
        
        time.sleep(0.5)  # Petit délai entre les requêtes
    
    # Test 2: GET /anomaly/history
    print("\n\n[TEST 2] GET /api/anomaly/history")
    print("-" * 70)
    
    try:
        # Sans filtres
        response = requests.get(
            f"{API_BASE_URL}/anomaly/history?limit=10&offset=0",
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✓ Get all anomalies: SUCCESS")
            print(f"  Total in DB: {data['data']['total']}")
            print(f"  Returned count: {data['data']['count']}")
            print(f"  Anomalies:")
            
            for anomaly in data['data']['anomalies'][:3]:  # Afficher les 3 premiers
                print(f"    - ID: {anomaly['id']}, Slice: {anomaly['slice_id']}, " +
                      f"Anomaly: {anomaly['is_anomaly']}, Score: {anomaly['score']}")
        else:
            print(f"✗ FAILED: {response.status_code}")
    
    except Exception as e:
        print(f"✗ ERROR: {str(e)}")
    
    # Filtrer par slice_id
    if detected_anomalies:
        try:
            response = requests.get(
                f"{API_BASE_URL}/anomaly/history?slice_id={detected_anomalies[0]}&is_anomaly=true",
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"\n✓ Filter by slice and anomaly: SUCCESS")
                print(f"  Found: {data['data']['count']} anomalies for {detected_anomalies[0]}")
            else:
                print(f"✗ FAILED: {response.status_code}")
        
        except Exception as e:
            print(f"✗ ERROR: {str(e)}")
    
    # Test 3: GET /anomaly/stats
    print("\n\n[TEST 3] GET /api/anomaly/stats")
    print("-" * 70)
    
    try:
        response = requests.get(
            f"{API_BASE_URL}/anomaly/stats?days=7",
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✓ Get statistics: SUCCESS")
            print(f"  Total detections: {data['data']['total_detections']}")
            print(f"  Total anomalies: {data['data']['total_anomalies']}")
            print(f"  Anomaly rate: {data['data']['anomaly_rate']}%")
            
            if data['data']['by_slice']:
                print(f"\n  By Slice:")
                for slice_id, stats in list(data['data']['by_slice'].items())[:3]:
                    print(f"    - {slice_id}: {stats['anomalies']}/{stats['total']} " +
                          f"({stats['rate']}%)")
            
            if data['data']['by_method']:
                print(f"\n  By Method:")
                for method, count in data['data']['by_method'].items():
                    print(f"    - {method}: {count} anomalies")
        else:
            print(f"✗ FAILED: {response.status_code}")
    
    except Exception as e:
        print(f"✗ ERROR: {str(e)}")
    
    print("\n" + "=" * 70)
    print("Testing completed!")
    print("=" * 70)

if __name__ == "__main__":
    try:
        print("\nWaiting for API to be available...")
        
        # Vérifier que l'API est disponible
        max_retries = 5
        for i in range(max_retries):
            try:
                requests.get(f"{API_BASE_URL}/anomaly/stats", timeout=2)
                print("✓ API is online\n")
                break
            except:
                if i < max_retries - 1:
                    print(f"  Retrying... ({i+1}/{max_retries})")
                    time.sleep(2)
                else:
                    print("✗ API is not responding. Make sure the Flask app is running:")
                    print(f"  python run.py")
                    exit(1)
        
        test_api()
    
    except KeyboardInterrupt:
        print("\n\nTesting interrupted by user")
