# NormScout Flask Application - Comprehensive Codebase Analysis

## 1. MAIN FLASK APPLICATION STRUCTURE

### Entry Point: `/home/user/Hausertimo.github.io/app.py`
- **Framework**: Flask with Blueprints architecture
- **Port**: 8080 (configured in Flask and Gunicorn)
- **Static/Template Folder**: `static/` directory at `/`
- **Environment Loading**: python-dotenv (loads from parent directory .env file)
- **Key Dependencies**: Redis (required), Flask, Gunicorn

**Initialization Flow**:
1. Load environment variables first (critical for API keys)
2. Initialize Flask app instance
3. Set up Redis connection (REQUIRED - throws RuntimeError if missing)
4. Register all blueprints
5. Initialize blueprint-specific dependencies

**Redis Configuration**:
- Mandatory dependency - app fails to start without `REDIS_URL` env variable
- Used for: Visitor counters, metrics storage, workspace persistence
- Connection validation on startup

---

## 2. ROUTING STRUCTURE & BLUEPRINTS

### Blueprint Architecture (6 Blueprints registered):

#### **Blueprint 1: `main_bp` (main.py)**
- **Route Prefix**: Root `/`
- **Purpose**: Serves static pages
- **Endpoints**:
  - `GET /` → Serves `/static/index.html` (landing page)
  - `GET /privacy` → Serves `/static/privacy.html`
  - `GET /terms` → Serves `/static/terms.html`
  - `GET /contact` → Serves `/static/contact.html`
  - `GET /img/<filename>` → Serves images from `/static/img/`

#### **Blueprint 2: `analytics_bp` (analytics.py)**
- **Route Prefix**: `/api`
- **Purpose**: Tracks metrics and visitor analytics
- **Endpoints**:
  - `GET/POST /api/visitor-count` → Increments visitor counter (POST) or gets count (GET)
  - `GET /api/metrics` → Returns all metrics (products_searched, norms_scouted, monthly_users)
- **Data Storage**: Redis keys with initial values
  - `monthly_users`: 413
  - `products_searched`: 703
  - `norms_scouted`: 6397
- **Initialization**: `init_redis(redis_client)` called from app.py

#### **Blueprint 3: `compliance_bp` (compliance.py)**
- **Route Prefix**: `/api`
- **Purpose**: Product compliance analysis
- **Endpoints**:
  - `POST /api/run` → Main endpoint for product compliance analysis
    - Accepts: `{"product": "...", "country": "..."}`
    - Validates product using LLM
    - Increments counters on valid products
    - Returns validation status
- **Dependencies**: Injected at startup
  - Redis client
  - Service functions (validate_product_input, analyze_product_compliance)

#### **Blueprint 4: `develope_bp` (develope.py)**
- **Route Prefix**: `/develope` and `/api/develope`
- **Purpose**: AI-powered conversational workspace for compliance analysis
- **Endpoints**:
  - `GET /develope` → Renders `develope.html` template
  - `POST /api/develope/start` → Starts new conversation session
  - `POST /api/develope/respond` → Continues conversation
  - `POST /api/develope/analyze` → Analyzes norms for completed conversation
  - `GET /api/develope/analyze-stream` → SSE stream for real-time analysis progress
  - `POST /api/develope/ask-analysis` → Q&A about completed analysis (post-analysis)
  - `GET /api/develope/session/<session_id>` → Retrieves session data
- **Session Storage**: In-memory dictionary `conversation_sessions = {}`
  - TODO: Migrate to Redis (noted in code)
  - Sessions store: history, completeness status, product description, matched norms
- **Features**:
  - Conversational completeness analysis (LLM-based)
  - Multi-turn conversation support
  - Server-Sent Events (SSE) for streaming progress
  - Post-analysis Q&A functionality

#### **Blueprint 6: REMOVED - Old `workspace_bp` (workspace.py)**
- **Status**: DEPRECATED - Removed from codebase
- **Replacement**: Workspace functionality moved to `normscout_auth.py` (Supabase-based)
- **Old Route Prefix**: `/workspace` and `/api/workspace`
- **New Route Prefix**: `/api/workspaces` (in normscout_auth.py)
- **Migration**: Redis-based storage replaced with Supabase PostgreSQL database

---

