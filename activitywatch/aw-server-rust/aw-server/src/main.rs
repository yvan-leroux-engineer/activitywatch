#[macro_use]
extern crate log;

use std::env;
use std::path::PathBuf;

use clap::crate_version;
use clap::Parser;
use sqlx::PgPool;

use aw_server::*;

#[cfg(target_os = "linux")]
use sd_notify::NotifyState;
#[cfg(all(target_os = "linux", target_arch = "x86"))]
extern crate jemallocator;
#[cfg(all(target_os = "linux", target_arch = "x86"))]
#[global_allocator]
static ALLOC: jemallocator::Jemalloc = jemallocator::Jemalloc;

/// Rust server for ActivityWatch
#[derive(Parser)]
#[clap(version = crate_version!(), author = "Johan Bjäreholt, Erik Bjäreholt, et al.")]
struct Opts {
    /// Run in testing mode
    #[clap(long)]
    testing: bool,

    /// Verbose output
    #[clap(long)]
    verbose: bool,

    /// Address to listen to
    #[clap(long)]
    host: Option<String>,

    /// Port to listen on
    #[clap(long)]
    port: Option<String>,

    /// Path to database override
    /// Also implies --no-legacy-import if no db found
    #[clap(long)]
    dbpath: Option<String>,

    /// Path to webui override
    #[clap(long)]
    webpath: Option<String>,

    /// Mapping of custom static paths to serve, in the format: watcher1=/path,watcher2=/path2
    #[clap(long)]
    custom_static: Option<String>,

    /// Device ID override
    #[clap(long)]
    device_id: Option<String>,

    /// Don't import from aw-server-python if no aw-server-rust db found
    #[clap(long)]
    no_legacy_import: bool,
}

#[rocket::main]
async fn main() -> Result<(), rocket::Error> {
    let opts: Opts = Opts::parse();

    use std::sync::Mutex;

    let mut testing = opts.testing;

    // Always override environment if --testing is specified
    if !testing && cfg!(debug_assertions) {
        testing = true;
    }

    logging::setup_logger("aw-server-rust", testing, opts.verbose)
        .expect("Failed to setup logging");

    if testing {
        info!("Running server in Testing mode");
    }

    let mut config = config::create_config(testing);

    // set host if overridden via command line
    if let Some(host) = opts.host {
        config.address = host;
    } else if let Ok(host) = env::var("API_HOST") {
        // Or from environment variable
        config.address = host;
    }

    // set port if overridden via command line
    if let Some(port) = opts.port {
        config.port = port.parse().unwrap();
    } else if let Ok(port) = env::var("API_PORT") {
        // Or from environment variable
        config.port = port.parse().unwrap_or_else(|_| {
            if testing { 5666 } else { 5600 }
        });
    }

    // set custom_static if overridden, transform into map
    if let Some(custom_static_str) = opts.custom_static {
        let custom_static_map: std::collections::HashMap<String, String> = custom_static_str
            .split(',')
            .map(|s| {
                let mut split = s.split('=');
                let key = split.next().unwrap().to_string();
                let value = split.next().unwrap().to_string();
                (key, value)
            })
            .collect();
        config.custom_static.extend(custom_static_map);

        // validate paths, log error if invalid
        // remove invalid paths
        for (name, path) in config.custom_static.clone().iter() {
            if !std::path::Path::new(path).exists() {
                error!("custom_static path for {} does not exist ({})", name, path);
                config.custom_static.remove(name);
            }
        }
    }

    // Get database connection string from environment or use dbpath
    let db_connection_string: String = if let Some(dbpath) = opts.dbpath.clone() {
        // If dbpath is provided and starts with postgresql://, use it directly
        if dbpath.starts_with("postgresql://") {
            dbpath
        } else {
            // Legacy SQLite path - not supported
            error!("SQLite database path is not supported. Use PostgreSQL connection string (postgresql://...)");
            panic!("SQLite is not supported in modernized version. Set DATABASE_URL environment variable with PostgreSQL connection string.");
        }
    } else {
        // Get from DATABASE_URL environment variable (required)
        env::var("DATABASE_URL")
            .expect("DATABASE_URL environment variable is required. Set it to a PostgreSQL connection string (e.g., postgresql://user:password@host:5432/database)")
    };
    // Log connection string with password masked
    let masked_connection = if let Some(at_pos) = db_connection_string.find('@') {
        format!("postgresql://***@{}", &db_connection_string[at_pos+1..])
    } else {
        "postgresql://***".to_string()
    };
    info!("Using PostgreSQL database: {}", masked_connection);

    let asset_path = opts.webpath.map(|webpath| PathBuf::from(webpath));
    info!("Using aw-webui assets at path {:?}", asset_path);

    // Legacy import is disabled for PostgreSQL (fresh start)
    let legacy_import = false;
    info!("Legacy import is disabled for PostgreSQL (fresh database start)");

    let device_id: String = if let Some(id) = opts.device_id {
        id
    } else {
        device_id::get_device_id()
    };

    // Create database pool for API key operations
    let db_pool = sqlx::PgPool::connect(&db_connection_string).await.ok();

    let server_state = endpoints::ServerState {
        datastore: Mutex::new(aw_datastore::Datastore::new(db_connection_string.clone(), legacy_import)),
        asset_resolver: endpoints::AssetResolver::new(asset_path),
        device_id,
        db_pool,
    };

    let _rocket = endpoints::build_rocket(server_state, config)
        .ignite()
        .await?;
    #[cfg(target_os = "linux")]
    let _ = sd_notify::notify(true, &[NotifyState::Ready]);
    _rocket.launch().await?;

    Ok(())
}
