from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Depends, Query
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import FileResponse, HTMLResponse
from sqlmodel import SQLModel, create_engine, Session, select, Field, func
from sqlalchemy import text
from typing import List, Optional
import os
from datetime import datetime, timedelta
import json
import hashlib
import secrets
import smtplib
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import re

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    import os
    # Check if .env file exists before loading
    if os.path.exists('.env'):
        load_dotenv()
        print("✅ Loaded environment variables from .env file")
    else:
        print("ℹ️  No .env file found. Using default environment variables.")
except ImportError:
    print("Warning: python-dotenv not installed. Install with: pip install python-dotenv")

# Configure email settings (you'll need to set these environment variables)
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
APP_BASE_URL = os.getenv("APP_BASE_URL", "http://127.0.0.1:8000")

# Import Google Vision food detection (REST via requests; no heavy client required)
try:
    from food_detection import identify_food_with_google_vision, identify_food_local
    
    # Check for Google Vision credentials in environment variables (Render-friendly)
    GOOGLE_SERVICE_ACCOUNT_JSON = os.getenv("GOOGLE_SERVICE_ACCOUNT")
    GOOGLE_VISION_SERVICE_ACCOUNT_PATH = os.getenv("GOOGLE_VISION_SERVICE_ACCOUNT_PATH")
    
    # Try environment variable first (recommended for Render), then file path
    if GOOGLE_SERVICE_ACCOUNT_JSON:
        try:
            import json
            service_account_info = json.loads(GOOGLE_SERVICE_ACCOUNT_JSON)
            GOOGLE_VISION_AVAILABLE = True
            print("✅ Google Vision API configured (environment variable)")
        except (json.JSONDecodeError, KeyError) as e:
            print(f"❌ Invalid Google Vision service account JSON: {e}")
            GOOGLE_VISION_AVAILABLE = False
    elif GOOGLE_VISION_SERVICE_ACCOUNT_PATH and os.path.exists(GOOGLE_VISION_SERVICE_ACCOUNT_PATH):
        GOOGLE_VISION_AVAILABLE = True
        print(f"✅ Google Vision API configured (service account file: {GOOGLE_VISION_SERVICE_ACCOUNT_PATH})")
    else:
        GOOGLE_VISION_AVAILABLE = False
        print("ℹ️  Google Vision API not configured. Set GOOGLE_SERVICE_ACCOUNT environment variable or GOOGLE_VISION_SERVICE_ACCOUNT_PATH file path.")
        
except ImportError:
    GOOGLE_VISION_AVAILABLE = False
    print("Warning: food_detection module not importable. Ensure the file exists.")

# For backward compatibility
LOCAL_AI_AVAILABLE = GOOGLE_VISION_AVAILABLE

# Enhanced protein database (values per 100g); optimized for realistic 250g portions
PROTEIN_DATABASE = {
    # Meats & Poultry (realistic values for typical servings)
    "chicken": 31.0, "chicken breast": 31.0, "chicken thigh": 28.0, "chicken wing": 30.0,
    "beef": 26.0, "steak": 26.0, "ground beef": 26.0, "beef burger": 26.0, "burger": 26.0,
    "pork": 25.0, "pork chop": 25.0, "bacon": 37.0, "ham": 22.0, "sausage": 18.0,
    "salmon": 20.0, "tuna": 30.0, "cod": 18.0, "tilapia": 26.0, "fish": 20.0,
    "turkey": 29.0, "duck": 23.0, "lamb": 25.0, "shrimp": 24.0, "prawns": 24.0,
    
    # Dairy & Eggs (adjusted for realistic portions)
    "egg": 13.0, "eggs": 13.0, "milk": 3.4, "cheese": 25.0, "cheddar": 25.0,
    "yogurt": 10.0, "greek yogurt": 10.0, "cottage cheese": 11.0, "cream cheese": 6.0,
    
    # Nuts & Seeds (high density foods - realistic for smaller portions)
    "peanut butter": 25.0, "almonds": 21.0, "walnuts": 15.0, "cashews": 18.0,
    "sunflower seeds": 21.0, "chia seeds": 17.0, "pumpkin seeds": 19.0,
    
    # Plant-based Proteins
    "tofu": 8.0, "tempeh": 20.0, "lentils": 9.0, "beans": 9.0, "black beans": 9.0,
    "kidney beans": 9.0, "chickpeas": 9.0, "edamame": 11.0, "hummus": 8.0,
    
    # Grains & Cereals (adjusted for realistic portions)
    "quinoa": 14.0, "rice": 2.7, "brown rice": 2.7, "bread": 9.0, "whole wheat bread": 13.0,
    "pasta": 5.5, "spaghetti": 5.5, "oatmeal": 6.0, "oats": 6.0, "cereal": 10.0,
    
    # Vegetables (low density - realistic for larger portions)
    "broccoli": 2.8, "spinach": 2.9, "kale": 4.3, "asparagus": 2.2, "brussels sprouts": 3.4,
    "cauliflower": 1.9, "peas": 5.4, "corn": 3.2, "potato": 2.0, "sweet potato": 1.6,
    
    # Fast Food & Common Meals (adjusted for realistic serving sizes)
    "pizza": 10.0, "pizza slice": 10.0, "hamburger": 18.0, "hot dog": 12.0,
    "sandwich": 12.0, "wrap": 12.0, "taco": 12.0, "burrito": 15.0,
    "noodles": 5.5, "ramen": 5.5, "soup": 2.0, "salad": 2.0,
    
    # Breakfast Foods
    "pancakes": 6.0, "waffles": 6.0, "french toast": 8.0, "bagel": 10.0,
    "muffin": 5.0, "croissant": 8.0, "english muffin": 8.0,
    
    # Snacks & Others (adjusted for realistic portions)
    "protein bar": 20.0, "protein shake": 7.0, "smoothie": 2.0,
    "ice cream": 4.0, "chocolate": 5.0, "cookies": 5.0, "cake": 4.0
}

# Enhanced calorie database (values per 100g); optimized for realistic 250g portions
CALORIE_DATABASE = {
    # Meats & Poultry (realistic values for typical servings)
    "chicken": 165, "chicken breast": 165, "chicken thigh": 209, "chicken wing": 290,
    "beef": 250, "steak": 250, "ground beef": 250, "beef burger": 250, "burger": 250,
    "pork": 242, "pork chop": 242, "bacon": 541, "ham": 145, "sausage": 296,
    "salmon": 208, "tuna": 144, "cod": 105, "tilapia": 96, "fish": 208,
    "turkey": 189, "duck": 337, "lamb": 294, "shrimp": 99, "prawns": 99,
    
    # Dairy & Eggs (realistic values)
    "egg": 155, "eggs": 155, "milk": 42, "cheese": 402, "cheddar": 402,
    "yogurt": 59, "greek yogurt": 59, "cottage cheese": 98, "cream cheese": 342,
    
    # Nuts & Seeds (high density - realistic for smaller portions)
    "peanut butter": 588, "almonds": 579, "walnuts": 654, "cashews": 553,
    "sunflower seeds": 584, "chia seeds": 486, "pumpkin seeds": 559,
    
    # Plant-based Proteins
    "tofu": 76, "tempeh": 192, "lentils": 116, "beans": 116, "black beans": 116,
    "kidney beans": 116, "chickpeas": 164, "edamame": 121, "hummus": 166,
    
    # Grains & Cereals (adjusted for realistic portions)
    "quinoa": 120, "rice": 130, "brown rice": 111, "bread": 265, "whole wheat bread": 247,
    "pasta": 158, "spaghetti": 158, "oatmeal": 68, "oats": 68, "cereal": 378,
    
    # Vegetables (low density - realistic for larger portions)
    "broccoli": 34, "spinach": 23, "kale": 49, "asparagus": 20, "brussels sprouts": 43,
    "cauliflower": 25, "peas": 84, "corn": 86, "potato": 77, "sweet potato": 86,
    
    # Fast Food & Common Meals (adjusted for realistic serving sizes)
    "pizza": 266, "pizza slice": 266, "hamburger": 295, "hot dog": 151,
    "sandwich": 250, "wrap": 250, "taco": 226, "burrito": 300,
    "noodles": 158, "ramen": 158, "soup": 35, "salad": 25,
    
    # Breakfast Foods
    "pancakes": 227, "waffles": 291, "french toast": 229, "bagel": 245,
    "muffin": 265, "croissant": 406, "english muffin": 157,
    
    # Snacks & Others (adjusted for realistic portions)
    "protein bar": 350, "protein shake": 80, "smoothie": 40,
    "ice cream": 207, "chocolate": 545, "cookies": 502, "cake": 257
}

