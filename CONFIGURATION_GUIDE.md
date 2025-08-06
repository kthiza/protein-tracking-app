# 🚀 Protein Tracker App - Configuration Guide

## 📧 Email Configuration (Required for account verification)

### Step 1: Enable 2-Step Verification
1. Go to [Google Account Security](https://myaccount.google.com/security)
2. Click on "2-Step Verification"
3. Follow the steps to enable it

### Step 2: Generate App Password
1. Go to [App Passwords](https://myaccount.google.com/apppasswords)
2. Select "Mail" from the dropdown
3. Select "Other (Custom name)"
4. Name it "Protein Tracker App"
5. Click "Generate"
6. **Copy the 16-character password** (e.g., `abcd efgh ijkl mnop`)

### Step 3: Update .env file
Edit your `.env` file and replace:
```env
SMTP_USERNAME=your_actual_gmail@gmail.com
SMTP_PASSWORD=your_16_character_app_password
```

## 🤖 Google Cloud Vision API (Optional for AI detection)

### Step 1: Create Google Cloud Project
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Note your Project ID

### Step 2: Enable Vision API
1. Go to [APIs & Services](https://console.cloud.google.com/apis)
2. Click "Enable APIs and Services"
3. Search for "Cloud Vision API"
4. Click "Enable"

### Step 3: Create API Key
1. Go to [Credentials](https://console.cloud.google.com/apis/credentials)
2. Click "Create Credentials" → "API Key"
3. Copy the API key
4. (Optional) Restrict the API key to Vision API only

### Step 4: Update .env file
Edit your `.env` file and replace:
```env
GOOGLE_API_KEY=your_actual_api_key_here
```

## 🔧 Quick Setup Script

Run the automated setup script:
```bash
python setup_env.py
```

This will guide you through the configuration process step by step.

## ✅ Verification

After configuration:

1. **Restart the server**:
   ```bash
   python main.py
   ```

2. **Test email verification**:
   - Register a new account
   - Check your email for verification link
   - Click the link to verify

3. **Test AI detection**:
   - Upload a meal photo
   - Enable "Use AI Detection"
   - Check if food items are automatically detected

## 🆘 Troubleshooting

### Email Issues
- **"Invalid credentials"**: Make sure you're using App Password, not regular password
- **"2-Step Verification required"**: Enable 2-Step Verification first
- **"Less secure app access"**: Use App Password instead

### Google Vision Issues
- **"API not enabled"**: Enable Cloud Vision API in Google Cloud Console
- **"Invalid API key"**: Check your API key format
- **"Quota exceeded"**: Check your Google Cloud billing

## 📞 Support

If you encounter issues:
1. Check the troubleshooting section above
2. Verify all credentials are correct
3. Ensure services are enabled in Google Cloud Console
4. Check your Google Cloud billing status 