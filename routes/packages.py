"""
Package Management Blueprint

Handles norm database package rentals, subscriptions, and access control.
Integrates with Stripe for payments and Supabase for data persistence.
"""

import os
import logging
from flask import Blueprint, request, jsonify, render_template, redirect, url_for
from functools import wraps
from typing import Optional, Dict

# Import auth decorator from normscout_auth
from normscout_auth import require_auth, get_current_user_id, get_current_user, supabase

# Import package manager service
from services.package_manager import PackageManager, PACKAGES, PackageError, PackageAccessError

# Import Stripe service
from services.stripe_payment import StripePaymentService

logger = logging.getLogger(__name__)

# Create blueprint
packages_bp = Blueprint('packages', __name__)

# Global service instances (initialized via init function)
package_manager: Optional[PackageManager] = None
stripe_service: Optional[StripePaymentService] = None
redis_client = None


def init_packages_dependencies(redis, stripe_api_key=None):
    """
    Initialize package blueprint dependencies.
    Called from app.py during startup.

    Args:
        redis: Redis client instance
        stripe_api_key: Optional Stripe API key (defaults to env var)
    """
    global package_manager, stripe_service, redis_client

    redis_client = redis
    package_manager = PackageManager(supabase, redis)

    # Initialize Stripe service
    try:
        stripe_service = StripePaymentService(api_key=stripe_api_key)
        logger.info("Package management initialized with Stripe integration")
    except Exception as e:
        logger.warning(f"Stripe service initialization failed: {e}")
        logger.info("Package management initialized without Stripe integration")


# ============================================================================
# UI ROUTES
# ============================================================================

@packages_bp.route('/packages')
@require_auth
def packages_page():
    """
    Package selection page with visual boxes.
    Shows all available packages with pricing and features.
    """
    try:
        user_id = get_current_user_id()

        # Get user's current packages
        active_packages = package_manager.get_user_packages(user_id, status='active')
        trial_packages = package_manager.get_user_packages(user_id, status='trial')

        active_package_types = [pkg['package_type'] for pkg in active_packages]
        trial_package_types = [pkg['package_type'] for pkg in trial_packages]

        # Calculate potential savings
        savings_info = package_manager.calculate_bundle_savings(user_id)

        return render_template(
            'packages.html',
            packages=PACKAGES,
            active_packages=active_package_types,
            trial_packages=trial_package_types,
            savings_info=savings_info,
            user=get_current_user()
        )

    except Exception as e:
        logger.error(f"Error loading packages page: {e}")
        return render_template('error.html', error="Failed to load packages"), 500


@packages_bp.route('/packages/manage')
@require_auth
def manage_packages():
    """
    User's package management dashboard.
    Shows active subscriptions, usage statistics, and billing history.
    """
    try:
        user_id = get_current_user_id()

        # Get user's packages
        active_packages = package_manager.get_user_packages(user_id, status='active')
        trial_packages = package_manager.get_user_packages(user_id, status='trial')
        expired_packages = package_manager.get_user_packages(user_id, status='expired')

        # Enrich package data with configuration
        for pkg_list in [active_packages, trial_packages, expired_packages]:
            for pkg in pkg_list:
                pkg_type = pkg.get('package_type')
                pkg['config'] = PACKAGES.get(pkg_type, {})

        # Get usage statistics
        usage_stats = package_manager.get_usage_stats(user_id, days=30)

        # Get allowed databases
        allowed_databases = package_manager.get_allowed_databases(user_id)

        return render_template(
            'package_manage.html',
            active_packages=active_packages,
            trial_packages=trial_packages,
            expired_packages=expired_packages,
            usage_stats=usage_stats,
            allowed_databases=allowed_databases,
            user=get_current_user()
        )

    except Exception as e:
        logger.error(f"Error loading manage packages page: {e}")
        return render_template('error.html', error="Failed to load package management"), 500


@packages_bp.route('/packages/success')
@require_auth
def purchase_success():
    """
    Success page after Stripe checkout.
    Shows confirmation and next steps.
    """
    session_id = request.args.get('session_id')

    return render_template(
        'package_success.html',
        session_id=session_id,
        user=get_current_user()
    )


# ============================================================================
# API ROUTES - PACKAGE INFO
# ============================================================================

@packages_bp.route('/api/packages/list', methods=['GET'])
def list_packages():
    """
    Get list of all available packages.
    Public endpoint (no auth required).
    """
    return jsonify({
        'success': True,
        'packages': PACKAGES
    })


@packages_bp.route('/api/packages/<package_type>', methods=['GET'])
def get_package_details(package_type: str):
    """
    Get details for a specific package.
    Public endpoint (no auth required).
    """
    pkg = PACKAGES.get(package_type)

    if not pkg:
        return jsonify({
            'success': False,
            'error': 'Package not found'
        }), 404

    return jsonify({
        'success': True,
        'package': pkg
    })


