# Tasks: Base do Backend e Infraestrutura Local

**Input**: Design documents from `specs/001-backend-base-infra/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/

**Tests**: Testes unitários para cada funcionalidade (TDD — testes escritos antes da implementação).

**Organization**: Tasks grouped by user story for independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Exact file paths included in descriptions

## Path Conventions

- **Package**: `app/` at repository root
- **Tests**: `tests/unit/` at repository root
- **Config**: root-level files (pyproject.toml, Dockerfile, docker-compose.yml, .env.example)

---

## Phase 1: Setup (Project Initialization)

**Purpose**: Create project skeleton, dependency management, and base configuration files

- [X] T001 Create `pyproject.toml` with project metadata, dependencies (fastapi, uvicorn, pydantic-settings, sqlalchemy, asyncpg, httpx, alembic, redis) and dev dependencies (pytest, pytest-asyncio, httpx, pytest-cov)
- [X] T002 Create `.gitignore` with Python, Docker, IDE, and env exclusions
- [X] T003 [P] Create directory structure with `__init__.py` files: `app/`, `app/api/`, `app/api/routes/`, `app/api/v1/`, `app/api/v1/routes/`, `app/services/`, `app/providers/`, `app/providers/evolution/`, `app/models/`, `app/schemas/`, `app/core/`
- [X] T004 [P] Create directory structure: `alembic/`, `alembic/versions/`, `scripts/`, `tests/`, `tests/unit/`, `tests/integration/`
- [X] T005 [P] Create `.env.example` with all required environment variables and example values
- [X] T006 [P] Create `tests/unit/conftest.py` with shared fixtures (mock env vars via monkeypatch, async_client factory with httpx.AsyncClient)

**Checkpoint**: Project skeleton created, `uv sync` installs dependencies without errors

---

## Phase 2: Foundational (Core Infrastructure)

**Purpose**: Core modules that ALL user stories depend on — MUST complete before story implementation

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Tests for Foundational Phase

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T007 [P] Unit test for config module in `tests/unit/test_config.py` — test default values (APP_ENV=development, APP_PORT=8000, LOG_LEVEL=INFO), test validation rejects invalid APP_ENV, test validation rejects invalid LOG_LEVEL, test missing required var raises ValidationError
- [X] T008 [P] Unit test for logging module in `tests/unit/test_logging.py` — test JSON format when APP_ENV=production, test text format when APP_ENV=development, test LOG_LEVEL is respected

### Implementation for Foundational Phase

- [X] T009 Implement `app/core/config.py` with Pydantic BaseSettings (AppSettings class, all env vars, validators for APP_ENV/LOG_LEVEL/APP_PORT/HTTP_TIMEOUT/DATABASE_URL)
- [X] T010 [P] Implement `app/core/logging.py` with stdlib logging dictConfig (JSON format in production, text in development, LOG_LEVEL from config)
- [X] T011 [P] Create `app/providers/base.py` with abstract `MessagingProvider` class (empty ABC placeholder for future specs)
- [X] T012 Implement `app/main.py` with FastAPI app factory (title="WhatsApp Gateway", version="0.1.0", load config, setup logging, include routers)

**Checkpoint**: `uv run pytest tests/unit/test_config.py tests/unit/test_logging.py -v` passes; `uv run python -c "from app.core.config import get_settings"` works

---

## Phase 3: User Story 1 — Subir Ambiente Local Completo (Priority: P1) 🎯 MVP

**Goal**: Desenvolvedor clona o repo e sobe todo o ambiente com `docker compose up`

**Independent Test**: Executar `docker compose up` e verificar que todos os 5 serviços sobem e respondem nas suas portas

### Implementation for User Story 1

- [X] T013 [US1] Create `Dockerfile` with multi-stage build (python:3.12-slim base, uv install, copy app, uvicorn entrypoint on port 8000)
- [X] T014 [US1] Create `docker-compose.yml` with 5 services (backend build local port 8000 env_file volume mount, postgres:16 port 5432 named volume pgdata, redis:7-alpine port 6379, n8n docker.n8n.io/n8nio/n8n port 5678 named volume n8ndata, evolution-api evoapicloud/evolution-api:v2.3.4 port 8080 named volume evolution_instances), volumes section (pgdata, n8ndata, evolution_instances) and default bridge network
- [X] T015 [US1] Validate `docker compose config` passes without errors

**Checkpoint**: `docker compose up --build` starts all 5 services, `docker compose ps` shows all running

---

## Phase 4: User Story 2 — Verificar Saúde do Backend (Priority: P1)

**Goal**: Endpoint GET /health retorna status 200 com informações do serviço

**Independent Test**: `curl http://localhost:8000/health` retorna `{"status": "ok", "service": "whatsapp-gateway", "version": "0.1.0"}`

### Tests for User Story 2

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T016 [P] [US2] Unit test for health endpoint in `tests/unit/test_health.py` — test GET /health returns 200, test response body matches `{"status":"ok","service":"whatsapp-gateway","version":"0.1.0"}`, test no authentication required

### Implementation for User Story 2

- [X] T017 [US2] Create `app/schemas/health.py` with HealthResponse Pydantic model (status: str, service: str, version: str)
- [X] T018 [US2] Create `app/api/routes/health.py` with `GET /health` route returning HealthResponse (public, no auth — lives outside /v1 prefix)
- [X] T019 [US2] Register health router in `app/main.py` at root path `/health` (NOT under `/v1` prefix — infrastructure endpoint)

**Checkpoint**: `uv run pytest tests/unit/test_health.py -v` passes; backend running responds to GET /health correctly

---

## Phase 5: User Story 3 — Configurar Variáveis de Ambiente (Priority: P2)

**Goal**: Desenvolvedor configura o projeto copiando `.env.example` e o backend valida na inicialização

