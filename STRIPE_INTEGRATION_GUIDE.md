# Stripe Payment Integration Guide

Complete guide for integrating Stripe payments into NormScout.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Setup Instructions](#setup-instructions)
3. [Integration with Authentication](#integration-with-authentication)
4. [Testing](#testing)
5. [Production Deployment](#production-deployment)
6. [Frontend Integration](#frontend-integration)
7. [Webhook Configuration](#webhook-configuration)
8. [Common Use Cases](#common-use-cases)

---

## Quick Start

The Stripe payment system has been prepared and is ready for integration. Here's what's included:

### Files Created

```
services/
  ├── stripe_payment.py       # Core Stripe service (READY)
  └── payment_config.py        # Pricing plans & configuration (CUSTOMIZE)

routes/
  └── payment.py               # Payment API endpoints (INTEGRATE)

static/
  └── payment_example.html     # Frontend example (REFERENCE)

STRIPE_INTEGRATION_GUIDE.md  # This file
.env.example                  # Environment variables template
```

### Current Status

✅ **Ready to Use**
- Stripe service module with all payment operations
- REST API endpoints for payments and subscriptions
- Webhook handling for automatic updates
- Payment configuration with customizable pricing plans
- Frontend example with Stripe Elements

⚠️ **Needs Integration** (after login system is ready)
- User authentication checks in routes
- Database storage for customer IDs and subscriptions
- Access control based on payment status

---

## Setup Instructions

### 1. Install Stripe

Add to `requirements.txt`:

```txt
stripe==7.4.0
```

Then install:

```bash
pip install -r requirements.txt
```

### 2. Get Stripe API Keys

1. Create account at [stripe.com](https://stripe.com)
2. Get your API keys from [Dashboard → Developers → API keys](https://dashboard.stripe.com/apikeys)
3. For testing, use **Test mode** keys (they start with `pk_test_` and `sk_test_`)

### 3. Set Environment Variables

Create or update your `.env` file:

```env
# Stripe API Keys (TEST MODE - for development)
STRIPE_SECRET_KEY=sk_test_your_test_key_here
STRIPE_PUBLISHABLE_KEY=pk_test_your_test_key_here
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret_here

# For production, use LIVE keys:
# STRIPE_SECRET_KEY=sk_live_your_live_key_here
# STRIPE_PUBLISHABLE_KEY=pk_live_your_live_key_here
```

### 4. Register Payment Blueprint

In `app.py`, add the payment blueprint:

```python
# Import the payment blueprint
from routes.payment import payment_bp

# Register it with Flask
app.register_blueprint(payment_bp)
```

### 5. Create Products in Stripe Dashboard

1. Go to [Stripe Dashboard → Products](https://dashboard.stripe.com/products)
2. Click "Add product"
3. Create your pricing plans:

   **Pro Plan**
   - Name: "NormScout Pro"
   - Description: "Unlimited compliance searches"
   - Pricing: $29.99/month
   - After creating, copy the **Price ID** (starts with `price_`)

   **Enterprise Plan**
   - Name: "NormScout Enterprise"
   - Description: "Everything in Pro + API access"
   - Pricing: $99.99/month
   - Copy the **Price ID**

4. Update `services/payment_config.py` with your Price IDs:

```python
STRIPE_PRICE_IDS = {
    'pro_monthly': 'price_ABC123...', # Your actual price ID
    'enterprise_monthly': 'price_XYZ789...',
}
```

---

## Integration with Authentication

Once you have a login system, integrate payments by following these steps:

### Step 1: Update Database Schema

Add to your User model/table:

```python
# Example with SQLAlchemy
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True)
    # ... existing fields ...

    # Add these fields:
    stripe_customer_id = db.Column(db.String(100))
    current_plan = db.Column(db.String(50), default='free')
    subscription_status = db.Column(db.String(50))  # active, canceled, etc.
    subscription_id = db.Column(db.String(100))
```

### Step 2: Implement Helper Functions

In `routes/payment.py`, replace the TODO placeholders:

```python
def get_current_user():
    """Get the currently logged-in user"""
    from flask import session
    from models import User  # Your user model

    if 'user_id' not in session:
        return None

    user = User.query.get(session['user_id'])
    return {
        'user_id': user.id,
        'email': user.email,
        'stripe_customer_id': user.stripe_customer_id,
        'current_plan': user.current_plan
    }

def save_customer_id(user_id: str, stripe_customer_id: str):
    """Save Stripe customer ID to database"""
    from models import User, db

    user = User.query.get(user_id)
    user.stripe_customer_id = stripe_customer_id
    db.session.commit()

def save_subscription(user_id: str, subscription_id: str, subscription_data: dict):
    """Save subscription to database"""
    from models import User, db

    user = User.query.get(user_id)
    user.subscription_id = subscription_id
    user.current_plan = subscription_data.get('plan', 'pro')
    user.subscription_status = 'active'
    db.session.commit()

def grant_access(user_id: str, plan: str):
    """Grant user access to paid features"""
    from models import User, db

    user = User.query.get(user_id)
    user.current_plan = plan
    user.subscription_status = 'active'
    db.session.commit()

def revoke_access(user_id: str):
    """Revoke user access"""
    from models import User, db

    user = User.query.get(user_id)
    user.current_plan = 'free'
    user.subscription_status = 'canceled'
    db.session.commit()
```

### Step 3: Add Login Required Decorator

Create a decorator to protect payment endpoints:

```python
from functools import wraps
from flask import jsonify

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_current_user()
        if user is None:
            return jsonify({'success': False, 'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function

# Then use it on endpoints:
@payment_bp.route('/create-payment-intent', methods=['POST'])
@login_required
def create_payment_intent():
    user = get_current_user()
    # ... rest of the code
```

### Step 4: Check User Plan Before Features

Add this middleware/decorator to check if user has access:

```python
def requires_plan(minimum_plan='free'):
    """Decorator to check if user has required plan"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user = get_current_user()
            if not user:
                return jsonify({'error': 'Login required'}), 401

            plan_hierarchy = ['free', 'pro', 'enterprise']
            user_plan_level = plan_hierarchy.index(user.get('current_plan', 'free'))
            required_level = plan_hierarchy.index(minimum_plan)

            if user_plan_level < required_level:
                return jsonify({
                    'error': 'Upgrade required',
                    'required_plan': minimum_plan,
                    'current_plan': user.get('current_plan')
                }), 403

            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Usage example:
@app.route('/api/detailed-report')
@requires_plan('pro')
def get_detailed_report():
    # Only accessible to Pro and Enterprise users
    pass
```

---

## Testing

### Test with Stripe Test Cards

Use these test card numbers:

| Card Number         | Scenario                  |
|---------------------|---------------------------|
| 4242 4242 4242 4242 | Successful payment        |
| 4000 0000 0000 9995 | Payment declined          |
| 4000 0025 0000 3155 | Requires authentication   |

**Test Details:**
- Expiry: Any future date (e.g., 12/34)
- CVC: Any 3 digits (e.g., 123)
- ZIP: Any 5 digits (e.g., 12345)

### Test One-Time Payment

```bash
# Create a test payment intent
curl -X POST http://localhost:8080/api/payment/create-payment-intent \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 2999,
    "currency": "usd",
    "description": "Test payment"
  }'
```

### Test Subscription

```bash
# First, get your price_id from Stripe Dashboard

# Create a customer
curl -X POST http://localhost:8080/api/payment/customer/create \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "name": "Test User"
  }'

# Create subscription
curl -X POST http://localhost:8080/api/payment/subscription/create \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "cus_xxx",
    "price_id": "price_xxx"
  }'
```

### Test Webhooks Locally

Use Stripe CLI to test webhooks locally:

```bash
# Install Stripe CLI
# Download from: https://stripe.com/docs/stripe-cli

# Login to Stripe
stripe login

# Forward webhooks to your local server
stripe listen --forward-to localhost:8080/api/payment/webhook

# This will give you a webhook secret starting with whsec_
# Add it to your .env file as STRIPE_WEBHOOK_SECRET

# Test a webhook event
stripe trigger payment_intent.succeeded
```

---

## Production Deployment

### 1. Switch to Live Keys

In production environment variables:

```env
STRIPE_SECRET_KEY=sk_live_your_live_key_here
STRIPE_PUBLISHABLE_KEY=pk_live_your_live_key_here
```

### 2. Configure Live Webhook

1. Go to [Stripe Dashboard → Webhooks](https://dashboard.stripe.com/webhooks)
2. Click "Add endpoint"
3. Endpoint URL: `https://yourdomain.com/api/payment/webhook`
4. Select events to listen to:
   - `payment_intent.succeeded`
   - `payment_intent.payment_failed`
   - `customer.subscription.created`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
   - `invoice.payment_succeeded`
   - `invoice.payment_failed`
5. Copy the webhook signing secret
6. Add to production environment: `STRIPE_WEBHOOK_SECRET=whsec_xxx`

### 3. Test Production Webhooks

```bash
# Send test event to production webhook
stripe trigger payment_intent.succeeded \
  --stripe-account acct_xxx
```

### 4. Enable Stripe Radar (Fraud Prevention)

1. Go to [Stripe Dashboard → Radar](https://dashboard.stripe.com/radar/overview)
2. Enable fraud protection rules
3. Review and adjust fraud threshold settings

### 5. Setup Email Receipts

In [Stripe Dashboard → Settings → Emails](https://dashboard.stripe.com/settings/emails):
- Enable customer email receipts
- Customize email templates
- Set your business name and logo

---

## Frontend Integration

### Basic Payment Form

See `static/payment_example.html` for a complete working example.

Quick setup:

```html
<!-- Load Stripe.js -->
<script src="https://js.stripe.com/v3/"></script>

<script>
// Initialize Stripe
const stripe = Stripe('pk_test_your_publishable_key');

// Create payment intent
async function checkout() {
  const response = await fetch('/api/payment/create-payment-intent', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      amount: 2999,  // $29.99
      currency: 'usd'
    })
  });

  const { client_secret } = await response.json();

  // Redirect to Stripe Checkout
  const { error } = await stripe.confirmCardPayment(client_secret, {
    payment_method: {
      card: cardElement,
      billing_details: { email: userEmail }
    }
  });

  if (error) {
    alert(error.message);
  } else {
    alert('Payment successful!');
  }
}
</script>
```

### Subscription Flow

```javascript
async function subscribe(planName) {
  // Get price ID for plan
  const priceId = planName === 'pro'
    ? 'price_xxx'
    : 'price_yyy';

  // Create subscription
  const response = await fetch('/api/payment/subscription/create', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ price_id: priceId })
  });

  const { client_secret } = await response.json();

  // Confirm payment
  const { error } = await stripe.confirmCardPayment(client_secret);

  if (!error) {
    window.location.href = '/dashboard';  // Redirect to dashboard
  }
}
```

---

## Webhook Configuration

### Event Types and Actions

| Event Type | Action | Your Response |
|------------|--------|---------------|
| `payment_intent.succeeded` | Grant access | Activate user's plan |
| `payment_intent.payment_failed` | Notify user | Send payment failed email |
| `customer.subscription.created` | Activate subscription | Grant plan access |
| `customer.subscription.updated` | Update status | Update user's plan |
| `customer.subscription.deleted` | Revoke access | Downgrade to free |
| `invoice.payment_succeeded` | Confirm payment | Extend subscription |
| `invoice.payment_failed` | Retry payment | Notify user, retry |

### Webhook Security

The webhook endpoint automatically:
- Verifies Stripe signature
- Prevents replay attacks
- Validates event authenticity

### Testing Webhook Locally

```bash
# Terminal 1: Run your Flask app
python app.py

# Terminal 2: Forward webhooks
stripe listen --forward-to localhost:8080/api/payment/webhook

# Terminal 3: Trigger test events
stripe trigger payment_intent.succeeded
stripe trigger customer.subscription.created
stripe trigger invoice.payment_failed
```

---

## Common Use Cases

### Use Case 1: Upgrade User to Pro Plan

```python
from services.stripe_payment import StripePaymentService

payment_service = StripePaymentService()

# Create subscription
result = payment_service.create_subscription(
    customer_id=user.stripe_customer_id,
    price_id='price_pro_monthly',
    metadata={'user_id': user.id, 'plan': 'pro'}
)

if result['success']:
    # Save subscription
    save_subscription(user.id, result['subscription_id'], {'plan': 'pro'})
```

### Use Case 2: One-Time Payment for Report

```python
# Create payment intent
result = payment_service.create_payment_intent(
    amount=999,  # $9.99
    currency='usd',
    customer_id=user.stripe_customer_id,
    description='Single Compliance Report',
    metadata={
        'user_id': user.id,
        'product_id': 'single_report',
        'report_id': report.id
    }
)

# Return client_secret to frontend
return jsonify({'client_secret': result['client_secret']})
```

### Use Case 3: Cancel Subscription

```python
# Cancel at end of billing period
result = payment_service.cancel_subscription(
    subscription_id=user.subscription_id,
    immediate=False  # Wait until period end
)

if result['success']:
    update_subscription_status(user.subscription_id, 'canceling')
```

### Use Case 4: Handle Failed Payment

```python
# In webhook handler
if event_type == 'invoice.payment_failed':
    user_id = metadata.get('user_id')

    # Send email notification
    send_email(
        to=user.email,
        subject='Payment Failed',
        template='payment_failed',
        data={'retry_date': retry_date}
    )

    # Optionally suspend access after 3 failed attempts
    if failed_attempts >= 3:
        revoke_access(user_id)
```

### Use Case 5: Prorate Upgrade/Downgrade

```python
# Stripe automatically handles proration
# When user upgrades mid-cycle, they're credited for unused time

# Upgrade from Pro to Enterprise
result = payment_service.create_subscription(
    customer_id=user.stripe_customer_id,
    price_id='price_enterprise_monthly',
    metadata={'user_id': user.id, 'plan': 'enterprise'}
)

# Stripe will:
# 1. Cancel current Pro subscription
# 2. Credit unused Pro time
# 3. Apply credit to Enterprise subscription
# 4. Charge the difference
```

---

## Troubleshooting

### Common Issues

**Issue**: "No API key provided"
- **Solution**: Check that `STRIPE_SECRET_KEY` is set in environment variables

**Issue**: "Webhook signature verification failed"
- **Solution**: Verify `STRIPE_WEBHOOK_SECRET` matches the secret in Stripe Dashboard

**Issue**: "Customer not found"
- **Solution**: Create customer first using `/api/payment/customer/create`

**Issue**: "Invalid price_id"
- **Solution**: Update `payment_config.py` with actual price IDs from Stripe Dashboard

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Stripe Logs

View all API requests in [Stripe Dashboard → Developers → Logs](https://dashboard.stripe.com/logs)

---

## Next Steps

1. ✅ Install Stripe: `pip install stripe==7.4.0`
2. ✅ Get API keys from Stripe Dashboard
3. ✅ Add environment variables to `.env`
4. ✅ Register payment blueprint in `app.py`
5. ✅ Create products in Stripe Dashboard
6. ✅ Update `payment_config.py` with price IDs
7. ⏳ Implement user authentication
8. ⏳ Integrate helper functions in `routes/payment.py`
9. ⏳ Add frontend payment UI
10. ⏳ Configure webhooks in Stripe Dashboard
11. ⏳ Test end-to-end payment flow
12. ⏳ Deploy to production

---

## Support Resources

- **Stripe Documentation**: https://stripe.com/docs
- **Stripe API Reference**: https://stripe.com/docs/api
- **Stripe Testing**: https://stripe.com/docs/testing
- **Stripe Webhooks**: https://stripe.com/docs/webhooks
- **Stripe CLI**: https://stripe.com/docs/stripe-cli

For questions about this integration, refer to the code comments in:
- `services/stripe_payment.py`
- `routes/payment.py`
- `services/payment_config.py`