@packages_bp.route('/api/packages/<package_type>/preview', methods=['GET'])
def preview_package(package_type: str):
    """
    Get sample norms from a package for preview.
    Shows first 10 norms from each database.
    """
    pkg = PACKAGES.get(package_type)

    if not pkg:
        return jsonify({
            'success': False,
            'error': 'Package not found'
        }), 404

    try:
        from services.norm_matcher import load_norms

        # Load sample norms
        databases = pkg['databases']
        if databases == 'all':
            from services.package_manager import ALL_DATABASE_FILES
            databases = ALL_DATABASE_FILES[:3]  # Sample from first 3 databases

        all_norms = load_norms(databases)

        # Get first 10 norms
        sample_norms = all_norms[:10]

        return jsonify({
            'success': True,
            'package': pkg,
            'sample_norms': sample_norms,
            'total_norms': len(all_norms)
        })

    except Exception as e:
        logger.error(f"Error previewing package: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================================
# API ROUTES - USER PACKAGES
# ============================================================================

@packages_bp.route('/api/packages/my-packages', methods=['GET'])
@require_auth
def get_my_packages():
    """
    Get current user's active packages.
    """
    try:
        user_id = get_current_user_id()

        active = package_manager.get_user_packages(user_id, status='active')
        trial = package_manager.get_user_packages(user_id, status='trial')

        # Enrich with package config
        for pkg_list in [active, trial]:
            for pkg in pkg_list:
                pkg['config'] = PACKAGES.get(pkg['package_type'], {})

        return jsonify({
            'success': True,
            'active_packages': active,
            'trial_packages': trial
        })

    except Exception as e:
        logger.error(f"Error getting user packages: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@packages_bp.route('/api/packages/allowed-databases', methods=['GET'])
@require_auth
def get_allowed_databases():
    """
    Get list of database files the user has access to.
    Used by /develope route to determine which norms to check.
    """
    try:
        user_id = get_current_user_id()
        databases = package_manager.get_allowed_databases(user_id)

        return jsonify({
            'success': True,
            'databases': databases,
            'count': len(databases)
        })

    except Exception as e:
        logger.error(f"Error getting allowed databases: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@packages_bp.route('/api/packages/usage', methods=['GET'])
@require_auth
def get_usage_stats():
    """
    Get usage statistics for current user.
    """
    try:
        user_id = get_current_user_id()
        days = request.args.get('days', 30, type=int)

        stats = package_manager.get_usage_stats(user_id, days=days)

        return jsonify({
            'success': True,
            'stats': stats,
            'period_days': days
        })

    except Exception as e:
        logger.error(f"Error getting usage stats: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================================
# API ROUTES - PURCHASE & CHECKOUT
# ============================================================================

@packages_bp.route('/api/packages/purchase', methods=['POST'])
@require_auth
def purchase_package():
    """
    Initiate Stripe checkout for a package.
    Creates checkout session and returns URL.
    """
    if not stripe_service:
        return jsonify({
            'success': False,
            'error': 'Payment system not configured'
        }), 503

    try:
        user_id = get_current_user_id()
        user = get_current_user()
        data = request.get_json()

        package_type = data.get('package_type')
        is_trial = data.get('is_trial', False)

        # Validate package
        if package_type not in PACKAGES:
            return jsonify({
                'success': False,
                'error': 'Invalid package type'
            }), 400

        pkg = PACKAGES[package_type]

        # Check if user already has this package
        active = package_manager.get_user_packages(user_id, status='active')
        trial = package_manager.get_user_packages(user_id, status='trial')

        for existing in active + trial:
            if existing.get('package_type') == package_type:
                return jsonify({
                    'success': False,
                    'error': f'You already have an active {pkg["name"]} subscription'
                }), 400

        # Get or create Stripe customer
        customer_id = None

        # Check if user already has Stripe customer ID
        try:
            mapping = supabase.table('user_stripe_mapping').select(
                'stripe_customer_id'
            ).eq('user_id', user_id).execute()

            if mapping.data:
                customer_id = mapping.data[0]['stripe_customer_id']
        except:
            pass

        # Create customer if needed
        if not customer_id:
            import stripe
            customer = stripe.Customer.create(
                email=user.email,
                metadata={
                    'user_id': user_id,
                    'source': 'normscout_packages'
                }
            )
            customer_id = customer.id

            # Store mapping
            try:
                supabase.table('user_stripe_mapping').insert({
                    'user_id': user_id,
                    'stripe_customer_id': customer_id,
                    'customer_email': user.email
                }).execute()
            except Exception as e:
                logger.warning(f"Failed to store customer mapping: {e}")

        # Create checkout session
        import stripe
        base_url = request.host_url.rstrip('/')

        session_params = {
            'customer': customer_id,
            'payment_method_types': ['card'],
            'line_items': [{
                'price_data': {
                    'currency': 'usd',
                    'unit_amount': pkg['price'],
                    'product_data': {
                        'name': pkg['name'],
                        'description': pkg['description'],
                        'images': []  # Add package image URLs if available
                    },
                    'recurring': {'interval': 'month'},
                },
                'quantity': 1,
            }],
            'mode': 'subscription',
            'success_url': f"{base_url}/packages/success?session_id={{CHECKOUT_SESSION_ID}}",
            'cancel_url': f"{base_url}/packages",
            'metadata': {
                'user_id': user_id,
                'package_type': package_type,
                'source': 'normscout_packages'
            }
        }

        # Add trial if requested
        if is_trial:
            trial_days = pkg.get('trial_days', 14)
            session_params['subscription_data'] = {
                'trial_period_days': trial_days,
                'metadata': {
                    'user_id': user_id,
                    'package_type': package_type
                }
            }

        session = stripe.checkout.Session.create(**session_params)

        logger.info(f"Created checkout session {session.id} for user {user_id}, package {package_type}")

        return jsonify({
            'success': True,
            'checkout_url': session.url,
            'session_id': session.id
        })

    except Exception as e:
        logger.error(f"Error creating checkout session: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@packages_bp.route('/api/packages/activate', methods=['POST'])
def activate_package():
    """
    Activate a package after successful payment.
    Called by Stripe webhook handler.
    Internal use only (no @require_auth decorator).
    """
    # This should only be called by the webhook handler
    # We validate using the data provided, not user session

    data = request.get_json()
    user_id = data.get('user_id')
    package_type = data.get('package_type')
    stripe_subscription_id = data.get('stripe_subscription_id')
    stripe_customer_id = data.get('stripe_customer_id')
    is_trial = data.get('is_trial', False)

    if not all([user_id, package_type, stripe_subscription_id, stripe_customer_id]):
        return jsonify({
            'success': False,
            'error': 'Missing required fields'
        }), 400

    try:
        result = package_manager.activate_package(
            user_id=user_id,
            package_type=package_type,
            stripe_subscription_id=stripe_subscription_id,
            stripe_customer_id=stripe_customer_id,
            is_trial=is_trial
        )

        return jsonify({
            'success': True,
            'package': result
        })

    except PackageError as e:
        logger.error(f"Error activating package: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

    except Exception as e:
        logger.error(f"Unexpected error activating package: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


@packages_bp.route('/api/packages/cancel', methods=['POST'])
@require_auth
def cancel_package():
    """
    Cancel a user's package subscription.
    """
    try:
        user_id = get_current_user_id()
        data = request.get_json()

        package_type = data.get('package_type')
        reason = data.get('reason', 'User requested cancellation')

        if not package_type:
            return jsonify({
                'success': False,
                'error': 'Package type required'
            }), 400

        # Get the package record to find Stripe subscription ID
        packages = package_manager.get_user_packages(user_id, status='active')
        package_record = None

        for pkg in packages:
            if pkg.get('package_type') == package_type:
                package_record = pkg
                break

        if not package_record:
            return jsonify({
                'success': False,
                'error': 'No active subscription found for this package'
            }), 404

        # Cancel in Stripe if subscription exists
        stripe_sub_id = package_record.get('stripe_subscription_id')
        if stripe_sub_id and stripe_service:
            try:
                import stripe
                stripe.Subscription.modify(
                    stripe_sub_id,
                    cancel_at_period_end=True
                )
                logger.info(f"Cancelled Stripe subscription {stripe_sub_id}")
            except Exception as e:
                logger.error(f"Error cancelling Stripe subscription: {e}")

        # Deactivate in our system
        success = package_manager.deactivate_package(user_id, package_type, reason)

        if success:
            return jsonify({
                'success': True,
                'message': 'Package cancelled successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to cancel package'
            }), 500

    except Exception as e:
        logger.error(f"Error cancelling package: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================================
# API ROUTES - ADMIN (Optional)
# ============================================================================

@packages_bp.route('/api/packages/admin/stats', methods=['GET'])
@require_auth
def admin_package_stats():
    """
    Get package statistics for admin dashboard.
    TODO: Add admin role check
    """
    try:
        # TODO: Add @require_admin decorator when implemented
        user = get_current_user()

        # For now, just check if user email is admin (temporary)
        # admin_emails = os.getenv('ADMIN_EMAILS', '').split(',')
        # if user.email not in admin_emails:
        #     return jsonify({'success': False, 'error': 'Unauthorized'}), 403

        # Get statistics from Supabase
        stats_result = supabase.rpc('get_package_statistics').execute()

        return jsonify({
            'success': True,
            'statistics': stats_result.data or []
        })

    except Exception as e:
        logger.error(f"Error getting admin stats: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@packages_bp.errorhandler(PackageAccessError)
def handle_access_error(error):
    """Handle package access errors"""
    return jsonify({
        'success': False,
        'error': str(error),
        'error_type': 'access_denied'
    }), 403


@packages_bp.errorhandler(PackageError)
def handle_package_error(error):
    """Handle general package errors"""
    return jsonify({
        'success': False,
        'error': str(error),
        'error_type': 'package_error'
    }), 400
