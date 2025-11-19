// Helper functions for PostgreSQL operations
// This module provides async PostgreSQL operations that can be called from sync context

use chrono::{DateTime, Duration, Utc};
use sqlx::{PgPool, Row};
use serde_json::Value;

use aw_models::{Bucket, BucketMetadata, Event};

use crate::DatastoreError;

pub async fn get_stored_buckets(pool: &PgPool) -> Result<std::collections::HashMap<String, Bucket>, DatastoreError> {
    let mut buckets = std::collections::HashMap::new();
    
    let rows = sqlx::query(
        r#"
        SELECT 
            buckets.id,
            buckets.bucket_id,
            buckets.name,
            buckets.type,
            buckets.client,
            buckets.hostname,
            buckets.created,
            buckets.data,
            MIN(events.timestamp) as first_event,
            MAX(events.timestamp + (events.duration || ' microseconds')::interval) as last_event
        FROM buckets
        LEFT OUTER JOIN events ON buckets.bucket_id = events.bucket_id
        GROUP BY buckets.id, buckets.bucket_id, buckets.name, buckets.type, 
                 buckets.client, buckets.hostname, buckets.created, buckets.data
        "#
    )
    .fetch_all(pool)
    .await
    .map_err(|e| DatastoreError::InternalError(format!("Failed to query buckets: {}", e)))?;

    for row in rows {
        let id: i32 = row.try_get("id").map_err(|e| DatastoreError::InternalError(format!("Failed to get id: {}", e)))?;
        let bucket_id: String = row.try_get("bucket_id").map_err(|e| DatastoreError::InternalError(format!("Failed to get bucket_id: {}", e)))?;
        let _name: Option<String> = row.try_get("name").ok(); // Name is stored in DB but not in Bucket model
        let _type: String = row.try_get("type").map_err(|e| DatastoreError::InternalError(format!("Failed to get type: {}", e)))?;
        let client: String = row.try_get("client").map_err(|e| DatastoreError::InternalError(format!("Failed to get client: {}", e)))?;
        let hostname: String = row.try_get("hostname").map_err(|e| DatastoreError::InternalError(format!("Failed to get hostname: {}", e)))?;
        let created: DateTime<Utc> = row.try_get("created").map_err(|e| DatastoreError::InternalError(format!("Failed to get created: {}", e)))?;
        let data: Value = row.try_get("data").map_err(|e| DatastoreError::InternalError(format!("Failed to get data: {}", e)))?;
        let first_event: Option<DateTime<Utc>> = row.try_get("first_event").ok();
        let last_event: Option<DateTime<Utc>> = row.try_get("last_event").ok();

        let data_map = match data {
            Value::Object(map) => map,
            _ => serde_json::Map::new(),
        };

        let bucket = Bucket {
            bid: Some(id as i64),
            id: bucket_id.clone(),
            _type,
            client,
            hostname,
            created: Some(created),
            data: data_map,
            metadata: BucketMetadata {
                start: first_event,
                end: last_event,
            },
            events: None,
            last_updated: None,
        };

        buckets.insert(bucket_id, bucket);
    }

    Ok(buckets)
}

pub async fn create_bucket(
    pool: &PgPool,
    bucket: &mut Bucket,
) -> Result<(), DatastoreError> {
    let created = bucket.created.unwrap_or_else(Utc::now);
    let data_json = serde_json::to_value(&bucket.data)
        .map_err(|e| DatastoreError::InternalError(format!("Failed to serialize bucket data: {}", e)))?;

    let id: i32 = sqlx::query_scalar(
        r#"
        INSERT INTO buckets (bucket_id, name, type, client, hostname, created, data)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        RETURNING id
        "#
    )
    .bind(&bucket.id)
    .bind(&bucket.id) // Use bucket_id as name if name not available
    .bind(&bucket._type)
    .bind(&bucket.client)
    .bind(&bucket.hostname)
    .bind(created)
    .bind(data_json)
    .fetch_one(pool)
    .await
    .map_err(|e| {
        if e.to_string().contains("duplicate key") {
            DatastoreError::BucketAlreadyExists(bucket.id.clone())
        } else {
            DatastoreError::InternalError(format!("Failed to create bucket: {}", e))
        }
    })?;

    bucket.bid = Some(id as i64);
    bucket.created = Some(created);
    Ok(())
}