**Independent Test**: Remover uma variável obrigatória do `.env` e verificar que o backend falha com mensagem clara

### Tests for User Story 3

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T020 [P] [US3] Unit test for startup validation in `tests/unit/test_startup.py` — test app startup fails gracefully with clear error message when required env var (DATABASE_URL) is missing, test app starts successfully with all env vars present

### Implementation for User Story 3

- [X] T021 [US3] Add startup validation in `app/main.py` — load settings on startup event, catch ValidationError and print clear missing-variable message before exit
- [X] T022 [US3] Document all variables in `.env.example` with inline comments explaining each one

**Checkpoint**: `uv run pytest tests/unit/test_startup.py -v` passes; backend fails fast with clear error when required env var is missing

---

## Phase 6: User Story 4 — Documentação OpenAPI Automática (Priority: P3)

**Goal**: Desenvolvedor acessa /docs e /redoc para ver a documentação da API

**Independent Test**: Abrir `http://localhost:8000/docs` no navegador e ver Swagger UI com endpoint /health documentado

### Tests for User Story 4

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T023 [P] [US4] Unit test for OpenAPI in `tests/unit/test_openapi.py` — test GET /docs returns 200, test GET /openapi.json contains /health path, test OpenAPI schema has correct title and version

### Implementation for User Story 4

- [X] T024 [US4] Add OpenAPI metadata to `app/main.py` (description, tags_metadata with "Infrastructure" tag — title/version already set in T012)
- [X] T025 [US4] Add OpenAPI operation metadata to health endpoint in `app/api/routes/health.py` (tags=["Infrastructure"], summary, description, operationId, response_model)

**Checkpoint**: `uv run pytest tests/unit/test_openapi.py -v` passes; `/docs` shows Swagger UI with /health documented

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Alembic setup, final validations, cleanup

- [X] T026 [P] Create `alembic.ini` at project root with async PostgreSQL driver config and `alembic/env.py` with async migration support
- [X] T027 [P] Create `app/core/database.py` with async SQLAlchemy engine and session factory (placeholder, no active connection in this spec)
- [X] T028 [P] Create `app/core/redis.py` with Redis connection placeholder (provisioned only, no active usage in this spec)
- [X] T029 Run full test suite: `uv run pytest tests/unit/ -v --cov=app --cov-report=term-missing`
- [X] T030 Run quickstart.md validation: full `docker compose up`, health check, docs access, `docker compose down` (verify startup < 2 min per SC-001)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 (needs pyproject.toml and directory structure)
- **User Story 1 (Phase 3)**: Depends on Phase 2 (needs app/main.py for Dockerfile entrypoint)
- **User Story 2 (Phase 4)**: Depends on Phase 2 (needs app/main.py and core modules)
- **User Story 3 (Phase 5)**: Depends on Phase 2 (needs config.py)
- **User Story 4 (Phase 6)**: Depends on Phase 4 (needs health endpoint to document)
- **Polish (Phase 7)**: Can start after Phase 2, ideally after all stories

### User Story Dependencies

- **User Story 1 (P1)**: Independent — only needs foundational app structure
- **User Story 2 (P1)**: Independent — only needs foundational app structure
- **User Story 3 (P2)**: Independent — only needs config module
- **User Story 4 (P3)**: Depends on US2 (needs health endpoint to be visible in docs)

### Within Each User Story

- Tests MUST be written and FAIL before implementation (TDD)
- Models/schemas before routes
- Routes before registration in main.py
- Core implementation before integration

### Parallel Opportunities

- T003 + T004 + T005 + T006: All setup tasks on different files
- T007 + T008: Independent test files (config and logging)
- T010 + T011: Independent core modules (logging + provider base)
- T013 + T017: Dockerfile and schemas (different stories, no conflict)
- T026 + T027 + T028: All polish tasks on different files
- US1, US2, US3 can proceed in parallel after Phase 2

---

## Parallel Example: Setup Phase

```bash
# Launch all parallel setup tasks together:
Task: "Create directory structure app/ with __init__.py files"
Task: "Create directory structure alembic/, scripts/, tests/"
Task: "Create .env.example with all required variables"
Task: "Create tests/unit/conftest.py with shared fixtures"
```

## Parallel Example: Foundational Tests

```bash
# Launch test tasks in parallel before implementation:
Task: "Unit test for config module in tests/unit/test_config.py"
Task: "Unit test for logging module in tests/unit/test_logging.py"
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 2)

1. Complete Phase 1: Setup (T001-T006)
2. Complete Phase 2: Foundational tests then implementation (T007-T012)
3. Complete Phase 3: User Story 1 — Docker environment (T013-T015)
4. Complete Phase 4: User Story 2 — Health check tests then implementation (T016-T019)
5. **STOP and VALIDATE**: `docker compose up`, `curl /health`, `pytest tests/unit/ -v`
6. This gives a fully functional, tested local environment

### Incremental Delivery

1. Setup + Foundational → Skeleton ready, core tests pass
2. Add US1 (Docker) → Environment runs → Validate
3. Add US2 (Health) → API responds, tests pass → Validate
4. Add US3 (Config validation) → Robust startup, tests pass → Validate
5. Add US4 (Docs) → Developer experience complete, tests pass → Validate
6. Polish → Full coverage report, production-ready

---

## Notes

- Total: 30 tasks across 7 phases (6 test tasks + 24 implementation tasks)
- TDD approach: test tasks precede implementation in each phase
- All tasks target the `app/` package as defined in plan.md
- Test fixtures in conftest.py handle env var mocking for isolated tests
- Evolution API is only provisioned (Docker service), no code integration
- Redis is only provisioned, no active connection code
- PostgreSQL connection is placeholder only (active usage in Spec 003)
