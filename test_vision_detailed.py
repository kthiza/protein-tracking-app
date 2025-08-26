#!/usr/bin/env python3
"""
Detailed test script to debug Google Vision API detection
"""

import os
import json

def test_vision_api_detailed():
    """Test Google Vision API with detailed output"""
    print("🔍 Detailed Google Vision API Test")
    print("=" * 50)
    
    image_path = "uploads/meal_1_20250823_141309_pasta.jfif"
    
    if not os.path.exists(image_path):
        print(f"❌ Test image not found: {image_path}")
        return
    
    try:
        from google.cloud import vision
        from google.oauth2 import service_account
        
        # Initialize client
        credentials = service_account.Credentials.from_service_account_file(
            "service-account-key.json",
            scopes=['https://www.googleapis.com/auth/cloud-platform']
        )
        client = vision.ImageAnnotatorClient(credentials=credentials)
        
        # Read image
        with open(image_path, 'rb') as image_file:
            content = image_file.read()
        
        image = vision.Image(content=content)
        
        # Get all labels
        response = client.label_detection(image=image)
        labels = response.label_annotations
        
        print(f"🏷️  All labels detected ({len(labels)} total):")
        for i, label in enumerate(labels):
            print(f"   {i+1}. {label.description} (confidence: {label.score:.3f})")
        
        # Get object localization
        print(f"\n🎯 Object localization:")
        response_objects = client.object_localization(image=image)
        objects = response_objects.localized_object_annotations
        
        print(f"   Objects detected ({len(objects)} total):")
        for i, obj in enumerate(objects):
            print(f"   {i+1}. {obj.name} (confidence: {obj.score:.3f})")
        
        # Get text detection
        print(f"\n📝 Text detection:")
        response_text = client.text_detection(image=image)
        texts = response_text.text_annotations
        
        if texts:
            print(f"   Text detected: {texts[0].description}")
        else:
            print("   No text detected")
        
        # Get web detection
        print(f"\n🌐 Web detection:")
        response_web = client.web_detection(image=image)
        web_detection = response_web.web_detection
        
        if web_detection.web_entities:
            print(f"   Web entities ({len(web_detection.web_entities)} total):")
            for i, entity in enumerate(web_detection.web_entities[:10]):  # Show top 10
                print(f"   {i+1}. {entity.description} (score: {entity.score:.3f})")
        
        if web_detection.full_matching_images:
            print(f"   Full matching images: {len(web_detection.full_matching_images)}")
        
        if web_detection.partial_matching_images:
            print(f"   Partial matching images: {len(web_detection.partial_matching_images)}")
        
        if web_detection.visually_similar_images:
            print(f"   Visually similar images: {len(web_detection.visually_similar_images)}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

def test_food_detection_components():
    """Test individual components of food detection"""
    print("\n🔍 Testing Food Detection Components")
    print("=" * 50)
    
    image_path = "uploads/meal_1_20250823_141309_pasta.jfif"
    
    try:
        from food_detection import GoogleVisionFoodDetector
        
        detector = GoogleVisionFoodDetector()
        
        # Test the detection
        result = detector.detect_food_in_image(image_path)
        
        print(f"📊 Detection result:")
        print(f"   Foods: {result.get('foods', [])}")
        print(f"   Protein: {result.get('protein_per_100g', 0)}g")
        print(f"   Confidence scores: {result.get('confidence_scores', {})}")
        print(f"   Detection method: {result.get('detection_method', 'unknown')}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_vision_api_detailed()
    test_food_detection_components()
