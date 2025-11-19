// API Key management endpoints

use rocket::serde::json::Json;
use rocket::http::Status;
use rocket::State;
use serde::{Deserialize, Serialize};
use sqlx::PgPool;

use crate::endpoints::{HttpErrorJson, ServerState};
use aw_datastore::api_key_helpers;

#[derive(Serialize, Deserialize)]
pub struct CreateApiKeyRequest {
    pub client_id: String,
    pub description: Option<String>,
}

#[derive(Serialize, Deserialize)]
pub struct CreateApiKeyResponse {
    pub id: i32,
    pub api_key: String,
    pub client_id: String,
    pub description: Option<String>,
    pub created_at: chrono::DateTime<chrono::Utc>,
}

#[derive(Serialize, Deserialize)]
pub struct ApiKeyInfo {
    pub id: i32,
    pub client_id: String,
    pub description: Option<String>,
    pub created_at: chrono::DateTime<chrono::Utc>,
    pub last_used_at: Option<chrono::DateTime<chrono::Utc>>,
    pub is_active: bool,
}

#[derive(Serialize, Deserialize)]
pub struct ErrorResponse {
    pub error: String,
}

/// Create a new API key
/// Note: The API key is returned only once on creation
#[post("/api-keys", data = "<request>")]
pub async fn create_api_key(
    request: Json<CreateApiKeyRequest>,
    state: &State<ServerState>,
) -> Result<Json<CreateApiKeyResponse>, (Status, Json<ErrorResponse>)> {
    let pool = match &state.db_pool {
        Some(pool) => pool,
        None => {
            return Err((
                Status::InternalServerError,
                Json(ErrorResponse {
                    error: "Database pool not available".to_string(),
                }),
            ));
        }
    };

    match api_key_helpers::create_api_key(
        pool,
        &request.client_id,
        request.description.as_deref(),
    )
    .await
    {
        Ok((id, api_key)) => {
            // Get created_at timestamp
            let created_at = chrono::Utc::now();
            
            Ok(Json(CreateApiKeyResponse {
                id,
                api_key,
                client_id: request.client_id.clone(),
                description: request.description.clone(),
                created_at,
            }))
        }
        Err(e) => Err((
            Status::InternalServerError,
            Json(ErrorResponse {
                error: format!("Failed to create API key: {}", e),
            }),
        )),
    }
}

/// List all API keys (without exposing the keys themselves)
#[get("/api-keys")]
pub async fn list_api_keys(
    state: &State<ServerState>,
) -> Result<Json<Vec<ApiKeyInfo>>, (Status, Json<ErrorResponse>)> {
    let pool = match &state.db_pool {
        Some(pool) => pool,
        None => {
            return Err((
                Status::InternalServerError,
                Json(ErrorResponse {
                    error: "Database pool not available".to_string(),
                }),
            ));
        }
    };

    match api_key_helpers::list_api_keys(pool).await {
        Ok(keys) => {
            let info: Vec<ApiKeyInfo> = keys
                .into_iter()
                .map(|k| ApiKeyInfo {
                    id: k.id,
                    client_id: k.client_id,
                    description: k.description,
                    created_at: k.created_at,
                    last_used_at: k.last_used_at,
                    is_active: k.is_active,
                })
                .collect();
            Ok(Json(info))
        }
        Err(e) => Err((
            Status::InternalServerError,
            Json(ErrorResponse {
                error: format!("Failed to list API keys: {}", e),
            }),
        )),
    }
}

/// Revoke an API key
#[delete("/api-keys/<key_id>")]
pub async fn revoke_api_key(
    key_id: i32,
    state: &State<ServerState>,
) -> Result<(), (Status, Json<ErrorResponse>)> {
    let pool = match &state.db_pool {
        Some(pool) => pool,
        None => {
            return Err((
                Status::InternalServerError,
                Json(ErrorResponse {
                    error: "Database pool not available".to_string(),
                }),
            ));
        }
    };

    match api_key_helpers::revoke_api_key(pool, key_id).await {
        Ok(true) => Ok(()),
        Ok(false) => Err((
            Status::NotFound,
            Json(ErrorResponse {
                error: "API key not found".to_string(),
            }),
        )),
        Err(e) => Err((
            Status::InternalServerError,
            Json(ErrorResponse {
                error: format!("Failed to revoke API key: {}", e),
            }),
        )),
    }
}

