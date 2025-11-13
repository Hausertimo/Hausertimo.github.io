# 📊 Universal User Tracking System - Setup Guide

A flexible, privacy-first user tracking system that can be deployed to **any website** with minimal configuration.

---

## 🚀 Quick Start (5 Minutes)

### For NormScout (Current Site)

✅ **Already configured!** The tracking system is fully integrated and ready to use.

- Visit `/analytics` to see your dashboard
- All pages are already tracking user behavior
- Cookie consent banner appears automatically for new visitors

---

## 🔧 Adding to a New Site (Step-by-Step)

### Prerequisites

- Flask application
- Redis instance (for data storage)
- Python 3.7+

### Step 1: Copy Required Files

Copy these files to your new project:

```bash
# Core tracking library (frontend)
cp static/tracking.js <your-project>/static/

# Backend routes
cp routes/tracking.py <your-project>/routes/

# Storage service
cp services/tracking_storage.py <your-project>/services/

# Analytics dashboard (optional but recommended)
cp static/analytics.html <your-project>/static/
```

### Step 2: Install Dependencies

No additional Python packages needed! The system uses only:
- `flask` (already in your project)
- `redis` (already in your project)

### Step 3: Register Tracking Routes

In your `app.py` or main Flask file:

```python
# Import the tracking routes initializer
from routes.tracking import init_tracking_routes

# After creating your Flask app and Redis client
init_tracking_routes(app, redis_client)
```

That's it! The tracking system is now active.

### Step 4: Add Tracking to Your HTML Pages

Add this script tag before `</body>` in your HTML files:

```html
<!-- For static HTML files -->
<script src="/static/tracking.js"></script>

<!-- For Jinja templates -->
<script src="{{ url_for('static', filename='tracking.js') }}"></script>
```

### Step 5: Configure (Optional)

You can customize the tracking behavior by adding a config object **before** loading tracking.js:

```html
<script>
    window.TRACKING_CONFIG = {
        // API endpoint (default: '/api/tracking/event')
        apiEndpoint: '/api/tracking/event',

        // Number of events to batch before sending (default: 10)
        batchSize: 10,

        // Send events every X milliseconds (default: 5000)
        batchInterval: 5000,

        // Enable/disable specific features
        enableScrollTracking: true,
        enableClickTracking: true,
        enableFormTracking: true,
        enableVisibilityTracking: true,

        // Scroll depth thresholds to track (default: [25, 50, 75, 90, 100])
        scrollDepthThresholds: [25, 50, 75, 90, 100],

        // Privacy policy URL (shown in consent banner)
        privacyPolicyUrl: '/privacy',

        // Cookie settings
        cookieName: 'user_tracking_consent',
        cookieExpiry: 365,  // days

        // Enable debug logging (default: false)
        debug: false
    };
</script>
<script src="/static/tracking.js"></script>
```

---

## 🎯 Advanced Features

### Custom Event Tracking

Track custom events from anywhere in your JavaScript:

```javascript
// Track a custom business event
window.UserTracker.track('product_purchased', {
    product_id: '12345',
    price: 99.99,
    category: 'electronics'
});

// Track user milestones
window.UserTracker.track('tutorial_completed', {
    step: 5,
    time_taken: 120  // seconds
});
```

### Enhanced Element Tracking

Add data attributes to automatically track specific elements:

```html
<!-- Track button clicks -->
<button data-track="cta-signup" data-track-label="Hero CTA">
    Sign Up Now
</button>

<!-- Track link clicks -->
<a href="/pricing" data-track="pricing-link">View Pricing</a>

<!-- Track section visibility (fires when 50% visible) -->
<section data-track-section="features">
    <h2>Amazing Features</h2>
</section>
```

### Programmatic Consent Management

Control consent from your own UI:

```javascript
// Give analytics consent
window.UserTracker.consent.give(true);

// Revoke consent (deletes session data)
window.UserTracker.consent.revoke();

// Check consent status
const hasConsent = window.UserTracker.consent.hasConsent();

// Get current session ID
const sessionId = window.UserTracker.getSessionId();
```

