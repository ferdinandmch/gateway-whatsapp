# Tasks: Provider Evolution API

**Input**: Design documents from `specs/002-evolution-provider/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/

**Tests**: Testes unitários obrigatórios para cada funcionalidade (FR-014). TDD — testes escritos antes da implementação.

**Organization**: Tasks grouped by user story for independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Exact file paths included in descriptions

## Path Conventions

- **Package**: `app/` at repository root
- **Tests**: `tests/unit/` at repository root
- **Provider**: `app/providers/evolution/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Criar schemas internos, utilitário de telefone e expandir a interface base — blocos compartilhados por todas as user stories

- [X] T001 [P] Create `app/schemas/provider.py` with `ProviderResult` (success, data, error), `ProviderError` (code, message), `InstanceState` enum (connected, disconnected, connecting, not_found), `MessageType` enum (text, image, audio, document, video)
- [X] T002 [P] Create `app/core/phone.py` with `normalize_phone(number: str) -> str` implementing DT-044 rules (strip non-numeric, prefix 55 if missing, suffix @s.whatsapp.net)
- [X] T003 [P] Create `app/providers/evolution/schemas.py` with internal Pydantic models for Evolution API request/response payloads (CreateInstanceRequest, SendTextRequest, SendMediaRequest, ConnectionStateResponse)
- [X] T004 Update `app/providers/base.py` — remove old `send_message` stub and replace with all abstract methods: `create_instance`, `get_instance_status`, `connect_instance`, `disconnect_instance`, `delete_instance`, `send_text`, `send_media`
- [X] T005 [P] Add `WEBHOOK_BASE_URL: str` to `app/core/config.py` AppSettings class with default value in `.env.example` (`http://host.docker.internal:8000`)
- [X] T006 [P] Create `tests/unit/test_provider/__init__.py` and `tests/unit/test_provider/conftest.py` with shared fixtures (mock HTTPX client via respx, pre-configured EvolutionProvider instance with test URL/key)

**Checkpoint**: Shared infrastructure ready. `uv run python -c "from app.schemas.provider import ProviderResult, InstanceState"` works. `uv run python -c "from app.core.phone import normalize_phone"` works.

---

## Phase 2: Foundational (Core Provider Skeleton)

**Purpose**: Create the EvolutionProvider class skeleton with HTTP client setup — MUST complete before story implementation

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Tests for Foundational Phase

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T007 [P] Unit test for phone normalization in `tests/unit/test_provider/test_phone.py` — test strip spaces/parens/hyphens, test prefix 55 added when missing, test prefix 55 not duplicated, test @s.whatsapp.net suffix, test already-normalized number passes through

### Implementation for Foundational Phase

- [X] T008 Implement `app/core/phone.py` — `normalize_phone` function per DT-044 rules
- [X] T009 Create `app/providers/evolution/provider.py` with `EvolutionProvider` class skeleton: constructor accepting `base_url: str`, `api_key: str`, `webhook_base_url: str`, `timeout: int`; internal `httpx.AsyncClient` setup; all abstract methods as stubs raising NotImplementedError

**Checkpoint**: `uv run pytest tests/unit/test_provider/test_phone.py -v` passes. EvolutionProvider instantiates without error.

---

## Phase 3: User Story 1 — Enviar Mensagem de Texto (Priority: P1) 🎯 MVP

**Goal**: O provider envia mensagem de texto via Evolution API e retorna resultado normalizado

**Independent Test**: Chamar `send_text` com mock HTTPX, verificar payload enviado e resultado normalizado

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Unit test for `send_text` success in `tests/unit/test_provider/test_evolution_provider.py` — mock POST to `/message/sendText/{instance}`, verify outgoing payload contains normalized phone (digits + @s.whatsapp.net format), verify content, verify ProviderResult with provider_message_id
- [X] T011 [P] [US1] Unit test for `send_text` failures in `tests/unit/test_provider/test_evolution_provider.py` — test timeout returns PROVIDER_TIMEOUT, test 500 returns PROVIDER_ERROR, test 404 returns INSTANCE_NOT_FOUND, test connection error returns PROVIDER_UNAVAILABLE, test unexpected response returns UNEXPECTED_RESPONSE

### Implementation for User Story 1

- [X] T012 [US1] Implement `send_text` method in `app/providers/evolution/provider.py` — build payload with normalized phone number, POST to `/message/sendText/{instance_name}`, map response to ProviderResult, handle all error scenarios with ProviderError codes
- [X] T013 [US1] Add helper method `_make_request` in `app/providers/evolution/provider.py` — centralized HTTP call with apikey header, timeout, error mapping (DRY for all operations)

**Checkpoint**: `uv run pytest tests/unit/test_provider/test_evolution_provider.py -k "send_text" -v` passes

---

## Phase 4: User Story 2 — Enviar Mensagem de Mídia (Priority: P1)

**Goal**: O provider envia mensagens de mídia (imagem, áudio, documento, vídeo) via Evolution API

**Independent Test**: Chamar `send_media` para cada tipo, verificar payloads específicos e resultados normalizados

