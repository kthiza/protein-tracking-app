#!/usr/bin/env python3
"""
Debug script to check calorie values in the database
"""

import sqlite3
import json
from datetime import datetime

def check_database():
    """Check the database for meal data and calorie values"""
    conn = sqlite3.connect('protein_app.db')
    cursor = conn.cursor()
    
    print("=== DATABASE DEBUG ===")
    
    # Check if meal table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='meal'")
    if not cursor.fetchone():
        print("❌ Meal table does not exist!")
        return
    
    print("✅ Meal table exists")
    
    # Check table structure
    cursor.execute("PRAGMA table_info(meal)")
    columns = cursor.fetchall()
    print("\n📋 Table structure:")
    for col in columns:
        print(f"  {col[1]} ({col[2]})")
    
    # Check if total_calories column exists
    has_calories = any(col[1] == 'total_calories' for col in columns)
    print(f"\n{'✅' if has_calories else '❌'} total_calories column exists")
    
    # Get all meals
    cursor.execute("SELECT id, user_id, food_items, total_protein, total_calories, created_at FROM meal ORDER BY created_at DESC LIMIT 10")
    meals = cursor.fetchall()
    
    print(f"\n📊 Found {len(meals)} meals (showing latest 10):")
    
    for meal in meals:
        meal_id, user_id, food_items, total_protein, total_calories, created_at = meal
        try:
            foods = json.loads(food_items) if food_items else []
        except:
            foods = []
        
        print(f"\n🍽️  Meal ID: {meal_id}")
        print(f"   User ID: {user_id}")
        print(f"   Foods: {foods}")
        print(f"   Protein: {total_protein}g")
        print(f"   Calories: {total_calories} (type: {type(total_calories)})")
        print(f"   Created: {created_at}")
        
        if total_calories == 0 or total_calories is None:
            print("   ⚠️  WARNING: Calories is 0 or None!")
    
    # Check for any meals with non-zero calories
    cursor.execute("SELECT COUNT(*) FROM meal WHERE total_calories > 0")
    non_zero_count = cursor.fetchone()[0]
    print(f"\n📈 Meals with non-zero calories: {non_zero_count}")
    
    # Check for any meals with null calories
    cursor.execute("SELECT COUNT(*) FROM meal WHERE total_calories IS NULL")
    null_count = cursor.fetchone()[0]
    print(f"📈 Meals with NULL calories: {null_count}")
    
    conn.close()

if __name__ == "__main__":
    check_database()
