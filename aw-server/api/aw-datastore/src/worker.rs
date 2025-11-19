use std::collections::HashMap;
use std::fmt;
use std::thread;

use chrono::DateTime;
use chrono::Duration;
use chrono::Utc;

use aw_models::Bucket;
use aw_models::Event;

use crate::DatastoreError;
use crate::DatastoreMethod;
use crate::postgres_helpers;

use mpsc_requests::ResponseReceiver;
use sqlx::PgPool;

type RequestSender = mpsc_requests::RequestSender<Command, Result<Response, DatastoreError>>;
type RequestReceiver = mpsc_requests::RequestReceiver<Command, Result<Response, DatastoreError>>;

#[derive(Clone)]
pub struct Datastore {
    requester: RequestSender,
}

impl fmt::Debug for Datastore {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        write!(f, "Datastore()")
    }
}

/*
 * TODO:
 * - Allow read requests to go straight through a read-only db connection instead of requesting the
 * worker thread for better performance?
 * TODO: Add an separate "Import" request which does an import with an transaction
 */

#[allow(clippy::large_enum_variant)]
#[derive(Debug, Clone)]
pub enum Response {
    Empty(),
    Bucket(Bucket),
    BucketMap(HashMap<String, Bucket>),
    Event(Event),
    EventList(Vec<Event>),
    Count(i64),
    KeyValue(String),
    KeyValues(HashMap<String, String>),
}

#[allow(clippy::large_enum_variant)]
#[derive(Debug, Clone)]
pub enum Command {
    CreateBucket(Bucket),
    DeleteBucket(String),
    GetBucket(String),
    GetBuckets(),
    InsertEvents(String, Vec<Event>),
    Heartbeat(String, Event, f64),
    GetEvent(String, i64),
    GetEvents(
        String,
        Option<DateTime<Utc>>,
        Option<DateTime<Utc>>,
        Option<u64>,
    ),
    GetEventCount(String, Option<DateTime<Utc>>, Option<DateTime<Utc>>),
    DeleteEventsById(String, Vec<i64>),
    ForceCommit(),
    GetKeyValues(String),
    GetKeyValue(String),
    SetKeyValue(String, String),
    DeleteKeyValue(String),
    Close(),
}

fn _unwrap_response(
    receiver: ResponseReceiver<Result<Response, DatastoreError>>,
) -> Result<(), DatastoreError> {
    match receiver.collect().unwrap() {
        Ok(r) => match r {
            Response::Empty() => Ok(()),
            _ => panic!("Invalid response"),
        },
        Err(e) => Err(e),
    }
}

struct DatastoreWorker {
    responder: RequestReceiver,
    legacy_import: bool,
    quit: bool,
    uncommitted_events: usize,
    commit: bool,
    last_heartbeat: HashMap<String, Option<Event>>,
}

impl DatastoreWorker {
    pub fn new(
        responder: mpsc_requests::RequestReceiver<Command, Result<Response, DatastoreError>>,
        legacy_import: bool,
    ) -> Self {
        DatastoreWorker {
            responder,
            legacy_import,
            quit: false,
            uncommitted_events: 0,
            commit: false,
            last_heartbeat: HashMap::new(),
        }
    }

    fn work_loop(&mut self, method: DatastoreMethod) {
        match method {
            DatastoreMethod::Postgres(connection_string) => {
                self.work_loop_postgres(connection_string);
            }
        }
    }

    fn work_loop_postgres(&mut self, connection_string: String) {
        // Create tokio runtime for async PostgreSQL operations
        let rt = tokio::runtime::Runtime::new().expect("Failed to create tokio runtime");
        
        // Create PostgreSQL connection pool
        let pool = rt.block_on(async {
            sqlx::PgPool::connect(&connection_string)
                .await
                .expect("Failed to connect to PostgreSQL database")
        });

        // Run migrations
        rt.block_on(async {
            // SQLx migrations - migrations directory is relative to crate root
            // The migrate! macro embeds migrations at compile time
            // Migrations are copied to ./aw-datastore/migrations in Docker
            // We use the compile-time macro which knows the path at build time
            match sqlx::migrate!("./migrations").run(&pool).await {
                Ok(_) => info!("Database migrations completed successfully"),
                Err(e) => {
                    error!("Failed to run database migrations: {}", e);
                    // Don't panic - migrations might already be applied
                    warn!("Migration error (may be harmless if already applied): {}", e);
                }
            }
        });

        // Load buckets into cache
        let mut buckets_cache = rt.block_on(async {
            postgres_helpers::get_stored_buckets(&pool).await.unwrap()
        });

        // Start handling and respond to requests
        loop {
            let last_commit_time: DateTime<Utc> = Utc::now();
            self.uncommitted_events = 0;
            self.commit = false;

            loop {
                let (request, response_sender) = match self.responder.poll() {
                    Ok((req, res_sender)) => (req, res_sender),
                    Err(err) => {
                        error!("DB worker quitting, error: {err:?}");
                        self.quit = true;
                        break;
                    }
                };
                
                let response = rt.block_on(async {
                    self.handle_request_postgres(request, &pool, &mut buckets_cache).await
                });
                
                response_sender.respond(response);

                let now: DateTime<Utc> = Utc::now();
                let commit_interval_passed: bool = (now - last_commit_time) > Duration::seconds(15);
                if self.commit
                    || commit_interval_passed
                    || self.uncommitted_events > 100
                    || self.quit
                {
                    break;
                };
            }

            debug!(
                "Commit cycle completed. Force commit {}, {} uncommitted events",
                self.commit, self.uncommitted_events
            );

            if self.quit {
                break;
            };
        }
        info!("DB Worker thread finished");
    }

