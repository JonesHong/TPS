# Translation Proxy System (TPS) Implementation Todo List

Based on `TranslationProxySystemSpecification.md` (v2.0).

**✅ 實作狀態：全部完成 (2025-12-05)**

## Phase 1: Project Initialization & Environment Setup ✅
- [x] **Initialize Project Structure**
    - [x] Create project directory layout (`src`, `tests`, `scripts`, `config`).
    - [x] Initialize Git repository.
    - [x] Create `.gitignore` (exclude `.env`, `*.db`, `__pycache__`, `venv`).
- [x] **Dependency Management**
    - [x] Create `pyproject.toml` (使用 uv 管理).
    - [x] Add core libraries: `fastapi`, `uvicorn`, `pydantic`.
    - [x] Add client libraries: `openai`, `deepl`, `google-cloud-translate`.
    - [x] Add utilities: `tiktoken`, `python-dotenv`, `aiosqlite`.
- [x] **Environment Configuration**
    - [x] Create `.env.example`.
    - [x] Set up `.env` loading logic.
    - [x] Define required variables:
        - `DEEPL_API_KEY`
        - `OPENAI_API_KEY`
        - `GOOGLE_APPLICATION_CREDENTIALS` (path to JSON)
        - `SQLITE_DB_PATH`
        - `DAILY_BUDGET_GOOGLE`
        - `DAILY_BUDGET_OPENAI`

## Phase 2: Database Layer (SQLite) ✅
- [x] **Database Connection & Configuration**
    - [x] Implement DB connection manager (`src/tps/db/connection.py`).
    - [x] **CRITICAL**: Apply PRAGMA settings on connect:
        - `PRAGMA journal_mode = WAL;`
        - `PRAGMA synchronous = NORMAL;`
        - `PRAGMA cache_size = -64000;`
        - `PRAGMA busy_timeout = 5000;`
- [x] **Schema Migration / Initialization**
    - [x] Create `translations` table (Cache Layer).
        - Columns: `cache_key`, `source_lang`, `target_lang`, `original_text`, `translated_text`, `provider`, `is_refined`, `refinement_model`, `char_count`, `created_at`, `last_accessed_at`, `expires_at`.
        - Primary Key: `cache_key`.
    - [x] Create `daily_usage_stats` table (Cost Control).
        - Columns: `date`, `provider`, `request_count`, `char_count`, `token_input`, `token_output`, `cost_estimated`.
        - Primary Key: Composite (`date`, `provider`).
    - [x] Create Indices:
        - `idx_cleanup` on `translations(last_accessed_at)`.
- [x] **Data Access Object (DAO)** (`src/tps/db/dao.py`)
    - [x] Implement `get_cached_translation(key)`.
    - [x] Implement `upsert_translation(...)`.
    - [x] Implement `update_last_accessed(key)`.
    - [x] Implement `get_daily_usage(date, provider)`.
    - [x] Implement `increment_usage_stats(...)`.

## Phase 3: API Client Wrappers (The "Tiers") ✅
- [x] **Tier 2: DeepL Client** (`src/tps/clients/deepl_client.py`)
    - [x] Implement `translate(text, source, target)`.
    - [x] Handle `QuotaExceededException` specifically (trigger failover).
    - [x] Map other errors to generic SystemError.
- [x] **Tier 3: OpenAI Client** (`src/tps/clients/openai_client.py`)
    - [x] Initialize `tiktoken` encoder for accurate counting.
    - [x] Implement `translate(text, source, target, model='gpt-4o-mini')`.
        - [x] Construct System/User prompts (JSON output).
        - [x] Parse JSON response.
    - [x] Implement `refine(original, draft, source, target, model)`.
    - [x] Handle `ContextWindowExceeded` and `RateLimitError`.
- [x] **Tier 4: Google Translate Client** (`src/tps/clients/google_client.py`)
    - [x] Implement `translate(text, source, target)`.
    - [x] Handle Authentication errors.

## Phase 4: Core Logic & Strategy Implementation ✅
- [x] **Key Generation** (`src/tps/core/key_generator.py`)
    - [x] Implement `generate_cache_key(text, source, target, format)`.
    - [x] Ensure normalization (strip whitespace) but preserve variables/tags.
- [x] **Cost Control & Circuit Breaker** (`src/tps/core/cost_control.py`)
    - [x] Implement `is_quota_exceeded(provider)`.
    - [x] Implement `is_budget_exceeded(provider)`.
        - [x] Logic for Google: `(char_count / 1M) * 20 > limit`.
        - [x] Logic for OpenAI: `(tokens * price) > limit`.
- [x] **Main Workflow** (`src/tps/core/workflow.py`)
    - [x] **Step 1**: Cache Lookup.
        - [x] Return immediately if hit AND (`!enable_refinement` OR `is_refined`).
    - [x] **Step 2**: Tier 2 (DeepL) attempt.
    - [x] **Step 3**: Tier 3 (OpenAI) fallback.
    - [x] **Step 4**: Tier 4 (Google) last resort.
    - [x] **Step 5**: Refinement (Optional).
        - [x] Check `enable_refinement` flag.
        - [x] Skip if provider was already OpenAI.
    - [x] **Step 6**: Save to DB & Update Stats.
- [x] **Response Standardization**
    - [x] Define standard JSON response structure (`success`, `data`, `error`).

## Phase 5: REST API Interface ✅
- [x] **API Setup** (`src/tps/app.py`, `src/tps/api/routes.py`)
    - [x] Create FastAPI app.
    - [x] Define Request Model (Pydantic): `text`, `source_lang`, `target_lang`, `format`, `enable_refinement`.
- [x] **Endpoints**
    - [x] `POST /translate`: Main entry point.
    - [x] `GET /health`: Simple health check.
    - [x] `GET /stats`: View current usage/cost.
    - [x] `GET /providers`: View provider availability.

## Phase 6: Operations & Maintenance ✅
- [x] **Logging**
    - [x] Configure structured logging.
    - [x] **Security Check**: Ensure PII (original text) is NOT logged in production logs.
- [x] **Maintenance Scripts**
    - [x] Create `scripts/cleanup_cache.py`: Delete entries older than 90 days.
    - [x] Create `scripts/vacuum_db.py`: Run `VACUUM`.
    - [x] Set up Cron jobs or Scheduler instructions (in README).

## Phase 7: Testing & QA ✅
- [x] **Unit Tests** (12 tests passing)
    - [x] Test Key Generation (hashing consistency).
    - [x] Test Cost Estimation formulas.
    - [x] Test Quota/Budget exceeded logic.
- [x] **Mock Tests**
    - [x] Mock DeepL failure -> Verify OpenAI called.
    - [x] Mock DeepL+OpenAI failure -> Verify Google called.
    - [x] Mock Budget Exceeded -> Verify request skipped to next tier.
    - [x] Mock Cache hit -> Verify no provider called.
- [x] **Test Configuration**
    - [x] pytest-asyncio setup.
    - [x] conftest.py with fixtures.
