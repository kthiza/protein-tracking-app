#!/usr/bin/env python3
"""
Setup script for Protein Tracker App environment configuration
"""

import os
import re

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_api_key(api_key):
    """Basic validation for Google Cloud API key"""
    return len(api_key) > 20 and api_key != "your_google_cloud_api_key_here"

def validate_app_password(password):
    """Validate Gmail App Password format"""
    return len(password) == 16 and password.isalnum()

def setup_email_config():
    """Setup email configuration"""
    print("📧 Email Configuration Setup")
    print("=" * 40)
    print("To use email verification, you need to:")
    print("1. Enable 2-Step Verification on your Google Account")
    print("2. Generate an App Password")
    print("3. Use the App Password (not your regular password)")
    print()
    
    email = input("Enter your Gmail address: ").strip()
    if not validate_email(email):
        print("❌ Invalid email format. Please enter a valid Gmail address.")
        return None, None
    
    print("\n🔐 Gmail App Password Setup:")
    print("1. Go to: https://myaccount.google.com/security")
    print("2. Enable 2-Step Verification (if not already enabled)")
    print("3. Go to: 2-Step Verification → App passwords")
    print("4. Select 'Mail' and 'Other (Custom name)'")
    print("5. Name it 'Protein Tracker App'")
    print("6. Copy the 16-character password")
    print()
    
    app_password = input("Enter your Gmail App Password (16 characters): ").strip()
    if not validate_app_password(app_password):
        print("❌ Invalid App Password. It should be 16 characters long.")
        return None, None
    
    return email, app_password

def setup_google_vision():
    """Setup Google Cloud Vision API"""
    print("\n🤖 Google Cloud Vision API Setup")
    print("=" * 40)
    print("This is optional but enables AI food detection.")
    print("To get an API key:")
    print("1. Go to: https://console.cloud.google.com/")
    print("2. Create a new project or select existing one")
    print("3. Enable the Vision API")
    print("4. Create credentials (API Key)")
    print("5. Copy the API key")
    print()
    
    use_vision = input("Do you want to configure Google Cloud Vision? (y/n): ").strip().lower()
    if use_vision != 'y':
        return None
    
    api_key = input("Enter your Google Cloud Vision API Key: ").strip()
    if not validate_api_key(api_key):
        print("❌ Invalid API key format.")
        return None
    
    return api_key

def update_env_file(email, app_password, api_key):
    """Update the .env file with new settings"""
    env_content = f"""# Google Cloud Vision API (optional)
GOOGLE_API_KEY={api_key or 'your_google_cloud_api_key_here'}

# Email settings for verification (Gmail)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME={email or 'your_email@gmail.com'}
SMTP_PASSWORD={app_password or 'your_app_password'}
"""
    
    try:
        with open('.env', 'w') as f:
            f.write(env_content)
        print("\n✅ .env file updated successfully!")
        return True
    except Exception as e:
        print(f"❌ Error updating .env file: {e}")
        return False

def main():
    """Main setup function"""
    print("🚀 Protein Tracker App - Environment Setup")
    print("=" * 50)
    print()
    
    # Email setup
    email, app_password = setup_email_config()
    
    # Google Vision setup
    api_key = setup_google_vision()
    
    # Update .env file
    if email and app_password:
        if update_env_file(email, app_password, api_key):
            print("\n🎉 Setup completed successfully!")
            print("\n📋 Summary:")
            print(f"   Email: {email}")
            print(f"   Google Vision: {'Configured' if api_key else 'Not configured'}")
            print("\n🔧 Next steps:")
            print("1. Restart your server: python main.py")
            print("2. Test registration with email verification")
            print("3. Test the live camera functionality")
        else:
            print("\n❌ Setup failed. Please try again.")
    else:
        print("\n⚠️  Email configuration is required for account verification.")
        print("   Please run the setup again and provide valid email credentials.")

if __name__ == "__main__":
    main() 