# Database setup with optimized settings for multiple users
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./protein_app.db?check_same_thread=False")
engine = create_engine(
    DATABASE_URL,
    echo=False,
    connect_args={
        "check_same_thread": False,
        "timeout": 30,
    },
    # SQLite uses NullPool; pooling args like pool_size/max_overflow are not supported
    pool_pre_ping=True,
)

# Security
security = HTTPBearer()

# Simple in-memory cache for performance optimization
import threading
from collections import OrderedDict

class SimpleCache:
    def __init__(self, max_size=1000):
        self.max_size = max_size
        self.cache = OrderedDict()
        self.lock = threading.Lock()
    
    def get(self, key):
        with self.lock:
            if key in self.cache:
                # Move to end (most recently used)
                value = self.cache.pop(key)
                self.cache[key] = value
                return value
            return None
    
    def set(self, key, value, ttl=300):  # 5 minutes default TTL
        with self.lock:
            if key in self.cache:
                self.cache.pop(key)
            elif len(self.cache) >= self.max_size:
                # Remove least recently used
                self.cache.popitem(last=False)
            
            self.cache[key] = {
                'value': value,
                'expires_at': time.time() + ttl
            }
    
    def cleanup(self):
        """Remove expired entries"""
        with self.lock:
            current_time = time.time()
            expired_keys = [
                key for key, data in self.cache.items()
                if data['expires_at'] < current_time
            ]
            for key in expired_keys:
                self.cache.pop(key, None)

# Global cache instance
cache = SimpleCache()

# Models
class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True)
    email: str = Field(unique=True, index=True)
    password_hash: str
    weight_kg: Optional[float] = Field(default=None)
    protein_goal: Optional[float] = Field(default=None)
    calorie_goal: Optional[float] = Field(default=None)  # Added calorie goal field
    activity_level: Optional[str] = Field(default="moderate")  # Added activity level field
    last_weight_update: Optional[datetime] = Field(default=None)
    email_verified: bool = Field(default=False)
    verification_token: Optional[str] = Field(default=None)
    profile_picture_path: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.now)

class Meal(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    image_path: str
    food_items: str
    total_protein: float
    total_calories: float
    created_at: datetime = Field(default_factory=datetime.now)

from contextlib import asynccontextmanager

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
    
    # Create additional indexes for better performance
    with Session(engine) as session:
        # Create index on user_id and created_at for meals (most common query)
        session.exec(text("CREATE INDEX IF NOT EXISTS idx_meals_user_created ON meal (user_id, created_at)"))
        # Create index on created_at for date filtering
        session.exec(text("CREATE INDEX IF NOT EXISTS idx_meals_created_at ON meal (created_at)"))
        # Create index on user_id for user-specific queries
        session.exec(text("CREATE INDEX IF NOT EXISTS idx_meals_user_id ON meal (user_id)"))
        session.commit()

# Background cleanup functions (disabled for now to fix startup issues)
async def cleanup_old_meals():
    """Background task to clean up old meal images and data"""
    pass  # Disabled for now

async def cleanup_cache():
    """Background task to clean up expired cache entries"""
    pass  # Disabled for now

# Create FastAPI app
app = FastAPI(title="Protein Tracking App", version="4.0.0")

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    create_db_and_tables()

# Add CORS middleware (no credentials; supports file:// origins)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_origin_regex=r".*",
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"]
)

def hash_password(password: str) -> str:
    """Hash a password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its hash"""
    return hash_password(password) == hashed

def generate_verification_token() -> str:
    """Generate a random verification token"""
    return secrets.token_urlsafe(32)

def calculate_protein_goal(weight_kg: float, activity_level: str = "moderate") -> float:
    """Calculate protein goal based on weight and activity level"""
    # Calculate protein needs based on activity level (g per kg body weight)
    protein_multipliers = {
        'sedentary': 0.8,
        'light': 1.0,
        'moderate': 1.2,
        'active': 1.6,
        'athlete': 2.0
    }
    
    multiplier = protein_multipliers.get(activity_level, 1.2)
    return round(weight_kg * multiplier, 1)

def calculate_calorie_goal(weight_kg: float, activity_level: str = "moderate") -> float:
    """Calculate calorie goal based on weight and activity level"""
    # Calculate BMR using Mifflin-St Jeor Equation
    # BMR = 10 × weight(kg) + 6.25 × height(cm) - 5 × age(y) + 5 (for men)
    # For simplicity, we'll use a simplified calculation based on weight and activity level
    
    # Base calorie needs per kg of body weight
    calorie_multipliers = {
        'sedentary': 25,      # Little to no exercise
        'light': 30,          # Light exercise 1-3 days/week
        'moderate': 35,       # Moderate exercise 3-5 days/week
        'active': 40,         # Hard exercise 6-7 days/week
        'athlete': 45         # Very hard exercise, physical job
    }
    
    multiplier = calorie_multipliers.get(activity_level, 35)
    return round(weight_kg * multiplier, 0)

def is_valid_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def send_verification_email(email: str, username: str, token: str):
    """Send verification email with professional HTML template"""
    if not SMTP_USERNAME or not SMTP_PASSWORD:
        print(f"⚠️  Email verification not configured!")
        print(f"   For user {username} ({email}), verification token: {token}")
        print(f"   To enable email verification, run: python setup_env.py")
        return False
    
    try:
        msg = MIMEMultipart('alternative')
        msg['From'] = f"KthizaTrack <{SMTP_USERNAME}>"
        msg['To'] = email
        msg['Subject'] = "Welcome to KthizaTrack - Verify Your Account"
        
        verification_url = f"{APP_BASE_URL.rstrip('/')}/auth/verify/{token}"
        
        # Plain text version
        text_body = f"""
Hello {username}!

Welcome to KthizaTrack! 🎉

Please verify your email address by clicking the link below:

{verification_url}

This verification link will expire in 24 hours.

If you didn't create this account, please ignore this email.

Best regards,
The KthizaTrack Team

---
KthizaTrack - Your Personal Nutrition Assistant
        """
        
        # HTML version with professional styling and button
        html_body = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Verify Your KthizaTrack Account</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f8f9fa;
        }}
        .email-container {{
            background-color: #ffffff;
            border-radius: 12px;
            padding: 40px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }}
        .header {{
            text-align: center;
            margin-bottom: 30px;
        }}
        .logo {{
            font-size: 28px;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 10px;
        }}
        .subtitle {{
            color: #7f8c8d;
            font-size: 16px;
        }}
        .welcome-text {{
            font-size: 18px;
            color: #2c3e50;
            margin-bottom: 25px;
        }}
        .verification-section {{
            background-color: #f8f9fa;
            border-radius: 8px;
            padding: 25px;
            margin: 25px 0;
            text-align: center;
        }}
        .verify-button {{
            display: inline-block;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px 30px;
            text-decoration: none;
            border-radius: 25px;
            font-weight: bold;
            font-size: 16px;
            margin: 20px 0;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
            transition: all 0.3s ease;
        }}
        .verify-button:hover {{
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
        }}
        .fallback-link {{
            color: #667eea;
            text-decoration: none;
            font-size: 14px;
            word-break: break-all;
        }}
        .footer {{
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #ecf0f1;
            text-align: center;
            color: #7f8c8d;
            font-size: 14px;
        }}
        .warning {{
            background-color: #fff3cd;
            border: 1px solid #ffeaa7;
            border-radius: 6px;
            padding: 15px;
            margin: 20px 0;
            color: #856404;
        }}
        .emoji {{
            font-size: 20px;
        }}
    </style>
