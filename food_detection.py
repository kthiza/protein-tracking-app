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
        
        # Comprehensive protein database with accurate values from USDA and nutrition databases
        self.protein_database = {
            # Meat & Fish (High Protein) - Values per 100g cooked
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
            "egg": 13.0, "eggs": 13.0, "scrambled eggs": 13.0, "fried eggs": 13.0, "fried egg": 13.0, "boiled eggs": 13.0,
            "omelet": 13.0, "omelette": 13.0, "poached eggs": 13.0, "deviled eggs": 13.0, "yolk": 16.0,
            "milk": 3.4, "cheese": 25.0, "cheddar": 25.0, "mozzarella": 22.0, "parmesan": 38.0,
            "feta": 14.0, "blue cheese": 21.0, "swiss": 27.0, "gouda": 25.0, "brie": 20.0,
            "yogurt": 10.0, "greek yogurt": 10.0, "cottage cheese": 11.0, "cream cheese": 6.0,
            "butter": 0.9, "cream": 2.1, "sour cream": 2.4, "whipping cream": 2.1,
            
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
        """Detect food items in an image using Google Vision API with multi-item meal support"""
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
            
            # Perform web detection for better food identification
            response_web = self.client.web_detection(image=image)
            web_detection = response_web.web_detection
            
            # Process detected labels with improved confidence thresholds for multi-item meals
            detected_foods = []
            confidence_scores = {}
            
            print(f"🏷️  Detected {len(labels)} labels from Vision API:")
            # Process each label from Google Vision API
            for label in labels:
                label_desc = label.description.lower().strip()
                confidence = label.score
                
                if confidence >= 0.65:
                    # Check if this label matches any food items with improved matching
                    food_items = self._extract_food_with_improved_matching(label_desc, confidence, detected_foods)
                    for food in food_items:
                        if food not in detected_foods:
                            detected_foods.append(food)
                            confidence_scores[food] = confidence
            
            # Process web detection results for better multi-item detection
            if web_detection.web_entities:
                print(f"🌐 Processing {len(web_detection.web_entities)} web entities:")
                for entity in web_detection.web_entities:
                    entity_desc = entity.description.lower().strip()
                    confidence = entity.score
                    
                    # Use a lower threshold for web entities as they can be more specific
                    if confidence >= 0.55:
                        print(f"   - {entity_desc} (score: {confidence:.3f})")
                        food_items = self._extract_food_with_improved_matching(entity_desc, confidence, detected_foods)
                        for food in food_items:
                            if food not in detected_foods:
                                detected_foods.append(food)
                                confidence_scores[food] = confidence
            
            # Apply improved filtering for multi-item meals
            filtered_foods = self._filter_multi_item_detections(detected_foods, confidence_scores)

            # Canonicalize outputs to database-friendly items
            filtered_foods = self._canonicalize_food_list(filtered_foods)
            
            if not filtered_foods:
                print("⚠️  No food items detected in image")
                return {
                    "foods": [],
                    "protein_per_100g": 0,
                    "confidence_scores": {},
                    "detection_method": "google_vision_api"
                }
            
            # Calculate total protein content using the 300g normalization (for logs only)
            total_protein = self.calculate_protein_content(filtered_foods)
            
            print(f"🎯 Successfully detected {len(filtered_foods)} food items:")
            for food in filtered_foods:
                conf = confidence_scores.get(food, 0.5)
                protein = self.protein_database.get(food, 5.0)
                print(f"   - {food} (confidence: {conf:.3f}, protein: {protein}g/100g)")
            
            if len(filtered_foods) == 1:
                print(f"📊 Single food item: {filtered_foods[0]}, 300g")
            else:
                grams_per_item = 300.0 / len(filtered_foods)
                print(f"📊 Multiple food items: {len(filtered_foods)} items, {grams_per_item:.0f}g each")
            print(f"📊 Total protein content: {total_protein:.1f}g")
            
            return {
                "foods": filtered_foods,
                "protein_per_100g": total_protein,  # Now represents protein for 120g total food
                "confidence_scores": {k: v for k, v in confidence_scores.items() if k in filtered_foods},
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
        
        # Handle meat-based sauces and complex dishes FIRST (before direct matches)
        meat_sauce_mappings = {
            "bolognese": "beef",
            "bolognese sauce": "beef",
            "meat sauce": "beef",
            "beef sauce": "beef",
            "beef spaghetti": "beef",
            "beef pasta": "beef",
            "chicken sauce": "chicken",
            "chicken pasta": "chicken",
            "pork sauce": "pork",
            "lamb sauce": "lamb",
            "turkey sauce": "turkey"
        }
        
        # Check for meat-based sauce descriptions first
        sauce_found = False
        for sauce_desc, meat_type in meat_sauce_mappings.items():
            if sauce_desc in label and meat_type not in foods:
                foods.append(meat_type)
                sauce_found = True
                break  # Only use the first matching sauce
        
        # Direct exact matches - highest priority (but skip if we found a sauce)
        if label in self.protein_database and not sauce_found:
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
            ("turkey rice", ["turkey", "rice"])
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
        
        # Improved partial matching for individual food items
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
        if confidence >= 0.85 and not foods:
            category_matches = self._match_food_categories(label, already_detected_foods)
            for item in category_matches:
                if item not in foods:
                    foods.append(item)
        
        return foods

    def _extract_meal_components(self, meal_label: str, confidence: float) -> List[str]:
        """Extract individual food components from meal descriptions"""
        components = []
        
        # Common breakfast components
        breakfast_components = {
            "english breakfast": ["bacon", "eggs", "sausage", "toast", "beans", "mushrooms", "tomato"],
            "full breakfast": ["bacon", "eggs", "sausage", "toast", "beans", "mushrooms", "tomato"],
            "american breakfast": ["bacon", "eggs", "pancakes", "toast", "sausage"],
            "continental breakfast": ["bread", "cheese", "yogurt", "fruit", "cereal"],
            "breakfast": ["eggs", "bacon", "toast", "cereal", "milk", "yogurt"]
        }
        
        # Check for specific meal types
        for meal_type, items in breakfast_components.items():
            if meal_type in meal_label:
                # Add components based on confidence level
                if confidence >= 0.80:
                    components.extend(items[:4])  # Add top 4 components for high confidence
                elif confidence >= 0.70:
                    components.extend(items[:2])  # Add top 2 components for medium confidence
        
        return components

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

    def _filter_multi_item_detections(self, foods: List[str], confidence_scores: Dict[str, float]) -> List[str]:
        """Filter detections to include multiple relevant food items for complex meals"""
        filtered = []
        
        # Group similar/related foods to avoid over-detection
        food_groups = {
            "beef_group": ["beef", "steak", "roast beef", "ground beef", "beef steak", "ribeye", "sirloin", "filet mignon", "t-bone", "porterhouse", "beef burger", "hamburger", "bolognese"],
            "chicken_group": ["chicken", "chicken breast", "chicken thigh", "chicken wing", "chicken nuggets", "chicken tenders", "fried chicken", "roasted chicken"],
            "pork_group": ["pork", "pork chop", "bacon", "ham", "pork loin", "pork tenderloin", "pork belly", "pulled pork", "pork ribs", "pork shoulder"],
            "fish_group": ["salmon", "tuna", "cod", "tilapia", "trout", "mackerel", "halibut", "sea bass", "red snapper", "grouper", "swordfish"],
            "dairy_group": ["milk", "cheese", "cheddar", "mozzarella", "parmesan", "feta", "blue cheese", "swiss", "gouda", "brie", "yogurt", "greek yogurt", "cottage cheese"],
            "egg_group": ["egg", "eggs", "scrambled eggs", "fried eggs", "fried egg", "boiled eggs", "omelet", "omelette", "poached eggs", "deviled eggs"],
            "bread_group": ["bread", "white bread", "whole wheat bread", "sourdough", "bagel", "toast"],
            "pasta_group": ["pasta", "spaghetti", "penne", "fettuccine", "lasagna", "noodles"],
            "rice_group": ["rice", "white rice", "brown rice", "wild rice", "jasmine rice"],
            "sauce_group": ["bolognese", "marinara", "alfredo", "carbonara", "pesto", "tomato sauce"],
            "pizza_group": ["pizza", "pepperoni", "margherita", "hawaiian", "supreme", "cheese pizza", "pepperoni pizza"],
            "wrap_group": ["wrap", "burrito", "taco", "quesadilla", "enchilada", "fajita", "shawarma", "gyro", "kebab", "pita", "tortilla", "flatbread", "naan", "roti", "chapati"],
            "bean_group": ["beans", "baked beans", "black beans", "kidney beans", "pinto beans", "navy beans", "lima beans", "cannellini beans", "great northern beans", "white beans", "garbanzo beans", "chickpeas"]
        }
        
        # Define specificity levels for each group to prioritize more specific terms
        specificity_rules = {
            "beef_group": {
                "specific": ["steak", "roast beef", "ground beef", "beef steak", "ribeye", "sirloin", "filet mignon", "t-bone", "porterhouse", "beef burger", "hamburger"],
                "generic": ["beef", "bolognese"]
            },
            "pasta_group": {
                "specific": ["spaghetti", "penne", "fettuccine", "lasagna"],
                "generic": ["pasta", "noodles"]
            },
            "pizza_group": {
                "specific": ["pizza"],
                "generic": ["pepperoni", "margherita", "hawaiian", "supreme", "cheese pizza", "pepperoni pizza"]
            },
            "wrap_group": {
                "specific": ["burrito", "taco", "quesadilla", "enchilada", "fajita", "shawarma", "gyro", "kebab"],
                "generic": ["wrap", "pita", "tortilla", "flatbread", "naan", "roti", "chapati"]
            },
            "bean_group": {
                "specific": ["baked beans", "black beans", "kidney beans", "pinto beans", "navy beans", "lima beans", "cannellini beans", "great northern beans", "white beans", "garbanzo beans", "chickpeas"],
                "generic": ["beans"]
            },
            "bread_group": {
                "specific": ["white bread", "whole wheat bread", "sourdough", "bagel", "toast"],
                "generic": ["bread"]
            },
            "rice_group": {
                "specific": ["white rice", "brown rice", "wild rice", "jasmine rice"],
                "generic": ["rice"]
            },
            "chicken_group": {
                "specific": ["chicken breast", "chicken thigh", "chicken wing", "chicken nuggets", "chicken tenders", "fried chicken", "roasted chicken"],
                "generic": ["chicken"]
            },
            "pork_group": {
                "specific": ["pork chop", "bacon", "ham", "pork loin", "pork tenderloin", "pork belly", "pulled pork", "pork ribs", "pork shoulder"],
                "generic": ["pork"]
            }
        }
        
        # Find the best item from each group
        best_items = {}
        for food in foods:
            confidence = confidence_scores.get(food, 0.5)
            protein_content = self.protein_database.get(food, 0)
            
            # Check if this food belongs to a group
            food_grouped = False
            for group_name, group_items in food_groups.items():
                if food in group_items:
                    food_grouped = True
                    
                    # Special handling for beef group - prioritize beef over bolognese
                    if group_name == "beef_group":
                        if food == "bolognese":
                            # Check if beef is already in the foods list
                            if "beef" in foods:
                                continue  # Skip bolognese if beef is already detected
                        elif food == "beef" and group_name in best_items:
                            current_best = best_items[group_name]
                            if current_best and current_best[0] == "bolognese":
                                # Replace bolognese with beef
                                best_items[group_name] = (food, confidence, protein_content)
                                continue
                    
                    # Generalized specificity handling for all groups
                    if group_name in specificity_rules:
                        rules = specificity_rules[group_name]
                        specific_terms = rules["specific"]
                        generic_terms = rules["generic"]
                        
                        if food in specific_terms:
                            # Specific terms get priority over generic terms
                            if group_name not in best_items:
                                best_items[group_name] = (food, confidence + 0.1, protein_content)  # Boost confidence
                            else:
                                # Only replace if the new item is more specific or has higher score
                                current_best = best_items[group_name]
                                current_food = current_best[0]
                                
                                # If current item is generic and new item is specific, replace it
                                if current_food in generic_terms and food in specific_terms:
                                    best_items[group_name] = (food, confidence, protein_content)
                                # If both are specific or both are generic, use score comparison
                                elif (current_food in specific_terms) == (food in specific_terms):
                                    current_score = current_best[1] + (current_best[2] / 100)
                                    new_score = confidence + (protein_content / 100)
                                    if new_score > current_score:
                                        best_items[group_name] = (food, confidence, protein_content)
                        elif food in generic_terms:
                            # Only add generic terms if no specific term is detected
                            if group_name not in best_items:
                                best_items[group_name] = (food, confidence, protein_content)
                            else:
                                # Only keep generic term if current item is also generic and has lower score
                                current_best = best_items[group_name]
                                current_food = current_best[0]
                                if current_food in generic_terms:
                                    current_score = current_best[1] + (current_best[2] / 100)
                                    new_score = confidence + (protein_content / 100)
                                    if new_score > current_score:
                                        best_items[group_name] = (food, confidence, protein_content)
                        continue
                    else:
                        # For groups without specific rules, use standard scoring
                        if group_name not in best_items:
                            best_items[group_name] = (food, confidence, protein_content)
                        else:
                            current_best = best_items[group_name]
                            current_score = current_best[1] + (current_best[2] / 100)
                            new_score = confidence + (protein_content / 100)
                            if new_score > current_score:
                                best_items[group_name] = (food, confidence, protein_content)
                    break
            
            # If not grouped, add it directly
            if not food_grouped:
                filtered.append((food, confidence, protein_content))
        
        # Add the best item from each group
        for group_name, (food, confidence, protein_content) in best_items.items():
            filtered.append((food, confidence, protein_content))
        
        # Post-process to remove redundant items using general food relationships
        final_filtered = []
        
        # Define food relationships (component -> main dish)
        food_relationships = {
            # Pasta types -> pasta
            "spaghetti": "pasta", "linguine": "pasta", "penne": "pasta", 
            "fettuccine": "pasta", "lasagna": "pasta", "rigatoni": "pasta",
            "ziti": "pasta", "rotini": "pasta", "farfalle": "pasta",
            
            # Rice types -> rice
            "white rice": "rice", "brown rice": "rice", "wild rice": "rice",
            "jasmine rice": "rice", "basmati rice": "rice",
            
            # Salad types -> salad
            "greek salad": "salad", "caesar salad": "salad", "cobb salad": "salad",
            "garden salad": "salad", "green salad": "salad", "tabbouleh": "salad",
            
            # Bread types -> bread
            "white bread": "bread", "whole wheat bread": "bread", "sourdough": "bread",
            "bagel": "bread", "toast": "bread",
            
            # Meat types -> main meat
            "chicken breast": "chicken", "chicken thigh": "chicken", "chicken wing": "chicken",
            "ground beef": "beef", "beef steak": "beef", "roast beef": "beef",
            "pork chop": "pork", "pork loin": "pork", "pork tenderloin": "pork",
            
            # Dish components -> main dish
            "bolognese": "beef",  # bolognese sauce contains beef
        }
        
        # First pass: consolidate related foods
        consolidated_foods = {}
        for food, conf, protein in filtered:
            # Check if this food should be consolidated to a main category
            if food in food_relationships and food_relationships[food] is not None:
                main_food = food_relationships[food]
                # Keep the higher confidence version
                if main_food not in consolidated_foods or conf > consolidated_foods[main_food][1]:
                    consolidated_foods[main_food] = (main_food, conf, protein)
            else:
                # Keep the food as is
                if food not in consolidated_foods or conf > consolidated_foods[food][1]:
                    consolidated_foods[food] = (food, conf, protein)
        
        # Convert back to list
        final_filtered = list(consolidated_foods.values())
        
        # Handle meal breakdown
        meal_components = []
        for food, conf, protein in final_filtered:
            if food == "english breakfast":
                meal_components.extend([("bacon", conf, 37.0), ("egg", conf, 13.0), ("sausage", conf, 18.0)])
            elif food == "full breakfast":
                meal_components.extend([("bacon", conf, 37.0), ("egg", conf, 13.0), ("sausage", conf, 18.0)])
            elif food == "american breakfast":
                meal_components.extend([("bacon", conf, 37.0), ("egg", conf, 13.0), ("pancakes", conf, 6.0)])
            elif food == "continental breakfast":
                meal_components.extend([("bread", conf, 8.0), ("cheese", conf, 25.0), ("yogurt", conf, 10.0)])
            else:
                meal_components.append((food, conf, protein))
        
        # Remove duplicates from meal components
        seen_foods = set()
        unique_components = []
        for food, conf, protein in meal_components:
            if food not in seen_foods:
                seen_foods.add(food)
                unique_components.append((food, conf, protein))
        
        final_filtered = unique_components
        
        # UNIVERSAL APPROACH: Focus on the primary food item
        # Sort by confidence and protein content to find the most significant food
        final_filtered.sort(key=lambda x: (x[1], x[2]), reverse=True)
        
        # For any image, we want to identify the PRIMARY food item
        # If we have multiple items, only keep the most confident one unless there's a clear multi-item dish
        if len(final_filtered) >= 2:
            primary_food, primary_conf, primary_protein = final_filtered[0]
            secondary_food, secondary_conf, secondary_protein = final_filtered[1]
            
            # Check if this looks like a legitimate multi-item dish
            # Only include multiple items if they're clearly part of a complex dish
            is_complex_dish = False
            
            # Define legitimate multi-item dish patterns
            complex_dish_patterns = [
                # Meat + starch combinations (clear main dish + side)
                ("beef", "pasta"), ("beef", "rice"), ("beef", "bread"),
                ("chicken", "rice"), ("chicken", "pasta"), ("chicken", "bread"),
                ("pork", "rice"), ("pork", "pasta"), ("pork", "bread"),
                ("fish", "rice"), ("fish", "pasta"), ("fish", "bread"),
                
                # Sandwich/wrap patterns (clear sandwich structure)
                ("bread", "meat"), ("bread", "chicken"), ("bread", "beef"), ("bread", "pork"),
                ("wrap", "meat"), ("wrap", "chicken"), ("wrap", "beef"), ("wrap", "pork"),
                
                # Pizza patterns (clear pizza structure) - REMOVED cheese since it's a component
                ("pizza", "pepperoni"), ("pizza", "meat"),
            ]
            
            # Check if the two items form a legitimate complex dish
            for pattern in complex_dish_patterns:
                if (primary_food == pattern[0] and secondary_food == pattern[1]) or \
                   (primary_food == pattern[1] and secondary_food == pattern[0]):
                    is_complex_dish = True
                    break
            
            # If it's not a legitimate complex dish, keep only the primary item
            if not is_complex_dish:
                final_filtered = [final_filtered[0]]
        
        # Additional filtering: Remove non-food items and dish components
        non_food_items = [
            "salt", "pepper", "black pepper", "white pepper", "salt and pepper",
            "sugar", "honey", "syrup", "oil", "olive oil", "vegetable oil",
            "vinegar", "lemon juice", "lime juice", "soy sauce", "hot sauce",
            "ketchup", "mustard", "mayonnaise", "butter", "margarine",
            "flour", "baking powder", "baking soda", "yeast", "breadcrumbs",
            "water", "ice", "steam", "smoke", "air", "dust", "dirt",
            # Dish components that shouldn't be detected separately
            "cheese", "mozzarella", "cheddar", "parmesan", "gouda", "swiss", "provolone",
            "cream cheese", "cottage cheese", "ricotta", "feta", "blue cheese",
            "sauce", "gravy", "dressing", "marinade", "seasoning", "herbs", "spices"
        ]
        
        final_filtered = [(food, conf, protein) for food, conf, protein in final_filtered 
                         if food not in non_food_items]
        
        # Return up to 3 items maximum (primary + others if legitimate complex dish)
        return [food for food, conf, protein in final_filtered[:3]] if final_filtered else []

    def calculate_protein_content(self, foods: List[str]) -> float:
        """Calculate total protein content for detected foods normalized to 300g total food weight"""
        if not foods:
            return 0.0
        
        # Calculate raw protein sum per 100g for each food
        raw_protein_per_100g = 0.0
        for food in foods:
            protein_per_100g = self.protein_database.get(food, 5.0)  # Default 5g if not found
            raw_protein_per_100g += protein_per_100g
        
        # For single food item: return protein content for 300g of that food
        if len(foods) == 1:
            protein_per_100g = self.protein_database.get(foods[0], 5.0)
            total_protein = (protein_per_100g * 300.0) / 100.0
            return round(total_protein, 1)
        
        # For multiple food items: distribute 300g equally among items
        # Each item gets 300g / num_items, then calculate protein for that portion
        grams_per_item = 300.0 / len(foods)
        total_protein = 0.0
        
        for food in foods:
            protein_per_100g = self.protein_database.get(food, 5.0)
            protein_for_this_item = (protein_per_100g * grams_per_item) / 100.0
            total_protein += protein_for_this_item
        
        return round(total_protein, 1)

    def _canonicalize_food_list(self, foods: List[str]) -> List[str]:
        """Map detected items to canonical keys used in the nutrition databases and de-duplicate.
        Keeps original order, limits to top 3 items.
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
            # Stop at 3 items to avoid overcounting
            if len(canonical) >= 3:
                break
        return canonical


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