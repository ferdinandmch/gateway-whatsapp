# Tasks: Envio de Mensagens

**Input**: Design documents from `specs/005-message-sending/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/

**Tests**: Incluídos conforme feedback do projeto (testes ao final de cada spec).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Migration de banco e schemas base necessários para todas as user stories

- [ ] T001 Create Alembic migration to add columns `media_url` (Text, nullable), `filename` (String(255), nullable), `raw_payload` (JSONB, nullable) to `messages` table in alembic/versions/
- [ ] T002 Update Message model with new fields `media_url`, `filename`, `raw_payload` in app/models/message.py
- [ ] T003 [P] Add phone number validation function `validate_phone_format` in app/core/phone.py (only digits, 10-13 chars after stripping non-digits; raises ValueError if invalid)
- [ ] T004 [P] Create message request/response Pydantic schemas in app/schemas/message.py (SendTextRequest, SendImageRequest, SendAudioRequest, SendDocumentRequest, SendVideoRequest, MessageResponse)

**Checkpoint**: Database migrated, schemas ready — MessageService can now be built.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: MessageService core logic that all endpoints depend on

**⚠️ CRITICAL**: No endpoint can work without this phase complete

- [ ] T005 Create MessageService class in app/services/message_service.py with constructor receiving `db: AsyncSession` and `provider: MessagingProvider`
- [ ] T006 Implement `_get_instance_for_sending` helper in app/services/message_service.py — validates instance belongs to client, status is "connected"; raises HTTPException with INSTANCE_NOT_FOUND or INSTANCE_DISCONNECTED
- [ ] T007 Implement `_record_message` helper in app/services/message_service.py — creates Message record with status "pending", returns the Message object
- [ ] T008 Implement `_handle_send_result` helper in app/services/message_service.py — on success: update status to "sent", set provider_message_id, save raw_payload; on failure: update status to "failed", create ErrorLog entry with context="message.send_failed"
- [ ] T009 Register message routes in app/api/v1/routes/__init__.py and app/main.py (import and include router with prefix /v1/messages, tags=["messages"])

**Checkpoint**: Service core ready — individual endpoints can now be implemented in parallel.

---

## Phase 3: User Story 1 - Enviar mensagem de texto (Priority: P1) 🎯 MVP

**Goal**: Cliente autenticado envia mensagem de texto via instância conectada

**Independent Test**: POST /v1/messages/text com payload válido retorna message_id e status "sent"

### Implementation for User Story 1

- [ ] T010 [US1] Implement `send_text` method in app/services/message_service.py — calls validate_phone_format, _get_instance_for_sending, _record_message, provider.send_text, _handle_send_result; returns MessageResponse
- [ ] T011 [US1] Create POST /v1/messages/text route in app/api/v1/routes/messages.py — depends on get_current_client, get_db, get_provider; calls message_service.send_text
- [ ] T012 [US1] Write unit tests for send_text in tests/unit/test_message_service.py — test success, instance not found, instance disconnected, provider failure, validation error (invalid phone)
- [ ] T013 [US1] Write unit tests for validate_phone_format and normalize_phone in tests/unit/test_phone_validation.py — test validation (10-13 digits, reject letters/too short/too long); test normalization (add prefix 55 when missing, strip non-digits, append @s.whatsapp.net suffix, passthrough if already suffixed)
- [ ] T014 [US1] Write integration test for POST /v1/messages/text in tests/integration/test_messages_api.py — test full flow with mocked provider

**Checkpoint**: Text messaging fully functional and tested independently.

---

## Phase 4: User Story 2 - Enviar mensagem de imagem (Priority: P2)

**Goal**: Cliente envia imagem via instância conectada com legenda opcional

**Independent Test**: POST /v1/messages/image com media_url retorna message_id com message_type "image"

### Implementation for User Story 2

- [ ] T015 [US2] Implement `send_media` method in app/services/message_service.py — generic method for all media types; calls validate_phone_format, _get_instance_for_sending, _record_message (with media_url, caption, filename), provider.send_media, _handle_send_result
- [ ] T016 [US2] Create POST /v1/messages/image route in app/api/v1/routes/messages.py — calls message_service.send_media with media_type=image
- [ ] T017 [US2] Write unit tests for send_media (image) in tests/unit/test_message_service.py — test success with caption, success without caption, missing media_url
- [ ] T018 [US2] Write integration test for POST /v1/messages/image in tests/integration/test_messages_api.py

**Checkpoint**: Image sending works independently. Media send infrastructure ready for other types.

---

## Phase 5: User Story 3 - Enviar áudio, documento e vídeo (Priority: P3)

**Goal**: Completar cobertura de todos os tipos de mídia da V1

**Independent Test**: POST para cada endpoint retorna message_id com message_type correto

### Implementation for User Story 3

- [ ] T019 [P] [US3] Create POST /v1/messages/audio route in app/api/v1/routes/messages.py — calls message_service.send_media with media_type=audio
- [ ] T020 [P] [US3] Create POST /v1/messages/document route in app/api/v1/routes/messages.py — calls message_service.send_media with media_type=document; includes filename in request
- [ ] T021 [P] [US3] Create POST /v1/messages/video route in app/api/v1/routes/messages.py — calls message_service.send_media with media_type=video
- [ ] T022 [US3] Write unit tests for send_media (audio, document, video) in tests/unit/test_message_service.py — test document with filename, audio without caption, video with caption
- [ ] T023 [US3] Write integration tests for audio, document, video endpoints in tests/integration/test_messages_api.py

**Checkpoint**: All 5 message types functional. Full V1 messaging coverage complete.

---

## Phase 6: User Story 4 - Registro e rastreabilidade (Priority: P2)

**Goal**: Garantir que toda tentativa de envio é registrada persistentemente

**Independent Test**: Após envio (sucesso ou falha), consultar banco e confirmar registro com campos corretos

### Implementation for User Story 4

- [ ] T024 [US4] Verify _record_message stores all required fields (direction, content_type, body, remote_jid, media_url, filename, status) in tests/unit/test_message_service.py — add assertions for each field
- [ ] T025 [US4] Verify _handle_send_result on failure creates ErrorLog entry with context, error_message, and details (instance_id, message_id, provider_error) in tests/unit/test_message_service.py
- [ ] T026 [US4] Verify raw_payload is stored on success (provider response data) in tests/unit/test_message_service.py

**Checkpoint**: Full audit trail verified — every send attempt is traceable.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T027 [P] Add structured logging (logger.info/error) for all message operations in app/services/message_service.py — include instance_id, message_id, client_id, content_type
- [ ] T028 [P] Validate all error responses follow standard format {code, message, details} in app/api/v1/routes/messages.py
- [x] T029 Run all tests and fix any failures
- [ ] T030 Run quickstart.md validation — manually verify each curl example against running app

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 completion — BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Phase 2 completion
  - US1 (P1): Can start after Phase 2
  - US2 (P2): Can start after Phase 2 (send_media is independent of send_text)
  - US3 (P3): Depends on US2 (reuses send_media method)
  - US4 (P2): Can start after US1 (validates recording behavior that exists from Phase 2)
- **Polish (Phase 7)**: Depends on all user stories complete

### User Story Dependencies

- **US1 (text)**: Phase 2 → US1 (independent)
- **US2 (image)**: Phase 2 → US2 (independent, builds send_media)
- **US3 (audio/doc/video)**: Phase 2 + US2 → US3 (reuses send_media from US2)
- **US4 (rastreabilidade)**: Phase 2 + US1 → US4 (validates recording logic)

### Within Each User Story

- Implementation before tests (tests validate the implementation)
- Service methods before route endpoints
- Core flow before edge cases

### Parallel Opportunities

- T003 + T004 can run in parallel (different files)
- T019 + T020 + T021 can run in parallel (same file but independent routes)
- T027 + T028 can run in parallel (different concerns)
- US1 and US2 can run in parallel after Phase 2

---

## Parallel Example: User Story 3

```bash
# Launch all route tasks for User Story 3 together:
Task: "Create POST /v1/messages/audio route in app/api/v1/routes/messages.py"
Task: "Create POST /v1/messages/document route in app/api/v1/routes/messages.py"
Task: "Create POST /v1/messages/video route in app/api/v1/routes/messages.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (migration + schemas)
2. Complete Phase 2: Foundational (MessageService core)
3. Complete Phase 3: User Story 1 (send_text)
4. **STOP and VALIDATE**: Test text message sending independently
5. Deploy/demo if ready

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add US1 (text) → Test → MVP ready!
3. Add US2 (image) → Test → Media infrastructure proven
4. Add US3 (audio/doc/video) → Test → Full coverage
5. Add US4 (rastreabilidade) → Test → Audit trail complete
6. Polish → Production-quality

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Provider layer (send_text, send_media) already exists — no provider changes needed
- Message model exists but needs 3 new columns via migration
- phone.normalize_phone exists but needs validation wrapper
- Follow InstanceService pattern for MessageService (constructor with db + provider)
- Field mapping spec→model: `message_type`→`content_type`, `message`/`content`→`body`, `to`→`remote_jid` (normalized). Schemas Pydantic devem usar a terminologia da spec (contratos públicos) e converter internamente para o modelo.
- Message não tem `client_id` direto — client é derivado via `instance.client_id` (join). Validação de ownership é feita consultando Instance com filtro de client_id.