## 3. DATABASE SETUP

### Database Type: **Redis (NoSQL Key-Value Store)**
- **No SQL Database** - Redis only
- **No ORM** - Direct Redis client usage (`redis.from_url()`)
- **Connection**: `redis_client = redis.from_url(REDIS_URL, decode_responses=True)`
- **Models**: None (using dictionaries/JSON for data structure)

### Data Storage Patterns:

#### Analytics Keys:
```
monthly_users      → Integer counter
products_searched  → Integer counter
norms_scouted      → Integer counter
```

#### Workspace Keys (DEPRECATED):
```
workspace:{uuid}  → REMOVED - Now stored in Supabase PostgreSQL (see normscout_auth.py)
```

#### Feedback:
```
File-based: feedback/feedback.jsonl (JSON Lines format)
```

#### Session Data:
```
In-memory: conversation_sessions dict (no persistence)
```

### Data Files:
- **norms.json** (`/home/user/Hausertimo.github.io/data/norms.json`)
  - 548 lines, ~24KB
  - Contains EU regulatory standards/norms database
  - Structure: Array of norm objects with `id`, `name`, `category`, `applies_to`, `description`, `url`
  - Examples: DIR-2014/35/EU (LVD), DIR-2014/30/EU (EMC), EN 62368-1, etc.

---

## 4. AUTHENTICATION & USER MANAGEMENT

### Current Status: **NO AUTHENTICATION IMPLEMENTED**

**Key Findings**:
- No login system
- No user accounts or user management
- No password hashing/verification
- No JWT or session tokens
- No role-based access control
- All endpoints publicly accessible

**Session Management**:
- Flask `session` is imported but NOT used for authentication
- Only in-memory `conversation_sessions` dictionary for ephemeral user conversations
- Sessions stored by `session_id` (UUID), not tied to users

**Feedback Collection** (Anonymous):
- User can optionally provide name/email in feedback forms
- Email is optional (not required for feedback submission)
- No user authentication needed to submit feedback

**Implications for Future Authentication**:
- All endpoints are currently public/stateless
- No database of users exists
- Workspace data is accessible via UUID only (security by obscurity, not authentication)
- Sessions expire when server restarts (in-memory storage)

---

## 5. FRONTEND APPROACH

### Architecture: **Multi-Page with Static HTML + JavaScript**

#### Page Structure:

1. **Static HTML Pages** (served from `/static/`):
   - `index.html` (18.5 KB) - Landing page with hero section, how-it-works, features
   - `privacy.html` (13.9 KB) - Privacy policy
   - `terms.html` (13.9 KB) - Terms of service
   - `contact.html` (15.7 KB) - Contact form/page

2. **Template-Rendered Pages** (Flask `render_template`):
   - `develope.html` (38.6 KB) - Conversational compliance workspace
   - `workspace.html` (17 KB) - Persistent workspace display

#### CSS Framework:
- **Style**: `/static/style.css` (29.9 KB)
- **Approach**: Custom CSS (no Bootstrap, Tailwind, or other framework detected)
- **CSS Variables**: Used extensively (brand colors, spacing, typography)
- **Responsive**: Mobile-first design with media queries and mobile menu toggle
- **Design**: Modern gradient-based UI with custom components

#### JavaScript Framework: **Vanilla JavaScript (ES6)**
- **Main File**: `/static/functions.js` (34.5 KB)
- **No Framework**: No React, Vue, Angular, etc.
- **Approach**: Plain JavaScript with modern features:
  - Fetch API for HTTP requests
  - Async/await patterns
  - Event listeners and DOM manipulation
  - No build tool or bundling

#### Key JavaScript Features:

**Initialization Functions**:
```javascript
- initializeMobileMenu()      // Hamburger menu for mobile
- initializeSmoothScrolling() // Anchor link smooth scroll
- initializeDemoSection()     // Demo/search functionality
- initializeAnimations()      // Scroll-based animations
- initializeEnhancedFormInteractions() // Form handling
- initializeVisitorCounter()  // Fetches and displays metrics
```

**Async Operations**:
```javascript
- fetch('/api/visitor-count', {POST}) // Increment counter
- fetch('/api/metrics')                // Get all metrics
- fetch('/api/run', {POST})           // Run compliance analysis
- fetch('/api/develope/start', {POST}) // Start conversation
```

