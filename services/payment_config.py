"""
Payment Configuration

This file contains payment plans, pricing, and Stripe product/price configurations.
Update this file to manage your pricing tiers and plans.

After creating products in Stripe Dashboard, update the PRICE_IDS with actual IDs.
"""

# ==================== PRICING PLANS ====================

PRICING_PLANS = {
    'free': {
        'name': 'Free',
        'display_name': 'Free Plan',
        'price': 0,
        'currency': 'usd',
        'interval': None,
        'features': [
            '5 product analyses per month',
            'Basic compliance overview',
            'Single market search',
            'Community support'
        ],
        'limits': {
            'monthly_searches': 5,
            'markets': 1,
            'detailed_reports': False,
            'api_access': False
        }
    },

    'pro': {
        'name': 'Pro',
        'display_name': 'Pro Plan',
        'price': 2999,  # $29.99 in cents
        'currency': 'usd',
        'interval': 'month',
        'stripe_price_id': 'price_xxx',  # TODO: Replace with actual Stripe price ID
        'features': [
            'Unlimited product analyses',
            'Detailed compliance reports',
            'All markets supported',
            'Export to PDF',
            'Priority email support',
            'Regulatory updates'
        ],
        'limits': {
            'monthly_searches': -1,  # -1 = unlimited
            'markets': -1,
            'detailed_reports': True,
            'api_access': False
        }
    },

    'enterprise': {
        'name': 'Enterprise',
        'display_name': 'Enterprise Plan',
        'price': 9999,  # $99.99 in cents
        'currency': 'usd',
        'interval': 'month',
        'stripe_price_id': 'price_yyy',  # TODO: Replace with actual Stripe price ID
        'features': [
            'Everything in Pro',
            'API access',
            'Bulk analysis',
            'Custom integrations',
            'Dedicated account manager',
            'SLA guarantee',
            'White-label options'
        ],
        'limits': {
            'monthly_searches': -1,
            'markets': -1,
            'detailed_reports': True,
            'api_access': True,
            'bulk_analysis': True,
            'white_label': True
        }
    }
}


# ==================== ONE-TIME PRODUCTS ====================

ONE_TIME_PRODUCTS = {
    'single_report': {
        'name': 'Single Detailed Report',
        'display_name': 'One-Time Detailed Report',
        'price': 999,  # $9.99 in cents
        'currency': 'usd',
        'description': 'Get a comprehensive compliance report for a single product',
        'features': [
            'One detailed compliance analysis',
            'PDF export',
            'All markets included',
            'Valid for 30 days'
        ]
    },

    'market_bundle': {
        'name': 'Multi-Market Bundle',
        'display_name': '10 Product Analyses',
        'price': 4999,  # $49.99 in cents
        'currency': 'usd',
        'description': 'Bundle of 10 detailed product analyses',
        'features': [
            '10 detailed compliance analyses',
            'PDF exports included',
            'All markets supported',
            'Valid for 90 days'
        ]
    }
}


# ==================== STRIPE PRICE IDS ====================
# After creating products in Stripe Dashboard, update these IDs

STRIPE_PRICE_IDS = {
    # Monthly subscriptions
    'pro_monthly': 'price_xxx',  # TODO: Replace with actual price ID from Stripe
    'enterprise_monthly': 'price_yyy',  # TODO: Replace with actual price ID from Stripe

    # Annual subscriptions (if you want to offer yearly billing)
    'pro_yearly': 'price_zzz',  # TODO: Create in Stripe and add ID
    'enterprise_yearly': 'price_www',  # TODO: Create in Stripe and add ID

    # One-time products (optional - can also handle via payment intents)
    # 'single_report': 'price_aaa',
    # 'market_bundle': 'price_bbb',
}


# ==================== FEATURE FLAGS ====================

FEATURE_FLAGS = {
    # Enable/disable payment features
    'subscriptions_enabled': True,
    'one_time_payments_enabled': True,
    'trial_period_enabled': True,
    'trial_days': 14,

    # Payment methods
    'credit_card_enabled': True,
    'sepa_debit_enabled': False,  # EU bank transfers
    'ideal_enabled': False,  # Netherlands
    'giropay_enabled': False,  # Germany

    # Billing
    'invoices_enabled': True,
    'proration_enabled': True,  # Prorate when upgrading/downgrading
}


# ==================== HELPER FUNCTIONS ====================

def get_plan(plan_name: str) -> dict:
    """
    Get pricing plan by name.

    Args:
        plan_name: Plan name ('free', 'pro', 'enterprise')

    Returns:
        dict: Plan configuration
    """
    return PRICING_PLANS.get(plan_name)


