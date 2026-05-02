#!/usr/bin/env python3
"""
MS-3 Dashboard & Alerts Service Launcher
Network Slicing Microservice - Dashboard & Alerts (MS-3)
"""

import sys
import os
import subprocess
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_dependencies():
    """Check if required dependencies are installed"""
    logger.info("MS-3: Checking dependencies...")
    
    required_packages = [
        'flask',
        'flask_sqlalchemy', 
        'pymysql',
        'requests'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            logger.info(f"MS-3: ✓ {package} is installed")
        except ImportError:
            missing_packages.append(package)
            logger.error(f"MS-3: ✗ {package} is missing")
    
    if missing_packages:
        logger.error(f"MS-3: Missing packages: {', '.join(missing_packages)}")
        logger.info("MS-3: Install with: pip install -r ms3_requirements.txt")
        return False
    
    logger.info("MS-3: All dependencies satisfied")
    return True

def start_ms3_service():
    """Start the MS-3 Dashboard & Alerts Service"""
    logger.info("=" * 60)
    logger.info("MS-3: Dashboard & Alerts Service")
    logger.info("Network Slicing Microservice")
    logger.info("=" * 60)
    
    if not check_dependencies():
        sys.exit(1)
    
    logger.info("MS-3: Starting Dashboard & Alerts Service...")
    logger.info("MS-3: Service will be available at http://localhost:5003")
    logger.info("MS-3: Dashboard UI at http://localhost:5003/")
    logger.info("MS-3: Health check at http://localhost:5003/ms3/health")
    logger.info("MS-3: Press Ctrl+C to stop the service")
    logger.info("-" * 60)
    
    try:
        # Import and run the MS-3 service
        from ms3_dashboard_service import app
        app.run(debug=False, host='0.0.0.0', port=5003)
    except KeyboardInterrupt:
        logger.info("MS-3: Service stopped by user")
    except Exception as e:
        logger.error(f"MS-3: Service failed to start: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    start_ms3_service()
