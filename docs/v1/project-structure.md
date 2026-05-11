```
backend/app
│
├── main.py                                      # FastAPI app init, mounts all routers, registers middleware
├── config.py                                    # ← was config.conf — typed settings via pydantic-settings, reads .env
│
├── api/
│   ├── dependencies.py                          # ← absorbs routerProvider.py — shared Depends(): db session, current user, engine injection
│   ├── middleware/
│   │   ├── logging.py                           # request/response logging middleware
│   │   ├── timing.py                            # injects X-Process-Time header on every response
│   │   └── cors.py                              # CORS rules as code rather than inline kwargs in main.py
│   │
│   └── v1/
│       ├── router.py                            # ← was apiV1.py — mounts all v1 sub-routers under /v1
│       │
│       ├── events/                              # ← was client.py + entities_router.py split across these
│       │   ├── __init__.py
│       │   ├── router.py                        # mounts list/query/detail/bulk under /v1/events
│       │   ├── list.py                          # GET  /events — quick filtered list via query params
│       │   ├── query.py                         # POST /events/query — full EventQuery body
│       │   ├── detail.py                        # GET  /events/{uuid} — single dataset
│       │   └── bulk.py                          # POST /events/bulk — fetch multiple by uuid list
│       │
│       ├── auth/                                # ← was auth_router.py split across these
│       │   ├── router.py                        # mounts login/token under /v1/auth
│       │   ├── login.py                         # POST /auth/login — returns token pair
│       │   └── token.py                         # POST /auth/refresh — refreshes access token
│       │
│       ├── navigation/                          # ← was navigation_router.py split across these
│       │   ├── router.py                        # mounts FK lookup endpoints under /v1/navigation
│       │   ├── campaigns.py                     # GET /navigation/campaigns — list valid campaign names
│       │   ├── detectors.py                     # GET /navigation/detectors
│       │   ├── accelerators.py                  # GET /navigation/accelerators
│       │   └── stages.py                        # GET /navigation/stages
│       │
│       ├── search/
│       │   ├── router.py                        # mounts search endpoints under /v1/search
│       │   ├── fulltext.py                      # GET  /search?q= — fuzzy search over name/description/comment
│       │   ├── similar.py                       # GET  /events/{uuid}/similar — same process, different ecm or generator
│       │   └── suggest.py                       # GET  /search/suggest — autocomplete on field values
│       │
│       ├── analytics/
│       │   ├── router.py                        # mounts analytics endpoints under /v1/analytics
│       │   ├── histogram.py                     # POST /analytics/histogram — distribution of any numeric field
│       │   ├── summary.py                       # POST /analytics/summary — count/sum/mean grouped by field
│       │   ├── compare.py                       # POST /analytics/compare — delta report between two dataset groups
│       │   └── coverage.py                      # GET  /analytics/coverage — phase space map: which (process, ecm) exist
│       │
│       ├── collections/
│       │   ├── router.py                        # mounts collection endpoints under /v1/collections
│       │   ├── list.py                          # GET    /collections — user's saved collections
│       │   ├── create.py                        # POST   /collections
│       │   ├── detail.py                        # GET    /collections/{id}
│       │   └── membership.py                    # POST   /collections/{id}/events — add/remove datasets
│       │
│       ├── jobs/
│       │   ├── router.py                        # mounts async job endpoints under /v1/jobs
│       │   ├── submit.py                        # POST /jobs — submit long export or heavy analytics
│       │   ├── status.py                        # GET  /jobs/{id} — poll job state
│       │   └── result.py                        # GET  /jobs/{id}/result — retrieve completed output
│       │
│       └── export/
│           ├── router.py                        # mounts export endpoints under /v1/export
│           ├── yaml.py                          # GET /export/yaml — FCCAnalyses processList format
│           ├── python.py                        # GET /export/python — ready-to-paste Python dict literal
│           └── csv.py                           # GET /export/csv
│
├── models/                                      # Pydantic only — API contract, validation, serialization
│   ├── common.py                                # ← was generic.py — PaginatedResponse, ErrorEnvelope, SortOrder
│   │
│   ├── auth/
│   │   ├── __init__.py
│   │   ├── credentials.py                       # LoginRequest (username + password)
│   │   ├── token.py                             # TokenResponse, TokenPayload (JWT claims: sub, exp, scopes)
│   │   └── user.py                              # User (public), UserInDB (includes hashed_password)
│   │
│   ├── event/
│   │   ├── __init__.py
│   │   ├── query.py                             # ← was queryModel.py — EventQuery, EventFields, EventFilters, EventOptions
│   │   ├── response.py                          # EventResponse (full), EventSummary (light projection for list endpoints)
│   │   └── name.py                              # DatasetNameComponents — parsed fields from dataset name string
│   │
│   ├── navigation/
│   │   ├── __init__.py
│   │   ├── accelerator.py                       # AcceleratorResponse
│   │   ├── campaign.py                          # CampaignResponse
│   │   ├── detector.py                          # DetectorResponse
│   │   └── stage.py                             # StageResponse
│   │
│   ├── search/
│   │   ├── __init__.py
│   │   ├── query.py                             # FulltextQuery, SuggestQuery
│   │   └── response.py                          # SearchHit (result + relevance score + matched fields)
│   │
│   ├── analytics/
│   │   ├── __init__.py
│   │   ├── histogram.py                         # HistogramRequest, Bin, HistogramResponse
│   │   ├── summary.py                           # SummaryRequest, GroupedSummary
│   │   └── compare.py                           # CompareRequest, DeltaReport
│   │
│   ├── collections/
│   │   ├── __init__.py
│   │   ├── collection.py                        # Collection, CollectionCreate, CollectionUpdate
│   │   └── membership.py                        # CollectionMembership, MembershipUpdate
│   │
│   ├── jobs/
│   │   ├── __init__.py
│   │   ├── job.py                               # Job, JobStatus enum (pending/running/done/failed)
│   │   └── result.py                            # JobResult — generic wrapper around any completed payload
│   │
│   └── export/
│       ├── __init__.py
│       └── format.py                            # ExportFormat enum, ExportRequest
│
├── engine/                                      # Pure logic — no I/O, no HTTP, fully unit-testable
│   │
│   ├── query/
│   │   ├── __init__.py
│   │   ├── engine.py                            # EventQueryEngine — orchestrates resolver + parser + builder
│   │   ├── field_resolver.py                    # ← absorbs part of gclql_query_parser_utils.py — FK name → id
│   │   ├── filter_parser.py                     # RangeFilter / set membership → typed FilterPredicate
│   │   └── option_builder.py                    # limit/offset/sort → SQL-ready options struct
│   │
│   ├── parsing/
│   │   ├── __init__.py
│   │   ├── name_parser.py                       # ← absorbs parsing_utils.py — "wzp6_gammae_eZ_Zqq_ecm365" → DatasetNameComponents
│   │   ├── process_parser.py                    # "gammae_eZ_Zqq" → initial_state / hard_process / decay_channel
│   │   └── generator_registry.py                # "wz"→Whizard, "p6"→Pythia6, "p8"→Pythia8, "mg5"→MadGraph5 …
│   │
│   ├── search/
│   │   ├── __init__.py
│   │   ├── fulltext_engine.py                   # ← absorbs search_module.py — tokenises, scores, ranks
│   │   ├── similarity_engine.py                 # finds related datasets by process/ecm proximity
│   │   └── suggest_engine.py                    # prefix matching for autocomplete
│   │
│   ├── analytics/
│   │   ├── __init__.py
│   │   ├── histogram_engine.py                  # bins a numeric field across a result set
│   │   ├── summary_engine.py                    # group-by + aggregation (count, sum, mean, weighted xsec)
│   │   ├── compare_engine.py                    # computes deltas and ratios between two dataset groups
│   │   └── coverage_engine.py                   # builds ecm × process phase space matrix
│   │
│   └── export/
│       ├── __init__.py
│       ├── yaml_formatter.py                    # EventResponse → FCCAnalyses processList YAML block
│       ├── python_formatter.py                  # EventResponse → Python dict literal for notebooks
│       └── csv_formatter.py                     # EventResponse → CSV rows
│
├── services/                                    # Orchestration — calls engine + repository, owns use-case logic
│   ├── event_service.py                         # query → engine.resolve → repo.fetch → EventResponse
│   ├── navigation_service.py                    # serves FK lookup tables to API and engine
│   ├── import_service.py                        # ← absorbs data_import_module.py + schema_discovery.py — ingests datasets, validates via name_parser
│   ├── file_watcher.py                          # ← stays — watches EOS/local paths, triggers import_service
│   ├── search_service.py                        # orchestrates fulltext + similarity engines over repo results
│   ├── analytics_service.py                     # orchestrates analytics engines, handles caching of heavy aggregations
│   ├── collection_service.py                    # CRUD for user-owned dataset collections
│   ├── export_service.py                        # selects formatter, handles streaming for large outputs
│   └── job_service.py                           # submits tasks to worker queue, tracks and exposes job state
│
├── repository/                                  # Data access only — SQL in, plain dicts/ORM objects out
│   ├── base.py                                  # ← absorbs database.py + sql_utils.py — engine, session factory, get_db, Base
│   ├── schema.sql                               # ← was database.sql — canonical schema definition
│   │
│   ├── orm/                                     # ← absorbs json_data_model.py + schema_mapping_module.py
│   │   ├── __init__.py
│   │   ├── event.py                             # EventORM — maps to the main datasets table
│   │   ├── user.py                              # UserORM
│   │   ├── collection.py                        # CollectionORM, CollectionMembershipORM
│   │   ├── job.py                               # JobORM (id, status, payload JSONB, result JSONB)
│   │   └── navigation/
│   │       ├── __init__.py
│   │       ├── accelerator.py                   # AcceleratorORM
│   │       ├── campaign.py                      # CampaignORM
│   │       ├── detector.py                      # DetectorORM
│   │       └── stage.py                         # StageORM
│   │
│   ├── event/
│   │   ├── __init__.py
│   │   ├── read.py                              # ← absorbs entity_retrieval_module.py — SELECT, filter assembly, post-filter for JSON/derived fields
│   │   └── write.py                             # ← absorbs entity_management_module.py — INSERT, UPDATE, soft-delete
│   │
│   ├── collection/
│   │   ├── __init__.py
│   │   ├── read.py                              # fetch collections by user, by id
│   │   └── write.py                             # create, update, delete collections and memberships
│   │
│   ├── job/
│   │   ├── __init__.py
│   │   ├── read.py                              # fetch job by id, list jobs by user
│   │   └── write.py                             # create job, update status, store result
│   │
│   ├── navigation/                              # ← absorbs navigation_module.py split across these
│   │   ├── __init__.py
│   │   ├── accelerator.py                       # fetch all accelerators, resolve name → id
│   │   ├── campaign.py
│   │   ├── detector.py
│   │   └── stage.py
│   │
│   └── data/
│       └── en4.json                             # ← was storage/data/en4.json — seed/reference data for import
│
├── workers/                                     # Async task execution — runs outside the request cycle
│   ├── __init__.py
│   ├── config.py                                # broker URL, queue names, concurrency settings
│   ├── tasks/
│   │   ├── export_task.py                       # large exports (500+ datasets) run here via job queue
│   │   ├── analytics_task.py                    # heavy aggregations that would time out in HTTP
│   │   └── import_task.py                       # bulk ingest triggered by file_watcher
│   └── registry.py                              # maps task name string → callable, used by job_service
│
└── utils/                                       # Stateless, domain-agnostic helpers — no imports from models/ or engine/
    ├── auth.py                                  # ← was auth_utils.py — JWT encode/decode, password hashing
    ├── logging.py                               # ← was logging_utils.py — structured log formatter, get_logger
    ├── errors.py                                # ← was errors_utils.py — HTTPException subclasses, error envelope builder
    ├── pagination.py                            # offset/limit → slice, build PaginatedResponse
    ├── http.py                                  # ← was http_client_utils.py — httpx client wrapper for outbound calls (EOS, CVMFS)
    ├── uuid.py                                  # ← was uuid_utils.py — generate, validate, normalise UUIDs
    └── config.py                                # ← was config_utils.py — helpers for reading config.py values safely
```