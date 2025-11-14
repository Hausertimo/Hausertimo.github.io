"""
Package Manager Service

Handles all business logic for norm database packages including:
- Package access validation
- Database access control
- Usage tracking
- Subscription management
- Caching layer for performance
"""

import os
import json
import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from threading import Lock
from functools import lru_cache

logger = logging.getLogger(__name__)

# ============================================================================
# PACKAGE DEFINITIONS
# ============================================================================

PACKAGES = {
    'iso_box': {
        'name': 'ISO Standards Box',
        'description': '60+ ISO/IEC international standards',
        'databases': ['norms_iso.json', 'norms_iec.json'],
        'price': 4999,  # $49.99/month in cents
        'stripe_price_id': None,  # Set after creating in Stripe Dashboard
        'norm_count': 60,
        'regions': ['Global'],
        'industries': ['All'],
        'trial_days': 14,
        'features': [
            'ISO 9001, 14001, 27001 coverage',
            'IEC electrical safety standards',
            'Unlimited analyses',
            'PDF exports'
        ],
        'icon': '🌍',
        'color': '#3B82F6'
    },
    'asia_box': {
        'name': 'Asia Standards Box',
        'description': 'China, Japan, India, UAE/GCC regulations',
        'databases': ['norms_china.json', 'norms_japan.json', 'norms_india.json', 'norms_uae_gcc.json'],
        'price': 3999,  # $39.99/month
        'stripe_price_id': None,
        'norm_count': 45,
        'regions': ['China', 'Japan', 'India', 'UAE', 'GCC'],
        'industries': ['All'],
        'trial_days': 14,
        'features': [
            'China GB standards',
            'Japan JIS standards',
            'India BIS standards',
            'GCC region compliance',
            'Unlimited analyses'
        ],
        'icon': '🏯',
        'color': '#EF4444'
    },
    'us_box': {
        'name': 'US Standards Box',
        'description': 'US-specific regulations and standards',
        'databases': ['norms_us.json'],
        'price': 2999,  # $29.99/month
        'stripe_price_id': None,
        'norm_count': 30,
        'regions': ['United States'],
        'industries': ['All'],
        'trial_days': 14,
        'features': [
            'US federal regulations',
            'State-specific requirements',
            'OSHA compliance',
            'FDA guidelines',
            'Unlimited analyses'
        ],
        'icon': '🦅',
        'color': '#10B981'
    },
    'industry_automotive': {
        'name': 'Automotive Industry Standards',
        'description': 'IATF 16949, ISO/TS automotive standards',
        'databases': ['norms_industry_automotive.json'],
        'price': 3499,  # $34.99/month
        'stripe_price_id': None,
        'norm_count': 35,
        'regions': ['Global'],
        'industries': ['Automotive'],
        'trial_days': 14,
        'features': [
            'IATF 16949 coverage',
            'Automotive safety standards',
            'Supply chain requirements',
            'Unlimited analyses'
        ],
        'icon': '🚗',
        'color': '#F59E0B'
    },
    'industry_medical': {
        'name': 'Medical Device Standards',
        'description': 'ISO 13485, FDA 21 CFR, MDR compliance',
        'databases': ['norms_industry_medical.json'],
        'price': 3499,  # $34.99/month
        'stripe_price_id': None,
        'norm_count': 40,
        'regions': ['Global'],
        'industries': ['Medical Devices'],
        'trial_days': 14,
        'features': [
            'ISO 13485 coverage',
            'FDA compliance',
            'EU MDR requirements',
            'Risk management standards',
            'Unlimited analyses'
        ],
        'icon': '⚕️',
        'color': '#8B5CF6'
    },
    'mega_bundle': {
        'name': 'All Access Bundle',
        'description': 'Complete access to all norm databases',
        'databases': 'all',  # Special value for all databases
        'price': 9999,  # $99.99/month
        'stripe_price_id': None,
        'norm_count': 200,
        'regions': ['Global'],
        'industries': ['All'],
        'trial_days': 14,
        'features': [
            'Access to ALL databases',
            'All geographic regions',
            'All industry standards',
            'Priority support',
            'Advanced analytics',
            'Unlimited analyses'
        ],
        'icon': '⭐',
        'color': '#EC4899',
        'is_bundle': True
    }
}

