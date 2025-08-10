# Protein Tracker App

An AI-powered nutrition tracking application that helps you monitor your protein intake using image recognition and manual food entry. **Optimized for 100+ active users and hundreds of meal posts.**

## 🚀 Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the application:**
   ```bash
   python main.py
   ```

3. **Open your browser:**
   Navigate to `http://127.0.0.1:8000/static/login.html` (or your server's host). The frontend auto-detects the API base via `window.location.origin` so it works on any IP or hostname.

## ⚡ Performance Optimizations

### High-Scale Architecture
- **100+ Concurrent Users**: Optimized database connections and connection pooling
- **Hundreds of Meal Posts**: Efficient pagination and caching system
- **Fast Response Times**: In-memory caching for frequently accessed data
- **Scalable Database**: Optimized SQLite with proper indexing

### Key Optimizations
- **Database Connection Pooling**: 20 connections with 30 overflow capacity
- **In-Memory Caching**: LRU cache with TTL for dashboard data
- **Pagination**: Configurable page sizes (1-100 items per page)
- **Database Indexes**: Optimized queries on user_id and created_at
- **Background Tasks**: Automatic cache cleanup and meal cleanup
- **Today's Meals**: Shows ALL meals for the day, not just 6 most recent

### Performance Testing
Run the optimization test suite:
```bash
python test_optimization.py
```

This tests concurrent users, caching performance, and pagination functionality.

## 🔧 Configuration

### Email Verification Setup (Optional)
To enable email verification for new accounts:

```bash
python setup_env.py
```

Follow the prompts to configure Gmail SMTP settings.

**Note:** If email verification is not configured, new accounts will be automatically verified and users can log in immediately.

### Google Cloud Vision API (Optional)
For AI-powered food detection, add your API key to `.env` and restart the server:

```
GOOGLE_VISION_API_KEY=your_key_here
```

If the key is missing or a request fails, the app automatically falls back to a heuristic detector so uploads never fail.

Set `APP_BASE_URL` in your environment if you need email links to point to a public hostname (used in verification emails):

```
APP_BASE_URL=https://your.domain:8000
```

**Note:** If no valid API key is configured, the app uses a robust fallback detector so uploads still succeed.

## 🐛 Troubleshooting

### Account Creation Issues

If you encounter problems creating accounts:

1. **JavaScript Error:** The form reset error has been fixed. Try refreshing the page.

2. **Email Verification:** 
   - If email verification is not configured, accounts are automatically verified
   - If you need to manually verify an existing account, run:
     ```bash
     python cleanup.py
     ```
   - Select option 2 to manually verify users

3. **"Account Already Exists" Error:**
   - This happens when the first registration attempt creates the account but fails to send verification email
   - Use the cleanup script to verify the existing account or reset the password

### Manual Account Management

The `cleanup.py` script provides several utilities:

- **List all users** - See all registered users and their verification status
- **Manually verify users** - Verify accounts that couldn't receive email verification
- **Reset passwords** - Reset user passwords if needed
- **Clean up old meals** - Remove old meal data and images

## 📧 Email Verification

The app supports email verification for enhanced security:

- **Configured:** Users receive verification emails and must verify before logging in
- **Not Configured:** Accounts are automatically verified for immediate access

To check email verification status, visit: `http://127.0.0.1:8000/auth/email-status` (adjust host as needed)

## 🍽️ Features

- **User Registration & Authentication**
- **Email Verification** (optional)
- **Protein Tracking**
- **Image Upload & Analysis**
- **AI Food Recognition** (with Google Cloud Vision)
- **Dashboard with Progress Tracking**
- **Weight-based Protein Goals**
- **Profile Picture Management**
- **High-Performance Architecture**
- **Pagination for Large Datasets**
- **Today's Meals View** (shows all meals, not just 6)
- **Toggle Between Today and All Meals**

## 🛠️ API Endpoints

### Authentication
- `POST /auth/register` - User registration
- `POST /auth/login` - User login
- `GET /auth/verify/{token}` - Email verification
- `POST /auth/verify-manual` - Manual verification
- `GET /auth/email-status` - Check email configuration

### User Management
- `GET /users/profile` - Get user profile
- `POST /users/update-profile` - Update user profile
- `POST /users/upload-profile-picture` - Upload profile picture
- `GET /users/profile-picture/{user_id}` - Get profile picture
- `POST /users/update-weight` - Update user weight

### Meals
- `POST /meals/upload/` - Upload meal images
- `GET /meals` - Get user meals (with pagination and date filtering)
- `GET /meals/today` - Get all meals for today

### Dashboard
- `GET /dashboard` - Get user dashboard data (cached)

## 🔒 Security

- Password hashing with SHA-256
- Optional email verification
- Token-based authentication
- Input validation and sanitization
- File upload validation
- Rate limiting and connection management

## 📁 Project Structure

```
Protein App/
├── main.py                 # FastAPI application (optimized)
├── setup_env.py            # Environment configuration
├── setup_google_vision.py  # Google Vision API setup
├── cleanup.py              # Database utilities
├── test_optimization.py    # Performance testing script
├── test_profile_picture.py # Profile picture testing
├── requirements.txt        # Python dependencies
├── static/                 # Frontend files
│   ├── login.html         # Login/registration page
│   ├── dashboard.html     # Main dashboard (optimized)
│   ├── settings.html      # User settings
│   └── index.html         # Landing page
├── uploads/               # Meal images (auto-created)
└── profile_pictures/      # Profile pictures (auto-created)
```

## 🧪 Testing

### Performance Testing
```bash
python test_optimization.py
```

### Profile Picture Testing
```bash
python test_profile_picture.py
```

### Manual Testing
1. Register multiple users
2. Upload many meals per user
3. Test pagination in "All Meals" view
4. Verify "Today's Meals" shows all meals for the day
5. Test dashboard performance with cached data

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly with the optimization test suite
5. Submit a pull request

## 📄 License

This project is open source and available under the MIT License.
