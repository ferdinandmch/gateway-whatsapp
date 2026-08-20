# Tasks: Persistência e Modelagem Inicial

**Input**: Design documents from `specs/003-persistence-initial-modeling/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, quickstart.md

**Tests**: Included — spec requires pytest coverage for each functionality.

**Organization**: Tasks grouped by user story for independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup

**Purpose**: Shared infrastructure for all models

- [x] T001 [P] Create model mixins (TimestampMixin, SoftDeleteMixin) in app/models/base.py
- [x] T002 [P] Update app/core/database.py with pool_size/max_overflow config and async session dependency

**Checkpoint**: Base infrastructure ready for model definitions

---

## Phase 2: Foundational (Client model — shared dependency)

**Purpose**: Client entity is the root for all other entities. MUST be complete before stories can proceed.

**⚠️ CRITICAL**: Instance, Message, and WebhookEvent all depend on Client existing.

- [x] T003 Create Client model in app/models/client.py (UUID pk, name, is_active, soft-delete via mixin, timestamps via mixin)
- [x] T004 Update app/models/__init__.py to import Client and re-export Base

**Checkpoint**: Client model defined — user story implementation can begin

---

## Phase 3: User Story 1 - Persistir dados de instâncias WhatsApp (Priority: P1) 🎯 MVP

**Goal**: Instance model with FK to Client, status enum (disconnected/connecting/connected/closed), provider_instance_id, soft-delete

**Independent Test**: Create an instance linked to a client, verify persistence of FK, status, and metadata

### Tests for User Story 1

- [x] T005 [P] [US1] Unit test for Instance model creation and status values in tests/unit/test_models.py
- [x] T006 [P] [US1] Unit test for Client-Instance relationship and FK constraint in tests/unit/test_models.py

### Implementation for User Story 1

- [x] T007 [US1] Create Instance model in app/models/instance.py (UUID pk, client_id FK, name, status with enum values, provider_instance_id unique nullable, soft-delete, timestamps)
- [x] T008 [US1] Update app/models/__init__.py to import Instance

**Checkpoint**: Client + Instance models functional and independently testable

---

## Phase 4: User Story 2 - Persistir mensagens enviadas e recebidas (Priority: P2)

**Goal**: Message model with FK to Instance, direction (inbound/outbound), content_type, body, remote_jid, status, provider_message_id

**Independent Test**: Create message records with different types/directions linked to an instance, verify persistence and query by instance

### Tests for User Story 2

- [x] T009 [P] [US2] Unit test for Message model creation with all content types and directions in tests/unit/test_models.py
- [x] T010 [P] [US2] Unit test for Instance-Message relationship and query filtering in tests/unit/test_models.py

### Implementation for User Story 2

- [x] T011 [US2] Create Message model in app/models/message.py (UUID pk, instance_id FK, direction, content_type, body, remote_jid, status, provider_message_id, timestamps)
- [x] T012 [US2] Update app/models/__init__.py to import Message

**Checkpoint**: Messages can be persisted and queried per instance

---

## Phase 5: User Story 3 - Persistir eventos de webhook (Priority: P2)

**Goal**: WebhookEvent model with FK to Instance (nullable), event_type, raw_payload (JSONB), processing_status

**Independent Test**: Create webhook events with varied JSONB payloads, verify raw_payload preservation and filtering by instance/type

### Tests for User Story 3

- [x] T013 [P] [US3] Unit test for WebhookEvent model creation with JSONB payload in tests/unit/test_models.py
- [x] T014 [P] [US3] Unit test for nullable instance_id and payload integrity (including 1MB payload) in tests/unit/test_models.py

### Implementation for User Story 3

- [x] T015 [US3] Create WebhookEvent model in app/models/webhook_event.py (UUID pk, instance_id FK nullable, event_type, raw_payload JSONB, processing_status, processed_at nullable, created_at)
- [x] T016 [US3] Update app/models/__init__.py to import WebhookEvent

**Checkpoint**: Webhook events can be stored with raw payload preserved

---

## Phase 6: User Story 4 - ErrorLog (Priority: P2)

**Goal**: ErrorLog model standalone for diagnostics — context, error_message, details (JSONB)

**Independent Test**: Create error log entries and verify persistence with variable JSONB details

### Implementation for User Story 4

- [x] T017 [P] [US4] Create ErrorLog model in app/models/error_log.py (UUID pk, context, error_message, details JSONB nullable, created_at)
- [x] T018 [US4] Update app/models/__init__.py to import ErrorLog

**Checkpoint**: All 5 models defined

---

## Phase 7: User Story 5 - Migrations reproduzíveis (Priority: P1)

**Goal**: Alembic migration inicial que cria todas as tabelas com constraints, índices e relacionamentos. Reversível (up/down).

**Independent Test**: Apply migration on clean DB, verify all tables exist; rollback, verify all tables removed

### Implementation for User Story 5

- [x] T019 [US5] Update alembic/env.py to set target_metadata = Base.metadata (import from app.models)
- [x] T020 [US5] Generate initial migration in alembic/versions/0001_initial_schema.py
- [x] T021 [US5] Review and adjust generated migration — verify indexes, constraints, JSONB columns, and downgrade function
- [x] T022 [US5] Test migration: apply upgrade head on clean PostgreSQL, verify all tables created
- [x] T023 [US5] Test migration: apply downgrade base, verify all tables removed

**Checkpoint**: Migrations fully functional — upgrade and downgrade verified (pending Docker)

---

## Phase 8: Integration Tests

**Purpose**: End-to-end validation of models + migrations + database

- [x] T024 [P] Create integration test fixture with test database session in tests/integration/conftest.py
- [x] T025 [P] Integration test: create Client → Instance → Message chain, verify FK constraints in tests/integration/test_migrations.py
- [x] T026 [P] Integration test: verify soft-delete behavior (deleted_at set, record still queryable explicitly) in tests/integration/test_migrations.py
- [x] T027 Integration test: verify client isolation (Instance query scoped to client_id) in tests/integration/test_migrations.py

**Checkpoint**: Integration tests written — execution requires running PostgreSQL (TEST_DATABASE_URL)

---

## Phase 9: Polish & Cross-Cutting Concerns

- [x] T028 [P] Run quickstart.md validation (apply migration, verify tables via SQL) — pending Docker
- [x] T029 Verify all models have proper __tablename__ and __repr__

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — start immediately
- **Phase 2 (Foundational)**: Depends on Phase 1 (needs mixins)
- **Phase 3-6 (User Stories 1-4)**: All depend on Phase 2 (need Client model)
  - US1 (Instance): depends on Client
  - US2 (Message): depends on Instance (US1)
  - US3 (WebhookEvent): depends on Client only (instance_id nullable)
  - US4 (ErrorLog): no model dependencies (standalone)
- **Phase 7 (Migrations)**: Depends on all models being defined (Phases 3-6)
- **Phase 8 (Integration)**: Depends on Phase 7 (needs migrations applied)
- **Phase 9 (Polish)**: Depends on Phase 8

### User Story Dependencies

- **US1 (Instance)**: Depends on Foundational (Client) — can start after Phase 2
- **US2 (Message)**: Depends on US1 (Instance model must exist for FK)
- **US3 (WebhookEvent)**: Can start after Phase 2 (FK nullable to Instance)
- **US4 (ErrorLog)**: Can start after Phase 1 (standalone, only needs mixins)
- **US5 (Migrations)**: Depends on US1-US4 (all models must be defined)

### Parallel Opportunities

- T001 + T002 (Setup tasks — different files)
- T005 + T006 (US1 tests — same file but independent test functions)
- US3 + US4 can run in parallel (no dependencies between them)
- T024 + T025 + T026 (integration tests — independent test cases)

---

## Notes

- All models use SQLAlchemy 2.x declarative style with `Mapped[]` type annotations
- Mixins avoid code duplication for timestamps and soft-delete
- JSONB fields use `sqlalchemy.dialects.postgresql.JSONB`
- UUIDs generated Python-side via `uuid.uuid4` (not server-default)
- Enum values stored as VARCHAR (native_enum=False) for simpler migrations
- Soft-delete only on Client and Instance; Message/WebhookEvent/ErrorLog are append-only
- SQLAlchemy column defaults apply at flush/insert time, not at Python __init__ time — unit tests pass explicit values
- T022/T023/T028 require running PostgreSQL (Docker Compose) — run with: `docker compose up -d postgres`
