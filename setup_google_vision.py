#!/usr/bin/env python3
"""
Google Vision API Setup Script
This script helps you set up Google Vision API for food detection.
"""

import os
import json
from typing import Optional

def setup_google_vision_api():
    """Guide user through setting up Google Vision API"""
    print("🔧 Google Vision API Setup")
    print("=" * 50)
    print()
    print("To use Google Vision API for food detection, you need to:")
    print("1. Create a Google Cloud Project")
    print("2. Enable the Vision API")
    print("3. Create an API key")
    print("4. Configure the API key in this app")
    print()
    
    # Check if API key is already configured
    current_key = "93a73af420dc3ca3811ded584c81e5bc03cb76d5"
    print(f"Current API key: {current_key}")
    print("Status: ❌ Invalid (as tested)")
    print()
    
    print("📋 Step-by-step instructions:")
    print()
    print("1. Go to Google Cloud Console:")
    print("   https://console.cloud.google.com/")
    print()
    print("2. Create a new project or select existing one")
    print()
    print("3. Enable the Vision API:")
    print("   - Go to APIs & Services > Library")
    print("   - Search for 'Cloud Vision API'")
    print("   - Click on it and press 'Enable'")
    print()
    print("4. Create an API key:")
    print("   - Go to APIs & Services > Credentials")
    print("   - Click 'Create Credentials' > 'API Key'")
    print("   - Copy the generated API key")
    print()
    print("5. (Optional) Restrict the API key:")
    print("   - Click on the created API key")
    print("   - Under 'Application restrictions', select 'HTTP referrers'")
    print("   - Under 'API restrictions', select 'Restrict key'")
    print("   - Select 'Cloud Vision API' from the dropdown")
    print()
    
    # Ask user if they want to update the API key
    new_key = input("Enter your new API key (or press Enter to skip): ").strip()
    
    if new_key:
        update_api_key(new_key)
    else:
        print("API key not updated. The app will continue using fallback detection.")
        print()
        print("💡 Tips:")
        print("- The fallback detection works but is less accurate")
        print("- You can always run this script again to update the API key")
        print("- Keep your API key secure and don't share it publicly")

def update_api_key(new_key: str):
    """Update the API key in the food detection file"""
    try:
        # Read the current food_detection.py file
        with open('food_detection.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Replace the API key
        old_key = "93a73af420dc3ca3811ded584c81e5bc03cb76d5"
        updated_content = content.replace(old_key, new_key)
        
        # Write the updated content back
        with open('food_detection.py', 'w', encoding='utf-8') as f:
            f.write(updated_content)
        
        print("✅ API key updated successfully!")
        print(f"New key: {new_key}")
        print()
        print("🔄 Restart the application to use the new API key")
        
    except Exception as e:
        print(f"❌ Failed to update API key: {e}")
        print("Please manually update the API key in food_detection.py")

def test_api_key(api_key: str) -> bool:
    """Test if the API key is valid"""
    try:
        import requests
        
        # Simple test request
        url = f"https://vision.googleapis.com/v1/images:annotate?key={api_key}"
        payload = {
            "requests": [
                {
                    "image": {
                        "content": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
                    },
                    "features": [
                        {
                            "type": "LABEL_DETECTION",
                            "maxResults": 1
                        }
                    ]
                }
            ]
        }
        
        headers = {'Content-Type': 'application/json'}
        response = requests.post(url, json=payload, headers=headers)
        
        return response.status_code == 200
        
    except Exception:
        return False

def main():
    """Main function"""
    print("🍽️  Protein App - Google Vision API Setup")
    print("=" * 50)
    print()
    
    setup_google_vision_api()
    
    print()
    print("🎯 Next steps:")
    print("1. Get your API key from Google Cloud Console")
    print("2. Run this script again to update the key")
    print("3. Restart the application")
    print("4. Test food detection with an image")
    print()
    print("📚 For more help, visit:")
    print("   https://cloud.google.com/vision/docs/setup")

if __name__ == "__main__":
    main()
