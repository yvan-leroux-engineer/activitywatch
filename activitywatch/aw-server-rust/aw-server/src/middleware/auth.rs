// JWT Authentication middleware for Rocket
// Note: Authentication is optional and can be enabled via feature flag
// For now, we'll make it optional to maintain backward compatibility

use rocket::request::{FromRequest, Outcome, Request};
use rocket::http::Status;
use jsonwebtoken::{decode, DecodingKey, Validation, Algorithm};
use serde::{Deserialize, Serialize};
use std::env;

#[derive(Debug, Serialize, Deserialize)]
pub struct Claims {
    pub user_id: String,
    pub roles: Vec<String>,
    pub exp: usize,
}

pub struct AuthenticatedUser {
    pub user_id: String,
    pub roles: Vec<String>,
}

#[derive(Debug)]
pub enum AuthError {
    Missing,
    Invalid,
    Expired,
}

#[rocket::async_trait]
impl<'r> FromRequest<'r> for AuthenticatedUser {
    type Error = AuthError;

    async fn from_request(request: &'r Request<'_>) -> Outcome<Self, Self::Error> {
        // Check if authentication is enabled via environment variable
        let auth_enabled = env::var("AUTH_ENABLED")
            .map(|v| v == "true")
            .unwrap_or(false);

        // If auth is disabled, allow all requests (backward compatibility)
        if !auth_enabled {
            return Outcome::Success(AuthenticatedUser {
                user_id: "anonymous".to_string(),
                roles: vec!["public".to_string()],
            });
        }

        // Extract token from Authorization header
        let auth_header = request.headers().get_one("Authorization");
        let token = match auth_header {
            Some(header) => {
                if header.starts_with("Bearer ") {
                    &header[7..]
                } else {
                    return Outcome::Error((Status::Unauthorized, AuthError::Missing));
                }
            }
            None => return Outcome::Error((Status::Unauthorized, AuthError::Missing)),
        };

        // Get JWT secret from environment
        let secret = env::var("JWT_SECRET")
            .expect("JWT_SECRET environment variable is required when AUTH_ENABLED=true");

        // Decode and validate token
        let validation = Validation::new(Algorithm::HS256);
        match decode::<Claims>(
            token,
            &DecodingKey::from_secret(secret.as_ref()),
            &validation,
        ) {
            Ok(token_data) => {
                Outcome::Success(AuthenticatedUser {
                    user_id: token_data.claims.user_id,
                    roles: token_data.claims.roles,
                })
            }
            Err(_) => Outcome::Error((Status::Unauthorized, AuthError::Invalid)),
        }
    }
}

// Helper function to create JWT token (for login endpoint)
pub fn create_token(user_id: &str, roles: Vec<String>) -> Result<String, jsonwebtoken::errors::Error> {
    let secret = env::var("JWT_SECRET")
        .expect("JWT_SECRET environment variable is required");
    
    let expiration = chrono::Utc::now()
        .checked_add_signed(chrono::Duration::hours(24))
        .expect("Failed to calculate expiration")
        .timestamp() as usize;

    let claims = Claims {
        user_id: user_id.to_string(),
        roles,
        exp: expiration,
    };

    jsonwebtoken::encode(
        &jsonwebtoken::Header::new(Algorithm::HS256),
        &claims,
        &jsonwebtoken::EncodingKey::from_secret(secret.as_ref()),
    )
}

