from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Depends, Query
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import FileResponse
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
    load_dotenv()
except ImportError:
    print("Warning: python-dotenv not installed. Install with: pip install python-dotenv")

# Configure email settings (you'll need to set these environment variables)
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
APP_BASE_URL = os.getenv("APP_BASE_URL", "http://127.0.0.1:8000")

# Import Google Vision food detection (REST via requests; no heavy client required)
try:
    from food_detection import identify_food_with_google_vision, identify_food_local
    GOOGLE_VISION_AVAILABLE = bool(os.getenv("GOOGLE_VISION_API_KEY"))
    if GOOGLE_VISION_AVAILABLE:
        print("✅ Google Vision API configured (env var GOOGLE_VISION_API_KEY found)")
    else:
        print("ℹ️  Google Vision API is required for high-quality food detection.")
except ImportError:
    GOOGLE_VISION_AVAILABLE = False
    print("Warning: food_detection module not importable. Ensure the file exists.")

# For backward compatibility
LOCAL_AI_AVAILABLE = GOOGLE_VISION_AVAILABLE

# Enhanced protein database (values per 100g); harmonized with detection module
PROTEIN_DATABASE = {
    # Meats & Poultry
    "chicken": 31.0, "chicken breast": 31.0, "chicken thigh": 28.0, "chicken wing": 30.0,
    "beef": 26.0, "steak": 26.0, "ground beef": 26.0, "beef burger": 26.0, "burger": 26.0,
    "pork": 25.0, "pork chop": 25.0, "bacon": 37.0, "ham": 22.0, "sausage": 18.0,
    "salmon": 20.0, "tuna": 30.0, "cod": 18.0, "tilapia": 26.0, "fish": 20.0,
    "turkey": 29.0, "duck": 23.0, "lamb": 25.0, "shrimp": 24.0, "prawns": 24.0,
    
    # Dairy & Eggs
    "egg": 13.0, "eggs": 13.0, "milk": 3.4, "cheese": 25.0, "cheddar": 25.0,
    "yogurt": 10.0, "greek yogurt": 10.0, "cottage cheese": 11.0, "cream cheese": 6.0,
    
    # Nuts & Seeds
    "peanut butter": 25.0, "almonds": 21.0, "walnuts": 15.0, "cashews": 18.0,
    "sunflower seeds": 21.0, "chia seeds": 17.0, "pumpkin seeds": 19.0,
    
    # Plant-based Proteins
    "tofu": 8.0, "tempeh": 20.0, "lentils": 9.0, "beans": 21.0, "black beans": 21.0,
    "kidney beans": 24.0, "chickpeas": 19.0, "edamame": 11.0, "hummus": 8.0,
    
    # Grains & Cereals
    "quinoa": 14.0, "rice": 2.7, "brown rice": 2.7, "bread": 9.0, "whole wheat bread": 13.0,
    "pasta": 13.0, "spaghetti": 13.0, "oatmeal": 13.0, "oats": 13.0, "cereal": 10.0,
    
    # Vegetables
    "broccoli": 2.8, "spinach": 2.9, "kale": 4.3, "asparagus": 2.2, "brussels sprouts": 3.4,
    "cauliflower": 1.9, "peas": 5.4, "corn": 3.2, "potato": 2.0, "sweet potato": 1.6,
    
    # Fast Food & Common Meals (adjusted for typical serving sizes)
    "pizza": 25.0, "pizza slice": 12.0, "hamburger": 35.0, "hot dog": 15.0,
    "sandwich": 20.0, "wrap": 20.0, "taco": 18.0, "burrito": 25.0,
    "noodles": 20.0, "ramen": 20.0, "soup": 12.0, "salad": 8.0,
    
    # Breakfast Foods
    "pancakes": 6.0, "waffles": 6.0, "french toast": 8.0, "bagel": 10.0,
    "muffin": 5.0, "croissant": 8.0, "english muffin": 8.0,
    
    # Snacks & Others
    "protein bar": 20.0, "protein shake": 25.0, "smoothie": 8.0,
    "ice cream": 4.0, "chocolate": 5.0, "cookies": 5.0, "cake": 4.0
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

def is_valid_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def send_verification_email(email: str, username: str, token: str):
    """Send verification email"""
    if not SMTP_USERNAME or not SMTP_PASSWORD:
        print(f"⚠️  Email verification not configured!")
        print(f"   For user {username} ({email}), verification token: {token}")
        print(f"   To enable email verification, run: python setup_env.py")
        return False
    
    try:
        msg = MIMEMultipart()
        msg['From'] = SMTP_USERNAME
        msg['To'] = email
        msg['Subject'] = "Verify your Protein Tracker account"
        
        verification_url = f"{APP_BASE_URL.rstrip('/')}/auth/verify/{token}"
        body = f"""
        Hello {username}!
        
        Welcome to Protein Tracker! Please verify your email address by clicking the link below:
        
        {verification_url}
        
        If you didn't create this account, please ignore this email.
        
        Best regards,
        Protein Tracker Team
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
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
    """Calculate total protein content for multi-item meals with smart portion adjustment"""
    raw_protein = 0.0
    matched_foods = []
    
    for food_item in food_items:
        food_lower = food_item.lower().strip()
        found_match = False
        
        if food_lower in PROTEIN_DATABASE:
            protein_value = PROTEIN_DATABASE[food_lower]
            raw_protein += protein_value
            matched_foods.append(food_item)
            found_match = True
            print(f"   ✅ Matched '{food_item}' -> {protein_value}g protein")
        else:
            for db_item, protein_value in PROTEIN_DATABASE.items():
                if db_item in food_lower or food_lower in db_item:
                    raw_protein += protein_value
                    matched_foods.append(food_item)
                    found_match = True
                    print(f"   ✅ Matched '{food_item}' -> {protein_value}g protein (via '{db_item}')")
                    break
        
        if not found_match:
            # Try to estimate protein based on food type
            estimated_protein = _estimate_protein_from_food_name(food_lower)
            raw_protein += estimated_protein
            print(f"   ⚠️  No exact match for '{food_item}' -> {estimated_protein}g protein (estimated)")
    
    # Apply smart portion adjustment based on number of items
    portion_multiplier = _calculate_portion_multiplier(len(food_items))
    total_protein = raw_protein * portion_multiplier
    
    print(f"📊 Raw protein sum: {raw_protein:.1f}g")
    print(f"📊 Portion multiplier: {portion_multiplier:.2f}x")
    print(f"📊 Adjusted protein calculation: {total_protein:.1f}g from {len(food_items)} items")
    return round(total_protein, 1), matched_foods

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
        return 13.0
    elif any(word in food_name for word in ['rice', 'quinoa', 'oatmeal', 'cereal']):
        return 8.0
    elif any(word in food_name for word in ['pizza', 'slice']):
        return 20.0
    
    # Vegetables
    elif any(word in food_name for word in ['salad', 'vegetable', 'broccoli', 'spinach', 'kale']):
        return 3.0
    
    # Nuts and seeds
    elif any(word in food_name for word in ['nut', 'seed', 'almond', 'peanut']):
        return 20.0
    
    # Fast food and processed foods
    elif any(word in food_name for word in ['burger', 'hot dog', 'taco', 'burrito']):
        return 25.0
    elif any(word in food_name for word in ['fries', 'chips', 'snack']):
        return 5.0
    
    # Desserts and sweets
    elif any(word in food_name for word in ['cake', 'cookie', 'dessert', 'sweet', 'chocolate']):
        return 4.0
    
    # Default for unknown foods
    else:
        return 8.0  # Reasonable default for mixed/complex foods

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
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/static/login.html")

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
        
        # Local testing: allow auto-verify when email not configured
        if not email_configured:
            print("ℹ️  Email not configured; accounts will be auto-verified.")
        
        user = User(
            username=username,
            email=email,
            password_hash=password_hash,
            verification_token=verification_token,
            email_verified=email_configured or True
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
            "email_configured": email_configured
        }

@app.post("/auth/login")
async def login_user(username: str = Form(...), password: str = Form(...)):
    with Session(engine) as session:
        user = session.exec(select(User).where(User.username == username)).first()
        
        if not user or not verify_password(password, user.password_hash):
            raise HTTPException(status_code=401, detail="Invalid username or password")
        
        # Optionally enforce verification if email is configured
        # if SMTP_USERNAME and SMTP_PASSWORD and not user.email_verified:
        #     raise HTTPException(status_code=401, detail="Please verify your email before logging in")
        
        return {
            "message": "Login successful",
            "user_id": user.id,
            "username": user.username,
            "email": user.email,
            "weight_kg": user.weight_kg,
            "protein_goal": round(user.protein_goal, 1) if user.protein_goal else None,
            "last_weight_update": user.last_weight_update.isoformat() if user.last_weight_update else None,
            "token": str(user.id)  # Simple token for now
        }

@app.get("/auth/verify/{token}")
async def verify_email(token: str):
    with Session(engine) as session:
        user = session.exec(select(User).where(User.verification_token == token)).first()
        
        if not user:
            raise HTTPException(status_code=404, detail="Invalid verification token")
        
        user.email_verified = True
        user.verification_token = None
        session.commit()
        
        return {
            "message": "Email verified successfully! You can now log in.",
            "username": user.username
        }

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
        
        # Update weight, activity level, and protein goal
        user.weight_kg = weight_kg
        user.activity_level = activity_level
        user.protein_goal = calculate_protein_goal(weight_kg, activity_level)
        user.last_weight_update = datetime.now()
        
        session.commit()
        session.refresh(user)
        
        return {
            "message": "Weight updated successfully",
            "weight_kg": user.weight_kg,
            "activity_level": user.activity_level,
            "protein_goal": round(user.protein_goal, 1) if user.protein_goal else None,
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
        
        return {
            "message": "Protein goal updated successfully",
            "protein_goal": round(user.protein_goal, 1) if user.protein_goal else None
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
        
        # Update activity level and recalculate protein goal if weight exists
        user.activity_level = activity_level
        if user.weight_kg:
            user.protein_goal = calculate_protein_goal(user.weight_kg, activity_level)
        
        session.commit()
        session.refresh(user)
        
        return {
            "message": "Activity level updated successfully",
            "activity_level": user.activity_level,
            "protein_goal": round(user.protein_goal, 1) if user.protein_goal else None
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
        
        with Session(engine) as session:
            meal = Meal(
                user_id=current_user.id,
                image_path=file_path,
                food_items=json.dumps(food_list),
                total_protein=total_protein
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
        today = datetime.now().date()
        today_meals = session.exec(select(Meal).where(
            Meal.user_id == current_user.id,
            func.date(Meal.created_at) == today
        )).all()
        
        today_protein = round(sum(meal.total_protein for meal in today_meals), 1)
        
        all_meals = session.exec(select(Meal).where(Meal.user_id == current_user.id)).all()
        
        week_ago = datetime.now().date() - timedelta(days=7)
        weekly_meals = session.exec(select(Meal).where(
            Meal.user_id == current_user.id,
            func.date(Meal.created_at) >= week_ago
        )).all()
        weekly_protein = round(sum(meal.total_protein for meal in weekly_meals), 1)
        
        # Check if user needs weight update (weekly popup)
        needs_weight_update = False
        if current_user.last_weight_update:
            days_since_update = (datetime.now() - current_user.last_weight_update).days
            needs_weight_update = days_since_update >= 7
        else:
            needs_weight_update = True  # First time user
        
        result = {
            "user": {
                "id": current_user.id,
                "username": current_user.username,
                "weight_kg": current_user.weight_kg,
                "protein_goal": round(current_user.protein_goal, 1) if current_user.protein_goal else None,
                "last_weight_update": current_user.last_weight_update.isoformat() if current_user.last_weight_update else None,
                "needs_weight_update": needs_weight_update,
                "profile_picture_path": current_user.profile_picture_path
            },
            "today": {
                "total_protein": round(today_protein, 1),
                "goal_progress": round((today_protein / current_user.protein_goal) * 100 if current_user.protein_goal else 0, 1),
                "meals_count": len(today_meals),
                "remaining_protein": round(max(0, (current_user.protein_goal or 0) - today_protein), 1)
            },
            "weekly": {
                "total_protein": round(weekly_protein, 1),
                "average_daily": round(weekly_protein / 7, 1),
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
    print("🚀 Starting Protein Tracker Server...")
    print("📍 Server will be available at:")
    print("   • http://127.0.0.1:8000")
    print("   • http://localhost:8000")
    print("🔧 Press Ctrl+C to stop the server")
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=False) 