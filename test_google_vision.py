#!/usr/bin/env python3
"""
Test script to verify Google Vision API configuration
Run this locally to test your Google Vision setup before deploying
"""

import os
import json
import sys

def test_environment_variables():
    """Test if environment variables are properly set"""
    print("🔍 Testing Environment Variables...")
    
    # Test .env file loading
    try:
        from dotenv import load_dotenv
        if os.path.exists('.env'):
            load_dotenv()
            print("✅ .env file found and loaded")
        else:
            print("ℹ️  No .env file found (this is normal for production)")
    except ImportError:
        print("⚠️  python-dotenv not installed")
    
    # Test Google Vision variables
    google_service_account = os.getenv("GOOGLE_SERVICE_ACCOUNT")
    google_vision_path = os.getenv("GOOGLE_VISION_SERVICE_ACCOUNT_PATH")
    
    if google_service_account:
        try:
            service_account_info = json.loads(google_service_account)
            print("✅ GOOGLE_SERVICE_ACCOUNT environment variable found")
            print(f"   Project ID: {service_account_info.get('project_id', 'Unknown')}")
            print(f"   Client Email: {service_account_info.get('client_email', 'Unknown')}")
            return True
        except json.JSONDecodeError as e:
            print(f"❌ GOOGLE_SERVICE_ACCOUNT contains invalid JSON: {e}")
            return False
    elif google_vision_path:
        if os.path.exists(google_vision_path):
            print(f"✅ GOOGLE_VISION_SERVICE_ACCOUNT_PATH found: {google_vision_path}")
            try:
                with open(google_vision_path, 'r') as f:
                    service_account_info = json.load(f)
                print(f"   Project ID: {service_account_info.get('project_id', 'Unknown')}")
                print(f"   Client Email: {service_account_info.get('client_email', 'Unknown')}")
                return True
            except Exception as e:
                print(f"❌ Error reading service account file: {e}")
                return False
        else:
            print(f"❌ Service account file not found: {google_vision_path}")
            return False
    else:
        print("❌ No Google Vision credentials found")
        print("   Set GOOGLE_SERVICE_ACCOUNT environment variable or")
        print("   Set GOOGLE_VISION_SERVICE_ACCOUNT_PATH and ensure file exists")
        return False

def test_vision_api_import():
    """Test if Google Vision API can be imported"""
    print("\n🔍 Testing Google Vision API Import...")
    
    try:
        from google.cloud import vision
        from google.oauth2 import service_account
        print("✅ Google Vision API libraries imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Google Vision API libraries not available: {e}")
        print("   Install with: pip install google-cloud-vision")
        return False

def test_vision_api_connection():
    """Test actual connection to Google Vision API"""
    print("\n🔍 Testing Google Vision API Connection...")
    
    try:
        from google.cloud import vision
        from google.oauth2 import service_account
        
        # Get credentials
        google_service_account = os.getenv("GOOGLE_SERVICE_ACCOUNT")
        google_vision_path = os.getenv("GOOGLE_VISION_SERVICE_ACCOUNT_PATH", "service-account-key.json")
        
        if google_service_account:
            service_account_info = json.loads(google_service_account)
            credentials = service_account.Credentials.from_service_account_info(
                service_account_info,
                scopes=['https://www.googleapis.com/auth/cloud-platform']
            )
        elif os.path.exists(google_vision_path):
            credentials = service_account.Credentials.from_service_account_file(
                google_vision_path,
                scopes=['https://www.googleapis.com/auth/cloud-platform']
            )
        else:
            print("❌ No valid credentials found")
            return False
        
        # Initialize client
        client = vision.ImageAnnotatorClient(credentials=credentials)
        
        # Test with a simple image
        test_image_content = b'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=='
        image = vision.Image(content=test_image_content)
        
        # Make a test request
        response = client.label_detection(image=image)
        
        if response.error.message:
            print(f"❌ Vision API error: {response.error.message}")
            return False
        
        print("✅ Google Vision API connection successful!")
        print("   API is working correctly")
        return True
        
    except Exception as e:
        print(f"❌ Vision API connection failed: {e}")
        return False

def main():
    """Main test function"""
    print("🧪 Google Vision API Configuration Test")
    print("=" * 50)
    
    env_ok = test_environment_variables()
    import_ok = test_vision_api_import()
    
    if env_ok and import_ok:
        connection_ok = test_vision_api_connection()
        if connection_ok:
            print("\n🎉 All tests passed! Google Vision API is properly configured.")
            print("   Your app should work with AI food detection.")
        else:
            print("\n⚠️  Environment and imports OK, but API connection failed.")
            print("   Check your Google Cloud project settings and billing.")
    else:
        print("\n❌ Configuration issues found.")
        print("   Please fix the issues above before deploying.")
    
    print("\n📋 Next Steps:")
    if not env_ok:
        print("   1. Set up Google Cloud service account")
        print("   2. Configure environment variables")
        print("   3. See GOOGLE_VISION_SETUP.md for detailed instructions")
    elif not import_ok:
        print("   1. Install Google Vision API: pip install google-cloud-vision")
        print("   2. Add to requirements.txt for deployment")
    else:
        print("   1. Deploy to Render with environment variables")
        print("   2. Test food detection in your app")

if __name__ == "__main__":
    main()