pub async fn delete_bucket(pool: &PgPool, bucket_id: &str) -> Result<(), DatastoreError> {
    // Events are deleted via CASCADE foreign key
    let rows_affected = sqlx::query("DELETE FROM buckets WHERE bucket_id = $1")
        .bind(bucket_id)
        .execute(pool)
        .await
        .map_err(|e| DatastoreError::InternalError(format!("Failed to delete bucket: {}", e)))?
        .rows_affected();

    if rows_affected == 0 {
        return Err(DatastoreError::NoSuchBucket(bucket_id.to_string()));
    }

    Ok(())
}

pub async fn insert_events(
    pool: &PgPool,
    bucket_id: &str,
    events: &mut [Event],
) -> Result<Vec<Event>, DatastoreError> {
    let mut inserted_events = Vec::new();

    for event in events.iter_mut() {
        let data_json = serde_json::to_value(&event.data)
            .map_err(|e| DatastoreError::InternalError(format!("Failed to serialize event data: {}", e)))?;

        // Convert chrono::Duration to microseconds (BIGINT)
        let duration_microseconds = event.duration.num_microseconds()
            .ok_or_else(|| DatastoreError::InternalError("Duration too large for microseconds".to_string()))?;

        let id: i64 = sqlx::query_scalar(
            r#"
            INSERT INTO events (bucket_id, timestamp, duration, data)
            VALUES ($1, $2, $3, $4)
            RETURNING id
            "#
        )
        .bind(bucket_id)
        .bind(event.timestamp)
        .bind(duration_microseconds)
        .bind(data_json)
        .fetch_one(pool)
        .await
        .map_err(|e| DatastoreError::InternalError(format!("Failed to insert event: {}", e)))?;

        event.id = Some(id);
        inserted_events.push(event.clone());
    }

    Ok(inserted_events)
}

pub async fn get_events(
    pool: &PgPool,
    bucket_id: &str,
    starttime_opt: Option<DateTime<Utc>>,
    endtime_opt: Option<DateTime<Utc>>,
    limit_opt: Option<u64>,
) -> Result<Vec<Event>, DatastoreError> {
    let rows = match (starttime_opt, endtime_opt, limit_opt) {
        (Some(start), Some(end), Some(limit)) => {
            sqlx::query(
            r#"
            SELECT id, timestamp, duration, data
            FROM events
            WHERE bucket_id = $1
                AND timestamp + (duration::text || ' microseconds')::interval >= $2
                AND timestamp <= $3
            ORDER BY timestamp DESC
            LIMIT $4
            "#
            )
            .bind(bucket_id)
            .bind(start)
            .bind(end)
            .bind(limit as i64)
            .fetch_all(pool)
            .await
        }
        (Some(start), Some(end), None) => {
            sqlx::query(
                r#"
                SELECT id, timestamp, duration, data
                FROM events
                WHERE bucket_id = $1
                    AND timestamp + (duration::text || ' microseconds')::interval >= $2
                    AND timestamp <= $3
                ORDER BY timestamp DESC
                "#
            )
            .bind(bucket_id)
            .bind(start)
            .bind(end)
            .fetch_all(pool)
            .await
        }
        (Some(start), None, Some(limit)) => {
            sqlx::query(
                r#"
                SELECT id, timestamp, duration, data
                FROM events
                WHERE bucket_id = $1
                    AND timestamp + (duration::text || ' microseconds')::interval >= $2
                ORDER BY timestamp DESC
                LIMIT $3
                "#
            )
            .bind(bucket_id)
            .bind(start)
            .bind(limit as i64)
            .fetch_all(pool)
            .await
        }
        (None, Some(end), Some(limit)) => {
            sqlx::query(
                r#"
                SELECT id, timestamp, duration, data
                FROM events
                WHERE bucket_id = $1
                    AND timestamp <= $2
                ORDER BY timestamp DESC
                LIMIT $3
                "#
            )
            .bind(bucket_id)
            .bind(end)
            .bind(limit as i64)
            .fetch_all(pool)
            .await
        }
        (None, None, Some(limit)) => {
            sqlx::query(
                r#"
                SELECT id, timestamp, duration, data
                FROM events
                WHERE bucket_id = $1
                ORDER BY timestamp DESC
                LIMIT $2
                "#
            )
            .bind(bucket_id)
            .bind(limit as i64)
            .fetch_all(pool)
            .await
        }
        _ => {
            sqlx::query(
                r#"
                SELECT id, timestamp, duration, data
                FROM events
                WHERE bucket_id = $1
                ORDER BY timestamp DESC
                "#
            )
            .bind(bucket_id)
            .fetch_all(pool)
            .await
        }
    }
    .map_err(|e| DatastoreError::InternalError(format!("Failed to query events: {}", e)))?;

    let mut events = Vec::new();
    for row in rows {
        let id: i64 = row.try_get("id").map_err(|e| DatastoreError::InternalError(format!("Failed to get id: {}", e)))?;
        let timestamp: DateTime<Utc> = row.try_get("timestamp").map_err(|e| DatastoreError::InternalError(format!("Failed to get timestamp: {}", e)))?;
        // Duration stored as microseconds (BIGINT), convert to chrono::Duration
        let duration_microseconds: i64 = row.try_get("duration").map_err(|e| DatastoreError::InternalError(format!("Failed to get duration: {}", e)))?;
        let duration = Duration::microseconds(duration_microseconds);
        let data: Value = row.try_get("data").map_err(|e| DatastoreError::InternalError(format!("Failed to get data: {}", e)))?;

        let data_map = match data {
            Value::Object(map) => map,
            _ => serde_json::Map::new(),
        };

        events.push(Event {
            id: Some(id),
            timestamp,
            duration,
            data: data_map,
        });
    }

    Ok(events)
}

