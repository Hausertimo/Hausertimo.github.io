# Supabase Authentication Setup Guide

Complete guide for implementing Google + GitHub OAuth with Supabase in your Flask app.

---

## ✅ What You've Already Done

- [x] Created Supabase project
- [x] Added environment variables (SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SERVICE_KEY)
- [x] Set up Google OAuth credentials
- [x] Set up GitHub OAuth credentials
- [x] Installed `supabase` and `weasyprint` packages

---

## 📋 What You Need to Do Now

### Step 1: Run Database Schema

1. Go to your Supabase dashboard: https://supabase.com/dashboard
2. Select your project: `svkhmzluonxvujwsrnzv`
3. Click **SQL Editor** (left sidebar)
4. Click **New Query**
5. Copy and paste this SQL:

```sql
-- Workspaces table
CREATE TABLE IF NOT EXISTS public.workspaces (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,

    -- User-facing fields
    name TEXT NOT NULL,
    workspace_number INTEGER NOT NULL,

    -- Compliance data
    product_description TEXT NOT NULL,
    matched_norms JSONB,
    all_results JSONB,

    -- Q&A history
    qa_history JSONB DEFAULT '[]'::jsonb,
    qa_count INTEGER DEFAULT 0,

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_accessed TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Soft delete
    is_archived BOOLEAN DEFAULT FALSE,

    -- Constraints
    CONSTRAINT unique_workspace_number_per_user UNIQUE(user_id, workspace_number)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_workspaces_user_id ON workspaces(user_id);
CREATE INDEX IF NOT EXISTS idx_workspaces_last_accessed ON workspaces(last_accessed DESC);
CREATE INDEX IF NOT EXISTS idx_workspaces_created_at ON workspaces(created_at DESC);

-- Row Level Security (RLS)
ALTER TABLE workspaces ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only access their own workspaces
DROP POLICY IF EXISTS "Users can access own workspaces" ON workspaces;
CREATE POLICY "Users can access own workspaces"
ON workspaces
FOR ALL
USING (auth.uid() = user_id);

-- Function to auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger to auto-update updated_at
DROP TRIGGER IF EXISTS update_workspaces_updated_at ON workspaces;
CREATE TRIGGER update_workspaces_updated_at
    BEFORE UPDATE ON workspaces
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
```

6. Click **Run** (or press Ctrl+Enter)
7. You should see "Success. No rows returned"

---

### Step 2: Update OAuth Callback URLs

#### Google Cloud Console

1. Go to https://console.cloud.google.com/apis/credentials
2. Find your OAuth 2.0 Client ID
3. Under **Authorized redirect URIs**, add:
   ```
   https://svkhmzluonxvujwsrnzv.supabase.co/auth/v1/callback
   ```
4. Click **Save**

#### GitHub

1. Go to https://github.com/settings/developers
2. Find your OAuth App "NormScout"
3. Update **Authorization callback URL** to:
   ```
   https://svkhmzluonxvujwsrnzv.supabase.co/auth/v1/callback
   ```
4. Click **Update application**

---

### Step 3: Add Environment Variable

Add this to your `.env` file:

```bash
# Site URL (for OAuth redirects)
SITE_URL=https://normscout.ch

# Or for local testing:
# SITE_URL=http://localhost:8080
```

---

### Step 4: Integrate with Flask App

In your `app.py`, add:

```python
# Import Supabase auth module
from supabase_auth import init_app, require_auth, get_current_user_id

# Initialize Supabase auth (registers all routes)
init_app(app)
```

That's it! All auth routes are now available:
- `/auth/login/google` - Login with Google
- `/auth/login/github` - Login with GitHub
- `/auth/callback` - OAuth callback
- `/auth/logout` - Logout
- `/auth/me` - Get current user
- `/api/workspaces/` - All workspace routes

---

## 🚀 Available API Endpoints

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/auth/login/google` | Login with Google |
| GET | `/auth/login/github` | Login with GitHub |
| GET | `/auth/callback` | OAuth callback (automatic) |
| POST | `/auth/session` | Create session (automatic) |
| POST | `/auth/logout` | Logout user |
| GET | `/auth/me` | Get current user info |

### Workspaces

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/workspaces/create` | Create workspace | ✅ |
| GET | `/api/workspaces/` | List all workspaces | ✅ |
| GET | `/api/workspaces/<id>` | Get single workspace | ✅ |
| PATCH | `/api/workspaces/<id>/rename` | Rename workspace | ✅ |
| DELETE | `/api/workspaces/<id>` | Delete workspace | ✅ |
| POST | `/api/workspaces/<id>/ask` | Ask question | ✅ |
| GET | `/api/workspaces/<id>/export/pdf` | Export as PDF | ✅ |

