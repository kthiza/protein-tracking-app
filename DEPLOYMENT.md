# 🚀 KthizaTrack Deployment Guide for Render

This guide will walk you through deploying your Protein Tracking App to Render, a cloud platform that makes it easy to deploy web services.

## 📋 Prerequisites

1. **GitHub Account**: Your code must be in a GitHub repository
2. **Render Account**: Sign up at [render.com](https://render.com)
3. **Google Cloud Vision API** (Optional): For AI food detection features

## 🔧 Pre-Deployment Setup

### 1. Prepare Your Repository

Make sure your repository has these files:
- ✅ `main.py` - Your FastAPI application
- ✅ `requirements.txt` - Python dependencies
- ✅ `render.yaml` - Render configuration (optional but recommended)
- ✅ `static/` - Frontend files
- ✅ `.gitignore` - Excludes sensitive files

### 2. Environment Variables Setup

Create a `.env` file locally for testing (don't commit this to Git):

```env
# Database
DATABASE_URL=sqlite:///./protein_app.db

# Email Configuration (Optional)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Google Vision API (Optional)
GOOGLE_VISION_SERVICE_ACCOUNT_PATH=path/to/service-account.json

# App Configuration
APP_BASE_URL=https://your-app-name.onrender.com
```

## 🌐 Deploy to Render

### Method 1: Using Render Dashboard (Recommended)

1. **Connect Your Repository**
   - Go to [render.com](https://render.com) and sign in
   - Click "New +" → "Web Service"
   - Connect your GitHub account
   - Select your repository

2. **Configure Your Service**
   ```
   Name: protein-tracker (or your preferred name)
   Region: Choose closest to your users
   Branch: main (or your default branch)
   Root Directory: (leave empty if code is in root)
   Runtime: Python 3
       Build Command: pip install -r requirements.txt
    Start Command: uvicorn main:app --host 0.0.0.0 --port $PORT --workers 4
   ```

3. **Environment Variables**
   Add these in the Environment tab:
   ```
   DATABASE_URL: postgresql://postgres:password@localhost:5432/protein_app
   APP_BASE_URL: https://kthiza-track.onrender.com
   SMTP_SERVER: smtp.gmail.com
   SMTP_PORT: 587
   SMTP_USERNAME: your-email@gmail.com
   SMTP_PASSWORD: your-app-password
   GOOGLE_VISION_SERVICE_ACCOUNT_PATH: /opt/render/project/src/service-account.json
   ```

4. **Deploy**
   - Click "Create Web Service"
   - Render will automatically build and deploy your app
   - Your app will be available at: `https://kthiza-track.onrender.com`

### Method 2: Using render.yaml (Blue-Green Deployment)

If you have the `render.yaml` file in your repository:

1. Go to Render Dashboard
2. Click "New +" → "Blueprint"
3. Connect your repository
4. Render will automatically detect and use the `render.yaml` configuration

## 🔍 Post-Deployment Verification

### 1. Health Check
Visit your app's health endpoint:
```
https://kthiza-track.onrender.com/api/health
```
Should return: `{"status": "healthy", "timestamp": "..."}`

### 2. Main Application
Visit your app's main URL:
```
https://kthiza-track.onrender.com
```
Should show the KthizaTrack landing page.

### 3. Test Features
- ✅ User registration/login
- ✅ Meal upload and tracking
- ✅ Dashboard functionality
- ✅ Email verification (if configured)

## 🔧 Environment Variables Reference

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `DATABASE_URL` | Yes | Database connection string | `postgresql://...` |
| `APP_BASE_URL` | Yes | Your app's public URL | `https://app.onrender.com` |
| `SMTP_SERVER` | No | Email server for verification | `smtp.gmail.com` |
| `SMTP_PORT` | No | Email server port | `587` |
| `SMTP_USERNAME` | No | Email username | `your-email@gmail.com` |
| `SMTP_PASSWORD` | No | Email app password | `your-app-password` |
| `GOOGLE_VISION_SERVICE_ACCOUNT_PATH` | No | Google Vision API key path | `/opt/render/project/src/service-account.json` |

## 🗄️ Database Configuration

### SQLite (Default - Free Tier)
- Render will automatically create a SQLite database
- Data persists between deployments
- Good for development and small apps

### PostgreSQL (Recommended for Production)
1. Create a PostgreSQL database in Render
2. Get the connection string
3. Set `DATABASE_URL` environment variable
4. Update your app to use PostgreSQL

## 📧 Email Configuration

### Gmail Setup
1. Enable 2-factor authentication on your Gmail account
2. Generate an App Password:
   - Go to Google Account settings
   - Security → 2-Step Verification → App passwords
   - Generate password for "Mail"
3. Use the generated password as `SMTP_PASSWORD`

### Other Email Providers
Update the SMTP settings according to your provider:
- **Outlook**: `smtp-mail.outlook.com:587`
- **Yahoo**: `smtp.mail.yahoo.com:587`
- **Custom**: Use your provider's SMTP settings

## 🤖 Google Vision API Setup (Optional)

### 1. Create Google Cloud Project
1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project
3. Enable Vision API
4. Create a service account
5. Download the JSON key file

### 2. Upload to Render
1. In your Render service dashboard
2. Go to Environment tab
3. Add the service account JSON as a file
4. Set `GOOGLE_VISION_SERVICE_ACCOUNT_PATH` to the file path

## 🔄 Continuous Deployment

Render automatically deploys when you push to your main branch:
1. Make changes to your code
2. Commit and push to GitHub
3. Render detects changes and auto-deploys
4. Your app updates automatically

## 🐛 Troubleshooting

### Common Issues

#### 1. Build Failures
```
Error: Module not found
```
**Solution**: Check `requirements.txt` includes all dependencies

#### 2. Port Issues
```
Error: Address already in use
```
**Solution**: Make sure your app uses `$PORT` environment variable

#### 3. Database Connection
```
Error: Database connection failed
```
**Solution**: Check `DATABASE_URL` environment variable

#### 4. Static Files Not Loading
```
Error: 404 for static files
```
**Solution**: Ensure `static/` directory is in your repository

### Debug Commands

Check your app logs in Render dashboard:
1. Go to your service
2. Click "Logs" tab
3. Look for error messages

### Local Testing

Test your production configuration locally:
```bash
# Set environment variables
export PORT=8000
export DATABASE_URL=sqlite:///./test.db
export APP_BASE_URL=http://localhost:8000

# Run with production settings
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT
```

## 📊 Monitoring and Analytics

### Render Dashboard
- View real-time logs
- Monitor resource usage
- Check deployment status
- Set up alerts

### Health Checks
Your app includes a health check endpoint:
```
GET /api/health
```

## 🔒 Security Considerations

### Environment Variables
- Never commit sensitive data to Git
- Use Render's environment variable system
- Rotate passwords regularly

### HTTPS
- Render provides free SSL certificates
- All traffic is automatically encrypted

### Database Security
- Use strong database passwords
- Restrict database access
- Regular backups

## 📈 Scaling

### Free Tier Limits
- 750 hours/month
- 512MB RAM
- Shared CPU
- Sleep after 15 minutes of inactivity

### Paid Plans
- Always-on services
- More RAM and CPU
- Custom domains
- Advanced features

## 🆘 Support

### Render Support
- [Render Documentation](https://render.com/docs)
- [Render Community](https://community.render.com)
- [Render Status](https://status.render.com)

### App-Specific Issues
- Check the logs in Render dashboard
- Verify environment variables
- Test locally with production settings

## 🎉 Success!

Once deployed, your Protein Tracking App will be:
- ✅ Publicly accessible
- ✅ Automatically updated on code changes
- ✅ SSL secured
- ✅ Monitored and logged
- ✅ Ready for users worldwide!

Your app URL: `https://kthiza-track.onrender.com`