    async fn handle_request_postgres(
        &mut self,
        request: Command,
        pool: &PgPool,
        buckets_cache: &mut HashMap<String, Bucket>,
    ) -> Result<Response, DatastoreError> {
        match request {
            Command::CreateBucket(mut bucket) => {
                match postgres_helpers::create_bucket(pool, &mut bucket).await {
                    Ok(_) => {
                        buckets_cache.insert(bucket.id.clone(), bucket.clone());
                        self.commit = true;
                        Ok(Response::Empty())
                    }
                    Err(e) => Err(e),
                }
            }
            Command::DeleteBucket(bucketname) => {
                match postgres_helpers::delete_bucket(pool, &bucketname).await {
                    Ok(_) => {
                        buckets_cache.remove(&bucketname);
                        self.commit = true;
                        Ok(Response::Empty())
                    }
                    Err(e) => Err(e),
                }
            }
            Command::GetBucket(bucketname) => {
                match buckets_cache.get(&bucketname) {
                    Some(bucket) => Ok(Response::Bucket(bucket.clone())),
                    None => Err(DatastoreError::NoSuchBucket(bucketname)),
                }
            }
            Command::GetBuckets() => Ok(Response::BucketMap(buckets_cache.clone())),
            Command::InsertEvents(bucketname, mut events) => {
                match postgres_helpers::insert_events(pool, &bucketname, &mut events).await {
                    Ok(inserted_events) => {
                        self.uncommitted_events += inserted_events.len();
                        self.last_heartbeat.insert(bucketname.to_string(), None);
                        Ok(Response::EventList(inserted_events))
                    }
                    Err(e) => Err(e),
                }
            }
            Command::Heartbeat(bucketname, event, pulsetime) => {
                // Get last heartbeat from cache or database
                let last_event_opt = if let Some(cached) = self.last_heartbeat.get(&bucketname) {
                    cached.clone()
                } else {
                    let mut events = postgres_helpers::get_events(pool, &bucketname, None, None, Some(1)).await?;
                    events.pop()
                };

                let merged_event = match last_event_opt {
                    Some(last_event) => {
                        match aw_transform::heartbeat(&last_event, &event, pulsetime) {
                            Some(merged) => {
                                postgres_helpers::replace_last_event(pool, &bucketname, &merged).await?;
                                merged
                            }
                            None => {
                                let mut events_vec = vec![event.clone()];
                                let inserted = postgres_helpers::insert_events(pool, &bucketname, &mut events_vec).await?;
                                inserted.into_iter().next().unwrap_or(event)
                            }
                        }
                    }
                    None => {
                        let mut events_vec = vec![event.clone()];
                        let inserted = postgres_helpers::insert_events(pool, &bucketname, &mut events_vec).await?;
                        inserted.into_iter().next().unwrap_or(event)
                    }
                };

                self.uncommitted_events += 1;
                self.last_heartbeat.insert(bucketname.to_string(), Some(merged_event.clone()));
                Ok(Response::Event(merged_event))
            }
            Command::GetEvent(bucketname, event_id) => {
                match postgres_helpers::get_event(pool, &bucketname, event_id).await {
                    Ok(event) => Ok(Response::Event(event)),
                    Err(e) => Err(e),
                }
            }
            Command::GetEvents(bucketname, starttime_opt, endtime_opt, limit_opt) => {
                match postgres_helpers::get_events(pool, &bucketname, starttime_opt, endtime_opt, limit_opt).await {
                    Ok(events) => Ok(Response::EventList(events)),
                    Err(e) => Err(e),
                }
            }
            Command::GetEventCount(bucketname, starttime_opt, endtime_opt) => {
                match postgres_helpers::get_event_count(pool, &bucketname, starttime_opt, endtime_opt).await {
                    Ok(count) => Ok(Response::Count(count)),
                    Err(e) => Err(e),
                }
            }
            Command::DeleteEventsById(bucketname, event_ids) => {
                match postgres_helpers::delete_events_by_id(pool, &bucketname, event_ids).await {
                    Ok(_) => Ok(Response::Empty()),
                    Err(e) => Err(e),
                }
            }
            Command::ForceCommit() => {
                self.commit = true;
                Ok(Response::Empty())
            }
            Command::GetKeyValues(pattern) => {
                match postgres_helpers::get_key_values(pool, &pattern).await {
                    Ok(result) => Ok(Response::KeyValues(result)),
                    Err(e) => Err(e),
                }
            }
            Command::SetKeyValue(key, data) => {
                match postgres_helpers::set_key_value(pool, &key, &data).await {
                    Ok(_) => Ok(Response::Empty()),
                    Err(e) => Err(e),
                }
            }
            Command::GetKeyValue(key) => {
                match postgres_helpers::get_key_value(pool, &key).await {
                    Ok(result) => Ok(Response::KeyValue(result)),
                    Err(e) => Err(e),
                }
            }
            Command::DeleteKeyValue(key) => {
                match postgres_helpers::delete_key_value(pool, &key).await {
                    Ok(_) => Ok(Response::Empty()),
                    Err(e) => Err(e),
                }
            }
            Command::Close() => {
                self.quit = true;
                Ok(Response::Empty())
            }
        }
    }

