# Google Vision API Setup for Render Deployment

## Overview
This guide explains how to configure Google Vision API for your Protein App deployed on Render.

## Why Google Vision API is "Not Configured"

The message "ℹ️ Google Vision API not configured" appears because:
1. The `GOOGLE_SERVICE_ACCOUNT` environment variable is not set in Render
2. The service account JSON file is not available in the deployment environment

## Setup Instructions

### Step 1: Get Google Cloud Service Account Key

1. **Go to Google Cloud Console**: https://console.cloud.google.com/
2. **Select your project** (or create a new one)
3. **Enable Vision API**:
   - Go to "APIs & Services" > "Library"
   - Search for "Cloud Vision API"
   - Click "Enable"
4. **Create Service Account**:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "Service Account"
   - Fill in the details and click "Create"
5. **Create Key**:
   - Click on your service account
   - Go to "Keys" tab
   - Click "Add Key" > "Create New Key"
   - Choose "JSON" format
   - Download the JSON file

### Step 2: Configure Render Environment Variables

1. **Go to your Render dashboard**: https://dashboard.render.com/
2. **Select your Protein App service**
3. **Go to "Environment" tab**
4. **Add Environment Variable**:
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

### Step 3: Deploy and Verify

1. **Save the environment variable** in Render
2. **Redeploy your service** (Render will automatically redeploy)
3. **Check the logs** - you should see:
   ```
   ✅ Google Vision API configured (environment variable)
   ```

## Alternative: Using Service Account File

If you prefer to use a file instead of environment variable:

1. **Upload your JSON file** to your project repository
2. **Set environment variable**:
   - **Key**: `GOOGLE_VISION_SERVICE_ACCOUNT_PATH`
   - **Value**: `service-account-key.json` (or your file name)

## Testing the Setup

After deployment, you can test if Google Vision is working:

1. **Upload a food image** through your app
2. **Check if AI detection works** (should identify foods automatically)
3. **Check the logs** for any Vision API errors

## Troubleshooting

### Common Issues:

1. **"Invalid JSON" error**:
   - Make sure you copied the entire JSON content
   - Don't add extra quotes or formatting

2. **"Permission denied" error**:
   - Ensure your service account has Vision API permissions
   - Check that Vision API is enabled in your Google Cloud project

3. **"Quota exceeded" error**:
   - Google Cloud Vision API has usage limits
   - Check your Google Cloud billing and quotas

### Cost Considerations:

- **Google Vision API is not free** for production use
- **First 1000 requests/month are free**
- **After that**: ~$1.50 per 1000 requests
- **Monitor usage** in Google Cloud Console

## Security Notes

- **Never commit service account keys** to your git repository
- **Use environment variables** in production (recommended)
- **Rotate keys regularly** for security
- **Limit service account permissions** to only what's needed

## Optional: Disable Google Vision

If you don't want to use Google Vision API:
- The app will work fine without it
- Users can manually enter food items
- No additional setup required
