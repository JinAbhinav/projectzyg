-- Create the necessary tables for threat intelligence database

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create enum types
CREATE TYPE severity_level AS ENUM ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL');

-- Create threats table
CREATE TABLE IF NOT EXISTS threats (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    threat_type TEXT NOT NULL,
    severity severity_level NOT NULL,
    confidence FLOAT NOT NULL CHECK (confidence >= 0.0 AND confidence <= 1.0),
    tactics JSONB,
    techniques JSONB,
    source_url TEXT NOT NULL,
    discovery_date TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    mitigations JSONB,
    references JSONB
);

-- Create threat actors table
CREATE TABLE IF NOT EXISTS threat_actors (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    threat_id UUID NOT NULL REFERENCES threats(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT,
    aliases JSONB,
    origin_country TEXT,
    motivation JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create indicators (IOCs) table
CREATE TABLE IF NOT EXISTS threat_indicators (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    threat_id UUID NOT NULL REFERENCES threats(id) ON DELETE CASCADE,
    type TEXT NOT NULL,
    value TEXT NOT NULL,
    confidence FLOAT NOT NULL CHECK (confidence >= 0.0 AND confidence <= 1.0),
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (threat_id, type, value)
);

-- Create affected systems table
CREATE TABLE IF NOT EXISTS affected_systems (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    threat_id UUID NOT NULL REFERENCES threats(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    type TEXT NOT NULL,
    version TEXT,
    impact TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Add indexes for better performance
CREATE INDEX idx_threats_threat_type ON threats(threat_type);
CREATE INDEX idx_threats_severity ON threats(severity);
CREATE INDEX idx_threat_actors_name ON threat_actors(name);
CREATE INDEX idx_threat_indicators_type_value ON threat_indicators(type, value);
CREATE INDEX idx_affected_systems_name_type ON affected_systems(name, type);

-- Add full-text search capabilities
ALTER TABLE threats ADD COLUMN IF NOT EXISTS search_vector tsvector;
CREATE INDEX IF NOT EXISTS threats_search_idx ON threats USING GIN(search_vector);

-- Create function to update search vector
CREATE OR REPLACE FUNCTION threats_search_update() RETURNS trigger AS $$
BEGIN
  NEW.search_vector = 
    setweight(to_tsvector('english', coalesce(NEW.title, '')), 'A') ||
    setweight(to_tsvector('english', coalesce(NEW.description, '')), 'B') ||
    setweight(to_tsvector('english', coalesce(NEW.threat_type, '')), 'C');
  RETURN NEW;
END
$$ LANGUAGE plpgsql;

-- Create trigger to update search vector on insert or update
CREATE TRIGGER threats_search_vector_update
BEFORE INSERT OR UPDATE ON threats
FOR EACH ROW EXECUTE FUNCTION threats_search_update();

-- Create RLS policies
ALTER TABLE threats ENABLE ROW LEVEL SECURITY;
ALTER TABLE threat_actors ENABLE ROW LEVEL SECURITY;
ALTER TABLE threat_indicators ENABLE ROW LEVEL SECURITY;
ALTER TABLE affected_systems ENABLE ROW LEVEL SECURITY;

-- Create policy for authenticated users to read all threats
CREATE POLICY "Authenticated users can read threats"
ON threats FOR SELECT
TO authenticated
USING (true);

-- Create policy for authenticated users to insert threats
CREATE POLICY "Authenticated users can insert threats"
ON threats FOR INSERT
TO authenticated
WITH CHECK (true);

-- Apply similar policies to related tables
CREATE POLICY "Authenticated users can read threat actors"
ON threat_actors FOR SELECT
TO authenticated
USING (true);

CREATE POLICY "Authenticated users can read threat indicators"
ON threat_indicators FOR SELECT
TO authenticated
USING (true);

CREATE POLICY "Authenticated users can read affected systems"
ON affected_systems FOR SELECT
TO authenticated
USING (true);

-- Create policy for inserting related records
CREATE POLICY "Authenticated users can insert threat actors"
ON threat_actors FOR INSERT
TO authenticated
WITH CHECK (true);

CREATE POLICY "Authenticated users can insert threat indicators"
ON threat_indicators FOR INSERT
TO authenticated
WITH CHECK (true);

CREATE POLICY "Authenticated users can insert affected systems"
ON affected_systems FOR INSERT
TO authenticated
WITH CHECK (true); 