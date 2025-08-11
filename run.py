#!/usr/bin/env python3
"""
🍗 Protein Tracker - Server Runner
Simple script to start the backend server
"""

import subprocess
import sys
import os
from pathlib import Path

def print_header():
    print("🍗 Protein Tracker")
    print("=" * 40)
    print("Starting server...")
    print()

def check_dependencies():
    """Install required dependencies"""
    print("📦 Checking dependencies...")
    
    try:
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ], capture_output=True, text=True, check=False)
        
        if result.returncode == 0:
            print("✅ Dependencies installed successfully")
        else:
            print("⚠️  Some dependency issues detected, but continuing...")
            if result.stderr:
                print(f"   Warning: {result.stderr.strip()}")
    except Exception as e:
        print(f"⚠️  Could not install dependencies: {e}")
        print("   You may need to run: pip install -r requirements.txt")
    
    print()

def check_google_vision_setup():
    """Check if Google Vision API is properly set up"""
    print("🔍 Checking Google Vision API setup...")
    
    try:
        result = subprocess.run([
            sys.executable, "setup_google_vision.py", "status"
        ], capture_output=True, text=True, check=False)
        
        if result.returncode == 0:
            print("✅ Google Vision API setup check completed")
        else:
            print("⚠️  Google Vision API setup check failed")
    except Exception as e:
        print(f"⚠️  Could not check Google Vision setup: {e}")
    
    print()

def start_server():
    """Start the FastAPI server"""
    print("🚀 Starting FastAPI server...")
    print("🌐 Server will be available at: http://127.0.0.1:8000")
    print("💡 Keep this window open while using the app")
    print("⏹️  Press Ctrl+C to stop the server")
    print()
    
    try:
        subprocess.run([
            sys.executable, "-m", "uvicorn", "main:app", 
            "--reload", "--host", "127.0.0.1", "--port", "8000"
        ], check=True)
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Server failed to start: {e}")
        print("\n🔧 Troubleshooting:")
        print("1. Check that main.py exists in the current directory")
        print("2. Try: pip install -r requirements.txt")
        print("3. Check for Python/dependency conflicts")
        return False
    except FileNotFoundError:
        print("\n❌ uvicorn not found. Installing...")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "uvicorn"], check=True)
            print("✅ uvicorn installed. Rerun this script.")
        except Exception as e:
            print(f"❌ Failed to install uvicorn: {e}")
        return False
    
    return True

def main():
    print_header()
    
    # Check if we're in the right directory
    if not Path("main.py").exists():
        print("❌ main.py not found!")
        print("   Please run this script from the Protein App directory")
        sys.exit(1)
    
    # Check dependencies
    check_dependencies()
    
    # Check Google Vision setup (optional)
    if Path("setup_google_vision.py").exists():
        check_google_vision_setup()
    
    # Start server
    success = start_server()
    
    if not success:
        print("\n💡 Alternative startup command:")
        print("   python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000")
        sys.exit(1)

if __name__ == "__main__":
    main()