### Tests for User Story 2

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T014 [P] [US2] Unit test for `send_media` success (all types) in `tests/unit/test_provider/test_evolution_provider.py` — test image with caption, test audio without caption, test document with filename, test video with caption; verify outgoing payload contains normalized phone, verify correct media payload per type and ProviderResult
- [X] T015 [P] [US2] Unit test for `send_media` failures in `tests/unit/test_provider/test_evolution_provider.py` — test same error mapping as send_text (PROVIDER_TIMEOUT, PROVIDER_ERROR, INSTANCE_NOT_FOUND, PROVIDER_UNAVAILABLE, INVALID_REQUEST for 400)

### Implementation for User Story 2

- [X] T016 [US2] Implement `send_media` method in `app/providers/evolution/provider.py` — build payload based on MessageType (mediatype, media URL, caption, fileName), POST to `/message/sendMedia/{instance_name}`, map response to ProviderResult, reuse `_make_request`

**Checkpoint**: `uv run pytest tests/unit/test_provider/test_evolution_provider.py -k "send_media" -v` passes

---

## Phase 5: User Story 3 — Verificar Status de Instância (Priority: P2)

**Goal**: O provider consulta e retorna status normalizado de uma instância

**Independent Test**: Chamar `get_instance_status` com mock, verificar mapeamento de estados Evolution → internos

### Tests for User Story 3

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T017 [P] [US3] Unit test for `get_instance_status` in `tests/unit/test_provider/test_evolution_provider.py` — test "open" maps to connected, test "close" maps to disconnected, test "connecting" maps to connecting, test "qrcode" maps to connecting, test 404 maps to not_found, test error scenarios (timeout, 500, connection refused)

### Implementation for User Story 3

- [X] T018 [US3] Implement `get_instance_status` method in `app/providers/evolution/provider.py` — GET `/instance/connectionState/{instance_name}`, map Evolution state to InstanceState enum, handle 404 as not_found state (not error), reuse `_make_request`

**Checkpoint**: `uv run pytest tests/unit/test_provider/test_evolution_provider.py -k "instance_status" -v` passes

---

## Phase 6: User Story 4 — Criar Instância (Priority: P2)

**Goal**: O provider cria uma instância na Evolution API com webhook configurado automaticamente

**Independent Test**: Chamar `create_instance`, verificar que webhook URL é construída corretamente e instância é criada

### Tests for User Story 4

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T019 [P] [US4] Unit test for `create_instance` in `tests/unit/test_provider/test_evolution_provider.py` — test success returns instance_name, test webhook URL constructed as `{WEBHOOK_BASE_URL}/v1/webhooks/evolution/{instance_name}`, test INSTANCE_ALREADY_EXISTS on 409/conflict, test error scenarios

### Implementation for User Story 4

- [X] T020 [US4] Implement `create_instance` method in `app/providers/evolution/provider.py` — build webhook URL from `webhook_base_url`, POST to `/instance/create` with instanceName and webhook config, map response to ProviderResult, handle 409 as INSTANCE_ALREADY_EXISTS

**Checkpoint**: `uv run pytest tests/unit/test_provider/test_evolution_provider.py -k "create_instance" -v` passes

---

## Phase 7: User Story 5 — Conectar e Desconectar Instância (Priority: P2)

**Goal**: O provider inicia conexão (QR code) e executa logout de instâncias

**Independent Test**: Chamar `connect_instance` e `disconnect_instance` com mocks, verificar dados de QR code e confirmação de logout

### Tests for User Story 5

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T021 [P] [US5] Unit test for `connect_instance` in `tests/unit/test_provider/test_evolution_provider.py` — test success returns qrcode and/or pairingCode, test INSTANCE_NOT_FOUND on 404, test error scenarios
- [X] T022 [P] [US5] Unit test for `disconnect_instance` in `tests/unit/test_provider/test_evolution_provider.py` — test success returns instance_name confirmation, test INSTANCE_NOT_FOUND on 404, test error scenarios

### Implementation for User Story 5

- [X] T023 [US5] Implement `connect_instance` method in `app/providers/evolution/provider.py` — GET `/instance/connect/{instance_name}`, extract qrcode/pairingCode from response, map to ProviderResult
- [X] T024 [US5] Implement `disconnect_instance` method in `app/providers/evolution/provider.py` — DELETE `/instance/logout/{instance_name}`, map to ProviderResult with confirmation

**Checkpoint**: `uv run pytest tests/unit/test_provider/test_evolution_provider.py -k "connect or disconnect" -v` passes

---

## Phase 8: User Story 6 — Deletar Instância (Priority: P3)

**Goal**: O provider remove uma instância da Evolution API

**Independent Test**: Chamar `delete_instance` com mock, verificar que a instância é removida

### Tests for User Story 6

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T025 [P] [US6] Unit test for `delete_instance` in `tests/unit/test_provider/test_evolution_provider.py` — test success returns confirmation, test INSTANCE_NOT_FOUND on 404, test error scenarios

### Implementation for User Story 6

