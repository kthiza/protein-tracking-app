from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Depends, Query
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import FileResponse, HTMLResponse
from sqlmodel import SQLModel, create_engine, Session, select, Field, func
from sqlalchemy import text
from typing import List, Optional, Dict
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

# Load environment variables from .env file (local development only)
try:
    from dotenv import load_dotenv
    import os
    # Check if .env file exists before loading (local development only)
    if os.path.exists('.env'):
        load_dotenv()
        print("✅ Loaded environment variables from .env file (local development)")
    else:
        print("ℹ️  No .env file found. Using environment variables from system/deployment platform.")
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
            print(f"   Project ID: {service_account_info.get('project_id', 'Unknown')}")
        except (json.JSONDecodeError, KeyError) as e:
            print(f"❌ Invalid Google Vision service account JSON: {e}")
            print("   Please check your GOOGLE_SERVICE_ACCOUNT environment variable in Render dashboard")
            GOOGLE_VISION_AVAILABLE = False
    elif GOOGLE_VISION_SERVICE_ACCOUNT_PATH and os.path.exists(GOOGLE_VISION_SERVICE_ACCOUNT_PATH):
        GOOGLE_VISION_AVAILABLE = True
        print(f"✅ Google Vision API configured (service account file: {GOOGLE_VISION_SERVICE_ACCOUNT_PATH})")
    else:
        GOOGLE_VISION_AVAILABLE = False
        print("ℹ️  Google Vision API not configured. This is optional - the app will work without it.")
        print("   To enable AI food detection:")
        print("   1. Set GOOGLE_SERVICE_ACCOUNT environment variable in Render dashboard")
        print("   2. Or upload service-account-key.json and set GOOGLE_VISION_SERVICE_ACCOUNT_PATH")
        print("   See GOOGLE_VISION_SETUP.md for detailed instructions")
        
except ImportError:
    GOOGLE_VISION_AVAILABLE = False
    print("Warning: food_detection module not importable. Ensure the file exists.")

# For backward compatibility
LOCAL_AI_AVAILABLE = GOOGLE_VISION_AVAILABLE