pub async fn get_event(
    pool: &PgPool,
    bucket_id: &str,
    event_id: i64,
) -> Result<Event, DatastoreError> {
    let row = sqlx::query(
        r#"
        SELECT id, timestamp, duration, data
        FROM events
        WHERE bucket_id = $1 AND id = $2
        LIMIT 1
        "#
    )
    .bind(bucket_id)
    .bind(event_id)
    .fetch_optional(pool)
    .await
    .map_err(|e| DatastoreError::InternalError(format!("Failed to query event: {}", e)))?
    .ok_or_else(|| DatastoreError::InternalError("Event not found".to_string()))?;

    let id: i64 = row.try_get("id").map_err(|e| DatastoreError::InternalError(format!("Failed to get id: {}", e)))?;
    let timestamp: DateTime<Utc> = row.try_get("timestamp").map_err(|e| DatastoreError::InternalError(format!("Failed to get timestamp: {}", e)))?;
    // PostgreSQL INTERVAL is stored as microseconds, convert to chrono::Duration
    let duration_microseconds: i64 = row.try_get("duration").map_err(|e| DatastoreError::InternalError(format!("Failed to get duration: {}", e)))?;
    let duration = Duration::microseconds(duration_microseconds);
    let data: Value = row.try_get("data").map_err(|e| DatastoreError::InternalError(format!("Failed to get data: {}", e)))?;

    let data_map = match data {
        Value::Object(map) => map,
        _ => serde_json::Map::new(),
    };

    Ok(Event {
        id: Some(id),
        timestamp,
        duration,
        data: data_map,
    })
}

pub async fn get_event_count(
    pool: &PgPool,
    bucket_id: &str,
    starttime_opt: Option<DateTime<Utc>>,
    endtime_opt: Option<DateTime<Utc>>,
) -> Result<i64, DatastoreError> {
    let count: i64 = match (starttime_opt, endtime_opt) {
        (Some(start), Some(end)) => {
            sqlx::query_scalar(
                r#"
                SELECT COUNT(*) FROM events
                WHERE bucket_id = $1
                    AND timestamp + (duration::text || ' microseconds')::interval >= $2
                    AND timestamp <= $3
                "#
            )
            .bind(bucket_id)
            .bind(start)
            .bind(end)
            .fetch_one(pool)
            .await
        }
        (Some(start), None) => {
            sqlx::query_scalar(
                r#"
                SELECT COUNT(*) FROM events
                WHERE bucket_id = $1
                    AND timestamp + (duration::text || ' microseconds')::interval >= $2
                "#
            )
            .bind(bucket_id)
            .bind(start)
            .fetch_one(pool)
            .await
        }
        (None, Some(end)) => {
            sqlx::query_scalar(
                r#"
                SELECT COUNT(*) FROM events
                WHERE bucket_id = $1
                    AND timestamp <= $2
                "#
            )
            .bind(bucket_id)
            .bind(end)
            .fetch_one(pool)
            .await
        }
        (None, None) => {
            sqlx::query_scalar(
                r#"
                SELECT COUNT(*) FROM events
                WHERE bucket_id = $1
                "#
            )
            .bind(bucket_id)
            .fetch_one(pool)
            .await
        }
    }
    .map_err(|e| DatastoreError::InternalError(format!("Failed to count events: {}", e)))?;

    Ok(count)
}

