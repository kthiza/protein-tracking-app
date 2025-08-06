#!/usr/bin/env python3
"""
Quick setup script for Protein Tracker App
"""

def update_env_file():
    """Update .env file with provided credentials"""
    
    print("🚀 Quick Setup - Protein Tracker App")
    print("=" * 40)
    
    # Email configuration
    print("\n📧 Email Configuration:")
    email = input("Gmail address (or press Enter to skip): ").strip()
    
    if email:
        print("\n🔐 Gmail App Password:")
        print("1. Go to: https://myaccount.google.com/apppasswords")
        print("2. Generate a 16-character App Password")
        print("3. Copy it (format: abcd efgh ijkl mnop)")
        print()
        app_password = input("App Password (16 characters): ").strip()
    else:
        app_password = ""
    
    # Google Vision API
    print("\n🤖 Google Cloud Vision API:")
    api_key = input("API Key (or press Enter to skip): ").strip()
    
    # Create .env content
    env_content = f"""# Google Cloud Vision API (optional)
GOOGLE_API_KEY={api_key or 'your_google_cloud_api_key_here'}

# Email settings for verification (Gmail)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME={email or 'your_email@gmail.com'}
SMTP_PASSWORD={app_password or 'your_app_password'}
"""
    
    # Write to .env file
    try:
        with open('.env', 'w') as f:
            f.write(env_content)
        
        print("\n✅ .env file updated successfully!")
        print(f"\n📋 Configuration Summary:")
        print(f"   Email: {email or 'Not configured'}")
        print(f"   Google Vision: {'Configured' if api_key else 'Not configured'}")
        
        if email and app_password:
            print("\n🎉 Email verification is ready!")
            print("   You can now register accounts and receive verification emails.")
        
        if api_key:
            print("\n🤖 AI detection is ready!")
            print("   You can now use Google Cloud Vision for food recognition.")
        
        print("\n🔧 Next steps:")
        print("1. Restart your server: python main.py")
        print("2. Test the application at: http://localhost:8000")
        
    except Exception as e:
        print(f"❌ Error updating .env file: {e}")

if __name__ == "__main__":
    update_env_file() 