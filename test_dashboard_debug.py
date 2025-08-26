#!/usr/bin/env python3
"""
Debug script to test dashboard functionality and identify issues with goal persistence
"""

import requests
import json
import os
from datetime import datetime

def test_dashboard_functionality():
    """Test the dashboard functionality to identify issues"""
    
    # Get the base URL from environment or use default
    base_url = os.getenv('APP_BASE_URL', 'http://127.0.0.1:8000')
    
    print(f"🔍 Testing dashboard functionality at: {base_url}")
    print(f"⏰ Test time: {datetime.now()}")
    
    # Test 1: Check if the server is running
    try:
        response = requests.get(f"{base_url}/", timeout=10)
        print(f"✅ Server is running (status: {response.status_code})")
    except Exception as e:
        print(f"❌ Server is not running: {e}")
        return
    
    # Test 2: Check database connection
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        if response.status_code == 200:
            health_data = response.json()
            print(f"✅ Database connection: {health_data.get('database', 'Unknown')}")
        else:
            print(f"⚠️  Health check failed (status: {response.status_code})")
    except Exception as e:
        print(f"⚠️  Health check error: {e}")
    
    # Test 3: Check if there are any users in the database
    try:
        response = requests.get(f"{base_url}/users", timeout=10)
        if response.status_code == 200:
            users_data = response.json()
            print(f"✅ Users in database: {len(users_data.get('users', []))}")
            
            # Show user details if any exist
            for user in users_data.get('users', [])[:3]:  # Show first 3 users
                print(f"   - User: {user.get('username', 'Unknown')} (ID: {user.get('id', 'Unknown')})")
                print(f"     Protein goal: {user.get('protein_goal', 'Not set')}")
                print(f"     Calorie goal: {user.get('calorie_goal', 'Not set')}")
        else:
            print(f"⚠️  Users endpoint failed (status: {response.status_code})")
    except Exception as e:
        print(f"⚠️  Users endpoint error: {e}")
    
    # Test 4: Check environment variables
    print("\n🔧 Environment Variables:")
    env_vars = [
        'DATABASE_URL',
        'APP_BASE_URL',
        'GOOGLE_SERVICE_ACCOUNT',
        'SMTP_SERVER'
    ]
    
    for var in env_vars:
        value = os.getenv(var)
        if value:
            # Mask sensitive values
            if 'password' in var.lower() or 'key' in var.lower() or 'secret' in var.lower():
                masked_value = value[:10] + '...' if len(value) > 10 else '***'
                print(f"   {var}: {masked_value}")
            else:
                print(f"   {var}: {value}")
        else:
            print(f"   {var}: Not set")
    
    # Test 5: Check database type
    database_url = os.getenv('DATABASE_URL', 'sqlite:///./protein_app.db')
    if 'sqlite' in database_url:
        print("\n⚠️  WARNING: Using SQLite database")
        print("   - On Render free tier, SQLite databases are ephemeral")
        print("   - Data will be lost on service restarts")
        print("   - Consider using PostgreSQL for data persistence")
    elif 'postgresql' in database_url:
        print("\n✅ Using PostgreSQL database (persistent)")
    else:
        print(f"\n⚠️  Unknown database type: {database_url}")
    
    print("\n🎯 Recommendations:")
    print("1. If using Render free tier, consider upgrading to paid plan for PostgreSQL")
    print("2. Or use external database service (Railway, Supabase, Neon)")
    print("3. Check if user goals are being saved correctly in settings")
    print("4. Verify that the dashboard endpoint returns fresh user data")

if __name__ == "__main__":
    test_dashboard_functionality()
