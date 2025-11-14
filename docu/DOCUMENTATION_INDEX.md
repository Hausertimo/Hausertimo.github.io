# NormScout Codebase Documentation Index

This directory contains comprehensive documentation of the NormScout Flask application codebase, prepared for in-depth understanding and authentication implementation planning.

## Documentation Files

### 1. **CODEBASE_ANALYSIS.md** (18 KB)
**Comprehensive technical analysis of the entire application**

Contains:
- Flask application structure & entry point (app.py)
- Complete routing structure with all 6 blueprints
- Database setup (Redis configuration)
- Current authentication status (NONE - all endpoints public)
- Frontend architecture (Vanilla JS, custom CSS, static HTML)
- All dependencies and libraries (Flask, Redis, OpenRouter API, etc.)
- Overall architecture & organization patterns
- Project file structure

**Best for**: Getting a complete technical overview, understanding how components fit together

**Key Sections**:
- Section 2: All 6 Blueprints detailed (main, analytics, compliance, fields, develope, workspace)
- Section 4: Authentication findings - NO login system exists
- Section 7: Overall architecture & design patterns

---

### 2. **ARCHITECTURE_DIAGRAMS.md** (27 KB)
**Visual system architecture and data flow diagrams**

Contains:
- High-level system flow diagram (Frontend → Flask → Services → Redis → External APIs)
- Request-response flow for compliance analysis (4 steps)
- Norm matching detailed process
- Authentication & security current state (all public endpoints)
- Deployment architecture (Fly.io setup)
- Key file locations and directory organization

**Best for**: Understanding system flow, how requests are processed, seeing architecture visually

**Key Diagrams**:
- System flow: Client → Blueprints → Services → Redis
- User journey: Landing page → Validation → Conversation → Workspace
- Norm matching: Product description → LLM calls → Results
- Security: 4 levels of endpoint access (all public)
- Deployment: Docker → Fly.io → External services

---

### 3. **AUTHENTICATION_GUIDE.md** (16 KB)
**Step-by-step guide to implementing authentication**

Contains:
- Current state summary (NO authentication)
- 3 recommended authentication approaches:
  1. Session-based (simplest)
  2. JWT Token-based (recommended - scalable)
  3. OAuth2 (Google/GitHub login)
- Database schemas for user management
- Protected routes and middleware decorators
- Frontend authentication integration
- Environment variables needed
- Phase-by-phase migration strategy
- Testing examples
- Recommendation: JWT Token-Based approach

**Best for**: Planning and implementing authentication, understanding trade-offs

**Recommendation**:
- **JWT Token-Based Auth** (Option 2)
- Reasoning: API-heavy app, future mobile apps, stateless scaling
- Time estimate: 2-3 days for basic implementation
- Requires: Flask-JWT-Extended, SQLAlchemy, PostgreSQL/MySQL

---

### 4. **NORMS_GUIDE.md** (15 KB - Existing)
**EU regulatory norms and compliance standards database**

Contains information about the norms.json database and compliance requirements.

---

## Quick Reference: Application Overview

### Technology Stack

| Component | Technology |
|-----------|-----------|
| **Web Framework** | Flask with Blueprints |
| **Database** | Redis (cache) - NO SQL DB |
| **ORM** | None (direct Redis client) |
| **Authentication** | NONE (needs implementation) |
| **Frontend** | Vanilla JavaScript (ES6) + Custom CSS |
| **Server** | Gunicorn (WSGI) |
| **Deployment** | Docker on Fly.io |
| **External APIs** | OpenRouter (LLM proxy) |

### Key Statistics

- **6 Blueprints**: main, analytics, compliance, fields, develope, workspace
- **5 Service Modules**: openrouter, product_conversation, norm_matcher, field_framework, workspace_storage
- **2 Flask Templates**: develope.html, workspace.html
- **4 Static Pages**: index.html, privacy.html, terms.html, contact.html
- **1 Data File**: norms.json (EU standards - 548 lines)
- **Dependencies**: 5 (Flask, gunicorn, requests, python-dotenv, redis)
- **Code Files**: 18 Python files + HTML/CSS/JS

### Current Status

- **Authentication**: None
- **User Management**: None
- **Database**: Redis only (no user data storage)
- **Session Storage**: In-memory Python dict (not persisted)
- **Security Model**: Public endpoints + UUID-based access

---

## How to Use This Documentation

### For New Developers
1. Start with **CODEBASE_ANALYSIS.md** (Section 1-2)
2. Read **ARCHITECTURE_DIAGRAMS.md** to see how it flows
3. Review the routes in CODEBASE_ANALYSIS.md (Section 2)

### For Authentication Implementation
1. Read **CODEBASE_ANALYSIS.md** Section 4 (current state)
2. Study **AUTHENTICATION_GUIDE.md** (Options and recommendations)
3. Use the database schema and code examples provided
4. Follow the phase-by-phase migration strategy

### For Frontend Development
1. Check CODEBASE_ANALYSIS.md Section 5 (Frontend approach)
2. Review ARCHITECTURE_DIAGRAMS.md (User journey flow)
3. Look at static/functions.js for API patterns
4. Check AUTHENTICATION_GUIDE.md for auth integration