    // Legacy SQLite handle_request removed - PostgreSQL only
}

impl Datastore {
    pub fn new(dbpath: String, _legacy_import: bool) -> Self {
        // dbpath must be a PostgreSQL connection string
        if !dbpath.starts_with("postgresql://") {
            panic!("Only PostgreSQL connection strings are supported. Expected format: postgresql://user:password@host:port/database");
        }
        let method = DatastoreMethod::Postgres(dbpath);
        Datastore::_new_internal(method, false) // legacy_import always false for PostgreSQL
    }

    pub fn new_postgres(connection_string: String, _legacy_import: bool) -> Self {
        let method = DatastoreMethod::Postgres(connection_string);
        Datastore::_new_internal(method, false) // legacy_import always false for PostgreSQL
    }

    fn _new_internal(method: DatastoreMethod, legacy_import: bool) -> Self {
        let (requester, responder) =
            mpsc_requests::channel::<Command, Result<Response, DatastoreError>>();
        let _thread = thread::spawn(move || {
            let mut di = DatastoreWorker::new(responder, legacy_import);
            di.work_loop(method);
        });
        Datastore { requester }
    }

    pub fn create_bucket(&self, bucket: &Bucket) -> Result<(), DatastoreError> {
        let cmd = Command::CreateBucket(bucket.clone());
        let receiver = self.requester.request(cmd).unwrap();
        match receiver.collect().unwrap() {
            Ok(_) => Ok(()),
            Err(e) => Err(e),
        }
    }

    pub fn delete_bucket(&self, bucket_id: &str) -> Result<(), DatastoreError> {
        let cmd = Command::DeleteBucket(bucket_id.to_string());
        let receiver = self.requester.request(cmd).unwrap();
        match receiver.collect().unwrap() {
            Ok(r) => match r {
                Response::Empty() => Ok(()),
                _ => panic!("Invalid response"),
            },
            Err(e) => Err(e),
        }
    }

    pub fn get_bucket(&self, bucket_id: &str) -> Result<Bucket, DatastoreError> {
        let cmd = Command::GetBucket(bucket_id.to_string());
        let receiver = self.requester.request(cmd).unwrap();
        match receiver.collect().unwrap() {
            Ok(r) => match r {
                Response::Bucket(b) => Ok(b),
                _ => panic!("Invalid response"),
            },
            Err(e) => Err(e),
        }
    }

    pub fn get_buckets(&self) -> Result<HashMap<String, Bucket>, DatastoreError> {
        let cmd = Command::GetBuckets();
        let receiver = self.requester.request(cmd).unwrap();
        match receiver.collect().unwrap() {
            Ok(r) => match r {
                Response::BucketMap(bm) => Ok(bm),
                e => Err(DatastoreError::InternalError(format!(
                    "Invalid response: {e:?}"
                ))),
            },
            Err(e) => Err(e),
        }
    }

    pub fn insert_events(
        &self,
        bucket_id: &str,
        events: &[Event],
    ) -> Result<Vec<Event>, DatastoreError> {
        let cmd = Command::InsertEvents(bucket_id.to_string(), events.to_vec());
        let receiver = self.requester.request(cmd).unwrap();
        match receiver.collect().unwrap() {
            Ok(r) => match r {
                Response::EventList(events) => Ok(events),
                _ => panic!("Invalid response"),
            },
            Err(e) => Err(e),
        }
    }

