#!/usr/bin/env python3
"""
🔧 Port Binding Test Script
Tests if the app can bind to the PORT environment variable correctly
"""

import os
import uvicorn
from main import app

def test_port_binding():
    """Test port binding with environment variable"""
    # Get port from environment variable (like Render does)
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")
    
    print(f"🔧 Testing port binding...")
    print(f"📍 Host: {host}")
    print(f"📍 Port: {port}")
    print(f"📍 Environment PORT: {os.environ.get('PORT', 'Not set')}")
    
    try:
        # Test if we can bind to the port
        uvicorn.run(app, host=host, port=port, log_level="info")
        print("✅ Port binding test successful!")
    except Exception as e:
        print(f"❌ Port binding test failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    test_port_binding()