---

## 💻 Frontend Integration Examples

### Login Button

```html
<button onclick="loginWithGoogle()">Login with Google</button>
<button onclick="loginWithGitHub()">Login with GitHub</button>

<script>
function loginWithGoogle() {
    window.location.href = '/auth/login/google';
}

function loginWithGitHub() {
    window.location.href = '/auth/login/github';
}
</script>
```

### Create Workspace (After Analysis)

```javascript
// After compliance analysis, prompt for workspace name
const workspaceName = prompt("Name your workspace:");

const response = await fetch('/api/workspaces/create', {
    method: 'POST',
    credentials: 'include',  // Important: send cookies
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        name: workspaceName,
        product_description: productDescription,
        matched_norms: complianceResults.matched_norms,
        all_results: complianceResults.all_results
    })
});

const data = await response.json();
console.log("Workspace created:", data.workspace);
```

### List User's Workspaces

```javascript
const response = await fetch('/api/workspaces/', {
    credentials: 'include'  // Send auth cookie
});

const data = await response.json();
console.log("Workspaces:", data.workspaces);

// Display in UI
data.workspaces.forEach(ws => {
    console.log(`Workspace #${ws.workspace_number}: ${ws.name}`);
});
```

### Ask Question in Workspace

```javascript
const response = await fetch(`/api/workspaces/${workspaceId}/ask`, {
    method: 'POST',
    credentials: 'include',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        question: "What certifications are needed?"
    })
});

const data = await response.json();
console.log("Answer:", data.qa.answer);
```

### Export Workspace as PDF

```javascript
// Download PDF
window.location.href = `/api/workspaces/${workspaceId}/export/pdf`;
```

---

## 🔐 Security Features

### Built-in Security

1. **Row Level Security (RLS)** - Users can only access their own workspaces
2. **httpOnly Cookies** - Tokens not accessible to JavaScript (prevents XSS)
3. **CSRF Protection** - SameSite cookies
4. **Token Validation** - Every request validates JWT with Supabase
5. **Automatic User Isolation** - Database enforces ownership

### Protected Routes

Use `@require_auth` decorator:

```python
from supabase_auth import require_auth, get_current_user_id

@app.route('/my-protected-route')
@require_auth
def my_route():
    user_id = get_current_user_id()
    return jsonify({"message": f"Hello user {user_id}"})
```

---

## 🎯 Future: Add Workspace Limits

When ready to enforce limits, edit `supabase_auth.py`:

```python
class Config:
    MAX_WORKSPACES_PER_USER = 50   # Enable limit
    MAX_QA_PER_WORKSPACE = 100     # Enable limit
```

The code is already structured to enforce these limits automatically!

---

## 🧪 Testing

### Test OAuth Flow

1. Visit `https://normscout.ch/auth/login/google`
2. Authenticate with Google
3. You'll be redirected to `/dashboard`
4. Cookie is automatically set

### Test API

```bash
# Get current user (must be logged in via browser first to get cookie)
curl https://normscout.ch/auth/me \
  -H "Cookie: sb_session=YOUR_TOKEN"

# Or use Authorization header
curl https://normscout.ch/auth/me \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 🐛 Troubleshooting

### "Not authenticated" error

**Cause:** No token in cookie or header
**Fix:** Make sure you're logged in, or send `credentials: 'include'` in fetch

### "Workspace not found"

**Cause:** Trying to access another user's workspace
**Fix:** Row Level Security is working! You can only access your own workspaces

### OAuth callback fails

**Cause:** Wrong redirect URI in Google/GitHub
**Fix:** Make sure you added `https://svkhmzluonxvujwsrnzv.supabase.co/auth/v1/callback`

### Database connection error

**Cause:** Tables not created
**Fix:** Run the SQL schema in Step 1

---

## 📚 Next Steps

1. ✅ Run SQL schema (Step 1)
2. ✅ Update OAuth callbacks (Step 2)
3. ✅ Add SITE_URL to .env (Step 3)
4. ✅ Add `init_app(app)` to app.py (Step 4)
5. Create `/dashboard` page to list workspaces
6. Update `/develope` to prompt login before creating workspace
7. Create `/workspace/<id>` page to view/edit workspace
8. Integrate Q&A with your LLM service

---

## 🤝 Questions?

Check the code comments in `supabase_auth.py` for detailed documentation of each function!