### Listen to Consent Changes

React to consent changes in your code:

```javascript
window.addEventListener('trackingConsentChanged', (e) => {
    console.log('Consent changed:', e.detail.consent);

    if (e.detail.consent) {
        // User accepted tracking - maybe load additional analytics
        console.log('Loading additional tracking...');
    } else {
        // User rejected - stop any other analytics
        console.log('Stopping all tracking...');
    }
});
```

---

## 📊 Analytics API Endpoints

### Available Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/tracking/event` | POST | Store tracking events (auto-called by tracking.js) |
| `/api/tracking/analytics?days=7` | GET | Get analytics summary |
| `/api/tracking/page-metrics` | GET | Get all page metrics |
| `/api/tracking/page-metrics?page=/index` | GET | Get specific page metrics |
| `/api/tracking/session/<id>` | GET | Get session data |
| `/api/tracking/session/<id>` | DELETE | Delete session (GDPR) |
| `/api/tracking/journey/<id>` | GET | Get user journey |
| `/api/tracking/export/<id>` | GET | Export session data (GDPR) |
| `/api/tracking/health` | GET | Health check |
| `/analytics` | GET | Analytics dashboard page |

### Example: Get Analytics Summary

```javascript
// Fetch last 30 days of analytics
fetch('/api/tracking/analytics?days=30')
    .then(response => response.json())
    .then(data => {
        console.log('Total visitors:', data.visitors.total);
        console.log('Page views:', data.page_views.total);
        console.log('Top pages:', data.top_pages);
    });
```

### Example: Get Page Performance

```javascript
// Get performance for all pages
fetch('/api/tracking/page-metrics')
    .then(response => response.json())
    .then(data => {
        data.pages.forEach(page => {
            console.log(`${page.page}: ${page.views} views, ${page.avg_time}s avg time`);
        });
    });
```

---

## 🔒 Privacy & GDPR Compliance

### Built-in Privacy Features

✅ **Cookie Consent Banner** - Automatically shown to new visitors
✅ **Granular Controls** - Users can choose analytics vs. essential-only
✅ **No PII Collection** - No IP addresses, no fingerprinting
✅ **Anonymous Sessions** - UUID-based session IDs only
✅ **Data Retention** - Automatic cleanup after 30 days
✅ **Right to Deletion** - DELETE endpoint for user data removal
✅ **Data Portability** - Export endpoint for GDPR Article 20

### GDPR Compliance Checklist

- [x] Consent obtained before tracking
- [x] Clear privacy policy disclosure
- [x] Easy consent withdrawal
- [x] Data deletion on request
- [x] Data export on request
- [x] Transparent about data collection
- [x] No third-party data sharing
- [x] Secure data storage (Redis with TTL)

### Update Your Privacy Policy

Add this section to your privacy policy:

```markdown
## Analytics and Cookies

We use first-party cookies and analytics to understand how visitors use our website.
This helps us improve your experience and make our site better.

**What we collect:**
- Pages you visit
- Time spent on each page
- Buttons and links you click
- Scroll depth and engagement
- Device type and screen size
- Referrer (where you came from)

**What we DON'T collect:**
- IP addresses
- Personal information
- Browsing history outside our site
- Any data that identifies you personally

**Your choices:**
You can accept or reject analytics cookies at any time via the cookie banner.
Essential cookies (for site functionality) cannot be disabled.

**Data retention:**
Analytics data is automatically deleted after 30 days.

**Your rights:**
You have the right to:
- Access your data
- Delete your data
- Export your data
- Withdraw consent at any time

To exercise these rights, contact us at [your-email].
```

---

## 🎨 Customizing the Cookie Banner

### Change Colors

The cookie banner uses CSS variables. Override them in your stylesheet:

```css
/* Change banner gradient */
#cookie-consent-banner {
    background: linear-gradient(135deg, #your-color-1 0%, #your-color-2 100%);
}

/* Change button colors */
.cookie-btn-primary {
    background: #your-brand-color;
    color: white;
}
```

### Modify Banner Text

Edit the banner HTML in `tracking.js` (search for "cookie-consent-banner"):

```javascript
this.banner.innerHTML = `
    <div class="cookie-consent-content">
        <div class="cookie-consent-text">
            <span class="cookie-icon">🍪</span>
            <p>Your custom message here!
            <a href="${CONFIG.privacyPolicyUrl}" target="_blank">Learn more</a></p>
        </div>
        ...
    </div>
`;
```

---

## 📈 Viewing Analytics

### Dashboard

Visit `/analytics` on your site to see:
- Total and today's visitor counts
- Page views and engagement
- Top performing pages
- Average time on page
- Engagement rates

### Custom Dashboards

Build your own using the API:

```html
<!DOCTYPE html>
<html>
<head>
    <title>My Custom Analytics</title>
</head>
<body>
    <h1>Site Analytics</h1>
    <div id="stats"></div>

    <script>
        async function loadStats() {
            const response = await fetch('/api/tracking/analytics?days=7');
            const data = await response.json();

            document.getElementById('stats').innerHTML = `
                <p>Visitors: ${data.visitors.total}</p>
                <p>Page Views: ${data.page_views.total}</p>
                <p>Avg Pages/Visitor: ${data.page_views.avg_per_visitor}</p>
            `;
        }

        loadStats();
    </script>
</body>
</html>
```

---

## 🏗️ Multi-Site Deployment

### Using Different Redis Namespaces

To run tracking for multiple sites on the same Redis instance:

```python
# Site 1
from services.tracking_storage import TrackingStorage
storage1 = TrackingStorage(redis_client, key_prefix="site1_tracking")

# Site 2
storage2 = TrackingStorage(redis_client, key_prefix="site2_tracking")

# Pass to init function
init_tracking_routes(app, redis_client)  # Uses default prefix

# Or customize in tracking.py:
storage = TrackingStorage(redis_client, key_prefix="mysite_tracking")
```

### Environment-Based Configuration

```python
import os

# Use environment variable for key prefix
site_name = os.getenv('SITE_NAME', 'default')
storage = TrackingStorage(redis_client, key_prefix=f"{site_name}_tracking")
```

---

## 🐛 Troubleshooting

### Tracking Not Working

1. **Check browser console** - Enable debug mode:
   ```javascript
   window.TRACKING_CONFIG = { debug: true };
   ```

2. **Verify Redis connection** - Visit `/api/tracking/health`

3. **Check consent** - Look for cookie banner or check localStorage

4. **Network tab** - Ensure requests to `/api/tracking/event` succeed

### Cookie Banner Not Appearing

- Check if consent was already given (look for `user_tracking_consent` cookie)
- Clear cookies and reload
- Check browser console for JavaScript errors

### Analytics Dashboard Empty

- Wait for some page views to be tracked
- Check if Redis contains data: `redis-cli KEYS "normscout_tracking:*"`
- Verify tracking.js is loaded on pages

### Data Not Persisting

- Check Redis TTL settings in `tracking_storage.py`
- Verify Redis server isn't flushing data
- Ensure Redis has enough memory

---

## 🎯 What Gets Tracked Automatically

### Zero Configuration Tracking

Without any data attributes or custom code, tracking.js automatically captures:

- ✅ Page views (every page load)
- ✅ Time spent on page
- ✅ Active time (actual engagement, not just tab open)
- ✅ Scroll depth (25%, 50%, 75%, 90%, 100%)
- ✅ Link clicks (all `<a>` tags)
- ✅ Button clicks (all `<button>` tags)
- ✅ Form submissions
- ✅ Page visibility changes (tab switching)
- ✅ Viewport size
- ✅ Referrer
- ✅ User agent
- ✅ Language

### Enhanced Tracking (with data attributes)

Add `data-track` attributes for labeled tracking:

