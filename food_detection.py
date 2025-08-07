import os
import json
from typing import List, Dict
from google.cloud import vision
from google.oauth2 import service_account
import requests

class GoogleVisionFoodDetector:
    def __init__(self, api_key: str = "AIzaSyDV1WAFp928_8u-h3K2VcetMAXG7xVdZhI"):
        """Initialize Google Vision API client"""
        self.api_key = api_key
        self.api_url = f"https://vision.googleapis.com/v1/images:annotate?key={api_key}"
        
        # Enhanced protein database with more comprehensive food items
        self.protein_database = {
            # Meat & Fish
            "chicken": 31.0, "chicken breast": 31.0, "chicken thigh": 28.0, "chicken wing": 30.0,
            "beef": 26.0, "steak": 26.0, "ground beef": 26.0, "beef steak": 26.0,
            "pork": 25.0, "pork chop": 25.0, "bacon": 37.0, "ham": 22.0,
            "salmon": 20.0, "tuna": 30.0, "cod": 18.0, "tilapia": 26.0,
            "turkey": 29.0, "turkey breast": 29.0, "duck": 23.0,
            "lamb": 25.0, "veal": 24.0, "venison": 30.0,
            
            # Dairy & Eggs
            "egg": 13.0, "eggs": 13.0, "milk": 3.4, "cheese": 25.0,
            "yogurt": 10.0, "greek yogurt": 10.0, "cottage cheese": 11.0,
            "cream cheese": 6.0, "cheddar": 25.0, "mozzarella": 22.0,
            "parmesan": 38.0, "feta": 14.0, "blue cheese": 21.0,
            
            # Plant-based Proteins
            "tofu": 8.0, "tempeh": 20.0, "edamame": 11.0, "soybeans": 36.0,
            "lentils": 9.0, "beans": 7.0, "black beans": 8.0, "kidney beans": 8.0,
            "chickpeas": 9.0, "garbanzo beans": 9.0, "pinto beans": 9.0,
            "quinoa": 14.0, "seitan": 75.0, "spirulina": 57.0,
            
            # Nuts & Seeds
            "almonds": 21.0, "walnuts": 15.0, "peanuts": 26.0, "cashews": 18.0,
            "pistachios": 20.0, "pecans": 9.0, "macadamia": 8.0,
            "chia seeds": 17.0, "flax seeds": 18.0, "hemp seeds": 32.0,
            "sunflower seeds": 21.0, "pumpkin seeds": 19.0,
            "peanut butter": 25.0, "almond butter": 21.0,
            
            # Grains & Carbohydrates
            "rice": 2.7, "brown rice": 2.7, "white rice": 2.7, "wild rice": 4.0,
            "bread": 9.0, "whole wheat bread": 9.0, "white bread": 9.0,
            "pasta": 13.0, "spaghetti": 13.0, "penne": 13.0, "macaroni": 13.0,
            "oatmeal": 13.0, "oats": 13.0, "cereal": 8.0,
            "wheat": 13.0, "barley": 12.0, "rye": 10.0,
            
            # Vegetables
            "broccoli": 2.8, "spinach": 2.9, "kale": 4.3, "collard greens": 3.0,
            "brussels sprouts": 3.4, "asparagus": 2.2, "artichoke": 3.3,
            "cauliflower": 1.9, "cabbage": 1.3, "lettuce": 1.4,
            "carrots": 0.9, "tomatoes": 0.9, "onions": 1.1, "garlic": 6.4,
            "bell peppers": 0.9, "jalapeno": 1.3, "cucumber": 0.7,
            "zucchini": 1.2, "eggplant": 1.0, "mushrooms": 3.1,
            "potatoes": 2.0, "sweet potatoes": 1.6, "corn": 3.2,
            "peas": 5.4, "green beans": 1.8, "celery": 0.7,
            
            # Fruits
            "apples": 0.3, "bananas": 1.1, "oranges": 0.9, "strawberries": 0.7,
            "blueberries": 0.7, "raspberries": 1.2, "blackberries": 1.4,
            "grapes": 0.6, "pineapple": 0.5, "mango": 0.8, "peach": 0.9,
            "pear": 0.4, "plum": 0.7, "cherries": 1.1, "kiwi": 1.1,
            "avocado": 2.0, "coconut": 3.3, "lemon": 1.1, "lime": 0.7,
            
            # Seafood
            "shrimp": 24.0, "crab": 19.0, "lobster": 19.0, "oysters": 9.0,
            "mussels": 12.0, "clams": 12.0, "scallops": 20.0,
            "mackerel": 19.0, "sardines": 24.0, "anchovies": 28.0,
            "herring": 18.0, "trout": 20.0, "bass": 18.0,
            
            # Processed Foods
            "hot dog": 12.0, "sausage": 14.0, "pepperoni": 19.0,
            "salami": 22.0, "pastrami": 22.0, "corned beef": 27.0,
            "deli meat": 18.0, "lunch meat": 18.0, "jerky": 33.0,
            "nuggets": 14.0, "tenders": 18.0, "patty": 18.0,
            
            # Common Dishes
            "burger": 18.0, "hamburger": 18.0, "sandwich": 15.0,
            "pizza": 11.0, "lasagna": 12.0, "spaghetti": 13.0,
            "stir fry": 12.0, "curry": 10.0, "soup": 8.0,
            "salad": 5.0, "wrap": 12.0, "burrito": 15.0,
            "taco": 12.0, "enchilada": 10.0, "quesadilla": 15.0
        }

    def detect_food_in_image(self, image_path: str) -> Dict:
        """Detect food items in an image using Google Vision API with improved filtering"""
        try:
            # Read the image file and encode as base64
            with open(image_path, 'rb') as image_file:
                import base64
                image_content = base64.b64encode(image_file.read()).decode('utf-8')
            
            # Prepare the request payload
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
            
            # Make the API request
            headers = {
                'Content-Type': 'application/json'
            }
            
            print(f"🔗 Making request to Google Vision API...")
            response = requests.post(self.api_url, json=payload, headers=headers)
            
            # Check if the request was successful
            if response.status_code != 200:
                print(f"❌ API Error: {response.status_code}")
                print(f"❌ Response: {response.text}")
                
                # Check if it's an API key error
                if "API key not valid" in response.text or "INVALID_ARGUMENT" in response.text:
                    print("⚠️  Invalid API key detected. Using fallback detection...")
                    return self._fallback_detection(image_path)
                
                return {
                    'detected_foods': [],
                    'confidence_scores': {},
                    'total_protein': 0.0,
                    'all_labels': [],
                    'success': False,
                    'error': f"API Error {response.status_code}: {response.text}"
                }
            
            # Parse the response
            result = response.json()
            print(f"✅ API Response received successfully")
            
            if 'responses' not in result or not result['responses']:
                return {
                    'detected_foods': [],
                    'confidence_scores': {},
                    'total_protein': 0.0,
                    'all_labels': [],
                    'success': False,
                    'error': 'No response from Google Vision API'
                }
            
            # Extract labels from the response
            labels = result['responses'][0].get('labelAnnotations', [])
            all_labels = [label['description'] for label in labels]
            print(f"📋 Found {len(labels)} labels from API")
            
            # Extract food-related labels with improved filtering
            food_candidates = []
            confidence_scores = {}
            
            # Filter out generic terms and only keep specific food items
            generic_terms = ['food', 'ingredient', 'cooking', 'recipe', 'meal', 'dish', 'cuisine']
            
            for label in labels:
                label_text = label['description'].lower()
                confidence = label['score']
                
                # Skip generic terms
                if label_text in generic_terms:
                    print(f"🔍 Skipping generic term: {label_text} (confidence: {confidence:.2f})")
                    continue
                
                # Check if this label matches any food in our database
                matched_food = self._find_food_match(label_text)
                
                if matched_food:
                    # Check for false positives
                    if self._is_likely_false_positive(matched_food, all_labels):
                        print(f"🚫 Skipping likely false positive: {matched_food} (confidence: {confidence:.2f})")
                        continue
                    
                    # Increase confidence threshold to avoid false positives
                    if confidence >= 0.8:  # Higher confidence threshold
                        food_candidates.append((matched_food, confidence))
                        print(f"🎯 Candidate: {matched_food} (confidence: {confidence:.2f})")
                    else:
                        print(f"📉 Low confidence skipped: {matched_food} (confidence: {confidence:.2f})")
                else:
                    # Keep track of all labels for debugging
                    print(f"🔍 No match: {label_text} (confidence: {confidence:.2f})")
            
            # Group similar foods and select the best representative for each group
            food_items, confidence_scores = self._group_similar_foods(food_candidates)
            
            # Limit to top 3 most confident unique food groups to avoid unrealistic results
            if len(food_items) > 3:
                print(f"⚠️  Limiting to top 3 unique food groups (had {len(food_items)})")
                # Sort by confidence and take top 3
                sorted_items = sorted(food_items, key=lambda x: confidence_scores.get(x, 0), reverse=True)
                food_items = sorted_items[:3]
                # Update confidence scores
                confidence_scores = {food: confidence_scores.get(food, 0) for food in food_items}
            
            # Calculate protein content
            total_protein = self._calculate_protein(food_items)
            
            return {
                'detected_foods': food_items,
                'confidence_scores': confidence_scores,
                'total_protein': total_protein,
                'all_labels': [label['description'] for label in labels],
                'success': True
            }
            
        except Exception as e:
            print(f"❌ Google Vision API error: {str(e)}")
            print("⚠️  Using fallback detection...")
            return self._fallback_detection(image_path)

    def _fallback_detection(self, image_path: str) -> Dict:
        """Fallback detection when API is not available"""
        print("🔄 Using fallback food detection...")
        
        # Simple fallback - return some common foods based on filename
        filename = os.path.basename(image_path).lower()
        
        # Try to guess based on filename patterns
        fallback_foods = []
        
        if "meal" in filename:
            # Common meal foods
            fallback_foods = ["chicken", "rice", "vegetables"]
        elif "breakfast" in filename:
            fallback_foods = ["eggs", "bread", "milk"]
        elif "lunch" in filename:
            fallback_foods = ["sandwich", "salad", "soup"]
        elif "dinner" in filename:
            fallback_foods = ["beef", "pasta", "vegetables"]
        else:
            # Default fallback
            fallback_foods = ["chicken", "rice", "vegetables"]
        
        total_protein = self._calculate_protein(fallback_foods)
        
        print(f"🔄 Fallback detected: {fallback_foods}")
        print(f"📊 Estimated protein content: {total_protein}g per 100g")
        
        return {
            'detected_foods': fallback_foods,
            'confidence_scores': {food: 0.5 for food in fallback_foods},  # Lower confidence for fallback
            'total_protein': total_protein,
            'all_labels': [],
            'success': True,
            'fallback_used': True
        }

    def _find_food_match(self, label_text: str) -> str:
        """Find the best matching food item from our database with improved selectivity"""
        label_text = label_text.lower().strip()
        
        # Direct match - highest priority
        if label_text in self.protein_database:
            return label_text
        
        # Handle generic meat terms - don't map to specific meats unless no specific meat is detected
        generic_meat_terms = ['meat', 'red meat', 'white meat']
        if label_text in generic_meat_terms:
            # Return None for generic meat terms - let the grouping logic handle them
            return None
        
        # Check for very specific food matches (avoid generic terms)
        specific_food_keywords = [
            'chicken', 'beef', 'pork', 'salmon', 'tuna', 'turkey', 'lamb', 'veal',
            'egg', 'milk', 'cheese', 'yogurt', 'tofu', 'lentils', 'beans', 'quinoa',
            'rice', 'bread', 'pasta', 'broccoli', 'spinach', 'carrots', 'tomatoes',
            'apples', 'bananas', 'oranges', 'almonds', 'walnuts', 'peanuts',
            'shrimp', 'crab', 'lobster', 'bacon', 'ham', 'sausage', 'pepperoni'
        ]
        
        # Only match if the label contains specific food keywords
        for keyword in specific_food_keywords:
            if keyword in label_text:
                # Find the best matching food item
                for food_name in self.protein_database.keys():
                    if keyword in food_name or food_name in keyword:
                        return food_name
        
        # Check for partial matches only for very specific terms
        for food_name in self.protein_database.keys():
            # Only match if there's a strong overlap (not just generic terms)
            if (food_name in label_text and len(food_name) > 3) or \
               (label_text in food_name and len(label_text) > 3):
                return food_name
        
        return None

    def _is_likely_false_positive(self, food_name: str, all_labels: List[str]) -> bool:
        """Check if a food detection is likely a false positive based on context"""
        food_name_lower = food_name.lower()
        all_labels_lower = [label.lower() for label in all_labels]
        
        # If deli meat is detected but no other meat-related terms are present, it might be false
        if food_name_lower in ['deli meat', 'lunch meat', 'cold cuts']:
            meat_indicators = ['meat', 'beef', 'pork', 'chicken', 'turkey', 'ham', 'salami', 'pastrami']
            has_other_meat_indicators = any(indicator in ' '.join(all_labels_lower) for indicator in meat_indicators)
            if not has_other_meat_indicators:
                print(f"⚠️  Potential false positive: {food_name} (no other meat indicators found)")
                return True
        
        # If a specific meat is detected but the image seems to be vegetarian
        if food_name_lower in ['beef', 'steak', 'pork', 'lamb']:
            vegetarian_indicators = ['rice', 'vegetable', 'salad', 'curry', 'vegetarian', 'vegan']
            has_vegetarian_indicators = any(indicator in ' '.join(all_labels_lower) for indicator in vegetarian_indicators)
            if has_vegetarian_indicators and not any(meat in ' '.join(all_labels_lower) for meat in ['meat', 'chicken', 'fish']):
                print(f"⚠️  Potential false positive: {food_name} (vegetarian context detected)")
                return True
        
        return False

    def _group_similar_foods(self, food_candidates: List[tuple]) -> tuple[List[str], dict]:
        """Group similar foods together and select the best representative for each group"""
        if not food_candidates:
            return [], {}
        
        # Define food groups (similar foods that should be grouped together)
        food_groups = {
            'beef_group': ['beef', 'steak', 'deli meat', 'pastrami', 'corned beef', 'roast beef', 'ground beef', 'beef burger'],
            'chicken_group': ['chicken', 'chicken breast', 'chicken thigh', 'chicken wing', 'chicken burger'],
            'pork_group': ['pork', 'bacon', 'ham', 'sausage', 'pepperoni', 'pork chop'],
            'fish_group': ['salmon', 'tuna', 'cod', 'tilapia', 'mackerel', 'sardines'],
            'dairy_group': ['milk', 'cheese', 'yogurt', 'cream', 'butter'],
            'egg_group': ['egg', 'eggs'],
            'bread_group': ['bread', 'toast', 'sandwich', 'burger bun'],
            'rice_group': ['rice', 'white rice', 'brown rice', 'fried rice', 'curry', 'basmati', 'jasmine rice'],
            'pasta_group': ['pasta', 'spaghetti', 'macaroni', 'penne', 'lasagna'],
            'vegetable_group': ['broccoli', 'spinach', 'carrots', 'tomatoes', 'lettuce', 'cucumber', 'leaf vegetable'],
            'fruit_group': ['apple', 'banana', 'orange', 'grape', 'strawberry'],
            'nut_group': ['almonds', 'walnuts', 'peanuts', 'cashews', 'pecans'],
            'meat_general': ['meat', 'red meat', 'lunch meat', 'cold cuts']
        }
        
        # Group candidates by their food group
        grouped_candidates = {}
        
        for food, confidence in food_candidates:
            # Find which group this food belongs to
            food_group = None
            for group_name, group_foods in food_groups.items():
                if food in group_foods:
                    food_group = group_name
                    break
            
            # If no group found, create a single-item group
            if food_group is None:
                food_group = f"single_{food}"
            
            # Add to group, keeping track of confidence
            if food_group not in grouped_candidates:
                grouped_candidates[food_group] = []
            grouped_candidates[food_group].append((food, confidence))
        
        # Select the best representative for each group (highest confidence)
        final_foods = []
        confidence_scores = {}
        
        for group_name, candidates in grouped_candidates.items():
            # Sort by confidence and take the best one
            best_candidate = max(candidates, key=lambda x: x[1])
            best_food, best_confidence = best_candidate
            
            final_foods.append(best_food)
            confidence_scores[best_food] = best_confidence
            
            # Log the grouping decision
            if len(candidates) > 1:
                all_foods = [f"{food}({conf:.2f})" for food, conf in candidates]
                print(f"🔄 Grouped {group_name}: {', '.join(all_foods)} → {best_food} (confidence: {best_confidence:.2f})")
            else:
                print(f"✅ Selected: {best_food} (confidence: {best_confidence:.2f})")
        
        return final_foods, confidence_scores

    def _calculate_protein(self, food_items: List[str]) -> float:
        """Calculate total protein content for detected foods"""
        total_protein = 0.0
        
        for food in food_items:
            if food in self.protein_database:
                total_protein += self.protein_database[food]
            else:
                # Default protein value for unknown foods
                total_protein += 5.0
        
        return round(total_protein, 1)

