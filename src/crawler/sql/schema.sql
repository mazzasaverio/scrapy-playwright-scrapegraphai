
-- name: create_schema!
CREATE TABLE IF NOT EXISTS frontier_url (
    id BIGSERIAL PRIMARY KEY,
    url TEXT NOT NULL,
    category TEXT NOT NULL,
    type INTEGER NOT NULL CHECK (type >= 0 AND type <= 2),
    depth INTEGER NOT NULL DEFAULT 0,
    is_target BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP WITH TIME ZONE,
    failed_attempts INTEGER DEFAULT 0,
    last_error TEXT,
    UNIQUE(url, category)
);

CREATE INDEX IF NOT EXISTS idx_frontier_url_status 
    ON frontier_url(processed_at) 
    WHERE processed_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_frontier_url_category 
    ON frontier_url(category);

CREATE TABLE IF NOT EXISTS config_url_log (
    id BIGSERIAL PRIMARY KEY,
    url TEXT NOT NULL,
    category TEXT NOT NULL,
    type INTEGER NOT NULL CHECK (type >= 0 AND type <= 2),
    last_checked_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    success_count INTEGER DEFAULT 0,
    failure_count INTEGER DEFAULT 0,
    last_status TEXT,
    UNIQUE(url, category)
);

CREATE INDEX IF NOT EXISTS idx_config_url_log_category 
    ON config_url_log(category);