- [X] T026 [US6] Implement `delete_instance` method in `app/providers/evolution/provider.py` — DELETE `/instance/delete/{instance_name}`, map to ProviderResult

**Checkpoint**: `uv run pytest tests/unit/test_provider/test_evolution_provider.py -k "delete_instance" -v` passes

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Validação final, exports e cleanup

- [X] T027 [P] Update `app/providers/evolution/__init__.py` with proper exports (EvolutionProvider)
- [X] T028 [P] Update `app/providers/__init__.py` with exports (MessagingProvider from base)
- [X] T029 Run full test suite: `uv run pytest tests/unit/test_provider/ -v --cov=app/providers --cov=app/core/phone --cov-report=term-missing`
- [X] T030 Verify no imports from `app/providers/evolution/` exist in `app/services/` or `app/api/` (only `app/providers/base.py` interface should be referenced)
- [X] T031 Run quickstart.md validation: verify EvolutionProvider imports, phone normalization works, all tests pass

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 (needs schemas, phone module, provider skeleton)
- **User Story 1 (Phase 3)**: Depends on Phase 2 (needs provider skeleton with `_make_request`)
- **User Story 2 (Phase 4)**: Depends on Phase 3 (reuses `_make_request` pattern from US1)
- **User Story 3 (Phase 5)**: Depends on Phase 2 (independent of US1/US2)
- **User Story 4 (Phase 6)**: Depends on Phase 2 (independent of US1/US2/US3)
- **User Story 5 (Phase 7)**: Depends on Phase 2 (independent of other stories)
- **User Story 6 (Phase 8)**: Depends on Phase 2 (independent of other stories)
- **Polish (Phase 9)**: Depends on all user stories complete

### User Story Dependencies

- **US1 (P1)**: Independent after Phase 2 — establishes `_make_request` helper
- **US2 (P1)**: Depends on US1 (reuses `_make_request`)
- **US3 (P2)**: Independent after Phase 2
- **US4 (P2)**: Independent after Phase 2
- **US5 (P2)**: Independent after Phase 2
- **US6 (P3)**: Independent after Phase 2

### Within Each User Story

- Tests MUST be written and FAIL before implementation (TDD)
- Implementation uses `_make_request` helper from US1 (or Phase 2 for parallel stories)
- Each story independently verifiable via `pytest -k` filter

### Parallel Opportunities

- T001 + T002 + T003 + T005 + T006: All setup tasks on different files
- T010 + T011: Independent test scenarios for send_text
- T014 + T015: Independent test scenarios for send_media
- T017 + T019 + T021 + T022 + T025: All test tasks for US3-US6 (after Phase 2)
- US3, US4, US5, US6 can proceed in parallel after Phase 2 (if US1 `_make_request` extracted to Phase 2)
- T027 + T028: Independent export updates

---

## Parallel Example: Setup Phase

```bash
# Launch all parallel setup tasks together:
Task: "Create app/schemas/provider.py with ProviderResult, ProviderError, InstanceState, MessageType"
Task: "Create app/core/phone.py with normalize_phone"
Task: "Create app/providers/evolution/schemas.py with Evolution API payload models"
Task: "Add WEBHOOK_BASE_URL to app/core/config.py"
Task: "Create tests/unit/test_provider/conftest.py with fixtures"
```

## Parallel Example: US3-US6 Tests

```bash
# After Phase 2, launch all P2/P3 test tasks:
Task: "Unit test for get_instance_status"
Task: "Unit test for create_instance"
Task: "Unit test for connect_instance"
Task: "Unit test for disconnect_instance"
Task: "Unit test for delete_instance"
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 2)

1. Complete Phase 1: Setup (T001-T006)
2. Complete Phase 2: Foundational (T007-T009)
3. Complete Phase 3: User Story 1 — send_text (T010-T013)
4. Complete Phase 4: User Story 2 — send_media (T014-T016)
5. **STOP and VALIDATE**: `uv run pytest tests/unit/test_provider/ -v` — all messaging tests pass
6. This gives a fully functional messaging provider

### Incremental Delivery

1. Setup + Foundational → Provider skeleton ready, phone tests pass
2. Add US1 (send_text) → Core messaging works → Validate
3. Add US2 (send_media) → All message types work → Validate
4. Add US3 (status) → Instance status queryable → Validate
5. Add US4 (create) → Instance lifecycle begins → Validate
6. Add US5 (connect/disconnect) → Full lifecycle → Validate
7. Add US6 (delete) → Complete lifecycle → Validate
8. Polish → Full coverage, exports clean

---

## Notes

- Total: 31 tasks across 9 phases (12 test tasks + 19 implementation tasks)
- TDD approach: test tasks precede implementation in each phase
- All tests use mock HTTPX (respx) — no real Evolution API needed
- `_make_request` helper centralizes HTTP logic — DRY across all operations
- Provider never imported directly by services — only through `MessagingProvider` interface
- Phone normalization is in `app/core/` (shared utility, not provider-specific)
- No database interaction in this spec — purely in-memory provider layer
