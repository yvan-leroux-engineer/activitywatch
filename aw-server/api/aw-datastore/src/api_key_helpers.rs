// Helper functions for API key operations
// This module provides async PostgreSQL operations for API key management

use chrono::{DateTime, Utc};
use sqlx::{PgPool, Row};

/// Hash an API key using SHA-256 (hex encoded)
pub fn hash_api_key(key: &str) -> String {
    use sha2::{Sha256, Digest};
    let mut hasher = Sha256::new();
    hasher.update(key.as_bytes());
    format!("{:x}", hasher.finalize())
}

/// Generate a secure random API key
fn generate_api_key() -> String {
    use getrandom::getrandom;
    let mut bytes = [0u8; 32];
    getrandom(&mut bytes).expect("Failed to generate random bytes");
    hex::encode(bytes)
}

/// Create a new API key
pub async fn create_api_key(
    pool: &PgPool,
    client_id: &str,
    description: Option<&str>,
) -> Result<(i32, String), sqlx::Error> {
    // Generate a secure random API key
    let api_key = generate_api_key();
    
    // Hash the key before storing
    let key_hash = hash_api_key(&api_key);
    
    let id: i32 = sqlx::query_scalar(
        r#"
        INSERT INTO api_keys (key_hash, client_id, description, created_at, is_active)
        VALUES ($1, $2, $3, NOW(), TRUE)
        RETURNING id
        "#
    )
    .bind(&key_hash)
    .bind(client_id)
    .bind(description)
    .fetch_one(pool)
    .await?;
    
    Ok((id, api_key))
}

/// Validate an API key and return client_id if valid
pub async fn validate_api_key(
    pool: &PgPool,
    api_key: &str,
) -> Result<Option<(i32, String)>, sqlx::Error> {
    let key_hash = hash_api_key(api_key);
    
    let row = sqlx::query(
        r#"
        SELECT id, client_id
        FROM api_keys
        WHERE key_hash = $1 AND is_active = TRUE
        "#
    )
    .bind(&key_hash)
    .fetch_optional(pool)
    .await?;
    
    match row {
        Some(row) => {
            let id: i32 = row.try_get("id")?;
            let client_id: String = row.try_get("client_id")?;
            
            // Update last_used_at
            sqlx::query(
                r#"
                UPDATE api_keys
                SET last_used_at = NOW()
                WHERE id = $1
                "#
            )
            .bind(id)
            .execute(pool)
            .await?;
            
            Ok(Some((id, client_id)))
        }
        None => Ok(None),
    }
}

/// List all API keys (without exposing the keys themselves)
pub async fn list_api_keys(
    pool: &PgPool,
) -> Result<Vec<ApiKeyInfo>, sqlx::Error> {
    let rows = sqlx::query(
        r#"
        SELECT id, client_id, description, created_at, last_used_at, is_active
        FROM api_keys
        ORDER BY created_at DESC
        "#
    )
    .fetch_all(pool)
    .await?;
    
    let mut keys = Vec::new();
    for row in rows {
        keys.push(ApiKeyInfo {
            id: row.try_get("id")?,
            client_id: row.try_get("client_id")?,
            description: row.try_get("description")?,
            created_at: row.try_get("created_at")?,
            last_used_at: row.try_get("last_used_at")?,
            is_active: row.try_get("is_active")?,
        });
    }
    
    Ok(keys)
}

/// Revoke an API key
pub async fn revoke_api_key(
    pool: &PgPool,
    key_id: i32,
) -> Result<bool, sqlx::Error> {
    let rows_affected = sqlx::query(
        r#"
        UPDATE api_keys
        SET is_active = FALSE
        WHERE id = $1
        "#
    )
    .bind(key_id)
    .execute(pool)
    .await?
    .rows_affected();
    
    Ok(rows_affected > 0)
}

#[derive(Debug, Clone)]
pub struct ApiKeyInfo {
    pub id: i32,
    pub client_id: String,
    pub description: Option<String>,
    pub created_at: DateTime<Utc>,
    pub last_used_at: Option<DateTime<Utc>>,
    pub is_active: bool,
}

