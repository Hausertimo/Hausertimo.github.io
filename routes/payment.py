"""
Payment Routes Blueprint

This blueprint handles all Stripe payment-related endpoints.
It provides REST API endpoints for creating payments, managing subscriptions,
and handling webhooks.

IMPORTANT: This blueprint is ready for integration but requires:
    1. User authentication system to get user_id and customer_id
    2. Database to store customer_id mapping to user_id
    3. Webhook endpoint configuration in Stripe Dashboard

When integrating with authentication:
    - Replace TODO comments with actual user authentication checks
    - Store stripe_customer_id in your user database
    - Protect endpoints with @login_required decorator
"""

from flask import Blueprint, request, jsonify
import os
import logging
from services.stripe_payment import StripePaymentService

logger = logging.getLogger(__name__)

# Create blueprint
payment_bp = Blueprint('payment', __name__, url_prefix='/api/payment')

# Initialize payment service
payment_service = StripePaymentService()


# ==================== HELPER FUNCTIONS ====================

def get_current_user():
    """
    TODO: Replace this with your actual authentication logic.

    When you implement authentication, this function should:
    1. Check session/JWT token
    2. Return user data including user_id and stripe_customer_id

    Example return:
        {
            'user_id': '12345',
            'email': 'user@example.com',
            'stripe_customer_id': 'cus_xxx'  # If already exists
        }
    """
    # PLACEHOLDER - Replace with actual auth
    # For now, return None to indicate no user is logged in
    return None

    # Example implementation with session:
    # from flask import session
    # if 'user_id' in session:
    #     return {
    #         'user_id': session['user_id'],
    #         'email': session['email'],
    #         'stripe_customer_id': session.get('stripe_customer_id')
    #     }
    # return None


def save_customer_id(user_id: str, stripe_customer_id: str):
    """
    TODO: Save Stripe customer ID to your user database.

    Args:
        user_id: Your internal user ID
        stripe_customer_id: Stripe customer ID to save

    Example implementation:
        db.users.update_one(
            {'user_id': user_id},
            {'$set': {'stripe_customer_id': stripe_customer_id}}
        )
    """
    # PLACEHOLDER - Implement database save
    logger.info(f"TODO: Save customer_id {stripe_customer_id} for user {user_id}")
    pass


def save_subscription(user_id: str, subscription_id: str, subscription_data: dict):
    """
    TODO: Save subscription data to your database.

    Args:
        user_id: Your internal user ID
        subscription_id: Stripe subscription ID
        subscription_data: Subscription details (status, plan, etc.)

    Example implementation:
        db.subscriptions.insert_one({
            'user_id': user_id,
            'subscription_id': subscription_id,
            'status': subscription_data['status'],
            'plan': subscription_data['plan'],
            'created_at': datetime.now()
        })
    """
    # PLACEHOLDER - Implement database save
    logger.info(f"TODO: Save subscription {subscription_id} for user {user_id}")
    pass


def update_subscription_status(subscription_id: str, status: str):
    """
    TODO: Update subscription status in your database.

    Args:
        subscription_id: Stripe subscription ID
        status: New status ('active', 'canceled', etc.)
    """
    # PLACEHOLDER - Implement database update
    logger.info(f"TODO: Update subscription {subscription_id} status to {status}")
    pass


def grant_access(user_id: str, plan: str):
    """
    TODO: Grant user access to paid features.

    Args:
        user_id: Your internal user ID
        plan: Plan name ('pro', 'enterprise', etc.)
    """
    # PLACEHOLDER - Implement access grant
    logger.info(f"TODO: Grant {plan} access to user {user_id}")
    pass


def revoke_access(user_id: str):
    """
    TODO: Revoke user access to paid features.

    Args:
        user_id: Your internal user ID
    """
    # PLACEHOLDER - Implement access revocation
    logger.info(f"TODO: Revoke access for user {user_id}")
    pass


# ==================== STRIPE CHECKOUT (RECOMMENDED) ====================

