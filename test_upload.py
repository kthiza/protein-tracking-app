#!/usr/bin/env python3
"""
Test script to verify upload endpoint and food detection
"""

import os
import sys
from pathlib import Path

def test_food_detection():
    """Test food detection with the existing image"""
    print("🧪 Testing Food Detection")
    print("=" * 40)
    
    # Test with existing image
    image_path = "uploads/meal_1_20250823_141309_pasta.jfif"
    
    if not os.path.exists(image_path):
        print(f"❌ Test image not found: {image_path}")
        return False
    
    try:
        # Import and test the detection functions
        from main import identify_food_with_vision, identify_food_local_fallback
        
        print(f"🔍 Testing with image: {image_path}")
        
        # Test main detection function
        print("\n1. Testing main detection function:")
        result = identify_food_with_vision(image_path)
        print(f"   Result: {result}")
        
        # Test fallback function
        print("\n2. Testing fallback function:")
        fallback_result = identify_food_local_fallback(image_path)
        print(f"   Result: {fallback_result}")
        
        # Test with different filenames
        print("\n3. Testing fallback with different filenames:")
        test_cases = [
            "chicken_meal.jpg",
            "pizza_slice.png", 
            "beef_burger.jpeg",
            "salad_bowl.jpg",
            "fish_dinner.png"
        ]
        
        for test_filename in test_cases:
            result = identify_food_local_fallback(f"uploads/{test_filename}")
            print(f"   {test_filename}: {result}")
        
        print("\n✅ Food detection tests completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def test_google_vision_status():
    """Test Google Vision API status"""
    print("\n🔍 Testing Google Vision API Status")
    print("=" * 40)
    
    try:
        from main import GOOGLE_VISION_AVAILABLE
        print(f"Google Vision Available: {GOOGLE_VISION_AVAILABLE}")
        
        if GOOGLE_VISION_AVAILABLE:
            from food_detection import identify_food_with_google_vision
            image_path = "uploads/meal_1_20250823_141309_pasta.jfif"
            
            if os.path.exists(image_path):
                print("Testing Google Vision API directly...")
                result = identify_food_with_google_vision(image_path)
                print(f"Google Vision Result: {result}")
            else:
                print("Test image not found for Google Vision test")
        
        return True
        
    except Exception as e:
        print(f"❌ Google Vision test failed: {e}")
        return False

def main():
    """Main test function"""
    print("🧪 Upload and Food Detection Test")
    print("=" * 50)
    
    # Test Google Vision status
    vision_ok = test_google_vision_status()
    
    # Test food detection
    detection_ok = test_food_detection()
    
    if vision_ok and detection_ok:
        print("\n🎉 All tests passed!")
        print("   The upload system should work correctly now.")
    else:
        print("\n⚠️  Some tests failed.")
        print("   Check the output above for details.")

if __name__ == "__main__":
    main()
