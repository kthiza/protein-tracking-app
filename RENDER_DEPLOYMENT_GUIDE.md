# Render Deployment Guide for Protein App

## Quick Setup for Render

This guide will help you deploy your Protein App to Render with Google Vision API support.

## Prerequisites

1. **Google Cloud Account** with billing enabled
2. **Render Account** (free tier available)
3. **GitHub/GitLab repository** with your Protein App code

## Step 1: Set Up Google Cloud Vision API

### 1.1 Create Google Cloud Project
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable billing for the project

### 1.2 Enable Vision API
1. Go to "APIs & Services" > "Library"
2. Search for "Cloud Vision API"
3. Click "Enable"

### 1.3 Create Service Account
1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "Service Account"
3. Fill in:
   - **Service account name**: `protein-app-vision`
   - **Description**: `Service account for Protein App Vision API`
4. Click "Create and Continue"
5. Skip role assignment (we'll add permissions later)
6. Click "Done"

### 1.4 Add Vision API Permissions
1. Click on your service account
2. Go to "Permissions" tab
3. Click "Grant Access"
4. Add role: "Cloud Vision API User"
5. Click "Save"

### 1.5 Create Service Account Key
1. Go to "Keys" tab
2. Click "Add Key" > "Create New Key"
3. Choose "JSON" format
4. Click "Create"
5. **Download the JSON file** (you'll need this for Render)

## Step 2: Deploy to Render

### 2.1 Connect Repository
1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Click "New" > "Web Service"
3. Connect your GitHub/GitLab repository
4. Select your Protein App repository

### 2.2 Configure Web Service
1. **Name**: `protein-app` (or your preferred name)
2. **Environment**: `Python 3`
3. **Build Command**: `pip install -r requirements.txt`
4. **Start Command**: `python main.py`
5. **Plan**: Free (or paid if you prefer)

### 2.3 Set Environment Variables
1. Go to "Environment" tab
2. Add the following environment variables:

#### Required Variables:
- **Key**: `GOOGLE_SERVICE_ACCOUNT`
- **Value**: Copy the **entire content** of your downloaded JSON file
- **Example**:
  ```json
  {
    "type": "service_account",
    "project_id": "your-project-id",
    "private_key_id": "abc123...",
    "private_key": "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n",
    "client_email": "your-service@your-project.iam.gserviceaccount.com",
    "client_id": "123456789",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/your-service%40your-project.iam.gserviceaccount.com"
  }
  ```

#### Optional Variables:
- **Key**: `DATABASE_URL`
- **Value**: Your database URL (if using external database)

### 2.4 Deploy
1. Click "Create Web Service"
2. Wait for deployment to complete (usually 2-5 minutes)
3. Your app will be available at: `https://your-app-name.onrender.com`

## Step 3: Verify Deployment

### 3.1 Check Deployment Logs
1. Go to your Render service
2. Click "Logs" tab
3. Look for these success messages:
   ```
   ✅ Google Vision API configured (environment variable)
   ✅ Google Vision API initialized with environment variable
   ```

### 3.2 Test Food Detection
1. Go to your deployed app URL
2. Upload a food image
3. Verify that AI detection works and shows different foods for different images
4. Check that it's not showing the same hardcoded "chicken, rice, vegetables" for all images

## Troubleshooting

### Common Issues:

1. **"Google Vision API not configured"**
   - Check that `GOOGLE_SERVICE_ACCOUNT` environment variable is set
   - Verify the JSON content is complete and valid
   - Redeploy after fixing the environment variable

2. **"Invalid JSON" error**
   - Make sure you copied the entire JSON file content
   - Don't add extra quotes or formatting
   - Use a JSON validator to check the format

3. **"Permission denied" error**
   - Ensure Vision API is enabled in Google Cloud
   - Check that service account has "Cloud Vision API User" role
   - Verify the service account email is correct

4. **"Service account file not found"**
   - This error should not occur with environment variables
   - Make sure you're using `GOOGLE_SERVICE_ACCOUNT` not file paths

### Testing Commands

You can test your deployment by:

1. **Checking the health endpoint**: `https://your-app-name.onrender.com/api/health`
2. **Testing the API**: `https://your-app-name.onrender.com/api/test`
3. **Uploading images** through the web interface

## Cost Management

### Google Cloud Vision API Costs:
- **Free tier**: 1,000 requests/month
- **Paid tier**: ~$1.50 per 1,000 requests
- **Monitor usage** in Google Cloud Console

### Render Costs:
- **Free tier**: Available with limitations
- **Paid tier**: Starts at $7/month for better performance

## Security Best Practices

1. **Never commit service account keys** to your repository
2. **Use environment variables** for all sensitive data
3. **Rotate service account keys** regularly
4. **Monitor API usage** to prevent unexpected charges
5. **Limit service account permissions** to only what's needed

## Support

If you encounter issues:

1. **Check Render logs** for deployment errors
2. **Verify environment variables** are set correctly
3. **Test locally** with the same environment variables
4. **Check Google Cloud Console** for API usage and errors

## Next Steps

After successful deployment:

1. **Set up a custom domain** (optional)
2. **Configure SSL certificates** (automatic with Render)
3. **Set up monitoring** and alerts
4. **Optimize performance** if needed
5. **Scale up** as your app grows
