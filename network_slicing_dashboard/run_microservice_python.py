#!/usr/bin/env python3
"""
Run microservice architecture with Python (without Docker)
"""

import subprocess
import time
import os
import signal
import sys
from multiprocessing import Process

def run_service(script_path, port, name):
    """Run a service as a subprocess"""
    try:
        print(f"Starting {name} on port {port}...")
        process = subprocess.Popen([
            sys.executable, script_path
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait a bit for service to start
        time.sleep(3)
        
        print(f"Service {name} started successfully!")
        return process
    except Exception as e:
        print(f"Error starting {name}: {e}")
        return None

def check_port(port):
    """Check if port is available"""
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('localhost', port))
    sock.close()
    return result != 0

def main():
    print("=== 6G Network Slicing Microservice Architecture ===")
    print("Starting services without Docker...")
    
    # Check if required ports are available
    required_ports = [8000, 8001, 8002, 8003, 8004, 8500]
    for port in required_ports:
        if not check_port(port):
            print(f"Port {port} is already in use!")
            return
    
    services = []
    
    try:
        # Start API Gateway
        if os.path.exists("api-gateway/main.py"):
            proc = run_service("api-gateway/main.py", 8000, "API Gateway")
            if proc:
                services.append(proc)
        
        # Start Prediction Service
        if os.path.exists("prediction-service/main.py"):
            proc = run_service("prediction-service/main.py", 8001, "Prediction Service")
            if proc:
                services.append(proc)
        
        # Start Model Service
        if os.path.exists("model-service/main.py"):
            proc = run_service("model-service/main.py", 8002, "Model Service")
            if proc:
                services.append(proc)
        
        # Start Trustworthy AI Service
        if os.path.exists("trustworthy-ai-service/main.py"):
            proc = run_service("trustworthy-ai-service/main.py", 8003, "Trustworthy AI Service")
            if proc:
                services.append(proc)
        
        # Start Monitoring Service
        if os.path.exists("monitoring-service/main.py"):
            proc = run_service("monitoring-service/main.py", 8004, "Monitoring Service")
            if proc:
                services.append(proc)
        
        # Start Frontend Service
        if os.path.exists("frontend-service/app.py"):
            proc = run_service("frontend-service/app.py", 8500, "Frontend Service")
            if proc:
                services.append(proc)
        
        print("\n=== All Services Started ===")
        print("API Gateway: http://localhost:8000")
        print("Frontend: http://localhost:8500")
        print("Prediction Service: http://localhost:8001")
        print("Model Service: http://localhost:8002")
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
