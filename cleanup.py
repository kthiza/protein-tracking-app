#!/usr/bin/env python3
"""
Database Utilities and Cleanup Script for Protein Tracker App

This script provides various utilities for managing the database:
- List all users and their verification status
- Manually verify user accounts
- Reset user passwords
- Clean up old meal data and images
- Database maintenance and optimization
"""

import os
import sys
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import List, Optional

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from sqlmodel import SQLModel, create_engine, Session, select, func
    from sqlalchemy import text
except ImportError as e:
    print(f"❌ Error importing SQLModel: {e}")
    print("Please install required dependencies: pip install -r requirements.txt")
    sys.exit(1)

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./protein_app.db?check_same_thread=False")
engine = create_engine(DATABASE_URL, echo=False)

# Import models from main.py
try:
    from main import User, Meal, hash_password, verify_password
except ImportError as e:
    print(f"❌ Error importing models from main.py: {e}")
    print("Make sure main.py is in the same directory")
    sys.exit(1)

def print_header(title: str):
    """Print a formatted header"""
    print("\n" + "="*60)
    print(f" {title}")
    print("="*60)

def print_success(message: str):
    """Print a success message"""
    print(f"✅ {message}")

def print_error(message: str):
    """Print an error message"""
    print(f"❌ {message}")

def print_info(message: str):
    """Print an info message"""
    print(f"ℹ️  {message}")

def list_all_users():
    """List all users in the database"""
    print_header("All Users in Database")
    
    with Session(engine) as session:
        users = session.exec(select(User).order_by(User.created_at.desc())).all()
        
        if not users:
            print("No users found in the database.")
            return
        
        print(f"Total users: {len(users)}")
        print("\n{:<4} {:<15} {:<25} {:<10} {:<12} {:<15}".format(
            "ID", "Username", "Email", "Verified", "Weight", "Protein Goal"
        ))
        print("-" * 85)
        
        for user in users:
            verified = "✅ Yes" if user.email_verified else "❌ No"
            weight = f"{user.weight_kg}kg" if user.weight_kg else "Not set"
            protein_goal = f"{user.protein_goal}g" if user.protein_goal else "Not set"
            
            print("{:<4} {:<15} {:<25} {:<10} {:<12} {:<15}".format(
                user.id, 
                user.username[:14], 
                user.email[:24], 
                verified, 
                weight, 
                protein_goal
            ))

def verify_user_account():
    """Manually verify a user account"""
    print_header("Manual Account Verification")
    
    username = input("Enter username to verify: ").strip()
    if not username:
        print_error("Username is required")
        return
    
    with Session(engine) as session:
        user = session.exec(select(User).where(User.username == username)).first()
        
        if not user:
            print_error(f"User '{username}' not found")
            return
        
        if user.email_verified:
            print_info(f"User '{username}' is already verified")
            return
        
        # Verify the account
        user.email_verified = True
        user.verification_token = None
        session.commit()
        
        print_success(f"User '{username}' has been verified successfully!")
        print_info(f"Email: {user.email}")
        print_info(f"Created: {user.created_at.strftime('%Y-%m-%d %H:%M:%S')}")

def reset_user_password():
    """Reset a user's password"""
    print_header("Reset User Password")
    
    username = input("Enter username: ").strip()
    if not username:
        print_error("Username is required")
        return
    
    with Session(engine) as session:
        user = session.exec(select(User).where(User.username == username)).first()
        
        if not user:
            print_error(f"User '{username}' not found")
            return
        
        # Generate new password
        new_password = secrets.token_urlsafe(8)
        password_hash = hash_password(new_password)
        
        # Update password
        user.password_hash = password_hash
        session.commit()
        
        print_success(f"Password reset for user '{username}'")
        print_info(f"New password: {new_password}")
        print_info("Please share this password with the user securely")

