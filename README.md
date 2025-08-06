# Protein Tracking App

A professional, AI-powered web application that tracks protein intake through photo analysis using Google Cloud Vision API, featuring secure authentication, automatic cleanup, and weekly weight updates.

## 🚀 Features

### Core Functionality
- **AI-Powered Food Recognition**: Upload photos of your meals and automatically identify food items using Google Cloud Vision API
- **Protein Calculation**: Automatically calculate protein content based on identified foods
- **Daily Goal Tracking**: Set protein goals based on your body weight (1.6g per kg)
- **Progress Dashboard**: Visual progress tracking and meal history
- **Weekly Weight Updates**: Popup reminders to update weight and recalculate protein goals

### Security & User Management
- **Secure Authentication**: Username/password login with email verification
- **Password Hashing**: SHA-256 password encryption
- **Email Verification**: Secure account activation via email
- **Session Management**: Persistent login with localStorage
- **Bearer Token Authentication**: Secure API access

### Professional UI/UX
- **Multi-Page Structure**: Separate login and dashboard pages
- **Responsive Design**: Modern, mobile-friendly interface
- **Weight Update Modal**: Weekly popup for weight updates
- **Real-time Dashboard**: Live protein tracking and progress visualization

### System Features
- **Automatic Cleanup**: Daily cleanup of old meal data and images (24-hour retention)
- **Manual Cleanup**: Admin endpoint for testing cleanup functionality
- **Background Tasks**: Non-blocking cleanup operations
- **Error Handling**: Comprehensive error handling and user feedback

## 🛠️ Technology Stack

- **Backend**: Python with FastAPI
- **Database**: SQLite with SQLModel ORM
- **AI/Vision**: Google Cloud Vision API (optional)
- **Frontend**: HTML, CSS, JavaScript
- **Authentication**: HTTPBearer tokens, SHA-256 hashing
- **Email**: SMTP for verification emails
- **Environment**: Python 3.8+

## 📋 Prerequisites

- Python 3.8 or higher
- Google Cloud account with Vision API enabled (optional)
- SMTP server for email verification (Gmail recommended)

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
   # Google Cloud Vision API (optional)
   GOOGLE_API_KEY=your_google_cloud_api_key_here
   
   # Email settings for verification
   SMTP_SERVER=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USERNAME=your_email@gmail.com
   SMTP_PASSWORD=your_app_password
   ```

5. **Configure Email (Required for account verification)**
   - For Gmail: Use an App Password (not your regular password)
   - Enable 2-factor authentication on your Google account
   - Generate an App Password in Google Account settings
   - Add the App Password to your `.env` file

## 🚀 Usage

### Starting the Application
```bash
python main.py
```

The application will be available at `http://localhost:8000`

### User Flow
1. **Registration**: Create account with username, email, and password
2. **Email Verification**: Check email and click verification link
3. **Login**: Use username and password to access dashboard
4. **Weight Setup**: Set initial weight via weekly popup
5. **Meal Tracking**: Upload photos and track protein intake
6. **Weekly Updates**: Update weight when prompted

### Testing
```bash
# Run comprehensive test suite
python test_complete_flow.py

# Run with verification token (after registration)
python test_complete_flow.py YOUR_TOKEN_HERE
```

### Cleanup
```bash
# Clean up database and files
python cleanup.py
```

## 📁 Project Structure

```
Protein-Tracking-App/
├── main.py                    # FastAPI backend application
├── static/                    # Frontend files
│   ├── index.html            # Redirect page
│   ├── login.html            # Login/registration page
│   └── dashboard.html        # Main dashboard
├── requirements.txt           # Python dependencies
├── test_complete_flow.py     # Comprehensive test suite
├── cleanup.py                # Database and file cleanup utility
├── .env                      # Environment variables (create this)
├── .gitignore               # Git ignore rules
└── README.md                # This file
```

## 🔄 API Endpoints

### Authentication
- `POST /auth/register` - User registration
- `POST /auth/login` - User login
- `GET /auth/verify/{token}` - Email verification

### User Management
- `GET /users/profile` - Get user profile
- `POST /users/update-weight` - Update weight and protein goal

### Meal Management
- `POST /meals/upload/` - Upload meal photo
- `GET /meals` - Get user's meal history

