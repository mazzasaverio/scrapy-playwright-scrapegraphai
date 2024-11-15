-- Create frontier_url table if it doesn't exist
CREATE TABLE IF NOT EXISTS frontier_url (
    id BIGSERIAL PRIMARY KEY,
    url TEXT NOT NULL,
    category TEXT NOT NULL,
    url_type INTEGER NOT NULL CHECK (
        url_type >= 0
        AND url_type <= 4
    ),
    depth INTEGER NOT NULL DEFAULT 0,
    max_depth INTEGER NOT NULL DEFAULT 0,
    main_domain TEXT,
    target_patterns TEXT [],
    seed_pattern TEXT,
    is_target BOOLEAN NOT NULL DEFAULT false,
    parent_url TEXT,
    -- Using TEXT instead of ENUM
    url_state TEXT NOT NULL DEFAULT 'pending' CHECK (
        url_state IN (
            'pending',
            'processing',
            'processed',
            'failed',
            'skipped'
        )
    ),
    error_message TEXT,
    insert_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_update TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(url, category)
);
-- Create indices for frontier_url if they don't exist
CREATE INDEX IF NOT EXISTS idx_frontier_url_state ON frontier_url(url_state);
CREATE INDEX IF NOT EXISTS idx_frontier_url_category ON frontier_url(category);
CREATE INDEX IF NOT EXISTS idx_frontier_url_domain ON frontier_url(main_domain);
CREATE INDEX IF NOT EXISTS idx_frontier_url_type ON frontier_url(url_type);
CREATE INDEX IF NOT EXISTS idx_frontier_url_is_target ON frontier_url(is_target);
-- Create config_url_log table if it doesn't exist
CREATE TABLE IF NOT EXISTS config_url_log (
    id BIGSERIAL PRIMARY KEY,
    url TEXT NOT NULL,
    category TEXT NOT NULL,
    url_type INTEGER NOT NULL CHECK (
        url_type >= 0
        AND url_type <= 4
    ),
    -- Using TEXT instead of ENUM
    config_state TEXT NOT NULL DEFAULT 'pending' CHECK (
        config_state IN (
            'pending',
            'running',
            'completed',
            'failed',
            'partially_completed'
        )
    ),
    -- Process tracking
    start_time TIMESTAMP WITH TIME ZONE,
    end_time TIMESTAMP WITH TIME ZONE,
    processing_duration FLOAT,
    -- Counters
    total_urls_found INTEGER DEFAULT 0,
    target_urls_found INTEGER DEFAULT 0,
    seed_urls_found INTEGER DEFAULT 0,
    failed_urls INTEGER DEFAULT 0,
    -- Configuration
    max_depth INTEGER NOT NULL DEFAULT 0,
    reached_depth INTEGER DEFAULT 0,
    target_patterns TEXT [],
    seed_pattern TEXT,
    -- Error handling
    error_message TEXT,
    warning_messages TEXT [],
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    -- Additional metadata
    metadata JSONB DEFAULT '{}'::jsonb,
    UNIQUE(url, category)
);
-- Create indices for config_url_log if they don't exist
CREATE INDEX IF NOT EXISTS idx_config_url_log_category ON config_url_log(category);
CREATE INDEX IF NOT EXISTS idx_config_url_log_state ON config_url_log(config_state);
CREATE INDEX IF NOT EXISTS idx_config_url_log_type ON config_url_log(url_type);
CREATE INDEX IF NOT EXISTS idx_config_url_log_updated ON config_url_log(updated_at);
-- Create or replace function for updating last_update column
CREATE OR REPLACE FUNCTION update_last_update_column() RETURNS TRIGGER AS $$ BEGIN NEW.last_update = CURRENT_TIMESTAMP;
RETURN NEW;
END;
$$ LANGUAGE 'plpgsql';
-- Create or replace function for updating updated_at column
CREATE OR REPLACE FUNCTION update_updated_at_column() RETURNS TRIGGER AS $$ BEGIN NEW.updated_at = CURRENT_TIMESTAMP;
RETURN NEW;
END;
$$ LANGUAGE 'plpgsql';
-- Drop and recreate triggers to ensure they are up to date
DROP TRIGGER IF EXISTS update_frontier_url_last_update ON frontier_url;
CREATE TRIGGER update_frontier_url_last_update BEFORE
UPDATE ON frontier_url FOR EACH ROW EXECUTE FUNCTION update_last_update_column();
DROP TRIGGER IF EXISTS update_config_url_log_updated_at ON config_url_log;
CREATE TRIGGER update_config_url_log_updated_at BEFORE
UPDATE ON config_url_log FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
-- Add comments
COMMENT ON TABLE frontier_url IS 'Stores URLs to be crawled and their metadata';
COMMENT ON TABLE config_url_log IS 'Logs configuration and results of URL processing';
COMMENT ON COLUMN frontier_url.url_state IS 'Current state of URL processing (pending, processing, processed, failed, skipped)';
COMMENT ON COLUMN config_url_log.config_state IS 'Current state of configuration processing (pending, running, completed, failed, partially_completed)';
-- Create schema version table if it doesn't exist
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
-- Insert initial schema version if not exists
INSERT INTO schema_version (version)
VALUES (1) ON CONFLICT (version) DO NOTHING;