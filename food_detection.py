import os
from typing import List, Dict, Optional, Tuple
from google.cloud import vision
from google.oauth2 import service_account

# Load .env if available (non-fatal if package not installed)
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

FD_VERSION = "food-detect-v8: labels 0.70/0.55/0.45, web 0.65/0.55/0.45, crops:on"

try:
    from PIL import Image
    _PIL_AVAILABLE = True
except Exception:
    _PIL_AVAILABLE = False

class GoogleVisionFoodDetector:
    def __init__(self, service_account_path: str = None):
        """Initialize Google Vision API client with service account authentication.
        
        Args:
            service_account_path: Path to the service account JSON key file (optional)
        """
        self.service_account_path = service_account_path
        self.client = None
        
        # Initialize the Vision API client
        try:
            # Try environment variable first (recommended for Render deployment)
            GOOGLE_SERVICE_ACCOUNT_JSON = os.getenv("GOOGLE_SERVICE_ACCOUNT")
            
            if GOOGLE_SERVICE_ACCOUNT_JSON:
                # Use environment variable (Render deployment)
                try:
                    import json
                    service_account_info = json.loads(GOOGLE_SERVICE_ACCOUNT_JSON)
                    credentials = service_account.Credentials.from_service_account_info(
                        service_account_info,
                        scopes=['https://www.googleapis.com/auth/cloud-platform']
                    )
                    self.client = vision.ImageAnnotatorClient(credentials=credentials)
                    print(f"✅ Google Vision API initialized with environment variable")
                    print(f"   Project ID: {service_account_info.get('project_id', 'Unknown')}")
                except (json.JSONDecodeError, KeyError) as e:
                    print(f"❌ Invalid Google Vision service account JSON in environment: {e}")
                    raise e
            
            elif service_account_path and os.path.exists(service_account_path):
                # Use service account file (local development)
                credentials = service_account.Credentials.from_service_account_file(
                    service_account_path,
                    scopes=['https://www.googleapis.com/auth/cloud-platform']
                )
                self.client = vision.ImageAnnotatorClient(credentials=credentials)
                print(f"✅ Google Vision API initialized with service account file: {service_account_path}")
            
            elif os.path.exists("service-account-key.json"):
                # Fallback to default service account file
                credentials = service_account.Credentials.from_service_account_file(
                    "service-account-key.json",
                    scopes=['https://www.googleapis.com/auth/cloud-platform']
                )
                self.client = vision.ImageAnnotatorClient(credentials=credentials)
                print(f"✅ Google Vision API initialized with default service account file")
            
            else:
                raise FileNotFoundError("No Google Vision credentials found. Set GOOGLE_SERVICE_ACCOUNT environment variable or provide service account file.")
                
        except Exception as e:
            print(f"❌ Failed to initialize Google Vision API: {e}")
            raise e
        
        # Comprehensive protein database with realistic values (20% reduced from USDA values)
        self.protein_database = {
            # Meat & Fish (High Protein) - Values per 100g cooked (reduced by 20%)
n breakfast            "chicken": 35.0, "chicken breast": 35.0, "chicken thigh": 30.8, "chicken wing": 33.6,
            "chicken nuggets": 9.8, "chicken tenders": 14.0, "fried chicken": 14.0, "roasted chicken": 17.5,
            "chicken soup": 4.2, "chicken salad": 8.4, "chicken curry": 9.8, "chicken marsala": 11.2,
            "beef": 29.4, "steak": 29.4, "ground beef": 29.4, "beef steak": 29.4, "ribeye": 29.4, "sirloin": 29.4,
            "filet mignon": 14.7, "t-bone": 14.7, "porterhouse": 14.7, "beef burger": 14.7, "hamburger": 14.7,
            "beef stew": 8.4, "beef stroganoff": 9.8, "beef tacos": 8.4, "beef chili": 9.8,
            "pork": 28.0, "pork chop": 28.0, "bacon": 42.0, "ham": 25.2, "pork loin": 28.0, "pork tenderloin": 28.0,
            "pork belly": 14.0, "pulled pork": 14.0, "pork ribs": 14.0, "pork shoulder": 14.0,
            "sausage": 19.6, "pepperoni": 28.0, "salami": 25.2, "prosciutto": 30.8, "mortadella": 25.2,
            "chorizo": 12.6, "kielbasa": 9.8, "bratwurst": 8.4, "italian sausage": 9.8,
            "salmon": 22.4, "tuna": 33.6, "cod": 19.6, "tilapia": 29.4, "trout": 22.4, "mackerel": 21.0,
            "halibut": 22.4, "sea bass": 22.4, "red snapper": 22.4, "grouper": 22.4, "swordfish": 22.4,
            "shrimp": 26.6, "crab": 21.0, "lobster": 22.4, "oysters": 9.8, "mussels": 14.0, "clams": 14.0,
            "scallops": 22.4, "calamari": 19.6, "octopus": 19.6, "crayfish": 19.6,
            "turkey": 32.2, "turkey breast": 32.2, "duck": 25.2, "goose": 25.2, "quail": 25.2,
            "pheasant": 25.2, "partridge": 25.2, "turkey bacon": 28.0, "turkey sausage": 19.6,
            "lamb": 28.0, "veal": 26.6, "venison": 33.6, "bison": 30.8, "elk": 33.6, "rabbit": 30.8,
            "goat": 28.0, "wild boar": 28.0, "antelope": 33.6, "moose": 33.6,
            
            # Dairy & Eggs (High Protein) - 30% reduced from previous values
            "egg": 14.0, "eggs": 14.0, "scrambled eggs": 14.0, "fried eggs": 14.0, "fried egg": 14.0, "boiled eggs": 14.0,
            "omelet": 14.0, "omelette": 14.0, "poached eggs": 14.0, "deviled eggs": 14.0, "yolk": 18.2,
            "milk": 3.8, "cheese": 28.0, "cheddar": 28.0, "mozzarella": 25.2, "parmesan": 42.0,
            "feta": 15.4, "blue cheese": 23.8, "swiss": 30.8, "gouda": 28.0, "brie": 22.4,
            "yogurt": 11.2, "greek yogurt": 11.2, "cottage cheese": 12.6, "cream cheese": 7.0,
            "butter": 1.0, "cream": 2.4, "sour cream": 2.6, "whipping cream": 2.4,
            
            # Plant-based Proteins (Medium-High Protein)
            "tofu": 8.0, "tempeh": 20.0, "edamame": 11.0, "soybeans": 36.0, "soy milk": 3.3,
            "lentils": 9.0,             "beans": 9.0, "baked beans": 9.0, "black beans": 9.0, "kidney beans": 9.0, "pinto beans": 9.0,
            "navy beans": 9.0, "lima beans": 9.0, "cannellini beans": 9.0, "great northern beans": 9.0, "white beans": 9.0, "garbanzo beans": 9.0, "chickpeas": 9.0,
            "hummus": 8.0, "falafel": 8.0,
            "split peas": 9.0, "black eyed peas": 8.0, "adzuki beans": 8.0, "mung beans": 8.0,
            "quinoa": 14.0, "seitan": 25.0, "spirulina": 57.0, "nutritional yeast": 50.0,
            "textured vegetable protein": 50.0, "pea protein": 25.0, "rice protein": 25.0,
            
            # Nuts & Seeds (Medium Protein)
            "almonds": 21.0, "walnuts": 15.0, "peanuts": 26.0, "cashews": 18.0, "pistachios": 20.0,
            "pecans": 9.0, "macadamia": 8.0, "hazelnuts": 15.0, "brazil nuts": 14.0,
            "chia seeds": 17.0, "flax seeds": 18.0, "hemp seeds": 32.0, "sunflower seeds": 21.0,
            "pumpkin seeds": 19.0, "sesame seeds": 18.0, "poppy seeds": 18.0,
            "peanut butter": 25.0, "almond butter": 21.0, "cashew butter": 18.0,
            
            # Grains & Carbs (Lower Protein) - Updated with accurate values
            "rice": 2.7, "white rice": 2.7, "brown rice": 2.7, "wild rice": 4.0, "jasmine rice": 2.7,
            "bread": 8.0, "white bread": 8.0, "whole wheat bread": 8.0, "sourdough": 8.0, "bagel": 10.0,
            "pasta": 5.0, "spaghetti": 5.0, "penne": 5.0, "fettuccine": 5.0, "lasagna": 8.0, "linguine": 5.0, "rigatoni": 5.0, "ziti": 5.0, "rotini": 5.0, "farfalle": 5.0, "orecchiette": 5.0, "gnocchi": 5.0, "ravioli": 8.0, "tortellini": 8.0, "manicotti": 8.0, "cannelloni": 8.0,
            "bolognese": 8.0, "marinara": 3.0, "alfredo": 6.0, "carbonara": 12.0, "pesto": 4.0,
            "tomato sauce": 2.0,
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
            
            # Popular Dishes & Meals (Composite Protein) - UPDATED WITH ACCURATE VALUES
            "pizza": 12.0, "hamburger": 26.0, "hot dog": 12.0, "sandwich": 15.0, "sub": 15.0,
            "taco": 12.0, "burrito": 15.0, "quesadilla": 18.0, "enchilada": 12.0, "fajita": 15.0, "shawarma": 18.0, "gyro": 18.0, "kebab": 18.0, "wrap": 12.0, "pita": 8.0, "tortilla": 8.0, "flatbread": 8.0, "naan": 8.0, "roti": 8.0, "chapati": 8.0,
            "sushi": 8.0, "sashimi": 20.0, "ramen": 8.0,
            "pasta": 5.0, "spaghetti": 5.0, "lasagna": 8.0, "mac and cheese": 12.0, "penne": 5.0,
            "bean stew": 12.0, "vegetable stew": 8.0, "meat stew": 15.0, "chili": 15.0, "casserole": 12.0, "goulash": 12.0,
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
            "chocolate": 4.0, "candy": 1.0, "gum": 0.0,
            
            # ADDITIONAL COMMON FOODS WITH ACCURATE PROTEIN VALUES
            "toast": 8.0, "english muffin": 8.0, "croissant": 8.0, "danish": 6.0,
            "muffin": 6.0, "donut": 4.0, "cookie": 5.0, "brownie": 4.0,
            "ice cream": 4.0, "yogurt": 10.0, "pudding": 3.0, "jello": 2.0,
            "chocolate": 4.0, "candy": 1.0, "gum": 0.0,
            "coffee": 0.1, "tea": 0.0, "juice": 0.5, "soda": 0.0,
            "beer": 0.5, "wine": 0.1, "liquor": 0.0,
            "ketchup": 1.0, "mustard": 4.0, "mayonnaise": 1.0, "hot sauce": 0.5,
            "soy sauce": 8.0, "teriyaki": 8.0, "barbecue sauce": 1.0,
            "ranch": 1.0, "italian dressing": 1.0, "vinaigrette": 1.0,
            "olive oil": 0.0, "vegetable oil": 0.0, "butter": 0.9,
            "margarine": 0.2, "shortening": 0.0, "lard": 0.0,
            "sugar": 0.0, "honey": 0.3, "maple syrup": 0.0, "agave": 0.0,
            "salt": 0.0, "pepper": 10.0, "garlic powder": 16.0, "onion powder": 10.0,
            "oregano": 9.0, "basil": 22.0, "thyme": 6.0, "rosemary": 3.0,
            "cumin": 18.0, "coriander": 12.0, "turmeric": 8.0, "ginger": 1.8,
            "cinnamon": 4.0, "nutmeg": 6.0, "cloves": 6.0, "allspice": 6.0,
            "vanilla": 0.1, "almond extract": 0.0, "lemon extract": 0.0,
            "food coloring": 0.0, "preservatives": 0.0, "additives": 0.0,
            
            # Additional common foods that might be detected by AI
            "pasul": 21.0,  # Serbian bean dish
            "english breakfast": 25.0,  # Full English breakfast with eggs, bacon, beans, etc.
            "full english": 25.0, "fry up": 25.0, "breakfast": 15.0,
            "continental breakfast": 8.0, "american breakfast": 15.0,
            "breakfast sandwich": 15.0, "breakfast burrito": 18.0,
            "omelette": 13.0, "scrambled eggs": 13.0, "fried eggs": 13.0,
            "poached eggs": 13.0, "soft boiled eggs": 13.0, "hard boiled eggs": 13.0,
            "sunny side up": 13.0, "over easy": 13.0, "over medium": 13.0, "over hard": 13.0,
            "benedict": 15.0, "florentine": 12.0, "royale": 15.0,
            "hash browns": 3.0, "home fries": 3.0, "breakfast potatoes": 3.0,
            "grits": 3.0, "polenta": 3.0, "cream of wheat": 3.0,
            "french toast": 8.0, "pancakes": 6.0, "waffles": 6.0, "crepes": 6.0,
            "muffin": 6.0, "scone": 6.0, "biscuit": 6.0, "croissant": 8.0,
            "danish": 6.0, "donut": 4.0, "bagel": 10.0, "english muffin": 8.0,
            "cereal": 8.0, "granola": 10.0, "muesli": 8.0, "oatmeal": 17.0,
            "porridge": 17.0, "cream of wheat": 3.0, "farina": 3.0,
            "yogurt": 10.0, "greek yogurt": 10.0, "cottage cheese": 11.0,
            "smoothie": 8.0, "protein shake": 25.0, "meal replacement": 20.0,
            "energy bar": 8.0, "protein bar": 20.0, "granola bar": 8.0,
            "trail mix": 15.0, "nuts": 20.0, "seeds": 20.0, "dried fruit": 3.0,
            "jerky": 30.0, "beef jerky": 30.0, "turkey jerky": 30.0,
            "pepperoni": 25.0, "salami": 22.0, "prosciutto": 28.0,
            "ham": 22.0, "bacon": 37.0, "sausage": 18.0, "chorizo": 22.0,
            "pepperoni": 25.0, "mortadella": 22.0, "bologna": 15.0,
            "pastrami": 22.0, "corned beef": 22.0, "roast beef": 26.0,
            "turkey": 29.0, "chicken": 31.0, "duck": 23.0, "goose": 22.0,
            "quail": 22.0, "pheasant": 22.0, "partridge": 22.0,
            "venison": 30.0, "bison": 28.0, "elk": 30.0, "rabbit": 28.0,
            "lamb": 25.0, "veal": 24.0, "goat": 25.0, "wild boar": 25.0,
            "antelope": 30.0, "moose": 30.0, "bear": 25.0, "alligator": 25.0,
            "ostrich": 30.0, "emu": 30.0, "kangaroo": 30.0, "camel": 25.0,
            "horse": 25.0, "donkey": 25.0, "mule": 25.0, "buffalo": 25.0,
            "yak": 25.0, "llama": 25.0, "alpaca": 25.0, "guinea pig": 20.0,
            "frog": 16.0, "snail": 16.0, "escargot": 16.0, "caviar": 25.0,
            "roe": 25.0, "fish eggs": 25.0, "anchovy": 20.0, "sardine": 20.0,
            "herring": 20.0, "mackerel": 19.0, "bluefish": 20.0, "striped bass": 20.0,
            "black sea bass": 20.0, "red snapper": 20.0, "grouper": 20.0,
            "sea bass": 20.0, "bass": 20.0, "perch": 20.0, "walleye": 20.0,
            "pike": 20.0, "pickerel": 20.0, "muskellunge": 20.0, "northern pike": 20.0,
            "chain pickerel": 20.0, "grass pickerel": 20.0, "redfin pickerel": 20.0,
            "american pickerel": 20.0, "european pike": 20.0, "northern pike": 20.0,
            "southern pike": 20.0, "western pike": 20.0, "eastern pike": 20.0,
            "central pike": 20.0, "north american pike": 20.0, "eurasian pike": 20.0,
            "amur pike": 20.0, "aquitanian pike": 20.0, "southern pike": 20.0,
            "western pike": 20.0, "eastern pike": 20.0, "central pike": 20.0,
            "north american pike": 20.0, "eurasian pike": 20.0, "amur pike": 20.0,
            "aquitanian pike": 20.0, "southern pike": 20.0, "western pike": 20.0,
            "eastern pike": 20.0, "central pike": 20.0, "north american pike": 20.0,
            "eurasian pike": 20.0, "amur pike": 20.0, "aquitanian pike": 20.0,
            
            # Additional Meat & Fish Varieties (100+ more)
            "lamb chop": 25.0, "lamb shank": 25.0, "lamb shoulder": 25.0, "lamb leg": 25.0,
            "rack of lamb": 25.0, "lamb loin": 25.0, "lamb rib": 25.0, "lamb neck": 25.0,
            "lamb breast": 25.0, "lamb kidney": 25.0, "lamb liver": 25.0, "lamb heart": 25.0,
            "lamb tongue": 25.0, "lamb brain": 25.0, "lamb sweetbreads": 25.0,
            "mutton": 25.0, "hogget": 25.0, "yearling": 25.0,
            "veal chop": 24.0, "veal cutlet": 24.0, "veal scallopini": 24.0, "veal osso buco": 24.0,
            "veal shank": 24.0, "veal shoulder": 24.0, "veal breast": 24.0, "veal kidney": 24.0,
            "veal liver": 24.0, "veal heart": 24.0, "veal tongue": 24.0, "veal sweetbreads": 24.0,
            "calf liver": 24.0, "calf brain": 24.0, "calf kidney": 24.0, "calf heart": 24.0,
            "calf tongue": 24.0, "calf sweetbreads": 24.0, "calf thymus": 24.0,
            "pork belly": 25.0, "pork shoulder": 25.0, "pork butt": 25.0, "pork picnic": 25.0,
            "pork hock": 25.0, "pork jowl": 25.0, "pork cheek": 25.0, "pork ear": 25.0,
            "pork snout": 25.0, "pork tail": 25.0, "pork trotter": 25.0, "pork kidney": 25.0,
            "pork liver": 25.0, "pork heart": 25.0, "pork tongue": 25.0, "pork brain": 25.0,
            "pork sweetbreads": 25.0, "pork chitterlings": 25.0, "pork tripe": 25.0,
            "beef tongue": 26.0, "beef liver": 26.0, "beef kidney": 26.0, "beef heart": 26.0,
            "beef brain": 26.0, "beef sweetbreads": 26.0, "beef tripe": 26.0, "beef oxtail": 26.0,
            "beef cheek": 26.0, "beef shank": 26.0, "beef brisket": 26.0, "beef plate": 26.0,
            "beef flank": 26.0, "beef skirt": 26.0, "beef hanger": 26.0, "beef flat iron": 26.0,
            "beef chuck": 26.0, "beef round": 26.0, "beef rump": 26.0, "beef top round": 26.0,
            "beef bottom round": 26.0, "beef eye round": 26.0, "beef heel": 26.0,
            "chicken liver": 31.0, "chicken heart": 31.0, "chicken gizzard": 31.0,
            "chicken neck": 31.0, "chicken back": 31.0, "chicken tail": 31.0,
            "chicken feet": 31.0, "chicken head": 31.0, "chicken brain": 31.0,
            "turkey liver": 29.0, "turkey heart": 29.0, "turkey gizzard": 29.0,
            "turkey neck": 29.0, "turkey wing": 29.0, "turkey leg": 29.0,
            "turkey thigh": 29.0, "turkey back": 29.0, "turkey tail": 29.0,
            "duck liver": 23.0, "duck heart": 23.0, "duck gizzard": 23.0,
            "duck neck": 23.0, "duck wing": 23.0, "duck leg": 23.0,
            "duck breast": 23.0, "duck back": 23.0, "duck tail": 23.0,
            "goose liver": 22.0, "goose heart": 22.0, "goose gizzard": 22.0,
            "goose neck": 22.0, "goose wing": 22.0, "goose leg": 22.0,
            "goose breast": 22.0, "goose back": 22.0, "goose tail": 22.0,
            "quail breast": 22.0, "quail leg": 22.0, "quail wing": 22.0,
            "pheasant breast": 22.0, "pheasant leg": 22.0, "pheasant wing": 22.0,
            "partridge breast": 22.0, "partridge leg": 22.0, "partridge wing": 22.0,
            "grouse breast": 22.0, "grouse leg": 22.0, "grouse wing": 22.0,
            "woodcock": 22.0, "snipe": 22.0, "teal": 22.0, "mallard": 22.0,
            "canvasback": 22.0, "redhead": 22.0, "scaup": 22.0, "wigeon": 22.0,
            "gadwall": 22.0, "pintail": 22.0, "shoveler": 22.0, "bluewing": 22.0,
            "greenwing": 22.0, "cinnamon": 22.0, "ruddy": 22.0, "bufflehead": 22.0,
            "goldeneye": 22.0, "merganser": 22.0, "eider": 22.0, "scoter": 22.0,
            "longtail": 22.0, "harlequin": 22.0, "oldsquaw": 22.0, "surf scoter": 22.0,
            "white-winged scoter": 22.0, "black scoter": 22.0, "common eider": 22.0,
            "king eider": 22.0, "spectacled eider": 22.0, "steller's eider": 22.0,
            "common goldeneye": 22.0, "barrow's goldeneye": 22.0, "bufflehead": 22.0,
            "hooded merganser": 22.0, "common merganser": 22.0, "red-breasted merganser": 22.0,
            "common loon": 22.0, "red-throated loon": 22.0, "pacific loon": 22.0,
            "arctic loon": 22.0, "yellow-billed loon": 22.0, "horned grebe": 22.0,
            "red-necked grebe": 22.0, "eared grebe": 22.0, "western grebe": 22.0,
            "clark's grebe": 22.0, "pied-billed grebe": 22.0,             "least grebe": 22.0,
            
            # Additional Fish & Seafood Varieties (200+ more)
            "atlantic cod": 18.0, "pacific cod": 18.0, "alaska cod": 18.0, "greenland cod": 18.0,
            "haddock": 18.0, "pollock": 18.0, "whiting": 18.0, "hake": 18.0,
            "lingcod": 18.0, "rockfish": 20.0, "red snapper": 20.0, "yellowtail snapper": 20.0,
            "mangrove snapper": 20.0, "mutton snapper": 20.0, "lane snapper": 20.0,
            "schoolmaster snapper": 20.0, "cubera snapper": 20.0, "dog snapper": 20.0,
            "blackfin snapper": 20.0, "silk snapper": 20.0, "queen snapper": 20.0,
            "wolffish": 20.0, "monkfish": 20.0, "anglerfish": 20.0, "goosefish": 20.0,
            "sea bass": 20.0, "black sea bass": 20.0, "striped bass": 20.0, "white bass": 20.0,
            "yellow bass": 20.0, "white perch": 20.0, "yellow perch": 20.0, "walleye": 20.0,
            "sauger": 20.0, "saugeye": 20.0, "bluegill": 20.0, "sunfish": 20.0,
            "pumpkinseed": 20.0, "redear sunfish": 20.0, "green sunfish": 20.0,
            "longear sunfish": 20.0, "warmouth": 20.0, "rock bass": 20.0,
            "crappie": 20.0, "black crappie": 20.0, "white crappie": 20.0,
            "largemouth bass": 20.0, "smallmouth bass": 20.0, "spotted bass": 20.0,
            "guadalupe bass": 20.0, "redeye bass": 20.0, "suzuki": 20.0,
            "channel catfish": 20.0, "blue catfish": 20.0, "flathead catfish": 20.0,
            "bullhead": 20.0, "yellow bullhead": 20.0, "brown bullhead": 20.0,
            "black bullhead": 20.0, "white catfish": 20.0, "madtom": 20.0,
            "stonecat": 20.0, "tadpole madtom": 20.0, "brindled madtom": 20.0,
            "northern madtom": 20.0, "margined madtom": 20.0, "slender madtom": 20.0,
            "freckled madtom": 20.0, "neosho madtom": 20.0, "checkered madtom": 20.0,
            "piebald madtom": 20.0, "saddled madtom": 20.0, "caddo madtom": 20.0,
            "elegant madtom": 20.0, "amber madtom": 20.0, "orangefin madtom": 20.0,
            "saddled madtom": 20.0, "checkered madtom": 20.0, "piebald madtom": 20.0,
            "neosho madtom": 20.0, "freckled madtom": 20.0, "slender madtom": 20.0,
            "margined madtom": 20.0, "northern madtom": 20.0, "brindled madtom": 20.0,
            "tadpole madtom": 20.0, "stonecat": 20.0, "madtom": 20.0,
            "white catfish": 20.0, "black bullhead": 20.0, "brown bullhead": 20.0,
            "yellow bullhead": 20.0, "bullhead": 20.0, "flathead catfish": 20.0,
            "blue catfish": 20.0, "channel catfish": 20.0, "suzuki": 20.0,
            "redeye bass": 20.0, "guadalupe bass": 20.0, "spotted bass": 20.0,
            "smallmouth bass": 20.0, "largemouth bass": 20.0, "white crappie": 20.0,
            "black crappie": 20.0, "crappie": 20.0, "rock bass": 20.0,
            "warmouth": 20.0, "longear sunfish": 20.0, "green sunfish": 20.0,
            "redear sunfish": 20.0, "pumpkinseed": 20.0, "sunfish": 20.0,
            "bluegill": 20.0, "saugeye": 20.0, "sauger": 20.0, "walleye": 20.0,
            "yellow perch": 20.0, "white perch": 20.0, "yellow bass": 20.0,
            "white bass": 20.0, "striped bass": 20.0, "black sea bass": 20.0,
            "sea bass": 20.0, "goosefish": 20.0, "anglerfish": 20.0, "monkfish": 20.0,
            "wolffish": 20.0, "queen snapper": 20.0, "silk snapper": 20.0,
            "blackfin snapper": 20.0, "dog snapper": 20.0, "cubera snapper": 20.0,
            "schoolmaster snapper": 20.0, "lane snapper": 20.0, "mutton snapper": 20.0,
            "mangrove snapper": 20.0, "yellowtail snapper": 20.0, "red snapper": 20.0,
            "rockfish": 20.0, "lingcod": 18.0, "hake": 18.0, "whiting": 18.0,
            "pollock": 18.0, "haddock": 18.0, "greenland cod": 18.0, "alaska cod": 18.0,
            "pacific cod": 18.0, "atlantic cod": 18.0,
            
            # Shellfish & Crustaceans (100+ more)
            "blue crab": 19.0, "dungeness crab": 19.0, "snow crab": 19.0, "king crab": 19.0,
            "stone crab": 19.0, "spider crab": 19.0, "horseshoe crab": 19.0,
            "hermit crab": 19.0, "fiddler crab": 19.0, "ghost crab": 19.0,
            "land crab": 19.0, "coconut crab": 19.0, "robber crab": 19.0,
            "christmas island red crab": 19.0, "japanese spider crab": 19.0,
            "alaskan king crab": 19.0, "red king crab": 19.0, "blue king crab": 19.0,
            "golden king crab": 19.0, "brown king crab": 19.0, "southern king crab": 19.0,
            "northern king crab": 19.0, "atlantic king crab": 19.0, "pacific king crab": 19.0,
            "indian ocean king crab": 19.0, "antarctic king crab": 19.0,
            "arctic king crab": 19.0, "bering sea king crab": 19.0, "okhotsk king crab": 19.0,
            "japan sea king crab": 19.0, "east china sea king crab": 19.0,
            "yellow sea king crab": 19.0, "south china sea king crab": 19.0,
            "philippine sea king crab": 19.0, "coral sea king crab": 19.0,
            "tasman sea king crab": 19.0, "southern ocean king crab": 19.0,
            "mediterranean king crab": 19.0, "black sea king crab": 19.0,
            "caspian sea king crab": 19.0, "aral sea king crab": 19.0,
            "baltic sea king crab": 19.0, "north sea king crab": 19.0,
            "celtic sea king crab": 19.0, "irish sea king crab": 19.0,
            "english channel king crab": 19.0, "biscay bay king crab": 19.0,
            "gulf of mexico king crab": 19.0, "caribbean sea king crab": 19.0,
            "gulf of california king crab": 19.0, "gulf of alaska king crab": 19.0,
            "beaufort sea king crab": 19.0, "chukchi sea king crab": 19.0,
            "east siberian sea king crab": 19.0, "laptev sea king crab": 19.0,
            "kara sea king crab": 19.0, "barents sea king crab": 19.0,
            "white sea king crab": 19.0, "pechora sea king crab": 19.0,
            
            # Additional Vegetables (100+ more)
            "artichoke": 3.3, "beets": 1.6, "celery": 0.7, "garlic": 6.4, "ginger": 1.8,
            "leek": 1.5, "parsnip": 1.2, "radish": 0.9, "rutabaga": 1.2, "turnip": 0.9,
            "bok choy": 1.5, "napa cabbage": 1.2, "watercress": 2.3, "arugula": 2.6,
            "collard greens": 3.6, "mustard greens": 2.9, "swiss chard": 1.8,
            "okra": 2.0, "jicama": 0.7, "kohlrabi": 1.7, "fennel": 1.2, "endive": 1.3,
            "escarole": 1.2, "radicchio": 1.4, "chicory": 1.4, "dandelion greens": 2.7,
            "beet greens": 2.2, "turnip greens": 1.5, "radish greens": 1.3,
            "carrot greens": 1.2, "parsnip greens": 1.1, "celery greens": 1.0,
            "fennel greens": 1.2, "leek greens": 1.1, "onion greens": 1.0,
            "garlic greens": 1.5, "ginger greens": 1.0, "turmeric greens": 1.0,
            "horseradish": 1.2, "wasabi": 1.5, "daikon": 0.6, "water chestnut": 1.4,
            "bamboo shoot": 2.6, "lotus root": 2.6, "taro root": 1.5, "cassava": 1.4,
            "yuca": 1.4, "malanga": 1.4, "eddo": 1.4, "dasheen": 1.4,
            "arrowroot": 0.3, "sago": 0.2, "tapioca": 0.2, "arrowhead": 0.3,
            "water caltrop": 1.4, "chinese water chestnut": 1.4, "japanese water chestnut": 1.4,
            "indian water chestnut": 1.4, "singhara": 1.4, "pani phal": 1.4,
            "water lily root": 1.4, "lotus seed": 17.0, "lotus stem": 1.4,
            "lotus leaf": 1.4, "lotus flower": 1.4, "lotus petal": 1.4,
            "lotus stamen": 1.4, "lotus pistil": 1.4, "lotus fruit": 1.4,
            "lotus pod": 1.4, "lotus seed pod": 1.4, "lotus seed head": 1.4,
            "lotus seed cluster": 1.4, "lotus seed bunch": 1.4, "lotus seed group": 1.4,
            "lotus seed collection": 1.4, "lotus seed gathering": 1.4, "lotus seed harvest": 1.4,
            "lotus seed crop": 1.4, "lotus seed yield": 1.4, "lotus seed production": 1.4,
            "lotus seed supply": 1.4, "lotus seed stock": 1.4, "lotus seed inventory": 1.4,
            "lotus seed reserve": 1.4, "lotus seed store": 1.4, "lotus seed cache": 1.4,
            "lotus seed hoard": 1.4, "lotus seed stash": 1.4, "lotus seed collection": 1.4,
            "lotus seed gathering": 1.4, "lotus seed harvest": 1.4, "lotus seed crop": 1.4,
            "lotus seed yield": 1.4, "lotus seed production": 1.4, "lotus seed supply": 1.4,
            "lotus seed stock": 1.4, "lotus seed inventory": 1.4, "lotus seed reserve": 1.4,
            "lotus seed store": 1.4, "lotus seed cache": 1.4, "lotus seed hoard": 1.4,
            "lotus seed stash": 1.4, "lotus seed collection": 1.4, "lotus seed gathering": 1.4,
            "lotus seed harvest": 1.4, "lotus seed crop": 1.4, "lotus seed yield": 1.4,
            "lotus seed production": 1.4, "lotus seed supply": 1.4, "lotus seed stock": 1.4,
            "lotus seed inventory": 1.4, "lotus seed reserve": 1.4, "lotus seed store": 1.4,
            "lotus seed cache": 1.4, "lotus seed hoard": 1.4, "lotus seed stash": 1.4
         }
         
        # Basic calorie database for validation (calories per 100g)
        self.calorie_database = {
            # Proteins
            "chicken": 165, "beef": 250, "pork": 242, "salmon": 208, "tuna": 144,
            "eggs": 155, "bacon": 541, "ham": 145, "cheese": 402, "milk": 42,
            
            # Carbs
            "rice": 130, "pasta": 131, "bread": 265, "toast": 265, "pizza": 266,
            "potato": 77, "corn": 86, "oats": 389, "quinoa": 120,
            
            # Vegetables
            "salad": 20, "broccoli": 34, "spinach": 23, "tomato": 18, "cucumber": 16,
            "lettuce": 15, "carrot": 41, "onion": 40, "mushrooms": 22,
            
            # Fruits
            "apple": 52, "banana": 89, "orange": 47, "strawberry": 32,
            
            # Legumes & Nuts
            "beans": 127, "lentils": 116, "chickpeas": 164, "almonds": 579,
            "peanuts": 567, "walnuts": 654, "cashews": 553,
            
            # Default for unknown foods (raised for more realistic average density)
            "default": 180
        }
        
        # High-confidence food keywords that should trigger detection
        self.food_keywords = {
            "meat": ["chicken", "beef", "pork", "lamb", "turkey", "duck", "steak", "meat", "bacon", "ham", "sausage"],
            "fish": ["salmon", "tuna", "cod", "tilapia", "fish", "seafood", "shrimp", "crab", "lobster"],
            "dairy": ["milk", "cheese", "yogurt", "cream", "butter", "cottage cheese", "greek yogurt"],
            "eggs": ["egg", "eggs", "omelet", "scrambled", "fried egg", "boiled egg"],
            "legumes": ["beans", "lentils", "chickpeas", "peas", "soy", "tofu"],
            "nuts": ["almonds", "walnuts", "peanuts", "cashews", "nuts", "pistachio"],
            "grains": ["rice", "bread", "pasta", "oats", "quinoa", "cereal", "noodles", "spaghetti"],
            "vegetables": ["broccoli", "spinach", "carrot", "potato", "tomato", "onion", "pepper", "lettuce"],
            "fruits": ["apple", "banana", "orange", "berry", "fruit", "grape", "strawberry", "blueberry"]
        }
        
        # Non-food items that should be filtered out
        self.non_food_keywords = {
            "containers": ["plate", "bowl", "dish", "cup", "glass", "mug", "container", "plateware"],
            "utensils": ["fork", "knife", "spoon", "chopstick", "chopsticks", "utensil", "cutlery"],
            "furniture": ["table", "chair", "counter", "surface", "desk", "furniture"],
            "appliances": ["microwave", "oven", "stove", "refrigerator", "appliance", "kitchen"],
            "materials": ["ceramic", "plastic", "metal", "wood", "glass", "fabric", "paper"],
            "generic": ["object", "item", "thing", "stuff", "material", "product", "goods"],
            "actions": ["eating", "cooking", "serving", "preparing", "dining", "meal time"],
            "places": ["restaurant", "kitchen", "dining room", "cafeteria", "food court"]
        }

        # Broad category mappings for consensus and conflict checks
        self.food_categories = {
            "meat": {"chicken", "beef", "pork", "lamb", "turkey", "ham", "bacon", "sausage", "pepperoni", "salami"},
            "fish": {"salmon", "tuna", "cod", "tilapia", "shrimp", "crab", "lobster", "fish"},
            "dairy": {"cheese", "milk", "yogurt", "cream", "butter"},
            "eggs": {"egg", "eggs", "omelet"},
            "carb": {"rice", "pasta", "bread", "toast", "pizza", "quinoa", "oats"},
            "vegetable": {"vegetables", "salad", "broccoli", "spinach", "tomato", "cucumber", "lettuce", "onion", "carrot", "mushrooms"},
            "fruit": {"apple", "banana", "orange", "strawberry", "berry", "grape"}
        }

    def _is_food_item(self, label: str) -> bool:
        """Validate if a detected label is actually a food item"""
        label_lower = label.lower().strip()
        
        # Check if it's explicitly a non-food item
        for category, keywords in self.non_food_keywords.items():
            if any(keyword in label_lower for keyword in keywords):
                return False
        
        # Check if it contains food keywords
        for category, keywords in self.food_keywords.items():
            if any(keyword in label_lower for keyword in keywords):
                return True
        
        # Check if it's in our protein database (direct food match)
        if label_lower in self.protein_database:
            return True
        
        # Check for common food patterns
        food_patterns = [
            "food", "meal", "dish", "cuisine", "recipe", "ingredient",
            "breakfast", "lunch", "dinner", "snack", "dessert",
            "soup", "salad", "sandwich", "pizza", "burger", "pasta",
            "cake", "pie", "cookie", "bread", "roll", "muffin"
        ]
        
        if any(pattern in label_lower for pattern in food_patterns):
            return True
        
        # If it's a single word and not obviously non-food, be more lenient
        if len(label_lower.split()) == 1 and len(label_lower) > 3:
            # Avoid obvious non-food single words
            non_food_single_words = ["plate", "bowl", "cup", "glass", "fork", "knife", "spoon", "table", "chair"]
            if label_lower not in non_food_single_words:
                return True
        
        return False

    def detect_food_in_image(self, image_path: str) -> Dict:
        """Detect food items in an image using Google Vision API with multi-item meal support"""
        if not self.client:
            raise RuntimeError("Google Vision API client not initialized")
        
        try:
            print(f"[FD] {FD_VERSION}")
            print(f"🔍 Analyzing image with Google Cloud Vision API: {image_path}")
            
            # Read the image file
            with open(image_path, 'rb') as image_file:
                content = image_file.read()
            
            image = vision.Image(content=content)
            
            # Perform label detection
            response = self.client.label_detection(image=image)
            labels = response.label_annotations
            
            # Perform web detection
            response_web = self.client.web_detection(image=image)
            web_detection = response_web.web_detection

            # Perform object localization to find distinct regions (helps multi-item plates)
            localized_objects = []
            try:
                obj_resp = self.client.object_localization(image=image)
                localized_objects = getattr(obj_resp, 'localized_object_annotations', []) or []
                print(f"🧩 Localized {len(localized_objects)} objects")
            except Exception as _e:
                print("⚠️ Object localization unavailable; continuing without region crops")

            # Optionally run per-crop label detection on top N likely food regions
            crop_food_candidates: List[str] = []
            crop_confidence: Dict[str, float] = {}
            if localized_objects:
                try:
                    crop_limit = 4
                    if _PIL_AVAILABLE:
                        base_img = Image.open(image_path).convert('RGB')
                        w, h = base_img.size
                        foodish_names = {"Food", "Dish", "Bowl", "Plate", "Fruit", "Vegetable", "Sandwich", "Bread", "Pizza", "Cake"}
                        # Sort by score desc, take top regions
                        top_objs = sorted(localized_objects, key=lambda o: getattr(o, 'score', 0.0), reverse=True)[:10]
                        kept = 0
                        for obj in top_objs:
                            if kept >= crop_limit:
                                break
                            name = getattr(obj, 'name', '')
                            score = float(getattr(obj, 'score', 0.0) or 0.0)
                            if name and (name in foodish_names or score >= 0.60):
                                # Compute crop box from normalized vertices
                                vertices = obj.bounding_poly.normalized_vertices
                                xs = [v.x for v in vertices]
                                ys = [v.y for v in vertices]
                                left = max(0, int(min(xs) * w))
                                top = max(0, int(min(ys) * h))
                                right = min(w, int(max(xs) * w))
                                bottom = min(h, int(max(ys) * h))
                                if right - left < 20 or bottom - top < 20:
                                    continue
                                crop = base_img.crop((left, top, right, bottom))
                                # Encode crop to bytes
                                from io import BytesIO
                                buf = BytesIO()
                                crop.save(buf, format='JPEG', quality=90)
                                crop_bytes = buf.getvalue()
                                crop_image = vision.Image(content=crop_bytes)
                                crop_labels = self.client.label_detection(image=crop_image).label_annotations or []
                                # Collect candidates from crop labels with slightly lenient thresholds
                                for cl in crop_labels:
                                    cl_desc = cl.description.lower().strip()
                                    cl_conf = float(cl.score or 0.0)
                                    if cl_conf >= 0.50:
                                        items = self._extract_food_with_improved_matching(cl_desc, cl_conf, crop_food_candidates)
                                        for it in items:
                                            if it not in crop_food_candidates:
                                                crop_food_candidates.append(it)
                                                crop_confidence[it] = max(crop_confidence.get(it, 0.0), cl_conf)
                                kept += 1
                        if crop_food_candidates:
                            print(f"🧩 Crops yielded candidates: {crop_food_candidates}")
                    else:
                        print("⚠️ Pillow not available; skipping crop-based refinement")
                except Exception as _e:
                    print(f"⚠️ Crop-based refinement failed: {_e}")

            # Process detected labels with IMPROVED confidence thresholds for better accuracy
            detected_foods = []
            confidence_scores = {}
            
            print(f"🏷️  Detected {len(labels)} labels from Vision API:")
            # Process each label from Google Vision API
            for label in labels:
                label_desc = label.description.lower().strip()
                confidence = label.score
                
                # ENHANCED confidence threshold system - more sensitive to food items
                if confidence >= 0.75:  # Very high confidence - process all
                    print(f"   🔍 Very high confidence: {label_desc} (confidence: {confidence:.3f})")
                    if self._is_food_item(label_desc):
                        food_items = self._extract_food_with_improved_matching(label_desc, confidence, detected_foods)
                        for food in food_items:
                            if food not in detected_foods:
                                detected_foods.append(food)
                                confidence_scores[food] = confidence
                                print(f"      ✅ Added: {food}")
                    else:
                        print(f"      ❌ Filtered out non-food: {label_desc}")
                elif confidence >= 0.65:  # High confidence - process with validation
                    print(f"   🔍 High confidence: {label_desc} (confidence: {confidence:.3f})")
                    if self._is_food_item(label_desc):
                        food_items = self._extract_food_with_improved_matching(label_desc, confidence, detected_foods)
                        for food in food_items:
                            if food not in detected_foods:
                                detected_foods.append(food)
                                confidence_scores[food] = confidence
                                print(f"      ✅ Added: {food}")
                    else:
                        print(f"      ❌ Filtered out non-food: {label_desc}")
                elif confidence >= 0.55:  # Medium confidence - strict validation
                    print(f"   🔍 Medium confidence: {label_desc} (confidence: {confidence:.3f})")
                    # Only process if it's clearly food and contains specific food keywords (comprehensive list)
                    if self._is_food_item(label_desc) and any(keyword in label_desc for keyword in ["chicken", "beef", "pork", "salmon", "rice", "pasta", "bread", "egg", "cheese", "fish", "meat", "vegetable", "salad", "fruit", "soup", "sandwich", "pizza", "burger", "noodle", "grain", "dairy", "sausage", "bacon", "toast", "beans", "mushrooms", "tomato", "breakfast", "hash browns", "black pudding", "white pudding", "potato", "onion", "carrot", "broccoli", "spinach", "lettuce", "cucumber", "pepper", "corn", "peas", "lentils", "quinoa", "oats", "cereal", "yogurt", "milk", "butter", "oil", "sauce", "gravy", "herbs", "spices", "garlic", "ginger", "curry", "stir", "fry", "roast", "grill", "bake", "steam", "boil"]):
                        food_items = self._extract_food_with_improved_matching(label_desc, confidence, detected_foods)
                        for food in food_items:
                            if food not in detected_foods:
                                detected_foods.append(food)
                                confidence_scores[food] = confidence
                                print(f"      ✅ Added: {food}")
                    else:
                        print(f"      ❌ Filtered out unclear/non-food: {label_desc}")
                elif confidence >= 0.50:  # Low confidence - very strict validation
                    print(f"   🔍 Low confidence: {label_desc} (confidence: {confidence:.3f})")
                    # Only process if it's very clearly food with high-confidence keywords (comprehensive list)
                    if self._is_food_item(label_desc) and any(keyword in label_desc for keyword in ["chicken", "beef", "pork", "salmon", "rice", "pasta", "bread", "egg", "cheese", "fish", "meat", "sausage", "bacon", "toast", "beans", "mushrooms", "tomato", "hash browns", "potato", "vegetable", "salad", "soup", "sandwich", "pizza", "burger", "noodle", "grain", "dairy", "fruit", "sauce", "gravy", "herbs", "spices", "curry", "stir", "fry", "roast", "grill", "bake"]):
                        food_items = self._extract_food_with_improved_matching(label_desc, confidence, detected_foods)
                        for food in food_items:
                            if food not in detected_foods:
                                detected_foods.append(food)
                                confidence_scores[food] = confidence
                                print(f"      ✅ Added: {food}")
                    else:
                        print(f"      ❌ Filtered out low confidence: {label_desc}")
                else:
                    print(f"   ❌ Skipped: {label_desc} (confidence: {confidence:.3f} < 0.50)")
            
            # Process web detection results with IMPROVED thresholds for better multi-item detection
            if web_detection.web_entities:
                print(f"🌐 Processing {len(web_detection.web_entities)} web entities:")
                for entity in web_detection.web_entities:
                    entity_desc = entity.description.lower().strip()
                    confidence = entity.score
                    
                    # IMPROVED thresholds for web entities with food validation
                    if confidence >= 0.70:  # Very high confidence web entities
                        print(f"   🌐 Very high confidence web entity: {entity_desc} (score: {confidence:.3f})")
                        if self._is_food_item(entity_desc):
                            food_items = self._extract_food_with_improved_matching(entity_desc, confidence, detected_foods)
                            for food in food_items:
                                if food not in detected_foods:
                                    detected_foods.append(food)
                                    confidence_scores[food] = confidence
                                    print(f"      ✅ Added from web: {food}")
                        else:
                            print(f"      ❌ Filtered out non-food web entity: {entity_desc}")
                    elif confidence >= 0.60:  # High confidence web entities
                        print(f"   🌐 High confidence web entity: {entity_desc} (score: {confidence:.3f})")
                        if self._is_food_item(entity_desc):
                            food_items = self._extract_food_with_improved_matching(entity_desc, confidence, detected_foods)
                            for food in food_items:
                                if food not in detected_foods:
                                    detected_foods.append(food)
                                    confidence_scores[food] = confidence
                                    print(f"      ✅ Added from web: {food}")
                        else:
                            print(f"      ❌ Filtered out non-food web entity: {entity_desc}")
                    elif confidence >= 0.55:  # Medium confidence web entities
                        print(f"   🌐 Medium confidence web entity: {entity_desc} (score: {confidence:.3f})")
                        # Only process if it's clearly food and contains specific food keywords (comprehensive list)
                        if self._is_food_item(entity_desc) and any(keyword in entity_desc for keyword in ["chicken", "beef", "pork", "salmon", "rice", "pasta", "bread", "egg", "cheese", "fish", "meat", "vegetable", "salad", "fruit", "soup", "sandwich", "pizza", "burger", "sausage", "bacon", "toast", "beans", "mushrooms", "tomato", "breakfast", "hash browns", "black pudding", "white pudding", "english breakfast", "full breakfast", "potato", "onion", "carrot", "broccoli", "spinach", "lettuce", "cucumber", "pepper", "corn", "peas", "lentils", "quinoa", "oats", "cereal", "yogurt", "milk", "butter", "oil", "sauce", "gravy", "herbs", "spices", "garlic", "ginger", "curry", "stir", "fry", "roast", "grill", "bake", "steam", "boil", "noodle", "grain", "dairy"]):
                            food_items = self._extract_food_with_improved_matching(entity_desc, confidence, detected_foods)
                            for food in food_items:
                                if food not in detected_foods:
                                    detected_foods.append(food)
                                    confidence_scores[food] = confidence
                                    print(f"      ✅ Added from web: {food}")
                        else:
                            print(f"      ❌ Filtered out unclear/non-food web entity: {entity_desc}")
                    elif confidence >= 0.50:  # Low confidence web entities
                        print(f"   🌐 Low confidence web entity: {entity_desc} (score: {confidence:.3f})")
                        # Only process if it's very clearly food with high-confidence keywords
                        if self._is_food_item(entity_desc) and any(keyword in entity_desc for keyword in ["chicken", "beef", "pork", "salmon", "rice", "pasta", "bread", "egg", "cheese", "fish", "meat"]):
                            food_items = self._extract_food_with_improved_matching(entity_desc, confidence, detected_foods)
                            for food in food_items:
                                if food not in detected_foods:
                                    detected_foods.append(food)
                                    confidence_scores[food] = confidence
                                    print(f"      ✅ Added from low confidence web: {food}")
                        else:
                            print(f"      ❌ Filtered out low confidence web entity: {entity_desc}")
                    else:
                        print(f"   ❌ Skipped web entity: {entity_desc} (score: {confidence:.3f} < 0.50)")

            # Merge crop-based candidates with main detections (boost consensus)
            if crop_food_candidates:
                for it in crop_food_candidates:
                    if it not in detected_foods:
                        detected_foods.append(it)
                    # Boost confidence if present in both sources
                    confidence_scores[it] = max(confidence_scores.get(it, 0.0), crop_confidence.get(it, 0.55))
                print(f"🧩 After crop fusion, candidates: {detected_foods}")
            
            # Category consensus filter to prevent outlier misclassifications
            detected_foods, confidence_scores = self._apply_category_consensus(detected_foods, confidence_scores)

            # Enhanced confidence-based filtering with IMPROVED thresholds
            print(f"🎯 Pre-filtering: {len(detected_foods)} foods detected")
            filtered_foods = self._enhanced_confidence_filtering(detected_foods, confidence_scores)
            print(f"🎯 Post-filtering: {len(filtered_foods)} foods remaining")
            
            # Apply improved filtering for multi-item meals
            filtered_foods = self._filter_and_prioritize_foods(filtered_foods, confidence_scores)

            # Canonicalize outputs to database-friendly items
            filtered_foods = self._canonicalize_food_list(filtered_foods)

            # If a strong pizza signal exists, correct cheese-only cases
            try:
                if web_detection and getattr(web_detection, 'web_entities', None):
                    wd = [getattr(e, 'description', '').lower() for e in web_detection.web_entities or []]
                    if 'pizza' in wd or any('pizza' in (d or '') for d in wd):
                        if 'pizza' not in filtered_foods and 'cheese' in filtered_foods:
                            print("   🍕 Detected pizza context in web entities; mapping cheese → pizza")
                            filtered_foods = [f for f in filtered_foods if f != 'cheese'] + ['pizza']
            except Exception:
                pass

            # Estimate portions directly from image using object localization area and confidences
            portions_g, total_estimated = self._estimate_portions_from_image(localized_objects, filtered_foods, confidence_scores, image_path)
            
            if not filtered_foods:
                print("⚠️  No food items detected in image")
                return {
                    "foods": [],
                    "protein_per_100g": 0,
                    "confidence_scores": {},
                    "detection_method": "google_vision_api"
                }
            
            # Calculate total protein content using estimated portions when available
            if portions_g:
                total_protein = self._calculate_protein_from_portions(filtered_foods, portions_g)
            else:
                total_protein = self.calculate_protein_content(filtered_foods)
            
            print(f"🎯 Successfully detected {len(filtered_foods)} food items:")
            for food in filtered_foods:
                conf = confidence_scores.get(food, 0.5)
                protein = self.protein_database.get(food, 5.0)
                print(f"   - {food} (confidence: {conf:.3f}, protein: {protein}g/100g)")
            
            if len(filtered_foods) == 1:
                print(f"📊 Single food item: {filtered_foods[0]}, 250g total")
            else:
                grams_per_item = 250.0 / len(filtered_foods)
                print(f"📊 Multiple food items: {len(filtered_foods)} items, {grams_per_item:.0f}g each (250g total)")
            print(f"📊 Total protein content: {total_protein:.1f}g")
            
            return {
                "foods": filtered_foods,
                "protein_per_100g": total_protein,  # Now represents protein for 250g total food
                "confidence_scores": {k: v for k, v in confidence_scores.items() if k in filtered_foods},
                "portions_g": portions_g,
                "estimated_total_g": total_estimated,
                "detection_method": "google_vision_api"
            }
            
        except Exception as e:
            print(f"❌ Google Vision API error: {e}")
            raise e

    def _extract_food_with_improved_matching(self, label: str, confidence: float, already_detected_foods: List[str] = None) -> List[str]:
        """Extract food items from Vision API labels with improved matching for multi-item meals"""
        foods = []
        if already_detected_foods is None:
            already_detected_foods = []
        
        # Clean and normalize the label
        label = label.lower().strip()
        
        # Handle complex dishes FIRST (before direct matches)
        complex_dish_mappings = {
            "bolognese": ["pasta", "beef"],  # bolognese is pasta with beef sauce
            "bolognese sauce": ["pasta", "beef"],
            "meat sauce": ["pasta", "beef"],
            "beef sauce": ["pasta", "beef"],
            "beef spaghetti": ["pasta", "beef"],
            "beef pasta": ["pasta", "beef"],
            "chicken sauce": ["pasta", "chicken"],
            "chicken pasta": ["pasta", "chicken"],
            "pork sauce": ["pasta", "pork"],
            "lamb sauce": ["pasta", "lamb"],
            "turkey sauce": ["pasta", "turkey"],
            "spaghetti bolognese": ["pasta", "beef"],
            "pasta bolognese": ["pasta", "beef"],
            # IMPROVED: Add more complex dish patterns
            "carbonara": ["pasta", "bacon", "eggs"],
            "alfredo": ["pasta", "cheese", "cream"],
            "marinara": ["pasta", "tomato", "herbs"],
            "pesto": ["pasta", "basil", "pine nuts", "cheese"],
            "curry": ["rice", "spices", "vegetables"],
            "stir fry": ["rice", "vegetables", "protein"],
            "fried rice": ["rice", "vegetables", "eggs"],
            "noodles": ["pasta", "vegetables"],
            "ramen": ["noodles", "broth", "vegetables"],
            "sushi": ["rice", "fish", "vegetables"],
            "burrito": ["wrap", "beans", "rice", "meat"],
            "taco": ["tortilla", "meat", "vegetables"],
            "quesadilla": ["tortilla", "cheese", "vegetables"],
            "enchilada": ["tortilla", "cheese", "sauce"],
            "fajita": ["tortilla", "meat", "vegetables"],
            "gyro": ["wrap", "meat", "vegetables"],
            "kebab": ["meat", "vegetables", "bread"],
            "shawarma": ["wrap", "meat", "vegetables"],
            "falafel": ["chickpeas", "vegetables", "bread"],
            "hummus": ["chickpeas", "tahini", "olive oil"],
            "guacamole": ["avocado", "tomato", "onion"],
            "salsa": ["tomato", "onion", "peppers"],
            "dip": ["cheese", "vegetables"],
            "spread": ["cheese", "vegetables"],
            "salad dressing": ["oil", "vinegar", "herbs"],
            "gravy": ["meat juices", "flour", "broth"],
            "sauce": ["tomato", "herbs", "spices"],
            "soup": ["broth", "vegetables", "meat"],
            "stew": ["meat", "vegetables", "broth"],
            "casserole": ["meat", "vegetables", "cheese"],
            "lasagna": ["pasta", "cheese", "meat", "sauce"],
            "pizza": ["dough", "cheese", "sauce"],
            "sandwich": ["bread", "meat", "vegetables"],
            "burger": ["bun", "meat", "vegetables"],
            "hot dog": ["bun", "sausage", "vegetables"],
            "sub": ["bread", "meat", "vegetables"],
            "wrap": ["tortilla", "meat", "vegetables"],
            "panini": ["bread", "cheese", "meat"],
            "toast": ["bread", "butter", "jam"],
            "french toast": ["bread", "eggs", "milk"],
            "pancakes": ["flour", "eggs", "milk"],
            "waffles": ["flour", "eggs", "milk"],
            "crepes": ["flour", "eggs", "milk"],
            "muffin": ["flour", "eggs", "sugar"],
            "scone": ["flour", "butter", "sugar"],
            "biscuit": ["flour", "butter", "milk"],
            "croissant": ["flour", "butter", "yeast"],
            "danish": ["flour", "butter", "sugar"],
            "donut": ["flour", "sugar", "yeast"],
            "bagel": ["flour", "yeast", "salt"],
            "english muffin": ["flour", "yeast", "milk"],
            "cereal": ["grains", "sugar", "milk"],
            "granola": ["oats", "nuts", "honey"],
            "muesli": ["oats", "nuts", "dried fruit"],
            "oatmeal": ["oats", "milk", "sugar"],
            "porridge": ["oats", "milk", "sugar"],
            "cream of wheat": ["wheat", "milk", "sugar"],
            "farina": ["wheat", "milk", "sugar"],
            "yogurt": ["milk", "bacteria", "fruit"],
            "greek yogurt": ["milk", "bacteria", "fruit"],
            "cottage cheese": ["milk", "bacteria", "salt"],
            "smoothie": ["fruit", "milk", "yogurt"],
            "protein shake": ["protein powder", "milk", "fruit"],
            "meal replacement": ["protein", "carbohydrates", "vitamins"],
            "energy bar": ["nuts", "dried fruit", "honey"],
            "protein bar": ["protein powder", "nuts", "honey"],
            "granola bar": ["oats", "nuts", "honey"],
            "trail mix": ["nuts", "dried fruit", "chocolate"],
            "nuts": ["protein", "healthy fats", "fiber"],
            "seeds": ["protein", "healthy fats", "fiber"],
            "dried fruit": ["fruit", "sugar", "fiber"],
            "jerky": ["meat", "salt", "spices"],
            "beef jerky": ["beef", "salt", "spices"],
            "turkey jerky": ["turkey", "salt", "spices"],
            "pepperoni": ["pork", "beef", "spices"],
            "salami": ["pork", "beef", "spices"],
            "prosciutto": ["pork", "salt", "spices"],
            "ham": ["pork", "salt", "spices"],
            "bacon": ["pork", "salt", "smoke"],
            "sausage": ["pork", "beef", "spices"],
            "chorizo": ["pork", "spices", "paprika"],
            "pepperoni": ["pork", "beef", "spices"],
            "mortadella": ["pork", "beef", "spices"],
            "bologna": ["pork", "beef", "spices"],
            "pastrami": ["beef", "salt", "spices"],
            "corned beef": ["beef", "salt", "spices"],
            "roast beef": ["beef", "salt", "spices"],
            # Additional complex dishes for better detection
            "chicken parmesan": ["chicken", "cheese", "pasta"],
            "chicken alfredo": ["chicken", "pasta", "cheese"],
            "beef stroganoff": ["beef", "pasta", "cream"],
            "chicken teriyaki": ["chicken", "rice", "vegetables"],
            "beef and broccoli": ["beef", "broccoli", "rice"],
            "chicken fried rice": ["chicken", "rice", "eggs", "vegetables"],
            "beef fried rice": ["beef", "rice", "eggs", "vegetables"],
            "shrimp fried rice": ["shrimp", "rice", "eggs", "vegetables"],
            "chicken noodle soup": ["chicken", "noodles", "vegetables"],
            "beef stew": ["beef", "vegetables", "potatoes"],
            "chicken pot pie": ["chicken", "vegetables", "pastry"],
            "fish and chips": ["fish", "potatoes", "batter"],
            "chicken wings": ["chicken", "sauce", "spices"],
            "buffalo wings": ["chicken", "hot sauce", "butter"],
            "chicken tenders": ["chicken", "breading", "oil"],
            "chicken nuggets": ["chicken", "breading", "oil"],
            "meatballs": ["meat", "breadcrumbs", "eggs"],
            "chicken meatballs": ["chicken", "breadcrumbs", "eggs"],
            "beef meatballs": ["beef", "breadcrumbs", "eggs"],
            "turkey meatballs": ["turkey", "breadcrumbs", "eggs"],
            "chicken salad": ["chicken", "vegetables", "dressing"],
            "tuna salad": ["tuna", "vegetables", "dressing"],
            "egg salad": ["eggs", "vegetables", "dressing"],
            "potato salad": ["potatoes", "vegetables", "dressing"],
            "mac and cheese": ["pasta", "cheese", "milk"],
            "chicken and rice": ["chicken", "rice", "vegetables"],
            "beef and rice": ["beef", "rice", "vegetables"],
            "pork and rice": ["pork", "rice", "vegetables"],
            "salmon and rice": ["salmon", "rice", "vegetables"],
            "chicken and vegetables": ["chicken", "vegetables"],
            "beef and vegetables": ["beef", "vegetables"],
            "pork and vegetables": ["pork", "vegetables"],
            "fish and vegetables": ["fish", "vegetables"],
            "chicken and potatoes": ["chicken", "potatoes"],
            "beef and potatoes": ["beef", "potatoes"],
            "pork and potatoes": ["pork", "potatoes"],
            "fish and potatoes": ["fish", "potatoes"],
            "turkey": ["turkey", "salt", "spices"],
            "chicken": ["chicken", "salt", "spices"],
            "duck": ["duck", "salt", "spices"],
            "goose": ["goose", "salt", "spices"],
            "quail": ["quail", "salt", "spices"],
            "pheasant": ["pheasant", "salt", "spices"],
            "partridge": ["partridge", "salt", "spices"],
            "venison": ["venison", "salt", "spices"],
            "bison": ["bison", "salt", "spices"],
            "elk": ["elk", "salt", "spices"],
            "rabbit": ["rabbit", "salt", "spices"],
            "lamb": ["lamb", "salt", "spices"],
            "veal": ["veal", "salt", "spices"],
            "goat": ["goat", "salt", "spices"],
            "wild boar": ["wild boar", "salt", "spices"],
            "antelope": ["antelope", "salt", "spices"],
            "moose": ["moose", "salt", "spices"],
            "bear": ["bear", "salt", "spices"],
            "alligator": ["alligator", "salt", "spices"],
            "ostrich": ["ostrich", "salt", "spices"],
            "emu": ["emu", "salt", "spices"],
            "kangaroo": ["kangaroo", "salt", "spices"],
            "camel": ["camel", "salt", "spices"],
            "horse": ["horse", "salt", "spices"],
            "donkey": ["donkey", "salt", "spices"],
            "mule": ["mule", "salt", "spices"],
            "buffalo": ["buffalo", "salt", "spices"],
            "yak": ["yak", "salt", "spices"],
            "llama": ["llama", "salt", "spices"],
            "alpaca": ["alpaca", "salt", "spices"],
            "guinea pig": ["guinea pig", "salt", "spices"],
            "frog": ["frog", "salt", "spices"],
            "snail": ["snail", "salt", "spices"],
            "escargot": ["snail", "salt", "spices"],
            "caviar": ["fish eggs", "salt", "spices"],
            "roe": ["fish eggs", "salt", "spices"],
            "fish eggs": ["fish eggs", "salt", "spices"],
            "anchovy": ["anchovy", "salt", "spices"],
            "sardine": ["sardine", "salt", "spices"],
            "herring": ["herring", "salt", "spices"],
            "mackerel": ["mackerel", "salt", "spices"],
            "bluefish": ["bluefish", "salt", "spices"],
            "striped bass": ["striped bass", "salt", "spices"],
            "black sea bass": ["black sea bass", "salt", "spices"],
            "red snapper": ["red snapper", "salt", "spices"],
            "grouper": ["grouper", "salt", "spices"],
            "sea bass": ["sea bass", "salt", "spices"],
            "bass": ["bass", "salt", "spices"],
            "perch": ["perch", "salt", "spices"],
            "walleye": ["walleye", "salt", "spices"],
            "pike": ["pike", "salt", "spices"],
            "pickerel": ["pickerel", "salt", "spices"],
            "muskellunge": ["muskellunge", "salt", "spices"],
            "northern pike": ["northern pike", "salt", "spices"],
            "chain pickerel": ["chain pickerel", "salt", "spices"],
            "grass pickerel": ["grass pickerel", "salt", "spices"],
            "redfin pickerel": ["redfin pickerel", "salt", "spices"],
            "american pickerel": ["american pickerel", "salt", "spices"],
            "european pike": ["european pike", "salt", "spices"],
            "southern pike": ["southern pike", "salt", "spices"],
            "western pike": ["western pike", "salt", "spices"],
            "eastern pike": ["eastern pike", "salt", "spices"],
            "central pike": ["central pike", "salt", "spices"],
            "north american pike": ["north american pike", "salt", "spices"],
            "eurasian pike": ["eurasian pike", "salt", "spices"],
            "amur pike": ["amur pike", "salt", "spices"],
            "aquitanian pike": ["aquitanian pike", "salt", "spices"]
        }
        
        # Check for complex dish descriptions first
        complex_dish_found = False
        for dish_desc, components in complex_dish_mappings.items():
            if dish_desc in label:
                for component in components:
                    if component not in foods:
                        foods.append(component)
                complex_dish_found = True
                break  # Only use the first matching complex dish
        
        # Direct exact matches - highest priority (but skip if we found a complex dish)
        if label in self.protein_database and not complex_dish_found:
            foods.append(label)
            # Don't return immediately - continue processing other labels for multi-item meals
        
        # Handle complex meal descriptions (e.g., "beef spaghetti", "chicken rice", "salad vegetables")
        # Split by common separators and check each part
        separators = [' ', ',', ' and ', ' with ', ' in ', ' on ', ' topped with ', ' served with ']
        for separator in separators:
            if separator in label:
                parts = [part.strip() for part in label.split(separator) if part.strip()]
                for part in parts:
                    if part in self.protein_database and part not in foods:
                        foods.append(part)
        
        # Handle specific complex dish patterns
        complex_dish_patterns = [
            ("beef spaghetti", ["beef", "pasta"]),
            ("beef pasta", ["beef", "pasta"]),
            ("chicken rice", ["chicken", "rice"]),
            ("chicken pasta", ["chicken", "pasta"]),
            ("salad vegetables", ["salad", "vegetables"]),
            ("fish vegetables", ["fish", "vegetables"]),
            ("pork rice", ["pork", "rice"]),
            ("lamb rice", ["lamb", "rice"]),
            ("turkey rice", ["turkey", "rice"]),
            ("curry rice", ["curry", "rice"]),
            ("curry chicken", ["curry", "chicken"]),
            ("curry beef", ["curry", "beef"]),
            ("sushi rice", ["sushi", "rice"]),
            ("pizza pepperoni", ["pizza", "pepperoni"]),
            ("pizza cheese", ["pizza", "cheese"]),
            ("wrap chicken", ["wrap", "chicken"]),
            ("wrap beef", ["wrap", "beef"]),
            ("sandwich chicken", ["sandwich", "chicken"]),
            ("sandwich beef", ["sandwich", "beef"]),
            # IMPROVED: Add more patterns
            ("pasta carbonara", ["pasta", "bacon", "eggs"]),
            ("pasta alfredo", ["pasta", "cheese", "cream"]),
            ("pasta marinara", ["pasta", "tomato", "herbs"]),
            ("pasta pesto", ["pasta", "basil", "pine nuts"]),
            ("rice curry", ["rice", "curry", "vegetables"]),
            ("rice stir fry", ["rice", "vegetables", "protein"]),
            ("rice fried", ["rice", "vegetables", "eggs"]),
            ("noodles ramen", ["noodles", "broth", "vegetables"]),
            ("noodles stir fry", ["noodles", "vegetables", "protein"]),
            ("sushi roll", ["sushi", "rice", "fish"]),
            ("burrito bowl", ["rice", "beans", "meat", "vegetables"]),
            ("taco salad", ["lettuce", "meat", "vegetables", "cheese"]),
            ("quesadilla chicken", ["tortilla", "chicken", "cheese"]),
            ("enchilada beef", ["tortilla", "beef", "cheese"]),
            ("fajita chicken", ["tortilla", "chicken", "vegetables"]),
            ("gyro lamb", ["wrap", "lamb", "vegetables"]),
            ("kebab chicken", ["chicken", "vegetables", "bread"]),
            ("shawarma chicken", ["wrap", "chicken", "vegetables"]),
            ("falafel wrap", ["chickpeas", "vegetables", "bread"]),
            ("hummus plate", ["chickpeas", "bread", "vegetables"]),
            ("guacamole chips", ["avocado", "tomato", "chips"]),
            ("salsa chips", ["tomato", "onion", "chips"]),
            ("dip vegetables", ["cheese", "vegetables"]),
            ("spread bread", ["cheese", "bread"]),
            ("salad dressing", ["oil", "vinegar", "herbs"]),
            ("gravy meat", ["meat juices", "flour", "broth"]),
            ("sauce pasta", ["tomato", "herbs", "spices"]),
            ("soup vegetables", ["broth", "vegetables", "meat"]),
            ("stew meat", ["meat", "vegetables", "broth"]),
            ("casserole cheese", ["meat", "vegetables", "cheese"]),
            ("lasagna meat", ["pasta", "cheese", "meat", "sauce"]),
            ("pizza cheese", ["dough", "cheese", "sauce"]),
            ("sandwich meat", ["bread", "meat", "vegetables"]),
            ("burger meat", ["bun", "meat", "vegetables"]),
            ("hot dog sausage", ["bun", "sausage", "vegetables"]),
            ("sub meat", ["bread", "meat", "vegetables"]),
            ("wrap meat", ["tortilla", "meat", "vegetables"]),
            ("panini cheese", ["bread", "cheese", "meat"]),
            ("toast butter", ["bread", "butter", "jam"]),
            ("french toast eggs", ["bread", "eggs", "milk"]),
            ("pancakes syrup", ["flour", "eggs", "milk", "syrup"]),
            ("waffles syrup", ["flour", "eggs", "milk", "syrup"]),
            ("crepes fruit", ["flour", "eggs", "milk", "fruit"]),
            ("muffin fruit", ["flour", "eggs", "sugar", "fruit"]),
            ("scone butter", ["flour", "butter", "sugar"]),
            ("biscuit butter", ["flour", "butter", "milk"]),
            ("croissant butter", ["flour", "butter", "yeast"]),
            ("danish fruit", ["flour", "butter", "sugar", "fruit"]),
            ("donut sugar", ["flour", "sugar", "yeast"]),
            ("bagel cream cheese", ["flour", "yeast", "cream cheese"]),
            ("english muffin butter", ["flour", "yeast", "milk", "butter"]),
            ("cereal milk", ["grains", "sugar", "milk"]),
            ("granola yogurt", ["oats", "nuts", "honey", "yogurt"]),
            ("muesli milk", ["oats", "nuts", "dried fruit", "milk"]),
            ("oatmeal fruit", ["oats", "milk", "sugar", "fruit"]),
            ("porridge fruit", ["oats", "milk", "sugar", "fruit"]),
            ("cream of wheat milk", ["wheat", "milk", "sugar"]),
            ("farina milk", ["wheat", "milk", "sugar"]),
            ("yogurt fruit", ["milk", "bacteria", "fruit"]),
            ("greek yogurt honey", ["milk", "bacteria", "honey"]),
            ("cottage cheese fruit", ["milk", "bacteria", "fruit"]),
            ("smoothie fruit", ["fruit", "milk", "yogurt"]),
            ("protein shake milk", ["protein powder", "milk", "fruit"]),
            ("meal replacement shake", ["protein", "carbohydrates", "vitamins"]),
            ("energy bar nuts", ["nuts", "dried fruit", "honey"]),
            ("protein bar nuts", ["protein powder", "nuts", "honey"]),
            ("granola bar nuts", ["oats", "nuts", "honey"]),
            ("trail mix nuts", ["nuts", "dried fruit", "chocolate"]),
            ("nuts fruit", ["nuts", "dried fruit"]),
            ("seeds fruit", ["seeds", "dried fruit"]),
            ("dried fruit nuts", ["dried fruit", "nuts"]),
            ("jerky meat", ["meat", "salt", "spices"]),
            ("beef jerky beef", ["beef", "salt", "spices"]),
            ("turkey jerky turkey", ["turkey", "salt", "spices"]),
            ("pepperoni pizza", ["pepperoni", "pizza", "cheese"]),
            ("salami sandwich", ["salami", "bread", "cheese"]),
            ("prosciutto bread", ["prosciutto", "bread", "cheese"]),
            ("ham sandwich", ["ham", "bread", "cheese"]),
            ("bacon eggs", ["bacon", "eggs"]),
            ("sausage bread", ["sausage", "bread"]),
            ("chorizo rice", ["chorizo", "rice", "vegetables"]),
            ("mortadella bread", ["mortadella", "bread", "cheese"]),
            ("bologna sandwich", ["bologna", "bread", "cheese"]),
            ("pastrami bread", ["pastrami", "bread", "cheese"]),
            ("corned beef cabbage", ["corned beef", "cabbage", "potato"]),
            ("roast beef sandwich", ["roast beef", "bread", "cheese"]),
            ("turkey sandwich", ["turkey", "bread", "cheese"]),
            ("chicken breast", ["chicken", "salt", "spices"]),
            ("duck orange", ["duck", "orange", "sauce"]),
            ("goose apple", ["goose", "apple", "sauce"]),
            ("quail grape", ["quail", "grape", "sauce"]),
            ("pheasant berry", ["pheasant", "berry", "sauce"]),
            ("partridge herb", ["partridge", "herb", "sauce"]),
            ("venison berry", ["venison", "berry", "sauce"]),
            ("bison berry", ["bison", "berry", "sauce"]),
            ("elk berry", ["elk", "berry", "sauce"]),
            ("rabbit herb", ["rabbit", "herb", "sauce"]),
            ("lamb mint", ["lamb", "mint", "sauce"]),
            ("veal herb", ["veal", "herb", "sauce"]),
            ("goat herb", ["goat", "herb", "sauce"]),
            ("wild boar berry", ["wild boar", "berry", "sauce"]),
            ("antelope berry", ["antelope", "berry", "sauce"]),
            ("moose berry", ["moose", "berry", "sauce"]),
            ("bear berry", ["bear", "berry", "sauce"]),
            ("alligator spice", ["alligator", "spice", "sauce"]),
            ("ostrich berry", ["ostrich", "berry", "sauce"]),
            ("emu berry", ["emu", "berry", "sauce"]),
            ("kangaroo berry", ["kangaroo", "berry", "sauce"]),
            ("camel spice", ["camel", "spice", "sauce"]),
            ("horse herb", ["horse", "herb", "sauce"]),
            ("donkey herb", ["donkey", "herb", "sauce"]),
            ("mule herb", ["mule", "herb", "sauce"]),
            ("buffalo berry", ["buffalo", "berry", "sauce"]),
            ("yak berry", ["yak", "berry", "sauce"]),
            ("llama herb", ["llama", "herb", "sauce"]),
            ("alpaca herb", ["alpaca", "herb", "sauce"]),
            ("guinea pig herb", ["guinea pig", "herb", "sauce"]),
            ("frog herb", ["frog", "herb", "sauce"]),
            ("snail herb", ["snail", "herb", "sauce"]),
            ("escargot herb", ["snail", "herb", "sauce"]),
            ("caviar bread", ["fish eggs", "bread", "butter"]),
            ("roe bread", ["fish eggs", "bread", "butter"]),
            ("fish eggs bread", ["fish eggs", "bread", "butter"]),
            ("anchovy pizza", ["anchovy", "pizza", "cheese"]),
            ("sardine bread", ["sardine", "bread", "cheese"]),
            ("herring bread", ["herring", "bread", "cheese"]),
            ("mackerel rice", ["mackerel", "rice", "vegetables"]),
            ("bluefish rice", ["bluefish", "rice", "vegetables"]),
            ("striped bass rice", ["striped bass", "rice", "vegetables"]),
            ("black sea bass rice", ["black sea bass", "rice", "vegetables"]),
            ("red snapper rice", ["red snapper", "rice", "vegetables"]),
            ("grouper rice", ["grouper", "rice", "vegetables"]),
            ("sea bass rice", ["sea bass", "rice", "vegetables"]),
            ("bass rice", ["bass", "rice", "vegetables"]),
            ("perch rice", ["perch", "rice", "vegetables"]),
            ("walleye rice", ["walleye", "rice", "vegetables"]),
            ("pike rice", ["pike", "rice", "vegetables"]),
            ("pickerel rice", ["pickerel", "rice", "vegetables"]),
            ("muskellunge rice", ["muskellunge", "rice", "vegetables"]),
            ("northern pike rice", ["northern pike", "rice", "vegetables"]),
            ("chain pickerel rice", ["chain pickerel", "rice", "vegetables"]),
            ("grass pickerel rice", ["grass pickerel", "rice", "vegetables"]),
            ("redfin pickerel rice", ["redfin pickerel", "rice", "vegetables"]),
            ("american pickerel rice", ["american pickerel", "rice", "vegetables"]),
            ("european pike rice", ["european pike", "rice", "vegetables"]),
            ("southern pike rice", ["southern pike", "rice", "vegetables"]),
            ("western pike rice", ["western pike", "rice", "vegetables"]),
            ("eastern pike rice", ["eastern pike", "rice", "vegetables"]),
            ("central pike rice", ["central pike", "rice", "vegetables"]),
            ("north american pike rice", ["north american pike", "rice", "vegetables"]),
            ("eurasian pike rice", ["eurasian pike", "rice", "vegetables"]),
            ("amur pike rice", ["amur pike", "rice", "vegetables"]),
            ("aquitanian pike rice", ["aquitanian pike", "rice", "vegetables"])
        ]
        
        for pattern, components in complex_dish_patterns:
            if pattern in label:
                for component in components:
                    if component not in foods:
                        foods.append(component)
        
        # Handle multi-item meal descriptions (e.g., "english breakfast", "full breakfast")
        meal_keywords = ["breakfast", "lunch", "dinner", "meal", "plate", "dish"]
        if any(keyword in label for keyword in meal_keywords):
            # For meal descriptions, extract individual components
            foods.extend(self._extract_meal_components(label, confidence))
            if foods:  # If we found meal components, return them
                return foods
        
        # IMPROVED: Special handling for breakfast items that suggest a full breakfast
        breakfast_indicators = ["sausage", "bacon", "eggs", "toast", "beans", "mushrooms", "tomato"]
        if any(indicator in label for indicator in breakfast_indicators):
            # If we detect a breakfast item, check if it might be part of a full breakfast
            if confidence >= 0.60:  # Medium confidence threshold
                # Add common breakfast companions
                breakfast_companions = []
                if "sausage" in label:
                    breakfast_companions = ["eggs", "bacon", "toast", "beans"]
                elif "bacon" in label:
                    breakfast_companions = ["eggs", "sausage", "toast"]
                elif "eggs" in label:
                    breakfast_companions = ["bacon", "sausage", "toast"]
                
                # Add companions if they're not already detected
                for companion in breakfast_companions:
                    if companion not in foods:
                        foods.append(companion)
                        print(f"🍳 Added breakfast companion: {companion} (detected with {label})")
        
        # ENHANCED: Comprehensive meal detection - detect ALL components for ANY meal type
        # Define common meal patterns and their typical components
        meal_patterns = {
            # Breakfast patterns
            "breakfast": ["eggs", "bacon", "sausage", "toast", "beans", "mushrooms", "tomato", "hash browns"],
            "english_breakfast": ["bacon", "eggs", "sausage", "toast", "beans", "mushrooms", "tomato", "hash browns"],
            "full_breakfast": ["bacon", "eggs", "sausage", "toast", "beans", "mushrooms", "tomato", "hash browns"],
            
            # Lunch patterns
            "lunch": ["chicken", "rice", "vegetables", "salad", "bread"],
            "sandwich": ["bread", "meat", "cheese", "vegetables", "sauce"],
            "salad": ["lettuce", "tomato", "cucumber", "cheese", "dressing"],
            
            # Dinner patterns
            "dinner": ["meat", "potato", "vegetables", "gravy", "bread"],
            "steak_dinner": ["beef", "potato", "vegetables", "gravy", "bread"],
            "chicken_dinner": ["chicken", "rice", "vegetables", "sauce", "bread"],
            
            # Pasta patterns
            "pasta": ["pasta", "sauce", "cheese", "meat", "vegetables"],
            "spaghetti": ["spaghetti", "tomato", "cheese", "meat", "herbs"],
            
            # Asian patterns
            "stir_fry": ["rice", "vegetables", "meat", "sauce", "noodles"],
            "curry": ["rice", "meat", "vegetables", "sauce", "bread"],
            
            # Generic patterns
            "meal": ["protein", "carbohydrate", "vegetables", "sauce"],
            "plate": ["protein", "carbohydrate", "vegetables", "sauce"]
        }
        
        # Check if the detected food suggests a larger meal pattern
        detected_meal_type = None
        for meal_type, components in meal_patterns.items():
            if any(component in label for component in components):
                detected_meal_type = meal_type
                break
        
        # If we detected a meal pattern, add ALL typical components
        if detected_meal_type and confidence >= 0.50:
            typical_components = meal_patterns[detected_meal_type]
            
            # Add ALL typical components if not already detected
            for component in typical_components:
                if component not in foods:
                    foods.append(component)
                    print(f"🍽️ Added {detected_meal_type} component: {component} (detected with {label})")
            
            print(f"🍽️ {detected_meal_type.replace('_', ' ').title()} detected! Total components: {len(foods)}")
        
        # IMPROVED partial matching for individual food items - more comprehensive
        for food_item in self.protein_database.keys():
            if food_item in label and len(food_item) >= 3:
                # Skip non-food items that shouldn't be detected
                non_food_items = [
                    "salt", "pepper", "black pepper", "white pepper", "salt and pepper",
                    "sugar", "honey", "syrup", "oil", "olive oil", "vegetable oil",
                    "vinegar", "lemon juice", "lime juice", "soy sauce", "hot sauce",
                    "ketchup", "mustard", "mayonnaise", "butter", "margarine",
                    "flour", "baking powder", "baking soda", "yeast", "breadcrumbs",
                    "water", "ice", "steam", "smoke", "air", "dust", "dirt"
                ]
                
                if food_item in non_food_items:
                    continue  # Skip non-food items
                
                # More flexible matching for multi-item detection
                is_valid_match = (
                    food_item in label or
                    label.startswith(food_item + " ") or
                    label.endswith(" " + food_item) or
                    food_item in label.split() or
                    any(word in food_item for word in label.split()) or
                    (len(food_item) >= 4 and food_item in label)
                )
                
                # Additional validation to prevent false matches
                is_not_partial_word = (
                    not any(other_food != food_item and other_food.startswith(food_item) 
                           for other_food in self.protein_database.keys())
                )
                
                # Additional validation to prevent substring false positives
                # Check if this is a real word boundary match, not just substring
                # More flexible matching for multi-word food items like "fried egg", "baked beans"
                is_word_boundary_match = (
                    food_item == label or  # Exact match
                    label.startswith(food_item + " ") or  # Starts with food item + space
                    label.endswith(" " + food_item) or  # Ends with space + food item
                    " " + food_item + " " in " " + label + " " or  # Word surrounded by spaces
                    food_item in label.split() or  # Food item is a separate word
                    # For multi-word food items, check if all words are present
                    (len(food_item.split()) > 1 and all(word in label for word in food_item.split())) or
                    # For single words, check if they're part of the label as a complete word
                    (len(food_item.split()) == 1 and (
                        food_item in label.split() or  # Food item is a separate word in the label
                        label.startswith(food_item + " ") or  # Label starts with food item
                        label.endswith(" " + food_item) or  # Label ends with food item
                        " " + food_item + " " in " " + label + " "  # Food item surrounded by spaces
                    ))
                )
                
                # Prevent overlapping wrap-related detections
                # If we're about to add a generic wrap but a specific wrap type is already detected (or vice versa), skip
                wrap_types = ["wrap", "burrito", "taco", "quesadilla", "enchilada", "fajita", "shawarma", "gyro", "kebab"]
                if food_item in wrap_types:
                    # Check if any other wrap type is already detected
                    skip_this_item = False
                    for existing_food in foods:
                        if existing_food in wrap_types and existing_food != food_item:
                            # If we're trying to add "wrap" but a specific type like "burrito" is already detected, skip wrap
                            if food_item == "wrap" and existing_food != "wrap":
                                skip_this_item = True
                                break
                            # If we're trying to add a specific type but "wrap" is already detected, replace wrap with specific type
                            elif food_item != "wrap" and existing_food == "wrap":
                                foods.remove("wrap")  # Remove generic wrap in favor of specific type
                                break
                            # If both are specific types, keep the one with higher confidence (handled by filtering later)
                            elif food_item != "wrap" and existing_food != "wrap":
                                skip_this_item = True
                                break
                    if skip_this_item:
                        continue
                
                if is_valid_match and is_not_partial_word and is_word_boundary_match and food_item not in foods:
                    foods.append(food_item)
        
        # Category-based matching for high-confidence categories (only if no specific items found)
        if confidence >= 0.75 and not foods:  # Lowered from 0.80
            category_matches = self._match_food_categories(label, already_detected_foods)
            for item in category_matches:
                if item not in foods:
                    foods.append(item)
        
        return foods

    def _extract_meal_components(self, meal_label: str, confidence: float) -> List[str]:
        """Extract individual food components from meal descriptions with enhanced accuracy"""
        components = []
        
        # ENHANCED breakfast components - comprehensive detection
        breakfast_components = {
            "english breakfast": ["bacon", "eggs", "sausage", "toast", "beans", "mushrooms", "tomato", "hash browns"],
            "full english": ["bacon", "eggs", "sausage", "toast", "beans", "mushrooms", "tomato", "hash browns"],
            "full breakfast": ["bacon", "eggs", "sausage", "toast", "beans", "mushrooms", "tomato", "hash browns"],
            "american breakfast": ["bacon", "eggs", "pancakes", "toast", "sausage", "hash browns"],
            "continental breakfast": ["bread", "cheese", "yogurt", "fruit", "cereal", "pastries"],
            "breakfast": ["eggs", "bacon", "toast", "cereal", "milk", "yogurt", "sausage"],
            "fry up": ["bacon", "eggs", "sausage", "toast", "beans", "mushrooms", "tomato", "hash browns"],
            "big breakfast": ["bacon", "eggs", "sausage", "toast", "beans", "hash browns", "mushrooms"],
            "weekend breakfast": ["bacon", "eggs", "pancakes", "waffles", "french toast", "sausage", "hash browns"],
            # ENHANCED: More comprehensive breakfast variations
            "brunch": ["eggs", "bacon", "toast", "fruit", "pastries", "coffee", "sausage"],
            "breakfast buffet": ["eggs", "bacon", "sausage", "toast", "cereal", "fruit", "pastries", "hash browns"],
            "breakfast sandwich": ["bread", "eggs", "cheese", "bacon", "sausage", "hash browns"],
            "breakfast burrito": ["tortilla", "eggs", "cheese", "bacon", "potato", "sausage"],
            "breakfast bowl": ["eggs", "rice", "vegetables", "meat", "sauce", "bacon"],
            "breakfast platter": ["eggs", "bacon", "sausage", "toast", "hash browns", "fruit", "mushrooms"],
            # ENHANCED: Individual breakfast items trigger full breakfast detection
            "sausage": ["sausage", "eggs", "bacon", "toast", "beans", "mushrooms", "tomato", "hash browns"],
            "bacon": ["bacon", "eggs", "sausage", "toast", "beans", "mushrooms", "tomato", "hash browns"],
            "eggs": ["eggs", "bacon", "sausage", "toast", "beans", "mushrooms", "tomato", "hash browns"]
        }
        
        # ENHANCED lunch/dinner components - comprehensive meal detection
        meal_components = {
            "lunch": ["sandwich", "salad", "soup", "pasta", "rice", "chicken", "beef", "vegetables", "bread"],
            "dinner": ["steak", "chicken", "fish", "pasta", "rice", "vegetables", "salad", "potato", "gravy", "bread"],
            "meal": ["protein", "carbohydrate", "vegetables", "sauce", "bread"],
            "plate": ["protein", "carbohydrate", "vegetables", "sauce", "bread"],
            "dish": ["protein", "carbohydrate", "vegetables", "sauce", "bread"],
            "feast": ["multiple_proteins", "carbohydrates", "vegetables", "sauces", "bread"],
            "spread": ["multiple_proteins", "carbohydrates", "vegetables", "sauces", "bread"],
            # ENHANCED: More comprehensive meal variations
            "lunch special": ["sandwich", "soup", "salad", "chips", "drink", "vegetables"],
            "dinner special": ["entree", "side", "salad", "bread", "dessert", "vegetables", "sauce"],
            "meal deal": ["main", "side", "drink", "dessert", "vegetables"],
            "combo": ["main", "side", "drink", "vegetables", "sauce"],
            "platter": ["meat", "cheese", "vegetables", "bread", "dips", "sauce"],
            "sampler": ["multiple_small_portions", "dips", "bread", "vegetables"],
            "tasting": ["small_portions", "multiple_items", "sauces", "bread"],
            "buffet": ["multiple_proteins", "carbohydrates", "vegetables", "soups", "desserts", "bread"],
            # ENHANCED: Specific cuisine patterns
            "pasta": ["pasta", "sauce", "cheese", "meat", "vegetables", "herbs"],
            "pizza": ["dough", "cheese", "sauce", "toppings", "vegetables"],
            "curry": ["rice", "meat", "vegetables", "sauce", "bread", "spices"],
            "stir fry": ["rice", "vegetables", "meat", "sauce", "noodles"],
            "salad": ["lettuce", "tomato", "cucumber", "cheese", "dressing", "vegetables"],
            "sandwich": ["bread", "meat", "cheese", "vegetables", "sauce"],
            "soup": ["broth", "vegetables", "meat", "herbs", "bread"]
        }
        
        # Check for specific meal types
        meal_found = False
        
        # Check breakfast patterns first (most specific)
        for meal_type, items in breakfast_components.items():
            if meal_type in meal_label:
                meal_found = True
                # Add components based on confidence level - ENHANCED thresholds for better detection
                if confidence >= 0.70:  # High confidence - add most components
                    components.extend(items[:8])  # Add up to 8 components for full breakfast
                    print(f"🍳 High confidence breakfast: {meal_type} -> {items[:8]}")
                elif confidence >= 0.60:  # Medium-high confidence
                    components.extend(items[:7])  # Add up to 7 components
                    print(f"🍳 Medium-high confidence breakfast: {meal_type} -> {items[:7]}")
                elif confidence >= 0.50:  # Medium confidence
                    components.extend(items[:6])  # Add up to 6 components
                    print(f"🍳 Medium confidence breakfast: {meal_type} -> {items[:6]}")
                else:
                    components.extend(items[:5])  # Add up to 5 components even at low confidence
                    print(f"🍳 Low confidence breakfast: {meal_type} -> {items[:5]}")
                break
        
        # Check other meal patterns if no breakfast found
        if not meal_found:
            for meal_type, items in meal_components.items():
                if meal_type in meal_label:
                    meal_found = True
                    # For generic meals, be more inclusive to detect all components
                    if confidence >= 0.65:  # High confidence - add most components
                        components.extend(items[:6])  # Add up to 6 components
                        print(f"🍽️ High confidence meal: {meal_type} -> {items[:6]}")
                    elif confidence >= 0.55:  # Medium-high confidence
                        components.extend(items[:5])  # Add up to 5 components
                        print(f"🍽️ Medium-high confidence meal: {meal_type} -> {items[:5]}")
                    elif confidence >= 0.50:  # Medium confidence
                        components.extend(items[:4])  # Add up to 4 components
                        print(f"🍽️ Medium confidence meal: {meal_type} -> {items[:4]}")
                    else:
                        components.extend(items[:3])  # Add up to 3 components even at low confidence
                        print(f"🍽️ Low confidence meal: {meal_type} -> {items[:3]}")
                    break
        
        # If no specific meal pattern found, try to extract individual food items
        if not meal_found:
            # IMPROVED: Look for more common food keywords in the meal label
            food_keywords = ["chicken", "beef", "pork", "fish", "eggs", "bacon", "sausage", 
                           "toast", "bread", "rice", "pasta", "vegetables", "salad", "cheese",
                           "turkey", "lamb", "salmon", "tuna", "shrimp", "crab", "lobster",
                           "beans", "lentils", "chickpeas", "potato", "corn", "broccoli", "spinach",
                           "tomato", "cucumber", "lettuce", "onion", "mushrooms", "carrot",
                           "apple", "banana", "orange", "berry", "grape", "peach", "pear",
                           "milk", "yogurt", "cream", "butter", "oil", "vinegar", "herbs", "spices"]
            
            for keyword in food_keywords:
                if keyword in meal_label:
                    components.append(keyword)
                    print(f"🔍 Extracted food keyword: {keyword} from '{meal_label}'")
            
            # IMPROVED: Limit components based on confidence - more inclusive
            if confidence >= 0.65:  # Lowered from 0.70
                components = components[:5]  # Increased from 4 to 5
            elif confidence >= 0.55:  # Lowered from 0.60
                components = components[:4]  # Increased from 3 to 4
            else:
                components = components[:3]  # Increased from 2 to 3
        
        # Remove duplicates while preserving order
        unique_components = []
        for component in components:
            if component not in unique_components:
                unique_components.append(component)
        
        print(f"🍽️ Final meal components: {unique_components}")
        return unique_components

    def _match_food_categories(self, label: str, already_detected_foods: List[str]) -> List[str]:
        """Match food categories to specific items"""
        category_matches = []
        
        category_mappings = {
            "meat": ["beef", "chicken", "pork", "lamb", "turkey"],  # Removed "steak" as it's too generic
            "fish": ["salmon", "tuna", "cod", "tilapia"],
            "dairy": ["milk", "cheese", "yogurt"],
            "eggs": ["egg", "eggs"],
            "legumes": ["beans", "lentils", "chickpeas"],
            "nuts": ["almonds", "walnuts", "peanuts", "cashews"],
            "bread": ["toast", "bread", "bagel"],
            "vegetables": ["tomato", "mushrooms", "spinach", "broccoli"],
            "fruits": ["apple", "banana", "orange", "berry"]
        }
        
        # Only match categories if the label is very specific to that category
        # and doesn't already contain specific food items
        for category, items in category_mappings.items():
            if category in label and not any(item in label for item in items):
                # Additional check: don't add generic meat items if specific meat products are detected
                if category == "meat":
                    # Check if specific meat products are already detected in any of the foods
                    specific_meats = ["pepperoni", "salami", "bacon", "ham", "sausage", "prosciutto", "mortadella", "chorizo", "kielbasa", "bratwurst"]
                    if any(specific_meat in already_detected_foods for specific_meat in specific_meats):
                        continue  # Skip adding generic meat if specific meat is already detected
                    
                    # Also check the current label for specific meats
                    if any(specific_meat in label for specific_meat in specific_meats):
                        continue  # Skip adding generic meat if specific meat is already detected
                    
                    # For meat category, be much more restrictive - only add if label specifically mentions beef-related terms
                    if category == "meat":
                        beef_keywords = ["beef", "steak", "burger", "hamburger", "roast beef", "ground beef", "beef steak", "ribeye", "sirloin", "filet", "t-bone", "porterhouse"]
                        if not any(beef_keyword in label for beef_keyword in beef_keywords):
                            continue  # Skip adding beef if no beef-specific terms are mentioned
                        
                        # Only add beef if beef-specific terms are found
                        if any(beef_keyword in label for beef_keyword in beef_keywords):
                            category_matches.append("beef")
                            continue
                
                # For other categories, add the most relevant item from the category
                for item in items:
                    if item in self.protein_database:
                        category_matches.append(item)
                        break  # Only add one item per category
        
        return category_matches

    def _enhanced_confidence_filtering(self, detected_foods: List[str], confidence_scores: Dict[str, float]) -> List[str]:
        """Enhanced confidence-based filtering to improve detection accuracy"""
        if not detected_foods:
            return []
        
        print(f"🔍 Enhanced confidence filtering for {len(detected_foods)} foods:")
        
        # IMPROVED confidence thresholds - balanced for accuracy vs recall
        if len(detected_foods) <= 2:
            # For 1-2 foods, be more lenient to catch all foods
            min_confidence = 0.50  # Raised from 0.40 for better accuracy
            high_confidence_threshold = 0.70  # Raised from 0.65
        elif len(detected_foods) <= 4:
            # For 3-4 foods, require moderate confidence
            min_confidence = 0.55  # Raised from 0.45
            high_confidence_threshold = 0.75  # Raised from 0.70
        else:
            # For 5+ foods, be more strict to avoid false positives
            min_confidence = 0.60  # Raised from 0.50
            high_confidence_threshold = 0.80  # Raised from 0.75
        
        # Filter foods by confidence
        filtered_foods = []
        for food in detected_foods:
            confidence = confidence_scores.get(food, 0.5)
            
            if confidence >= min_confidence:
                filtered_foods.append(food)
                print(f"   ✅ Kept: {food} (confidence: {confidence:.3f})")
            else:
                print(f"   ❌ Filtered out: {food} (confidence: {confidence:.3f} < {min_confidence})")
        
        # If we have too many foods after filtering, prioritize by confidence
        if len(filtered_foods) > 5:  # Increased from 4 to allow more foods
            print(f"   ⚠️  Too many foods ({len(filtered_foods)}), prioritizing by confidence...")
            # Sort by confidence and keep top 5
            filtered_foods.sort(key=lambda x: confidence_scores.get(x, 0.0), reverse=True)
            filtered_foods = filtered_foods[:5]  # Increased from 4 to 5
            print(f"   🎯 Kept top 5: {filtered_foods}")
        
        # Additional smart filtering for common false positives
        smart_filtered = []
        for food in filtered_foods:
            confidence = confidence_scores.get(food, 0.5)
            
            # High confidence foods are always kept
            if confidence >= high_confidence_threshold:
                smart_filtered.append(food)
                continue
            
            # For medium confidence foods, apply additional checks
            if confidence >= min_confidence:
                # Additional validation: ensure it's actually a food item
                if not self._is_food_item(food):
                    print(f"   ❌ Filtered out non-food: {food} (confidence: {confidence:.3f})")
                    continue
                
                # Check if this food makes sense with other detected foods
                if self._is_food_compatible(food, smart_filtered):
                    smart_filtered.append(food)
                else:
                    print(f"   ⚠️  Filtered out incompatible: {food} (confidence: {confidence:.3f})")
        
        print(f"   🎯 Final filtered foods: {smart_filtered}")
        return smart_filtered
    
    def _is_food_compatible(self, food: str, existing_foods: List[str]) -> bool:
        """Check if a food item is compatible with already detected foods"""
        if not existing_foods:
            return True
        
        # Define food compatibility groups
        protein_groups = {
            "meat": ["beef", "chicken", "pork", "lamb", "turkey", "steak", "burger"],
            "fish": ["salmon", "tuna", "cod", "tilapia", "shrimp", "crab", "lobster"],
            "dairy": ["milk", "cheese", "yogurt", "cream", "butter"],
            "eggs": ["egg", "eggs", "omelet", "scrambled"]
        }
        
        # Check if this food conflicts with existing foods
        for group_name, group_foods in protein_groups.items():
            if food in group_foods:
                # Check if we already have a food from this group
                for existing_food in existing_foods:
                    if existing_food in group_foods and existing_food != food:
                        # If this is a different protein source, it's usually compatible
                        if group_name == "meat" and len([f for f in existing_foods if f in group_foods]) < 2:
                            return True  # Allow up to 2 meat types
                        elif group_name == "fish" and len([f for f in existing_foods if f in group_foods]) < 2:
                            return True  # Allow up to 2 fish types
                        else:
                            return False  # Too many proteins from same group
        
        # Check for common meal patterns
        meal_patterns = {
            "breakfast": ["eggs", "bacon", "sausage", "toast", "beans", "mushroom", "tomato"],
            "pasta_dish": ["pasta", "spaghetti", "penne", "beef", "chicken", "sauce"],
            "rice_dish": ["rice", "chicken", "beef", "vegetables", "curry"],
            "salad": ["salad", "lettuce", "cucumber", "tomato", "cheese", "chickpeas"],
            "sandwich": ["bread", "toast", "chicken", "beef", "cheese", "lettuce", "tomato"]
        }
        
        # Check if this food fits any meal pattern
        for pattern_name, pattern_foods in meal_patterns.items():
            if food in pattern_foods:
                # Count how many foods from this pattern we already have
                pattern_count = len([f for f in existing_foods if f in pattern_foods])
                if pattern_count < 3:  # Allow up to 3 foods from same pattern
                    return True
        
        # If no conflicts found, food is compatible
        return True

    def calculate_protein_content(self, foods: List[str]) -> float:
        """Calculate total protein content for detected foods using realistic portion sizes"""
        if not foods:
            return 0.0
        
        # For single food item: use a realistic single-serving size (~200g cooked meal equivalent)
        if len(foods) == 1:
            food = foods[0]
            protein_per_100g = self.protein_database.get(food, 5.0)
            
            # Realistic portion size for a single main dish (reduced to 120g for more realistic portions)
            portion_size = 120.0
            total_protein = (protein_per_100g * portion_size) / 100.0
            # Validate and cap protein at realistic levels
            validated_protein = self._validate_protein_content(total_protein, 1)
            return round(validated_protein, 1)
        
        # For two food items: share a realistic total (~300g)
        if len(foods) == 2:
            total_protein = 0.0
            
            # Fixed portion sizes: 100g each for 2 foods = 200g total (more realistic portions)
            for food in foods:
                portion_size = 100.0
                protein_per_100g = self.protein_database.get(food, 5.0)
                protein_for_this_item = (protein_per_100g * portion_size) / 100.0
                total_protein += protein_for_this_item
                    
        else:
            # For 3+ items: use SMART portion distribution
            # Total plate should scale with number of foods for realistic calories
            total_plate_weight = self._get_total_plate_weight(len(foods))
            
            # Distribute portions intelligently based on food type and importance
            total_protein = 0.0
            for food in foods:
                # Get adjusted portion size for multi-item plates
                adjusted_portion = self._get_adjusted_portion_for_plate(food, foods, total_plate_weight)
                protein_per_100g = self.protein_database.get(food, 5.0)
                protein_for_this_item = (protein_per_100g * adjusted_portion) / 100.0
                total_protein += protein_for_this_item
        
        # Validate and cap protein at realistic levels for typical meals
        validated_protein = self._validate_protein_content(total_protein, len(foods))
        return round(validated_protein, 1)
    
    def _get_realistic_portion_size(self, food: str) -> float:
        """Get realistic portion size in grams for a given food item"""
        # Define realistic portion sizes based on typical servings
        portion_sizes = {
            # Proteins (typical serving sizes)
            "beef": 150.0, "steak": 150.0, "chicken": 150.0, "chicken breast": 150.0,
            "pork": 150.0, "pork chop": 150.0, "lamb": 150.0, "turkey": 150.0,
            "salmon": 150.0, "tuna": 150.0, "cod": 150.0, "tilapia": 150.0,
            "shrimp": 120.0, "crab": 120.0, "lobster": 120.0, "sashimi": 100.0,
            
            # Eggs and dairy
            "egg": 50.0, "eggs": 100.0, "bacon": 50.0, "ham": 100.0,
            "sausage": 100.0, "pepperoni": 50.0, "salami": 50.0,
            "cheese": 50.0, "milk": 250.0, "yogurt": 200.0,
            
            # Grains and carbs
            "pasta": 200.0, "spaghetti": 200.0, "rice": 180.0, "white rice": 180.0,
            "bread": 80.0, "toast": 80.0, "wrap": 100.0, "tortilla": 80.0,
            "pizza": 250.0, "sandwich": 200.0, "burger": 200.0,
            
            # Vegetables and fruits
            "salad": 150.0, "cucumber": 100.0, "tomato": 100.0, "broccoli": 150.0,
            "spinach": 100.0, "lettuce": 100.0, "carrot": 100.0, "potato": 150.0,
            
            # Legumes and nuts
            "beans": 150.0, "lentils": 150.0, "chickpeas": 150.0,
            "almonds": 30.0, "walnuts": 30.0, "peanuts": 30.0,
            
            # Composite dishes
            "cassoulet": 300.0, "curry": 300.0, "stew": 300.0, "soup": 300.0,
            "lasagna": 300.0, "casserole": 300.0, "paella": 300.0,
            
            # Breakfast items
            "oatmeal": 200.0, "cereal": 100.0, "granola": 100.0,
            "pancakes": 150.0, "waffles": 150.0, "french toast": 150.0
        }
        
        # Return realistic portion size, or default to 100g if not specified
        return portion_sizes.get(food.lower(), 100.0)
    
    def _get_total_plate_weight(self, num_foods: int) -> float:
        """Get total plate weight based on number of foods (much more realistic portions)."""
        if num_foods <= 1:
            return 120.0  # Single entree (much more realistic)
        if num_foods == 2:
            return 200.0  # Entree + side (more realistic)
        if num_foods == 3:
            return 300.0  # Protein + carb + veg (more realistic)
        if num_foods == 4:
            return 350.0  # More realistic
        if num_foods == 5:
            return 400.0  # More realistic
        # 6 or more items (buffet/tapas style)
        return 500.0  # More realistic
    
    def _get_adjusted_portion_for_plate(self, food: str, all_foods: List[str], total_plate_weight: float) -> float:
        """Get adjusted portion size for multi-item plates - fixed at 250g total"""
        # Food priority categories (higher priority = larger portion)
        high_priority = ["chicken", "beef", "pork", "salmon", "tuna", "eggs", "tofu", "beans"]
        medium_priority = ["rice", "pasta", "quinoa", "bread", "toast", "wrap", "pizza"]
        low_priority = ["vegetables", "salad", "tomato", "cucumber", "lettuce", "sauce", "gravy", "lemon"]
        
        # Calculate portion based on priority and total plate weight
        num_foods = len(all_foods)
        
        if num_foods == 2:
            # 2 foods: even split
            return total_plate_weight / 2.0
        if num_foods == 3:
            # 3 foods: prioritize protein, then carbs, then sides
            if food in high_priority:
                return total_plate_weight * 0.40
            if food in medium_priority:
                return total_plate_weight * 0.40
            return total_plate_weight * 0.20
        if num_foods == 4:
            # 4 foods: 35% protein, 35% carb, 30% others split
            if food in high_priority:
                return total_plate_weight * 0.35
            if food in medium_priority:
                return total_plate_weight * 0.35
            return total_plate_weight * 0.30 / max(1, len([f for f in all_foods if f not in high_priority and f not in medium_priority]))
        # 5+ foods: distribute with slight preference to protein and carbs
        if food in high_priority:
            return total_plate_weight * 0.30 / max(1, len([f for f in all_foods if f in high_priority]))
        if food in medium_priority:
            return total_plate_weight * 0.30 / max(1, len([f for f in all_foods if f in medium_priority]))
        return total_plate_weight * 0.40 / max(1, len([f for f in all_foods if f not in high_priority and f not in medium_priority]))
    
    def _validate_protein_content(self, calculated_protein: float, num_foods: int) -> float:
        """Validate and cap protein content at realistic levels for typical meals"""
        # Realistic protein limits based on meal type and number of items (much more realistic)
        protein_limits = {
            1: 25.0,   # Single food: max 25g protein (e.g., normal portion)
            2: 22.0,   # Two foods: max 22g protein (e.g., pasta + meat)
            3: 20.0,   # Three foods: max 20g protein (e.g., protein + carb + veg)
            4: 18.0,   # Four foods: max 18g protein (e.g., breakfast plate)
            5: 16.0,   # Five foods: max 16g protein
            6: 15.0,   # Six+ foods: max 15g protein (e.g., buffet style)
        }
        
        max_protein = protein_limits.get(num_foods, 25.0)
        
        # If calculated protein is unrealistically high, cap it
        if calculated_protein > max_protein:
            print(f"⚠️  Protein capped from {calculated_protein:.1f}g to {max_protein:.1f}g (realistic limit for {num_foods} items)")
            return max_protein
        
        return calculated_protein
    
    def calculate_calories(self, foods: List[str], portions: List[float]) -> float:
        """Calculate total calories for validation"""
        if len(foods) != len(portions):
            return 0.0
        
        total_calories = 0.0
        for food, portion in zip(foods, portions):
            calories_per_100g = self.calorie_database.get(food, self.calorie_database["default"])
            food_calories = (calories_per_100g * portion) / 100.0
            total_calories += food_calories
        
        return round(total_calories, 1)

    def _canonicalize_food_list(self, foods: List[str]) -> List[str]:
        """Map detected items to canonical keys used in the nutrition databases and de-duplicate.
        Keeps original order, limits to top 5 items (increased from 3).
        """
        if not foods:
            return []
        mapping = {
            "burger": "hamburger",
            "beefburger": "hamburger",
            "prawns": "shrimp",
            "fries": "potato",
            "chips": "chips",
            "cheese pizza": "pizza",
            "wraps": "wrap",
            "eggs": "eggs",
            "egg": "eggs",
            "veggies": "vegetables",
            # IMPROVED: Add more mappings for better detection
            "steak": "beef",
            "ground beef": "beef",
            "mince": "beef",
            "roast beef": "beef",
            "beef steak": "beef",
            "ribeye": "beef",
            "sirloin": "beef",
            "filet": "beef",
            "t-bone": "beef",
            "porterhouse": "beef",
            "chicken breast": "chicken",
            "chicken thigh": "chicken",
            "chicken wing": "chicken",
            "chicken leg": "chicken",
            "chicken drumstick": "chicken",
            "pork chop": "pork",
            "pork loin": "pork",
            "pork shoulder": "pork",
            "pork belly": "pork",
            "lamb chop": "lamb",
            "lamb shank": "lamb",
            "lamb shoulder": "lamb",
            "lamb leg": "lamb",
            "turkey breast": "turkey",
            "turkey thigh": "turkey",
            "turkey wing": "turkey",
            "turkey leg": "turkey",
            "salmon fillet": "salmon",
            "salmon steak": "salmon",
            "tuna steak": "tuna",
            "tuna fillet": "tuna",
            "cod fillet": "cod",
            "tilapia fillet": "tilapia",
            "shrimp": "shrimp",
            "prawn": "shrimp",
            "crab meat": "crab",
            "lobster meat": "lobster",
            "white rice": "rice",
            "brown rice": "rice",
            "jasmine rice": "rice",
            "basmati rice": "rice",
            "long grain rice": "rice",
            "short grain rice": "rice",
            "spaghetti": "pasta",
            "penne": "pasta",
            "fettuccine": "pasta",
            "lasagna": "pasta",
            "rigatoni": "pasta",
            "macaroni": "pasta",
            "farfalle": "pasta",
            "fusilli": "pasta",
            "rotini": "pasta",
            "orecchiette": "pasta",
            "ravioli": "pasta",
            "tortellini": "pasta",
            "bread": "bread",
            "toast": "toast",
            "bagel": "bagel",
            "english muffin": "english muffin",
            "bun": "bread",
            "roll": "bread",
            "croissant": "croissant",
            "danish": "danish",
            "donut": "donut",
            "muffin": "muffin",
            "scone": "scone",
            "biscuit": "biscuit",
            "pancake": "pancakes",
            "waffle": "waffles",
            "crepe": "crepes",
            "french toast": "french toast",
            "oatmeal": "oatmeal",
            "porridge": "porridge",
            "cereal": "cereal",
            "granola": "granola",
            "muesli": "muesli",
            "cream of wheat": "cream of wheat",
            "farina": "farina",
            "yogurt": "yogurt",
            "greek yogurt": "greek yogurt",
            "cottage cheese": "cottage cheese",
            "milk": "milk",
            "cheese": "cheese",
            "cream": "cream",
            "butter": "butter",
            "bacon": "bacon",
            "ham": "ham",
            "sausage": "sausage",
            "pepperoni": "pepperoni",
            "salami": "salami",
            "prosciutto": "prosciutto",
            "mortadella": "mortadella",
            "bologna": "bologna",
            "pastrami": "pastrami",
            "corned beef": "corned beef",
            "roast beef": "roast beef",
            "jerky": "jerky",
            "beef jerky": "beef jerky",
            "turkey jerky": "turkey jerky",
            "salad": "salad",
            "lettuce": "lettuce",
            "greens": "salad",
            "spinach": "spinach",
            "broccoli": "broccoli",
            "carrot": "carrot",
            "potato": "potato",
            "tomato": "tomato",
            "cucumber": "cucumber",
            "onion": "onion",
            "mushrooms": "mushrooms",
            "corn": "corn",
            "beans": "beans",
            "lentils": "lentils",
            "chickpeas": "chickpeas",
            "peas": "peas",
            "apple": "apple",
            "banana": "banana",
            "orange": "orange",
            "berry": "berry",
            "grape": "grape",
            "peach": "peach",
            "pear": "pear",
            "strawberry": "strawberry",
            "blueberry": "blueberry",
            "raspberry": "raspberry",
            "blackberry": "blackberry",
            "cherry": "cherry",
            "pineapple": "pineapple",
            "mango": "mango",
            "kiwi": "kiwi",
            "lemon": "lemon",
            "lime": "lime",
            "avocado": "avocado",
            "olive": "olive",
            "pickle": "pickle",
            "sauerkraut": "sauerkraut",
            "kimchi": "kimchi",
            "salsa": "salsa",
            "guacamole": "guacamole",
            "hummus": "hummus",
            "dip": "dip",
            "spread": "spread",
            "sauce": "sauce",
            "gravy": "gravy",
            "dressing": "dressing",
            "marinade": "marinade",
            "rub": "rub",
            "seasoning": "seasoning",
            "spice": "spice",
            "herb": "herb",
            "garlic": "garlic",
            "ginger": "ginger",
            "curry": "curry",
            "paprika": "paprika",
            "cumin": "cumin",
            "coriander": "coriander",
            "turmeric": "turmeric",
            "oregano": "oregano",
            "basil": "basil",
            "thyme": "thyme",
            "rosemary": "rosemary",
            "sage": "sage",
            "parsley": "parsley",
            "cilantro": "cilantro",
            "mint": "mint",
            "dill": "dill",
            "bay leaf": "bay leaf",
            "nutmeg": "nutmeg",
            "cinnamon": "cinnamon",
            "cloves": "cloves",
            "allspice": "allspice",
            "cardamom": "cardamom",
            "star anise": "star anise",
            "fennel": "fennel",
            "caraway": "caraway",
            "poppy seed": "poppy seed",
            "sesame seed": "sesame seed",
            "sunflower seed": "sunflower seed",
            "pumpkin seed": "pumpkin seed",
            "chia seed": "chia seed",
            "flax seed": "flax seed",
            "hemp seed": "hemp seed",
            "quinoa": "quinoa",
            "buckwheat": "buckwheat",
            "millet": "millet",
            "sorghum": "sorghum",
            "teff": "teff",
            "amaranth": "amaranth",
            "spelt": "spelt",
            "kamut": "kamut",
            "farro": "farro",
            "bulgur": "bulgur",
            "couscous": "couscous",
            "polenta": "polenta",
            "grits": "grits",
            "cornmeal": "cornmeal",
            "semolina": "semolina",
            "durum": "durum",
            "whole wheat": "whole wheat",
            "rye": "rye",
            "barley": "barley",
            "oats": "oats",
            "wheat": "wheat",
            "flour": "flour",
            "bread flour": "flour",
            "all purpose flour": "flour",
            "cake flour": "flour",
            "pastry flour": "flour",
            "self rising flour": "flour",
            "whole wheat flour": "flour",
            "rye flour": "flour",
            "buckwheat flour": "flour",
            "almond flour": "flour",
            "coconut flour": "flour",
            "chickpea flour": "flour",
            "rice flour": "flour",
            "potato flour": "flour",
            "tapioca flour": "flour",
            "arrowroot flour": "flour",
            "xanthan gum": "xanthan gum",
            "guar gum": "guar gum",
            "agar agar": "agar agar",
            "gelatin": "gelatin",
            "pectin": "pectin",
            "lecithin": "lecithin",
            "yeast": "yeast",
            "baking powder": "baking powder",
            "baking soda": "baking soda",
            "cream of tartar": "cream of tartar",
            "vanilla": "vanilla",
            "vanilla extract": "vanilla",
            "almond extract": "almond extract",
            "lemon extract": "lemon extract",
            "orange extract": "orange extract",
            "peppermint extract": "peppermint extract",
            "food coloring": "food coloring",
            "preservatives": "preservatives",
            "additives": "additives",
            "artificial sweetener": "artificial sweetener",
            "natural sweetener": "natural sweetener",
            "stevia": "stevia",
            "agave": "agave",
            "maple syrup": "maple syrup",
            "molasses": "molasses",
            "brown sugar": "brown sugar",
            "white sugar": "sugar",
            "powdered sugar": "powdered sugar",
            "turbinado sugar": "turbinado sugar",
            "demerara sugar": "demerara sugar",
            "muscovado sugar": "muscovado sugar",
            "palm sugar": "palm sugar",
            "coconut sugar": "coconut sugar",
            "date sugar": "date sugar",
            "fruit sugar": "fruit sugar",
            "corn syrup": "corn syrup",
            "high fructose corn syrup": "high fructose corn syrup",
            "invert sugar": "invert sugar",
            "lactose": "lactose",
            "maltose": "maltose",
            "dextrose": "dextrose",
            "fructose": "fructose",
            "glucose": "glucose",
            "sucrose": "sucrose",
            "maltodextrin": "maltodextrin",
            "polydextrose": "polydextrose",
            "sorbitol": "sorbitol",
            "xylitol": "xylitol",
            "erythritol": "erythritol",
            "mannitol": "mannitol",
            "isomalt": "isomalt",
            "lactitol": "lactitol",
            "maltitol": "maltitol",
            "hydrogenated oil": "hydrogenated oil",
            "partially hydrogenated oil": "partially hydrogenated oil",
            "trans fat": "trans fat",
            "saturated fat": "saturated fat",
            "unsaturated fat": "unsaturated fat",
            "monounsaturated fat": "monounsaturated fat",
            "polyunsaturated fat": "polyunsaturated fat",
            "omega 3": "omega 3",
            "omega 6": "omega 6",
            "omega 9": "omega 9",
            "essential fatty acids": "essential fatty acids",
            "linoleic acid": "linoleic acid",
            "alpha linolenic acid": "alpha linolenic acid",
            "arachidonic acid": "arachidonic acid",
            "docosahexaenoic acid": "docosahexaenoic acid",
            "eicosapentaenoic acid": "eicosapentaenoic acid",
            "gamma linolenic acid": "gamma linolenic acid",
            "conjugated linoleic acid": "conjugated linoleic acid",
            "medium chain triglycerides": "medium chain triglycerides",
            "short chain fatty acids": "short chain fatty acids",
            "long chain fatty acids": "long chain fatty acids",
            "triglycerides": "triglycerides",
            "phospholipids": "phospholipids",
            "sterols": "sterols",
            "cholesterol": "cholesterol",
            "phytosterols": "phytosterols",
            "stanols": "stanols",
            "squalene": "squalene",
            "coenzyme q10": "coenzyme q10",
            "ubiquinone": "ubiquinone",
            "carnitine": "carnitine",
            "acetyl l carnitine": "acetyl l carnitine",
            "propionyl l carnitine": "propionyl l carnitine",
            "l carnitine": "l carnitine",
            "creatine": "creatine",
            "creatine monohydrate": "creatine",
            "creatine ethyl ester": "creatine",
            "creatine hydrochloride": "creatine",
            "creatine citrate": "creatine",
            "creatine malate": "creatine",
            "creatine pyruvate": "creatine",
            "creatine alpha ketoglutarate": "creatine",
            "creatine orotate": "creatine",
            "creatine gluconate": "creatine",
            "creatine phosphate": "creatine",
            "creatine sulfate": "creatine",
            "creatine nitrate": "creatine",
            "creatine acetate": "creatine",
            "creatine fumarate": "creatine",
            "creatine succinate": "creatine",
            "creatine aspartate": "creatine",
            "creatine taurinate": "creatine",
            "creatine orotate": "creatine",
            "creatine gluconate": "creatine",
            "creatine phosphate": "creatine",
            "creatine sulfate": "creatine",
            "creatine nitrate": "creatine",
            "creatine acetate": "creatine",
            "creatine fumarate": "creatine",
            "creatine succinate": "creatine",
            "creatine aspartate": "creatine",
            "creatine taurinate": "creatine"
        }
        canonical: List[str] = []
        seen = set()
        for item in foods:
            key = item.strip().lower()
            mapped = mapping.get(key, key)
            # If mapped item not in protein DB, keep original to avoid losing information
            final_item = mapped if mapped in self.protein_database else key
            if final_item not in seen and final_item in self.protein_database:
                seen.add(final_item)
                canonical.append(final_item)
            # IMPROVED: Stop at 5 items instead of 3 to allow more foods
            if len(canonical) >= 5:
                break
        return canonical

    def _estimate_portions_from_image(self, localized_objects, foods: List[str], conf: Dict[str, float], image_path: str) -> Tuple[Dict[str, float], float]:
        """Estimate per-food portions (grams) using object areas and confidences.
        - Sum areas of foodish objects; map areas to foods by confidence order
        - Convert relative area → grams using image size and heuristic density
        """
        try:
            if not localized_objects or not foods:
                return {}, 0.0
            if not _PIL_AVAILABLE:
                return {}, 0.0
            base_img = Image.open(image_path).convert('RGB')
            w, h = base_img.size
            image_area = float(w * h)
            if image_area <= 0:
                return {}, 0.0

            # Collect foodish object areas
            foodish_names = {"Food", "Dish", "Bowl", "Plate", "Fruit", "Vegetable", "Sandwich", "Bread", "Pizza", "Cake"}
            regions = []
            for obj in localized_objects:
                name = getattr(obj, 'name', '')
                score = float(getattr(obj, 'score', 0.0) or 0.0)
                vertices = getattr(obj, 'bounding_poly', None)
                if not vertices:
                    continue
                vs = getattr(vertices, 'normalized_vertices', [])
                if not vs:
                    continue
                xs = [v.x for v in vs]
                ys = [v.y for v in vs]
                left = max(0.0, min(xs))
                top = max(0.0, min(ys))
                right = min(1.0, max(xs))
                bottom = min(1.0, max(ys))
                area = max(0.0, (right - left) * (bottom - top))
                if area <= 0.0:
                    continue
                # Prefer explicitly foodish objects or high score
                if name in foodish_names or score >= 0.60:
                    regions.append({"area": area, "score": score, "name": name})

            if not regions:
                return {}, 0.0

            # Sort regions by area*score (proxy for food mass prominence)
            regions.sort(key=lambda r: r["area"] * (0.5 + 0.5 * r["score"]), reverse=True)
            total_rel_area = sum(r["area"] for r in regions)
            if total_rel_area <= 0.0:
                return {}, 0.0

            # Heuristic: map total relative area to grams range depending on zoom
            # Use piecewise mapping to avoid extremes - MUCH MORE REALISTIC PORTIONS
            avg_rel_area = min(1.0, max(0.0, total_rel_area))
            # Calibrated to avoid unrealistic gram totals - reduced by ~60%
            if avg_rel_area > 0.35:
                est_total_g = 140.0  # Reduced from 350.0
            elif avg_rel_area > 0.20:
                est_total_g = 100.0  # Reduced from 250.0
            elif avg_rel_area > 0.10:
                est_total_g = 70.0   # Reduced from 180.0
            elif avg_rel_area > 0.05:
                est_total_g = 50.0   # Reduced from 120.0
            else:
                est_total_g = 35.0   # Reduced from 80.0

            # Distribute grams across foods by combining food confidence and region prominence
            # Build food weights
            food_weights: Dict[str, float] = {}
            for food in foods:
                base = max(0.05, conf.get(food, 0.5))
                # Penalize high-protein categories so grams don't over-allocate to meats
                if food in self.food_categories.get('meat', set()) or food in self.food_categories.get('fish', set()) or food in {"eggs", "egg"}:
                    base *= 0.75
                # Slightly boost carbs/veg to improve kcal
                if food in self.food_categories.get('carb', set()) or food in self.food_categories.get('vegetable', set()):
                    base *= 1.15
                food_weights[food] = base
            # Normalize food weights
            sw = sum(food_weights.values())
            if sw <= 0:
                return {}, 0.0
            for k in food_weights:
                food_weights[k] /= sw

            # Multiply by region prominence to reflect amount on plate
            # Use top-N regions equal to number of foods
            top_regions = regions[:len(foods)]
            region_weights = [r["area"] for r in top_regions]
            sr = sum(region_weights) or 1.0
            region_weights = [rw / sr for rw in region_weights]

            # Final per-food share: EQUAL SPLIT for multiple foods (25% each for 4 foods)
            portions: Dict[str, float] = {}
            num_foods = len(foods)
            equal_share = 1.0 / num_foods  # Each food gets equal share (25% for 4 foods)
            
            for idx, food in enumerate(foods):
                grams = equal_share * est_total_g
                # Per-food portion caps to avoid extremes - MUCH MORE REALISTIC
                grams = max(10.0, min(grams, 80.0))  # Reduced from 170.0 to 80.0
                portions[food] = round(grams, 1)

            # Ensure total grams are not excessive - MUCH MORE REALISTIC
            total_grams = sum(portions.values())
            if total_grams > 180.0:  # Reduced from 450.0 to 180.0
                scale = 180.0 / total_grams
                for k in portions:
                    portions[k] = round(portions[k] * scale, 1)
                total_grams = round(180.0, 1)

            return portions, round(total_grams, 1)
        except Exception as _e:
            print(f"⚠️ Portion estimation failed: {_e}")
            return {}, 0.0

    def _calculate_protein_from_portions(self, foods: List[str], portions: Dict[str, float]) -> float:
        total = 0.0
        for f in foods:
            grams = float(portions.get(f, 0.0))
            per100 = float(self.protein_database.get(f, 5.0))
            total += per100 * grams / 100.0
        return round(total, 1)

    def _apply_category_consensus(self, foods: List[str], conf: Dict[str, float]) -> Tuple[List[str], Dict[str, float]]:
        """Require consensus across broad categories and suppress improbable outliers.
        Example: if most signals point to vegetables/carb, suppress a lone meat term at low confidence.
        """
        if not foods:
            return foods, conf

        # Count categories
        category_counts: Dict[str, int] = {}
        food_to_category: Dict[str, str] = {}
        for f in foods:
            cat = None
            for c, items in self.food_categories.items():
                if f in items:
                    cat = c
                    break
            if cat:
                category_counts[cat] = category_counts.get(cat, 0) + 1
                food_to_category[f] = cat

        if not category_counts:
            # No category info; return as-is
            return foods, conf

        # Dominant category = the one with max count
        dominant_category = max(category_counts.items(), key=lambda kv: kv[1])[0]

        kept: List[str] = []
        new_conf: Dict[str, float] = {}
        for f in foods:
            cval = conf.get(f, 0.5)
            cat = food_to_category.get(f)

            if not cat:
                # Unknown category: keep if decent confidence
                if cval >= 0.60:
                    kept.append(f)
                    new_conf[f] = cval
                continue

            if cat == dominant_category:
                kept.append(f)
                new_conf[f] = cval
                continue

            # Outlier category: require higher confidence to keep
            # Prevent salad->pork style errors by requiring strong evidence for outliers
            if cval >= 0.80:
                kept.append(f)
                new_conf[f] = cval
            else:
                print(f"   ⚠️  Suppressed outlier '{f}' in category '{cat}' (confidence {cval:.2f}) vs dominant '{dominant_category}'")

        # Ensure at least one item remains
        if not kept:
            # Keep the highest confidence original item
            top = max(foods, key=lambda x: conf.get(x, 0.0))
            kept = [top]
            new_conf[top] = conf.get(top, 0.5)

        return kept, new_conf

    def _filter_and_prioritize_foods(self, foods: List[str], confidence_scores: Dict[str, float]) -> List[str]:
        """Filter and prioritize detected foods using improved logic for complex dishes"""
        if not foods:
            return []
        
        # Step 1: Clean and normalize food names
        cleaned_foods = []
        for food in foods:
            food_clean = food.lower().strip()
            # Remove common non-food terms
            if food_clean not in ['food', 'meal', 'dish', 'plate', 'bowl', 'serving']:
                cleaned_foods.append(food_clean)
        
        if not cleaned_foods:
            return []
        
        # Step 2: Score foods by confidence and nutritional significance
        scored_foods = []
        for food in cleaned_foods:
            confidence = confidence_scores.get(food, 0.5)
            protein_content = self.protein_database.get(food, 5.0)
            
            # Boost score for high-protein foods (more nutritionally significant)
            protein_boost = min(protein_content / 50.0, 0.3)  # Max 0.3 boost
            final_score = confidence + protein_boost
            
            scored_foods.append((food, final_score, protein_content))
        
        # Step 3: Sort by final score
        scored_foods.sort(key=lambda x: x[1], reverse=True)
        
        # Step 4: Smart dish analysis - detect complex dishes
        complex_dish_patterns = {
            # Pasta dishes
            "pasta_with_meat": ["pasta", "spaghetti", "penne", "fettuccine", "lasagna", "rigatoni"],
            "pasta_with_sauce": ["pasta", "spaghetti", "penne", "fettuccine", "lasagna", "rigatoni"],
            
            # Rice dishes  
            "rice_with_meat": ["rice", "white rice", "brown rice", "jasmine rice", "basmati rice"],
            "rice_with_vegetables": ["rice", "white rice", "brown rice", "jasmine rice", "basmati rice"],
            
            # Sandwich/wrap dishes
            "sandwich": ["bread", "toast", "bagel", "english muffin", "bun", "roll"],
            "wrap": ["wrap", "tortilla", "pita", "flatbread", "naan", "roti"],
            
            # Pizza dishes
            "pizza": ["pizza", "pepperoni", "margherita", "cheese pizza"],
            
            # Salad dishes
            "salad": ["salad", "lettuce", "greens", "vegetables", "cucumber", "tomato"],
            
            # Breakfast dishes
            "breakfast": ["egg", "eggs", "bacon", "sausage", "toast", "hash browns", "beans"],
            
            # Soup/stew dishes
            "soup": ["soup", "stew", "broth", "beans", "vegetables", "meat"]
        }
        
        # Step 5: Analyze detected foods for dish patterns
        detected_patterns = []
        for pattern_name, pattern_foods in complex_dish_patterns.items():
            matches = [food for food, _, _ in scored_foods if food in pattern_foods]
            if len(matches) >= 2:  # At least 2 components to form a dish
                detected_patterns.append((pattern_name, matches, len(matches)))
        
        # Step 6: Determine final food items based on dish analysis
        final_foods = []
        
        if detected_patterns:
            # We have complex dishes - prioritize the most complete one
            detected_patterns.sort(key=lambda x: x[2], reverse=True)  # Sort by number of components
            best_pattern = detected_patterns[0]
            
            if best_pattern[0] == "pasta_with_meat":
                # Pasta + meat dish (like spaghetti bolognese)
                pasta_items = [food for food, _, _ in scored_foods if food in ["pasta", "spaghetti", "penne", "fettuccine", "lasagna"]]
                meat_items = [food for food, _, _ in scored_foods if food in ["beef", "ground beef", "meat", "mince"]]
                
                if pasta_items and meat_items:
                    final_foods = [pasta_items[0], meat_items[0]]  # Keep pasta + meat
                elif pasta_items:
                    final_foods = [pasta_items[0]]  # Just pasta if no meat detected
                else:
                    final_foods = [scored_foods[0][0]]  # Fallback to highest scored item
                    
            elif best_pattern[0] == "rice_with_meat":
                # Rice + meat dish (like chicken curry with rice)
                rice_items = [food for food, _, _ in scored_foods if food in ["rice", "white rice", "brown rice", "jasmine rice"]]
                meat_items = [food for food, _, _ in scored_foods if food in ["chicken", "beef", "pork", "fish", "shrimp"]]
                
                if rice_items and meat_items:
                    final_foods = [meat_items[0], rice_items[0]]  # Keep meat + rice
                elif meat_items:
                    final_foods = [meat_items[0]]  # Just meat if no rice detected
                else:
                    final_foods = [scored_foods[0][0]]  # Fallback to highest scored item
                    
            elif best_pattern[0] == "breakfast":
                # Full breakfast - keep multiple components
                breakfast_items = [food for food, _, _ in scored_foods if food in ["egg", "eggs", "bacon", "sausage", "toast", "beans", "mushroom", "tomato"]]
                final_foods = breakfast_items[:3]  # Keep up to 3 breakfast items
                
            elif best_pattern[0] == "salad":
                # Salad - keep main components
                salad_items = [food for food, _, _ in scored_foods if food in ["salad", "lettuce", "greens", "cucumber", "tomato", "chickpeas", "cheese"]]
                final_foods = salad_items[:2]  # Keep up to 2 salad components
                
            elif best_pattern[0] == "pizza":
                # Pizza - keep pizza + main topping if detected
                pizza_items = [food for food, _, _ in scored_foods if food in ["pizza", "pepperoni", "cheese"]]
                final_foods = pizza_items[:2]  # Keep pizza + main topping
                
            else:
                # Other complex dishes - keep top 2-3 components
                pattern_foods = [food for food, _, _ in scored_foods if food in best_pattern[1]]
                final_foods = pattern_foods[:3]  # Keep up to 3 components
        else:
            # No clear dish pattern - use smart single-item detection
            if len(scored_foods) == 1:
                final_foods = [scored_foods[0][0]]
            else:
                # Multiple items but no clear dish - analyze for complementary foods
                primary_food = scored_foods[0][0]
                primary_protein = scored_foods[0][2]
                
                # If primary food is low protein, look for protein source
                if primary_protein < 10.0:
                    protein_foods = [food for food, _, protein in scored_foods if protein > 15.0]
                    if protein_foods:
                        final_foods = [primary_food, protein_foods[0]]
                    else:
                        final_foods = [primary_food]
                else:
                    # Primary food is protein-rich, keep it
                    final_foods = [primary_food]
        
        # Step 7: Final validation and cleanup
        validated_foods = []
        for food in final_foods:
            # Remove non-food items
            if food not in ['food', 'meal', 'dish', 'plate', 'bowl', 'serving', 'sauce', 'gravy', 'dressing']:
                validated_foods.append(food)
        
        # Ensure we don't exceed 3 items
        validated_foods = validated_foods[:3]
        
        print(f"🔍 Food detection analysis:")
        print(f"   Raw detected: {cleaned_foods}")
        print(f"   Complex patterns: {[p[0] for p in detected_patterns]}")
        print(f"   Final selection: {validated_foods}")
        
        return validated_foods


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


# For backward compatibility - but this will only use Google Vision API
def identify_food_local(image_path: str) -> List[str]:
    """Alias for the Google Vision function to maintain compatibility"""
    return identify_food_with_google_vision(image_path)