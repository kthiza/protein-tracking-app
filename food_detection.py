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
            
            # Grains & Carbs (lower protein)
            "rice": 2.7, "bread": 8.0, "pasta": 5.0, "oats": 17.0,
            "quinoa": 4.4, "barley": 3.5, "wheat": 13.0,
            
            # Vegetables (lower protein)
            "broccoli": 2.8, "spinach": 2.9, "kale": 4.3, "peas": 5.4,
            "corn": 3.3, "potato": 2.0, "sweet potato": 2.0,
            "mushrooms": 3.1, "asparagus": 2.2, "brussels sprouts": 3.4,
            
            # Fruits (very low protein)
            "apple": 0.3, "banana": 1.1, "orange": 0.9, "strawberry": 0.7,
            "blueberry": 0.7, "avocado": 2.0, "tomato": 0.9,
        }
        
        # Food categories for improved detection
        self.food_categories = {
            "meat": ["chicken", "beef", "pork", "lamb", "turkey", "duck", "steak"],
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
        """Detect food items in an image using Google Vision API"""
        if not self.client:
            raise RuntimeError("Google Vision API client not initialized")
        
        try:
            print(f"🔍 Analyzing image with Google Cloud Vision API: {image_path}")
            
            # Read the image file
            with open(image_path, 'rb') as image_file:
                content = image_file.read()
            
            image = vision.Image(content=content)
            
            # Perform label detection
            response = self.client.label_detection(image=image)
            labels = response.label_annotations
            
            # Also perform text detection (for menu items, etc.)
            text_response = self.client.text_detection(image=image)
            texts = text_response.text_annotations
            
            # Process detected labels
            detected_foods = []
            confidence_scores = {}
            
            print(f"🏷️  Detected {len(labels)} labels from Vision API:")
            for label in labels:
                label_desc = label.description.lower()
                confidence = label.score
                print(f"   - {label_desc} (confidence: {confidence:.2f})")
                
                # Check if this label matches any food items
                food_items = self._extract_food_from_label(label_desc)
                for food in food_items:
                    if food not in detected_foods:
                        detected_foods.append(food)
                        confidence_scores[food] = confidence
            
            # Process detected text for additional food identification
            if texts:
                print(f"📝 Detected text in image:")
                for text in texts[:5]:  # Limit to first 5 text detections
                    text_desc = text.description.lower()
                    print(f"   - {text_desc}")
                    food_items = self._extract_food_from_text(text_desc)
                    for food in food_items:
                        if food not in detected_foods:
                            detected_foods.append(food)
                            confidence_scores[food] = 0.8  # Default confidence for text detection
            
            if not detected_foods:
                print("⚠️  No food items detected in image")
                return {
                    "foods": [],
                    "protein_per_100g": 0,
                    "confidence_scores": {},
                    "detection_method": "google_vision_api"
                }
            
            # Calculate average protein content
            total_protein = sum(self.protein_database.get(food, 5.0) for food in detected_foods)
            avg_protein = total_protein / len(detected_foods) if detected_foods else 0
            
            print(f"🎯 Successfully detected {len(detected_foods)} food items:")
            for food in detected_foods:
                conf = confidence_scores.get(food, 0.5)
                protein = self.protein_database.get(food, 5.0)
                print(f"   - {food} (confidence: {conf:.2f}, protein: {protein}g/100g)")
            
            print(f"📊 Average protein content: {avg_protein:.1f}g per 100g")
            
            return {
                "foods": detected_foods,
                "protein_per_100g": round(avg_protein, 1),
                "confidence_scores": confidence_scores,
                "detection_method": "google_vision_api"
            }
            
        except Exception as e:
            print(f"❌ Google Vision API error: {e}")
            raise e

    def _extract_food_from_label(self, label: str) -> List[str]:
        """Extract food items from Vision API labels"""
        foods = []
        
        # Direct matches
        if label in self.protein_database:
            foods.append(label)
        
        # Partial matches
        for food_item in self.protein_database.keys():
            if food_item in label or label in food_item:
                if food_item not in foods:
                    foods.append(food_item)
        
        # Category-based matching
        for category, items in self.food_categories.items():
            if category in label:
                foods.extend([item for item in items if item in self.protein_database])
                break
        
        return foods

    def _extract_food_from_text(self, text: str) -> List[str]:
        """Extract food items from detected text"""
        foods = []
        text_words = text.split()
        
        for word in text_words:
            word = word.lower().strip('.,!?;:')
            if word in self.protein_database:
                if word not in foods:
                    foods.append(word)
        
        return foods

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
            print("❌ No food items detected")
            
        return detected_foods
        
    except FileNotFoundError as e:
        print(f"❌ Service account file not found: {e}")
        print("🔧 Please ensure 'service-account-key.json' is in the project directory")
        raise e
    except Exception as e:
        print(f"❌ Food detection failed: {e}")
        raise e


# For backward compatibility
def identify_food_local(image_path: str) -> List[str]:
    """Alias for the Google Vision function to maintain compatibility"""
    return identify_food_with_google_vision(image_path)