### Dashboard & Data
- `GET /dashboard` - Get dashboard data
- `GET /foods/suggestions` - Get food suggestions
- `GET /` - Root endpoint with app info

### Admin
- `POST /admin/cleanup` - Manual cleanup (testing)

## 🔒 Security Features

### Authentication System
- **Password Hashing**: SHA-256 encryption
- **Email Verification**: Required for account activation
- **Bearer Tokens**: Secure API access
- **Session Management**: Persistent login state

### Data Protection
- **Input Validation**: Comprehensive form validation
- **SQL Injection Protection**: SQLModel ORM
- **File Upload Security**: Restricted file types and sizes
- **Automatic Cleanup**: 24-hour data retention

## 🧹 Cleanup System

### Automatic Cleanup
- **Daily Execution**: Runs every 24 hours
- **Data Retention**: Keeps data for 24 hours only
- **File Management**: Deletes old images and database records
- **Background Processing**: Non-blocking operation

### Manual Cleanup
- **Testing Endpoint**: `/admin/cleanup` for development
- **Utility Script**: `cleanup.py` for file management
- **Flexible Options**: Choose cleanup scope

## ⚖️ Weight Update System

### Weekly Reminders
- **Automatic Detection**: Checks if weight update is needed
- **7-Day Cycle**: Prompts every 7 days
- **Modal Interface**: User-friendly popup
- **Goal Recalculation**: Updates protein goals automatically

### User Experience
- **First-Time Setup**: Required for new users
- **Regular Updates**: Weekly reminders
- **Visual Feedback**: Clear progress indicators
- **Data Persistence**: Saves update timestamps

## 🧪 Testing

### Test Suite
The `test_complete_flow.py` script provides comprehensive testing:

1. **Registration Test**: Creates new user account
2. **Verification Test**: Tests email verification
3. **Login Test**: Tests authentication
4. **Weight Update Test**: Tests weight management
5. **Dashboard Test**: Tests dashboard access
6. **Food Suggestions Test**: Tests food database

### Running Tests
```bash
# Step 1: Run registration test
python test_complete_flow.py

# Step 2: Check server logs for verification token
# Look for: "Email verification token for testuser: [TOKEN]"

# Step 3: Run complete test with token
python test_complete_flow.py YOUR_TOKEN_HERE
```

## 🚨 Troubleshooting

### Common Issues

**Email Verification Not Working**
- Check SMTP settings in `.env` file
- Ensure Gmail App Password is used (not regular password)
- Verify 2-factor authentication is enabled

**Google Vision API Errors**
- API is optional - app works without it
- Check API key in `.env` file
- Verify Vision API is enabled in Google Cloud Console

**Database Errors**
- Run `python cleanup.py` to reset database
- Ensure server is stopped before cleanup
- Check file permissions

**Login Issues**
- Verify email was confirmed
- Check username/password spelling
- Clear browser localStorage if needed

### Error Messages
- **"Invalid verification token"**: Token expired or incorrect
- **"Username already exists"**: Choose different username
- **"Email already exists"**: Use different email or verify existing account
- **"Login failed"**: Check credentials and email verification

## 📊 Future Enhancements

- [ ] Portion size estimation
- [ ] Multiple nutrition tracking (carbs, fats, calories)
- [ ] Mobile app version
- [ ] Social features and sharing
- [ ] Integration with fitness trackers
- [ ] Advanced analytics and insights
- [ ] Meal planning and recipes
- [ ] Barcode scanning for packaged foods

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
- **Email Configuration**: Required for account verification
- **Data Retention**: Meal data is automatically deleted after 24 hours
- **Google Cloud Costs**: Vision API has usage limits and costs (optional feature)
- **Database**: Uses SQLite for simplicity - consider PostgreSQL for production

## 🆘 Support

If you encounter any issues:
1. Check the troubleshooting section above
2. Verify all environment variables are set correctly
3. Ensure all dependencies are installed
4. Check the server logs for detailed error messages
5. Run the test suite to verify functionality

## 📈 Performance

- **FastAPI**: High-performance async web framework
- **SQLite**: Lightweight, file-based database
- **Background Tasks**: Non-blocking cleanup operations
- **Static Files**: Optimized frontend delivery
- **CORS Support**: Cross-origin request handling
