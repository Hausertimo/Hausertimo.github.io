# NormScout Deployment Guide

## Overview
NormScout is a Flask application that uses the OpenRouter API to provide compliance information for products in different markets. This guide covers local testing and deployment to Fly.io.

## Prerequisites
- Python 3.11+
- OpenRouter API key (get one at https://openrouter.ai)
- Fly.io account and CLI (for deployment)

## Local Development

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set Environment Variable

#### Windows (Command Prompt)
```cmd
set openrouter=sk-or-v1-your-actual-api-key-here
```

#### Windows (PowerShell)
```powershell
$env:openrouter = "sk-or-v1-your-actual-api-key-here"
```

#### Linux/Mac
```bash
export openrouter='sk-or-v1-your-actual-api-key-here'
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

## Deployment to Fly.io

### 1. Initial Setup (First Time Only)
```bash
# Install Fly CLI if not already installed
# See: https://fly.io/docs/getting-started/installing-flyctl/

# Login to Fly.io
fly auth login

# Launch the app (creates fly.toml)
fly launch --name normscout
```

### 2. Set the API Key Secret

**IMPORTANT:** Never commit your API key to git. Use Fly.io secrets instead:

```bash
fly secrets set openrouter='sk-or-v1-your-actual-api-key-here'
```

### 3. Deploy the Application
```bash
fly deploy
```

### 4. Check Deployment Status
```bash
# View logs
fly logs

# Check app status
fly status

# Open the deployed app
fly open
```

## Debugging Deployment Issues

### 1. Check Logs for Errors
```bash
fly logs --tail
```

Look for:
- "✓ OpenRouter API key found" - Key is configured correctly
- "✗ OpenRouter API key NOT FOUND!" - Key is missing
- API error messages with status codes

### 2. Verify Secret is Set
```bash
fly secrets list
```

You should see:
```
NAME        DIGEST                  CREATED AT
openrouter  xxxxxxxxxxxxxx          2025-09-23T10:00:00Z
```

### 3. Common Issues and Solutions

#### Issue: "API key NOT FOUND" in logs
**Solution:** Set the secret again:
```bash
fly secrets set openrouter='your-api-key'
fly deploy
```

#### Issue: 401 Unauthorized from OpenRouter
**Solution:** Your API key is invalid. Check:
- Key starts with 'sk-or-v1-' (typical format)
- No extra spaces or quotes in the key
- Key hasn't been revoked

#### Issue: 429 Too Many Requests
**Solution:** You've hit rate limits. Check your OpenRouter account for:
- Available credits
- Rate limit settings

#### Issue: Connection timeouts
**Solution:** The app has a 30-second timeout. Check:
- OpenRouter service status
- Network connectivity from Fly.io region

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

## File Structure
```
.
├── app.py              # Main Flask application
├── tests/test_api.py   # API testing script
├── requirements.txt    # Python dependencies
├── Dockerfile         # Container configuration
├── fly.toml           # Fly.io configuration
├── index.html         # Frontend
├── style.css          # Styles
└── functions.js       # Frontend JavaScript
```

## Security Notes

1. **Never commit API keys** to version control
2. Use environment variables or secrets management
3. The app uses HTTPS in production (enforced by Fly.io)
4. API keys are masked in logs for security

## Monitoring

### Check Application Logs
```bash
# Live logs
fly logs --tail

# Recent logs
fly logs -n 100
```

### Key Log Messages to Monitor
- `✓ OpenRouter API key found` - App started successfully
- `=== API Request Received ===` - Processing a request
- `API call successful!` - Request completed
- `OpenRouter API Error` - API issues to investigate

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