def delete_user():
    """Delete a user and all their data"""
    print_header("Delete User")
    
    username = input("Enter username to delete: ").strip()
    if not username:
        print_error("Username is required")
        return
    
    confirm = input(f"Are you sure you want to delete user '{username}' and ALL their data? (yes/no): ").strip().lower()
    if confirm != 'yes':
        print_info("Deletion cancelled")
        return
    
    with Session(engine) as session:
        user = session.exec(select(User).where(User.username == username)).first()
        
        if not user:
            print_error(f"User '{username}' not found")
            return
        
        # Get user's meals
        meals = session.exec(select(Meal).where(Meal.user_id == user.id)).all()
        
        # Delete meal images
        deleted_images = 0
        for meal in meals:
            if os.path.exists(meal.image_path):
                try:
                    os.remove(meal.image_path)
                    deleted_images += 1
                except Exception as e:
                    print_error(f"Failed to delete image {meal.image_path}: {e}")
        
        # Delete profile picture
        if user.profile_picture_path and os.path.exists(user.profile_picture_path):
            try:
                os.remove(user.profile_picture_path)
                print_info("Profile picture deleted")
            except Exception as e:
                print_error(f"Failed to delete profile picture: {e}")
        
        # Delete meals
        for meal in meals:
            session.delete(meal)
        
        # Delete user
        session.delete(user)
        session.commit()
        
        print_success(f"User '{username}' deleted successfully")
        print_info(f"Deleted {len(meals)} meals")
        print_info(f"Deleted {deleted_images} meal images")

def cleanup_old_meals():
    """Clean up old meal data and images"""
    print_header("Clean Up Old Meals")
    
    days = input("Delete meals older than how many days? (default: 30): ").strip()
    if not days:
        days = "30"
    
    try:
        days = int(days)
        if days < 1:
            print_error("Days must be at least 1")
            return
    except ValueError:
        print_error("Invalid number of days")
        return
    
    cutoff_date = datetime.now() - timedelta(days=days)
    
    with Session(engine) as session:
        # Find old meals
        old_meals = session.exec(
            select(Meal).where(Meal.created_at < cutoff_date)
        ).all()
        
        if not old_meals:
            print_info(f"No meals older than {days} days found")
            return
        
        print_info(f"Found {len(old_meals)} meals older than {days} days")
        
        # Delete meal images
        deleted_images = 0
        for meal in old_meals:
            if os.path.exists(meal.image_path):
                try:
                    os.remove(meal.image_path)
                    deleted_images += 1
                except Exception as e:
                    print_error(f"Failed to delete image {meal.image_path}: {e}")
        
        # Delete meal records
        for meal in old_meals:
            session.delete(meal)
        
        session.commit()
        
        print_success(f"Cleanup completed successfully")
        print_info(f"Deleted {len(old_meals)} meal records")
        print_info(f"Deleted {deleted_images} meal images")

def database_stats():
    """Show database statistics"""
    print_header("Database Statistics")
    
    with Session(engine) as session:
        # User stats
        total_users = session.exec(select(func.count(User.id))).first()
        verified_users = session.exec(select(func.count(User.id)).where(User.email_verified == True)).first()
        unverified_users = session.exec(select(func.count(User.id)).where(User.email_verified == False)).first()
        
        # Meal stats
        total_meals = session.exec(select(func.count(Meal.id))).first()
        today_meals = session.exec(
            select(func.count(Meal.id)).where(func.date(Meal.created_at) == datetime.now().date())
        ).first()
        
        # Protein stats
        total_protein = session.exec(select(func.sum(Meal.total_protein))).first() or 0
        avg_protein_per_meal = session.exec(select(func.avg(Meal.total_protein))).first() or 0
        
        print(f"Users:")
        print(f"  Total users: {total_users}")
        print(f"  Verified: {verified_users}")
        print(f"  Unverified: {unverified_users}")
        print(f"  Verification rate: {(verified_users/total_users*100):.1f}%" if total_users > 0 else "  Verification rate: N/A")
        
        print(f"\nMeals:")
        print(f"  Total meals: {total_meals}")
        print(f"  Today's meals: {today_meals}")
        print(f"  Total protein tracked: {total_protein:.1f}g")
        print(f"  Average protein per meal: {avg_protein_per_meal:.1f}g" if avg_protein_per_meal else "  Average protein per meal: N/A")
        
        # File system stats
        uploads_dir = "uploads"
        profile_dir = "profile_pictures"
        
        if os.path.exists(uploads_dir):
            upload_files = len([f for f in os.listdir(uploads_dir) if os.path.isfile(os.path.join(uploads_dir, f))])
            print(f"\nFiles:")
            print(f"  Meal images: {upload_files}")
        
        if os.path.exists(profile_dir):
            profile_files = len([f for f in os.listdir(profile_dir) if os.path.isfile(os.path.join(profile_dir, f))])
            print(f"  Profile pictures: {profile_files}")

