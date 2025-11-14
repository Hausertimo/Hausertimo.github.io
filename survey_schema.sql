-- AI Survey System Database Schema
-- Run this in your Supabase SQL Editor to create the required tables
-- ========================================================================

-- Surveys table (configurations)
CREATE TABLE IF NOT EXISTS public.surveys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,

    -- Survey settings
    name TEXT NOT NULL DEFAULT 'Untitled Survey',
    model_id TEXT NOT NULL,
    model_name TEXT NOT NULL,
    temperature NUMERIC(3,2) DEFAULT 0.7 CHECK (temperature >= 0 AND temperature <= 2),

    -- AI personality
    character_prompt TEXT NOT NULL,
    survey_brief TEXT NOT NULL,

    -- Topics configuration
    topics JSONB NOT NULL DEFAULT '[]'::jsonb,
    -- Format: [{"name": "Name", "description": "Full name", "mandatory": true, "order": 1}]

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT true,

    CONSTRAINT topics_not_empty CHECK (jsonb_array_length(topics) > 0)
);

-- Survey responses table (conversations)
CREATE TABLE IF NOT EXISTS public.survey_responses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    survey_id UUID NOT NULL REFERENCES surveys(id) ON DELETE CASCADE,

    -- Response metadata
    respondent_email TEXT,
    respondent_metadata JSONB DEFAULT '{}'::jsonb,

    -- Conversation data
    conversation JSONB NOT NULL DEFAULT '[]'::jsonb,
    -- Format: [{"role": "assistant", "content": "...", "timestamp": "..."}]

    -- Topic progress
    current_topic_index INTEGER DEFAULT 0,
    completed_topics JSONB DEFAULT '[]'::jsonb,
    -- Format: [{"topic": "Name", "value": "John Doe", "satisfied": true, "attempts": 1}]

    -- Status
    status TEXT DEFAULT 'in_progress' CHECK (status IN ('in_progress', 'completed', 'abandoned')),
    completed_at TIMESTAMP WITH TIME ZONE,

    -- Timestamps
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_interaction_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_surveys_user_id ON surveys(user_id);
CREATE INDEX IF NOT EXISTS idx_surveys_active ON surveys(is_active) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_survey_responses_survey_id ON survey_responses(survey_id);
CREATE INDEX IF NOT EXISTS idx_survey_responses_status ON survey_responses(status);

-- RLS Policies
ALTER TABLE surveys ENABLE ROW LEVEL SECURITY;
ALTER TABLE survey_responses ENABLE ROW LEVEL SECURITY;

-- Drop existing policies if they exist
DROP POLICY IF EXISTS "Users can manage own surveys" ON surveys;
DROP POLICY IF EXISTS "Survey owners can view responses" ON survey_responses;
DROP POLICY IF EXISTS "Anyone can create responses" ON survey_responses;
DROP POLICY IF EXISTS "Owners can update responses" ON survey_responses;

-- Users can only access their own surveys
CREATE POLICY "Users can manage own surveys"
ON surveys
FOR ALL
USING (auth.uid() = user_id);

-- Survey responses can be viewed by survey owner
CREATE POLICY "Survey owners can view responses"
ON survey_responses
FOR SELECT
USING (
    EXISTS (
        SELECT 1 FROM surveys
        WHERE surveys.id = survey_responses.survey_id
        AND surveys.user_id = auth.uid()
    )
);

-- Anyone can create responses (for public surveys)
CREATE POLICY "Anyone can create responses"
ON survey_responses
FOR INSERT
WITH CHECK (true);

-- Only response owner or survey owner can update
CREATE POLICY "Owners can update responses"
ON survey_responses
FOR UPDATE
USING (
    EXISTS (
        SELECT 1 FROM surveys
        WHERE surveys.id = survey_responses.survey_id
        AND surveys.user_id = auth.uid()
    )
);

-- Auto-update updated_at trigger
-- (Note: update_updated_at_column function should already exist from normscout_auth schema)
-- If it doesn't exist, create it:
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger to auto-update updated_at on surveys table
DROP TRIGGER IF EXISTS update_surveys_updated_at ON surveys;
CREATE TRIGGER update_surveys_updated_at
    BEFORE UPDATE ON surveys
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ========================================================================
-- Schema created successfully!
-- ========================================================================