**HTML Templates Used**:
```html
develope.html - Uses:
  - Chat messages container
  - Field blocks rendering system
  - Progress indicators
  - Real-time SSE stream handling

workspace.html - Uses:
  - Workspace data display
  - Norm listing
  - Q&A interface
  - Share/export functionality
```

#### Frontend Features:
- **Responsive Design**: Mobile hamburger menu, adaptive layouts
- **Animation**: Smooth transitions, scroll-triggered animations
- **Real-Time Updates**: Server-Sent Events (SSE) for streaming progress
- **Dynamic Forms**: Field blocks system for flexible form generation
- **Interactive Elements**: Expandable sections, button interactions, form validation
- **Analytics Display**: Live visitor counts and metrics display

---

## 6. DEPENDENCIES & LIBRARIES

### Main Dependencies (`requirements.txt`):
```
Flask          - Web framework
gunicorn       - WSGI application server
requests       - HTTP library (for API calls)
python-dotenv  - Environment variable management
redis          - Redis client for database/cache
```

### Service Libraries Used (via imports):

**AI/LLM Integration**:
- **OpenRouter API** - Third-party LLM provider
  - Models used:
    - `openai/gpt-4o-mini` - Default model for product validation
    - `anthropic/claude-3.5-sonnet` - For norm matching and completeness analysis
  - API Key: `openrouter` environment variable
  - Endpoint: `https://openrouter.ai/api/v1/chat/completions`

**Standard Library**:
- `os` - Environment variables, file system
- `logging` - Application logging
- `json` - JSON parsing
- `uuid` - Session ID generation
- `datetime` - Timestamps
- `threading` / `concurrent.futures` - Async norm matching

**Flask Extensions**:
- `Blueprint` - Modular routing
- `render_template` - HTML rendering
- `jsonify` - JSON responses
- `request` - HTTP request handling
- `session` - Flask session (imported but not actively used)
- `Response`, `stream_with_context` - SSE streaming

---

## 7. OVERALL ARCHITECTURE & ORGANIZATION

### Project Structure:
```
/home/user/Hausertimo.github.io/
├── app.py                     # Main Flask application
├── gunicorn.conf.py          # Gunicorn server config
├── requirements.txt          # Python dependencies
├── Dockerfile                # Docker image definition
├── fly.toml                  # Fly.io deployment config
├── CNAME                     # Domain configuration
│
├── routes/                   # Blueprint modules
│   ├── __init__.py
│   ├── main.py              # Static pages (/, /privacy, /terms, /contact)
│   ├── analytics.py         # Metrics endpoints
│   ├── compliance.py        # Product validation endpoint
│   ├── fields.py            # Field rendering/form endpoints
│   └── develope.py          # Conversational workspace
│
├── services/                # Business logic
│   ├── __init__.py
│   ├── openrouter.py       # LLM API integration
│   ├── product_conversation.py # Conversation analysis logic
│   └── norm_matcher.py     # Norm matching logic
│
│   Note: Workspace management moved to normscout_auth.py (Supabase-based)
│
├── templates/              # Jinja2 templates
│   ├── develope.html       # Workspace template
│   └── workspace.html      # Workspace display template
│
├── static/                 # Static assets
│   ├── index.html         # Landing page
│   ├── privacy.html       # Privacy policy
│   ├── terms.html         # Terms of service
│   ├── contact.html       # Contact page
│   ├── style.css          # Global styles
│   ├── functions.js       # Main JavaScript
│   ├── logo.ico          # Favicon
│   └── img/               # Logo images and SVGs
│
├── data/                   # Data files
│   └── norms.json         # EU regulatory standards database
│
├── feedback/              # User feedback storage
│   └── feedback.jsonl     # Feedback log (JSON Lines)
│
├── tests/                 # Test scripts
│   ├── test_api.py       # OpenRouter API testing
│   ├── simple_test.py    # Basic tests
│   └── reset_counters.py # Utility to reset metrics
│
└── docu/                  # Documentation
```

### Architectural Patterns:

#### **1. Blueprint-Based Routing**
- Modular organization - each feature is a separate blueprint
- Dependency injection pattern - services injected into blueprints at startup
- Clear separation of concerns

