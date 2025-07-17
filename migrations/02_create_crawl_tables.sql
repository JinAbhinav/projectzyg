-- Create the necessary tables for web crawl data storage

-- Create crawl_jobs table to track crawl requests
CREATE TABLE IF NOT EXISTS crawl_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    url TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending', -- pending, running, completed, error
    error_message TEXT,
    parameters JSONB, -- store crawl parameters
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by UUID REFERENCES auth.users(id),
    pages_crawled INTEGER DEFAULT 0
);

-- Create crawled_pages table to store individual crawled pages
CREATE TABLE IF NOT EXISTS crawled_pages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id UUID NOT NULL REFERENCES crawl_jobs(id) ON DELETE CASCADE,
    url TEXT NOT NULL,
    title TEXT,
    content TEXT, -- Markdown content
    html TEXT, -- Optional raw HTML
    page_type TEXT DEFAULT 'page', -- page, pdf, image, etc.
    content_type TEXT DEFAULT 'text/markdown',
    metadata JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create extracted_indicators table to store IOCs from crawled pages
CREATE TABLE IF NOT EXISTS extracted_indicators (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    page_id UUID NOT NULL REFERENCES crawled_pages(id) ON DELETE CASCADE,
    type TEXT NOT NULL, -- ip, domain, email, hash, etc.
    value TEXT NOT NULL,
    confidence FLOAT NOT NULL DEFAULT 0.9 CHECK (confidence >= 0.0 AND confidence <= 1.0),
    context TEXT, -- surrounding text for context
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (page_id, type, value)
);

-- Add search vector for full-text search on crawled pages
ALTER TABLE crawled_pages ADD COLUMN IF NOT EXISTS search_vector tsvector;
CREATE INDEX IF NOT EXISTS crawled_pages_search_idx ON crawled_pages USING GIN(search_vector);

-- Create function to update search vector
CREATE OR REPLACE FUNCTION crawled_pages_search_update() RETURNS trigger AS $$
BEGIN
  NEW.search_vector = 
    setweight(to_tsvector('english', coalesce(NEW.title, '')), 'A') ||
    setweight(to_tsvector('english', coalesce(NEW.url, '')), 'B') ||
    setweight(to_tsvector('english', coalesce(NEW.content, '')), 'C');
  RETURN NEW;
END
$$ LANGUAGE plpgsql;

-- Create trigger to update search vector on insert or update
CREATE TRIGGER crawled_pages_search_vector_update
BEFORE INSERT OR UPDATE ON crawled_pages
FOR EACH ROW EXECUTE FUNCTION crawled_pages_search_update();

-- Add indexes for better query performance
CREATE INDEX idx_crawl_jobs_status ON crawl_jobs(status);
CREATE INDEX idx_crawl_jobs_created_at ON crawl_jobs(created_at);
CREATE INDEX idx_crawled_pages_job_id ON crawled_pages(job_id);
CREATE INDEX idx_crawled_pages_url ON crawled_pages(url);
CREATE INDEX idx_extracted_indicators_type_value ON extracted_indicators(type, value);

-- Enable Row Level Security
ALTER TABLE crawl_jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE crawled_pages ENABLE ROW LEVEL SECURITY;
ALTER TABLE extracted_indicators ENABLE ROW LEVEL SECURITY;

-- RLS Policies for crawl_jobs
CREATE POLICY "Authenticated users can read all crawl jobs"
ON crawl_jobs FOR SELECT
TO authenticated
USING (true);

CREATE POLICY "Users can insert their own crawl jobs"
ON crawl_jobs FOR INSERT
TO authenticated
WITH CHECK (created_by = auth.uid());

-- RLS Policies for crawled_pages
CREATE POLICY "Authenticated users can read all crawled pages"
ON crawled_pages FOR SELECT
TO authenticated
USING (true);

-- RLS Policies for extracted_indicators
CREATE POLICY "Authenticated users can read all extracted indicators"
ON extracted_indicators FOR SELECT
TO authenticated
USING (true); 