# Authentication Implementation Guide for NormScout

## Current State Summary

**Status**: NO AUTHENTICATION IMPLEMENTED

The application currently:
- Has 0 user management
- Uses no login system
- All endpoints are publicly accessible
- Sessions identified only by UUID (not authenticated)
- Workspaces accessible by guessing UUIDs
- No password hashing or token management
- All data is stateless and anonymous

---

## Recommended Authentication Architecture

### Option 1: Session-Based Authentication (Simplest)

**Tech Stack**:
- Flask-Login (session management)
- Flask-SQLAlchemy (user database)
- Werkzeug (password hashing)
- PostgreSQL or MySQL (user data)

**Steps to Implement**:

1. Add dependencies to `requirements.txt`:
   ```
   Flask-Login
   Flask-SQLAlchemy
   psycopg2-binary
   ```

2. Create user model in new file `models.py`:
   ```python
   from flask_sqlalchemy import SQLAlchemy
   from flask_login import UserMixin
   from werkzeug.security import generate_password_hash, check_password_hash
   
   db = SQLAlchemy()
   
   class User(UserMixin, db.Model):
       id = db.Column(db.Integer, primary_key=True)
       username = db.Column(db.String(80), unique=True, nullable=False)
       email = db.Column(db.String(120), unique=True, nullable=False)
       password_hash = db.Column(db.String(200), nullable=False)
       created_at = db.Column(db.DateTime, default=datetime.utcnow)
       workspaces = db.relationship('Workspace', backref='owner', lazy=True)
       
       def set_password(self, password):
           self.password_hash = generate_password_hash(password)
       
       def check_password(self, password):
           return check_password_hash(self.password_hash, password)
   ```

3. Create auth blueprint in `routes/auth.py`:
   ```python
   from flask import Blueprint, render_template, request, jsonify, redirect, url_for
   from flask_login import login_user, logout_user, login_required
   from werkzeug.security import generate_password_hash
   from models import db, User
   
   auth_bp = Blueprint('auth', __name__)
   
   @auth_bp.route('/register', methods=['POST'])
   def register():
       data = request.get_json()
       username = data.get('username')
       email = data.get('email')
       password = data.get('password')
       
       if User.query.filter_by(username=username).first():
           return jsonify({"error": "Username exists"}), 400
       
       user = User(username=username, email=email)
       user.set_password(password)
       db.session.add(user)
       db.session.commit()
       
       return jsonify({"message": "Registered successfully"}), 201
   
   @auth_bp.route('/login', methods=['POST'])
   def login():
       data = request.get_json()
       user = User.query.filter_by(username=data['username']).first()
       
       if user and user.check_password(data['password']):
           login_user(user)
           return jsonify({"message": "Logged in"}), 200
       return jsonify({"error": "Invalid credentials"}), 401
   
   @auth_bp.route('/logout', methods=['POST'])
   @login_required
   def logout():
       logout_user()
       return jsonify({"message": "Logged out"}), 200
   ```

4. Update `app.py` to initialize auth:
   ```python
   from flask_login import LoginManager
   from models import db, User
   
   app = Flask(__name__)
   app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
   app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
   
   db.init_app(app)
   login_manager = LoginManager()
   login_manager.init_app(app)
   
   @login_manager.user_loader
   def load_user(user_id):
       return User.query.get(int(user_id))
   
   app.register_blueprint(auth_bp)
   ```

5. Protect workspace routes with `@login_required`:
   ```python
   from flask_login import login_required, current_user
   
   @workspace_bp.route('/api/workspace/create', methods=['POST'])
   @login_required
   def api_create_workspace():
       # Tie workspace to current_user
       workspace = create_workspace(redis_client, session_data, user_id=current_user.id)
       return jsonify({"workspace_id": workspace.id})
   ```

**Pros**:
- Simple to implement
- Familiar to Flask developers
- Built on standard libraries

**Cons**:
- Requires SQL database setup
- Session storage can become bottleneck at scale
- Not ideal for mobile apps

---

### Option 2: JWT Token-Based Authentication (Scalable)

**Tech Stack**:
- Flask-JWT-Extended (token management)
- Flask-SQLAlchemy (user database)
- PostgreSQL or MySQL

**Key Changes**:

1. Add to `requirements.txt`:
   ```
   Flask-JWT-Extended
   Flask-SQLAlchemy
   psycopg2-binary
   ```

2. Configure JWT in `app.py`:
   ```python
   from flask_jwt_extended import JWTManager
   
   app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')
   jwt = JWTManager(app)
   ```