# Enhanced protein database (values per 100g); optimized for realistic 250g portions
PROTEIN_DATABASE = {
lking about    # Meats & Poultry (30% reduced for realistic portions)
    "chicken": 21.7, "chicken breast": 21.7, "chicken thigh": 19.6, "chicken wing": 21.0,
    "beef": 18.2, "steak": 18.2, "ground beef": 18.2, "beef burger": 18.2, "burger": 18.2,
    "pork": 17.5, "pork chop": 17.5, "bacon": 25.9, "ham": 15.4, "sausage": 12.6,
    "salmon": 14.0, "tuna": 21.0, "cod": 12.6, "tilapia": 18.2, "fish": 14.0,
    "turkey": 20.3, "duck": 16.1, "lamb": 17.5, "shrimp": 16.8, "prawns": 16.8,
    
    # Dairy & Eggs (30% reduced for realistic portions)
    "egg": 9.1, "eggs": 9.1, "milk": 2.4, "cheese": 17.5, "cheddar": 17.5,
    "yogurt": 7.0, "greek yogurt": 7.0, "cottage cheese": 7.7, "cream cheese": 4.2,
    
    # Nuts & Seeds (30% reduced for realistic portions)
    "peanut butter": 17.5, "almonds": 14.7, "walnuts": 10.5, "cashews": 12.6,
    "sunflower seeds": 14.7, "chia seeds": 11.9, "pumpkin seeds": 13.3,
    
    # Plant-based Proteins (30% reduced for realistic portions)
    "tofu": 5.6, "tempeh": 14.0, "lentils": 6.3, "beans": 6.3, "black beans": 6.3,
    "kidney beans": 6.3, "chickpeas": 6.3, "edamame": 7.7, "hummus": 5.6,
    "seitan": 17.5,  # 30% reduced from 25g
    "pea protein": 17.5,  # 30% reduced from 25g
    "spirulina": 39.9,  # 30% reduced from 57g
    "nutritional yeast": 35.0,  # 30% reduced from 50g
    
    # Grains & Cereals (30% reduced for realistic portions)
    "quinoa": 9.8, "rice": 1.9, "brown rice": 1.9, "bread": 6.3, "whole wheat bread": 9.1,
    "pasta": 3.9, "spaghetti": 3.9, "oatmeal": 4.2, "oats": 4.2, "cereal": 7.0,
    
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
    
    # Plant-based Proteins (FIXED: More realistic values)
    "tofu": 76, "tempeh": 192, "lentils": 116, "beans": 116, "black beans": 116,
    "kidney beans": 116, "chickpeas": 164, "edamame": 121, "hummus": 166,
    "seitan": 370,  # FIXED: Was too low, now realistic for seitan
    "pea protein": 350,  # FIXED: Realistic for pea protein isolate
    "spirulina": 290,  # Realistic for spirulina powder
    "nutritional yeast": 325,  # Realistic for nutritional yeast flakes
    
    # Grains & Cereals (FIXED: More realistic values)
    "quinoa": 120, "rice": 130, "brown rice": 111, "bread": 265, "whole wheat bread": 247,
    "pasta": 158, "spaghetti": 158, "oatmeal": 68, "oats": 68, "cereal": 378,
    
    # Vegetables (low density - realistic for larger portions)
    "broccoli": 34, "spinach": 23, "kale": 49, "asparagus": 20, "brussels sprouts": 43,
    "cauliflower": 25, "peas": 84, "corn": 86, "potato": 77, "sweet potato": 86,
    
    # Fast Food & Common Meals (FIXED: More realistic values)
    "pizza": 266, "pizza slice": 266, "hamburger": 295, "hot dog": 151,
    "sandwich": 250, "wrap": 250, "taco": 226, "burrito": 300,
    "noodles": 158, "ramen": 158, "soup": 35, "salad": 25,
    
    # Breakfast Foods (FIXED: More realistic values)
    "pancakes": 227, "waffles": 291, "french toast": 229, "bagel": 245,
    "muffin": 265, "croissant": 406, "english muffin": 157,
    
    # Snacks & Others (FIXED: More realistic values)
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
    
    def delete(self, key):
        """Delete a specific key from cache"""
        with self.lock:
            self.cache.pop(key, None)
    
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
    # Slightly elevated to better align with calorie needs
    protein_multipliers = {
        'sedentary': 1.0,
        'light': 1.2,
        'moderate': 1.4,
        'active': 1.7,
        'athlete': 2.0
    }

    multiplier = protein_multipliers.get(activity_level, 1.4)
    weight_based = weight_kg * multiplier

    # Ensure protein isn't disproportionately low relative to calories
    # Use at least ~18% of estimated calories as protein (cal/4 = grams)
    estimated_calories = calculate_calorie_goal(weight_kg, activity_level)
    calorie_floor_g = 0.18 * estimated_calories / 4.0

    # Cap for safety at ~2.2 g/kg upper bound commonly recommended
    upper_cap = 2.2 * weight_kg

    goal = max(weight_based, calorie_floor_g)
    goal = min(goal, upper_cap)
    return round(goal, 1)

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
        
        # Use the correct base URL for verification links
        # Fix for malformed URLs - ensure we have a proper base URL
        base_url = APP_BASE_URL.rstrip('/')
        if not base_url or base_url == "http://127.0.0.1:8000":
            # Fallback to a reasonable default for production
            base_url = "https://kthiza-track.onrender.com"
            print(f"⚠️  APP_BASE_URL not set properly, using fallback: {base_url}")
        
        verification_url = f"{base_url}/auth/verify/{token}"
        print(f"🔗 Generated verification URL: {verification_url}")
        
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
            <strong>🌐 Production Ready:</strong> Your KthizaTrack app is now live and ready to use!
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
    
    # Compute unified portion weights for both protein and calories
    food_weights, normalized_total = _compute_portion_weights(food_items)
    total_protein = 0.0
    
    # Single or multi-item path now uses identical weights
    for food_item in food_items:
        food_lower = food_item.lower().strip()
        protein_per_100g = 0.0
        portion_weight = food_weights.get(food_item, 0.0)
        
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
    
    print(f"📊 Protein calculation: {total_protein:.1f}g from {normalized_total:.0f}g total (unified)")
    return round(total_protein, 1), matched_foods

def calculate_calories_enhanced(food_items: List[str]) -> tuple[float, List[str]]:
    """Calculate total calories for detected foods with realistic portion sizing"""
    matched_foods = []
    
    # Use the same unified portion weights as protein calculation
    food_weights, normalized_total = _compute_portion_weights(food_items)
    
    total_calories = 0.0
    
    for food_item in food_items:
        food_lower = food_item.lower().strip()
        calories_per_100g = 0.0
        portion_weight = food_weights.get(food_item, 0.0)
        
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
    
    print(f"📊 Calorie calculation: {total_calories:.1f} calories from {normalized_total:.0f}g total (unified)")
    return round(total_calories, 1), matched_foods

def _compute_portion_weights(food_items: List[str]) -> tuple[Dict[str, float], float]:
    """Compute unified portion weights for protein and calorie calculations.
    - Start from realistic per-item portions
    - Normalize total weight based on number of items
    """
    total_weight = 0.0
    food_weights: Dict[str, float] = {}
    for food_item in food_items:
        food_lower = food_item.lower().strip()
        realistic_portion = _get_realistic_portion_size(food_lower)
        food_weights[food_item] = realistic_portion
        total_weight += realistic_portion

    # Choose normalization target by number of items - MUCH MORE REALISTIC PORTIONS
    if len(food_items) <= 1:
        target_total = 120.0  # Reduced from 400g to 120g
    elif len(food_items) == 2:
        target_total = 200.0  # Reduced from 600g to 200g
    elif len(food_items) <= 4:
        target_total = 300.0  # Reduced from 800g to 300g
    else:
        target_total = 400.0  # Reduced from 1000g to 400g

    if total_weight > 0:
        scale_factor = target_total / total_weight
        for key in food_weights:
            food_weights[key] *= scale_factor

    return food_weights, target_total

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
        return 9.0
    elif any(word in food_name for word in ['pasta', 'noodles', 'spaghetti', 'macaroni']):
        return 5.5
    elif any(word in food_name for word in ['rice', 'quinoa', 'oatmeal', 'cereal']):
        return 6.0
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
        return 265
    elif any(word in food_name for word in ['rice', 'pasta', 'noodles', 'spaghetti']):
        return 158
    elif any(word in food_name for word in ['oatmeal', 'oats', 'cereal']):
        return 68
    
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
        return 10.0  # 10g for oils/fats

    # Medium-high density foods (cheese, bacon, etc.)
    elif any(word in food_name for word in ['cheese', 'cheddar', 'bacon', 'cream cheese']):
        return 40.0  # 40g for cheese/bacon

    # Steak gets a larger single-item portion
    elif 'steak' in food_name:
        return 200.0  # 200g for steak
    # Protein-rich foods (meats, fish, eggs) - moderate portions
    elif any(word in food_name for word in ['chicken', 'beef', 'pork', 'turkey', 'lamb', 'duck', 'salmon', 'tuna', 'fish', 'shrimp', 'prawn', 'egg']):
        return 120.0  # 120g for protein foods

    # Grains and carbs (pasta, rice, bread) - moderate portions
    elif any(word in food_name for word in ['pasta', 'spaghetti', 'rice', 'bread', 'quinoa', 'oatmeal', 'oats', 'cereal']):
        return 150.0  # 150g for grains

    # Fast food and mixed dishes - moderate portions
    elif any(word in food_name for word in ['pizza', 'burger', 'sandwich', 'wrap', 'taco', 'burrito', 'hot dog']):
        return 250.0  # 250g for complete meals

    # Low-density foods (vegetables, fruits) - larger portions
    elif any(word in food_name for word in ['broccoli', 'spinach', 'kale', 'asparagus', 'cauliflower', 'salad', 'vegetable', 'fruit', 'apple', 'banana']):
        return 250.0  # 250g for vegetables/fruits

    # Very low-density foods (soups, smoothies) - larger portions
    elif any(word in food_name for word in ['soup', 'smoothie']):
        return 350.0  # 350g for liquids
    
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
    """Multi-item food detection using Google Vision API with fallback system.
    
    This function uses Google Vision API with improved confidence thresholds
    to detect multiple food items in complex meals like English breakfast.
    If Google Vision fails, it uses a local fallback system.
    """
    try:
        print(f"🔍 Starting multi-item food detection for image: {image_path}")
        
        # Try Google Vision API first
        if GOOGLE_VISION_AVAILABLE:
            try:
                print("🤖 Attempting Google Vision API detection...")
                detected_foods = identify_food_with_google_vision(image_path)
                if detected_foods and len(detected_foods) > 0:
                    print(f"🎯 Google Vision Detection Results: {detected_foods}")
                    return detected_foods
                else:
                    print("⚠️  Google Vision API returned no results, trying fallback...")
            except Exception as e:
                print(f"❌ Google Vision API failed: {e}, trying fallback...")
        else:
            print("ℹ️  Google Vision API not available, using fallback...")
        
        # Fallback: Use local food detection based on image analysis
        print("🔄 Using local food detection fallback...")
        detected_foods = identify_food_local_fallback(image_path)
        print(f"🎯 Local Fallback Detection Results: {detected_foods}")
        return detected_foods or []
        
    except Exception as e:
        print(f"❌ All food detection methods failed: {e}")
        return []

def identify_food_local_fallback(image_path: str) -> List[str]:
    """Local fallback food detection that analyzes image characteristics"""
    try:
        print("🔧 Using intelligent local fallback detection...")
        
        # Import PIL for basic image analysis
        try:
            from PIL import Image
            import os
            
            # Get image file extension to make educated guesses
            filename = os.path.basename(image_path).lower()
            
            # Analyze filename for clues (map to canonical items in databases)
            if any(word in filename for word in ['pasta', 'spaghetti', 'noodle']):
                return ['pasta']
            elif any(word in filename for word in ['pizza', 'slice']):
                return ['pizza']
            elif any(word in filename for word in ['burger', 'hamburger']):
                return ['hamburger']
            elif any(word in filename for word in ['salad', 'vegetable']):
                return ['salad']
            elif any(word in filename for word in ['chicken', 'poultry']):
                return ['chicken']
            elif any(word in filename for word in ['fish', 'salmon', 'tuna']):
                return ['fish']
            elif any(word in filename for word in ['egg', 'breakfast']):
                return ['eggs']
            elif any(word in filename for word in ['rice', 'grain']):
                return ['rice']
            elif any(word in filename for word in ['bread', 'toast']):
                return ['bread']
            elif any(word in filename for word in ['soup', 'stew']):
                return ['soup']
            elif any(word in filename for word in ['sandwich', 'sub']):
                return ['sandwich']
            elif any(word in filename for word in ['taco', 'burrito', 'wrap']):
                return ['wrap']
            elif any(word in filename for word in ['sushi', 'roll']):
                return ['rice', 'fish']
            elif any(word in filename for word in ['steak', 'beef']):
                return ['beef']
            elif any(word in filename for word in ['pork', 'bacon']):
                return ['pork']
            elif any(word in filename for word in ['turkey', 'duck']):
                return ['turkey']
            elif any(word in filename for word in ['lamb', 'mutton']):
                return ['lamb']
            elif any(word in filename for word in ['shrimp', 'prawn']):
                return ['shrimp']
            elif any(word in filename for word in ['cheese', 'dairy']):
                return ['cheese']
            elif any(word in filename for word in ['milk', 'yogurt']):
                return ['milk']
            elif any(word in filename for word in ['nut', 'almond', 'peanut']):
                return ['almonds']
            elif any(word in filename for word in ['bean', 'lentil']):
                return ['beans']
            elif any(word in filename for word in ['tofu', 'soy']):
                return ['tofu']
            elif any(word in filename for word in ['quinoa', 'grain']):
                return ['quinoa']
            else:
                # Be conservative: if no clue, don't guess
                return []
                
        except ImportError:
            # If PIL is not available, use a simple timestamp-based variation
            import time
            timestamp = int(time.time())
            generic_options = [
                ['pasta', 'vegetables'],
                ['chicken', 'rice'],
                ['beef', 'potato'],
                ['fish', 'vegetables'],
                ['eggs', 'bread'],
                ['pizza', 'cheese'],
                ['salad', 'vegetables'],
                ['soup', 'vegetables'],
                ['sandwich', 'meat'],
                ['rice', 'vegetables']
            ]
            return generic_options[timestamp % len(generic_options)]
        
    except Exception as e:
        print(f"❌ Local fallback failed: {e}")
        # Return nothing if fallback fails, to allow manual entry or proper error
        return []

@app.get("/")
async def root():
    """Serve the professional landing page"""
    from fastapi.responses import FileResponse
    return FileResponse("static/index.html")

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        with Session(engine) as session:
            # Try a simple query
            result = session.exec(text("SELECT 1")).first()
            database_status = "connected" if result else "error"
    except Exception as e:
        database_status = f"error: {str(e)}"
    
    # Get database type from URL
    database_url = os.getenv("DATABASE_URL", "sqlite:///./protein_app.db")
    database_type = "sqlite" if "sqlite" in database_url else "postgresql" if "postgresql" in database_url else "unknown"
    
    return {
        "status": "healthy", 
        "timestamp": datetime.now().isoformat(),
        "database": database_status,
        "database_type": database_type,
        "environment": os.getenv("ENVIRONMENT", "development")
    }

@app.get("/api/test")
async def test_api():
    """Test endpoint to verify API is working"""
    return {"message": "API is working!", "timestamp": datetime.now().isoformat()}

@app.get("/users")
async def get_users():
    """Get all users (for debugging)"""
    with Session(engine) as session:
        users = session.exec(select(User)).all()
        return {
            "users": [
                {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "protein_goal": user.protein_goal,
                    "calorie_goal": user.calorie_goal,
                    "weight_kg": user.weight_kg,
                    "created_at": user.created_at.isoformat() if user.created_at else None
                }
                for user in users
            ]
        }

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
    """Verify user email with improved error handling and logging"""
    print(f"🔐 Email verification attempt with token: {token[:10]}...")
    
    try:
        with Session(engine) as session:
            # Find user by verification token
            user = session.exec(select(User).where(User.verification_token == token)).first()
            
            if not user:
                print(f"❌ No user found with verification token: {token[:10]}...")
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
                 <p>Please try registering again or contact support.</p>
                 <a href="/static/login.html" class="btn">Go to Login</a>
                    </div>
                </body>
                </html>
                """
                return HTMLResponse(content=error_html, status_code=404)
            
            # Check if user is already verified
            if user.email_verified:
                print(f"ℹ️  User {user.username} is already verified")
                # Return already verified page
                already_verified_html = f"""
                <!DOCTYPE html>
                <html lang="en">
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>Already Verified</title>
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
                        .info-icon {{ font-size: 60px; margin-bottom: 20px; }}
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
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="info-icon">ℹ️</div>
                        <h1>Already Verified!</h1>
                        <p>Hello <span class="username">{user.username}</span>! 🎉</p>
                        <p>Your email has already been verified. You can log in to your account.</p>
                                                 <a href="/static/login.html" class="btn">🚀 Go to Login</a>
                    </div>
                </body>
                </html>
                """
                return HTMLResponse(content=already_verified_html)
            
            # Verify the user
            print(f"✅ Verifying user: {user.username} (ID: {user.id})")
            user.email_verified = True
            user.verification_token = None
            session.commit()
            
            print(f"✅ Successfully verified user: {user.username}")
            
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
                        <strong>💡 Note:</strong> You can now log in to your account and start using KthizaTrack!
                    </div>
                    
                                         <a href="/static/login.html" class="btn">🚀 Start Using KthizaTrack</a>
                </div>
            </body>
            </html>
            """
            return HTMLResponse(content=success_html)
            
    except Exception as e:
        print(f"❌ Error during email verification: {e}")
        # Return error page
        error_html = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Verification Error</title>
            <style>
                body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; text-align: center; padding: 50px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }
                .container { background: rgba(255,255,255,0.1); padding: 40px; border-radius: 15px; backdrop-filter: blur(10px); }
                .error-icon { font-size: 60px; margin-bottom: 20px; }
                .btn { background: white; color: #667eea; padding: 12px 24px; text-decoration: none; border-radius: 25px; display: inline-block; margin-top: 20px; font-weight: bold; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="error-icon">⚠️</div>
                <h1>Verification Error</h1>
                                 <p>An error occurred during email verification.</p>
                 <p>Please try again or contact support.</p>
                 <a href="/static/login.html" class="btn">Go to Login</a>
            </div>
        </body>
        </html>
        """
        return HTMLResponse(content=error_html, status_code=500)

@app.get("/auth/email-status")
async def get_email_status():
    """Check if email verification is configured"""
    email_configured = bool(SMTP_USERNAME and SMTP_PASSWORD)
    
    return {
        "email_configured": email_configured,
        "smtp_server": SMTP_SERVER if email_configured else None,
        "smtp_port": SMTP_PORT if email_configured else None,
        "app_base_url": APP_BASE_URL,
        "app_base_url_fixed": "https://kthiza-track.onrender.com" if not APP_BASE_URL or APP_BASE_URL == "http://127.0.0.1:8000" else APP_BASE_URL,
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
    print(f"📸 Profile picture upload request for user: {current_user.username} (ID: {current_user.id})")
    print(f"📸 File name: {profile_picture.filename}")
    print(f"📸 Content type: {profile_picture.content_type}")
    
    # Validate file type
    if not profile_picture.content_type.startswith('image/'):
        print(f"❌ Invalid file type: {profile_picture.content_type}")
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
                print(f"❌ User not found in database: {current_user.id}")
                raise HTTPException(status_code=404, detail="User not found")
            
            # Delete old profile picture if it exists
            if user.profile_picture_path and os.path.exists(user.profile_picture_path):
                try:
                    os.remove(user.profile_picture_path)
                    print(f"🗑️  Deleted old profile picture: {user.profile_picture_path}")
                except Exception as e:
                    print(f"⚠️  Failed to delete old profile picture: {e}")
            
            # Update profile picture path
            user.profile_picture_path = file_path
            session.commit()
            session.refresh(user)
            print(f"✅ Profile picture path updated in database: {file_path}")
        
        print(f"✅ Profile picture upload completed successfully")
        return {
            "message": "Profile picture uploaded successfully",
            "profile_picture_path": file_path
        }
        
    except Exception as e:
        print(f"❌ Profile picture upload failed: {e}")
        # Clean up file if database update fails
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"🗑️  Cleaned up failed upload file: {file_path}")
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
        cache_key = f"dashboard_meals_{user.id}_{datetime.now().date()}"
        cache.delete(cache_key)  # Properly delete the cache entry
        
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
        cache_key = f"dashboard_meals_{user.id}_{datetime.now().date()}"
        cache.delete(cache_key)  # Properly delete the cache entry
        
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
        cache_key = f"dashboard_meals_{user.id}_{datetime.now().date()}"
        cache.delete(cache_key)  # Properly delete the cache entry
        
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
        cache_key = f"dashboard_meals_{user.id}_{datetime.now().date()}"
        cache.delete(cache_key)  # Properly delete the cache entry
        
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
            "available": GOOGLE_VISION_AVAILABLE or True,  # Always available with fallback
            "successful": False,
            "error": None
        }
        
        print(f"🤖 Multi-Item AI Detection Requested: {use_ai_detection}")
        print(f"🔧 Google Vision API Available: {GOOGLE_VISION_AVAILABLE}")
        print(f"🔧 Fallback System: Always Available")
        print(f"📁 Uploaded file: {filename}")
        print(f"📁 File path: {file_path}")
        
        result = None
        if use_ai_detection:
            try:
                print(f"🔍 Starting AI detection for: {file_path}")
                # Call detection and capture structured result if available
                try:
                    from food_detection import GoogleVisionFoodDetector
                    if GOOGLE_VISION_AVAILABLE:
                        result = GoogleVisionFoodDetector().detect_food_in_image(file_path)
                    else:
                        result = None
                except Exception:
                    result = None
                # Use the structured result foods if present; otherwise fallback
                detected_foods = result.get('foods', []) if isinstance(result, dict) else []
                if not detected_foods:
                    detected_foods = identify_food_with_vision(file_path)
                ai_detection_status["successful"] = len(detected_foods) > 0
                print(f"🎯 Multi-Item AI Detection Results: {detected_foods}")
                print(f"✅ AI Detection Success: {ai_detection_status['successful']}")
            except Exception as e:
                ai_detection_status["error"] = str(e)
                print(f"❌ AI Detection failed: {e}")
                # Even if AI detection fails, we'll continue with manual input
        
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
        
        # Use portions estimated by detector when available
        portions_g = result.get('portions_g') if isinstance(result, dict) else None
        if portions_g:
            # Keep list order weights
            ordered_portions = [float(portions_g.get(f, 0.0)) for f in food_list]
            total_protein = 0.0
            total_calories = 0.0
            for f, grams in zip(food_list, ordered_portions):
                f_lower = f.lower().strip()
                per100_p = PROTEIN_DATABASE.get(f_lower, _estimate_protein_from_food_name(f_lower))
                per100_c = CALORIE_DATABASE.get(f_lower, _estimate_calories_from_food_name(f_lower))
                total_protein += per100_p * grams / 100.0
                total_calories += per100_c * grams / 100.0
            total_protein = round(total_protein, 1)
            total_calories = round(total_calories, 1)
        else:
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
        cache_key = f"dashboard_meals_{current_user.id}_{datetime.now().date()}"
        cache.delete(cache_key)  # Properly delete the cache entry
        
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
    # Always get fresh data for goals - don't cache user goals
    # Only cache meal calculations which don't change frequently
    cache_key = f"dashboard_meals_{current_user.id}_{datetime.now().date()}"
    cached_meals = cache.get(cache_key)
    
    print(f"📊 Dashboard request for user {current_user.id} ({current_user.username})")
    
    with Session(engine) as session:
        # Always fetch fresh user data from database to get latest goals
        fresh_user = session.exec(select(User).where(User.id == current_user.id)).first()
        if not fresh_user:
            print(f"❌ User {current_user.id} not found in database")
            raise HTTPException(status_code=404, detail="User not found")
        
        print(f"✅ Fresh user data loaded: protein_goal={fresh_user.protein_goal}, calorie_goal={fresh_user.calorie_goal}")
        
        # Use cached meal data if available, otherwise fetch from database
        if cached_meals and cached_meals.get('value') and cached_meals['expires_at'] > time.time():
            print(f"📊 Using cached meal data for user {current_user.id}")
            today_protein = cached_meals['value']['today_protein']
            today_calories = cached_meals['value']['today_calories']
            weekly_protein = cached_meals['value']['weekly_protein']
            weekly_calories = cached_meals['value']['weekly_calories']
            today_meals_count = cached_meals['value']['today_meals_count']
            weekly_meals_count = cached_meals['value']['weekly_meals_count']
            all_meals_count = cached_meals['value']['all_meals_count']
            overall_stats = cached_meals['value']['overall_stats']
        else:
            print(f"📊 Fetching fresh meal data for user {current_user.id}")
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
            
            today_meals_count = len(today_meals)
            weekly_meals_count = len(weekly_meals)
            all_meals_count = len(all_meals)
            overall_stats = {
                "total_meals": len(all_meals),
                "average_protein_per_meal": round(sum(m.total_protein for m in all_meals) / len(all_meals) if all_meals else 0, 1),
                "total_protein_tracked": round(sum(m.total_protein for m in all_meals), 1)
            }
        
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
                "meals_count": today_meals_count,
                "remaining_protein": round(max(0, (fresh_user.protein_goal or 0) - today_protein), 1)
            },
            "weekly": {
                "total_calories": round(weekly_calories, 1),
                "average_daily": round(weekly_calories / 7, 1),
                "meals_count": weekly_meals_count
            },
            "overall": overall_stats
        }
        
        # Cache only meal calculations, not user goals
        meal_cache_data = {
            "today_protein": today_protein,
            "today_calories": today_calories,
            "weekly_protein": weekly_protein,
            "weekly_calories": weekly_calories,
            "today_meals_count": today_meals_count,
            "weekly_meals_count": weekly_meals_count,
            "all_meals_count": all_meals_count,
            "overall_stats": overall_stats
        }
        cache.set(cache_key, meal_cache_data, ttl=120)
        
        print(f"📊 Dashboard response: protein_goal={result['user']['protein_goal']}, calorie_goal={result['user']['calorie_goal']}")
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