# All available database files
ALL_DATABASE_FILES = [
    'norms.json',  # EU base (free)
    'norms_us.json',
    'norms_china.json',
    'norms_japan.json',
    'norms_iso.json',
    'norms_iec.json',
    'norms_uk.json',
    'norms_canada.json',
    'norms_australia.json',
    'norms_brazil.json',
    'norms_india.json',
    'norms_uae_gcc.json',
    'norms_eu_additional.json',
    'norms_industry_automotive.json',
    'norms_industry_medical.json',
    'norms_industry_electronics.json',
    'norms_industry_food.json',
    'norms_industry_construction.json',
    'norms_industry_energy.json'
]

# Free tier database (always accessible)
FREE_DATABASES = ['norms.json']


# ============================================================================
# EXCEPTIONS
# ============================================================================

class PackageError(Exception):
    """Base exception for package-related errors"""
    pass


class PackageAccessError(PackageError):
    """Raised when user doesn't have access to a package"""
    pass


class PackageNotFoundError(PackageError):
    """Raised when package type doesn't exist"""
    pass


class PackageAlreadyActiveError(PackageError):
    """Raised when trying to activate a package that's already active"""
    pass


# ============================================================================
# NORM DATABASE CACHE
# ============================================================================

class NormDatabaseCache:
    """
    Application-level cache for norm database files.
    Prevents repeated filesystem reads.
    """

    def __init__(self):
        self._cache: Dict[str, List[dict]] = {}
        self._lock = Lock()
        self._last_reload: Dict[str, datetime] = {}

    def get_norms(self, database_names: List[str]) -> List[dict]:
        """
        Get norms from multiple databases with caching.

        Args:
            database_names: List of database filenames

        Returns:
            Combined list of norms from all databases
        """
        all_norms = []

        for db_name in database_names:
            if db_name not in self._cache:
                with self._lock:
                    # Double-check locking pattern
                    if db_name not in self._cache:
                        self._cache[db_name] = self._load_from_disk(db_name)
                        self._last_reload[db_name] = datetime.now()

            all_norms.extend(self._cache[db_name])

        return all_norms

    def _load_from_disk(self, database_name: str) -> List[dict]:
        """Load norms from a database file on disk"""
        data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
        db_path = os.path.join(data_dir, database_name)

        if not os.path.exists(db_path):
            logger.warning(f"Database file not found: {database_name}")
            return []

        try:
            with open(db_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                norms = data.get('norms', [])

                # Add source metadata to each norm
                for norm in norms:
                    norm['source_database'] = database_name

                logger.info(f"Loaded {len(norms)} norms from {database_name}")
                return norms

        except Exception as e:
            logger.error(f"Error loading database {database_name}: {e}")
            return []

    def invalidate(self, database_name: Optional[str] = None):
        """Invalidate cache for a specific database or all databases"""
        with self._lock:
            if database_name:
                self._cache.pop(database_name, None)
                logger.info(f"Invalidated cache for {database_name}")
            else:
                self._cache.clear()
                logger.info("Invalidated all database caches")

    def get_stats(self) -> Dict:
        """Get cache statistics"""
        return {
            'cached_databases': len(self._cache),
            'total_norms_cached': sum(len(norms) for norms in self._cache.values()),
            'databases': list(self._cache.keys())
        }


# Global cache instance
_norm_cache = NormDatabaseCache()


# ============================================================================
# PACKAGE MANAGER
# ============================================================================

class PackageManager:
    """
    Main package management service.
    Handles access control, usage tracking, and subscription management.
    """

    def __init__(self, supabase_client, redis_client=None):
        """
        Initialize package manager.

        Args:
            supabase_client: Supabase client instance
            redis_client: Optional Redis client for caching
        """
        self.supabase = supabase_client
        self.redis = redis_client
        self.norm_cache = _norm_cache

    # ------------------------------------------------------------------------
    # PACKAGE ACCESS METHODS
    # ------------------------------------------------------------------------

    def get_user_packages(self, user_id: str, status: str = 'active') -> List[Dict]:
        """
        Get user's packages with Redis caching.

        Args:
            user_id: User's UUID
            status: Package status filter ('active', 'trial', 'expired', etc.)

        Returns:
            List of package records
        """
        # Try cache first if Redis is available
        if self.redis:
            cache_key = f"user_packages:{user_id}:{status}"
            try:
                cached = self.redis.get(cache_key)
                if cached:
                    return json.loads(cached)
            except Exception as e:
                logger.warning(f"Redis cache read failed: {e}")

        # Query from Supabase
        try:
            query = self.supabase.table('user_packages').select('*').eq('user_id', user_id)

            if status:
                query = query.eq('status', status)

            result = query.execute()
            packages = result.data or []

            # Cache for 5 minutes
            if self.redis:
                try:
                    self.redis.setex(cache_key, 300, json.dumps(packages))
                except Exception as e:
                    logger.warning(f"Redis cache write failed: {e}")

            return packages

        except Exception as e:
            logger.error(f"Error fetching user packages: {e}")
            return []

    def get_allowed_databases(self, user_id: str) -> List[str]:
        """
        Get list of database filenames user has access to.

        Args:
            user_id: User's UUID

        Returns:
            List of database filenames (e.g., ['norms.json', 'norms_us.json'])
        """
        # Always include free tier
        databases = set(FREE_DATABASES)

        # Get active and trial packages
        active_packages = self.get_user_packages(user_id, status='active')
        trial_packages = self.get_user_packages(user_id, status='trial')
        all_packages = active_packages + trial_packages

        for pkg in all_packages:
            # Check if package is actually accessible (not expired)
            if not self._is_package_accessible(pkg):
                continue

            package_type = pkg.get('package_type')
            pkg_config = PACKAGES.get(package_type)

            if not pkg_config:
                logger.warning(f"Unknown package type: {package_type}")
                continue

            # Mega bundle gets all databases
            if pkg_config['databases'] == 'all':
                return ALL_DATABASE_FILES

            # Add databases from this package
            databases.update(pkg_config['databases'])

        return sorted(list(databases))

    def _is_package_accessible(self, package: Dict) -> bool:
        """
        Check if a package record is currently accessible.

        Args:
            package: Package record from database

        Returns:
            True if accessible, False otherwise
        """
        status = package.get('status')

        # Check active packages
        if status == 'active':
            expires_at = package.get('expires_at')
            if expires_at is None:
                return True
            # Parse ISO timestamp
            try:
                expiry_date = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
                return expiry_date > datetime.now(expiry_date.tzinfo)
            except:
                return True

        # Check trial packages
        if status == 'trial' and package.get('is_trial'):
            trial_end = package.get('trial_end')
            if trial_end:
                try:
                    trial_end_date = datetime.fromisoformat(trial_end.replace('Z', '+00:00'))
                    return trial_end_date > datetime.now(trial_end_date.tzinfo)
                except:
                    pass

        return False

    def has_database_access(self, user_id: str, database_name: str) -> bool:
        """
        Check if user has access to a specific database.

        Args:
            user_id: User's UUID
            database_name: Database filename

        Returns:
            True if user has access, False otherwise
        """
        allowed_databases = self.get_allowed_databases(user_id)
        return database_name in allowed_databases

    def validate_database_access(self, user_id: str, database_names: List[str]) -> Tuple[bool, List[str]]:
        """
        Validate access to multiple databases.

        Args:
            user_id: User's UUID
            database_names: List of database filenames

        Returns:
            Tuple of (has_access, missing_databases)
        """
        allowed = self.get_allowed_databases(user_id)
        missing = [db for db in database_names if db not in allowed]

        return (len(missing) == 0, missing)

    # ------------------------------------------------------------------------
    # PACKAGE ACTIVATION & MANAGEMENT
    # ------------------------------------------------------------------------

    def activate_package(
        self,
        user_id: str,
        package_type: str,
        stripe_subscription_id: str,
        stripe_customer_id: str,
        is_trial: bool = False,
        trial_days: Optional[int] = None
    ) -> Dict:
        """
        Activate a package for a user.

        Args:
            user_id: User's UUID
            package_type: Package type identifier
            stripe_subscription_id: Stripe subscription ID
            stripe_customer_id: Stripe customer ID
            is_trial: Whether this is a trial activation
            trial_days: Number of trial days (defaults to package config)

        Returns:
            Activated package record

        Raises:
            PackageNotFoundError: If package type doesn't exist
            PackageAlreadyActiveError: If user already has this package active
        """
        # Validate package exists
        if package_type not in PACKAGES:
            raise PackageNotFoundError(f"Invalid package type: {package_type}")

        pkg_config = PACKAGES[package_type]

        # Check for existing active package of same type
        existing = self.get_user_packages(user_id, status='active')
        existing_trial = self.get_user_packages(user_id, status='trial')

        for pkg in existing + existing_trial:
            if pkg.get('package_type') == package_type:
                raise PackageAlreadyActiveError(
                    f"User already has active {package_type} package"
                )

        # Prepare package data
        now = datetime.now()

        if is_trial:
            trial_duration = trial_days or pkg_config.get('trial_days', 14)
            trial_end = now + timedelta(days=trial_duration)

            package_data = {
                'user_id': user_id,
                'package_type': package_type,
                'status': 'trial',
                'is_trial': True,
                'trial_start': now.isoformat(),
                'trial_end': trial_end.isoformat(),
                'activated_at': now.isoformat(),
                'stripe_subscription_id': stripe_subscription_id,
                'stripe_customer_id': stripe_customer_id,
                'metadata': {
                    'activation_source': 'stripe_webhook',
                    'package_config': pkg_config
                }
            }
        else:
            # Regular activation
            expires_at = now + timedelta(days=30)  # Monthly subscription

            package_data = {
                'user_id': user_id,
                'package_type': package_type,
                'status': 'active',
                'purchased_at': now.isoformat(),
                'activated_at': now.isoformat(),
                'expires_at': expires_at.isoformat(),
                'stripe_subscription_id': stripe_subscription_id,
                'stripe_customer_id': stripe_customer_id,
                'metadata': {
                    'activation_source': 'stripe_webhook',
                    'package_config': pkg_config
                }
            }

        # Insert into database
        try:
            result = self.supabase.table('user_packages').insert(package_data).execute()

            # Invalidate cache
            if self.redis:
                try:
                    self.redis.delete(f"user_packages:{user_id}:active")
                    self.redis.delete(f"user_packages:{user_id}:trial")
                except:
                    pass

            # Log audit event
            self._log_audit(user_id, 'package_activated', package_type, {
                'is_trial': is_trial,
                'stripe_subscription_id': stripe_subscription_id
            })

            logger.info(f"Activated package {package_type} for user {user_id} (trial={is_trial})")

            return result.data[0] if result.data else package_data

        except Exception as e:
            logger.error(f"Error activating package: {e}")
            raise PackageError(f"Failed to activate package: {e}")

    def deactivate_package(
        self,
        user_id: str,
        package_type: str,
        reason: Optional[str] = None
    ) -> bool:
        """
        Deactivate a user's package.

        Args:
            user_id: User's UUID
            package_type: Package type to deactivate
            reason: Optional cancellation reason

        Returns:
            True if deactivated successfully
        """
        try:
            update_data = {
                'status': 'cancelled',
                'cancelled_at': datetime.now().isoformat()
            }

            if reason:
                update_data['cancellation_reason'] = reason

            result = self.supabase.table('user_packages').update(update_data).eq(
                'user_id', user_id
            ).eq('package_type', package_type).eq('status', 'active').execute()

            # Invalidate cache
            if self.redis:
                try:
                    self.redis.delete(f"user_packages:{user_id}:active")
                except:
                    pass

            # Log audit event
            self._log_audit(user_id, 'package_deactivated', package_type, {
                'reason': reason
            })

            logger.info(f"Deactivated package {package_type} for user {user_id}")

            return True

        except Exception as e:
            logger.error(f"Error deactivating package: {e}")
            return False

    # ------------------------------------------------------------------------
    # USAGE TRACKING
    # ------------------------------------------------------------------------

    def track_usage(
        self,
        user_id: str,
        database_name: str,
        workspace_id: Optional[str] = None,
        operation: str = 'analysis'
    ):
        """
        Track database usage.

        Args:
            user_id: User's UUID
            database_name: Database filename accessed
            workspace_id: Optional workspace ID
            operation: Type of operation ('analysis', 'preview', 'export')
        """
        try:
            # Determine which package this database belongs to
            package_type = self._get_package_for_database(user_id, database_name)

            usage_data = {
                'user_id': user_id,
                'package_type': package_type,
                'database_name': database_name,
                'workspace_id': workspace_id,
                'operation': operation,
                'accessed_at': datetime.now().isoformat()
            }

            self.supabase.table('package_usage').insert(usage_data).execute()

        except Exception as e:
            # Don't fail the main operation if tracking fails
            logger.error(f"Error tracking usage: {e}")

    def _get_package_for_database(self, user_id: str, database_name: str) -> Optional[str]:
        """Determine which package a database belongs to for a user"""
        if database_name in FREE_DATABASES:
            return None

        packages = self.get_user_packages(user_id, status='active')
        packages.extend(self.get_user_packages(user_id, status='trial'))

        for pkg in packages:
            pkg_type = pkg.get('package_type')
            pkg_config = PACKAGES.get(pkg_type)

            if not pkg_config:
                continue

            if pkg_config['databases'] == 'all':
                return pkg_type

            if database_name in pkg_config['databases']:
                return pkg_type

        return None

    def get_usage_stats(self, user_id: str, days: int = 30) -> Dict:
        """Get usage statistics for a user"""
        try:
            since = (datetime.now() - timedelta(days=days)).isoformat()

            result = self.supabase.table('package_usage').select(
                'database_name, operation, accessed_at'
            ).eq('user_id', user_id).gte('accessed_at', since).execute()

            usage_data = result.data or []

            # Aggregate statistics
            stats = {
                'total_accesses': len(usage_data),
                'databases_used': len(set(u['database_name'] for u in usage_data)),
                'by_database': {},
                'by_operation': {}
            }

            for usage in usage_data:
                db = usage['database_name']
                op = usage['operation']

                stats['by_database'][db] = stats['by_database'].get(db, 0) + 1
                stats['by_operation'][op] = stats['by_operation'].get(op, 0) + 1

            return stats

        except Exception as e:
            logger.error(f"Error getting usage stats: {e}")
            return {'total_accesses': 0, 'databases_used': 0}

    # ------------------------------------------------------------------------
    # AUDIT LOGGING
    # ------------------------------------------------------------------------

    def _log_audit(
        self,
        user_id: str,
        action: str,
        package_type: Optional[str] = None,
        metadata: Optional[Dict] = None
    ):
        """Log an audit event"""
        try:
            audit_data = {
                'user_id': user_id,
                'action': action,
                'package_type': package_type,
                'metadata': metadata or {},
                'created_at': datetime.now().isoformat()
            }

            self.supabase.table('package_audit_log').insert(audit_data).execute()

        except Exception as e:
            logger.error(f"Error logging audit event: {e}")

    # ------------------------------------------------------------------------
    # UTILITY METHODS
    # ------------------------------------------------------------------------

    def get_package_info(self, package_type: str) -> Optional[Dict]:
        """Get package configuration"""
        return PACKAGES.get(package_type)

    def get_all_packages(self) -> Dict:
        """Get all available packages"""
        return PACKAGES

    def calculate_bundle_savings(self, user_id: str) -> Dict:
        """Calculate potential savings if user upgrades to mega bundle"""
        active_packages = self.get_user_packages(user_id, status='active')

        current_cost = sum(
            PACKAGES.get(pkg['package_type'], {}).get('price', 0)
            for pkg in active_packages
        )

        mega_cost = PACKAGES['mega_bundle']['price']

        if current_cost > mega_cost:
            savings = current_cost - mega_cost
            return {
                'should_upgrade': True,
                'monthly_savings': savings / 100,
                'current_monthly_cost': current_cost / 100,
                'mega_bundle_cost': mega_cost / 100,
                'message': f"Upgrade to Mega Bundle and save ${savings/100:.2f}/month!"
            }

        return {
            'should_upgrade': False,
            'current_monthly_cost': current_cost / 100
        }


# ============================================================================
# MODULE-LEVEL CONVENIENCE FUNCTIONS
# ============================================================================

def get_norm_cache_stats() -> Dict:
    """Get statistics about the norm database cache"""
    return _norm_cache.get_stats()


def invalidate_norm_cache(database_name: Optional[str] = None):
    """Invalidate the norm database cache"""
    _norm_cache.invalidate(database_name)
