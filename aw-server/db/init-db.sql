-- Initialize TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Create buckets table
CREATE TABLE IF NOT EXISTS buckets (
    id SERIAL PRIMARY KEY,
    bucket_id VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255),
    type VARCHAR(100) NOT NULL,
    client VARCHAR(100) NOT NULL,
    hostname VARCHAR(255) NOT NULL,
    created TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    data JSONB DEFAULT '{}'::jsonb
);

-- Create indexes for buckets
CREATE INDEX IF NOT EXISTS idx_buckets_bucket_id ON buckets(bucket_id);
CREATE INDEX IF NOT EXISTS idx_buckets_type ON buckets(type);
CREATE INDEX IF NOT EXISTS idx_buckets_hostname ON buckets(hostname);

-- Create events table
-- Duration stored as microseconds (BIGINT) for better SQLx compatibility
CREATE TABLE IF NOT EXISTS events (
    id BIGSERIAL,
    bucket_id VARCHAR(255) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    duration BIGINT NOT NULL,  -- Duration in microseconds
    data JSONB NOT NULL DEFAULT '{}'::jsonb,
    PRIMARY KEY (id, timestamp),
    CONSTRAINT fk_bucket FOREIGN KEY (bucket_id) REFERENCES buckets(bucket_id) ON DELETE CASCADE
);

-- Convert events table to hypertable for time-series optimization
-- Note: This will fail if hypertable already exists, which is fine
SELECT create_hypertable('events', 'timestamp', if_not_exists => TRUE);

-- Create indexes for events
CREATE INDEX IF NOT EXISTS idx_events_bucket_timestamp ON events(bucket_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_events_data_gin ON events USING GIN(data);

-- Create retention policy (optional - keeps last 1 year of data)
-- SELECT add_retention_policy('events', INTERVAL '1 year');

-- Create continuous aggregate for daily summaries (optional)
-- CREATE MATERIALIZED VIEW daily_summary
-- WITH (timescaledb.continuous) AS
-- SELECT
--     time_bucket('1 day', timestamp) AS day,
--     bucket_id,
--     COUNT(*) AS event_count,
--     SUM(duration) AS total_duration
-- FROM events
-- GROUP BY day, bucket_id;

-- Create key_value table for settings
CREATE TABLE IF NOT EXISTS key_value (
    key VARCHAR(255) PRIMARY KEY,
    value JSONB NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_key_value_updated ON key_value(updated_at);

