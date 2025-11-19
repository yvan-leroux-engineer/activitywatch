#[macro_use]
extern crate log;

#[macro_export]
macro_rules! json_map {
    { $( $key:literal : $value:expr),* } => {{
        use serde_json::Value;
        use serde_json::map::Map;
        #[allow(unused_mut)]
        let mut map : Map<String, Value> = Map::new();
        $(
          map.insert( $key.to_string(), json!($value) );
        )*
        map
    }};
}

mod worker;
mod postgres_helpers;
pub mod api_key_helpers;

pub use self::worker::Datastore;

#[derive(Debug, Clone)]
pub enum DatastoreMethod {
    Postgres(String), // PostgreSQL connection string (only supported method)
}

/* TODO: Implement this as a proper error */
#[derive(Debug, Clone)]
pub enum DatastoreError {
    NoSuchBucket(String),
    BucketAlreadyExists(String),
    NoSuchKey(String),
    MpscError,
    InternalError(String),
    // Errors specific to when migrate is disabled
    Uninitialized(String),
    OldDbVersion(String),
}
