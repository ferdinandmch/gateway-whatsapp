# Tasks: Gerenciamento de Instâncias WhatsApp

**Input**: Design documents from `specs/004-instance-management/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Incluídos conforme feedback do projeto (testes ao final de cada spec).

**Organization**: Tasks grouped by user story for independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup

**Purpose**: Schemas, migrations e dependências compartilhadas para esta feature

- [X] T001 Extend InstanceStatus enum with `created`, `error`, `removed` states in app/models/instance.py
- [X] T002 Add fields `phone_number`, `provider`, `n8n_webhook_url`, `webhook_enabled` to Instance model in app/models/instance.py
- [X] T003 Rename field `name` to `display_name` in Instance model in app/models/instance.py (keep `provider_instance_id` as-is)
- [X] T004 Generate Alembic migration for Instance model changes in alembic/versions/

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 Create Pydantic request/response schemas for instances in app/schemas/instance.py
- [X] T006 [P] Create `get_current_client` dependency (API Key auth + active check) in app/core/dependencies.py
- [X] T007 [P] Create `get_provider` dependency (returns configured EvolutionProvider) in app/core/dependencies.py
- [X] T008 [P] Create `get_db` dependency (AsyncSession from factory) in app/core/dependencies.py
- [X] T009 Create InstanceService class with shared helpers (`_get_instance_or_404`, `_count_active_instances`) in app/services/instance_service.py
- [X] T010 Register instances router in app/api/v1/routes/__init__.py and app/main.py

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Criar Instância (Priority: P1) 🎯 MVP

**Goal**: Operador cria instância com nome amigável; sistema sincroniza com provider e retorna dados da instância.

**Independent Test**: POST /v1/instances com display_name válido → 201 com status "created" e provider_instance_name preenchido.

### Implementation for User Story 1

- [X] T011 [US1] Implement `create_instance` method in InstanceService: validate limit (10), generate provider_instance_name (`inst_{uuid8}`), call provider, save with status "created" or "error" in app/services/instance_service.py
- [X] T012 [US1] Implement POST /v1/instances endpoint in app/api/v1/routes/instances.py
- [X] T013 [US1] Add `INSTANCE_LIMIT_REACHED` error code to error response handling in app/api/v1/routes/instances.py

**Checkpoint**: Can create instances via API. MVP functional.

---

## Phase 4: User Story 2 - Conectar Instância (Priority: P1)

**Goal**: Operador solicita conexão e recebe QR code/pairing code do provider.

**Independent Test**: POST /v1/instances/{id}/connect → 200 com qr_code e status "connecting".

### Implementation for User Story 2

- [X] T014 [US2] Implement `connect_instance` method in InstanceService: validate status (created/disconnected/error), call provider connect, update status to "connecting", return QR data in app/services/instance_service.py
- [X] T015 [US2] Implement POST /v1/instances/{instance_id}/connect endpoint in app/api/v1/routes/instances.py

**Checkpoint**: Can create and connect instances. Core flow functional.

---

## Phase 5: User Story 3 - Consultar Status (Priority: P2)

**Goal**: Operador consulta status atual da instância com dados atualizados do provider.

**Independent Test**: GET /v1/instances/{id}/status → 200 com status, phone_number e timestamps.

### Implementation for User Story 3

- [X] T016 [US3] Implement `get_instance_status` method in InstanceService: fetch instance, optionally sync with provider status, return combined data in app/services/instance_service.py
- [X] T017 [US3] Implement GET /v1/instances/{instance_id}/status endpoint in app/api/v1/routes/instances.py

**Checkpoint**: Can check instance connection state.

---

## Phase 6: User Story 4 - Desconectar Instância (Priority: P2)

**Goal**: Operador desconecta instância preservando dados internos.

**Independent Test**: POST /v1/instances/{id}/disconnect → 200 com status "disconnected".

### Implementation for User Story 4

- [X] T018 [US4] Implement `disconnect_instance` method in InstanceService: validate ownership, call provider disconnect, update status to "disconnected" (idempotent) in app/services/instance_service.py
- [X] T019 [US4] Implement POST /v1/instances/{instance_id}/disconnect endpoint in app/api/v1/routes/instances.py

**Checkpoint**: Full connection lifecycle (create → connect → disconnect) works.

---

## Phase 7: User Story 5 - Remover Instância (Priority: P3)

**Goal**: Operador remove instância com soft delete e sincronização com provider.

**Independent Test**: DELETE /v1/instances/{id} → 200 com status "removed"; instância não aparece na listagem.

### Implementation for User Story 5

- [X] T020 [US5] Implement `delete_instance` method in InstanceService: call provider delete (if supported), set deleted_at + status "removed" in app/services/instance_service.py
- [X] T021 [US5] Implement DELETE /v1/instances/{instance_id} endpoint in app/api/v1/routes/instances.py

**Checkpoint**: Complete CRUD lifecycle functional.

---

## Phase 8: User Story 6 - Listar Instâncias (Priority: P2)

**Goal**: Operador lista suas instâncias com paginação, ocultando removidas por padrão.

**Independent Test**: GET /v1/instances → 200 com lista paginada; removidas filtradas; include_removed=true mostra todas.

### Implementation for User Story 6

- [X] T022 [US6] Implement `list_instances` method in InstanceService: filter by client_id, exclude deleted_at unless include_removed, apply limit/offset, return items + total in app/services/instance_service.py
- [X] T023 [US6] Implement GET /v1/instances endpoint with query params (limit, offset, status, include_removed) in app/api/v1/routes/instances.py

**Checkpoint**: Operator can view and manage all instances.

---

## Phase 9: User Story 7 - Atualizar Instância (Priority: P3)

**Goal**: Operador atualiza display_name, n8n_webhook_url ou webhook_enabled de uma instância existente.

**Independent Test**: PATCH /v1/instances/{id} com novos valores → 200 com dados atualizados.

### Implementation for User Story 7

- [X] T031 [US7] Implement `update_instance` method in InstanceService: validate ownership, update allowed fields (display_name, n8n_webhook_url, webhook_enabled) in app/services/instance_service.py
- [X] T032 [US7] Implement PATCH /v1/instances/{instance_id} endpoint in app/api/v1/routes/instances.py
- [X] T033 [US7] Add InstanceUpdateRequest schema (all fields optional) in app/schemas/instance.py

**Checkpoint**: Operator can update instance configuration without recreating.

---

## Phase 10: Webhook Status Update

**Goal**: Status da instância atualizado automaticamente quando webhooks do provider chegam.

**Independent Test**: Chamar `update_status_from_webhook` com provider_instance_id e novo status → instância atualizada no banco.

### Implementation

- [X] T024 Implement `update_status_from_webhook` method in InstanceService: lookup by provider_instance_id, update status and phone_number if provided in app/services/instance_service.py

**Note**: Este método será invocado pela rota de webhooks implementada na spec 006. Nesta spec, apenas o service method é criado.

**Checkpoint**: Service expõe método para spec 006 (webhooks) integrar.

---

## Phase 11: Tests

**Purpose**: Testes cobrindo cada funcionalidade

- [X] T025 [P] Unit tests for InstanceService (create, connect, status, disconnect, delete, list, update, limit validation) in tests/unit/test_instance_service.py
- [X] T026 [P] Integration tests for all instance endpoints including PATCH (happy path + errors) in tests/integration/test_instances_api.py
- [X] T027 [P] Unit test for `get_current_client` dependency (valid key, invalid key, inactive client) in tests/unit/test_dependencies.py

**Checkpoint**: All functionality covered by automated tests.

---

## Phase 12: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T028 [P] Add structured logging for all instance operations (create, connect, disconnect, delete) in app/services/instance_service.py
- [X] T029 [P] Validate quickstart.md flow end-to-end manually
- [X] T030 Review error responses match contracts/errors.md codes

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 completion - BLOCKS all user stories
- **User Stories (Phase 3-8)**: All depend on Phase 2 completion
- **Webhook Update (Phase 9)**: Depends on Phase 2
- **Tests (Phase 10)**: Depends on all implementation phases
- **Polish (Phase 11)**: Depends on all phases

### User Story Dependencies

- **US1 - Criar (P1)**: After Phase 2 — No other story dependencies
- **US2 - Conectar (P1)**: After Phase 2 — Needs instance to exist (US1 impl shared via service)
- **US3 - Status (P2)**: After Phase 2 — Independent
- **US4 - Desconectar (P2)**: After Phase 2 — Independent
- **US5 - Remover (P3)**: After Phase 2 — Independent
- **US6 - Listar (P2)**: After Phase 2 — Independent
- **US7 - Atualizar (P3)**: After Phase 2 — Independent

### Within Each User Story

- Service method before endpoint
- Endpoint integrates with schemas from Phase 2

### Parallel Opportunities

- T006, T007, T008 (dependencies) can run in parallel
- US3, US4, US5, US6 are completely independent and can run in parallel after Phase 2
- All test tasks (T025, T026, T027) can run in parallel
- T028, T029, T030 (polish) can run in parallel

---

## Parallel Example: Foundational Phase

```text
# These can all run in parallel (different files):
T006: get_current_client dependency in app/core/dependencies.py
T007: get_provider dependency in app/core/dependencies.py
T008: get_db dependency in app/core/dependencies.py
```

## Parallel Example: User Stories after Phase 2

```text
# These stories are independent and can run in parallel:
Phase 5 (US3 - Status): T016, T017
Phase 6 (US4 - Desconectar): T018, T019
Phase 7 (US5 - Remover): T020, T021
Phase 8 (US6 - Listar): T022, T023
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (model changes + migration)
2. Complete Phase 2: Foundational (schemas, dependencies, service skeleton, router)
3. Complete Phase 3: US1 - Criar instância
4. **STOP and VALIDATE**: Test POST /v1/instances independently
5. Proceed to US2 (Conectar) for complete core flow

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. US1 (Criar) → MVP: can create instances
3. US2 (Conectar) → Core: can connect to WhatsApp
4. US3-US6 (Status, Desconectar, Remover, Listar) → Complete CRUD
5. Tests + Polish → Production-ready

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story is independently testable after Phase 2
- Commit after each task or logical group
- InstanceService centralizes all business logic; endpoints are thin
- `get_current_client` is basic auth for V1; spec 008 may refine later
