// API Key Authentication middleware for Rocket
// Supports optional authentication for backward compatibility

use rocket::request::{FromRequest, Outcome, Request};
use rocket::http::Status;
use rocket::State;
use std::env;

use aw_datastore::api_key_helpers;

pub struct ApiKeyAuth {
    pub key_id: i32,
    pub client_id: String,
}

#[derive(Debug)]
pub enum ApiKeyAuthError {
    Missing,
    Invalid,
    DatabaseError,
    AuthDisabled,
}

#[rocket::async_trait]
impl<'r> FromRequest<'r> for ApiKeyAuth {
    type Error = ApiKeyAuthError;

    async fn from_request(request: &'r Request<'_>) -> Outcome<Self, Self::Error> {
        // Check if API key authentication is enabled via environment variable
        let auth_enabled = env::var("API_KEY_AUTH_ENABLED")
            .map(|v| v == "true")
            .unwrap_or(false);

        // If auth is disabled, return error (caller should handle as optional)
        if !auth_enabled {
            return Outcome::Error((Status::Unauthorized, ApiKeyAuthError::AuthDisabled));
        }

        // Extract API key from X-API-Key header
        let api_key = match request.headers().get_one("X-API-Key") {
            Some(key) => key,
            None => return Outcome::Error((Status::Unauthorized, ApiKeyAuthError::Missing)),
        };

        // Get database pool from request guard
        let state = match request.guard::<&State<crate::endpoints::ServerState>>().await {
            rocket::outcome::Outcome::Success(state) => state,
            _ => return Outcome::Error((Status::InternalServerError, ApiKeyAuthError::DatabaseError)),
        };
        
        let pool = match &state.db_pool {
            Some(pool) => pool,
            None => return Outcome::Error((Status::InternalServerError, ApiKeyAuthError::DatabaseError)),
        };

        // Validate API key
        match api_key_helpers::validate_api_key(pool, api_key).await {
            Ok(Some((key_id, client_id))) => {
                Outcome::Success(ApiKeyAuth {
                    key_id,
                    client_id,
                })
            }
            Ok(None) => Outcome::Error((Status::Unauthorized, ApiKeyAuthError::Invalid)),
            Err(_) => Outcome::Error((Status::InternalServerError, ApiKeyAuthError::DatabaseError)),
        }
    }
}

// Optional API key auth - returns None if auth is disabled or missing
pub struct OptionalApiKeyAuth(pub Option<ApiKeyAuth>);

#[rocket::async_trait]
impl<'r> FromRequest<'r> for OptionalApiKeyAuth {
    type Error = ApiKeyAuthError;

    async fn from_request(request: &'r Request<'_>) -> Outcome<Self, Self::Error> {
        // Check if API key authentication is enabled
        let auth_enabled = env::var("API_KEY_AUTH_ENABLED")
            .map(|v| v == "true")
            .unwrap_or(false);

        // If auth is disabled, allow anonymous access
        if !auth_enabled {
            return Outcome::Success(OptionalApiKeyAuth(None));
        }

        // Try to extract API key
        let api_key = match request.headers().get_one("X-API-Key") {
            Some(key) => key,
            None => return Outcome::Success(OptionalApiKeyAuth(None)),
        };

        // Get database pool from request guard
        let state = match request.guard::<&State<crate::endpoints::ServerState>>().await {
            rocket::outcome::Outcome::Success(state) => state,
            _ => return Outcome::Success(OptionalApiKeyAuth(None)),
        };
        
        let pool = match &state.db_pool {
            Some(pool) => pool,
            None => return Outcome::Success(OptionalApiKeyAuth(None)),
        };

        // Validate API key
        match api_key_helpers::validate_api_key(pool, api_key).await {
            Ok(Some((key_id, client_id))) => {
                Outcome::Success(OptionalApiKeyAuth(Some(ApiKeyAuth {
                    key_id,
                    client_id,
                })))
            }
            Ok(None) => Outcome::Success(OptionalApiKeyAuth(None)),
            Err(_) => Outcome::Success(OptionalApiKeyAuth(None)), // Fail open for optional auth
        }
    }
}

