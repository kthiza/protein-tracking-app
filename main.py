from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlmodel import SQLModel, create_engine, Session, select, Field
from typing import List, Optional
import os
from datetime import datetime, timedelta
import json
import hashlib
import secrets
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import re

# Configure email settings (you'll need to set these environment variables)
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")

# Try to import Google Cloud Vision (optional)
try:
    from google.cloud import vision
    GOOGLE_VISION_AVAILABLE = True
except ImportError:
    GOOGLE_VISION_AVAILABLE = False

# Enhanced protein database
PROTEIN_DATABASE = {
    "chicken breast": 31, "salmon": 22, "tuna": 26, "beef": 26, "pork": 25,
    "turkey": 29, "eggs": 6, "milk": 8, "yogurt": 10, "cheese": 7,
    "tofu": 8, "lentils": 9, "beans": 7, "rice": 2, "broccoli": 3,
    "almonds": 6, "peanut butter": 4, "bread": 3, "pasta": 4,
    "spinach": 3, "quinoa": 4, "chickpeas": 9, "edamame": 11
}

# Database setup
DATABASE_URL = "sqlite:///./protein_app.db"
engine = create_engine(DATABASE_URL, echo=False)

# Security
security = HTTPBearer()

# Models
class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True)
    email: str = Field(unique=True, index=True)
    password_hash: str
    weight_kg: Optional[float] = Field(default=None)
    protein_goal: Optional[float] = Field(default=None)
    last_weight_update: Optional[datetime] = Field(default=None)
    email_verified: bool = Field(default=False)
    verification_token: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Meal(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    image_path: str
    food_items: str
    total_protein: float
    created_at: datetime = Field(default_factory=datetime.utcnow)

from contextlib import asynccontextmanager

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

async def cleanup_old_meals():
    """Background task to clean up old meal images and data"""
    import asyncio
    while True:
        try:
            # Wait for 24 hours
            await asyncio.sleep(24 * 60 * 60)  # 24 hours in seconds
            
            with Session(engine) as session:
                # Find meals older than 24 hours
                cutoff_time = datetime.utcnow() - timedelta(hours=24)
                old_meals = session.exec(
                    select(Meal).where(Meal.created_at < cutoff_time)
                ).all()
                
                for meal in old_meals:
                    # Delete the image file
                    if os.path.exists(meal.image_path):
                        try:
                            os.remove(meal.image_path)
                            print(f"Deleted old meal image: {meal.image_path}")
                        except Exception as e:
                            print(f"Failed to delete image {meal.image_path}: {e}")
                    
                    # Delete the meal record
                    session.delete(meal)
                
                session.commit()
                
                if old_meals:
                    print(f"Cleaned up {len(old_meals)} old meals")
                else:
                    print("No old meals to clean up")
                    
        except Exception as e:
            print(f"Error in cleanup task: {e}")
            await asyncio.sleep(60)  # Wait 1 minute before retrying

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    create_db_and_tables()
    # Start background cleanup task
    import asyncio
    cleanup_task = asyncio.create_task(cleanup_old_meals())
    yield
    # Shutdown
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass

# Create FastAPI app
app = FastAPI(title="Protein Tracking App", version="4.0.0", lifespan=lifespan)

# Add CORS middleware
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

def hash_password(password: str) -> str:
    """Hash a password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its hash"""
    return hash_password(password) == hashed

def generate_verification_token() -> str:
    """Generate a random verification token"""
    return secrets.token_urlsafe(32)

def is_valid_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def send_verification_email(email: str, username: str, token: str):
    """Send verification email"""
    if not SMTP_USERNAME or not SMTP_PASSWORD:
        print(f"Email verification token for {username}: {token}")
        return
    
    try:
        msg = MIMEMultipart()
        msg['From'] = SMTP_USERNAME
        msg['To'] = email
        msg['Subject'] = "Verify your Protein Tracker account"
        
        body = f"""
        Hello {username}!
        
        Welcome to Protein Tracker! Please verify your email address by clicking the link below:
        
        http://localhost:8000/verify/{token}
        
        If you didn't create this account, please ignore this email.
        
        Best regards,
        Protein Tracker Team
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()
    except Exception as e:
        print(f"Failed to send email: {e}")

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """Get current user from token"""
    token = credentials.credentials
    
    with Session(engine) as session:
        # For now, we'll use a simple token system
        # In production, you'd want to use JWT tokens
        user = session.exec(select(User).where(User.id == int(token))).first()
        if not user:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user

def calculate_protein_enhanced(food_items: List[str]) -> tuple[float, List[str]]:
    total_protein = 0.0
    matched_foods = []
    
    for food_item in food_items:
        food_lower = food_item.lower().strip()
        found_match = False
        
        if food_lower in PROTEIN_DATABASE:
            total_protein += PROTEIN_DATABASE[food_lower]
            matched_foods.append(food_item)
            found_match = True
        else:
            for db_item, protein_value in PROTEIN_DATABASE.items():
                if db_item in food_lower or food_lower in db_item:
                    total_protein += protein_value
                    matched_foods.append(food_item)
                    found_match = True
                    break
        
        if not found_match:
            total_protein += 5.0
    
    return round(total_protein, 1), matched_foods

def identify_food_with_vision(image_path: str) -> List[str]:
    if not GOOGLE_VISION_AVAILABLE:
        return []
    
    try:
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            return []
        
        client_options = {"api_key": api_key}
        client = vision.ImageAnnotatorClient(client_options=client_options)
        
        with open(image_path, 'rb') as image_file:
            content = image_file.read()
        
        image = vision.Image(content=content)
        response = client.label_detection(image=image)
        labels = response.label_annotations
        
        food_keywords = ['food', 'dish', 'meal', 'meat', 'fish', 'dairy', 'vegetable', 'fruit', 'protein']
        food_items = []
        
        for label in labels:
            label_text = label.description.lower()
            if any(keyword in label_text for keyword in food_keywords):
                food_items.append(label_text)
        
        return list(set(food_items))
    except Exception as e:
        print(f"Vision API error: {e}")
        return []

@app.get("/")
async def root():
    return {
        "message": "Protein Tracking App API",
        "version": "4.0.0",
        "features": {
            "google_vision_available": GOOGLE_VISION_AVAILABLE,
            "enhanced_protein_calculation": True,
            "user_management": True,
            "meal_tracking": True,
            "dashboard": True,
            "email_verification": True
        }
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
        
        user = User(
            username=username,
            email=email,
            password_hash=password_hash,
            verification_token=verification_token
        )
        
        session.add(user)
        session.commit()
        session.refresh(user)
        
        # Send verification email
        send_verification_email(email, username, verification_token)
        
        return {
            "message": "Account created successfully! Please check your email to verify your account.",
            "user_id": user.id,
            "username": user.username,
            "email": user.email
        }

@app.post("/auth/login")
async def login_user(username: str = Form(...), password: str = Form(...)):
    with Session(engine) as session:
        user = session.exec(select(User).where(User.username == username)).first()
        
        if not user or not verify_password(password, user.password_hash):
            raise HTTPException(status_code=401, detail="Invalid username or password")
        
        if not user.email_verified:
            raise HTTPException(status_code=401, detail="Please verify your email before logging in")
        
        return {
            "message": "Login successful",
            "user_id": user.id,
            "username": user.username,
            "email": user.email,
            "weight_kg": user.weight_kg,
            "protein_goal": user.protein_goal,
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

@app.get("/users/profile", response_model=dict)
async def get_user_profile(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "weight_kg": current_user.weight_kg,
        "protein_goal": current_user.protein_goal,
        "last_weight_update": current_user.last_weight_update.isoformat() if current_user.last_weight_update else None,
        "email_verified": current_user.email_verified,
        "created_at": current_user.created_at.isoformat()
    }

@app.post("/users/update-weight")
async def update_weight(
    current_user: User = Depends(get_current_user),
    weight_kg: float = Form(...)
):
    """Update user weight and recalculate protein goal"""
    if weight_kg <= 0:
        raise HTTPException(status_code=400, detail="Weight must be greater than 0")
    
    with Session(engine) as session:
        user = session.exec(select(User).where(User.id == current_user.id)).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Update weight and protein goal
        user.weight_kg = weight_kg
        user.protein_goal = weight_kg * 1.6  # Recalculate protein goal
        user.last_weight_update = datetime.utcnow()
        
        session.commit()
        session.refresh(user)
        
        return {
            "message": "Weight updated successfully",
            "weight_kg": user.weight_kg,
            "protein_goal": user.protein_goal,
            "last_weight_update": user.last_weight_update.isoformat()
        }

@app.post("/meals/upload/")
async def upload_meal(
    current_user: User = Depends(get_current_user),
    image: UploadFile = File(...),
    food_items: str = Form(""),
    use_ai_detection: bool = Form(False)
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
        
        if use_ai_detection and GOOGLE_VISION_AVAILABLE:
            detected_foods = identify_food_with_vision(file_path)
        else:
            detected_foods = []
        
        if food_items:
            manual_foods = [item.strip() for item in food_items.split(",")]
        else:
            manual_foods = []
        
        if detected_foods and manual_foods:
            food_list = list(set(detected_foods + manual_foods))
        elif detected_foods:
            food_list = detected_foods
        elif manual_foods:
            food_list = manual_foods
        else:
            food_list = ["chicken breast", "rice", "broccoli"]
        
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
        
        return {
            "message": "Meal processed successfully",
            "meal_id": meal.id,
            "food_items": food_list,
            "matched_foods": matched_foods,
            "total_protein": total_protein,
            "user_protein_goal": current_user.protein_goal,
            "ai_detection_used": use_ai_detection and GOOGLE_VISION_AVAILABLE,
            "google_vision_available": GOOGLE_VISION_AVAILABLE
        }
        
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Error processing meal: {str(e)}")

@app.get("/dashboard")
async def get_dashboard_data(current_user: User = Depends(get_current_user)):
    with Session(engine) as session:
        today = datetime.now().date()
        today_meals = session.exec(select(Meal).where(
            Meal.user_id == current_user.id,
            Meal.created_at >= today
        )).all()
        
        today_protein = sum(meal.total_protein for meal in today_meals)
        
        all_meals = session.exec(select(Meal).where(Meal.user_id == current_user.id)).all()
        
        week_ago = datetime.now().date() - timedelta(days=7)
        weekly_meals = session.exec(select(Meal).where(
            Meal.user_id == current_user.id,
            Meal.created_at >= week_ago
        )).all()
        weekly_protein = sum(meal.total_protein for meal in weekly_meals)
        
        # Check if user needs weight update (weekly popup)
        needs_weight_update = False
        if current_user.last_weight_update:
            days_since_update = (datetime.utcnow() - current_user.last_weight_update).days
            needs_weight_update = days_since_update >= 7
        else:
            needs_weight_update = True  # First time user
        
        return {
            "user": {
                "id": current_user.id,
                "username": current_user.username,
                "weight_kg": current_user.weight_kg,
                "protein_goal": current_user.protein_goal,
                "last_weight_update": current_user.last_weight_update.isoformat() if current_user.last_weight_update else None,
                "needs_weight_update": needs_weight_update
            },
            "today": {
                "total_protein": today_protein,
                "goal_progress": (today_protein / current_user.protein_goal) * 100 if current_user.protein_goal else 0,
                "meals_count": len(today_meals),
                "remaining_protein": max(0, (current_user.protein_goal or 0) - today_protein)
            },
            "weekly": {
                "total_protein": weekly_protein,
                "average_daily": weekly_protein / 7,
                "meals_count": len(weekly_meals)
            },
            "overall": {
                "total_meals": len(all_meals),
                "average_protein_per_meal": sum(m.total_protein for m in all_meals) / len(all_meals) if all_meals else 0,
                "total_protein_tracked": sum(m.total_protein for m in all_meals)
            }
        }

@app.get("/meals")
async def get_user_meals(current_user: User = Depends(get_current_user)):
    with Session(engine) as session:
        meals = session.exec(
            select(Meal).where(Meal.user_id == current_user.id).order_by(Meal.created_at.desc())
        ).all()
        
        return [
            {
                "id": meal.id,
                "food_items": json.loads(meal.food_items),
                "total_protein": meal.total_protein,
                "created_at": meal.created_at.isoformat()
            }
            for meal in meals
        ]

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
            cutoff_time = datetime.utcnow() - timedelta(hours=1)
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
    uvicorn.run(app, host="0.0.0.0", port=8000) 