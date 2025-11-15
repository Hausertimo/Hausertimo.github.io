# NormScout System Architecture Diagram

## High-Level System Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                      FRONTEND (Browser)                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────┐    ┌──────────────────┐                 │
│  │  index.html      │    │  develope.html   │                 │
│  │  (Landing Page)  │    │  (Workspace)     │                 │
│  └──────────────────┘    └──────────────────┘                 │
│           │                        │                           │
│  ┌────────┴────────┐      ┌────────┴────────┐                 │
│  │ Vanilla JS      │      │ Vanilla JS      │                 │
│  │ ES6/Fetch API   │      │ SSE Streaming   │                 │
│  │ Custom CSS      │      │ Real-time UI    │                 │
│  └────────┬────────┘      └────────┬────────┘                 │
│           │                        │                           │
└───────────┼────────────────────────┼──────────────────────────┘
            │                        │
            │   REST JSON API        │   SSE (Server-Sent Events)
            │                        │
┌───────────┼────────────────────────┼──────────────────────────┐
│ FLASK APPLICATION (Backend - Port 8080)                        │
├───────────┼────────────────────────┼──────────────────────────┤
│           │                        │                           │
│  ┌────────▼──────────┐   ┌─────────▼────────┐               │
│  │   BLUEPRINTS      │   │   BLUEPRINTS     │               │
│  │                   │   │                  │               │
│  │ ┌─────────────┐   │   │ ┌──────────────┐ │               │
│  │ │ main_bp     │   │   │ │ analytics_bp │ │               │
│  │ │ (Static)    │   │   │ │ (Metrics)    │ │               │
│  │ └─────────────┘   │   │ └──────────────┘ │               │
│  │                   │   │                  │               │
│  │ ┌─────────────┐   │   │ ┌──────────────┐ │               │
│  │ │compliance_bp│   │   │ │ fields_bp    │ │               │
│  │ │(Validation) │   │   │ │ (Forms)      │ │               │
│  │ └─────────────┘   │   │ └──────────────┘ │               │
│  │                   │   │                  │               │
│  │ ┌─────────────┐   │   │ ┌──────────────┐ │               │
│  │ │develope_bp  │   │   │ │workspace_bp  │ │               │
│  │ │(Conversational)   │ │(Persistent)  │ │               │
│  │ └─────────────┘   │   │ └──────────────┘ │               │
│  └───────┬──────────┘   └────────┬──────────┘               │
│          │                       │                           │
│  ┌───────┴───────────────────────┴──────┐                   │
│  │      SERVICES LAYER                  │                   │
│  │                                      │                   │
│  │ ┌──────────────────────────────────┐ │                   │
│  │ │ openrouter.py                    │ │                   │
│  │ │ (LLM API integration)            │ │                   │
│  │ └──────────────────────────────────┘ │                   │
│  │                                      │                   │
│  │ ┌──────────────────────────────────┐ │                   │
│  │ │ product_conversation.py          │ │                   │
│  │ │ (Completeness analysis)          │ │                   │
│  │ └──────────────────────────────────┘ │                   │
│  │                                      │                   │
│  │ ┌──────────────────────────────────┐ │                   │
│  │ │ norm_matcher.py                  │ │                   │
│  │ │ (Compliance matching)            │ │                   │
│  │ └──────────────────────────────────┘ │                   │
│  │                                      │                   │
│  │ ┌──────────────────────────────────┐ │                   │
│  │ │ (workspace_storage.py REMOVED)   │ │                   │
│  │ │ (Now in normscout_auth.py)       │ │                   │
│  │ └──────────────────────────────────┘ │                   │
│  └──────────┬──────────────────────────┘                   │
│             │                                               │
│  ┌──────────┴──────────┐   ┌─────────────────┐            │
│  │    DATA/FILES       │   │   EXTERNAL API  │            │
│  │                     │   │                 │            │
│  │ ┌────────────────┐  │   │ ┌──────────────┐│            │
│  │ │ norms.json     │  │   │ │ OpenRouter   ││            │
│  │ │ (EU Standards) │  │   │ │ (LLM)        ││            │
│  │ └────────────────┘  │   │ └──────────────┘│            │
│  │                     │   │                 │            │
│  │ ┌────────────────┐  │   │ ┌──────────────┐│            │
│  │ │feedback.jsonl  │  │   │ │ Anthropic    ││            │
│  │ │ (User feedback)│  │   │ │ Claude 3.5   ││            │
│  │ └────────────────┘  │   │ └──────────────┘│            │
│  └─────────┬───────────┘   │                 │            │
│            │               │ ┌──────────────┐│            │
│            │               │ │ OpenAI       ││            │
│            │               │ │ GPT-4o-mini  ││            │
│            │               │ └──────────────┘│            │
└────────────┼───────────────└─────────────────┘            │
             │                                               │