def optimize_database():
    """Optimize database performance"""
    print_header("Database Optimization")
    
    with Session(engine) as session:
        try:
            # Create indexes if they don't exist
            session.exec(text("CREATE INDEX IF NOT EXISTS idx_meals_user_created ON meal (user_id, created_at)"))
            session.exec(text("CREATE INDEX IF NOT EXISTS idx_meals_created_at ON meal (created_at)"))
            session.exec(text("CREATE INDEX IF NOT EXISTS idx_meals_user_id ON meal (user_id)"))
            
            # Analyze database
            session.exec(text("ANALYZE"))
            
            session.commit()
            print_success("Database optimization completed")
            print_info("Indexes created/verified")
            print_info("Database analyzed for query optimization")
            
        except Exception as e:
            print_error(f"Database optimization failed: {e}")

def export_user_data():
    """Export user data to CSV"""
    print_header("Export User Data")
    
    filename = input("Enter filename for export (default: user_export.csv): ").strip()
    if not filename:
        filename = "user_export.csv"
    
    if not filename.endswith('.csv'):
        filename += '.csv'
    
    try:
        import csv
        
        with Session(engine) as session:
            users = session.exec(select(User).order_by(User.created_at.desc())).all()
            
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['id', 'username', 'email', 'email_verified', 'weight_kg', 
                             'protein_goal', 'activity_level', 'created_at']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for user in users:
                    writer.writerow({
                        'id': user.id,
                        'username': user.username,
                        'email': user.email,
                        'email_verified': user.email_verified,
                        'weight_kg': user.weight_kg,
                        'protein_goal': user.protein_goal,
                        'activity_level': user.activity_level,
                        'created_at': user.created_at.isoformat() if user.created_at else None
                    })
        
        print_success(f"User data exported to {filename}")
        print_info(f"Exported {len(users)} users")
        
    except ImportError:
        print_error("CSV module not available")
    except Exception as e:
        print_error(f"Export failed: {e}")

def main_menu():
    """Display the main menu"""
    while True:
        print_header("Protein Tracker - Database Utilities")
        print("1. List all users")
        print("2. Verify user account")
        print("3. Reset user password")
        print("4. Delete user")
        print("5. Clean up old meals")
        print("6. Database statistics")
        print("7. Optimize database")
        print("8. Export user data")
        print("0. Exit")
        
        choice = input("\nSelect an option: ").strip()
        
        if choice == "1":
            list_all_users()
        elif choice == "2":
            verify_user_account()
        elif choice == "3":
            reset_user_password()
        elif choice == "4":
            delete_user()
        elif choice == "5":
            cleanup_old_meals()
        elif choice == "6":
            database_stats()
        elif choice == "7":
            optimize_database()
        elif choice == "8":
            export_user_data()
        elif choice == "0":
            print_info("Goodbye!")
            break
        else:
            print_error("Invalid option. Please try again.")
        
        input("\nPress Enter to continue...")

if __name__ == "__main__":
    try:
        # Check if database exists
        if not os.path.exists("protein_app.db"):
            print_error("Database file 'protein_app.db' not found")
            print_info("Please run the main application first to create the database")
            sys.exit(1)
        
        main_menu()
        
    except KeyboardInterrupt:
        print("\n\nGoodbye!")
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        sys.exit(1)
