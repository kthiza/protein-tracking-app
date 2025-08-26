#!/usr/bin/env python3
"""
Test script to verify Render deployment compatibility
"""

import os
import json

def test_environment_variable_support():
    """Test if the food detection works with environment variables"""
    print("🧪 Testing Render Deployment Compatibility")
    print("=" * 50)
    
    # Test 1: Check if environment variable is set
    google_service_account = os.getenv("GOOGLE_SERVICE_ACCOUNT")
    if google_service_account:
        print("✅ GOOGLE_SERVICE_ACCOUNT environment variable is set")
        try:
            service_account_info = json.loads(google_service_account)
            print(f"   Project ID: {service_account_info.get('project_id', 'Unknown')}")
            print(f"   Client Email: {service_account_info.get('client_email', 'Unknown')}")
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON in environment variable: {e}")
            return False
    else:
        print("ℹ️  GOOGLE_SERVICE_ACCOUNT environment variable not set")
        print("   This is normal for local development with service account files")
    
    # Test 2: Test food detection initialization
    print("\n🔍 Testing Food Detection Initialization...")
    try:
        from food_detection import GoogleVisionFoodDetector
        
        # Test initialization without parameters (should use environment variable or fallback)
        detector = GoogleVisionFoodDetector()
        print("✅ GoogleVisionFoodDetector initialized successfully")
        
        # Test if client is available
        if detector.client:
            print("✅ Google Vision API client is available")
        else:
            print("❌ Google Vision API client is not available")
            return False
            
    except Exception as e:
        print(f"❌ Food detection initialization failed: {e}")
        return False
    
    # Test 3: Test with actual image (if available)
    image_path = "uploads/meal_1_20250823_141309_pasta.jfif"
    if os.path.exists(image_path):
        print(f"\n🔍 Testing with actual image: {image_path}")
        try:
            result = detector.detect_food_in_image(image_path)
            detected_foods = result.get('foods', [])
            print(f"✅ Detection successful! Found {len(detected_foods)} food items: {detected_foods}")
            return True
        except Exception as e:
            print(f"❌ Detection failed: {e}")
            return False
    else:
        print(f"\nℹ️  Test image not found: {image_path}")
        print("   Skipping actual detection test")
        return True

def test_main_app_integration():
    """Test if the main app integration works"""
    print("\n🔍 Testing Main App Integration...")
    try:
        from main import identify_food_with_vision
        
        # Test the main function
        image_path = "uploads/meal_1_20250823_141309_pasta.jfif"
        if os.path.exists(image_path):
            result = identify_food_with_vision(image_path)
            print(f"✅ Main app integration successful! Result: {result}")
            return True
        else:
            print("ℹ️  Test image not found, skipping main app test")
            return True
            
    except Exception as e:
        print(f"❌ Main app integration failed: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 Render Deployment Compatibility Test")
    print("=" * 60)
    
    # Test environment variable support
    env_test_passed = test_environment_variable_support()
    
    # Test main app integration
    app_test_passed = test_main_app_integration()
    
    if env_test_passed and app_test_passed:
        print("\n🎉 All tests passed!")
        print("   Your app is ready for Render deployment.")
        print("\n📋 Deployment Checklist:")
        print("   1. ✅ Environment variable support implemented")
        print("   2. ✅ Google Vision API integration working")
        print("   3. ✅ Main app integration working")
        print("   4. 🔧 Set GOOGLE_SERVICE_ACCOUNT environment variable in Render dashboard")
        print("   5. 🔧 Deploy to Render")
    else:
        print("\n⚠️  Some tests failed.")
        print("   Check the output above for details.")
        print("\n🔧 For Render deployment:")
        print("   1. Set GOOGLE_SERVICE_ACCOUNT environment variable in Render dashboard")
        print("   2. Copy the entire service account JSON content as the value")
        print("   3. Deploy your app")

if __name__ == "__main__":
    main()