┌────────────┴──────────────────────────────────────────────┐
│           REDIS (Persistent Cache)                         │
├────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────────────────────────────────────────────┐ │
│  │ Analytics Counters:                                  │ │
│  │  - monthly_users (init: 413)                        │ │
│  │  - products_searched (init: 703)                    │ │
│  │  - norms_scouted (init: 6397)                       │ │
│  └──────────────────────────────────────────────────────┘ │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐ │
│  │ Workspace Storage:                                   │ │
│  │  Key: workspace:{uuid}                              │ │
│  │  Value: JSON (product, analysis, qa_history)       │ │
│  │  TTL: 30 days                                       │ │
│  └──────────────────────────────────────────────────────┘ │
│                                                             │
└────────────────────────────────────────────────────────────┘
```

## Request-Response Flow: Product Compliance Analysis

```
┌────────────────────────────────────────────────────────────┐
│ USER JOURNEY: From Product Input to Compliance Results    │
└────────────────────────────────────────────────────────────┘

Step 1: LANDING PAGE
───────────────────
  User visits /
    │
    ├─ Load index.html
    ├─ Fetch /api/metrics
    │   └─> Display: products_searched, norms_scouted, monthly_users
    ├─ Post to /api/visitor-count
    │   └─> Increment monthly_users counter
    └─> User enters product description

Step 2: QUICK VALIDATION (Optional)
──────────────────────────────────────
  POST /api/run
    │
    ├─ Input: {"product": "...", "country": "..."}
    │
    ├─ validate_product_input() [LLM]
    │   └─> Call OpenRouter: "Is this a real product?"
    │
    ├─ If invalid:
    │   ├─ Create error field block
    │   ├─ Add feedback button
    │   └─ Return error block to frontend
    │
    └─ If valid:
        ├─ Increment counters (Redis)
        ├─ analyze_product_compliance() [LLM]
        └─> Return compliance results

Step 3: CONVERSATIONAL WORKSPACE (Detailed Analysis)
───────────────────────────────────────────────────
  GET /develope (Render workspace page)

  Step 3a: Start Conversation
  ───────────────────────
  POST /api/develope/start
    │
    ├─ Create session_id (UUID)
    ├─ analyze_completeness() [LLM]
    │   └─> "Do we have enough product info?"
    │
    └─ Response: session_id + AI question or "Complete!"

  Step 3b: Multi-turn Dialog (Loop)
  ─────────────────────────────
  POST /api/develope/respond
    │
    ├─ Store user response in history
    ├─ analyze_completeness() [LLM] again
    │
    ├─ If not complete:
    │   ├─ generate_next_question() [LLM]
    │   └─ Return next question
    │
    └─ If complete:
        └─> Return "Ready to analyze!"

  Step 3c: Stream Norm Analysis
  ──────────────────────────
  GET /api/develope/analyze-stream (SSE)
    │
    ├─ Yield: "Building product summary..."
    │   └─> build_final_summary() from conversation history
    │
    ├─ Yield: Progress updates
    │   └─> match_norms_streaming() [Parallel LLM calls]
    │       └─> For each norm in norms.json:
    │           ├─ call_openrouter() [LLM]
    │           │   └─> "Does EN 62368-1 apply?"
    │           ├─ Yield progress: (completed/total)
    │           └─> Collect results
    │
    └─ Yield: "Complete!" + matched_norms

  Step 3d: Post-Analysis Q&A
  ──────────────────────
  POST /api/develope/ask-analysis
    │
    ├─ Input: {"session_id": "...", "question": "Why EN 62368-1?"}
    │
    ├─ answer_analysis_question() [LLM]
    │   └─> Uses matched_norms + all_results as context
    │
    └─> Return: answer + relevant_norms + confidence

