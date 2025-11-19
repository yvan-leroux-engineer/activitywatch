-- Insert fake buckets
INSERT INTO buckets (bucket_id, name, type, client, hostname, created, data)
VALUES 
    ('aw-watcher-window_test-machine', 'Window Activity', 'currentwindow', 'aw-watcher-window', 'test-machine', NOW() - INTERVAL '7 days', '{"$schema": "https://github.com/ActivityWatch/aw-server/raw/master/docs/schemas/current-window.schema.json"}'::jsonb),
    ('aw-watcher-afk_test-machine', 'AFK Status', 'afkstatus', 'aw-watcher-afk', 'test-machine', NOW() - INTERVAL '7 days', '{"$schema": "https://github.com/ActivityWatch/aw-server/raw/master/docs/schemas/afkstatus.schema.json"}'::jsonb),
    ('aw-watcher-web-chrome_test-machine', 'Chrome Browser', 'web.tab.current', 'aw-watcher-web-chrome', 'test-machine', NOW() - INTERVAL '5 days', '{"$schema": "https://github.com/ActivityWatch/aw-server/raw/master/docs/schemas/web-tab-current.schema.json"}'::jsonb)
ON CONFLICT (bucket_id) DO NOTHING;

-- Insert fake events for window watcher (last 3 days)
-- Generate events every 30 minutes during work hours (9 AM - 6 PM)
DO $$
DECLARE
    bucket_window_id VARCHAR(255) := 'aw-watcher-window_test-machine';
    bucket_afk_id VARCHAR(255) := 'aw-watcher-afk_test-machine';
    bucket_web_id VARCHAR(255) := 'aw-watcher-web-chrome_test-machine';
    event_time TIMESTAMPTZ;
    apps TEXT[] := ARRAY['Visual Studio Code', 'Google Chrome', 'Terminal', 'Slack', 'GitHub Desktop', 'Postman', 'Spotify'];
    windows TEXT[] := ARRAY['activityWatch - Visual Studio Code', 'GitHub - Google Chrome', 'Terminal - zsh', 'Slack', 'activityWatch - GitHub Desktop', 'API Testing - Postman', 'Spotify'];
    websites TEXT[] := ARRAY['github.com', 'stackoverflow.com', 'docs.rs', 'localhost:8080', 'reddit.com'];
    i INTEGER;
    j INTEGER;
    app_idx INTEGER;
    window_idx INTEGER;
    website_idx INTEGER;
    duration_seconds INTEGER;
BEGIN
    -- Window events for last 3 days
    FOR i IN 0..71 LOOP  -- 3 days * 24 hours = 72 hours, but we'll do work hours only
        event_time := NOW() - INTERVAL '3 days' + (i * INTERVAL '1 hour');
        
        -- Only create events during work hours (9 AM - 6 PM)
        IF EXTRACT(HOUR FROM event_time) >= 9 AND EXTRACT(HOUR FROM event_time) < 18 THEN
            app_idx := (i % array_length(apps, 1)) + 1;
            window_idx := (i % array_length(windows, 1)) + 1;
            duration_seconds := 1800 + (random() * 3600)::INTEGER; -- 30 min to 1.5 hours
            
            INSERT INTO events (bucket_id, timestamp, duration, data)
            VALUES (
                bucket_window_id,
                event_time,
                INTERVAL '1 second' * duration_seconds,
                jsonb_build_object(
                    'app', apps[app_idx],
                    'title', windows[window_idx]
                )
            );
            
            -- AFK status events (not AFK during work hours)
            INSERT INTO events (bucket_id, timestamp, duration, data)
            VALUES (
                bucket_afk_id,
                event_time,
                INTERVAL '1 second' * duration_seconds,
                jsonb_build_object('status', 'not-afk')
            );
            
            -- Web browser events (every 2nd hour)
            IF i % 2 = 0 THEN
                website_idx := (i % array_length(websites, 1)) + 1;
                INSERT INTO events (bucket_id, timestamp, duration, data)
                VALUES (
                    bucket_web_id,
                    event_time,
                    INTERVAL '1 second' * (900 + (random() * 1800)::INTEGER), -- 15-45 min
                    jsonb_build_object(
                        'url', 'https://' || websites[website_idx],
                        'title', 'Page Title - ' || websites[website_idx]
                    )
                );
            END IF;
        END IF;
    END LOOP;
    
    -- Add some AFK events during non-work hours
    FOR i IN 0..20 LOOP
        event_time := NOW() - INTERVAL '2 days' + (i * INTERVAL '2 hours');
        IF EXTRACT(HOUR FROM event_time) < 9 OR EXTRACT(HOUR FROM event_time) >= 18 THEN
            INSERT INTO events (bucket_id, timestamp, duration, data)
            VALUES (
                bucket_afk_id,
                event_time,
                INTERVAL '1 hour' * (1 + (random() * 2)::INTEGER),
                jsonb_build_object('status', 'afk')
            );
        END IF;
    END LOOP;
END $$;

-- Verify data was inserted
SELECT 
    'Buckets' as table_name,
    COUNT(*) as count
FROM buckets
UNION ALL
SELECT 
    'Events' as table_name,
    COUNT(*) as count
FROM events;

-- Show sample events
SELECT 
    bucket_id,
    timestamp,
    duration,
    data
FROM events
ORDER BY timestamp DESC
LIMIT 10;

