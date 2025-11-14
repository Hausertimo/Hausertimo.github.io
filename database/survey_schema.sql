-- ============================================================================
-- AI SURVEY SYSTEM SCHEMA
-- NormScout Survey Chat Builder
-- ============================================================================

-- Survey Configurations Table
-- Stores all survey configurations created by users
CREATE TABLE IF NOT EXISTS survey_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,

    -- Survey metadata
    name TEXT NOT NULL DEFAULT 'Untitled Survey',
    description TEXT,

    -- AI configuration
    model TEXT NOT NULL DEFAULT 'openai/gpt-4o-mini',
    temperature REAL NOT NULL DEFAULT 0.7,
    character_prompt TEXT NOT NULL DEFAULT 'You are a friendly AI assistant conducting a survey.',
    survey_explanation TEXT,  -- Context for the AI about why gathering this data

    -- Topics configuration (JSONB array)
    -- Format: [{"name": "Name", "mandatory": true, "order": 1}, ...]
    topics JSONB NOT NULL DEFAULT '[]'::jsonb,

    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    is_deleted BOOLEAN DEFAULT FALSE,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_survey_configs_user ON survey_configs(user_id);
CREATE INDEX IF NOT EXISTS idx_survey_configs_active ON survey_configs(is_active) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_survey_configs_deleted ON survey_configs(is_deleted) WHERE is_deleted = FALSE;

-- Survey Conversations Table
-- Stores individual survey chat sessions
CREATE TABLE IF NOT EXISTS survey_conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    survey_id UUID NOT NULL REFERENCES survey_configs(id) ON DELETE CASCADE,

    -- Optional user tracking (can be null for anonymous surveys)
    user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    session_identifier TEXT,  -- Browser fingerprint or custom ID for anonymous users

    -- Conversation data (JSONB for flexibility)
    messages JSONB NOT NULL DEFAULT '[]'::jsonb,  -- Full chat history
    -- Format: [{"role": "user"|"assistant", "content": "...", "timestamp": "..."}, ...]

    -- Topic tracking (JSONB for dynamic topics)
    topic_progress JSONB NOT NULL DEFAULT '{}'::jsonb,
    -- Format: {"Name": {"completed": true, "data": "John Doe", "attempts": 2}, ...}

    -- Survey state
    status TEXT NOT NULL DEFAULT 'in_progress',
    -- Status values: 'in_progress', 'completed', 'abandoned'
    current_topic TEXT,
    current_topic_index INTEGER DEFAULT 0,

    -- Results (structured data extracted from conversation)
    gathered_data JSONB DEFAULT '{}'::jsonb,
    -- Format: {"Name": "John Doe", "Age": "30", "Location": "Zurich", ...}

    -- Progress metrics
    completion_percentage REAL DEFAULT 0.0,
    total_messages INTEGER DEFAULT 0,

    -- Timestamps
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    last_message_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT valid_status CHECK (status IN ('in_progress', 'completed', 'abandoned')),
    CONSTRAINT valid_completion CHECK (completion_percentage >= 0 AND completion_percentage <= 100)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_survey_conversations_survey ON survey_conversations(survey_id);
CREATE INDEX IF NOT EXISTS idx_survey_conversations_user ON survey_conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_survey_conversations_status ON survey_conversations(status);
CREATE INDEX IF NOT EXISTS idx_survey_conversations_updated ON survey_conversations(last_message_at DESC);
CREATE INDEX IF NOT EXISTS idx_survey_conversations_session ON survey_conversations(session_identifier);

-- Survey Analytics Table (optional - for tracking events)
CREATE TABLE IF NOT EXISTS survey_analytics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    survey_id UUID REFERENCES survey_configs(id) ON DELETE CASCADE,
    conversation_id UUID REFERENCES survey_conversations(id) ON DELETE CASCADE,

    event_type TEXT NOT NULL,
    -- Event types: 'survey_started', 'topic_started', 'topic_completed', 'topic_failed', 'survey_completed', 'survey_abandoned'
    topic_name TEXT,

    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_survey_analytics_survey ON survey_analytics(survey_id);
CREATE INDEX IF NOT EXISTS idx_survey_analytics_conversation ON survey_analytics(conversation_id);
CREATE INDEX IF NOT EXISTS idx_survey_analytics_type ON survey_analytics(event_type);
CREATE INDEX IF NOT EXISTS idx_survey_analytics_created ON survey_analytics(created_at DESC);

-- ============================================================================
-- ROW LEVEL SECURITY (RLS) POLICIES
-- ============================================================================

ALTER TABLE survey_configs ENABLE ROW LEVEL SECURITY;
ALTER TABLE survey_conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE survey_analytics ENABLE ROW LEVEL SECURITY;

-- Survey Configs: Users can only manage their own surveys
DROP POLICY IF EXISTS "Users can view own surveys" ON survey_configs;
CREATE POLICY "Users can view own surveys"
ON survey_configs FOR SELECT
TO authenticated
USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can create own surveys" ON survey_configs;
CREATE POLICY "Users can create own surveys"
ON survey_configs FOR INSERT
TO authenticated
WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update own surveys" ON survey_configs;
CREATE POLICY "Users can update own surveys"
ON survey_configs FOR UPDATE
TO authenticated
USING (auth.uid() = user_id)
WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can delete own surveys" ON survey_configs;
CREATE POLICY "Users can delete own surveys"
ON survey_configs FOR DELETE
TO authenticated
USING (auth.uid() = user_id);