Step 4: WORKSPACE PERSISTENCE
──────────────────────────────
  POST /api/workspace/create
    │
    ├─ Convert session to workspace
    ├─ Create workspace_id (UUID)
    ├─ Store in Redis: workspace:{id}
    │   └─> TTL: 30 days
    │
    └─> Return: workspace_id + URL

  GET /workspace/{workspace_id}
    │
    ├─ Load from Redis: workspace:{id}
    ├─ Render workspace.html with data
    └─> Display: product, norms, Q&A interface

  POST /api/workspace/{id}/ask
    │
    ├─ Same Q&A logic as Step 3d
    ├─ Update qa_history in workspace
    └─> Return: answer
```

## Data Flow: Norm Matching Process

```
┌──────────────────────────────────────┐
│ NORM MATCHING DETAILED FLOW           │
└──────────────────────────────────────┘

Input: Product Description
       │
       │ build_final_summary()
       │ (Synthesize from conversation history)
       │
       ▼
Product Summary (Cleaned, structured)
       │
       │ match_norms_streaming()
       │ (ThreadPoolExecutor - parallel processing)
       │
       ├─────────────────────────────────────┐
       │ For each norm in norms.json:        │
       │                                     │
       │ ┌─────────────────────────────────┐ │
       │ │ check_norm_applies():           │ │
       │ │                                 │ │
       │ │ 1. Build LLM prompt:            │ │
       │ │    - Product details            │ │
       │ │    - Norm name & ID             │ │
       │ │    - "Applies to" criteria      │ │
       │ │                                 │ │
       │ │ 2. Call OpenRouter:             │ │
       │ │    model: claude-3.5-sonnet     │ │
       │ │    temp: 0.3 (deterministic)    │ │
       │ │    max_tokens: 200              │ │
       │ │                                 │ │
       │ │ 3. Parse response:              │ │
       │ │    APPLIES: yes/no              │ │
       │ │    CONFIDENCE: 0-100            │ │
       │ │    REASONING: explanation       │ │
       │ │                                 │ │
       │ │ 4. Yield progress event:        │ │
       │ │    ('progress', completed,      │ │
       │ │     total, norm_id)             │ │
       │ └─────────────────────────────────┘ │
       │                                     │
       │ (10 worker threads max)             │
       └─────────────────────────────────────┘
       │
       │ All results collected
       │
       ▼
Output: List of matched norms
        - norm_id, norm_name
        - applies (bool)
        - confidence (0-100)
        - reasoning (str)
```

## Authentication & Security Current State

```
┌──────────────────────────────────────────────┐
│ CURRENT SECURITY MODEL (No Authentication)   │
└──────────────────────────────────────────────┘

LEVEL 1: PUBLIC ENDPOINTS
─────────────────────────
  ✓ GET /              (Landing page)
  ✓ GET /privacy       (Public info)
  ✓ GET /terms         (Public info)
  ✓ GET /contact       (Contact page)
  ✓ POST /api/run      (Compliance check)
  ✓ GET /api/metrics   (Public stats)
  ✓ POST /api/visitor-count

LEVEL 2: EPHEMERAL SESSION ENDPOINTS (Session ID only)
────────────────────────────────────────────────────────
  ✓ POST /api/develope/start              [Returns session_id]
  ✓ POST /api/develope/respond            [Requires session_id in JSON]
  ✓ POST /api/develope/analyze            [Requires session_id in JSON]
  ✓ GET /api/develope/analyze-stream      [Requires session_id in query]
  ✓ POST /api/develope/ask-analysis       [Requires session_id in JSON]
  ✓ GET /api/develope/session/{id}        [No authentication]

  SECURITY: session_id = UUID (guessable)
           Expires when server restarts
           No user tied to session

LEVEL 3: PERSISTENT WORKSPACE ENDPOINTS (UUID only)
──────────────────────────────────────────────────
  ✓ GET /workspace/{id}              [No authentication]
  ✓ GET /api/workspace/{id}/data     [No authentication]
  ✓ POST /api/workspace/{id}/ask     [No authentication]
  ✓ DELETE /api/workspace/{id}/delete [No authentication]
  ✓ POST /api/workspace/create       [No authentication]

  SECURITY: workspace_id = UUID (guessable)
           No user tied to workspace
           Any UUID can access any workspace

LEVEL 4: FILE-BASED STORAGE
───────────────────────────
  ✓ POST /api/feedback/submit     [No authentication]
  ✓ Feedback saved to feedback.jsonl

  SECURITY: No user tracking
           Name & email optional
           No rate limiting

