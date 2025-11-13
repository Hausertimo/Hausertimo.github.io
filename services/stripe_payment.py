"""
Stripe Payment Service

This module provides a complete Stripe payment integration for NormScout.
It handles payment intent creation, subscription management, webhooks, and customer management.

Requirements:
    - stripe==7.4.0 (add to requirements.txt)
    - STRIPE_SECRET_KEY in environment variables
    - STRIPE_WEBHOOK_SECRET in environment variables (for webhook verification)
    - STRIPE_PUBLISHABLE_KEY for frontend (not used in this module)

Usage:
    from services.stripe_payment import StripePaymentService

    payment_service = StripePaymentService()

    # Create a one-time payment
    result = payment_service.create_payment_intent(
        amount=2999,  # in cents ($29.99)
        currency='usd',
        customer_email='user@example.com'
    )

    # Create a subscription
    subscription = payment_service.create_subscription(
        customer_id='cus_xxx',
        price_id='price_xxx'
    )
"""

import os
import stripe
import logging
from typing import Dict, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)


class StripePaymentService:
    """
    Comprehensive Stripe payment service for handling all payment operations.

    This service is designed to work independently and can be easily integrated
    once user authentication is implemented.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Stripe with API key.

        Args:
            api_key: Stripe secret key. If None, reads from STRIPE_SECRET_KEY env var
        """
        self.api_key = api_key or os.getenv('STRIPE_SECRET_KEY')
        if not self.api_key:
            logger.warning("STRIPE_SECRET_KEY not set. Payment service will not function.")
        else:
            stripe.api_key = self.api_key
            logger.info("Stripe payment service initialized")

    # ==================== CUSTOMER MANAGEMENT ====================

    def create_customer(
        self,
        email: str,
        name: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """
        Create a new Stripe customer.

        Args:
            email: Customer email address
            name: Customer name (optional)
            metadata: Additional metadata to attach (e.g., user_id from your system)

        Returns:
            Dict containing customer data including customer_id

        Example:
            customer = payment_service.create_customer(
                email='user@example.com',
                name='John Doe',
                metadata={'user_id': '12345', 'plan': 'pro'}
            )
        """
        try:
            customer_data = {
                'email': email,
            }

            if name:
                customer_data['name'] = name

            if metadata:
                customer_data['metadata'] = metadata

            customer = stripe.Customer.create(**customer_data)

            logger.info(f"Created Stripe customer: {customer.id} for {email}")

            return {
                'success': True,
                'customer_id': customer.id,
                'email': customer.email,
                'created': customer.created,
                'metadata': customer.metadata
            }

        except stripe.error.StripeError as e:
            logger.error(f"Error creating customer: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'error_type': type(e).__name__
            }

    def get_customer(self, customer_id: str) -> Dict:
        """
        Retrieve customer information.

        Args:
            customer_id: Stripe customer ID

        Returns:
            Dict containing customer data
        """
        try:
            customer = stripe.Customer.retrieve(customer_id)

            return {
                'success': True,
                'customer_id': customer.id,
                'email': customer.email,
                'name': customer.name,
                'metadata': customer.metadata,
                'created': customer.created
            }

        except stripe.error.StripeError as e:
            logger.error(f"Error retrieving customer: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def update_customer(
        self,
        customer_id: str,
        email: Optional[str] = None,
        name: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """
        Update customer information.

        Args:
            customer_id: Stripe customer ID
            email: New email (optional)
            name: New name (optional)
            metadata: Metadata to update (optional)

        Returns:
            Dict containing updated customer data
        """
        try:
            update_data = {}

            if email:
                update_data['email'] = email
            if name:
                update_data['name'] = name
            if metadata:
                update_data['metadata'] = metadata

            customer = stripe.Customer.modify(customer_id, **update_data)

            logger.info(f"Updated customer: {customer_id}")

            return {
                'success': True,
                'customer_id': customer.id,
                'email': customer.email,
                'name': customer.name
            }

        except stripe.error.StripeError as e:
            logger.error(f"Error updating customer: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    # ==================== ONE-TIME PAYMENTS ====================

    def create_payment_intent(
        self,
        amount: int,
        currency: str = 'usd',
        customer_id: Optional[str] = None,
        customer_email: Optional[str] = None,
        metadata: Optional[Dict] = None,
        description: Optional[str] = None
    ) -> Dict:
        """
        Create a payment intent for one-time payments.

        Args:
            amount: Amount in smallest currency unit (e.g., cents for USD)
            currency: Three-letter ISO currency code (default: 'usd')
            customer_id: Existing Stripe customer ID (optional)
            customer_email: Customer email if no customer_id provided
            metadata: Additional metadata (e.g., order_id, user_id)
            description: Payment description

        Returns:
            Dict containing payment intent data including client_secret for frontend

        Example:
            # For $29.99 payment
            result = payment_service.create_payment_intent(
                amount=2999,
                currency='usd',
                customer_email='user@example.com',
                description='NormScout Pro Plan - Monthly',
                metadata={'plan': 'pro', 'user_id': '12345'}
            )

            # Pass result['client_secret'] to frontend
        """
        try:
            payment_data = {
                'amount': amount,
                'currency': currency,
                'automatic_payment_methods': {
                    'enabled': True,
                },
            }

            if customer_id:
                payment_data['customer'] = customer_id
            elif customer_email:
                payment_data['receipt_email'] = customer_email

            if metadata:
                payment_data['metadata'] = metadata

            if description:
                payment_data['description'] = description

            payment_intent = stripe.PaymentIntent.create(**payment_data)

            logger.info(f"Created payment intent: {payment_intent.id} for amount: {amount} {currency}")

            return {
                'success': True,
                'payment_intent_id': payment_intent.id,
                'client_secret': payment_intent.client_secret,
                'amount': payment_intent.amount,
                'currency': payment_intent.currency,
                'status': payment_intent.status
            }

        except stripe.error.StripeError as e:
            logger.error(f"Error creating payment intent: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'error_type': type(e).__name__
            }

    def confirm_payment_intent(self, payment_intent_id: str) -> Dict:
        """
        Confirm a payment intent (server-side confirmation).

        Args:
            payment_intent_id: Payment intent ID to confirm

        Returns:
            Dict containing payment status
        """
        try:
            payment_intent = stripe.PaymentIntent.confirm(payment_intent_id)

            return {
                'success': True,
                'status': payment_intent.status,
                'payment_intent_id': payment_intent.id
            }

        except stripe.error.StripeError as e:
            logger.error(f"Error confirming payment: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_payment_intent(self, payment_intent_id: str) -> Dict:
        """
        Retrieve payment intent status.

        Args:
            payment_intent_id: Payment intent ID

        Returns:
            Dict containing payment intent data
        """
        try:
            payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)

            return {
                'success': True,
                'payment_intent_id': payment_intent.id,
                'status': payment_intent.status,
                'amount': payment_intent.amount,
                'currency': payment_intent.currency,
                'customer': payment_intent.customer,
                'metadata': payment_intent.metadata
            }

        except stripe.error.StripeError as e:
            logger.error(f"Error retrieving payment intent: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    # ==================== SUBSCRIPTIONS ====================

    def create_subscription(
        self,
        customer_id: str,
        price_id: str,
        trial_period_days: Optional[int] = None,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """
        Create a subscription for a customer.

        Args:
            customer_id: Stripe customer ID
            price_id: Stripe price ID (create prices in Stripe Dashboard)
            trial_period_days: Number of trial days (optional)
            metadata: Additional metadata

        Returns:
            Dict containing subscription data

        Example:
            subscription = payment_service.create_subscription(
                customer_id='cus_xxx',
                price_id='price_xxx',  # Create in Stripe Dashboard
                trial_period_days=14,
                metadata={'plan': 'pro', 'user_id': '12345'}
            )
        """
        try:
            subscription_data = {
                'customer': customer_id,
                'items': [{'price': price_id}],
                'payment_behavior': 'default_incomplete',
                'payment_settings': {
                    'save_default_payment_method': 'on_subscription'
                },
                'expand': ['latest_invoice.payment_intent'],
            }

            if trial_period_days:
                subscription_data['trial_period_days'] = trial_period_days

            if metadata:
                subscription_data['metadata'] = metadata

            subscription = stripe.Subscription.create(**subscription_data)

            logger.info(f"Created subscription: {subscription.id} for customer: {customer_id}")

            # Extract client secret for frontend
            client_secret = None
            if subscription.latest_invoice:
                client_secret = subscription.latest_invoice.payment_intent.client_secret

            return {
                'success': True,
                'subscription_id': subscription.id,
                'status': subscription.status,
                'client_secret': client_secret,
                'current_period_end': subscription.current_period_end,
                'trial_end': subscription.trial_end
            }

        except stripe.error.StripeError as e:
            logger.error(f"Error creating subscription: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def cancel_subscription(
        self,
        subscription_id: str,
        immediate: bool = False
    ) -> Dict:
        """
        Cancel a subscription.

        Args:
            subscription_id: Stripe subscription ID
            immediate: If True, cancel immediately. If False, cancel at period end

        Returns:
            Dict containing cancellation status
        """
        try:
            if immediate:
                subscription = stripe.Subscription.delete(subscription_id)
            else:
                subscription = stripe.Subscription.modify(
                    subscription_id,
                    cancel_at_period_end=True
                )

            logger.info(f"Cancelled subscription: {subscription_id}")

            return {
                'success': True,
                'subscription_id': subscription.id,
                'status': subscription.status,
                'canceled_at': subscription.canceled_at,
                'cancel_at_period_end': subscription.cancel_at_period_end
            }

        except stripe.error.StripeError as e:
            logger.error(f"Error cancelling subscription: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_subscription(self, subscription_id: str) -> Dict:
        """
        Retrieve subscription information.

        Args:
            subscription_id: Stripe subscription ID

        Returns:
            Dict containing subscription data
        """
        try:
            subscription = stripe.Subscription.retrieve(subscription_id)

            return {
                'success': True,
                'subscription_id': subscription.id,
                'status': subscription.status,
                'customer': subscription.customer,
                'current_period_end': subscription.current_period_end,
                'cancel_at_period_end': subscription.cancel_at_period_end,
                'metadata': subscription.metadata
            }

        except stripe.error.StripeError as e:
            logger.error(f"Error retrieving subscription: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def list_customer_subscriptions(self, customer_id: str) -> Dict:
        """
        List all subscriptions for a customer.

        Args:
            customer_id: Stripe customer ID

        Returns:
            Dict containing list of subscriptions
        """
        try:
            subscriptions = stripe.Subscription.list(customer=customer_id)

            subscription_list = []
            for sub in subscriptions.data:
                subscription_list.append({
                    'subscription_id': sub.id,
                    'status': sub.status,
                    'current_period_end': sub.current_period_end,
                    'cancel_at_period_end': sub.cancel_at_period_end
                })

            return {
                'success': True,
                'subscriptions': subscription_list,
                'count': len(subscription_list)
            }

        except stripe.error.StripeError as e:
            logger.error(f"Error listing subscriptions: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    # ==================== WEBHOOK HANDLING ====================

    def verify_webhook_signature(
        self,
        payload: bytes,
        signature: str,
        webhook_secret: Optional[str] = None
    ) -> Dict:
        """
        Verify Stripe webhook signature.

        Args:
            payload: Raw request body (bytes)
            signature: Stripe-Signature header value
            webhook_secret: Webhook secret from Stripe Dashboard

        Returns:
            Dict containing event data if valid, error if invalid

        Example:
            # In your webhook route:
            result = payment_service.verify_webhook_signature(
                payload=request.data,
                signature=request.headers.get('Stripe-Signature'),
                webhook_secret=os.getenv('STRIPE_WEBHOOK_SECRET')
            )

            if result['success']:
                event = result['event']
                # Handle event
        """
        secret = webhook_secret or os.getenv('STRIPE_WEBHOOK_SECRET')

        if not secret:
            logger.error("STRIPE_WEBHOOK_SECRET not configured")
            return {
                'success': False,
                'error': 'Webhook secret not configured'
            }

        try:
            event = stripe.Webhook.construct_event(
                payload, signature, secret
            )

            return {
                'success': True,
                'event': event,
                'event_type': event['type'],
                'event_id': event['id']
            }

        except ValueError as e:
            logger.error(f"Invalid payload: {str(e)}")
            return {
                'success': False,
                'error': 'Invalid payload'
            }

        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Invalid signature: {str(e)}")
            return {
                'success': False,
                'error': 'Invalid signature'
            }

    def handle_webhook_event(self, event: Dict) -> Dict:
        """
        Handle common webhook events.

        Args:
            event: Stripe event object from verify_webhook_signature

        Returns:
            Dict containing handling result and any actions to take

        Common Events:
            - payment_intent.succeeded: One-time payment successful
            - payment_intent.payment_failed: Payment failed
            - customer.subscription.created: New subscription
            - customer.subscription.updated: Subscription updated
            - customer.subscription.deleted: Subscription cancelled
            - invoice.payment_succeeded: Subscription payment successful
            - invoice.payment_failed: Subscription payment failed

        Example:
            result = payment_service.handle_webhook_event(event)

            if result['event_type'] == 'payment_intent.succeeded':
                # Grant access to user
                user_id = result['metadata'].get('user_id')
                # Your logic here
        """
        event_type = event['type']
        event_data = event['data']['object']

        logger.info(f"Processing webhook event: {event_type}")

        result = {
            'success': True,
            'event_type': event_type,
            'event_id': event['id'],
            'metadata': event_data.get('metadata', {})
        }

        # Payment Intent Events
        if event_type == 'payment_intent.succeeded':
            result['action'] = 'grant_access'
            result['payment_intent_id'] = event_data['id']
            result['amount'] = event_data['amount']
            result['customer_id'] = event_data.get('customer')
            logger.info(f"Payment succeeded: {event_data['id']}")

        elif event_type == 'payment_intent.payment_failed':
            result['action'] = 'notify_payment_failed'
            result['payment_intent_id'] = event_data['id']
            result['failure_message'] = event_data.get('last_payment_error', {}).get('message')
            logger.warning(f"Payment failed: {event_data['id']}")

        # Subscription Events
        elif event_type == 'customer.subscription.created':
            result['action'] = 'activate_subscription'
            result['subscription_id'] = event_data['id']
            result['customer_id'] = event_data['customer']
            result['status'] = event_data['status']
            logger.info(f"Subscription created: {event_data['id']}")

        elif event_type == 'customer.subscription.updated':
            result['action'] = 'update_subscription_status'
            result['subscription_id'] = event_data['id']
            result['customer_id'] = event_data['customer']
            result['status'] = event_data['status']
            result['cancel_at_period_end'] = event_data['cancel_at_period_end']
            logger.info(f"Subscription updated: {event_data['id']}")

        elif event_type == 'customer.subscription.deleted':
            result['action'] = 'revoke_subscription_access'
            result['subscription_id'] = event_data['id']
            result['customer_id'] = event_data['customer']
            logger.info(f"Subscription deleted: {event_data['id']}")

        # Invoice Events
        elif event_type == 'invoice.payment_succeeded':
            result['action'] = 'confirm_subscription_payment'
            result['invoice_id'] = event_data['id']
            result['customer_id'] = event_data['customer']
            result['subscription_id'] = event_data.get('subscription')
            result['amount_paid'] = event_data['amount_paid']
            logger.info(f"Invoice paid: {event_data['id']}")

        elif event_type == 'invoice.payment_failed':
            result['action'] = 'notify_invoice_failed'
            result['invoice_id'] = event_data['id']
            result['customer_id'] = event_data['customer']
            result['subscription_id'] = event_data.get('subscription')
            logger.warning(f"Invoice payment failed: {event_data['id']}")

        else:
            result['action'] = 'unhandled'
            logger.info(f"Unhandled event type: {event_type}")

        return result

    # ==================== REFUNDS ====================

    def create_refund(
        self,
        payment_intent_id: str,
        amount: Optional[int] = None,
        reason: Optional[str] = None
    ) -> Dict:
        """
        Create a refund for a payment.

        Args:
            payment_intent_id: Payment intent ID to refund
            amount: Amount to refund in cents (None = full refund)
            reason: Reason for refund ('duplicate', 'fraudulent', 'requested_by_customer')

        Returns:
            Dict containing refund data
        """
        try:
            refund_data = {
                'payment_intent': payment_intent_id
            }

            if amount:
                refund_data['amount'] = amount

            if reason:
                refund_data['reason'] = reason

            refund = stripe.Refund.create(**refund_data)

            logger.info(f"Created refund: {refund.id} for payment: {payment_intent_id}")

            return {
                'success': True,
                'refund_id': refund.id,
                'amount': refund.amount,
                'status': refund.status
            }

        except stripe.error.StripeError as e:
            logger.error(f"Error creating refund: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    # ==================== PAYMENT METHODS ====================

    def attach_payment_method(
        self,
        payment_method_id: str,
        customer_id: str
    ) -> Dict:
        """
        Attach a payment method to a customer.

        Args:
            payment_method_id: Payment method ID from frontend
            customer_id: Stripe customer ID

        Returns:
            Dict containing result
        """
        try:
            payment_method = stripe.PaymentMethod.attach(
                payment_method_id,
                customer=customer_id
            )

            logger.info(f"Attached payment method: {payment_method_id} to customer: {customer_id}")

            return {
                'success': True,
                'payment_method_id': payment_method.id,
                'type': payment_method.type
            }

        except stripe.error.StripeError as e:
            logger.error(f"Error attaching payment method: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def list_payment_methods(self, customer_id: str) -> Dict:
        """
        List all payment methods for a customer.

        Args:
            customer_id: Stripe customer ID

        Returns:
            Dict containing list of payment methods
        """
        try:
            payment_methods = stripe.PaymentMethod.list(
                customer=customer_id,
                type='card'
            )

            methods_list = []
            for pm in payment_methods.data:
                methods_list.append({
                    'payment_method_id': pm.id,
                    'type': pm.type,
                    'card_brand': pm.card.brand if pm.card else None,
                    'card_last4': pm.card.last4 if pm.card else None,
                    'exp_month': pm.card.exp_month if pm.card else None,
                    'exp_year': pm.card.exp_year if pm.card else None
                })

            return {
                'success': True,
                'payment_methods': methods_list,
                'count': len(methods_list)
            }

        except stripe.error.StripeError as e:
            logger.error(f"Error listing payment methods: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