-- Survey Conversations: Users can view conversations from their surveys
DROP POLICY IF EXISTS "Users can view survey conversations" ON survey_conversations;
CREATE POLICY "Users can view survey conversations"
ON survey_conversations FOR SELECT
TO authenticated
USING (
    survey_id IN (
        SELECT id FROM survey_configs WHERE user_id = auth.uid()
    )
);

DROP POLICY IF EXISTS "Anyone can create conversations" ON survey_conversations;
CREATE POLICY "Anyone can create conversations"
ON survey_conversations FOR INSERT
TO anon, authenticated
WITH CHECK (true);

DROP POLICY IF EXISTS "Users can update conversations from their surveys" ON survey_conversations;
CREATE POLICY "Users can update conversations from their surveys"
ON survey_conversations FOR UPDATE
TO authenticated
USING (
    survey_id IN (
        SELECT id FROM survey_configs WHERE user_id = auth.uid()
    )
);

-- Survey Analytics: Read-only for survey owners
DROP POLICY IF EXISTS "Users can view analytics" ON survey_analytics;
CREATE POLICY "Users can view analytics"
ON survey_analytics FOR SELECT
TO authenticated
USING (
    survey_id IN (
        SELECT id FROM survey_configs WHERE user_id = auth.uid()
    )
);

DROP POLICY IF EXISTS "System can insert analytics" ON survey_analytics;
CREATE POLICY "System can insert analytics"
ON survey_analytics FOR INSERT
TO anon, authenticated
WITH CHECK (true);

-- ============================================================================
-- TRIGGERS
-- ============================================================================

-- Auto-update updated_at timestamp on survey_configs
CREATE OR REPLACE FUNCTION update_survey_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS survey_configs_updated_at ON survey_configs;
CREATE TRIGGER survey_configs_updated_at
    BEFORE UPDATE ON survey_configs
    FOR EACH ROW
    EXECUTE FUNCTION update_survey_updated_at();

-- Auto-update last_message_at on new messages
CREATE OR REPLACE FUNCTION update_conversation_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.last_message_at = NOW();
    -- Update message count
    NEW.total_messages = jsonb_array_length(NEW.messages);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS conversation_timestamp_update ON survey_conversations;
CREATE TRIGGER conversation_timestamp_update
    BEFORE UPDATE ON survey_conversations
    FOR EACH ROW
    WHEN (OLD.messages IS DISTINCT FROM NEW.messages)
    EXECUTE FUNCTION update_conversation_timestamp();

-- ============================================================================
-- HELPER FUNCTIONS
-- ============================================================================

-- Function to get survey statistics
CREATE OR REPLACE FUNCTION get_survey_stats(survey_uuid UUID)
RETURNS JSON AS $$
DECLARE
    result JSON;
BEGIN
    SELECT json_build_object(
        'total_conversations', COUNT(*),
        'completed_conversations', COUNT(*) FILTER (WHERE status = 'completed'),
        'in_progress_conversations', COUNT(*) FILTER (WHERE status = 'in_progress'),
        'abandoned_conversations', COUNT(*) FILTER (WHERE status = 'abandoned'),
        'avg_completion_percentage', AVG(completion_percentage),
        'avg_messages', AVG(total_messages),
        'total_responses', SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END)
    ) INTO result
    FROM survey_conversations
    WHERE survey_id = survey_uuid;

    RETURN result;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to get all responses for a survey
CREATE OR REPLACE FUNCTION get_survey_responses(survey_uuid UUID)
RETURNS TABLE (
    conversation_id UUID,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    status TEXT,
    gathered_data JSONB,
    total_messages INTEGER,
    completion_percentage REAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        id,
        started_at,
        completed_at,
        status,
        gathered_data,
        total_messages,
        completion_percentage
    FROM survey_conversations
    WHERE survey_id = survey_uuid
    ORDER BY started_at DESC;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ============================================================================
-- INITIAL DATA / EXAMPLES (Optional - comment out for production)
-- ============================================================================

-- Example survey configuration (uncomment to use)
-- INSERT INTO survey_configs (user_id, name, description, model, temperature, character_prompt, survey_explanation, topics)
-- VALUES (
--     '00000000-0000-0000-0000-000000000000',  -- Replace with actual user_id
--     'Customer Feedback Survey',
--     'Gather customer insights about product experience',
--     'openai/gpt-4o-mini',
--     0.7,
--     'You are Emma, a friendly customer success manager conducting a feedback survey. Be conversational, empathetic, and genuinely interested in the responses.',
--     'We are gathering feedback to improve our product and understand customer needs better.',
--     '[
--         {"name": "Name", "mandatory": true, "order": 1},
--         {"name": "Email", "mandatory": true, "order": 2},
--         {"name": "Company", "mandatory": false, "order": 3},
--         {"name": "Job Title", "mandatory": false, "order": 4},
--         {"name": "Product Usage", "mandatory": true, "order": 5},
--         {"name": "Pain Points", "mandatory": true, "order": 6},
--         {"name": "Feature Requests", "mandatory": false, "order": 7}
--     ]'::jsonb
-- );

-- ============================================================================
-- SCHEMA COMPLETE
-- ============================================================================

-- Grant necessary permissions (adjust as needed for your setup)
-- GRANT ALL ON survey_configs TO authenticated;
-- GRANT ALL ON survey_conversations TO authenticated, anon;
-- GRANT ALL ON survey_analytics TO authenticated, anon;
