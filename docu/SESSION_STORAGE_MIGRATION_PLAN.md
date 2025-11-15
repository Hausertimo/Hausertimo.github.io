# Session Storage Migration Plan: In-Memory to Redis

**Status:** PLANNING
**Priority:** MEDIUM
**Current Risk:** Sessions lost on server restart
**Target:** Production-ready persistent session storage

---

## Current Implementation

**Location:** `routes/develope.py` line 23-24

```python
# In-memory storage for sessions (TODO: move to Redis)
conversation_sessions = {}
```

**Usage:**
- Used by all `/api/develope/*` endpoints
- Stores conversation state for teaser chat
- Keys: `session_id` (UUID)
- Values: `dict` with conversation history, product info, etc.

**Problem:**
- Sessions stored in Python dictionary (RAM only)
- Lost on server restart/deployment
- No persistence across multiple server instances
- Not production-ready

---

## Migration Strategy

### Phase 1: Redis Session Storage (Recommended)

**Benefits:**
- ✅ Persistent across restarts
- ✅ Shared across multiple instances
- ✅ Built-in TTL/expiration
- ✅ Redis already available in infrastructure

**Implementation Steps:**

1. **Add Redis session key prefix**
   ```python
   SESSION_PREFIX = "chat:session:"
   SESSION_TTL = 3600  # 1 hour timeout
   ```

2. **Create session storage wrapper**
   ```python
   def save_session(session_id, session_data):
       """Save conversation session to Redis"""
       key = f"{SESSION_PREFIX}{session_id}"
       redis_client.setex(key, SESSION_TTL, json.dumps(session_data))

   def get_session(session_id):
       """Retrieve conversation session from Redis"""
       key = f"{SESSION_PREFIX}{session_id}"
       data = redis_client.get(key)
       return json.loads(data) if data else None

   def delete_session(session_id):
       """Delete session from Redis"""
       key = f"{SESSION_PREFIX}{session_id}"
       redis_client.delete(key)
   ```

3. **Update all session access points** in `routes/develope.py`:
   - Line 54: `start_conversation()` - Use `save_session()`
   - Line 90: `continue_conversation()` - Use `get_session()` and `save_session()`
   - Line 187: `analyze_norms()` - Use `get_session()` and `save_session()`
   - Line 308: `ask_analysis_question()` - Use `get_session()`
   - Line 440: `get_session_route()` - Use `get_session()`

4. **Add session cleanup endpoint** (optional):
   ```python
   @develope_bp.route('/api/develope/session/<session_id>', methods=['DELETE'])
   def delete_session_route(session_id):
       """Delete a conversation session"""
       delete_session(session_id)
       return jsonify({"status": "deleted"})
   ```

---

### Phase 2: Testing & Validation

**Unit Tests:**
- Test session creation
- Test session retrieval
- Test session expiration (TTL)
- Test JSON serialization/deserialization
- Test missing session handling

**Integration Tests:**
- Start conversation → verify Redis storage
- Continue conversation → verify persistence
- Restart server → verify session survives
- Wait for TTL → verify auto-cleanup

**Load Testing:**
- Multiple concurrent sessions
- Session size limits
- Redis memory usage monitoring

---

### Phase 3: Deployment

**Pre-Deployment:**
1. Ensure Redis is available in production
2. Test Redis connection handling
3. Add error handling for Redis failures
4. Set appropriate TTL values

**Deployment Steps:**
1. Deploy new code with Redis sessions
2. Monitor Redis memory usage
3. Monitor session creation/retrieval logs
4. Verify no session loss issues

**Rollback Plan:**
- Keep old in-memory code commented out
- If issues arise, revert to in-memory with warning logs
- Fix issues and re-deploy

---

## Alternative: Supabase Session Storage

**If Redis is not preferred:**

Use Supabase table for session storage:

```sql
CREATE TABLE conversation_sessions (
  session_id UUID PRIMARY KEY,
  session_data JSONB NOT NULL,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  expires_at TIMESTAMP DEFAULT NOW() + INTERVAL '1 hour'
);

CREATE INDEX idx_sessions_expires ON conversation_sessions(expires_at);
```

**Pros:**
- Persistent in database
- No Redis dependency
- Queryable history

**Cons:**
- Slower than Redis
- More database load
- Requires cleanup job for expired sessions

---

## Recommended Timeline

| Phase | Duration | Tasks |
|-------|----------|-------|
| **Week 1** | Planning | Review this document, choose strategy |
| **Week 2** | Development | Implement Redis wrapper functions |
| **Week 3** | Testing | Unit tests, integration tests |
| **Week 4** | Deployment | Staging deployment, monitoring |
| **Week 5** | Production | Production deployment, verification |

---

## Code Changes Required

### Files to Modify:

1. **routes/develope.py**
   - Add session storage functions (save_session, get_session, delete_session)
   - Replace all `conversation_sessions[session_id]` with `get_session(session_id)`
   - Replace all direct dict assignments with `save_session(session_id, data)`
   - Remove global `conversation_sessions = {}`

2. **app.py** (if adding cleanup job)
   - Optional: Add background job to clean expired sessions

3. **tests/** (create new test file)
   - Add `tests/test_session_storage.py`
   - Test all session operations

---

## Session Data Structure

**Current Format:**
```python
{
    "session_id": "uuid-string",
    "history": [
        {"role": "user", "content": "..."},
        {"role": "assistant", "content": "..."}
    ],
    "product_description": "string",
    "complete": false,
    "matched_norms": [],
    "all_norm_results": {}
}
```

**Redis Key Format:**
```
chat:session:{uuid}
```

**TTL Considerations:**
- Active chat: 1 hour (3600 seconds)
- After analysis complete: 24 hours (86400 seconds)
- Option to extend TTL on each interaction

---

## Error Handling

**Redis Connection Failures:**
```python
def save_session(session_id, session_data):
    try:
        key = f"{SESSION_PREFIX}{session_id}"
        redis_client.setex(key, SESSION_TTL, json.dumps(session_data))
    except Exception as e:
        logger.error(f"Failed to save session {session_id}: {e}")
        # Fallback to in-memory for this request
        conversation_sessions[session_id] = session_data
```

**JSON Serialization Errors:**
```python
def save_session(session_id, session_data):
    try:
        serialized = json.dumps(session_data, default=str)
        # ... save to Redis
    except (TypeError, ValueError) as e:
        logger.error(f"Session data not JSON serializable: {e}")
        raise
```

---

## Monitoring & Metrics

**Key Metrics to Track:**
- Active session count: `redis_client.dbsize()`
- Session creation rate: counter
- Session retrieval errors: counter
- Redis memory usage: monitor
- Average session size: monitor

**Alerts:**
- Redis connection failures
- High session count (potential DoS)
- Large session sizes (>1MB)

---

## Next Steps

1. **Review and approve** this migration plan
2. **Choose strategy**: Redis (recommended) or Supabase
3. **Create development branch**: `feature/redis-session-storage`
4. **Implement** session storage wrapper functions
5. **Write tests** for session operations
6. **Deploy to staging** and verify
7. **Deploy to production** with monitoring

---

## Questions to Answer

- [ ] What should be the default session TTL? (Currently proposed: 1 hour)
- [ ] Should we extend TTL on each interaction?
- [ ] Do we need session cleanup API endpoint?
- [ ] Should sessions persist after analysis completion?
- [ ] What's the maximum session size we expect?
- [ ] Do we need session history/audit trail?

---

**Document Created:** November 15, 2025
**Last Updated:** November 15, 2025
**Status:** PENDING REVIEW
