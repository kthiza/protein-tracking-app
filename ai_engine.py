import json
import os
from typing import List, Dict, Any
from google.cloud import vision
from google.oauth2 import service_account
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Google Cloud Vision API setup
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

def setup_vision_client():
    """Setup Google Cloud Vision client with API key"""
    try:
        # For API key authentication
        client_options = {"api_key": GOOGLE_API_KEY}
        client = vision.ImageAnnotatorClient(client_options=client_options)
        return client
    except Exception as e:
        print(f"Error setting up Vision client: {e}")
        return None

def identify_food_items(image_path: str) -> List[str]:
    """
    Task 1: Food Identifier
    Takes an image file, sends it to Google Cloud Vision API, 
    and returns a clean list of identified food labels
    """
    client = setup_vision_client()
    if not client:
        return []
    
    try:
        # Read the image file
        with open(image_path, 'rb') as image_file:
            content = image_file.read()
        
        # Create image object
        image = vision.Image(content=content)
        
        # Perform label detection
        response = client.label_detection(image=image)
        labels = response.label_annotations
        
        # Filter for food-related labels
        food_keywords = [
            'food', 'dish', 'meal', 'cuisine', 'ingredient', 'produce',
            'meat', 'fish', 'poultry', 'dairy', 'vegetable', 'fruit',
            'grain', 'nut', 'seed', 'legume', 'protein'
        ]
        
        food_items = []
        for label in labels:
            label_text = label.description.lower()
            
            # Check if label contains food-related keywords
            if any(keyword in label_text for keyword in food_keywords):
                food_items.append(label_text)
            
            # Also check for specific food items in our database
            if label_text in load_protein_database():
                food_items.append(label_text)
        
        # Remove duplicates and return
        return list(set(food_items))
        
    except Exception as e:
        print(f"Error identifying food items: {e}")
        return []

def load_protein_database() -> Dict[str, int]:
    """Load the protein database from JSON file"""
    try:
        with open('protein_db.json', 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading protein database: {e}")
        return {}

def calculate_protein(food_items: List[str]) -> float:
    """
    Task 2: Protein Calculator
    Takes a list of food labels and uses the JSON database 
    to calculate and return the total estimated protein for the meal
    """
    protein_db = load_protein_database()
    total_protein = 0.0
    
    for food_item in food_items:
        # Try exact match first
        if food_item in protein_db:
            total_protein += protein_db[food_item]
        else:
            # Try partial matches
            for db_item, protein_value in protein_db.items():
                if db_item in food_item or food_item in db_item:
                    total_protein += protein_value
                    break
    
    return round(total_protein, 1)

def process_meal_image(image_path: str) -> Dict[str, Any]:
    """
    Main function that combines both tasks:
    Process an image and output estimated protein count
    """
    print(f"Processing image: {image_path}")
    
    # Task 1: Identify food items
    food_items = identify_food_items(image_path)
    print(f"Identified food items: {food_items}")
    
    # Task 2: Calculate protein
    total_protein = calculate_protein(food_items)
    print(f"Estimated protein: {total_protein} grams")
    
    return {
        "food_items": food_items,
        "total_protein_grams": total_protein,
        "image_path": image_path
    }

# Test function
if __name__ == "__main__":
    # Example usage
    test_image = "test_meal.jpg"  # You'll need to provide a test image
    
    if os.path.exists(test_image):
        result = process_meal_image(test_image)
        print("\n=== MEAL ANALYSIS RESULTS ===")
        print(f"Food Items: {result['food_items']}")
        print(f"Total Protein: {result['total_protein_grams']} grams")
    else:
        print(f"Test image '{test_image}' not found. Please provide a test image.")
        print("Usage: python ai_engine.py") 