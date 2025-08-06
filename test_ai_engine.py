#!/usr/bin/env python3
"""
Test script for the AI Engine (Phase 1)
This script demonstrates how to use the food identifier and protein calculator functions.
"""

import os
import sys
from ai_engine import process_meal_image, identify_food_items, calculate_protein

def test_protein_database():
    """Test the protein calculation with known food items"""
    print("=== Testing Protein Database ===")
    
    test_foods = ["chicken breast", "salmon", "eggs", "rice", "broccoli"]
    expected_proteins = [31, 22, 6, 2, 3]
    
    for food, expected in zip(test_foods, expected_proteins):
        protein = calculate_protein([food])
        print(f"{food}: {protein}g (expected: {expected}g)")
        assert protein == expected, f"Protein calculation failed for {food}"
    
    print("✅ Protein database tests passed!")

def test_food_identification():
    """Test food identification with a sample image"""
    print("\n=== Testing Food Identification ===")
    
    # Check if test image exists
    test_image = "test_meal.jpg"
    if not os.path.exists(test_image):
        print(f"⚠️  Test image '{test_image}' not found.")
        print("To test food identification, please add a food image named 'test_meal.jpg'")
        return False
    
    try:
        food_items = identify_food_items(test_image)
        print(f"Identified food items: {food_items}")
        
        if food_items:
            print("✅ Food identification test completed!")
            return True
        else:
            print("⚠️  No food items identified. This might be normal for some images.")
            return True
            
    except Exception as e:
        print(f"❌ Food identification test failed: {e}")
        return False

def test_full_pipeline():
    """Test the complete meal processing pipeline"""
    print("\n=== Testing Full Pipeline ===")
    
    test_image = "test_meal.jpg"
    if not os.path.exists(test_image):
        print(f"⚠️  Test image '{test_image}' not found. Skipping full pipeline test.")
        return False
    
    try:
        result = process_meal_image(test_image)
        
        print("=== MEAL ANALYSIS RESULTS ===")
        print(f"Food Items: {result['food_items']}")
        print(f"Total Protein: {result['total_protein_grams']} grams")
        print(f"Image: {result['image_path']}")
        
        print("✅ Full pipeline test completed!")
        return True
        
    except Exception as e:
        print(f"❌ Full pipeline test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing AI Engine (Phase 1)")
    print("=" * 40)
    
    # Test 1: Protein database
    test_protein_database()
    
    # Test 2: Food identification (if image available)
    test_food_identification()
    
    # Test 3: Full pipeline (if image available)
    test_full_pipeline()
    
    print("\n" + "=" * 40)
    print("🎉 All tests completed!")
    print("\nTo test with your own image:")
    print("1. Add a food image named 'test_meal.jpg' to this directory")
    print("2. Run: python test_ai_engine.py")
    print("3. Or run: python ai_engine.py")

if __name__ == "__main__":
    main() 