</head>
<body>
    <div class="email-container">
        <div class="header">
            <div class="logo">🍗 KthizaTrack</div>
            <div class="subtitle">Your Personal Nutrition Assistant</div>
        </div>
        
        <div class="welcome-text">
            Hello <strong>{username}</strong>! <span class="emoji">👋</span>
        </div>
        
        <p>Welcome to KthizaTrack! We're excited to have you on board. <span class="emoji">🎉</span></p>
        
        <p>To get started and access all the amazing features of your personal nutrition assistant, please verify your email address by clicking the button below:</p>
        
        <div class="verification-section">
            <a href="{verification_url}" class="verify-button">
                ✅ Verify My Account
            </a>
            
            <p style="margin-top: 20px; font-size: 14px; color: #7f8c8d;">
                If the button doesn't work, copy and paste this link into your browser:
            </p>
            <a href="{verification_url}" class="fallback-link">{verification_url}</a>
        </div>
        
        <div class="warning">
            <strong>⚠️ Important:</strong> This verification link will expire in 24 hours for your security.
        </div>
        
        <div class="warning" style="background-color: #e3f2fd; border-color: #2196f3; color: #1565c0;">
            <strong>💻 Development Note:</strong> This is a local development server. Make sure the KthizaTrack app is running on your computer before clicking the verification link.
        </div>
        
        <p>If you didn't create this account, please ignore this email. Your email address will not be used for any other purpose.</p>
        
        <div class="footer">
                    <p>Best regards,<br>
        <strong>The KthizaTrack Team</strong></p>
        
        <p style="margin-top: 20px;">
            🍗 KthizaTrack - Track your nutrition, achieve your goals
        </p>
        </div>
    </div>
