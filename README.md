# Protein Tracking App

An AI-powered web application that tracks protein intake through photo analysis using Google Cloud Vision API.

## 🚀 Features

- **AI-Powered Food Recognition**: Upload photos of your meals and automatically identify food items
- **Protein Calculation**: Automatically calculate protein content based on identified foods
- **Daily Goal Tracking**: Set protein goals based on your body weight (1.6g per kg)
- **Progress Dashboard**: Visual progress tracking and meal history
- **User Profiles**: Personalize your experience with weight-based goals

## 🛠️ Technology Stack

- **Backend**: Python with FastAPI
- **Database**: SQLite with SQLModel ORM
- **AI/Vision**: Google Cloud Vision API
- **Frontend**: HTML, CSS, JavaScript
- **Environment**: Python 3.8+

## 📋 Prerequisites

- Python 3.8 or higher
- Google Cloud account with Vision API enabled
- Google Cloud API key

## 🔧 Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/protein-tracking-app.git
   cd protein-tracking-app
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   # On Windows
   venv\Scripts\activate
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   Create a `.env` file in the project root:
   ```env
   GOOGLE_API_KEY=your_google_cloud_api_key_here
   ```

5. **Get Google Cloud API Key**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing one
   - Enable the Vision API
   - Create credentials (API Key)
   - Add the API key to your `.env` file

## 🚀 Usage

### Running the AI Engine (Phase 1)
```bash
python ai_engine.py
```

### Running the Web Application (Future Phases)
```bash
# Start the FastAPI server
uvicorn main:app --reload
```

Then open your browser to `http://localhost:8000`

## 📁 Project Structure

```
Protein-Tracking-App/
├── ai_engine.py          # Core AI functions for food recognition
├── protein_db.json       # Protein content database
├── requirements.txt      # Python dependencies
├── .env                  # Environment variables (create this)
├── .gitignore           # Git ignore rules
├── README.md            # This file
└── test_ai_engine.py    # Unit tests
```

## 🔄 Development Phases

### Phase 1: Core AI Engine ✅
- [x] Food identification using Google Cloud Vision API
- [x] Protein calculation from food database
- [x] Basic image processing pipeline

### Phase 2: Backend & Database (In Progress)
- [ ] FastAPI application setup
- [ ] SQLite database with SQLModel
- [ ] User management endpoints

### Phase 3: Application Integration (Planned)
- [ ] Meal upload endpoint
- [ ] Dashboard data endpoint
- [ ] AI engine integration

### Phase 4: Frontend Development (Planned)
- [ ] User interface
- [ ] Progress visualization
- [ ] Meal upload form

## 🧪 Testing

Run the test suite:
```bash
python test_ai_engine.py
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚠️ Important Notes

- **API Key Security**: Never commit your `.env` file to version control
- **Google Cloud Costs**: The Vision API has usage limits and costs. Monitor your usage in the Google Cloud Console
- **Database**: The protein database is a simplified version. For production use, consider using a comprehensive nutrition database

## 🆘 Support

If you encounter any issues:
1. Check that your Google Cloud API key is correctly set in the `.env` file
2. Ensure all dependencies are installed
3. Verify that the Vision API is enabled in your Google Cloud project
4. Check the logs for detailed error messages

## 📊 Future Enhancements

- [ ] Portion size estimation
- [ ] Multiple nutrition tracking (carbs, fats, calories)
- [ ] Mobile app version
- [ ] Social features and sharing
- [ ] Integration with fitness trackers
- [ ] Advanced analytics and insights