RECOMMENDATION FOR FUTURE:
─────────────────────────
Add middleware:
  1. User authentication (JWT or Session-based)
  2. Workspace ownership validation
  3. Rate limiting on /api/run, /api/develope/*
  4. User-scoped workspace storage
  5. API key for programmatic access
```

## Deployment Architecture

```
┌────────────────────────────────────────┐
│ DEPLOYMENT: Fly.io (normscout app)     │
└────────────────────────────────────────┘

┌─────────────────────────────┐
│ GitHub Repository           │
│ (Hausertimo.github.io)      │
└──────────────┬──────────────┘
               │
               │ Push
               │
┌──────────────▼──────────────┐
│ Fly.io (Frankfurt Region)   │
│                             │
│ ┌───────────────────────┐   │
│ │ Docker Container      │   │
│ │ (Python 3.11-slim)    │   │
│ │                       │   │
│ │ ┌─────────────────┐   │   │
│ │ │ Gunicorn Server │   │   │
│ │ │ Port: 8080      │   │   │
│ │ │ Workers: 1      │   │   │
│ │ │ Timeout: 180s   │   │   │
│ │ └────────┬────────┘   │   │
│ │          │            │   │
│ │ ┌────────▼────────┐   │   │
│ │ │ Flask App       │   │   │
│ │ └────────┬────────┘   │   │
│ │          │            │   │
│ │ ┌────────▼────────┐   │   │
│ │ │ Redis Client    │   │   │
│ │ │ (REDIS_URL env) │   │   │
│ │ └─────────────────┘   │   │
│ └───────────────────────┘   │
│                             │
│ ┌───────────────────────┐   │
│ │ Persistent Volumes:   │   │
│ │ - feedback/           │   │
│ │ - data/norms.json     │   │
│ └───────────────────────┘   │
│                             │
│ Auto-scaling:              │
│ ├─ Min machines: 0         │
│ ├─ Auto start: true        │
│ ├─ Auto stop: true         │
│ └─ Memory: 1GB per machine │
└─────────────────────────────┘
       │
       ├─ HTTPS enforced
       ├─ Auto-renewal certs
       └─ Load balanced

┌─────────────────────────────┐
│ External Services           │
│                             │
│ ┌─────────────────────┐     │
│ │ Redis Provider      │     │
│ │ (Third-party SaaS)  │     │
│ │ REDIS_URL env var   │     │
│ └─────────────────────┘     │
│                             │
│ ┌─────────────────────┐     │
│ │ OpenRouter API      │     │
│ │ openrouter env var  │     │
│ │ (LLM proxy)         │     │
│ └─────────────────────┘     │
└─────────────────────────────┘
```

## Key File Locations

```
Application Entry Point:
  /home/user/Hausertimo.github.io/app.py

Routes (API Endpoints):
  /home/user/Hausertimo.github.io/routes/
    ├── main.py            (Static pages)
    ├── analytics.py       (Metrics)
    ├── compliance.py      (Product validation)
    ├── fields.py          (Dynamic forms)
    └── develope.py        (Conversation)

Services (Business Logic):
  /home/user/Hausertimo.github.io/services/
    ├── openrouter.py            (LLM API)
    ├── product_conversation.py  (Conversation AI)
    └── norm_matcher.py          (Norm matching)

Note: Workspace functionality moved to normscout_auth.py (Supabase-based)

Frontend (Static Assets):
  /home/user/Hausertimo.github.io/static/
    ├── index.html        (Landing page)
    ├── develope.html     (Via /develope route - template)
    ├── functions.js      (Main JavaScript - 34.5KB)
    ├── style.css         (Global styles - 29.9KB)
    ├── privacy.html      (Privacy policy)
    ├── terms.html        (Terms)
    ├── contact.html      (Contact page)
    └── img/              (Logos & SVGs)

Templates (Dynamic HTML):
  /home/user/Hausertimo.github.io/templates/
    ├── develope.html
    └── workspace.html

Data:
  /home/user/Hausertimo.github.io/data/
    └── norms.json        (EU standards database)

Configuration:
  /home/user/Hausertimo.github.io/
    ├── Dockerfile        (Container definition)
    ├── fly.toml          (Fly.io config)
    ├── gunicorn.conf.py  (Server config)
    └── requirements.txt  (Python dependencies)

Feedback Storage:
  /home/user/Hausertimo.github.io/feedback/
    └── feedback.jsonl    (User feedback log)

Tests:
  /home/user/Hausertimo.github.io/tests/
    ├── test_api.py
    ├── simple_test.py
    └── reset_counters.py
```
