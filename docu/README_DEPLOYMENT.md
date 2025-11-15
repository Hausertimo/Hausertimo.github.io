# NormScout Deployment Guide

## Overview
NormScout is a Flask application that uses the OpenRouter API to provide compliance information for products in different markets. This guide covers local testing and deployment to Fly.io.

## Prerequisites
- Python 3.11+
- OpenRouter API key (get one at https://openrouter.ai)
- Redis database (get free tier at https://redis.com/try-free/)
- Fly.io account (for deployment)

## Local Development

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set Environment Variables

#### Windows (Command Prompt)
```cmd
set openrouter=sk-or-v1-your-actual-api-key-here
set REDIS_URL=redis://default:password@your-redis-host:port
```

#### Windows (PowerShell)
```powershell
$env:openrouter = "sk-or-v1-your-actual-api-key-here"
$env:REDIS_URL = "redis://default:password@your-redis-host:port"
```

#### Linux/Mac
```bash
export openrouter='sk-or-v1-your-actual-api-key-here'
export REDIS_URL='redis://default:password@your-redis-host:port'
```

### 3. Test the API Key
```bash
python tests/test_api.py
```

This script will:
- Verify your API key is configured
- Test direct OpenRouter API calls
- Test the local Flask app (if running)

### 4. Run the Application Locally
```bash
python app.py
```

The app will start on http://localhost:8080

Check the console output for:
- ✓ OpenRouter API key found (shows key length)
- API endpoint confirmation
- Any startup errors

## Deployment to Fly.io (Via Dashboard)

### 1. Redis Setup
First, get a Redis database:
- Sign up at https://redis.com/try-free/ (30MB free)
- Create a new database
- Copy the connection string (format: `redis://default:password@host:port`)

### 2. Configure Secrets on Fly.io Dashboard

1. Go to https://fly.io/dashboard
2. Select your `normscout` app
3. Navigate to the **Secrets** tab
4. Add these secrets:
   - **Name:** `openrouter` **Value:** `sk-or-v1-your-actual-api-key-here`
   - **Name:** `REDIS_URL` **Value:** `redis://default:password@your-redis-host:port`

### 3. Deploy via GitHub Push

Since you're using GitHub deployment:
1. Commit and push your changes to GitHub
2. Fly.io will automatically deploy from your repository
3. Monitor deployment at https://fly.io/dashboard

## Debugging Deployment Issues

### 1. Check Logs for Errors
Via Fly.io Dashboard:
- Go to your app → Monitoring → Live Logs

Look for:
- "Redis connected successfully" - Redis is working
- "OpenRouter API key found" - API key is configured
- "RuntimeError: Redis is required" - REDIS_URL not set
- API error messages with status codes

### 2. Verify Secrets are Set
Check in Fly.io Dashboard → Your App → Secrets tab

You should see:
- `openrouter` (your OpenRouter API key)
- `REDIS_URL` (your Redis connection string)

### 3. Common Issues and Solutions

#### Issue: "RuntimeError: Redis is required"
**Solution:** REDIS_URL not set. Add it in Fly.io Dashboard → Secrets

#### Issue: "Redis connection failed"
**Solution:** Check your Redis connection string:
- Format: `redis://default:password@host:port`
- No extra spaces or quotes
- Redis server is accessible

#### Issue: "API key NOT FOUND" in logs
**Solution:** Set the secret in Fly.io Dashboard → Secrets

#### Issue: 401 Unauthorized from OpenRouter
**Solution:** Your API key is invalid. Check:
- Key starts with 'sk-or-v1-' (typical format)
- Key hasn't been revoked

#### Issue: Visitor counter shows error
**Solution:** Redis connection issue. Check:
- REDIS_URL is correctly set
- Redis server is running
- Connection string is valid

### 4. Test the Deployed App
```bash
# Get your app URL
fly info

# Test with curl (replace with your URL)
curl -X POST https://normscout.fly.dev/api/run \
  -H "Content-Type: application/json" \
  -d '{"product":"Bluetooth Speaker","country":"eu"}'
```

## Environment Variables Reference

| Variable | Description | Required | Example |
|----------|-------------|----------|---------|
| `openrouter` | OpenRouter API key | Yes | `sk-or-v1-xxxxx` |
| `REDIS_URL` | Redis connection string | Yes | `redis://default:pass@host:port` |

## File Structure
```
.
├── app.py                  # Main Flask application
├── routes/                 # API route blueprints
│   ├── main.py            # Main routes
│   ├── analytics.py       # Analytics endpoints
│   ├── develope.py        # Workspace creation
│   └── tracking.py        # Visitor tracking
├── services/               # Business logic
│   ├── openrouter.py      # OpenRouter API client
│   ├── norm_matcher.py    # Norm matching logic
│   └── product_conversation.py # Conversation AI
├── static/                 # Frontend files
│   ├── index.html         # Main page
│   ├── bp.html            # Business plan page
│   ├── style.css          # Styles
│   └── functions.js       # Frontend JavaScript
├── tests/                  # Test files
│   └── test_api.py        # API testing script
├── requirements.txt        # Python dependencies
├── Dockerfile             # Container configuration
└── fly.toml              # Fly.io configuration
```

## Security Notes

1. **Never commit API keys** to version control
2. Use environment variables or secrets management
3. The app uses HTTPS in production (enforced by Fly.io)
4. API keys are masked in logs for security

## Monitoring

### Check Application Logs
Via Fly.io Dashboard:
- Go to your app → Monitoring → Live Logs

### Key Log Messages to Monitor
- `Redis connected successfully` - Redis connection established
- `OpenRouter API key found` - API key loaded
- `API call successful` - Request completed
- `Redis error in visitor count` - Counter issues to investigate

## Metrics & Counter Behavior

### Visitor Counter
- **Counts every page refresh** (not unique visitors)
- **No session/cookie tracking**
- **Persisted in Redis** (survives app restarts)
- **Initial value:** 413

### Product Metrics
- **Products Searched:** Increments when valid product is searched (starts at 703)
- **Norms Scouted:** Adds 10-20 randomly per product search (starts at 6,397)
- **Monthly Active Users:** Increments on every page load (starts at 413)

### Product Validation
- Uses confidence scoring (0.0-1.0) to detect garbage input
- Only rejects input with 0.9+ confidence of being garbage
- Allows creative/weird products (e.g., "flying toilet paper")
- Blocks obvious garbage:
  - Keyboard mashing: "asdfgh"
  - Personal statements: "I ate lunch"
  - Random text: "xxx yyy zzz"
  - Test inputs: "test test test"

### Known Issues Fixed
- Loading spinner now stops immediately after API response
- Scout Norms button can be used multiple times without page reload
- Validation is less aggressive - allows unusual product ideas

## Support

- OpenRouter Documentation: https://openrouter.ai/docs
- Fly.io Documentation: https://fly.io/docs
- Check API status: https://status.openrouter.ai

## Testing Checklist

- [ ] API key is set correctly
- [ ] `tests/test_api.py` passes all tests
- [ ] Local app responds to requests
- [ ] Deployed app shows "API key found" in logs
- [ ] Frontend can make successful API calls
- [ ] Error messages are helpful for debugging
  
# For the user 

How to Run NormScout Website Locally (Step-by-Step)
Quick Start Commands:
Option 1: From the root directory (Normscout folder):
cd Website/Hausertimo.github.io
python app.py
Option 2: If you're already in the Website folder:
cd Hausertimo.github.io
python app.py
Then:
Open your web browser
Go to: http://localhost:8080
That's it! The website should be running
To Stop the Server:
Press CTRL+C in the terminal window where it's running
If You Get Errors:
Missing dependencies error? Run this first:
pip install -r requirements.txt
Python not found? Make sure Python is installed:
python --version
If not installed, download from python.org
Complete Step-by-Step:
Open Command Prompt or Terminal
Navigate to the website folder:
cd c:\_git\Startup\Normscout\Website\Hausertimo.github.io
Run the app:
python app.py
You'll see: "Running on http://127.0.0.1:8080"
Open browser to: http://localhost:8080
That's all you need! The app will automatically find the API key from the .env file.