```html
<!-- These get tracked with custom labels -->
<button data-track="signup-button">Sign Up</button>
<a href="/pricing" data-track="pricing-link">Pricing</a>
<section data-track-section="testimonials">...</section>
```

---

## 📝 Example Use Cases

### E-commerce Site

```javascript
// Track product views
window.UserTracker.track('product_viewed', {
    product_id: '12345',
    category: 'electronics',
    price: 299.99
});

// Track add to cart
window.UserTracker.track('add_to_cart', {
    product_id: '12345',
    quantity: 1
});

// Track checkout
window.UserTracker.track('checkout_started', {
    cart_value: 299.99,
    item_count: 1
});
```

### SaaS Application

```javascript
// Track feature usage
window.UserTracker.track('feature_used', {
    feature: 'export_csv',
    user_plan: 'premium'
});

// Track trial sign-ups
window.UserTracker.track('trial_started', {
    plan: 'pro',
    trial_days: 14
});
```

### Content Site

```javascript
// Track article reads
window.UserTracker.track('article_read', {
    article_id: 'how-to-bake-bread',
    category: 'recipes',
    read_percentage: 100
});

// Track newsletter signups
window.UserTracker.track('newsletter_signup', {
    source: 'article_footer'
});
```

---

## 🔐 Security Notes

- **No XSS Risk** - All user input is JSON-encoded
- **No Injection Risk** - Redis commands are parameterized
- **No CSRF Needed** - Tracking endpoint is POST-only, no sensitive actions
- **Rate Limiting** - Consider adding rate limiting in production
- **HTTPS Required** - Always use HTTPS in production

---

## 📦 File Structure

```
your-project/
├── static/
│   ├── tracking.js          # Frontend tracking library
│   └── analytics.html       # Analytics dashboard
├── routes/
│   └── tracking.py          # Flask routes
├── services/
│   └── tracking_storage.py  # Redis storage layer
├── app.py                   # Register tracking routes here
└── TRACKING_SETUP.md        # This file
```

---

## 🎓 Learning More

### Key Files to Understand

1. **tracking.js** - Frontend tracking logic
   - Session management
   - Event queuing and batching
   - Cookie consent handling
   - Automatic event detection

2. **tracking_storage.py** - Backend storage
   - Redis data structures
   - Event storage and retrieval
   - Analytics aggregation
   - GDPR compliance helpers

3. **tracking.py** - Flask API routes
   - Event ingestion endpoint
   - Analytics endpoints
   - Session management endpoints

### Extending the System

Want to add custom features? Here are common extension points:

- **New event types**: Add to tracking.js event handlers
- **New metrics**: Modify `tracking_storage.py` aggregation
- **Custom dashboards**: Use the analytics API to build your own
- **Third-party integration**: Pipe events to external services
- **A/B testing**: Add variant tracking to events

---

## ✅ Deployment Checklist

Before going live:

- [ ] Redis is configured and accessible
- [ ] Tracking routes are registered in Flask
- [ ] tracking.js is loaded on all pages
- [ ] Privacy policy mentions tracking
- [ ] Cookie banner appears for new visitors
- [ ] Analytics dashboard is accessible
- [ ] Health check endpoint responds
- [ ] Test on multiple browsers
- [ ] Test on mobile devices
- [ ] Verify data appears in Redis
- [ ] Set up monitoring/alerts

---

## 🆘 Support

If you encounter issues:

1. Check this guide's troubleshooting section
2. Enable debug mode: `TRACKING_CONFIG = { debug: true }`
3. Check browser console and network tab
4. Verify Redis connection
5. Review Flask logs

---

**That's it! You now have a complete, privacy-first tracking system ready for any website.** 🎉

The system is designed to be:
- **Portable** - Works on any Flask site
- **Flexible** - Easy to customize and extend
- **Privacy-First** - GDPR compliant out of the box
- **Zero-Config** - Works without any setup
- **Production-Ready** - Scalable and performant