#### **2. Service Layer Architecture**
- Business logic separated from routes
- Reusable service functions
- Services handle: LLM calls, norm matching, workspace storage

#### **3. In-Memory Session Management**
- Ephemeral conversation sessions stored in Python dict
- Not persisted across server restarts
- Converted to persistent workspaces via Redis when complete

#### **4. Dependency Injection**
- Global variables in blueprints initialized at app startup
- Services passed to blueprints via `init_*` functions
- Avoids circular imports

#### **5. Redis as Persistent Backend**
- Metrics counters
- Workspace storage with TTL
- No traditional SQL database

#### **6. Frontend-Backend Integration**
- RESTful JSON API pattern
- Fetch API for all HTTP calls
- Server-Sent Events for real-time progress streaming
- Field blocks system for dynamic form rendering

### Application Flow:

1. **User lands on landing page** (`/index.html`)
   - Views metrics from `/api/metrics`
   - Mobile menu interaction via JavaScript

2. **User enters product description** 
   - `POST /api/run` → Validates product + analyzes compliance
   - Returns field blocks for rendering

3. **User accesses develope workspace** (`/develope`)
   - Starts conversation: `POST /api/develope/start`
   - Multi-turn dialog: `POST /api/develope/respond`
   - Analyzes norms: `GET /api/develope/analyze-stream` (SSE)
   - Q&A phase: `POST /api/develope/ask-analysis`

4. **Workspace persistence**
   - Converts session to workspace: `POST /api/workspace/create`
   - Workspace accessible indefinitely (30-day TTL): `GET /workspace/{id}`
   - Q&A continues in workspace: `POST /api/workspace/{id}/ask`

### Deployment:

**Containerization**:
- Docker: Python 3.11-slim base image
- Port: 8080
- Command: `gunicorn --config gunicorn.conf.py app:app`

**Server**:
- Gunicorn WSGI server (timeout: 180 seconds)
- Fly.io deployment (Frankfurt region)
- Force HTTPS enabled
- Auto-scaling enabled

**Environment Variables Required**:
- `REDIS_URL` - Redis connection string (mandatory)
- `openrouter` - OpenRouter API key (mandatory for LLM features)

---

## 8. KEY IMPLEMENTATION DETAILS RELEVANT TO AUTHENTICATION

### Current State:
- **No authentication layer** - all endpoints public
- **No user identification** - no user database or profiles
- **Session tracking** - only by anonymous UUIDs
- **Data access** - workspaces identified by UUID (guessable, not secure)

### For Future Authentication Implementation:

**Minimal Changes Needed**:
1. Add authentication blueprint with login/register endpoints
2. Add user database (would need SQLAlchemy + PostgreSQL/MySQL)
3. Add session middleware/decorator for protected routes
4. Modify workspace creation to tie workspaces to user_id
5. Add JWT or Flask-Session for token management

**Protected Routes to Consider**:
- `/api/workspace/<id>/ask` - Only workspace owner should access
- `/api/workspace/<id>/delete` - Only workspace owner should delete
- `/api/workspace/create` - Could be rate-limited
- Analytics endpoints - Could be protected from abuse

**Authentication Methods**:
- Username/Password with Flask-Login
- OAuth (Google, GitHub)
- JWT tokens via Flask-JWT-Extended
- API keys for programmatic access

---

## SUMMARY TABLE

| Aspect | Details |
|--------|---------|
| **Framework** | Flask with Blueprints |
| **Database** | Redis (no SQL) |
| **ORM** | None (direct Redis client) |
| **Models** | None (JSON in Redis) |
| **Auth** | NONE (no authentication) |
| **Frontend** | Vanilla JavaScript + HTML + CSS |
| **JS Framework** | None (plain ES6) |
| **CSS Framework** | Custom CSS |
| **API Type** | RESTful JSON |
| **Real-Time** | Server-Sent Events (SSE) |
| **LLM** | OpenRouter API (Claude, GPT-4o-mini) |
| **Server** | Gunicorn on Fly.io |
| **Feedback** | File-based (JSONL) |
| **Session Storage** | In-memory (Python dict) + Redis |
| **Static Files** | `/static` folder |
| **Templates** | 2 Jinja2 templates + 4 static HTML |