def get_price_id(plan_name: str, interval: str = 'month') -> str:
    """
    Get Stripe price ID for a plan.

    Args:
        plan_name: Plan name ('pro', 'enterprise')
        interval: Billing interval ('month', 'year')

    Returns:
        str: Stripe price ID or None
    """
    key = f"{plan_name}_{interval}ly"
    return STRIPE_PRICE_IDS.get(key)


def get_plan_limits(plan_name: str) -> dict:
    """
    Get usage limits for a plan.

    Args:
        plan_name: Plan name

    Returns:
        dict: Usage limits
    """
    plan = get_plan(plan_name)
    if plan:
        return plan.get('limits', {})
    return {}


def can_access_feature(plan_name: str, feature: str) -> bool:
    """
    Check if a plan has access to a feature.

    Args:
        plan_name: Plan name
        feature: Feature key from limits

    Returns:
        bool: True if feature is accessible
    """
    limits = get_plan_limits(plan_name)
    return limits.get(feature, False)


def get_all_plans() -> list:
    """
    Get all available pricing plans.

    Returns:
        list: List of all plans
    """
    return list(PRICING_PLANS.values())


def format_price(amount_cents: int, currency: str = 'usd') -> str:
    """
    Format price for display.

    Args:
        amount_cents: Amount in cents
        currency: Currency code

    Returns:
        str: Formatted price (e.g., "$29.99")
    """
    symbols = {
        'usd': '$',
        'eur': '€',
        'gbp': '£',
        'chf': 'CHF '
    }

    amount = amount_cents / 100
    symbol = symbols.get(currency.lower(), currency.upper() + ' ')

    if symbol.endswith(' '):
        return f"{symbol}{amount:.2f}"
    else:
        return f"{symbol}{amount:.2f}"


# ==================== WEBHOOK EVENT MAPPINGS ====================

# Map webhook actions to user permissions
WEBHOOK_ACTION_MAPPING = {
    'grant_access': {
        'action': 'activate_plan',
        'notification': 'payment_success'
    },
    'activate_subscription': {
        'action': 'activate_plan',
        'notification': 'subscription_started'
    },
    'revoke_subscription_access': {
        'action': 'deactivate_plan',
        'notification': 'subscription_ended'
    },
    'notify_payment_failed': {
        'action': 'suspend_access',
        'notification': 'payment_failed'
    },
    'notify_invoice_failed': {
        'action': 'payment_retry',
        'notification': 'invoice_failed'
    }
}


# ==================== USAGE TRACKING ====================

def check_usage_limit(plan_name: str, usage_type: str, current_usage: int) -> dict:
    """
    Check if user has exceeded their plan limits.

    Args:
        plan_name: User's plan name
        usage_type: Type of usage to check ('monthly_searches', etc.)
        current_usage: User's current usage count

    Returns:
        dict: {
            'allowed': bool,
            'limit': int,
            'remaining': int,
            'upgrade_required': bool
        }
    """
    limits = get_plan_limits(plan_name)
    limit = limits.get(usage_type, 0)

    # -1 means unlimited
    if limit == -1:
        return {
            'allowed': True,
            'limit': -1,
            'remaining': -1,
            'upgrade_required': False
        }

    allowed = current_usage < limit
    remaining = max(0, limit - current_usage)

    return {
        'allowed': allowed,
        'limit': limit,
        'remaining': remaining,
        'upgrade_required': not allowed
    }


# ==================== EXPORT FOR FRONTEND ====================

def get_pricing_for_frontend() -> dict:
    """
    Get pricing information formatted for frontend display.

    Returns:
        dict: Pricing data safe to send to frontend
    """
    frontend_plans = []

    for plan_key, plan in PRICING_PLANS.items():
        frontend_plans.append({
            'id': plan_key,
            'name': plan['display_name'],
            'price': plan['price'],
            'price_formatted': format_price(plan['price']) if plan['price'] > 0 else 'Free',
            'interval': plan['interval'],
            'features': plan['features'],
            'is_popular': plan_key == 'pro',  # Mark Pro as most popular
            'cta_text': 'Get Started' if plan_key == 'free' else 'Subscribe Now'
        })

    return {
        'plans': frontend_plans,
        'currency': 'usd',
        'trial_enabled': FEATURE_FLAGS['trial_period_enabled'],
        'trial_days': FEATURE_FLAGS['trial_days']
    }
