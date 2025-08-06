#!/usr/bin/env python3
"""
Cleanup script for Protein Tracker App
This script removes the database and uploaded files to start fresh.
"""

import os
import shutil
import sys
import requests
import json

def cleanup_files():
    """Remove database and uploaded files"""
    print("🧹 Cleaning up Protein Tracker App files...")
    
    # Remove database
    if os.path.exists("protein_app.db"):
        os.remove("protein_app.db")
        print("✅ Database removed")
    else:
        print("ℹ️  Database not found")
    
    # Remove uploads directory
    if os.path.exists("uploads"):
        shutil.rmtree("uploads")
        print("✅ Uploads directory removed")
    else:
        print("ℹ️  Uploads directory not found")
    
    print("🎉 File cleanup complete!")

def cleanup_old_meals():
    """Clean up old meals via API"""
    print("🧹 Cleaning up old meals via API...")
    
    try:
        response = requests.post("http://localhost:8000/admin/cleanup")
        if response.status_code == 200:
            result = response.json()
            print(f"✅ API cleanup successful!")
            print(f"Cleaned meals: {result.get('cleaned_meals', 0)}")
            print(f"Total old meals: {result.get('total_old_meals', 0)}")
        else:
            print(f"❌ API cleanup failed: {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"❌ API cleanup error: {e}")

def cleanup():
    """Main cleanup function"""
    print("🧹 Protein Tracker App Cleanup")
    print("=" * 40)
    
    # Ask user what to clean
    print("Choose cleanup option:")
    print("1. Clean files only (database + uploads)")
    print("2. Clean old meals via API")
    print("3. Full cleanup (files + API)")
    
    try:
        choice = input("Enter choice (1-3): ").strip()
        
        if choice == "1":
            cleanup_files()
        elif choice == "2":
            cleanup_old_meals()
        elif choice == "3":
            cleanup_files()
            cleanup_old_meals()
        else:
            print("❌ Invalid choice")
            return
            
        print("🎉 Cleanup complete!")
        
    except KeyboardInterrupt:
        print("\n❌ Cleanup cancelled by user")
    except Exception as e:
        print(f"❌ Error during cleanup: {e}")

if __name__ == "__main__":
    cleanup() 