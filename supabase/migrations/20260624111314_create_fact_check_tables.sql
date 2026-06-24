-- Create verification_sessions table for storing fact-check results
CREATE TABLE IF NOT EXISTS verification_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    document_name TEXT NOT NULL,
    total_claims INTEGER DEFAULT 0,
    verified_count INTEGER DEFAULT 0,
    inaccurate_count INTEGER DEFAULT 0,
    false_count INTEGER DEFAULT 0,
    unverifiable_count INTEGER DEFAULT 0,
    avg_confidence DECIMAL(5,2) DEFAULT 0,
    session_data JSONB DEFAULT '{}'::jsonb
);

-- Create claims table for individual claim records
CREATE TABLE IF NOT EXISTS verification_claims (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES verification_sessions(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    claim_text TEXT NOT NULL,
    claim_type TEXT NOT NULL,
    page_number INTEGER DEFAULT 1,
    category TEXT NOT NULL,
    confidence_score DECIMAL(5,2) DEFAULT 0,
    evidence JSONB DEFAULT '[]'::jsonb,
    source_urls JSONB DEFAULT '[]'::jsonb,
    explanation TEXT DEFAULT ''
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_verification_sessions_created_at ON verification_sessions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_verification_claims_session_id ON verification_claims(session_id);
CREATE INDEX IF NOT EXISTS idx_verification_claims_category ON verification_claims(category);

-- Enable RLS
ALTER TABLE verification_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE verification_claims ENABLE ROW LEVEL SECURITY;

-- RLS Policies for verification_sessions
CREATE POLICY "select_public_sessions" ON verification_sessions FOR SELECT
    TO anon, authenticated USING (true);

CREATE POLICY "insert_public_sessions" ON verification_sessions FOR INSERT
    TO anon, authenticated WITH CHECK (true);

CREATE POLICY "update_public_sessions" ON verification_sessions FOR UPDATE
    TO anon, authenticated USING (true) WITH CHECK (true);

CREATE POLICY "delete_public_sessions" ON verification_sessions FOR DELETE
    TO anon, authenticated USING (true);

-- RLS Policies for verification_claims
CREATE POLICY "select_public_claims" ON verification_claims FOR SELECT
    TO anon, authenticated USING (true);

CREATE POLICY "insert_public_claims" ON verification_claims FOR INSERT
    TO anon, authenticated WITH CHECK (true);

CREATE POLICY "update_public_claims" ON verification_claims FOR UPDATE
    TO anon, authenticated USING (true) WITH CHECK (true);

CREATE POLICY "delete_public_claims" ON verification_claims FOR DELETE
    TO anon, authenticated USING (true);