3. Create auth endpoints:
   ```python
   @auth_bp.route('/login', methods=['POST'])
   def login():
       data = request.get_json()
       user = User.query.filter_by(username=data['username']).first()
       
       if user and user.check_password(data['password']):
           access_token = create_access_token(identity=user.id)
           return jsonify({"access_token": access_token}), 200
       return jsonify({"error": "Invalid credentials"}), 401
   ```

4. Protect routes with decorator:
   ```python
   from flask_jwt_extended import jwt_required, get_jwt_identity
   
   @workspace_bp.route('/api/workspace/<id>/ask', methods=['POST'])
   @jwt_required()
   def api_workspace_ask(id):
       user_id = get_jwt_identity()
       workspace = load_workspace(redis_client, id)
       
       # Verify ownership
       if workspace['owner_id'] != user_id:
           return jsonify({"error": "Unauthorized"}), 403
       
       # Process Q&A
       return jsonify(result)
   ```

**Pros**:
- Stateless (no session storage)
- Scales to many servers
- Works well with mobile/SPA
- Standard JWT format

**Cons**:
- Requires careful token management
- Need refresh token strategy
- Slightly more complex setup

---

### Option 3: OAuth2 (Google/GitHub Login)

**Tech Stack**:
- Authlib (OAuth client)
- Flask-SQLAlchemy (optional user DB)

**Simplified Setup**:

1. Add to `requirements.txt`:
   ```
   authlib
   ```

2. Configure in `app.py`:
   ```python
   from authlib.integrations.flask_client import OAuth
   
   oauth = OAuth(app)
   google = oauth.register(
       name='google',
       client_id=os.getenv('GOOGLE_CLIENT_ID'),
       client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
       server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
       client_kwargs={'scope': 'openid email profile'}
   )
   ```

3. Auth routes:
   ```python
   @auth_bp.route('/login/google')
   def google_login():
       redirect_uri = url_for('auth.google_callback', _external=True)
       return google.authorize_redirect(redirect_uri)
   
   @auth_bp.route('/login/google/callback')
   def google_callback():
       token = google.authorize_access_token()
       user_info = token['userinfo']
       
       # Find or create user
       user = User.query.filter_by(email=user_info['email']).first()
       if not user:
           user = User(username=user_info['email'], email=user_info['email'])
           db.session.add(user)
       
       login_user(user)
       return redirect('/')
   ```

**Pros**:
- No password management needed
- Quick implementation
- Familiar UX for users

**Cons**:
- Dependency on OAuth provider
- Less control over user data
- Provider-specific setup

---

## Database Schema

### For Session or JWT Auth:

```sql
-- Users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(80) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(200) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Workspaces table (update from current Redis)
CREATE TABLE workspaces (
    id UUID PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    product_description TEXT,
    matched_norms JSONB,
    all_results JSONB,
    qa_history JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP
);

-- Sessions table (for session-based auth)
CREATE TABLE sessions (
    session_id VARCHAR(255) PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP
);

-- Feedback table (update from JSON file)
CREATE TABLE feedback (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    product VARCHAR(255),
    message TEXT,
    email VARCHAR(120),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## Protected Routes & Middleware

### Routes Requiring Authentication:

```python
# Workspace management - only by owner
@workspace_bp.route('/api/workspace/create', methods=['POST'])
@login_required
def create_workspace():
    # Tie to current_user.id
    
@workspace_bp.route('/api/workspace/<id>/ask', methods=['POST'])
@login_required
def workspace_ask(id):
    # Verify ownership before allowing Q&A
    
@workspace_bp.route('/api/workspace/<id>/delete', methods=['DELETE'])
@login_required
def delete_workspace(id):
    # Only owner can delete

# Conversation sessions - track user
@develope_bp.route('/api/develope/start', methods=['POST'])
@login_required
def start_conversation():
    # Tie session to current_user.id

# Optional: Rate limiting on expensive operations
@compliance_bp.route('/api/run', methods=['POST'])
@login_required
@rate_limit('10 per minute')
def run_compliance():
    # Expensive LLM operations
```

### Authentication Middleware Decorator:

```python
from functools import wraps
from flask_login import current_user
from flask import jsonify

def workspace_owner_required(f):
    @wraps(f)
    def decorated_function(workspace_id):
        workspace = load_workspace(redis_client, workspace_id)
        
        if not workspace:
            return jsonify({"error": "Not found"}), 404
        
        if workspace.get('user_id') != current_user.id:
            return jsonify({"error": "Forbidden"}), 403
        
        return f(workspace_id, workspace)
    
    return decorated_function

# Usage:
@workspace_bp.route('/api/workspace/<id>/ask', methods=['POST'])
@login_required
@workspace_owner_required
def api_workspace_ask(id, workspace):
    # workspace already loaded and verified
