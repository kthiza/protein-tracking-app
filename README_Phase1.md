# Phase 1: AI Engine - Protein Tracking App

This directory contains the core AI engine for the protein tracking application, implementing the first phase of development.

## Overview

The AI engine consists of two main components:
1. **Food Identifier**: Uses Google Cloud Vision API to identify food items in images
2. **Protein Calculator**: Uses a JSON database to calculate protein content

## Files Created

- `ai_engine.py` - Main AI engine with food identification and protein calculation functions
- `protein_db.json` - Database mapping food items to protein grams for standard servings
- `test_ai_engine.py` - Test script to verify functionality
- `config.py` - Configuration file for API keys and settings
- `requirements.txt` - Python dependencies

## Setup Instructions

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **API Key Configuration**:
   The Google Cloud Vision API key is already configured in the code:
   ```
   AIzaSyDIOaMLPjbrrXTswuzVycwyvDmL-0SFdkg
   ```

3. **Test the Setup**:
   ```bash
   python test_ai_engine.py
   ```

## Usage

### Basic Usage
```python
from ai_engine import process_meal_image

# Process an image and get protein analysis
result = process_meal_image("path/to/your/meal.jpg")
print(f"Food items: {result['food_items']}")
print(f"Total protein: {result['total_protein_grams']} grams")
```

### Individual Functions
```python
from ai_engine import identify_food_items, calculate_protein

# Step 1: Identify food items
food_items = identify_food_items("meal.jpg")

# Step 2: Calculate protein
protein = calculate_protein(food_items)
```

## Testing

1. **Test Protein Database**:
   ```bash
   python test_ai_engine.py
   ```
   This will test the protein calculation with known food items.

2. **Test with Your Own Image**:
   - Add a food image named `test_meal.jpg` to this directory
   - Run the test script again to see food identification in action

## API Functions

### `identify_food_items(image_path: str) -> List[str]`
- Takes an image file path
- Sends image to Google Cloud Vision API
- Returns a list of identified food items
- Filters for food-related labels and matches against protein database

### `calculate_protein(food_items: List[str]) -> float`
- Takes a list of food items
- Looks up protein content in `protein_db.json`
- Returns total estimated protein in grams
- Uses exact and partial matching for better results

### `process_meal_image(image_path: str) -> Dict[str, Any]`
- Combines both functions above
- Returns a dictionary with food items and total protein

## Protein Database

The `protein_db.json` file contains protein values for common foods:
- Meat & Fish: chicken breast (31g), salmon (22g), tuna (26g), etc.
- Dairy: milk (8g), yogurt (10g), cheese (7g), etc.
- Plant-based: tofu (8g), lentils (9g), beans (7g), etc.
- Nuts & Seeds: almonds (6g), chia seeds (4g), etc.

## Next Steps

This completes Phase 1 of the project. The next phases will:
- Phase 2: Backend & Database Foundation (FastAPI + SQLite)
- Phase 3: Integrating AI Engine with Backend
- Phase 4: Frontend Development

## Troubleshooting

1. **API Key Issues**: Ensure the Google Cloud Vision API key is valid and has proper permissions
2. **Image Format**: Supported formats: JPG, JPEG, PNG, GIF, BMP
3. **File Size**: Maximum 10MB per image
4. **Dependencies**: Make sure all packages in `requirements.txt` are installed

## Notes

- The system assumes "standard serving" sizes for protein calculations
- Food identification accuracy depends on image quality and Google Cloud Vision API
- The protein database can be expanded by adding more food items to `protein_db.json` 