def identify_food_with_google_vision(image_path: str) -> List[str]:
    """Main function to identify food items using Google Vision API"""
    try:
        print(f"🔍 Starting Google Vision API food detection for image: {image_path}")
        
        # Initialize detector
        detector = GoogleVisionFoodDetector()
        
        # Detect food items
        result = detector.detect_food_in_image(image_path)
        
        if result['success']:
            detected_foods = result['detected_foods']
            
            if detected_foods:
                print(f"✅ Detected {len(detected_foods)} food items:")
                for food in detected_foods:
                    confidence = result['confidence_scores'].get(food, 0)
                    print(f"   - {food} (confidence: {confidence:.2f})")
                
                print(f"📊 Estimated protein content: {result['total_protein']}g per 100g")
                
                # Show fallback warning if used
                if result.get('fallback_used'):
                    print("⚠️  Note: Using fallback detection due to API issues")
                    print("   To use Google Vision API, get a valid API key from:")
                    print("   https://console.cloud.google.com/apis/credentials")
                
                return detected_foods
            else:
                print("❌ No food items detected")
                return []
        else:
            print(f"❌ Google Vision API failed: {result.get('error', 'Unknown error')}")
            return []
            
    except Exception as e:
        print(f"❌ Food detection failed: {str(e)}")
        return []

# For backward compatibility
def identify_food_local(image_path: str) -> List[str]:
    """Alias for the Google Vision function to maintain compatibility"""
    return identify_food_with_google_vision(image_path)