### For Deployment/DevOps
1. Read ARCHITECTURE_DIAGRAMS.md (Deployment section)
2. Check app.py for environment variables needed
3. Review fly.toml and Dockerfile configuration
4. Note the Redis requirement (REDIS_URL env var)

---

## Key Files in Repository

### Critical Files
- `/app.py` - Main Flask application entry point
- `/requirements.txt` - Python dependencies (5 packages)
- `/Dockerfile` - Docker image configuration
- `/fly.toml` - Fly.io deployment configuration
- `/data/norms.json` - EU standards database

### Route Modules
- `/routes/main.py` - Landing page & static routes
- `/routes/analytics.py` - Metrics & visitor tracking
- `/routes/compliance.py` - Product validation
- `/routes/fields.py` - Dynamic form blocks
- `/routes/develope.py` - Conversational workspace
- `/routes/workspace.py` - Persistent storage

### Service Modules
- `/services/openrouter.py` - LLM API integration
- `/services/product_conversation.py` - Conversation AI
- `/services/norm_matcher.py` - Norm matching
- `/services/field_framework.py` - Dynamic forms
- `/services/workspace_storage.py` - Redis persistence

### Frontend Files
- `/static/index.html` - Landing page
- `/static/functions.js` - Main JavaScript (34.5 KB)
- `/static/style.css` - Global styles (29.9 KB)
- `/templates/develope.html` - Workspace template
- `/templates/workspace.html` - Workspace display

---

## Critical Implementation Notes

### Environment Variables Required

```bash
# Mandatory
REDIS_URL=redis://...           # Redis connection
openrouter=sk-...               # OpenRouter API key

# For Authentication (when implemented)
SECRET_KEY=your-secret-key      # Flask session
JWT_SECRET_KEY=your-jwt-secret  # JWT signing
DATABASE_URL=postgresql://...   # User database
```

### Important TODOs Found in Code

1. **develope.py (line 23)**: "TODO: move to Redis"
   - Currently uses in-memory conversation_sessions dict
   - Should migrate to Redis for persistence

2. **Database**: "No SQL database used"
   - Only Redis for caching
   - Need PostgreSQL/MySQL when adding user management

3. **Rate Limiting**: Not implemented
   - /api/run endpoint calls expensive LLM operations
   - Should add rate limiting before authentication

---

## API Endpoints Overview

### Public Endpoints (No Auth)
```
GET  /                    - Landing page
GET  /privacy             - Privacy policy
GET  /terms               - Terms of service
GET  /contact             - Contact page
POST /api/visitor-count   - Increment visitor counter
GET  /api/metrics         - Get analytics metrics
POST /api/run             - Product compliance check
GET  /api/fields/get      - Get field blocks
POST /api/fields/submit   - Submit field data
POST /api/feedback/submit - Submit user feedback
```

### Session-Based Endpoints (Session ID only)
```
GET  /develope                          - Render workspace
POST /api/develope/start                - Start conversation
POST /api/develope/respond              - Continue conversation
POST /api/develope/analyze              - Analyze norms
GET  /api/develope/analyze-stream       - Stream analysis (SSE)
POST /api/develope/ask-analysis         - Q&A about analysis
GET  /api/develope/session/{id}         - Get session data
```

### Workspace Endpoints (UUID only)
```
GET  /workspace/{id}                    - View workspace
GET  /api/workspace/{id}/data           - Get workspace JSON
POST /api/workspace/{id}/ask            - Q&A in workspace
DELETE /api/workspace/{id}/delete       - Delete workspace
POST /api/workspace/create              - Create workspace
```

**Security Note**: No authentication on any endpoint. Workspaces accessible by UUID only.

---

## Next Steps for Authentication

Based on the analysis, here's the recommended path forward:

### Immediate Actions
1. Review **AUTHENTICATION_GUIDE.md** in full
2. Choose authentication method (recommended: JWT Token-Based)
3. Plan database setup (PostgreSQL recommended)
4. Design user model structure

### Week 1: Infrastructure
- Add SQLAlchemy and Flask-JWT-Extended
- Create User model
- Create auth blueprint with register/login
- Set up test database

### Week 2: Integration
- Protect workspace routes with @jwt_required()
- Update workspace storage to track user_id
- Add ownership validation middleware
- Migrate existing workspaces

### Week 3: Frontend
- Create login/register UI
- Update function.js for JWT token handling
- Add user profile display
- Create logout functionality

### Week 4: Enhancement
- Add rate limiting
- Add email verification
- Add password reset
- Add account settings

---

## Document Maintenance

These documents were generated on: **2025-11-13**

**Update when**:
- Major architectural changes
- New blueprints or services added
- Authentication is implemented
- Frontend framework changes
- Deployment configuration changes

---

## Questions?

Refer to the specific documentation:
- **"How does X work?"** → CODEBASE_ANALYSIS.md
- **"What's the overall flow?"** → ARCHITECTURE_DIAGRAMS.md
- **"How do I add authentication?"** → AUTHENTICATION_GUIDE.md
- **"What environment variables are needed?"** → app.py or CODEBASE_ANALYSIS.md Section 7

Good luck with your implementation!
