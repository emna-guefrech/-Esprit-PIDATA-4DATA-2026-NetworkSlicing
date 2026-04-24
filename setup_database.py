#!/usr/bin/env python
"""
Database setup script - Creates MySQL database and tables automatically
No password required
"""

import pymysql
import sys

def setup_database():
    """Create database and tables"""
    
    try:
        # Connect to MySQL without password
        connection = pymysql.connect(
            host='127.0.0.1',
            user='root',
            password='',  # No password
            port=3306,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        print("✓ Connected to MySQL")
        
        with connection.cursor() as cursor:
            # Create database if not exists
            print("\n📦 Creating database 'network_slicing'...")
            cursor.execute("""
                CREATE DATABASE IF NOT EXISTS network_slicing 
                CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
            """)
            print("✓ Database created or already exists")
            
            # Select database
            cursor.execute("USE network_slicing")
            print("✓ Using network_slicing database")
            
            # Create users table
            print("\n📋 Creating users table...")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(80) UNIQUE NOT NULL,
                    email VARCHAR(120) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    role ENUM('system_admin', 'network_engineer', 'data_scientist', 'noc_operator') 
                        DEFAULT 'network_engineer',
                    is_active BOOLEAN DEFAULT TRUE,
                    email_verified BOOLEAN DEFAULT FALSE,
                    otp_code VARCHAR(6),
                    otp_expiry DATETIME,
                    reset_token VARCHAR(100) UNIQUE,
                    reset_token_expiry DATETIME,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_username (username),
                    INDEX idx_email (email)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            print("✓ Users table created")
            
            # Create alerts table (for dashboard)
            print("\n📋 Creating alerts table...")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS alerts (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    slice_id VARCHAR(100) NOT NULL,
                    level ENUM('WARN', 'CRITICAL') DEFAULT 'WARN',
                    message TEXT,
                    acknowledged BOOLEAN DEFAULT FALSE,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_slice_id (slice_id),
                    INDEX idx_level (level)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            print("✓ Alerts table created")
            
            # Create thresholds table
            print("\n📋 Creating thresholds table...")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS thresholds (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    metric VARCHAR(100) UNIQUE NOT NULL,
                    warn_value FLOAT,
                    critical_value FLOAT,
                    unit VARCHAR(50),
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_metric (metric)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            print("✓ Thresholds table created")
            
            # Create predictions table
            print("\n📋 Creating predictions table...")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS predictions (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    slice_id VARCHAR(100) NOT NULL,
                    congestion_level ENUM('Normal', 'Light', 'Critical') DEFAULT 'Normal',
                    qos_score FLOAT,
                    features_json TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_slice_id (slice_id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            print("✓ Predictions table created")
            
            # Create anomalies table
            print("\n📋 Creating anomalies table...")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS anomalies (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    slice_id VARCHAR(100) NOT NULL,
                    score FLOAT,
                    is_anomaly BOOLEAN DEFAULT FALSE,
                    method VARCHAR(100),
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_slice_id (slice_id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            print("✓ Anomalies table created")
            
            # Create model_versions table
            print("\n📋 Creating model_versions table...")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS model_versions (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    model_name VARCHAR(100) NOT NULL,
                    version VARCHAR(20),
                    r2_score FLOAT,
                    rmse FLOAT,
                    accuracy FLOAT,
                    trained_at DATETIME DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            print("✓ Model versions table created")
            
            # Create integration_logs table
            print("\n📋 Creating integration_logs table...")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS integration_logs (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    service VARCHAR(100) NOT NULL,
                    endpoint VARCHAR(255),
                    status_code INT,
                    latency_ms INT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_service (service),
                    INDEX idx_created_at (created_at)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            print("✓ Integration logs table created")
            
            # Create shap_logs table
            print("\n📋 Creating shap_logs table...")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS shap_logs (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    slice_id VARCHAR(100) NOT NULL,
                    model_version VARCHAR(20),
                    features_json TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_slice_id (slice_id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            print("✓ SHAP logs table created")
            
            connection.commit()
            print("\n" + "="*60)
            print("✅ DATABASE SETUP COMPLETE!")
            print("="*60)
            print("\nAll tables created successfully!")
            print("\nNext steps:")
            print("1. Create .env file: copy .env.example .env")
            print("2. Update .env with credentials (optional, password is blank)")
            print("3. Run the application: python run.py")
            print("4. Access: http://127.0.0.1:5000")
            
    except pymysql.Error as e:
        print(f"\n❌ MySQL Error: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure MySQL is running")
        print("2. Check if port 3306 is accessible")
        print("3. Verify MySQL root user exists with no password")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
    finally:
        if 'connection' in locals():
            connection.close()

if __name__ == '__main__':
    setup_database()