</body>
</html>
        """
        
        # Attach both plain text and HTML versions
        msg.attach(MIMEText(text_body, 'plain'))
        msg.attach(MIMEText(html_body, 'html'))
        
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=10) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)
        print(f"✅ Verification email sent to {email}")
        return True
    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        return False

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """Get current user from token"""
    token = credentials.credentials
    print(f"🔐 Authentication attempt with token: {token}")
    
    with Session(engine) as session:
        # For now, we'll use a simple token system
        # In production, you'd want to use JWT tokens
        # Token is a simple user id string for now; guard cast
        try:
            user_id = int(token)
            print(f"🔐 Parsed user_id: {user_id}")
        except ValueError:
            print(f"❌ Invalid token format: {token}")
            raise HTTPException(status_code=401, detail="Invalid token format")
        
        user = session.exec(select(User).where(User.id == user_id)).first()
        if not user:
            print(f"❌ User not found for id: {user_id}")
            raise HTTPException(status_code=401, detail="Invalid token")
        
        print(f"✅ Authenticated user: {user.username} (ID: {user.id})")
        return user

def calculate_protein_enhanced(food_items: List[str]) -> tuple[float, List[str]]:
    """Calculate total protein content for detected foods with realistic portion sizing"""
    matched_foods = []
    
    # For single food item: use realistic portion sizing
    if len(food_items) == 1:
        food_lower = food_items[0].lower().strip()
        protein_per_100g = 0.0
        
        if food_lower in PROTEIN_DATABASE:
            protein_per_100g = PROTEIN_DATABASE[food_lower]
            matched_foods.append(food_items[0])
            print(f"   ✅ Matched '{food_items[0]}' -> {protein_per_100g}g protein/100g")
        else:
            # Try to find a match
            for db_item, protein_value in PROTEIN_DATABASE.items():
                if db_item in food_lower or food_lower in db_item:
                    protein_per_100g = protein_value
                    matched_foods.append(food_items[0])
                    print(f"   ✅ Matched '{food_items[0]}' -> {protein_value}g protein/100g (via '{db_item}')")
                    break
            if protein_per_100g == 0.0:
                protein_per_100g = _estimate_protein_from_food_name(food_lower)
                print(f"   ⚠️  No exact match for '{food_items[0]}' -> {protein_per_100g}g protein/100g (estimated)")
        
        # Calculate realistic portion size based on food density
        realistic_portion = _get_realistic_portion_size(food_lower)
        total_protein = (protein_per_100g * realistic_portion) / 100.0
        
        print(f"📊 Single food item: {food_items[0]}, {realistic_portion}g (realistic portion)")
        print(f"📊 Protein calculation: {total_protein:.1f}g from {realistic_portion}g of {food_items[0]}")
        return round(total_protein, 1), matched_foods
    
    # For multiple food items: use weighted distribution based on food density
    total_weight = 0.0
    food_weights = {}
    
    # Calculate appropriate weights for each food item
    for food_item in food_items:
        food_lower = food_item.lower().strip()
        realistic_portion = _get_realistic_portion_size(food_lower)
        food_weights[food_item] = realistic_portion
        total_weight += realistic_portion
    
    # Normalize to 350g total
    if total_weight > 0:
        scale_factor = 350.0 / total_weight
        for food_item in food_weights:
            food_weights[food_item] *= scale_factor
    
    total_protein = 0.0
    
    for food_item in food_items:
        food_lower = food_item.lower().strip()
        protein_per_100g = 0.0
        portion_weight = food_weights.get(food_item, 250.0 / len(food_items))
        
        if food_lower in PROTEIN_DATABASE:
            protein_per_100g = PROTEIN_DATABASE[food_lower]
            matched_foods.append(food_item)
            print(f"   ✅ Matched '{food_item}' -> {protein_per_100g}g protein/100g")
        else:
            # Try to find a match
            for db_item, protein_value in PROTEIN_DATABASE.items():
                if db_item in food_lower or food_lower in db_item:
                    protein_per_100g = protein_value
                    matched_foods.append(food_item)
                    print(f"   ✅ Matched '{food_item}' -> {protein_value}g protein/100g (via '{db_item}')")
                    break
            if protein_per_100g == 0.0:
                protein_per_100g = _estimate_protein_from_food_name(food_lower)
                print(f"   ⚠️  No exact match for '{food_item}' -> {protein_per_100g}g protein/100g (estimated)")
        
        protein_for_this_item = (protein_per_100g * portion_weight) / 100.0
        total_protein += protein_for_this_item
        print(f"   📊 {food_item}: {portion_weight:.0f}g → {protein_for_this_item:.1f}g protein")
    
    print(f"📊 Multiple food items: {len(food_items)} items, {total_weight:.0f}g total → 350g normalized")
    print(f"📊 Protein calculation: {total_protein:.1f}g from 350g total")
    return round(total_protein, 1), matched_foods

def calculate_calories_enhanced(food_items: List[str]) -> tuple[float, List[str]]:
    """Calculate total calories for detected foods with realistic portion sizing"""
    matched_foods = []
    
    # For single food item: use realistic portion sizing
    if len(food_items) == 1:
        food_lower = food_items[0].lower().strip()
        calories_per_100g = 0.0
        
        if food_lower in CALORIE_DATABASE:
            calories_per_100g = CALORIE_DATABASE[food_lower]
            matched_foods.append(food_items[0])
            print(f"   ✅ Matched '{food_items[0]}' -> {calories_per_100g} calories/100g")
        else:
            # Try to find a match
            for db_item, calorie_value in CALORIE_DATABASE.items():
                if db_item in food_lower or food_lower in db_item:
                    calories_per_100g = calorie_value
                    matched_foods.append(food_items[0])
                    print(f"   ✅ Matched '{food_items[0]}' -> {calorie_value} calories/100g (via '{db_item}')")
                    break
            if calories_per_100g == 0.0:
                calories_per_100g = _estimate_calories_from_food_name(food_lower)
                print(f"   ⚠️  No exact match for '{food_items[0]}' -> {calories_per_100g} calories/100g (estimated)")
        
        # Calculate realistic portion size based on food density
        realistic_portion = _get_realistic_portion_size(food_lower)
        total_calories = (calories_per_100g * realistic_portion) / 100.0
        
        print(f"📊 Single food item: {food_items[0]}, {realistic_portion}g (realistic portion)")
        print(f"📊 Calorie calculation: {total_calories:.1f} calories from {realistic_portion}g of {food_items[0]}")
        return round(total_calories, 1), matched_foods
    
    # For multiple food items: use weighted distribution based on food density
    total_weight = 0.0
    food_weights = {}
    
    # Calculate appropriate weights for each food item
    for food_item in food_items:
        food_lower = food_item.lower().strip()
        realistic_portion = _get_realistic_portion_size(food_lower)
        food_weights[food_item] = realistic_portion
        total_weight += realistic_portion
    
    # Normalize to 350g total
    if total_weight > 0:
        scale_factor = 350.0 / total_weight
        for food_item in food_weights:
            food_weights[food_item] *= scale_factor
    
    total_calories = 0.0
    
    for food_item in food_items:
        food_lower = food_item.lower().strip()
        calories_per_100g = 0.0
        portion_weight = food_weights.get(food_item, 250.0 / len(food_items))
        
        if food_lower in CALORIE_DATABASE:
            calories_per_100g = CALORIE_DATABASE[food_lower]
            matched_foods.append(food_item)
            print(f"   ✅ Matched '{food_item}' -> {calories_per_100g} calories/100g")
        else:
            # Try to find a match
            for db_item, calorie_value in CALORIE_DATABASE.items():
                if db_item in food_lower or food_lower in db_item:
                    calories_per_100g = calorie_value
                    matched_foods.append(food_item)
                    print(f"   ✅ Matched '{food_item}' -> {calorie_value} calories/100g (via '{db_item}')")
                    break
            if calories_per_100g == 0.0:
                calories_per_100g = _estimate_calories_from_food_name(food_lower)
                print(f"   ⚠️  No exact match for '{food_item}' -> {calories_per_100g} calories/100g (estimated)")
        
        calories_for_this_item = (calories_per_100g * portion_weight) / 100.0
        total_calories += calories_for_this_item
        print(f"   📊 {food_item}: {portion_weight:.0f}g → {calories_for_this_item:.1f} calories")
    
    print(f"📊 Multiple food items: {len(food_items)} items, {total_weight:.0f}g total → 350g normalized")
    print(f"📊 Calorie calculation: {total_calories:.1f} calories from 350g total")
    return round(total_calories, 1), matched_foods

def _estimate_protein_from_food_name(food_name: str) -> float:
    """
    Estimate protein content based on food name patterns.
    Returns reasonable protein values for common foods not in the database.
    """
    food_name = food_name.lower()
    
    # Meat and protein-rich foods
    if any(word in food_name for word in ['meat', 'beef', 'steak', 'burger', 'patty', 'cutlet']):
        return 25.0
    elif any(word in food_name for word in ['chicken', 'poultry', 'breast', 'thigh', 'wing']):
        return 30.0
    elif any(word in food_name for word in ['fish', 'salmon', 'tuna', 'cod', 'seafood']):
        return 20.0
    elif any(word in food_name for word in ['pork', 'bacon', 'ham', 'sausage']):
        return 25.0
    elif any(word in food_name for word in ['egg', 'eggs']):
        return 13.0
    
    # Dairy products
    elif any(word in food_name for word in ['cheese', 'milk', 'yogurt', 'cream']):
        return 15.0
    
    # Grains and carbs
    elif any(word in food_name for word in ['bread', 'toast', 'sandwich', 'wrap']):
        return 10.0
    elif any(word in food_name for word in ['pasta', 'noodles', 'spaghetti', 'macaroni']):
        return 5.5
    elif any(word in food_name for word in ['rice', 'quinoa', 'oatmeal', 'cereal']):
        return 8.0
    elif any(word in food_name for word in ['pizza', 'slice']):
        return 10.0
    
    # Vegetables
    elif any(word in food_name for word in ['salad', 'vegetable', 'broccoli', 'spinach', 'kale']):
        return 2.0
    
    # Nuts and seeds
    elif any(word in food_name for word in ['nut', 'seed', 'almond', 'peanut']):
        return 20.0
    
    # Fast food and processed foods
    elif any(word in food_name for word in ['burger', 'hot dog', 'taco', 'burrito']):
        return 12.0
    elif any(word in food_name for word in ['fries', 'chips', 'snack']):
        return 5.0
    
    # Desserts and sweets
    elif any(word in food_name for word in ['cake', 'cookie', 'dessert', 'sweet', 'chocolate']):
        return 4.0
    
    # Default for unknown foods
    else:
        return 8.0  # Reasonable default for mixed/complex foods

def _estimate_calories_from_food_name(food_name: str) -> float:
    """
    Estimate calorie content based on food name patterns.
    Returns reasonable calorie values for common foods not in the database.
    """
    food_name = food_name.lower()
    
    # Meat and protein-rich foods
    if any(word in food_name for word in ['meat', 'beef', 'steak', 'burger', 'patty', 'cutlet']):
        return 250
    elif any(word in food_name for word in ['chicken', 'poultry', 'breast', 'thigh', 'wing']):
        return 165
    elif any(word in food_name for word in ['fish', 'salmon', 'tuna', 'cod', 'seafood']):
        return 200
    elif any(word in food_name for word in ['pork', 'bacon', 'ham', 'sausage']):
        return 250
    elif any(word in food_name for word in ['egg', 'eggs']):
        return 155
    
    # Dairy products
    elif any(word in food_name for word in ['milk', 'cheese', 'yogurt', 'cream']):
        return 100
    elif any(word in food_name for word in ['butter', 'margarine']):
        return 717
    
    # Grains and cereals
    elif any(word in food_name for word in ['bread', 'toast', 'sandwich', 'wrap']):
        return 250
    elif any(word in food_name for word in ['rice', 'pasta', 'noodles', 'spaghetti']):
        return 160
    elif any(word in food_name for word in ['oatmeal', 'oats', 'cereal']):
        return 100
    
    # Vegetables
    elif any(word in food_name for word in ['broccoli', 'spinach', 'kale', 'lettuce', 'salad']):
        return 25
    elif any(word in food_name for word in ['carrot', 'potato', 'sweet potato', 'corn']):
        return 80
    elif any(word in food_name for word in ['tomato', 'cucumber', 'pepper', 'onion']):
        return 20
    
    # Fruits
    elif any(word in food_name for word in ['apple', 'banana', 'orange', 'strawberry', 'berry']):
        return 50
    elif any(word in food_name for word in ['grape', 'pineapple', 'mango', 'peach']):
        return 60
    
    # Nuts and seeds
    elif any(word in food_name for word in ['nut', 'almond', 'walnut', 'cashew', 'seed']):
        return 600
    
    # Fast food and processed foods
    elif any(word in food_name for word in ['pizza', 'burger', 'hot dog', 'taco', 'burrito']):
        return 300
    elif any(word in food_name for word in ['fries', 'chips', 'crackers']):
        return 500
    
    # Desserts and sweets
    elif any(word in food_name for word in ['cake', 'cookie', 'dessert', 'sweet', 'chocolate']):
        return 400
    
    # Default for unknown foods
    else:
        return 150  # Reasonable default for mixed/complex foods

def _get_realistic_portion_size(food_name: str) -> float:
    """
    Returns realistic portion sizes in grams based on food density and typical serving sizes.
    This ensures that high-density foods (like nuts) get smaller portions and 
    low-density foods (like vegetables) get larger portions for a 250g total meal.
    """
    food_name = food_name.lower()
    
    # High-density foods (nuts, seeds, oils, etc.) - smaller portions
    if any(word in food_name for word in ['almond', 'walnut', 'cashew', 'peanut', 'nut', 'seed', 'chia', 'pumpkin', 'sunflower']):
        return 30.0  # 30g for nuts/seeds is a realistic serving
    
    # Very high-density foods (oils, butter, etc.)
    elif any(word in food_name for word in ['oil', 'butter', 'margarine']):
        return 15.0  # 15g for oils/fats
    
    # Medium-high density foods (cheese, bacon, etc.)
    elif any(word in food_name for word in ['cheese', 'cheddar', 'bacon', 'cream cheese']):
        return 50.0  # 50g for cheese
    
    # Steak gets a larger single-item portion
    elif 'steak' in food_name:
        return 250.0  # 250g for steak
    # Protein-rich foods (meats, fish, eggs) - moderate portions
    elif any(word in food_name for word in ['chicken', 'beef', 'pork', 'turkey', 'lamb', 'duck', 'salmon', 'tuna', 'fish', 'shrimp', 'prawn', 'egg']):
        return 150.0  # 150g for protein foods
    
    # Grains and carbs (pasta, rice, bread) - moderate portions
    elif any(word in food_name for word in ['pasta', 'spaghetti', 'rice', 'bread', 'quinoa', 'oatmeal', 'oats', 'cereal']):
        return 200.0  # 200g for grains
    
    # Fast food and mixed dishes - moderate portions
    elif any(word in food_name for word in ['pizza', 'burger', 'sandwich', 'wrap', 'taco', 'burrito', 'hot dog']):
        return 250.0  # 250g for complete meals
    
    # Low-density foods (vegetables, fruits) - larger portions
    elif any(word in food_name for word in ['broccoli', 'spinach', 'kale', 'asparagus', 'cauliflower', 'salad', 'vegetable', 'fruit', 'apple', 'banana']):
        return 300.0  # 300g for vegetables
    
    # Very low-density foods (soups, smoothies) - larger portions
    elif any(word in food_name for word in ['soup', 'smoothie']):
        return 400.0  # 400g for liquids
    
    # Default for unknown foods
    else:
        return 200.0  # 200g default

def _calculate_portion_multiplier(num_items: int) -> float:
    """
    Calculates a multiplier to adjust protein content for multi-item meals.
    Uses more realistic portion sizes for typical meal servings.
    """
    if num_items <= 1:
        return 1.0
    elif num_items == 2:
        return 0.65  # Each item gets about 65% of full portion
    elif num_items == 3:
        return 0.50  # Each item gets about 50% of full portion
    elif num_items == 4:
        return 0.35  # Each item gets about 35% of full portion
    elif num_items == 5:
        return 0.30  # Each item gets about 30% of full portion
    else:
        return 0.25  # Each item gets about 25% of full portion for very large meals

def identify_food_with_vision(image_path: str) -> List[str]:
    """Multi-item food detection using Google Vision API.
    
    This function uses Google Vision API with improved confidence thresholds
    to detect multiple food items in complex meals like English breakfast.
    """
    try:
        print(f"🔍 Starting multi-item food detection for image: {image_path}")
        detected_foods = identify_food_with_google_vision(image_path)
        print(f"🎯 Multi-Item Detection Results: {detected_foods}")
        return detected_foods or []
    except Exception as e:
        print(f"❌ Multi-item detection failed: {e}")
        # Return empty list instead of fallback - we want only AI detection
        return []

@app.get("/")
async def root():
    """Serve the professional landing page"""
    from fastapi.responses import FileResponse
    return FileResponse("static/index.html")

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.post("/auth/register")
async def register_user(
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...)
):
    # Validate inputs
    if len(username) < 3:
        raise HTTPException(status_code=400, detail="Username must be at least 3 characters")
    
    if len(password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
    
    if not is_valid_email(email):
        raise HTTPException(status_code=400, detail="Invalid email format")
    
    with Session(engine) as session:
        # Check if username or email already exists
        existing_user = session.exec(
            select(User).where((User.username == username) | (User.email == email))
        ).first()
        
        if existing_user:
            raise HTTPException(status_code=400, detail="Username or email already exists")
        
        # Create user without weight (will be set later)
        verification_token = generate_verification_token()
        password_hash = hash_password(password)
        
        # Check if email verification is configured
        email_configured = bool(SMTP_USERNAME and SMTP_PASSWORD)
        
        # Enforce email verification when configured
        if not email_configured:
            print("ℹ️  Email not configured; accounts will be auto-verified.")
        
        user = User(
            username=username,
            email=email,
            password_hash=password_hash,
            verification_token=verification_token,
            email_verified=not email_configured  # Only auto-verify if email not configured
        )
        
        session.add(user)
        session.commit()
        session.refresh(user)
        
        # Send verification email (if configured)
        email_sent = send_verification_email(email, username, verification_token) if email_configured else False
        
        response_message = "Account created successfully!"
        if email_configured and email_sent:
            response_message += " Please check your email to verify your account."
        else:
            response_message += " Email verification is not configured, so your account is automatically verified. You can log in now!"
        
        return {
            "message": response_message,
            "user_id": user.id,
            "username": user.username,
            "email": user.email,
            "email_verified": user.email_verified,
            "email_configured": email_configured,
            "email_sent": email_sent
        }

@app.post("/auth/login")
async def login_user(username: str = Form(...), password: str = Form(...)):
    with Session(engine) as session:
        user = session.exec(select(User).where(User.username == username)).first()
        
        if not user or not verify_password(password, user.password_hash):
            raise HTTPException(status_code=401, detail="Invalid username or password")
        
        # Enforce verification if email is configured
        if SMTP_USERNAME and SMTP_PASSWORD and not user.email_verified:
            raise HTTPException(status_code=401, detail="Please verify your email before logging in")
        
        return {
            "message": "Login successful",
            "user_id": user.id,
            "username": user.username,
            "email": user.email,
            "weight_kg": user.weight_kg,
            "protein_goal": round(user.protein_goal, 1) if user.protein_goal else None,
            "calorie_goal": round(user.calorie_goal, 0) if user.calorie_goal else None,
            "last_weight_update": user.last_weight_update.isoformat() if user.last_weight_update else None,
            "token": str(user.id)  # Simple token for now
        }

@app.get("/auth/verify/{token}")
async def verify_email(token: str):
    with Session(engine) as session:
        user = session.exec(select(User).where(User.verification_token == token)).first()
        
        if not user:
            # Return HTML error page
            error_html = """
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Invalid Verification Link</title>
                <style>
                    body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; text-align: center; padding: 50px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }
                    .container { background: rgba(255,255,255,0.1); padding: 40px; border-radius: 15px; backdrop-filter: blur(10px); }
                    .error-icon { font-size: 60px; margin-bottom: 20px; }
                    .btn { background: white; color: #667eea; padding: 12px 24px; text-decoration: none; border-radius: 25px; display: inline-block; margin-top: 20px; font-weight: bold; }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="error-icon">❌</div>
                    <h1>Invalid Verification Link</h1>
                    <p>This verification link is invalid or has expired.</p>
                    <a href="/login.html" class="btn">Go to Login</a>
                </div>
            </body>
            </html>
            """
            return HTMLResponse(content=error_html, status_code=404)
        
        user.email_verified = True
        user.verification_token = None
        session.commit()
        
        # Return HTML success page
        success_html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Email Verified Successfully</title>
            <style>
                body {{ 
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                    text-align: center; 
                    padding: 50px; 
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    color: white; 
                    margin: 0;
                    min-height: 100vh;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }}
                .container {{ 
                    background: rgba(255,255,255,0.1); 
                    padding: 40px; 
                    border-radius: 15px; 
                    backdrop-filter: blur(10px);
                    max-width: 500px;
                    box-shadow: 0 8px 32px rgba(0,0,0,0.1);
                }}
                .success-icon {{ font-size: 60px; margin-bottom: 20px; animation: bounce 2s infinite; }}
                @keyframes bounce {{ 0%, 20%, 50%, 80%, 100% {{ transform: translateY(0); }} 40% {{ transform: translateY(-10px); }} 60% {{ transform: translateY(-5px); }} }}
                .btn {{ 
                    background: white; 
                    color: #667eea; 
                    padding: 15px 30px; 
                    text-decoration: none; 
                    border-radius: 25px; 
                    display: inline-block; 
                    margin-top: 20px; 
                    font-weight: bold;
                    transition: all 0.3s ease;
                    box-shadow: 0 4px 15px rgba(0,0,0,0.2);
                }}
                .btn:hover {{ 
                    transform: translateY(-2px); 
                    box-shadow: 0 6px 20px rgba(0,0,0,0.3);
                }}
                .username {{ font-weight: bold; color: #ffd700; }}
                .note {{ 
                    background: rgba(255,255,255,0.1); 
                    padding: 15px; 
                    border-radius: 8px; 
                    margin: 20px 0; 
                    font-size: 14px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="success-icon">✅</div>
                <h1>Email Verified Successfully!</h1>
                <p>Welcome to KthizaTrack, <span class="username">{user.username}</span>! 🎉</p>
                <p>Your account has been verified and you can now log in to start tracking your nutrition.</p>
                
                <div class="note">
                    <strong>💡 Note:</strong> If you're accessing this from a different device or browser, 
                    you may need to open the app in your browser first.
                </div>
                
                <a href="/login.html" class="btn">🚀 Start Using KthizaTrack</a>
            </div>
        </body>
        </html>
        """
        return HTMLResponse(content=success_html)

@app.get("/auth/email-status")
async def get_email_status():
    """Check if email verification is configured"""
    email_configured = bool(SMTP_USERNAME and SMTP_PASSWORD)
    
    return {
        "email_configured": email_configured,
        "smtp_server": SMTP_SERVER if email_configured else None,
        "smtp_port": SMTP_PORT if email_configured else None,
        "setup_instructions": "Run 'python setup_env.py' to configure email verification" if not email_configured else None
    }

@app.post("/auth/verify-manual")
async def verify_email_manual(username: str = Form(...), token: str = Form(...)):
    """Manual email verification for testing purposes"""
    with Session(engine) as session:
        user = session.exec(select(User).where(
            (User.username == username) & (User.verification_token == token)
        )).first()
        
        if not user:
            raise HTTPException(status_code=404, detail="Invalid username or verification token")
        
        if user.email_verified:
            return {
                "message": "Account is already verified!",
                "username": user.username
            }
        
        user.email_verified = True
        user.verification_token = None
        session.commit()
        
        return {
            "message": "Email verified successfully! You can now log in.",
            "username": user.username
        }

@app.get("/users/profile", response_model=dict)
async def get_user_profile(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "weight_kg": current_user.weight_kg,
        "activity_level": current_user.activity_level,
        "protein_goal": round(current_user.protein_goal, 1) if current_user.protein_goal else None,
        "last_weight_update": current_user.last_weight_update.isoformat() if current_user.last_weight_update else None,
        "email_verified": current_user.email_verified,
        "profile_picture_path": current_user.profile_picture_path,
        "created_at": current_user.created_at.isoformat()
    }

@app.post("/users/update-profile")
async def update_profile(
    current_user: User = Depends(get_current_user),
    username: str = Form(...),
    email: str = Form(...)
):
    """Update user profile information"""
    if not username or not email:
        raise HTTPException(status_code=400, detail="Username and email are required")
    
    if not is_valid_email(email):
        raise HTTPException(status_code=400, detail="Invalid email format")
    
    with Session(engine) as session:
        user = session.exec(select(User).where(User.id == current_user.id)).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Check if username is already taken by another user
        existing_user = session.exec(select(User).where(User.username == username, User.id != current_user.id)).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Username already taken")
        
        # Check if email is already taken by another user
        existing_email = session.exec(select(User).where(User.email == email, User.id != current_user.id)).first()
        if existing_email:
            raise HTTPException(status_code=400, detail="Email already taken")
        
        # Update profile
        user.username = username
        user.email = email
        
        session.commit()
        session.refresh(user)
        
        return {
            "message": "Profile updated successfully",
            "username": user.username,
            "email": user.email
        }

@app.post("/users/upload-profile-picture")
async def upload_profile_picture(
    current_user: User = Depends(get_current_user),
    profile_picture: UploadFile = File(...)
):
    """Upload and save user profile picture"""
    # Validate file type
    if not profile_picture.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    # Create profile pictures directory
    profile_dir = "profile_pictures"
    os.makedirs(profile_dir, exist_ok=True)
    
    # Generate unique filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_extension = os.path.splitext(profile_picture.filename)[1]
    filename = f"profile_{current_user.id}_{timestamp}{file_extension}"
    file_path = os.path.join(profile_dir, filename)
    
    try:
        # Save the uploaded file
        with open(file_path, "wb") as buffer:
            content = await profile_picture.read()
            buffer.write(content)
        
        # Update user's profile picture path in database
        with Session(engine) as session:
            user = session.exec(select(User).where(User.id == current_user.id)).first()
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            
            # Delete old profile picture if it exists
            if user.profile_picture_path and os.path.exists(user.profile_picture_path):
                try:
                    os.remove(user.profile_picture_path)
                except Exception as e:
                    print(f"Failed to delete old profile picture: {e}")
            
            # Update profile picture path
            user.profile_picture_path = file_path
            session.commit()
            session.refresh(user)
        
        return {
            "message": "Profile picture uploaded successfully",
            "profile_picture_path": file_path
        }
        
    except Exception as e:
        # Clean up file if database update fails
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Failed to upload profile picture: {str(e)}")

@app.get("/users/profile-picture/{user_id}")
async def get_profile_picture(user_id: int):
    """Get user's profile picture"""
    with Session(engine) as session:
        user = session.exec(select(User).where(User.id == user_id)).first()
        if not user or not user.profile_picture_path:
            raise HTTPException(status_code=404, detail="Profile picture not found")
        
        if not os.path.exists(user.profile_picture_path):
            raise HTTPException(status_code=404, detail="Profile picture file not found")
        
        return FileResponse(user.profile_picture_path)

@app.post("/users/update-weight")
async def update_weight(
    current_user: User = Depends(get_current_user),
    weight_kg: float = Form(...),
    activity_level: str = Form("moderate")
):
    """Update user weight and recalculate protein goal"""
    print(f"⚖️  Weight update request for user: {current_user.username} (ID: {current_user.id})")
    print(f"⚖️  New weight: {weight_kg}kg, Activity level: {activity_level}")
    
    if weight_kg <= 0:
        raise HTTPException(status_code=400, detail="Weight must be greater than 0")
    
    with Session(engine) as session:
        user = session.exec(select(User).where(User.id == current_user.id)).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Update weight, activity level, protein goal, and calorie goal
        user.weight_kg = weight_kg
        user.activity_level = activity_level
        user.protein_goal = calculate_protein_goal(weight_kg, activity_level)
        user.calorie_goal = calculate_calorie_goal(weight_kg, activity_level)
        user.last_weight_update = datetime.now()
        
        session.commit()
        session.refresh(user)
        
        # Invalidate dashboard cache for this user
        cache_key = f"dashboard_{user.id}_{datetime.now().date()}"
        cache.set(cache_key, None, ttl=1)  # Invalidate immediately
        
        return {
            "message": "Weight updated successfully",
            "weight_kg": user.weight_kg,
            "activity_level": user.activity_level,
            "protein_goal": round(user.protein_goal, 1) if user.protein_goal else None,
            "calorie_goal": round(user.calorie_goal, 0) if user.calorie_goal else None,
            "last_weight_update": user.last_weight_update.isoformat()
        }

@app.post("/users/update-protein-goal")
async def update_protein_goal(
    current_user: User = Depends(get_current_user),
    protein_goal: float = Form(...)
):
    """Update user protein goal directly"""
    if protein_goal <= 0:
        raise HTTPException(status_code=400, detail="Protein goal must be greater than 0")
    
    with Session(engine) as session:
        user = session.exec(select(User).where(User.id == current_user.id)).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Update protein goal
        user.protein_goal = round(protein_goal, 1)
        
        session.commit()
        session.refresh(user)
        
        # Invalidate dashboard cache for this user
        cache_key = f"dashboard_{user.id}_{datetime.now().date()}"
        cache.set(cache_key, None, ttl=1)  # Invalidate immediately
        
        return {
            "message": "Protein goal updated successfully",
            "protein_goal": round(user.protein_goal, 1) if user.protein_goal else None
        }

@app.post("/users/update-calorie-goal")
async def update_calorie_goal(
    current_user: User = Depends(get_current_user),
    calorie_goal: float = Form(...)
):
    """Update user calorie goal directly"""
    if calorie_goal <= 0:
        raise HTTPException(status_code=400, detail="Calorie goal must be greater than 0")
    
    with Session(engine) as session:
        user = session.exec(select(User).where(User.id == current_user.id)).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Update calorie goal
        user.calorie_goal = round(calorie_goal, 0)
        
        session.commit()
        session.refresh(user)
        
        # Invalidate dashboard cache for this user
        cache_key = f"dashboard_{user.id}_{datetime.now().date()}"
        cache.set(cache_key, None, ttl=1)  # Invalidate immediately
        
        return {
            "message": "Calorie goal updated successfully",
            "calorie_goal": round(user.calorie_goal, 0) if user.calorie_goal else None
        }

@app.post("/users/update-activity-level")
async def update_activity_level(
    current_user: User = Depends(get_current_user),
    activity_level: str = Form(...)
):
    """Update user activity level and recalculate protein goal"""
    valid_levels = ['sedentary', 'light', 'moderate', 'active', 'athlete']
    if activity_level not in valid_levels:
        raise HTTPException(status_code=400, detail="Invalid activity level")
    
    with Session(engine) as session:
        user = session.exec(select(User).where(User.id == current_user.id)).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Update activity level and recalculate protein and calorie goals if weight exists
        user.activity_level = activity_level
        if user.weight_kg:
            user.protein_goal = calculate_protein_goal(user.weight_kg, activity_level)
            user.calorie_goal = calculate_calorie_goal(user.weight_kg, activity_level)
        
        session.commit()
        session.refresh(user)
        
        # Invalidate dashboard cache for this user
        cache_key = f"dashboard_{user.id}_{datetime.now().date()}"
        cache.set(cache_key, None, ttl=1)  # Invalidate immediately
        
        return {
            "message": "Activity level updated successfully",
            "activity_level": user.activity_level,
            "protein_goal": round(user.protein_goal, 1) if user.protein_goal else None,
            "calorie_goal": round(user.calorie_goal, 0) if user.calorie_goal else None
        }

@app.options("/meals/upload/")
async def upload_meal_options():
    """Handle CORS preflight for meal upload"""
    return {"message": "CORS preflight OK"}

@app.post("/meals/upload/")
async def upload_meal(
    current_user: User = Depends(get_current_user),
    image: UploadFile = File(...),
    food_items: str = Form(""),
    use_ai_detection: bool = Form(True)
):
    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"meal_{current_user.id}_{timestamp}_{image.filename}"
    file_path = os.path.join(upload_dir, filename)
    
    try:
        with open(file_path, "wb") as buffer:
            content = await image.read()
            buffer.write(content)
        
        # Try multi-item AI detection if enabled
        detected_foods = []
        ai_detection_status = {
            "attempted": use_ai_detection,
            "available": True,  # Google Vision API is always available if service account is configured
            "successful": False,
            "error": None
        }
        
        print(f"🤖 Multi-Item AI Detection Requested: {use_ai_detection}")
        print(f"🔧 Google Vision API with Service Account: Available")
        
        if use_ai_detection:
            try:
                detected_foods = identify_food_with_vision(file_path)
                ai_detection_status["successful"] = len(detected_foods) > 0
                print(f"🎯 Multi-Item AI Detection Results: {detected_foods}")
            except Exception as e:
                ai_detection_status["error"] = str(e)
                print(f"❌ AI Detection failed: {e}")
        
        # Parse manual food items
        manual_foods = []
        print(f"📝 Manual food items: '{food_items}'")
        if food_items:
            manual_foods = [item.strip() for item in food_items.split(",") if item.strip()]
            print(f"✅ Parsed manual foods: {manual_foods}")
        
        # Combine and determine final food list
        print(f"🤖 AI detected foods: {detected_foods}")
        print(f"✍️  Manual foods: {manual_foods}")
        
        if detected_foods and manual_foods:
            # Both AI and manual - combine them, removing duplicates
            food_list = list(set(detected_foods + manual_foods))
            print(f"🔄 Combined AI + Manual: {food_list}")
        elif detected_foods:
            # Only AI detection worked
            food_list = detected_foods
            print(f"🤖 AI Detection Only: {food_list}")
        elif manual_foods:
            # Only manual input
            food_list = manual_foods
            print(f"✍️  Manual Input Only: {food_list}")
        else:
            # No food items provided and AI failed
            food_list = []
            print("❌ No food items detected or provided")
        
        # Check if we have food items to process
        if not food_list:
            # Clean up the uploaded file since we can't process it
            if os.path.exists(file_path):
                os.remove(file_path)
            
            error_message = "No food items detected or provided. "
            if use_ai_detection and not detected_foods:
                error_message += "AI detection did not identify food items. Please enter food items manually."
            else:
                error_message += "Please enter the food items manually."
            
            raise HTTPException(status_code=400, detail=error_message)
        
        total_protein, matched_foods = calculate_protein_enhanced(food_list)
        total_calories, _ = calculate_calories_enhanced(food_list)
        
        with Session(engine) as session:
            meal = Meal(
                user_id=current_user.id,
                image_path=file_path,
                food_items=json.dumps(food_list),
                total_protein=total_protein,
                total_calories=total_calories
            )
            session.add(meal)
            session.commit()
            session.refresh(meal)
        
        # Invalidate cache for this user
        cache_key = f"dashboard_{current_user.id}_{datetime.now().date()}"
        cache.set(cache_key, None, ttl=1)  # Invalidate immediately
        
        return {
            "message": "Meal processed successfully",
            "meal_id": meal.id,
            "food_items": food_list,
            "matched_foods": matched_foods,
            "total_protein": total_protein,
            "total_calories": total_calories,
            "user_protein_goal": current_user.protein_goal,
            "ai_detection_used": use_ai_detection,
            "google_vision_available": GOOGLE_VISION_AVAILABLE,
            "detection_status": {
                "ai_detected": len(detected_foods) > 0,
                "manual_provided": len(manual_foods) > 0,
                "ai_available": GOOGLE_VISION_AVAILABLE,
                "ai_attempted": ai_detection_status["attempted"],
                "ai_successful": ai_detection_status["successful"],
                "ai_error": ai_detection_status["error"],
                "detected_foods": detected_foods,
                "manual_foods": manual_foods
            }
        }
        
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Error processing meal: {str(e)}")

@app.get("/dashboard")
async def get_dashboard_data(current_user: User = Depends(get_current_user)):
    # Check cache first
    cache_key = f"dashboard_{current_user.id}_{datetime.now().date()}"
    cached_data = cache.get(cache_key)
    if cached_data and cached_data['expires_at'] > time.time():
        return cached_data['value']
    
    with Session(engine) as session:
        # Fetch fresh user data from database to get latest goals
        fresh_user = session.exec(select(User).where(User.id == current_user.id)).first()
        if not fresh_user:
            raise HTTPException(status_code=404, detail="User not found")
        
        today = datetime.now().date()
        today_meals = session.exec(select(Meal).where(
            Meal.user_id == fresh_user.id,
            func.date(Meal.created_at) == today
        )).all()
        
        today_protein = round(sum(meal.total_protein for meal in today_meals), 1)
        today_calories = round(sum(meal.total_calories for meal in today_meals), 1)
        
        all_meals = session.exec(select(Meal).where(Meal.user_id == fresh_user.id)).all()
        
        week_ago = datetime.now().date() - timedelta(days=7)
        weekly_meals = session.exec(select(Meal).where(
            Meal.user_id == fresh_user.id,
            func.date(Meal.created_at) >= week_ago
        )).all()
        weekly_protein = round(sum(meal.total_protein for meal in weekly_meals), 1)
        weekly_calories = round(sum(meal.total_calories for meal in weekly_meals), 1)
        
        # Check if user needs weight update (weekly popup)
        needs_weight_update = False
        if fresh_user.last_weight_update:
            days_since_update = (datetime.now() - fresh_user.last_weight_update).days
            needs_weight_update = days_since_update >= 7
        else:
            needs_weight_update = True  # First time user
        
        result = {
            "user": {
                "id": fresh_user.id,
                "username": fresh_user.username,
                "weight_kg": fresh_user.weight_kg,
                "protein_goal": round(fresh_user.protein_goal, 1) if fresh_user.protein_goal else None,
                "calorie_goal": round(fresh_user.calorie_goal, 0) if fresh_user.calorie_goal else None,
                "last_weight_update": fresh_user.last_weight_update.isoformat() if fresh_user.last_weight_update else None,
                "needs_weight_update": needs_weight_update,
                "profile_picture_path": fresh_user.profile_picture_path
            },
            "today": {
                "total_protein": round(today_protein, 1),
                "total_calories": round(today_calories, 1),
                "goal_progress": round((today_protein / fresh_user.protein_goal) * 100 if fresh_user.protein_goal else 0, 1),
                "meals_count": len(today_meals),
                "remaining_protein": round(max(0, (fresh_user.protein_goal or 0) - today_protein), 1)
            },
            "weekly": {
                "total_calories": round(weekly_calories, 1),
                "average_daily": round(weekly_calories / 7, 1),
                "meals_count": len(weekly_meals)
            },
            "overall": {
                "total_meals": len(all_meals),
                "average_protein_per_meal": round(sum(m.total_protein for m in all_meals) / len(all_meals) if all_meals else 0, 1),
                "total_protein_tracked": round(sum(m.total_protein for m in all_meals), 1)
            }
        }
        
        # Cache the result for 2 minutes
        cache.set(cache_key, result, ttl=120)
        return result

@app.get("/meals")
async def get_user_meals(
    current_user: User = Depends(get_current_user),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    date_filter: Optional[str] = Query(None, description="Filter by date (YYYY-MM-DD)")
):
    """Get user meals with pagination and date filtering"""
    print(f"🍽️  Loading meals for user: {current_user.username} (ID: {current_user.id})")
    offset = (page - 1) * limit
    
    with Session(engine) as session:
        # Build query with optional date filter
        query = select(Meal).where(Meal.user_id == current_user.id)
        
        if date_filter:
            try:
                filter_date = datetime.strptime(date_filter, "%Y-%m-%d").date()
                query = query.where(
                    func.date(Meal.created_at) == filter_date
                )
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
        
        # Get total count for pagination
        count_query = select(func.count()).select_from(query.subquery())
        total_count = session.exec(count_query).first()
        
        # Get paginated results
        meals = session.exec(
            query.order_by(Meal.created_at.desc())
            .offset(offset)
            .limit(limit)
        ).all()
        
        return {
            "meals": [
                {
                    "id": meal.id,
                    "food_items": json.loads(meal.food_items),
                    "total_protein": meal.total_protein,
                    "total_calories": meal.total_calories,
                    "created_at": meal.created_at.isoformat()
                }
                for meal in meals
            ],
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total_count,
                "pages": (total_count + limit - 1) // limit,
                "has_next": page * limit < total_count,
                "has_prev": page > 1
            }
        }

