"""
Configuration file for the Protein Tracking App
Contains API keys and application settings
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Google Cloud Vision API Configuration
GOOGLE_CLOUD_API_KEY = os.getenv('GOOGLE_CLOUD_API_KEY', 'AIzaSyDIOaMLPjbrrXTswuzVycwyvDmL-0SFdkg')

# Application Settings
DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'

# Database Settings
DATABASE_URL = "sqlite:///./protein_tracker.db"

# File Upload Settings
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp'}

# Protein Calculation Settings
PROTEIN_PER_KG = 1.6  # grams of protein per kg of body weight 