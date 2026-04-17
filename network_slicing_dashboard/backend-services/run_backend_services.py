#!/usr/bin/env python3
"""
Run all backend services without Docker
"""

import subprocess
import time
import sys
import os
import signal
from multiprocessing import Process

def run_service(service_path, port, name):
    """Run a service as a subprocess"""
    try:
        print(f"Starting {name} on port {port}...")
        
        # Change to service directory
        os.chdir(service_path)
        
        # Install dependencies
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                       capture_output=True)
        
        # Run the service
        process = subprocess.Popen([
            sys.executable, "main.py"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait a bit for service to start
        time.sleep(3)
        
        print(f"Service {name} started successfully!")
        return process
    except Exception as e:
        print(f"Error starting {name}: {e}")
        return None

def main():
    print("=== 6G/5G Network Slicing Backend Services ===")
    print("Starting all backend services...")
    
    # Get current directory
    current_dir = os.getcwd()
    print(f"Current directory: {current_dir}")
    
    services = []
    
    try:
        # Start API Gateway
        api_gateway_path = os.path.join(current_dir, "api-gateway")
        if os.path.exists(api_gateway_path):
            proc = run_service(api_gateway_path, 8000, "API Gateway")
            if proc:
                services.append(proc)
        
        # Start 6G Prediction Service
        sixg_path = os.path.join(current_dir, "6g-prediction-service")
        if os.path.exists(sixg_path):
            proc = run_service(sixg_path, 8001, "6G Prediction Service")
            if proc:
                services.append(proc)
        
        # Start 5G Prediction Service
        fiveg_path = os.path.join(current_dir, "5g-prediction-service")
        if os.path.exists(fiveg_path):
            proc = run_service(fiveg_path, 8002, "5G Prediction Service")
            if proc:
                services.append(proc)
        
        # Start Trustworthy AI Service
        trustworthy_path = os.path.join(current_dir, "trustworthy-ai-service")
        if os.path.exists(trustworthy_path):
            proc = run_service(trustworthy_path, 8003, "Trustworthy AI Service")
            if proc:
                services.append(proc)
        
        # Start Monitoring Service
        monitoring_path = os.path.join(current_dir, "monitoring-service")
        if os.path.exists(monitoring_path):
            proc = run_service(monitoring_path, 8004, "Monitoring Service")
            if proc:
                services.append(proc)
        
        print("\n=== All Backend Services Started ===")
        print("API Gateway: http://localhost:8000")
        print("6G Prediction Service: http://localhost:8001")
        print("5G Prediction Service: http://localhost:8002")
        print("Trustworthy AI Service: http://localhost:8003")
        print("Monitoring Service: http://localhost:8004")
        print("\nPress Ctrl+C to stop all services...")
        
        # Keep services running
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nStopping all services...")
        for proc in services:
            if proc:
                proc.terminate()
        print("All services stopped!")
    
    except Exception as e:
        print(f"Error: {e}")
        # Cleanup on error
        for proc in services:
            if proc:
                proc.terminate()

if __name__ == "__main__":
    main()