@app.get("/meals/today")
async def get_today_meals(current_user: User = Depends(get_current_user)):
    """Get all meals for today with optimized query"""
    today = datetime.now().date()
    
    with Session(engine) as session:
        # Get all meals for today
        today_meals = session.exec(
            select(Meal).where(
                (Meal.user_id == current_user.id) &
                (func.date(Meal.created_at) == today)
            ).order_by(Meal.created_at.desc())
        ).all()
        
        return {
            "meals": [
                {
                    "id": meal.id,
                    "food_items": json.loads(meal.food_items),
                    "total_protein": meal.total_protein,
                    "total_calories": meal.total_calories,
                    "created_at": meal.created_at.isoformat()
                }
                for meal in today_meals
            ],
            "total_count": len(today_meals)
        }

@app.get("/foods/suggestions")
async def get_food_suggestions():
    categories = {
        "meat_fish": ["chicken breast", "salmon", "tuna", "beef", "turkey"],
        "dairy_eggs": ["eggs", "milk", "yogurt", "cheese"],
        "plant_based": ["tofu", "lentils", "beans", "quinoa", "chickpeas"],
        "vegetables": ["broccoli", "spinach", "kale"],
        "nuts_seeds": ["almonds", "peanut butter", "chia seeds"],
        "grains": ["rice", "bread", "pasta"]
    }
    
    return {
        "foods": list(PROTEIN_DATABASE.keys()),
        "total_foods": len(PROTEIN_DATABASE),
        "categories": categories,
        "protein_values": PROTEIN_DATABASE
    }

