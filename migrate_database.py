#!/usr/bin/env python
"""
Database migration - Add email fields to existing users table
"""

import pymysql
import sys

def migrate_database():
    """Add email columns to users table"""
    
    try:
        # Connect to MySQL
        connection = pymysql.connect(
            host='127.0.0.1',
            user='root',
            password='',
            port=3306,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        print("✓ Connected to MySQL")
        
        with connection.cursor() as cursor:
            # Select database
            cursor.execute("USE network_slicing")
            print("✓ Using network_slicing database")
            
            # Check if email column exists
            print("\n📋 Checking for email column...")
            cursor.execute("""
                SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = 'users' AND COLUMN_NAME = 'email'
            """)
            
            if not cursor.fetchone():
                print("❌ Email column missing - Adding columns...")
                
                # Add email column
                cursor.execute("""
                    ALTER TABLE users 
                    ADD COLUMN email VARCHAR(120) UNIQUE NOT NULL DEFAULT 'user@localhost'
                """)
                print("✓ Added email column")
                
                # Add email_verified column
                cursor.execute("""
                    ALTER TABLE users 
                    ADD COLUMN email_verified BOOLEAN DEFAULT FALSE
                """)
                print("✓ Added email_verified column")
                
                # Add OTP columns
                cursor.execute("""
                    ALTER TABLE users 
                    ADD COLUMN otp_code VARCHAR(6) DEFAULT NULL
                """)
                print("✓ Added otp_code column")
                
                cursor.execute("""
                    ALTER TABLE users 
                    ADD COLUMN otp_expiry DATETIME DEFAULT NULL
                """)
                print("✓ Added otp_expiry column")
                
                # Add reset token columns
                cursor.execute("""
                    ALTER TABLE users 
                    ADD COLUMN reset_token VARCHAR(100) UNIQUE DEFAULT NULL
                """)
                print("✓ Added reset_token column")
                
                cursor.execute("""
                    ALTER TABLE users 
                    ADD COLUMN reset_token_expiry DATETIME DEFAULT NULL
                """)
                print("✓ Added reset_token_expiry column")
                
                # Add email index
                cursor.execute("""
                    ALTER TABLE users 
                    ADD INDEX idx_email (email)
                """)
                print("✓ Added email index")
                
                connection.commit()
                
                print("\n" + "="*60)
                print("✅ DATABASE MIGRATION COMPLETE!")
                print("="*60)
                print("\nEmail columns successfully added to users table.")
                print("\nNext steps:")
                print("1. Run the application again: python run.py")
                print("2. The admin user will be created automatically")
                
            else:
                print("✓ Email column already exists")
                print("✓ Database is up to date")
                
    except pymysql.Error as e:
        print(f"\n❌ MySQL Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
    finally:
        if 'connection' in locals():
            connection.close()

if __name__ == '__main__':
    migrate_database()
