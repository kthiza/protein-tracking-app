import os
from google.cloud import vision
from google.oauth2 import service_account
from food_detection import GoogleVisionFoodDetector

def debug_vision_labels(image_path: str):
    """Debug function to see all labels returned by Google Vision API"""
    
    # Initialize the Vision API client
    service_account_path = "service-account-key.json"
    credentials = service_account.Credentials.from_service_account_file(
        service_account_path,
        scopes=['https://www.googleapis.com/auth/cloud-platform']
    )
    client = vision.ImageAnnotatorClient(credentials=credentials)
    
    # Read the image file
    with open(image_path, 'rb') as image_file:
        content = image_file.read()
    
    image = vision.Image(content=content)
    
    # Perform label detection
    response = client.label_detection(image=image)
    labels = response.label_annotations
    
    print(f"🔍 All labels detected by Google Vision API for {image_path}:")
    print("=" * 60)
    
    for i, label in enumerate(labels, 1):
        print(f"{i:2d}. {label.description:30s} (confidence: {label.score:.3f})")
    
    print("=" * 60)
    print(f"Total labels: {len(labels)}")
    
    # Test food matching logic
    print("\n🧪 Testing food matching logic:")
    print("=" * 60)
    
    detector = GoogleVisionFoodDetector()
    
    for label in labels:
        if label.score >= 0.70:  # Only test high-confidence labels
            label_desc = label.description.lower().strip()
            confidence = label.score
            
            print(f"\nTesting label: '{label_desc}' (confidence: {confidence:.3f})")
            
            # Test direct database match
            if label_desc in detector.protein_database:
                print(f"  ✅ Direct match found: '{label_desc}' -> {detector.protein_database[label_desc]}g protein")
            else:
                print(f"  ❌ No direct match in database")
                
                # Test partial matching
                matches = []
                for food_item in detector.protein_database.keys():
                    if food_item in label_desc and len(food_item) >= 3:
                        # Check word boundary matching
                        is_word_boundary_match = (
                            food_item == label_desc or
                            label_desc.startswith(food_item + " ") or
                            label_desc.endswith(" " + food_item) or
                            " " + food_item + " " in " " + label_desc + " " or
                            food_item in label_desc.split() or
                            (len(food_item.split()) > 1 and all(word in label_desc for word in food_item.split())) or
                            (len(food_item.split()) == 1 and food_item in label_desc)
                        )
                        
                        if is_word_boundary_match:
                            matches.append(food_item)
                
                if matches:
                    print(f"  🔍 Partial matches found: {matches}")
                else:
                    print(f"  ❌ No partial matches found")

if __name__ == "__main__":
    debug_vision_labels("uploads/meal_2_20250813_104149_english-breakfast.webp")