```

---

## Frontend Authentication Integration

### Required Frontend Changes:

1. **Login/Register Pages**:
   ```html
   <!-- Create static/login.html -->
   <form id="login-form">
       <input type="text" id="username" placeholder="Username">
       <input type="password" id="password" placeholder="Password">
       <button type="submit">Login</button>
   </form>
   
   <script>
   document.getElementById('login-form').addEventListener('submit', async (e) => {
       e.preventDefault();
       
       const response = await fetch('/api/auth/login', {
           method: 'POST',
           headers: {'Content-Type': 'application/json'},
           body: JSON.stringify({
               username: document.getElementById('username').value,
               password: document.getElementById('password').value
           })
       });
       
       const data = await response.json();
       
       if (response.ok) {
           // Store token (JWT)
           localStorage.setItem('access_token', data.access_token);
           // Or session is auto-handled by Flask
           window.location.href = '/develope';
       }
   });
   </script>
   ```

2. **Add JWT Header to API Calls**:
   ```javascript
   // For JWT:
   const token = localStorage.getItem('access_token');
   
   fetch('/api/workspace/create', {
       method: 'POST',
       headers: {
           'Content-Type': 'application/json',
           'Authorization': `Bearer ${token}`
       },
       body: JSON.stringify({session_id: sessionId})
   });
   
   // For Session-based: automatic with credentials
   fetch('/api/workspace/create', {
       method: 'POST',
       credentials: 'include', // Send cookies
       headers: {'Content-Type': 'application/json'},
       body: JSON.stringify({session_id: sessionId})
   });
   ```

3. **Protect Frontend Routes**:
   ```javascript
   // In functions.js - add auth check before develope
   async function checkAuth() {
       const response = await fetch('/api/auth/check', {
           credentials: 'include'
       });
       
       if (!response.ok) {
           window.location.href = '/login';
           return false;
       }
       return true;
   }
   
   // In develope.html init:
   document.addEventListener('DOMContentLoaded', async () => {
       if (!await checkAuth()) return;
       initializeDevelopeWorkspace();
   });
   ```

---

## Environment Variables to Add

```bash
# Session/JWT Auth
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-key-here

# Database
DATABASE_URL=postgresql://user:password@localhost/normscout_db

# OAuth (optional)
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret

# Rate limiting (optional)
RATELIMIT_STORAGE_URL=redis://localhost:6379/1
```

---

## Migration Strategy

### Phase 1: Add Auth Infrastructure (Week 1)
- [ ] Add SQLAlchemy models for User/Workspace
- [ ] Create auth blueprint with register/login
- [ ] Add database migrations
- [ ] Test basic authentication

### Phase 2: Protect Workspace Routes (Week 2)
- [ ] Add login_required decorators
- [ ] Add workspace ownership verification
- [ ] Update workspace storage to include user_id
- [ ] Migrate existing workspaces to have user_id

### Phase 3: Frontend Login UI (Week 3)
- [ ] Create login/register pages
- [ ] Update functions.js for auth flow
- [ ] Add logout button to header
- [ ] Show current user in UI

### Phase 4: Enhance Security (Week 4)
- [ ] Add rate limiting
- [ ] Add email verification
- [ ] Add password reset functionality
- [ ] Add account settings page

---

## Testing Authentication

```python
# tests/test_auth.py
import pytest
from app import app, db
from models import User

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.session.remove()
        db.drop_all()

def test_register(client):
    response = client.post('/api/auth/register', json={
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'testpass'
    })
    assert response.status_code == 201

def test_login(client):
    # Register first
    client.post('/api/auth/register', json={
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'testpass'
    })
    
    # Login
    response = client.post('/api/auth/login', json={
        'username': 'testuser',
        'password': 'testpass'
    })
    assert response.status_code == 200

def test_protected_route(client):
    # Try without auth
    response = client.post('/api/workspace/create')
    assert response.status_code == 401
```

---

## Recommended Approach for NormScout

**Recommendation: Option 2 (JWT Token-Based)**

**Reasoning**:
1. Application is AI/API-heavy, fits JWT pattern
2. May want mobile app in future (JWT is mobile-friendly)
3. Stateless = easier to scale
4. Frontend already uses Fetch API (works well with Bearer tokens)
5. Redux/session state management for frontend

**Implementation Order**:
1. Add Flask-JWT-Extended + SQLAlchemy
2. Create User model with basic fields
3. Create /api/auth/register and /api/auth/login endpoints
4. Add @jwt_required() to workspace routes
5. Update workspace storage to include user_id
6. Update frontend login flow
7. Add email verification and password reset later

**Time Estimate**: 2-3 days for basic implementation
