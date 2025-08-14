#!/usr/bin/env python3
"""
Test script to check API endpoints for meal data
"""

import requests
import json

def test_api():
    """Test the API endpoints to see what meal data is returned"""
    base_url = "http://127.0.0.1:8000"
    
    print("=== API DEBUG ===")
    
    # First, let's try to get a token (assuming user exists)
    try:
        login_response = requests.post(f"{base_url}/auth/login", json={
            "username": "testuser",
            "password": "testpass"
        })
        
        if login_response.status_code == 200:
            token = login_response.json().get("access_token")
            headers = {"Authorization": f"Bearer {token}"}
            print("✅ Successfully logged in")
        else:
            print(f"❌ Login failed: {login_response.status_code}")
            print("Response:", login_response.text)
            return
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return
    
    # Test /meals/today endpoint
    print("\n📊 Testing /meals/today endpoint:")
    try:
        today_response = requests.get(f"{base_url}/meals/today", headers=headers)
        print(f"Status: {today_response.status_code}")
        
        if today_response.status_code == 200:
            data = today_response.json()
            print(f"Response keys: {list(data.keys())}")
            
            meals = data.get("meals", [])
            print(f"Number of meals: {len(meals)}")
            
            for i, meal in enumerate(meals):
                print(f"\n🍽️  Meal {i+1}:")
                print(f"   ID: {meal.get('id')}")
                print(f"   Foods: {meal.get('food_items')}")
                print(f"   Protein: {meal.get('total_protein')}")
                print(f"   Calories: {meal.get('total_calories')} (type: {type(meal.get('total_calories'))})")
                print(f"   Created: {meal.get('created_at')}")
        else:
            print(f"Error: {today_response.text}")
    except Exception as e:
        print(f"❌ Error testing /meals/today: {e}")
    
    # Test /meals endpoint (history)
    print("\n📊 Testing /meals endpoint (history):")
    try:
        meals_response = requests.get(f"{base_url}/meals", headers=headers)
        print(f"Status: {meals_response.status_code}")
        
        if meals_response.status_code == 200:
            data = meals_response.json()
            print(f"Response keys: {list(data.keys())}")
            
            meals = data.get("meals", [])
            print(f"Number of meals: {len(meals)}")
            
            for i, meal in enumerate(meals[:3]):  # Show first 3 meals
                print(f"\n🍽️  Meal {i+1}:")
                print(f"   ID: {meal.get('id')}")
                print(f"   Foods: {meal.get('food_items')}")
                print(f"   Protein: {meal.get('total_protein')}")
                print(f"   Calories: {meal.get('total_calories')} (type: {type(meal.get('total_calories'))})")
                print(f"   Created: {meal.get('created_at')}")
        else:
            print(f"Error: {meals_response.text}")
    except Exception as e:
        print(f"❌ Error testing /meals: {e}")
    
    # Test /dashboard endpoint
    print("\n📊 Testing /dashboard endpoint:")
    try:
        dashboard_response = requests.get(f"{base_url}/dashboard", headers=headers)
        print(f"Status: {dashboard_response.status_code}")
        
        if dashboard_response.status_code == 200:
            data = dashboard_response.json()
            print(f"Response keys: {list(data.keys())}")
            
            today = data.get("today", {})
            print(f"Today data keys: {list(today.keys())}")
            print(f"Today calories: {today.get('total_calories')}")
            
            user = data.get("user", {})
            print(f"User calorie goal: {user.get('calorie_goal')}")
        else:
            print(f"Error: {dashboard_response.text}")
    except Exception as e:
        print(f"❌ Error testing /dashboard: {e}")

if __name__ == "__main__":
    test_api()
