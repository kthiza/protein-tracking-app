#!/usr/bin/env python3
"""
Test script for improved food detection
"""

from food_detection import identify_food_with_google_vision
import os
import requests
import base64
import json

def test_food_detection():
    """Test the improved food detection with sample images"""
    print("🧪 Testing Improved Food Detection")
    print("=" * 50)
    
    # Test with the image that contains rice, chicken, and veggies
    test_image = "uploads/meal_1_20250807_180005_download.jfif"
    
    if os.path.exists(test_image):
        print(f"📸 Testing with image: {test_image}")
        print()
        
        # First, let's see what the API actually detects
        print("🔍 Raw API Detection Results:")
        print("-" * 30)
        
        try:
            with open(test_image, 'rb') as image_file:
                image_content = base64.b64encode(image_file.read()).decode('utf-8')
            
            payload = {
                "requests": [
                    {
                        "image": {
                            "content": image_content
                        },
                        "features": [
                            {
                                "type": "LABEL_DETECTION",
                                "maxResults": 20
                            }
                        ]
                    }
                ]
            }
            
            api_key = "AIzaSyDV1WAFp928_8u-h3K2VcetMAXG7xVdZhI"
            api_url = f"https://vision.googleapis.com/v1/images:annotate?key={api_key}"
            
            response = requests.post(api_url, json=payload, headers={'Content-Type': 'application/json'})
            
            if response.status_code == 200:
                result = response.json()
                labels = result['responses'][0].get('labelAnnotations', [])
                
                print("All detected labels:")
                for i, label in enumerate(labels, 1):
                    print(f"  {i:2d}. {label['description']} (confidence: {label['score']:.2f})")
                
                print()
            else:
                print(f"❌ API Error: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error getting raw API results: {e}")
        
        print("🧪 Now testing with our improved detection:")
        print("-" * 40)
        
        result = identify_food_with_google_vision(test_image)
        
        print()
        print("📊 Test Results:")
        print(f"   Detected foods: {result}")
        print(f"   Number of foods: {len(result)}")
        print(f"   Using Google Vision API: ✅")
        
        if len(result) <= 5:
            print("   ✅ Detection looks realistic (≤5 foods)")
        else:
            print("   ⚠️  Too many foods detected")
            
    else:
        print(f"❌ Test image not found: {test_image}")
        print("   Please upload a food image first")

if __name__ == "__main__":
    test_food_detection()
