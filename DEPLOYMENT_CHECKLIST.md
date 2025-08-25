# 🚀 Render Deployment Checklist

## ✅ Pre-Deployment Checklist

### 1. Repository Setup
- [ ] Code is in a GitHub repository
- [ ] All files are committed and pushed
- [ ] `.gitignore` excludes sensitive files
- [ ] `requirements.txt` includes all dependencies
- [ ] `main.py` uses environment variables for port

### 2. Required Files
- [ ] `main.py` - FastAPI application
- [ ] `requirements.txt` - Python dependencies
- [ ] `static/` - Frontend files
- [ ] `render.yaml` - Render configuration (optional)
- [ ] `Procfile` - Alternative deployment config
- [ ] `runtime.txt` - Python version specification

### 3. Environment Variables (Optional)
- [ ] Email configuration (SMTP settings)
- [ ] Google Vision API credentials
- [ ] App base URL configuration

## 🌐 Render Deployment Steps

### Step 1: Create Render Account
1. Go to [render.com](https://render.com)
2. Sign up with GitHub account
3. Verify email address

### Step 2: Deploy Web Service
1. Click "New +" → "Web Service"
2. Connect GitHub repository
3. Configure service:
   ```
   Name: protein-tracker
   Region: Choose closest to you
   Branch: main
       Build Command: pip install -r requirements.txt
    Start Command: uvicorn main:app --host 0.0.0.0 --port $PORT
   ```

### Step 3: Environment Variables
Add these in Environment tab:
```
DATABASE_URL: sqlite:///./protein_app.db
APP_BASE_URL: https://kthiza-track.onrender.com
SMTP_SERVER: smtp.gmail.com
SMTP_PORT: 587
SMTP_USERNAME: your-email@gmail.com
SMTP_PASSWORD: your-app-password
```

### Step 4: Deploy
1. Click "Create Web Service"
2. Wait for build to complete
3. Your app is live at: `https://protein-tracker.onrender.com`

## 🔍 Post-Deployment Verification

### Health Check
- [ ] Visit: `https://protein-tracker.onrender.com/api/health`
- [ ] Should return: `{"status": "healthy", "timestamp": "..."}`

### Main App
- [ ] Visit: `https://protein-tracker.onrender.com`
- [ ] Should show KthizaTrack landing page

### Features Test
- [ ] User registration
- [ ] User login
- [ ] Meal upload
- [ ] Dashboard functionality
- [ ] Email verification (if configured)

## 🐛 Common Issues & Solutions

### Build Failures
**Problem**: Module not found
**Solution**: Check `requirements.txt` includes all dependencies

### Port Issues
**Problem**: Address already in use
**Solution**: Ensure app uses `$PORT` environment variable

### Database Issues
**Problem**: Database connection failed
**Solution**: Check `DATABASE_URL` environment variable

### Static Files
**Problem**: 404 for static files
**Solution**: Ensure `static/` directory is in repository

## 📞 Support

- **Render Docs**: [render.com/docs](https://render.com/docs)
- **Render Community**: [community.render.com](https://community.render.com)
- **App Logs**: Check in Render dashboard → Logs tab

## 🎉 Success!

Once deployed, your app will be:
- ✅ Publicly accessible worldwide
- ✅ SSL secured (HTTPS)
- ✅ Auto-deploys on code changes
- ✅ Monitored and logged
- ✅ Ready for users!

**Your App URL**: `https://protein-tracker.onrender.com`
