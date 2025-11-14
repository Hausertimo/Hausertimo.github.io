-- ============================================================================
-- DATABASE PACKAGES SYSTEM - SUPABASE SCHEMA
-- ============================================================================
-- This schema creates all necessary tables for the norm database packages
-- rental system with Stripe integration and user tracking.
--
-- To apply: Run this in your Supabase SQL Editor
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. PACKAGES REFERENCE TABLE
-- ----------------------------------------------------------------------------
-- Defines available package types and their metadata
CREATE TABLE IF NOT EXISTS packages (
    package_type TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    databases JSONB NOT NULL,  -- Array of database filenames
    price INTEGER NOT NULL,     -- Price in cents
    stripe_price_id TEXT,       -- Stripe Price ID (set after creating in Stripe)
    norm_count INTEGER,
    regions JSONB,              -- Array of geographic regions
    industries JSONB,           -- Array of industries
    trial_days INTEGER DEFAULT 14,
    features JSONB,             -- Array of feature descriptions
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add trigger for updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER packages_updated_at
    BEFORE UPDATE ON packages
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Insert default package definitions
INSERT INTO packages (package_type, name, description, databases, price, norm_count, regions, industries, features)
VALUES
    ('iso_box', 'ISO Standards Box', '60+ ISO/IEC international standards',
     '["norms_iso.json", "norms_iec.json"]'::jsonb,
     4999, 60,
     '["Global"]'::jsonb,
     '["All"]'::jsonb,
     '["ISO 9001, 14001, 27001 coverage", "IEC electrical safety standards", "Unlimited analyses", "PDF exports"]'::jsonb),

    ('asia_box', 'Asia Standards Box', 'China, Japan, India, UAE/GCC regulations',
     '["norms_china.json", "norms_japan.json", "norms_india.json", "norms_uae_gcc.json"]'::jsonb,
     3999, 45,
     '["China", "Japan", "India", "UAE", "GCC"]'::jsonb,
     '["All"]'::jsonb,
     '["China GB standards", "Japan JIS standards", "India BIS standards", "GCC region compliance", "Unlimited analyses"]'::jsonb),

    ('us_box', 'US Standards Box', 'US-specific regulations and standards',
     '["norms_us.json"]'::jsonb,
     2999, 30,
     '["United States"]'::jsonb,
     '["All"]'::jsonb,
     '["US federal regulations", "State-specific requirements", "OSHA compliance", "FDA guidelines", "Unlimited analyses"]'::jsonb),

    ('industry_automotive', 'Automotive Industry Standards', 'IATF 16949, ISO/TS automotive standards',
     '["norms_industry_automotive.json"]'::jsonb,
     3499, 35,
     '["Global"]'::jsonb,
     '["Automotive"]'::jsonb,
     '["IATF 16949 coverage", "Automotive safety standards", "Supply chain requirements", "Unlimited analyses"]'::jsonb),

    ('industry_medical', 'Medical Device Standards', 'ISO 13485, FDA 21 CFR, MDR compliance',
     '["norms_industry_medical.json"]'::jsonb,
     3499, 40,
     '["Global"]'::jsonb,
     '["Medical Devices"]'::jsonb,
     '["ISO 13485 coverage", "FDA compliance", "EU MDR requirements", "Risk management standards", "Unlimited analyses"]'::jsonb),

    ('mega_bundle', 'All Access Bundle', 'Complete access to all norm databases',
     '"all"'::jsonb,
     9999, 200,
     '["Global"]'::jsonb,
     '["All"]'::jsonb,
     '["Access to ALL databases", "All geographic regions", "All industry standards", "Priority support", "Advanced analytics", "Unlimited analyses"]'::jsonb)
ON CONFLICT (package_type) DO NOTHING;

-- ----------------------------------------------------------------------------
-- 2. USER-STRIPE CUSTOMER MAPPING
-- ----------------------------------------------------------------------------
-- Maps Supabase user IDs to Stripe customer IDs
CREATE TABLE IF NOT EXISTS user_stripe_mapping (
    user_id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    stripe_customer_id TEXT UNIQUE NOT NULL,
    customer_email TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_stripe_customer_id ON user_stripe_mapping(stripe_customer_id);

CREATE TRIGGER user_stripe_mapping_updated_at
    BEFORE UPDATE ON user_stripe_mapping
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ----------------------------------------------------------------------------
-- 3. USER PACKAGES (SUBSCRIPTIONS)
-- ----------------------------------------------------------------------------
-- Tracks which packages each user has purchased
CREATE TABLE IF NOT EXISTS user_packages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
    package_type TEXT REFERENCES packages(package_type) NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('active', 'trial', 'expired', 'cancelled', 'paused')),

    -- Subscription details
    purchased_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    activated_at TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE,

    -- Trial support
    is_trial BOOLEAN DEFAULT FALSE,
    trial_start TIMESTAMP WITH TIME ZONE,
    trial_end TIMESTAMP WITH TIME ZONE,

    -- Stripe integration
    stripe_subscription_id TEXT UNIQUE,
    stripe_customer_id TEXT,
    stripe_price_id TEXT,

    -- Metadata
    metadata JSONB,
    cancellation_reason TEXT,
    cancelled_at TIMESTAMP WITH TIME ZONE,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_user_packages_user_id ON user_packages(user_id);
CREATE INDEX idx_user_packages_status ON user_packages(status);
CREATE INDEX idx_user_packages_stripe_sub ON user_packages(stripe_subscription_id);

-- Optimized index for active package queries
CREATE INDEX idx_user_packages_user_status
ON user_packages(user_id, status)
WHERE status IN ('active', 'trial');

-- Prevent duplicate active packages of same type
CREATE UNIQUE INDEX idx_user_package_active_unique
ON user_packages(user_id, package_type)
WHERE status IN ('active', 'trial');

CREATE TRIGGER user_packages_updated_at
    BEFORE UPDATE ON user_packages
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ----------------------------------------------------------------------------
-- 4. PACKAGE USAGE TRACKING
-- ----------------------------------------------------------------------------
-- Tracks when users access specific norm databases
CREATE TABLE IF NOT EXISTS package_usage (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
    package_type TEXT REFERENCES packages(package_type),
    database_name TEXT NOT NULL,
    workspace_id UUID REFERENCES workspaces(id) ON DELETE SET NULL,
    operation TEXT DEFAULT 'analysis',  -- 'analysis', 'preview', 'export'
    accessed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for analytics queries
CREATE INDEX idx_package_usage_user_id ON package_usage(user_id);
CREATE INDEX idx_package_usage_database ON package_usage(database_name);
CREATE INDEX idx_package_usage_accessed_at ON package_usage(accessed_at);
CREATE INDEX idx_package_usage_workspace ON package_usage(workspace_id);

-- Composite index for user analytics
CREATE INDEX idx_package_usage_user_db_date
ON package_usage(user_id, database_name, accessed_at DESC);

-- ----------------------------------------------------------------------------
-- 5. PACKAGE BILLING EVENTS
-- ----------------------------------------------------------------------------
-- Tracks billing events for transparency and reconciliation
CREATE TABLE IF NOT EXISTS package_billing_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
    event_type TEXT NOT NULL,  -- 'purchase', 'upgrade', 'downgrade', 'cancel', 'renewal', 'refund'
    old_package TEXT REFERENCES packages(package_type),
    new_package TEXT REFERENCES packages(package_type),
    amount_charged INTEGER,  -- Amount in cents
    proration_amount INTEGER,  -- Proration credit/debit in cents
    stripe_invoice_id TEXT,
    stripe_event_id TEXT,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_billing_events_user_id ON package_billing_events(user_id);
CREATE INDEX idx_billing_events_created_at ON package_billing_events(created_at);
CREATE INDEX idx_billing_events_type ON package_billing_events(event_type);

-- ----------------------------------------------------------------------------
-- 6. PACKAGE AUDIT LOG
-- ----------------------------------------------------------------------------
-- Comprehensive audit trail for GDPR compliance and debugging
CREATE TABLE IF NOT EXISTS package_audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    action TEXT NOT NULL,  -- 'activated', 'deactivated', 'upgraded', 'downgraded', 'accessed', 'cancelled'
    package_type TEXT REFERENCES packages(package_type),
    stripe_event_id TEXT,
    ip_address INET,
    user_agent TEXT,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_audit_log_user_id ON package_audit_log(user_id);
CREATE INDEX idx_audit_log_created_at ON package_audit_log(created_at);
CREATE INDEX idx_audit_log_action ON package_audit_log(action);

-- Retention policy: automatically delete audit logs older than 3 years
CREATE OR REPLACE FUNCTION cleanup_old_audit_logs()
RETURNS void AS $$
BEGIN
    DELETE FROM package_audit_log
    WHERE created_at < NOW() - INTERVAL '3 years';
END;
$$ LANGUAGE plpgsql;

-- ----------------------------------------------------------------------------
-- 7. ROW LEVEL SECURITY (RLS) POLICIES
-- ----------------------------------------------------------------------------

-- Enable RLS on all tables
ALTER TABLE packages ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_stripe_mapping ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_packages ENABLE ROW LEVEL SECURITY;
ALTER TABLE package_usage ENABLE ROW LEVEL SECURITY;
ALTER TABLE package_billing_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE package_audit_log ENABLE ROW LEVEL SECURITY;

-- Packages table: readable by all authenticated users
CREATE POLICY "Packages are viewable by authenticated users"
ON packages FOR SELECT
TO authenticated
USING (is_active = true);

-- User-Stripe mapping: users can only see their own mapping
CREATE POLICY "Users can view own stripe mapping"
ON user_stripe_mapping FOR SELECT
TO authenticated
USING (auth.uid() = user_id);

-- User packages: users can only see their own packages
CREATE POLICY "Users can view own packages"
ON user_packages FOR SELECT
TO authenticated
USING (auth.uid() = user_id);

-- Package usage: users can only see their own usage
CREATE POLICY "Users can view own usage"
ON package_usage FOR SELECT
TO authenticated
USING (auth.uid() = user_id);

-- Billing events: users can only see their own billing
CREATE POLICY "Users can view own billing events"
ON package_billing_events FOR SELECT
TO authenticated
USING (auth.uid() = user_id);

-- Audit log: users can only see their own audit trail
CREATE POLICY "Users can view own audit log"
ON package_audit_log FOR SELECT
TO authenticated
USING (auth.uid() = user_id);

-- Service role policies (for backend operations)
-- These allow the service role to insert/update/delete
CREATE POLICY "Service can manage user packages"
ON user_packages FOR ALL
TO service_role
USING (true)
WITH CHECK (true);

CREATE POLICY "Service can manage stripe mapping"
ON user_stripe_mapping FOR ALL
TO service_role
USING (true)
WITH CHECK (true);

CREATE POLICY "Service can insert usage"
ON package_usage FOR INSERT
TO service_role
WITH CHECK (true);

CREATE POLICY "Service can insert billing events"
ON package_billing_events FOR INSERT
TO service_role
WITH CHECK (true);

CREATE POLICY "Service can insert audit logs"
ON package_audit_log FOR INSERT
TO service_role
WITH CHECK (true);

-- ----------------------------------------------------------------------------
-- 8. HELPER FUNCTIONS
-- ----------------------------------------------------------------------------

-- Check if a package is accessible (active or in trial)
CREATE OR REPLACE FUNCTION is_package_accessible(pkg_id UUID)
RETURNS BOOLEAN AS $$
DECLARE
    pkg_record RECORD;
BEGIN
    SELECT * INTO pkg_record FROM user_packages WHERE id = pkg_id;

    IF NOT FOUND THEN
        RETURN FALSE;
    END IF;

    -- Check if active and not expired
    IF pkg_record.status = 'active' AND (
        pkg_record.expires_at IS NULL OR
        pkg_record.expires_at > NOW()
    ) THEN
        RETURN TRUE;
    END IF;

    -- Check if in trial and trial not ended
    IF pkg_record.is_trial = TRUE AND
       pkg_record.status = 'trial' AND
       pkg_record.trial_end > NOW() THEN
        RETURN TRUE;
    END IF;

    RETURN FALSE;
END;
$$ LANGUAGE plpgsql;

-- Get all accessible databases for a user
CREATE OR REPLACE FUNCTION get_user_accessible_databases(p_user_id UUID)
RETURNS TEXT[] AS $$
DECLARE
    databases TEXT[];
    pkg RECORD;
    pkg_config RECORD;
BEGIN
    -- Always include free EU base
    databases := ARRAY['norms.json'];

    -- Get all active/trial packages for user
    FOR pkg IN
        SELECT package_type
        FROM user_packages
        WHERE user_id = p_user_id
        AND status IN ('active', 'trial')
        AND (
            (status = 'active' AND (expires_at IS NULL OR expires_at > NOW()))
            OR (status = 'trial' AND trial_end > NOW())
        )
    LOOP
        -- Get package configuration
        SELECT * INTO pkg_config FROM packages WHERE package_type = pkg.package_type;

        IF pkg_config.databases = '"all"'::jsonb THEN
            -- Mega bundle gets all databases
            RETURN ARRAY[
                'norms.json', 'norms_us.json', 'norms_china.json', 'norms_japan.json',
                'norms_iso.json', 'norms_iec.json', 'norms_uk.json', 'norms_canada.json',
                'norms_australia.json', 'norms_brazil.json', 'norms_india.json',
                'norms_uae_gcc.json', 'norms_eu_additional.json',
                'norms_industry_automotive.json', 'norms_industry_medical.json',
                'norms_industry_electronics.json', 'norms_industry_food.json',
                'norms_industry_construction.json', 'norms_industry_energy.json'
            ];
        ELSE
            -- Add databases from this package
            SELECT array_agg(value::text) INTO databases
            FROM jsonb_array_elements_text(pkg_config.databases);
        END IF;
    END LOOP;

    -- Return unique databases
    RETURN array(SELECT DISTINCT unnest(databases));
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Check if user has access to specific database
CREATE OR REPLACE FUNCTION user_has_database_access(p_user_id UUID, p_database_name TEXT)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN p_database_name = ANY(get_user_accessible_databases(p_user_id));
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Get package statistics for admin dashboard
CREATE OR REPLACE FUNCTION get_package_statistics()
RETURNS TABLE(
    package_type TEXT,
    active_subscriptions BIGINT,
    trial_subscriptions BIGINT,
    total_revenue INTEGER,
    total_usage BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        p.package_type,
        COUNT(*) FILTER (WHERE up.status = 'active') as active_subscriptions,
        COUNT(*) FILTER (WHERE up.status = 'trial') as trial_subscriptions,
        (COUNT(*) FILTER (WHERE up.status = 'active') * p.price)::INTEGER as total_revenue,
        (SELECT COUNT(*) FROM package_usage pu WHERE pu.package_type = p.package_type) as total_usage
    FROM packages p
    LEFT JOIN user_packages up ON p.package_type = up.package_type
    GROUP BY p.package_type, p.price;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ----------------------------------------------------------------------------
-- 9. VIEWS FOR ANALYTICS
-- ----------------------------------------------------------------------------

-- Active subscriptions summary
CREATE OR REPLACE VIEW active_subscriptions_summary AS
SELECT
    u.id as user_id,
    u.email,
    up.package_type,
    p.name as package_name,
    up.status,
    up.activated_at,
    up.expires_at,
    up.is_trial,
    up.trial_end,
    p.price as monthly_price
FROM user_packages up
JOIN auth.users u ON up.user_id = u.id
JOIN packages p ON up.package_type = p.package_type
WHERE up.status IN ('active', 'trial');

-- Usage statistics by database
CREATE OR REPLACE VIEW usage_by_database AS
SELECT
    database_name,
    COUNT(*) as total_accesses,
    COUNT(DISTINCT user_id) as unique_users,
    COUNT(DISTINCT DATE(accessed_at)) as active_days,
    MAX(accessed_at) as last_accessed
FROM package_usage
GROUP BY database_name
ORDER BY total_accesses DESC;

-- User spending summary
CREATE OR REPLACE VIEW user_spending_summary AS
SELECT
    user_id,
    COUNT(DISTINCT package_type) as packages_count,
    SUM(p.price) as total_monthly_cost,
    MIN(purchased_at) as first_purchase,
    MAX(purchased_at) as latest_purchase
FROM user_packages up
JOIN packages p ON up.package_type = p.package_type
WHERE up.status = 'active'
GROUP BY user_id;

-- ----------------------------------------------------------------------------
-- 10. SCHEDULED JOBS (Run via Supabase Edge Functions or cron)
-- ----------------------------------------------------------------------------

-- Auto-expire packages that have passed their expiration date
CREATE OR REPLACE FUNCTION auto_expire_packages()
RETURNS void AS $$
BEGIN
    UPDATE user_packages
    SET status = 'expired',
        updated_at = NOW()
    WHERE status = 'active'
    AND expires_at < NOW()
    AND expires_at IS NOT NULL;

    -- Also expire trials
    UPDATE user_packages
    SET status = 'expired',
        updated_at = NOW()
    WHERE status = 'trial'
    AND trial_end < NOW();
END;
$$ LANGUAGE plpgsql;

-- Clean up old audit logs (3+ years old)
-- Call this monthly via cron job

-- ============================================================================
-- SETUP COMPLETE
-- ============================================================================
--
-- Next steps:
-- 1. Run this SQL in your Supabase SQL Editor
-- 2. Create Stripe Products and Prices for each package
-- 3. Update packages table with stripe_price_id values
-- 4. Set up webhook endpoint in Stripe dashboard
-- 5. Configure environment variables for Stripe
--
-- ============================================================================
