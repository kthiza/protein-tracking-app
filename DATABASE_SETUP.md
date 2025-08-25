# 🗄️ Database Setup Guide

## 📋 Overview

Your KthizaTrack app uses SQLModel with configurable database backends. The database URL is set via the `DATABASE_URL` environment variable.

## 🔧 Current Configuration

Your `main.py` already supports multiple database types:

```python
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./protein_app.db?check_same_thread=False")
engine = create_engine(DATABASE_URL, echo=False, connect_args={"check_same_thread": False})
```

## 🌐 Deployment Options

### 1. **Local Development**
```env
DATABASE_URL=sqlite:///./protein_app.db
```
- ✅ Data persists locally
- ✅ Simple setup
- ✅ Good for development

### 2. **Render Free Tier (Ephemeral)**
```env
DATABASE_URL=sqlite:///./protein_app.db
```
- ✅ Free
- ❌ Data lost on restarts
- ❌ Not suitable for production

### 3. **Render with PostgreSQL (Persistent)**
```env
DATABASE_URL=postgresql://user:password@host:port/database
```
- ✅ Data persists permanently
- ✅ Production-ready
- ❌ Requires paid plan ($7/month)

### 4. **External Database Services**

#### **Railway (Recommended)**
- Free tier available
- PostgreSQL database
- Easy setup

#### **Supabase**
- Free tier available
- PostgreSQL database
- Built-in authentication

#### **Neon**
- Free tier available
- Serverless PostgreSQL
- Auto-scaling

## 🚀 Quick Setup Commands

### Local Development
```bash
# No setup needed - uses default SQLite
python main.py
```

### Render Free Tier
```bash
# In Render Environment Variables:
DATABASE_URL=sqlite:///./protein_app.db
```

### Render with PostgreSQL
```bash
# 1. Create PostgreSQL database in Render
# 2. Copy connection string
# 3. Set in Environment Variables:
DATABASE_URL=postgresql://user:password@host:port/database
```

### External Database
```bash
# 1. Create database on external service
# 2. Copy connection string
# 3. Set in Environment Variables:
DATABASE_URL=postgresql://user:password@host:port/database
```

## 🔍 Database Migration

Your app automatically creates tables on startup:

```python
def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
```

No manual migration needed!

## 📊 Database Schema

### Users Table
- `id`: Primary key
- `username`: Unique username
- `email`: Unique email
- `password_hash`: Hashed password
- `weight_kg`: User weight
- `protein_goal`: Daily protein goal
- `calorie_goal`: Daily calorie goal
- `activity_level`: Activity level
- `email_verified`: Email verification status
- `created_at`: Account creation date

### Meals Table
- `id`: Primary key
- `user_id`: Foreign key to users
- `image_path`: Path to meal image
- `food_items`: JSON array of food items
- `total_protein`: Calculated protein content
- `total_calories`: Calculated calorie content
- `created_at`: Meal creation date

## 🛠️ Troubleshooting

### Common Issues

#### 1. **Database Connection Failed**
```
Error: Could not parse rfc1738 URL
```
**Solution**: Check `DATABASE_URL` format

#### 2. **Permission Denied**
```
Error: Permission denied
```
**Solution**: Check database credentials

#### 3. **Table Not Found**
```
Error: Table 'user' doesn't exist
```
**Solution**: App will auto-create tables on startup

### Debug Commands

```bash
# Test database connection
python -c "from main import engine; print('Database OK')"

# Check environment variables
echo $DATABASE_URL

# Test SQLite locally
sqlite3 protein_app.db ".tables"
```

## 🎯 Recommendations

### For Development
- Use SQLite locally
- Simple and fast

### For Testing
- Use SQLite on Render free tier
- Good for testing features

### For Production
- Use PostgreSQL (Render paid or external)
- Data persistence is crucial

### For Free Production
- Use external PostgreSQL service
- Railway, Supabase, or Neon
- Free tiers available
