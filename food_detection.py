import os
from typing import List, Dict, Optional
from google.cloud import vision
from google.oauth2 import service_account

# Load .env if available (non-fatal if package not installed)
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

class GoogleVisionFoodDetector:
    def __init__(self, service_account_path: str = "service-account-key.json"):
        """Initialize Google Vision API client with service account authentication.
        
        Args:
            service_account_path: Path to the service account JSON key file
        """
        self.service_account_path = service_account_path
        self.client = None
        
        # Initialize the Vision API client
        try:
            if os.path.exists(service_account_path):
                credentials = service_account.Credentials.from_service_account_file(
                    service_account_path,
                    scopes=['https://www.googleapis.com/auth/cloud-platform']
                )
                self.client = vision.ImageAnnotatorClient(credentials=credentials)
                print(f"✅ Google Vision API initialized with service account: {service_account_path}")
            else:
                raise FileNotFoundError(f"Service account file not found: {service_account_path}")
        except Exception as e:
            print(f"❌ Failed to initialize Google Vision API: {e}")
            raise e
        
        # Comprehensive protein database with extensive food items and dishes
        self.protein_database = {
            # Meat & Fish (High Protein)
            "chicken": 31.0, "chicken breast": 31.0, "chicken thigh": 28.0, "chicken wing": 30.0,
            "chicken nuggets": 18.0, "chicken tenders": 25.0, "fried chicken": 25.0, "roasted chicken": 31.0,
            "chicken soup": 8.0, "chicken salad": 15.0, "chicken curry": 18.0, "chicken marsala": 20.0,
            "beef": 26.0, "steak": 26.0, "ground beef": 26.0, "beef steak": 26.0, "ribeye": 26.0, "sirloin": 26.0,
            "filet mignon": 26.0, "t-bone": 26.0, "porterhouse": 26.0, "beef burger": 26.0, "hamburger": 26.0,
            "beef stew": 15.0, "beef stroganoff": 18.0, "beef tacos": 15.0, "beef chili": 18.0,
            "pork": 25.0, "pork chop": 25.0, "bacon": 37.0, "ham": 22.0, "pork loin": 25.0, "pork tenderloin": 25.0,
            "pork belly": 25.0, "pulled pork": 25.0, "pork ribs": 25.0, "pork shoulder": 25.0,
            "sausage": 18.0, "pepperoni": 25.0, "salami": 22.0, "prosciutto": 28.0, "mortadella": 22.0,
            "chorizo": 22.0, "kielbasa": 18.0, "bratwurst": 15.0, "italian sausage": 18.0,
            "salmon": 20.0, "tuna": 30.0, "cod": 18.0, "tilapia": 26.0, "trout": 20.0, "mackerel": 19.0,
            "halibut": 20.0, "sea bass": 20.0, "red snapper": 20.0, "grouper": 20.0, "swordfish": 20.0,
            "shrimp": 24.0, "crab": 19.0, "lobster": 20.0, "oysters": 9.0, "mussels": 12.0, "clams": 12.0,
            "scallops": 20.0, "calamari": 18.0, "octopus": 18.0, "crayfish": 18.0,
            "turkey": 29.0, "turkey breast": 29.0, "duck": 23.0, "goose": 22.0, "quail": 22.0,
            "pheasant": 22.0, "partridge": 22.0, "turkey bacon": 25.0, "turkey sausage": 18.0,
            "lamb": 25.0, "veal": 24.0, "venison": 30.0, "bison": 28.0, "elk": 30.0, "rabbit": 28.0,
            "goat": 25.0, "wild boar": 25.0, "antelope": 30.0, "moose": 30.0,
            
            # Dairy & Eggs (High Protein)
            "egg": 13.0, "eggs": 13.0, "scrambled eggs": 13.0, "fried eggs": 13.0, "boiled eggs": 13.0,
            "omelet": 13.0, "omelette": 13.0, "poached eggs": 13.0, "deviled eggs": 13.0,
            "milk": 3.4, "cheese": 25.0, "cheddar": 25.0, "mozzarella": 22.0, "parmesan": 38.0,
            "feta": 14.0, "blue cheese": 21.0, "swiss": 27.0, "gouda": 25.0, "brie": 20.0,
            "yogurt": 10.0, "greek yogurt": 10.0, "cottage cheese": 11.0, "cream cheese": 6.0,
            "butter": 0.9, "cream": 2.1, "sour cream": 2.4, "whipping cream": 2.1,
            
            # Plant-based Proteins (Medium-High Protein)
            "tofu": 8.0, "tempeh": 20.0, "edamame": 11.0, "soybeans": 36.0, "soy milk": 3.3,
            "lentils": 9.0, "beans": 7.0, "black beans": 8.0, "kidney beans": 8.0, "pinto beans": 8.0,
            "navy beans": 8.0, "lima beans": 8.0, "cannellini beans": 8.0, "great northern beans": 8.0, "white beans": 8.0, "kidney beans": 8.0, "pinto beans": 8.0, "black beans": 8.0, "garbanzo beans": 9.0, "chickpeas": 9.0,
            "chickpeas": 9.0, "garbanzo beans": 9.0, "hummus": 8.0, "falafel": 8.0,
            "split peas": 8.0, "black eyed peas": 8.0, "adzuki beans": 8.0, "mung beans": 8.0,
            "quinoa": 14.0, "seitan": 75.0, "spirulina": 57.0, "nutritional yeast": 50.0,
            "textured vegetable protein": 50.0, "pea protein": 80.0, "rice protein": 80.0,
            
            # Nuts & Seeds (Medium Protein)
            "almonds": 21.0, "walnuts": 15.0, "peanuts": 26.0, "cashews": 18.0, "pistachios": 20.0,
            "pecans": 9.0, "macadamia": 8.0, "hazelnuts": 15.0, "brazil nuts": 14.0,
            "chia seeds": 17.0, "flax seeds": 18.0, "hemp seeds": 32.0, "sunflower seeds": 21.0,
            "pumpkin seeds": 19.0, "sesame seeds": 18.0, "poppy seeds": 18.0,
            "peanut butter": 25.0, "almond butter": 21.0, "cashew butter": 18.0,
            
            # Grains & Carbs (Lower Protein)
            "rice": 2.7, "white rice": 2.7, "brown rice": 2.7, "wild rice": 4.0, "jasmine rice": 2.7,
            "bread": 8.0, "white bread": 8.0, "whole wheat bread": 8.0, "sourdough": 8.0, "bagel": 10.0,
            "pasta": 5.0, "spaghetti": 5.0, "penne": 5.0, "fettuccine": 5.0, "lasagna": 8.0,
            "oats": 17.0, "oatmeal": 17.0, "quinoa": 4.4, "barley": 3.5, "wheat": 13.0,
            "cereal": 8.0, "granola": 10.0, "muesli": 8.0,
            
            # Vegetables (Low Protein)
            "broccoli": 2.8, "spinach": 2.9, "kale": 4.3, "peas": 5.4, "green peas": 5.4,
            "corn": 3.3, "potato": 2.0, "sweet potato": 2.0, "carrot": 0.9, "onion": 1.1,
            "mushrooms": 3.1, "asparagus": 2.2, "brussels sprouts": 3.4, "cauliflower": 1.9,
            "bell pepper": 1.0, "tomato": 0.9, "cucumber": 0.7, "lettuce": 1.4, "cabbage": 1.3,
            "zucchini": 1.2, "eggplant": 1.0, "squash": 1.2, "pumpkin": 1.0,
            "artichoke": 3.3, "beets": 1.6, "celery": 0.7, "garlic": 6.4, "ginger": 1.8,
            "leek": 1.5, "parsnip": 1.2, "radish": 0.9, "rutabaga": 1.2, "turnip": 0.9,
            "bok choy": 1.5, "napa cabbage": 1.2, "watercress": 2.3, "arugula": 2.6,
            "collard greens": 3.6, "mustard greens": 2.9, "swiss chard": 1.8,
            "okra": 2.0, "jicama": 0.7, "kohlrabi": 1.7, "fennel": 1.2, "endive": 1.3,
            "escarole": 1.2, "radicchio": 1.4, "chicory": 1.4, "dandelion greens": 2.7,
            
            # Fruits (Very Low Protein)
            "apple": 0.3, "banana": 1.1, "orange": 0.9, "strawberry": 0.7, "blueberry": 0.7,
            "raspberry": 1.2, "blackberry": 1.4, "grape": 0.6, "pineapple": 0.5, "mango": 0.8,
            "avocado": 2.0, "tomato": 0.9, "lemon": 1.1, "lime": 0.7, "grapefruit": 0.8,
            "peach": 0.9, "pear": 0.4, "plum": 0.7, "cherry": 1.1, "watermelon": 0.6,
            
            # Popular Dishes & Meals (Composite Protein)
            "pizza": 12.0, "hamburger": 26.0, "hot dog": 12.0, "sandwich": 15.0, "sub": 15.0,
            "taco": 12.0, "burrito": 15.0, "quesadilla": 18.0, "enchilada": 12.0, "fajita": 15.0,
            "sushi": 8.0, "sashimi": 20.0, "ramen": 8.0, "stir fry": 15.0, "curry": 12.0,
            "pasta": 5.0, "spaghetti": 5.0, "lasagna": 8.0, "mac and cheese": 12.0, "penne": 5.0,
            "soup": 8.0, "stew": 12.0, "bean stew": 12.0, "vegetable stew": 8.0, "meat stew": 15.0, "chili": 15.0, "casserole": 12.0, "goulash": 12.0,
            "salad": 8.0, "caesar salad": 12.0, "greek salad": 10.0, "cobb salad": 15.0,
            "steak": 26.0, "grilled chicken": 31.0, "fried chicken": 25.0, "fish and chips": 15.0,
            "meatballs": 18.0, "meatloaf": 18.0, "roast beef": 26.0, "pulled pork": 25.0,
            "barbecue": 20.0, "bbq": 20.0, "kebab": 18.0, "gyro": 18.0, "shawarma": 18.0,
            "dumplings": 8.0, "spring rolls": 6.0, "egg rolls": 8.0, "wonton": 8.0, "potstickers": 8.0,
            "noodles": 5.0, "rice": 2.7, "fried rice": 6.0, "risotto": 6.0, "paella": 12.0,
            "omelet": 13.0, "scrambled eggs": 13.0, "frittata": 12.0, "quiche": 12.0,
            "pancakes": 6.0, "waffles": 6.0, "french toast": 8.0, "cereal": 8.0,
            "oatmeal": 17.0, "granola": 10.0, "yogurt": 10.0, "smoothie": 8.0,
            
            # International Cuisines
            "pad thai": 8.0, "pho": 8.0, "bibimbap": 12.0, "bulgogi": 20.0, "japchae": 8.0,
            "miso soup": 6.0, "tempura": 8.0, "teriyaki": 18.0, "sukiyaki": 15.0,
            "dim sum": 8.0, "kung pao": 15.0, "sweet and sour": 8.0, "general tso": 15.0,
            "butter chicken": 18.0, "tikka masala": 15.0, "biryani": 12.0, "naan": 8.0,
            "falafel": 8.0, "hummus": 8.0, "tabbouleh": 6.0, "baba ganoush": 4.0,
            "paella": 12.0, "tapas": 10.0, "gazpacho": 4.0, "ratatouille": 6.0,
            "coq au vin": 20.0, "beef bourguignon": 20.0, "cassoulet": 15.0,
            "schnitzel": 18.0, "bratwurst": 15.0, "sauerbraten": 20.0,
            "borscht": 8.0, "pelmeni": 12.0, "goulash": 12.0, "paprikash": 15.0,
            "moussaka": 12.0, "souvlaki": 18.0, "dolmades": 8.0, "spanakopita": 8.0,
            "feijoada": 15.0, "moqueca": 12.0, "churrasco": 25.0, "empanada": 8.0,
            "ceviche": 15.0, "arepa": 8.0, "tamale": 8.0, "pozole": 12.0,
            
            # Snacks & Treats
            "chips": 6.0, "popcorn": 11.0, "pretzels": 10.0, "crackers": 8.0, "nuts": 20.0,
            "trail mix": 15.0, "protein bar": 20.0, "energy bar": 8.0, "granola bar": 8.0,
            "ice cream": 4.0, "yogurt": 10.0, "pudding": 3.0, "jello": 2.0,
            
            # Beverages
            "milk": 3.4, "soy milk": 3.3, "almond milk": 1.0, "oat milk": 1.0, "protein shake": 25.0,
            "smoothie": 8.0, "juice": 0.5, "coffee": 0.1, "tea": 0.0,
            
            # Condiments & Sauces
            "ketchup": 1.0, "mustard": 4.0, "mayonnaise": 1.0, "hot sauce": 0.5, "soy sauce": 8.0,
            "teriyaki": 8.0, "barbecue sauce": 1.0, "ranch": 1.0, "italian dressing": 1.0,
            
            # Desserts
            "cake": 5.0, "cookie": 5.0, "brownie": 4.0, "pie": 4.0, "cheesecake": 6.0,
            "chocolate": 4.0, "candy": 1.0, "gum": 0.0
        }
        
        # High-confidence food keywords that should trigger detection
        self.food_keywords = {
            "meat": ["chicken", "beef", "pork", "lamb", "turkey", "duck", "steak", "meat"],
            "fish": ["salmon", "tuna", "cod", "tilapia", "fish", "seafood"],
            "dairy": ["milk", "cheese", "yogurt", "cream", "butter"],
            "eggs": ["egg", "eggs", "omelet", "scrambled"],
            "legumes": ["beans", "lentils", "chickpeas", "peas"],
            "nuts": ["almonds", "walnuts", "peanuts", "cashews", "nuts"],
            "grains": ["rice", "bread", "pasta", "oats", "quinoa", "cereal"],
            "vegetables": ["broccoli", "spinach", "carrot", "potato", "tomato"],
            "fruits": ["apple", "banana", "orange", "berry", "fruit"]
        }

    def detect_food_in_image(self, image_path: str) -> Dict:
        """Detect food items in an image using Google Vision API with maximum accuracy"""
        if not self.client:
            raise RuntimeError("Google Vision API client not initialized")
        
        try:
            print(f"🔍 Analyzing image with Google Cloud Vision API: {image_path}")
            
            # Read the image file
            with open(image_path, 'rb') as image_file:
                content = image_file.read()
            
            image = vision.Image(content=content)
            
            # Perform label detection with higher max results
            response = self.client.label_detection(image=image)
            labels = response.label_annotations
            
            # Process detected labels with extremely high confidence threshold
            detected_foods = []
            confidence_scores = {}
            
            print(f"🏷️  Detected {len(labels)} labels from Vision API:")
            for label in labels:
                label_desc = label.description.lower().strip()
                confidence = label.score
                print(f"   - {label_desc} (confidence: {confidence:.3f})")
                
                # Only process extremely high-confidence labels (0.90 or higher)
                if confidence >= 0.90:
                    # Check if this label matches any food items with ultra-strict matching
                    food_items = self._extract_food_with_ultra_strict_matching(label_desc, confidence)
                    for food in food_items:
                        if food not in detected_foods:
                            detected_foods.append(food)
                            confidence_scores[food] = confidence
            
            # Apply maximum quality filtering
            filtered_foods = self._filter_maximum_quality_detections(detected_foods, confidence_scores)
            
            if not filtered_foods:
                print("⚠️  No maximum-quality food items detected in image")
                return {
                    "foods": [],
                    "protein_per_100g": 0,
                    "confidence_scores": {},
                    "detection_method": "google_vision_api"
                }
            
            # Calculate average protein content
            total_protein = sum(self.protein_database.get(food, 5.0) for food in filtered_foods)
            avg_protein = total_protein / len(filtered_foods) if filtered_foods else 0
            
            print(f"🎯 Successfully detected {len(filtered_foods)} maximum-quality food items:")
            for food in filtered_foods:
                conf = confidence_scores.get(food, 0.5)
                protein = self.protein_database.get(food, 5.0)
                print(f"   - {food} (confidence: {conf:.3f}, protein: {protein}g/100g)")
            
            print(f"📊 Average protein content: {avg_protein:.1f}g per 100g")
            
            return {
                "foods": filtered_foods,
                "protein_per_100g": round(avg_protein, 1),
                "confidence_scores": {k: v for k, v in confidence_scores.items() if k in filtered_foods},
                "detection_method": "google_vision_api"
            }
            
        except Exception as e:
            print(f"❌ Google Vision API error: {e}")
            raise e

    def _extract_food_with_ultra_strict_matching(self, label: str, confidence: float) -> List[str]:
        """Extract food items from Vision API labels with ultra-strict matching for maximum accuracy"""
        foods = []
        
        # Clean and normalize the label
        label = label.lower().strip()
        
        # Direct exact matches only - highest priority
        if label in self.protein_database:
            foods.append(label)
            return foods
        
        # Special handling for stew-like dishes (more lenient)
        stew_keywords = ["stew", "soup", "chili", "casserole", "goulash"]
        if any(keyword in label for keyword in stew_keywords):
            # For stew-like dishes, be more lenient with matching
            for food_item in self.protein_database.keys():
                if food_item in label and len(food_item) >= 3:  # Lower threshold for stew dishes
                    # More lenient matching for stew dishes
                    is_stew_match = (
                        food_item in label or
                        label.startswith(food_item + " ") or
                        label.endswith(" " + food_item) or
                        food_item in label.split() or
                        any(word in food_item for word in label.split())
                    )
                    
                    if is_stew_match and food_item not in foods:
                        foods.append(food_item)
                        return foods  # Return immediately for stew dishes
        
        # Ultra-restrictive partial matching - only for very specific cases
        for food_item in self.protein_database.keys():
            if food_item in label and len(food_item) >= 5:  # Only match food items with 5+ characters
                # Check if the food item is a dominant part of the label
                # Must be at least 80% of the label length or be a clear prefix/suffix
                # Additional validation to prevent false matches
                is_dominant_match = (
                    len(food_item) >= len(label) * 0.8 or 
                    label.startswith(food_item + " ") or 
                    label.endswith(" " + food_item) or
                    label == food_item or
                    label.startswith(food_item + ",") or
                    label.endswith("," + food_item) or
                    label.startswith(food_item + " and") or
                    label.endswith(" and " + food_item)
                )
                
                # Additional check: ensure it's not part of a longer, different word
                is_not_partial_word = (
                    not any(other_food != food_item and other_food.startswith(food_item) 
                           for other_food in self.protein_database.keys())
                )
                
                if is_dominant_match and is_not_partial_word:
                    if food_item not in foods:
                        foods.append(food_item)
                        # Return immediately after first perfect match
                        return foods
        
        # Category-based matching - only for extremely specific, ultra-high-confidence categories
        if confidence >= 0.98:  # Ultra-high confidence threshold
            ultra_specific_categories = {
                "meat": ["chicken", "beef", "pork", "lamb", "turkey", "steak"],
                "fish": ["salmon", "tuna", "cod", "tilapia"],
                "dairy": ["milk", "cheese", "yogurt"],
                "eggs": ["egg", "eggs"],
                "legumes": ["beans", "lentils", "chickpeas"],
                "nuts": ["almonds", "walnuts", "peanuts", "cashews"]
            }
            
            for category, items in ultra_specific_categories.items():
                if category in label:
                    # Only add the most relevant item from the category
                    for item in items:
                        if item in self.protein_database and item not in foods:
                            foods.append(item)
                            return foods  # Return immediately after first category match
        
        return foods

    def _filter_maximum_quality_detections(self, foods: List[str], confidence_scores: Dict[str, float]) -> List[str]:
        """Filter detections to only include maximum-quality, highly relevant food items"""
        filtered = []
        
        for food in foods:
            confidence = confidence_scores.get(food, 0.5)
            protein_content = self.protein_database.get(food, 0)
            
            # Only include foods with:
            # 1. Ultra-high confidence (0.90+)
            # 2. Significant protein content (>5g/100g)
            # 3. Not a generic term
            # 4. Minimum length requirement
            # 5. Additional validation for maximum accuracy
            generic_terms = ["food", "meal", "dish", "plate", "dinner", "lunch", "breakfast", 
                           "cuisine", "cooking", "recipe", "ingredient", "protein", "meat", "fish",
                           "animal", "creature", "organism", "substance", "material"]
            
            # Additional validation: ensure the food item is specific and not ambiguous
            # Lower confidence threshold for stew-like dishes
            stew_keywords = ["stew", "soup", "chili", "casserole", "goulash"]
            is_stew_dish = any(keyword in food for keyword in stew_keywords)
            min_confidence = 0.75 if is_stew_dish else 0.90  # Lower threshold for stew dishes
            
            is_specific_food = (
                confidence >= min_confidence and 
                protein_content > 5.0 and 
                len(food) >= 4 and
                food not in generic_terms and
                not any(word in food for word in ["mix", "combination", "variety", "assortment"])
            )
            
            if is_specific_food:
                filtered.append(food)
        
        # Sort by confidence first, then by protein content, take only the MOST confident detection
        filtered.sort(key=lambda x: (confidence_scores.get(x, 0), self.protein_database.get(x, 0)), reverse=True)
        
        # Return only the single most confident detection to ensure maximum accuracy
        return filtered[:1] if filtered else []

    def calculate_protein_content(self, foods: List[str], portion_size: float = 100.0) -> float:
        """Calculate total protein content for detected foods"""
        if not foods:
            return 0.0
        
        total_protein = 0.0
        for food in foods:
            protein_per_100g = self.protein_database.get(food, 5.0)  # Default 5g if not found
            total_protein += protein_per_100g
        
        # Calculate for portion size
        portion_protein = (total_protein / len(foods)) * (portion_size / 100.0)
        
        return round(portion_protein, 1)


def identify_food_with_google_vision(image_path: str) -> List[str]:
    """Main function to identify food items using Google Vision API with service account"""
    try:
        print(f"🔍 Starting Google Cloud Vision API food detection for image: {image_path}")
        
        # Initialize detector
        detector = GoogleVisionFoodDetector()
        
        # Detect food items
        result = detector.detect_food_in_image(image_path)
        detected_foods = result.get('foods', [])
        
        if detected_foods:
            print(f"✅ Detection successful! Found {len(detected_foods)} food items: {detected_foods}")
        else:
            print("❌ No high-quality food items detected")
            
        return detected_foods
        
    except FileNotFoundError as e:
        print(f"❌ Service account file not found: {e}")
        print("🔧 Please ensure 'service-account-key.json' is in the project directory")
        raise e
    except Exception as e:
        print(f"❌ Food detection failed: {e}")
        raise e


# For backward compatibility - but this will only use Google Vision API
def identify_food_local(image_path: str) -> List[str]:
    """Alias for the Google Vision function to maintain compatibility"""
    return identify_food_with_google_vision(image_path)