pub async fn delete_events_by_id(
    pool: &PgPool,
    bucket_id: &str,
    event_ids: Vec<i64>,
) -> Result<(), DatastoreError> {
    if event_ids.is_empty() {
        return Ok(());
    }

    sqlx::query("DELETE FROM events WHERE bucket_id = $1 AND id = ANY($2)")
        .bind(bucket_id)
        .bind(event_ids)
        .execute(pool)
        .await
        .map_err(|e| DatastoreError::InternalError(format!("Failed to delete events: {}", e)))?;

    Ok(())
}

pub async fn replace_last_event(
    pool: &PgPool,
    bucket_id: &str,
    event: &Event,
) -> Result<(), DatastoreError> {
    let data_json = serde_json::to_value(&event.data)
        .map_err(|e| DatastoreError::InternalError(format!("Failed to serialize event data: {}", e)))?;

    // Convert chrono::Duration to PostgreSQL INTERVAL (store as microseconds)
    let duration_microseconds = event.duration.num_microseconds()
        .ok_or_else(|| DatastoreError::InternalError("Duration too large for microseconds".to_string()))?;

    sqlx::query(
        r#"
        UPDATE events
        SET timestamp = $1, duration = $2, data = $3
        WHERE bucket_id = $4
            AND id = (
                SELECT id FROM events
                WHERE bucket_id = $4
                ORDER BY timestamp DESC, id DESC
                LIMIT 1
            )
        "#
    )
    .bind(event.timestamp)
    .bind(duration_microseconds)
    .bind(data_json)
    .bind(bucket_id)
    .execute(pool)
    .await
    .map_err(|e| DatastoreError::InternalError(format!("Failed to replace last event: {}", e)))?;

    Ok(())
}

pub async fn get_key_value(pool: &PgPool, key: &str) -> Result<String, DatastoreError> {
    let row = sqlx::query("SELECT value FROM key_value WHERE key = $1")
        .bind(key)
        .fetch_optional(pool)
        .await
        .map_err(|e| DatastoreError::InternalError(format!("Failed to get key value: {}", e)))?;

    match row {
        Some(row) => {
            let value: Value = row.try_get("value").map_err(|e| DatastoreError::InternalError(format!("Failed to get value: {}", e)))?;
            serde_json::to_string(&value)
                .map_err(|e| DatastoreError::InternalError(format!("Failed to serialize value: {}", e)))
        }
        None => Err(DatastoreError::NoSuchKey(key.to_string())),
    }
}

pub async fn set_key_value(
    pool: &PgPool,
    key: &str,
    value: &str,
) -> Result<(), DatastoreError> {
    let value_json: Value = serde_json::from_str(value)
        .map_err(|e| DatastoreError::InternalError(format!("Failed to parse value JSON: {}", e)))?;

    sqlx::query(
        r#"
        INSERT INTO key_value (key, value, updated_at)
        VALUES ($1, $2, NOW())
        ON CONFLICT (key) DO UPDATE SET value = $2, updated_at = NOW()
        "#
    )
    .bind(key)
    .bind(value_json)
    .execute(pool)
    .await
    .map_err(|e| DatastoreError::InternalError(format!("Failed to set key value: {}", e)))?;

    Ok(())
}

pub async fn delete_key_value(pool: &PgPool, key: &str) -> Result<(), DatastoreError> {
    sqlx::query("DELETE FROM key_value WHERE key = $1")
        .bind(key)
        .execute(pool)
        .await
        .map_err(|e| DatastoreError::InternalError(format!("Failed to delete key value: {}", e)))?;

    Ok(())
}

pub async fn get_key_values(
    pool: &PgPool,
    pattern: &str,
) -> Result<std::collections::HashMap<String, String>, DatastoreError> {
    let rows = sqlx::query("SELECT key, value FROM key_value WHERE key LIKE $1")
        .bind(pattern)
        .fetch_all(pool)
        .await
        .map_err(|e| DatastoreError::InternalError(format!("Failed to get key values: {}", e)))?;

    let mut result = std::collections::HashMap::new();
    for row in rows {
        let key: String = row.try_get("key").map_err(|e| DatastoreError::InternalError(format!("Failed to get key: {}", e)))?;
        let value: Value = row.try_get("value").map_err(|e| DatastoreError::InternalError(format!("Failed to get value: {}", e)))?;

        // Only return keys starting with "settings."
        if !key.starts_with("settings.") {
            continue;
        }

        let value_str = serde_json::to_string(&value)
            .map_err(|e| DatastoreError::InternalError(format!("Failed to serialize value: {}", e)))?;
        result.insert(key, value_str);
    }

    Ok(result)
}

