# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview
NormScout is a compliance intelligence platform that helps businesses navigate international product regulations. The application uses OpenRouter's AI API to analyze product compliance requirements for different markets, providing instant regulatory insights.

## Architecture & Tech Stack
- **Frontend**: Vanilla HTML/CSS/JavaScript (no framework dependencies for simplicity)
- **Backend**: Flask (Python) - minimal, lightweight API server
- **AI Integration**: OpenRouter API (GPT-4-mini model)
- **Deployment**: Fly.io (containerized with Docker)
- **Environment**: Uses python-dotenv for local development

## File Structure & Purpose

### Core Application Files
- **app.py**: Flask backend that handles API requests and OpenRouter integration
  - Loads environment variables from .env
  - Provides /api/run endpoint for compliance analysis
  - Includes comprehensive logging and error handling
  - Serves static files (HTML, CSS, JS)

- **index.html**: Landing page with demo interface
  - Clean, professional design focused on conversion
  - Three-step demo flow: Product input → Country selection → Analysis
  - Mobile-responsive layout

- **functions.js**: Frontend logic and interactions
  - `formatMarkdownToHTML()`: Converts AI markdown responses to formatted HTML
  - `startDemo()`: Handles form submission with loading states
  - `showDemoResults()`: Displays formatted compliance analysis
  - Smooth scrolling, animations, and mobile menu functionality

- **style.css**: Design system and styling
  - CSS variables for consistent theming
  - Responsive grid layouts
  - Loading animations (spinner, slideUp)
  - Professional blue/white color scheme

### Logo Styling & Branding
- **Logo structure**: "NormScout" displayed as two parts
  - "Norm": Bold (font-weight: 700), Blue (#4c7fdc)
  - "Scout": Normal weight (font-weight: 400), Grey (#6b7280)
- **Logo size**: 27px font size
- **Header background**: Light grey (#f9fafb) with transparency (rgba(249, 250, 251, 0.95)) for contrast with grey "Scout" text
- **Logo classes**: `.logo-norm` and `.logo-scout` for consistent branding across the site
- **Usage**: Applied to both header logo and "Why NormScout?" section title

### Testing & Documentation
- **tests/test_api.py**: Comprehensive API testing script
  - Tests API key configuration
  - Direct OpenRouter API testing
  - Local Flask app testing
  - Color-coded terminal output for clarity

- **tests/simple_test.py**: Minimal API test for quick debugging
- **README_DEPLOYMENT.md**: Deployment instructions for Fly.io
- **requirements.txt**: Python dependencies (Flask, requests, gunicorn, python-dotenv)

### Configuration Files
- **Dockerfile**: Container configuration for Fly.io deployment
- **fly.toml**: Fly.io deployment settings
- **.env**: Local environment variables (not committed to git)

## Key Design Decisions & Thought Process

### 1. **Simplicity First**
Chose vanilla JavaScript over React/Vue to minimize complexity and dependencies. The application is straightforward enough that a framework would add unnecessary overhead.

### 2. **Environment Variable Management**
Implemented python-dotenv for seamless local development while using Fly.io secrets for production. This allows the same codebase to work locally and in production without modification.

### 3. **Enhanced Error Handling**
Added comprehensive logging throughout the application to make debugging easier:
- Startup logs show if API key is loaded
- Request/response logging for API calls
- Detailed error messages for common issues

### 4. **User Experience Focus**
- Loading animations provide immediate feedback
- Markdown formatting makes AI responses readable
- Professional design builds trust
- Mobile-first responsive approach

### 5. **Testing Infrastructure**
Created multiple test scripts to validate different aspects:
- Direct API testing to isolate OpenRouter issues
- Flask app testing to verify integration
- Color-coded output for better developer experience

### 6. **Security Considerations**
- API keys stored as environment variables, never in code
- Keys masked in logs
- HTTPS enforced in production (Fly.io)
- No sensitive data stored client-side

## Development Workflow

### Local Development
1. Set API key in .env file: `openrouter=sk-or-v1-...`
2. Install dependencies: `pip install -r requirements.txt`
3. Run app: `python app.py`
4. Test API: `python tests/test_api.py`

### IMPORTANT: Version Control
**ALWAYS commit and push changes after making updates:**
```bash
git add .
git commit -m "Descriptive message about changes"
git push
```
The user expects all changes to be committed and pushed to GitHub immediately.

### Deployment to Fly.io
1. Set secret: `fly secrets set openrouter='your-key'`
2. Deploy: `fly deploy`
3. Monitor: `fly logs --tail`

## Common Issues & Solutions

### API Returns 401 "User not found"
- API key is invalid or expired
- Solution: Get new key from OpenRouter dashboard

### No Response from Backend
- Check if Flask app is running
- Verify .env file is in correct location
- Check browser console for CORS errors

### Formatting Issues
- `formatMarkdownToHTML()` handles most markdown patterns
- Add new patterns as needed for specific AI responses

## Future Improvements to Consider
- Add caching for repeated queries
- Implement rate limiting
- Add more country options
- Create user accounts for saved searches
- Add export functionality for compliance reports
- Implement webhook notifications for regulation updates

## Testing Commands
```bash
# Test API directly
python tests/simple_test.py

# Comprehensive testing
python tests/test_api.py

# Test Flask endpoint
curl -X POST http://localhost:8080/api/run \
  -H "Content-Type: application/json" \
  -d '{"product":"Bluetooth Speaker","country":"eu"}'
```

## Important Notes
- Always test API changes locally before deploying
- Keep API keys secure and rotate regularly
- Monitor Fly.io logs for production issues
- The formatMarkdownToHTML function may need updates as AI response formats evolve