    pub fn heartbeat(
        &self,
        bucket_id: &str,
        heartbeat: Event,
        pulsetime: f64,
    ) -> Result<Event, DatastoreError> {
        let cmd = Command::Heartbeat(bucket_id.to_string(), heartbeat, pulsetime);
        let receiver = self.requester.request(cmd).unwrap();
        match receiver.collect().unwrap() {
            Ok(r) => match r {
                Response::Event(e) => Ok(e),
                _ => panic!("Invalid response"),
            },
            Err(e) => Err(e),
        }
    }

    pub fn get_event(&self, bucket_id: &str, event_id: i64) -> Result<Event, DatastoreError> {
        let cmd = Command::GetEvent(bucket_id.to_string(), event_id);
        let receiver = self.requester.request(cmd).unwrap();
        match receiver.collect().unwrap() {
            Ok(r) => match r {
                Response::Event(el) => Ok(el),
                _ => panic!("Invalid response"),
            },
            Err(e) => Err(e),
        }
    }

    pub fn get_events(
        &self,
        bucket_id: &str,
        starttime_opt: Option<DateTime<Utc>>,
        endtime_opt: Option<DateTime<Utc>>,
        limit_opt: Option<u64>,
    ) -> Result<Vec<Event>, DatastoreError> {
        let cmd = Command::GetEvents(bucket_id.to_string(), starttime_opt, endtime_opt, limit_opt);
        let receiver = self.requester.request(cmd).unwrap();
        match receiver.collect().unwrap() {
            Ok(r) => match r {
                Response::EventList(el) => Ok(el),
                _ => panic!("Invalid response"),
            },
            Err(e) => Err(e),
        }
    }

    pub fn get_event_count(
        &self,
        bucket_id: &str,
        starttime_opt: Option<DateTime<Utc>>,
        endtime_opt: Option<DateTime<Utc>>,
    ) -> Result<i64, DatastoreError> {
        let cmd = Command::GetEventCount(bucket_id.to_string(), starttime_opt, endtime_opt);
        let receiver = self.requester.request(cmd).unwrap();
        match receiver.collect().unwrap() {
            Ok(r) => match r {
                Response::Count(n) => Ok(n),
                _ => panic!("Invalid response"),
            },
            Err(e) => Err(e),
        }
    }

    pub fn delete_events_by_id(
        &self,
        bucket_id: &str,
        event_ids: Vec<i64>,
    ) -> Result<(), DatastoreError> {
        let cmd = Command::DeleteEventsById(bucket_id.to_string(), event_ids);
        let receiver = self.requester.request(cmd).unwrap();
        match receiver.collect().unwrap() {
            Ok(r) => match r {
                Response::Empty() => Ok(()),
                _ => panic!("Invalid response"),
            },
            Err(e) => Err(e),
        }
    }

    pub fn force_commit(&self) -> Result<(), DatastoreError> {
        let cmd = Command::ForceCommit();
        let receiver = self.requester.request(cmd).unwrap();
        match receiver.collect().unwrap() {
            Ok(r) => match r {
                Response::Empty() => Ok(()),
                _ => panic!("Invalid response"),
            },
            Err(e) => Err(e),
        }
    }

    pub fn get_key_values(&self, pattern: &str) -> Result<HashMap<String, String>, DatastoreError> {
        let cmd = Command::GetKeyValues(pattern.to_string());
        let receiver = self.requester.request(cmd).unwrap();

        match receiver.collect().unwrap() {
            Ok(r) => match r {
                Response::KeyValues(value) => Ok(value),
                _ => panic!("Invalid response"),
            },
            Err(e) => Err(e),
        }
    }

    pub fn get_key_value(&self, key: &str) -> Result<String, DatastoreError> {
        let cmd = Command::GetKeyValue(key.to_string());
        let receiver = self.requester.request(cmd).unwrap();

        match receiver.collect().unwrap() {
            Ok(r) => match r {
                Response::KeyValue(kv) => Ok(kv),
                _ => panic!("Invalid response"),
            },
            Err(e) => Err(e),
        }
    }

    pub fn set_key_value(&self, key: &str, data: &str) -> Result<(), DatastoreError> {
        let cmd = Command::SetKeyValue(key.to_string(), data.to_string());
        let receiver = self.requester.request(cmd).unwrap();

        _unwrap_response(receiver)
    }

    pub fn delete_key_value(&self, key: &str) -> Result<(), DatastoreError> {
        let cmd = Command::DeleteKeyValue(key.to_string());
        let receiver = self.requester.request(cmd).unwrap();

        _unwrap_response(receiver)
    }

    // Should block until worker has stopped
    pub fn close(&self) {
        info!("Sending close request to database");
        let receiver = self.requester.request(Command::Close()).unwrap();

        match receiver.collect().unwrap() {
            Ok(r) => match r {
                Response::Empty() => (),
                _ => panic!("Invalid response"),
            },
            Err(e) => panic!("Error closing database: {:?}", e),
        }
    }
}
