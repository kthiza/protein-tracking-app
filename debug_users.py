#!/usr/bin/env python3
"""
Debug script to check users in the database
"""

import sqlite3
import hashlib
from datetime import datetime

def check_users():
    """Check users in the database"""
    conn = sqlite3.connect('protein_app.db')
    cursor = conn.cursor()
    
    print("=== USER DEBUG ===")
    
    # Check if user table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user'")
    if not cursor.fetchone():
        print("❌ User table does not exist!")
        return
    
    print("✅ User table exists")
    
    # Check table structure
    cursor.execute("PRAGMA table_info(user)")
    columns = cursor.fetchall()
    print("\n📋 User table structure:")
    for col in columns:
        print(f"  {col[1]} ({col[2]}) - NOT NULL: {col[3]} - DEFAULT: {col[4]}")
    
    # Get all users
    cursor.execute("SELECT * FROM user")
    users = cursor.fetchall()
    
    print(f"\n👥 Found {len(users)} users:")
    
    for user in users:
        print(f"\n👤 User: {user}")
    
    conn.close()

def create_test_user():
    """Create a test user if none exists"""
    conn = sqlite3.connect('protein_app.db')
    cursor = conn.cursor()
    
    # Check if testuser exists
    cursor.execute("SELECT id FROM user WHERE username = 'testuser'")
    if cursor.fetchone():
        print("✅ Test user already exists")
        conn.close()
        return
    
    # Get table structure to know all columns
    cursor.execute("PRAGMA table_info(user)")
    columns = [col[1] for col in cursor.fetchall()]
    print(f"Columns: {columns}")
    
    # Create test user with all required fields
    password_hash = hashlib.sha256("testpass".encode()).hexdigest()
    
    # Build the INSERT statement dynamically
    placeholders = ', '.join(['?' for _ in columns])
    column_names = ', '.join(columns)
    
    # Create values tuple with defaults for all columns
    values = {
        'username': 'testuser',
        'email': 'test@example.com',
        'password_hash': password_hash,
        'weight_kg': 70.0,
        'protein_goal': 84.0,
        'calorie_goal': 2450.0,
        'created_at': datetime.now(),
        'email_verified': True,
        'verification_token': None,
        'last_weight_update': datetime.now(),
        'activity_level': 'moderate',
        'height_cm': 175,
        'age': 30,
        'gender': 'male'
    }
    
    # Create values list in the order of columns
    value_list = [values.get(col, None) for col in columns]
    
    try:
        cursor.execute(f"INSERT INTO user ({column_names}) VALUES ({placeholders})", value_list)
        conn.commit()
        print("✅ Created test user: testuser / testpass")
    except Exception as e:
        print(f"❌ Error creating test user: {e}")
    
    conn.close()

if __name__ == "__main__":
    check_users()
    print("\n" + "="*50)
    create_test_user()
