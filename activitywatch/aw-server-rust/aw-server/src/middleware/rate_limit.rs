// Rate limiting middleware
// Note: Rate limiting is optional and can be enabled via environment variable
// For now, using in-memory cache. Redis integration can be added later.

use std::collections::HashMap;
use std::sync::Mutex;
use std::time::{Duration, SystemTime, UNIX_EPOCH};
use rocket::fairing::{Fairing, Info, Kind};
use rocket::{Request, Response};
use rocket::http::Status;
use std::env;

lazy_static::lazy_static! {
    static ref RATE_LIMIT_CACHE: Mutex<HashMap<String, Vec<SystemTime>>> = Mutex::new(HashMap::new());
}

pub struct RateLimiter {
    pub requests_per_minute: u32,
    pub window_seconds: u64,
}

impl RateLimiter {
    pub fn new(requests_per_minute: u32) -> Self {
        Self {
            requests_per_minute,
            window_seconds: 60,
        }
    }

    fn check_rate_limit(&self, key: &str) -> bool {
        let mut cache = RATE_LIMIT_CACHE.lock().unwrap();
        let now = SystemTime::now();
        let window_start = now
            .checked_sub(Duration::from_secs(self.window_seconds))
            .unwrap_or(UNIX_EPOCH);

        // Get or create entry for this key
        let requests = cache.entry(key.to_string()).or_insert_with(Vec::new);

        // Remove old requests outside the window
        requests.retain(|&time| time > window_start);

        // Check if limit exceeded
        if requests.len() >= self.requests_per_minute as usize {
            false
        } else {
            requests.push(now);
            true
        }
    }
}

#[rocket::async_trait]
impl Fairing for RateLimiter {
    fn info(&self) -> Info {
        Info {
            name: "Rate Limiter",
            kind: Kind::Request,
        }
    }

    async fn on_request(&self, request: &mut Request<'_>, _: &mut rocket::Data<'_>) {
        // Check if rate limiting is enabled
        let rate_limit_enabled = env::var("RATE_LIMIT_ENABLED")
            .map(|v| v == "true")
            .unwrap_or(false);

        if !rate_limit_enabled {
            return;
        }

        // Get client IP
        let client_ip = request
            .client_ip()
            .map(|ip| ip.to_string())
            .unwrap_or_else(|| "unknown".to_string());

        // Check rate limit
        if !self.check_rate_limit(&client_ip) {
            // Rate limit exceeded - we'll handle this in the response
            request.local_cache(|| Status::TooManyRequests);
        }
    }

    async fn on_response<'r>(&self, request: &'r Request<'_>, response: &mut Response<'r>) {
        // Check if rate limit was exceeded
        if let Some(status) = request.local_cache(|| None::<Status>) {
            if *status == Status::TooManyRequests {
                response.set_status(Status::TooManyRequests);
                response.set_header(rocket::http::ContentType::Plain);
                response.set_sized_body("Rate limit exceeded".len(), std::io::Cursor::new("Rate limit exceeded"));
            }
        }
    }
}

