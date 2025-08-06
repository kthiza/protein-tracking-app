#!/usr/bin/env python3
"""
Comprehensive test script for Protein Tracker App
Tests: register -> verify -> login -> update weight -> dashboard
"""

import requests
import json
import sys

def test_registration():
    """Test user registration"""
    print("🔵 Step 1: Testing user registration...")
    
    register_data = {
        "username": "testuser",
        "email": "testuser@example.com",
        "password": "testpass123"
    }
    
    try:
        response = requests.post("http://localhost:8000/auth/register", data=register_data)
        print(f"Registration Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Registration successful!")
            print(f"User ID: {result.get('user_id')}")
            print(f"Username: {result.get('username')}")
            print(f"Email: {result.get('email')}")
            return True
        else:
            print(f"❌ Registration failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Registration error: {e}")
        return False

def test_verification(token):
    """Test email verification"""
    print(f"\n🔵 Step 2: Testing email verification with token: {token}")
    
    try:
        response = requests.get(f"http://localhost:8000/auth/verify/{token}")
        print(f"Verification Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Email verification successful!")
            print(f"Message: {result.get('message')}")
            return True
        else:
            print(f"❌ Verification failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Verification error: {e}")
        return False

def test_login():
    """Test user login"""
    print("\n🔵 Step 3: Testing user login...")
    
    login_data = {
        "username": "testuser",
        "password": "testpass123"
    }
    
    try:
        response = requests.post("http://localhost:8000/auth/login", data=login_data)
        print(f"Login Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Login successful!")
            print(f"User ID: {result.get('user_id')}")
            print(f"Username: {result.get('username')}")
            print(f"Token: {result.get('token')}")
            return result.get('token')
        else:
            print(f"❌ Login failed: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Login error: {e}")
        return None

def test_weight_update(token):
    """Test weight update"""
    print("\n🔵 Step 4: Testing weight update...")
    
    headers = {"Authorization": f"Bearer {token}"}
    weight_data = {"weight_kg": "75.5"}
    
    try:
        response = requests.post("http://localhost:8000/users/update-weight", 
                               data=weight_data, headers=headers)
        print(f"Weight Update Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Weight update successful!")
            print(f"Weight: {result.get('weight_kg')} kg")
            print(f"Protein Goal: {result.get('protein_goal')} g")
            return True
        else:
            print(f"❌ Weight update failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Weight update error: {e}")
        return False

def test_dashboard(token):
    """Test dashboard access"""
    print("\n🔵 Step 5: Testing dashboard access...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get("http://localhost:8000/dashboard", headers=headers)
        print(f"Dashboard Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Dashboard access successful!")
            print(f"User: {result.get('user', {}).get('username')}")
            print(f"Weight: {result.get('user', {}).get('weight_kg')} kg")
            print(f"Protein Goal: {result.get('user', {}).get('protein_goal')} g")
            print(f"Today's Protein: {result.get('today', {}).get('total_protein')} g")
            return True
        else:
            print(f"❌ Dashboard access failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Dashboard error: {e}")
        return False

def test_food_suggestions():
    """Test food suggestions endpoint"""
    print("\n🔵 Step 6: Testing food suggestions...")
    
    try:
        response = requests.get("http://localhost:8000/foods/suggestions")
        print(f"Food Suggestions Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Food suggestions successful!")
            print(f"Total foods: {result.get('total_foods')}")
            print(f"Categories: {list(result.get('categories', {}).keys())}")
            return True
        else:
            print(f"❌ Food suggestions failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Food suggestions error: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Protein Tracker App - Comprehensive Test Suite")
    print("=" * 50)
    
    # Test 1: Registration (skip if user exists)
    if not test_registration():
        print("\n⚠️  User already exists, proceeding with verification...")
    
    # Test 2: Verification (requires manual token)
    print("\n⚠️  For verification, you need to:")
    print("1. Check the server logs for the verification token")
    print("2. Look for: 'Email verification token for testuser: [TOKEN]'")
    print("3. Run this script again with the token as argument")
    print("\nExample: python test_complete_flow.py YOUR_TOKEN_HERE")
    
    if len(sys.argv) > 1:
        token = sys.argv[1]
        if not test_verification(token):
            print("\n❌ Test failed at verification step")
            return
        
        # Test 3: Login
        auth_token = test_login()
        if not auth_token:
            print("\n❌ Test failed at login step")
            return
        
        # Test 4: Weight Update
        if not test_weight_update(auth_token):
            print("\n❌ Test failed at weight update step")
            return
        
        # Test 5: Dashboard
        if not test_dashboard(auth_token):
            print("\n❌ Test failed at dashboard step")
            return
        
        # Test 6: Food Suggestions
        if not test_food_suggestions():
            print("\n❌ Test failed at food suggestions step")
            return
        
        print("\n🎉 All tests completed successfully!")
    else:
        print("\n📝 To complete the test, run with verification token:")
        print("python test_complete_flow.py YOUR_TOKEN_HERE")

if __name__ == "__main__":
    main() 