@app.delete("/users/delete-account")
async def delete_user_account(current_user: User = Depends(get_current_user)):
    """Delete user account and all associated data"""
    try:
        with Session(engine) as session:
            # Get the user with all related data
            user = session.get(User, current_user.id)
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            
            # Delete all meals for this user
            user_meals = session.exec(
                select(Meal).where(Meal.user_id == current_user.id)
            ).all()
            
            # Delete meal images and records
            for meal in user_meals:
                if meal.image_path and os.path.exists(meal.image_path):
                    try:
                        os.remove(meal.image_path)
                    except Exception as e:
                        print(f"Failed to delete image {meal.image_path}: {e}")
                session.delete(meal)
            
            # Delete profile picture if exists
            if user.profile_picture_path and os.path.exists(user.profile_picture_path):
                try:
                    os.remove(user.profile_picture_path)
                except Exception as e:
                    print(f"Failed to delete profile picture {user.profile_picture_path}: {e}")
            
            # Delete the user
            session.delete(user)
            session.commit()
            
            return {
                "message": "Account deleted successfully",
                "deleted_meals": len(user_meals),
                "user_id": current_user.id
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete account: {str(e)}")

@app.post("/admin/cleanup")
async def manual_cleanup():
    """Manual cleanup endpoint for testing"""
    try:
        with Session(engine) as session:
            # Find meals older than 1 hour (for testing)
            cutoff_time = datetime.now() - timedelta(hours=1)
            old_meals = session.exec(
                select(Meal).where(Meal.created_at < cutoff_time)
            ).all()
            
            cleaned_count = 0
            for meal in old_meals:
                # Delete the image file
                if os.path.exists(meal.image_path):
                    try:
                        os.remove(meal.image_path)
                        cleaned_count += 1
                    except Exception as e:
                        print(f"Failed to delete image {meal.image_path}: {e}")
                
                # Delete the meal record
                session.delete(meal)
            
            session.commit()
            
            return {
                "message": f"Manual cleanup completed",
                "cleaned_meals": cleaned_count,
                "total_old_meals": len(old_meals)
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cleanup failed: {str(e)}")

app.mount("/static", StaticFiles(directory="static"), name="static")

if __name__ == "__main__":
    import uvicorn
    import os
    
    # Get port from environment variable (Render requirement)
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")
    
    print("🚀 Starting KthizaTrack Server...")
    print(f"📍 Server will be available at: http://{host}:{port}")
    print("🔧 Press Ctrl+C to stop the server")
    uvicorn.run(app, host=host, port=port, reload=False) 