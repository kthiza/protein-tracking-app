#!/usr/bin/env python3
"""
Google Vision API Setup Script
This script helps you set up Google Vision API for food detection.
"""

import os
import json
from typing import Optional

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

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
    
    # Check if API key is already configured in environment
    current_key = os.getenv("GOOGLE_VISION_API_KEY", "<not set>")
    print(f"Current API key (from .env / environment): {current_key}")
    print("Status: " + ("✅ Set" if current_key and current_key != "<not set>" else "❌ Not set"))
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
        print("API key not updated. The app requires Google Vision API for food detection.")
        print()
        print("💡 Tips:")
        print("- Google Vision API is required for accurate food detection")
        print("- You can always run this script again to update the API key")
        print("- Keep your API key secure and don't share it publicly")

def update_api_key(new_key: str):
    """Write the API key to a .env file rather than checking code into source."""
    try:
        # Update .env file (create if missing)
        lines = []
        if os.path.exists('.env'):
            with open('.env', 'r', encoding='utf-8') as f:
                lines = f.readlines()
        
        key_written = False
        with open('.env', 'w', encoding='utf-8') as f:
            for line in lines:
                if line.strip().startswith('GOOGLE_VISION_API_KEY='):
                    f.write(f'GOOGLE_VISION_API_KEY={new_key}\n')
                    key_written = True
                else:
                    f.write(line)
            if not key_written:
                f.write(f'GOOGLE_VISION_API_KEY={new_key}\n')
        
        print("✅ API key saved to .env (GOOGLE_VISION_API_KEY)")
        print("🔄 Restart the application to use the new API key")
    except Exception as e:
        print(f"❌ Failed to write .env: {e}")
        print("Please set the environment variable GOOGLE_VISION_API_KEY manually.")

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