@payment_bp.route('/create-checkout-session', methods=['POST'])
def create_checkout_session():
    """
    Create a Stripe Checkout session - redirects user to Stripe's hosted payment page.
    This is the RECOMMENDED approach as Stripe handles all payment UI and security.

    Request body:
        {
            "price_id": "price_xxx",  // Stripe price ID from Dashboard
            "mode": "subscription",   // 'subscription' or 'payment' (one-time)
            "plan": "pro"            // Optional: plan name for metadata
        }

    Returns:
        {
            "success": true,
            "checkout_url": "https://checkout.stripe.com/...",
            "session_id": "cs_xxx"
        }

    Frontend usage:
        const response = await fetch('/api/payment/create-checkout-session', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({price_id: 'price_xxx', mode: 'subscription'})
        });
        const {checkout_url} = await response.json();
        window.location.href = checkout_url;  // Redirect to Stripe
    """
    # TODO: Add authentication check
    # user = get_current_user()
    # if not user:
    #     return jsonify({'success': False, 'error': 'Not authenticated'}), 401

    try:
        import stripe
        data = request.get_json()

        price_id = data.get('price_id')
        mode = data.get('mode', 'subscription')  # 'subscription' or 'payment'
        plan = data.get('plan', 'pro')

        if not price_id:
            return jsonify({'success': False, 'error': 'Price ID required'}), 400

        # Get base URL for success/cancel redirects
        # In production, use your actual domain
        base_url = os.getenv('BASE_URL', 'http://localhost:8080')

        # Create Checkout Session
        session_config = {
            'payment_method_types': ['card'],
            'line_items': [{
                'price': price_id,
                'quantity': 1,
            }],
            'mode': mode,
            'success_url': f'{base_url}/payment/success?session_id={{CHECKOUT_SESSION_ID}}',
            'cancel_url': f'{base_url}/payment/cancel',
            'metadata': {
                # TODO: Add user_id when auth is implemented
                # 'user_id': user['user_id'],
                'plan': plan
            }
        }

        # Pre-fill customer email if available
        # TODO: Uncomment when auth is ready
        # if user.get('email'):
        #     session_config['customer_email'] = user['email']

        # If user already has a Stripe customer ID, use it
        # TODO: Uncomment when auth is ready
        # if user.get('stripe_customer_id'):
        #     session_config['customer'] = user['stripe_customer_id']

        session = stripe.checkout.Session.create(**session_config)

        logger.info(f"Created checkout session: {session.id}")

        return jsonify({
            'success': True,
            'checkout_url': session.url,
            'session_id': session.id
        })

    except Exception as e:
        logger.error(f"Error creating checkout session: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@payment_bp.route('/checkout-session/<session_id>', methods=['GET'])
def get_checkout_session(session_id):
    """
    Retrieve checkout session details (useful for success page).

    Returns:
        {
            "success": true,
            "session": {
                "payment_status": "paid",
                "customer_email": "user@example.com",
                "amount_total": 2999,
                ...
            }
        }
    """
    try:
        import stripe
        session = stripe.checkout.Session.retrieve(session_id)

        return jsonify({
            'success': True,
            'session': {
                'id': session.id,
                'payment_status': session.payment_status,
                'customer_email': session.customer_details.email if session.customer_details else None,
                'amount_total': session.amount_total,
                'currency': session.currency,
                'customer': session.customer,
                'subscription': session.subscription,
                'metadata': session.metadata
            }
        })

    except Exception as e:
        logger.error(f"Error retrieving checkout session: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== CUSTOMER ENDPOINTS ====================

@payment_bp.route('/customer/create', methods=['POST'])
def create_customer():
    """
    Create a Stripe customer for the logged-in user.

    Request body:
        {
            "email": "user@example.com",
            "name": "John Doe"  (optional)
        }

    Returns:
        {
            "success": true,
            "customer_id": "cus_xxx"
        }
    """
    # TODO: Add authentication check
    # user = get_current_user()
    # if not user:
    #     return jsonify({'success': False, 'error': 'Not authenticated'}), 401

    try:
        data = request.get_json()
        email = data.get('email')
        name = data.get('name')

        if not email:
            return jsonify({'success': False, 'error': 'Email required'}), 400

        # Create Stripe customer
        result = payment_service.create_customer(
            email=email,
            name=name,
            metadata={
                # TODO: Add user_id when auth is implemented
                # 'user_id': user['user_id']
            }
        )

        if result['success']:
            # TODO: Save customer_id to database
            # save_customer_id(user['user_id'], result['customer_id'])
            pass

        return jsonify(result)

    except Exception as e:
        logger.error(f"Error creating customer: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@payment_bp.route('/customer/info', methods=['GET'])
def get_customer_info():
    """
    Get customer information for the logged-in user.

    Returns:
        {
            "success": true,
            "customer_id": "cus_xxx",
            "email": "user@example.com",
            ...
        }
    """
    # TODO: Add authentication check
    # user = get_current_user()
    # if not user:
    #     return jsonify({'success': False, 'error': 'Not authenticated'}), 401

    # if not user.get('stripe_customer_id'):
    #     return jsonify({'success': False, 'error': 'No customer ID found'}), 404

    try:
        # TODO: Get customer_id from user data
        customer_id = request.args.get('customer_id')  # Temporary for testing

        if not customer_id:
            return jsonify({'success': False, 'error': 'Customer ID required'}), 400

        result = payment_service.get_customer(customer_id)
        return jsonify(result)

    except Exception as e:
        logger.error(f"Error getting customer info: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== PAYMENT INTENT ENDPOINTS ====================

@payment_bp.route('/create-payment-intent', methods=['POST'])
def create_payment_intent():
    """
    Create a payment intent for one-time payment.

    Request body:
        {
            "amount": 2999,  // Amount in cents ($29.99)
            "currency": "usd",
            "description": "NormScout Pro Plan",
            "plan": "pro"  // Optional metadata
        }

    Returns:
        {
            "success": true,
            "client_secret": "pi_xxx_secret_xxx",
            "payment_intent_id": "pi_xxx"
        }

    Frontend should use client_secret with Stripe.js
    """
    # TODO: Add authentication check
    # user = get_current_user()
    # if not user:
    #     return jsonify({'success': False, 'error': 'Not authenticated'}), 401

    try:
        data = request.get_json()

        amount = data.get('amount')
        currency = data.get('currency', 'usd')
        description = data.get('description')
        plan = data.get('plan')

        if not amount:
            return jsonify({'success': False, 'error': 'Amount required'}), 400

        # Create payment intent
        result = payment_service.create_payment_intent(
            amount=amount,
            currency=currency,
            # customer_id=user.get('stripe_customer_id'),  # TODO: Uncomment when auth ready
            # customer_email=user['email'],  # TODO: Uncomment when auth ready
            description=description,
            metadata={
                # TODO: Add user_id when auth is implemented
                # 'user_id': user['user_id'],
                'plan': plan
            }
        )

        return jsonify(result)

    except Exception as e:
        logger.error(f"Error creating payment intent: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@payment_bp.route('/payment-status/<payment_intent_id>', methods=['GET'])
def get_payment_status(payment_intent_id):
    """
    Check the status of a payment intent.

    Returns:
        {
            "success": true,
            "status": "succeeded",
            "amount": 2999,
            ...
        }
    """
    try:
        result = payment_service.get_payment_intent(payment_intent_id)
        return jsonify(result)

    except Exception as e:
        logger.error(f"Error getting payment status: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== SUBSCRIPTION ENDPOINTS ====================

@payment_bp.route('/subscription/create', methods=['POST'])
def create_subscription():
    """
    Create a subscription for the logged-in user.

    Request body:
        {
            "price_id": "price_xxx",  // Stripe price ID (create in Dashboard)
            "trial_days": 14,  // Optional
            "plan": "pro"  // Optional metadata
        }

    Returns:
        {
            "success": true,
            "subscription_id": "sub_xxx",
            "client_secret": "pi_xxx_secret_xxx",
            "status": "active"
        }
    """
    # TODO: Add authentication check
    # user = get_current_user()
    # if not user:
    #     return jsonify({'success': False, 'error': 'Not authenticated'}), 401

    # if not user.get('stripe_customer_id'):
    #     return jsonify({'success': False, 'error': 'Customer not found. Create customer first'}), 400

    try:
        data = request.get_json()

        price_id = data.get('price_id')
        trial_days = data.get('trial_days')
        plan = data.get('plan')

        if not price_id:
            return jsonify({'success': False, 'error': 'Price ID required'}), 400

        # Create subscription
        result = payment_service.create_subscription(
            # customer_id=user['stripe_customer_id'],  # TODO: Uncomment when auth ready
            customer_id=data.get('customer_id'),  # Temporary for testing
            price_id=price_id,
            trial_period_days=trial_days,
            metadata={
                # TODO: Add user_id when auth is implemented
                # 'user_id': user['user_id'],
                'plan': plan
            }
        )

        if result['success']:
            # TODO: Save subscription to database
            # save_subscription(user['user_id'], result['subscription_id'], {
            #     'plan': plan,
            #     'status': result['status']
            # })
            pass

        return jsonify(result)

    except Exception as e:
        logger.error(f"Error creating subscription: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@payment_bp.route('/subscription/cancel', methods=['POST'])
def cancel_subscription():
    """
    Cancel a subscription.

    Request body:
        {
            "subscription_id": "sub_xxx",
            "immediate": false  // true = cancel now, false = cancel at period end
        }

    Returns:
        {
            "success": true,
            "status": "canceled"
        }
    """
    # TODO: Add authentication check
    # user = get_current_user()
    # if not user:
    #     return jsonify({'success': False, 'error': 'Not authenticated'}), 401

    try:
        data = request.get_json()

        subscription_id = data.get('subscription_id')
        immediate = data.get('immediate', False)

        if not subscription_id:
            return jsonify({'success': False, 'error': 'Subscription ID required'}), 400

        # TODO: Verify subscription belongs to user
        # subscription = db.subscriptions.find_one({
        #     'subscription_id': subscription_id,
        #     'user_id': user['user_id']
        # })
        # if not subscription:
        #     return jsonify({'success': False, 'error': 'Subscription not found'}), 404

        result = payment_service.cancel_subscription(
            subscription_id=subscription_id,
            immediate=immediate
        )

        if result['success']:
            # TODO: Update subscription status in database
            # update_subscription_status(subscription_id, 'canceled')
            pass

        return jsonify(result)

    except Exception as e:
        logger.error(f"Error canceling subscription: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@payment_bp.route('/subscription/list', methods=['GET'])
def list_subscriptions():
    """
    List all subscriptions for the logged-in user.

    Returns:
        {
            "success": true,
            "subscriptions": [...]
        }
    """
    # TODO: Add authentication check
    # user = get_current_user()
    # if not user:
    #     return jsonify({'success': False, 'error': 'Not authenticated'}), 401

    try:
        # TODO: Get customer_id from user
        customer_id = request.args.get('customer_id')  # Temporary for testing

        if not customer_id:
            return jsonify({'success': False, 'error': 'Customer ID required'}), 400

        result = payment_service.list_customer_subscriptions(customer_id)
        return jsonify(result)

    except Exception as e:
        logger.error(f"Error listing subscriptions: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== WEBHOOK ENDPOINT ====================

@payment_bp.route('/webhook', methods=['POST'])
def stripe_webhook():
    """
    Handle Stripe webhooks.

    Configure this endpoint in Stripe Dashboard:
    https://dashboard.stripe.com/webhooks

    Webhook URL: https://yourdomain.com/api/payment/webhook

    Important events to enable:
    - payment_intent.succeeded
    - payment_intent.payment_failed
    - customer.subscription.created
    - customer.subscription.updated
    - customer.subscription.deleted
    - invoice.payment_succeeded
    - invoice.payment_failed
    """
    payload = request.data
    signature = request.headers.get('Stripe-Signature')

    # Verify webhook signature
    result = payment_service.verify_webhook_signature(
        payload=payload,
        signature=signature
    )

    if not result['success']:
        logger.error(f"Webhook signature verification failed: {result['error']}")
        return jsonify({'error': result['error']}), 400

    event = result['event']

    # Handle the event
    handling_result = payment_service.handle_webhook_event(event)

    # Process the result based on action
    action = handling_result.get('action')
    metadata = handling_result.get('metadata', {})

    # Handle webhook events and activate/deactivate packages
    if action == 'grant_access':
        # Payment succeeded - grant access
        user_id = metadata.get('user_id')
        plan = metadata.get('plan', 'pro')
        logger.info(f"Payment succeeded - Grant {plan} access to user {user_id}")
        # Note: For one-time payments, consider implementing separate logic

    elif action == 'activate_subscription':
        # Subscription created - activate package
        user_id = metadata.get('user_id')
        package_type = metadata.get('package_type')
        subscription_id = handling_result.get('subscription_id')
        customer_id = handling_result.get('customer_id')

        if user_id and package_type:
            try:
                # Import package manager (lazy import to avoid circular dependency)
                from services.package_manager import PackageManager
                from normscout_auth import supabase

                # Get Redis client if available
                try:
                    from app import redis_client
                except:
                    redis_client = None

                pkg_manager = PackageManager(supabase, redis_client)

                # Check if this is a trial subscription
                is_trial = False
                if 'subscription' in handling_result:
                    sub_data = handling_result['subscription']
                    is_trial = sub_data.get('status') == 'trialing'

                # Activate the package
                pkg_manager.activate_package(
                    user_id=user_id,
                    package_type=package_type,
                    stripe_subscription_id=subscription_id,
                    stripe_customer_id=customer_id,
                    is_trial=is_trial
                )

                logger.info(f"✅ Activated package {package_type} for user {user_id} (subscription: {subscription_id}, trial: {is_trial})")

            except Exception as e:
                logger.error(f"❌ Failed to activate package for user {user_id}: {e}")
                # Don't fail the webhook - Stripe expects 200 response
        else:
            logger.warning(f"Missing user_id or package_type in subscription metadata: {metadata}")

    elif action == 'revoke_subscription_access':
        # Subscription cancelled - deactivate package
        user_id = metadata.get('user_id')
        package_type = metadata.get('package_type')
        subscription_id = handling_result.get('subscription_id')

        if user_id and package_type:
            try:
                from services.package_manager import PackageManager
                from normscout_auth import supabase

                try:
                    from app import redis_client
                except:
                    redis_client = None

                pkg_manager = PackageManager(supabase, redis_client)

                # Deactivate the package
                pkg_manager.deactivate_package(
                    user_id=user_id,
                    package_type=package_type,
                    reason='Subscription cancelled via Stripe'
                )

                logger.info(f"✅ Deactivated package {package_type} for user {user_id} (subscription: {subscription_id})")

            except Exception as e:
                logger.error(f"❌ Failed to deactivate package for user {user_id}: {e}")
        else:
            logger.warning(f"Missing user_id or package_type in cancellation metadata: {metadata}")

    elif action == 'update_subscription_status':
        # Subscription updated - handle status changes
        subscription_id = handling_result.get('subscription_id')
        status = handling_result.get('status')
        user_id = metadata.get('user_id')
        package_type = metadata.get('package_type')

        logger.info(f"Subscription {subscription_id} updated to status: {status}")

        # Handle trial ending -> active conversion
        if status == 'active' and user_id and package_type:
            try:
                from services.package_manager import PackageManager
                from normscout_auth import supabase

                try:
                    from app import redis_client
                except:
                    redis_client = None

                pkg_manager = PackageManager(supabase, redis_client)

                # Update the package status from trial to active
                result = supabase.table('user_packages').update({
                    'status': 'active',
                    'is_trial': False
                }).eq('user_id', user_id).eq('package_type', package_type).eq('status', 'trial').execute()

                if result.data:
                    logger.info(f"✅ Converted trial to active for user {user_id}, package {package_type}")

            except Exception as e:
                logger.error(f"❌ Failed to update package status: {e}")

    return jsonify({'success': True, 'received': True})


# ==================== REFUND ENDPOINT ====================

@payment_bp.route('/refund', methods=['POST'])
def create_refund():
    """
    Create a refund (admin/support use).

    Request body:
        {
            "payment_intent_id": "pi_xxx",
            "amount": 2999,  // Optional - omit for full refund
            "reason": "requested_by_customer"
        }

    Returns:
        {
            "success": true,
            "refund_id": "re_xxx"
        }
    """
    # TODO: Add admin authentication check
    # This should only be accessible to admins/support staff

    try:
        data = request.get_json()

        payment_intent_id = data.get('payment_intent_id')
        amount = data.get('amount')
        reason = data.get('reason', 'requested_by_customer')

        if not payment_intent_id:
            return jsonify({'success': False, 'error': 'Payment intent ID required'}), 400

        result = payment_service.create_refund(
            payment_intent_id=payment_intent_id,
            amount=amount,
            reason=reason
        )

        return jsonify(result)

    except Exception as e:
        logger.error(f"Error creating refund: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== PAYMENT METHODS ENDPOINT ====================

@payment_bp.route('/payment-methods', methods=['GET'])
def list_payment_methods():
    """
    List payment methods for the logged-in user.

    Returns:
        {
            "success": true,
            "payment_methods": [
                {
                    "payment_method_id": "pm_xxx",
                    "card_brand": "visa",
                    "card_last4": "4242",
                    ...
                }
            ]
        }
    """
    # TODO: Add authentication check
    # user = get_current_user()
    # if not user:
    #     return jsonify({'success': False, 'error': 'Not authenticated'}), 401

    try:
        # TODO: Get customer_id from user
        customer_id = request.args.get('customer_id')  # Temporary for testing

        if not customer_id:
            return jsonify({'success': False, 'error': 'Customer ID required'}), 400

        result = payment_service.list_payment_methods(customer_id)
        return jsonify(result)

    except Exception as e:
        logger.error(f"Error listing payment methods: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== CONFIG ENDPOINT ====================

@payment_bp.route('/config', methods=['GET'])
def get_stripe_config():
    """
    Get Stripe publishable key for frontend.

    Returns:
        {
            "publishable_key": "pk_xxx"
        }
    """
    return jsonify({
        'publishable_key': os.getenv('STRIPE_PUBLISHABLE_KEY', '')
    })
