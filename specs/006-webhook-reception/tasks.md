# Tasks: Recebimento de Webhooks

**Input**: Design documents from `/specs/006-webhook-reception/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/

**Tests**: Incluídos conforme feedback do projeto (testes ao final de cada spec).

**Organization**: Tasks agrupadas por user story para implementação e teste independentes.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Pode rodar em paralelo (arquivos diferentes, sem dependências)
- **[Story]**: User story associada (US1, US2, US3, US4)
- Caminhos exatos incluídos nas descrições

---

## Phase 1: Setup

**Purpose**: Preparação da estrutura para recebimento de webhooks

- [X] T001 Criar migration Alembic para expandir tabela `webhook_events` com campos: client_id, provider, provider_instance_name, normalized_payload, forwarded_to_n8n, n8n_status_code, n8n_response, received_at, forwarded_at e valor `ignored` no enum em `alembic/versions/`
- [X] T002 Atualizar model WebhookEvent com novos campos e relacionamento com Client em `app/models/webhook_event.py`
- [X] T003 [P] Criar pacote `app/webhooks/__init__.py`
- [X] T004 [P] Criar schemas Pydantic para webhook request/response em `app/schemas/webhook.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Componentes core que TODAS as user stories dependem

**⚠️ CRITICAL**: Nenhuma user story pode iniciar sem esta fase completa

- [X] T005 Implementar dependency `verify_webhook_secret` para validação do header X-Webhook-Secret em `app/core/dependencies.py`
- [X] T006 Implementar classificador de eventos (Evolution API → tipo interno) em `app/webhooks/classifier.py`
- [X] T007 Implementar normalizador de payload (payload bruto → formato interno padronizado) em `app/webhooks/normalizer.py`
- [X] T008 Implementar forwarder para n8n (POST payload normalizado para n8n_webhook_url) em `app/webhooks/forwarder.py`
- [X] T009 Implementar WebhookService com fluxo de orquestração completo em `app/services/webhook_service.py`
- [X] T010 Criar rota POST /v1/webhooks/evolution com validação de segredo e chamada ao WebhookService em `app/api/v1/routes/webhooks.py`
- [X] T011 Registrar router de webhooks no app principal

**Checkpoint**: Infraestrutura de webhook pronta — implementação das user stories pode começar

---

## Phase 3: User Story 1 - Receber Mensagem de Entrada (Priority: P1) 🎯 MVP

**Goal**: Receber evento de mensagem da Evolution API, salvar payload bruto, normalizar, registrar mensagem inbound no sistema

**Independent Test**: Enviar POST simulando mensagem recebida e verificar que a mensagem aparece em `messages` com remetente, conteúdo e tipo corretos

### Implementation for User Story 1

- [X] T012 [US1] Implementar lógica de classificação para `messages.upsert` (fromMe=false) → `message.received` no classifier em `app/webhooks/classifier.py`
- [X] T013 [US1] Implementar normalização de mensagem de texto (extrair from, content, timestamp, provider_message_id) em `app/webhooks/normalizer.py`
- [X] T014 [US1] Implementar normalização de mensagens de mídia (image, audio, document, video — extrair media_url, caption, message_type) em `app/webhooks/normalizer.py`
- [X] T015 [US1] Implementar no WebhookService: lookup de instância por provider_instance_id, preenchimento de client_id/instance_id em `app/services/webhook_service.py`
- [X] T016 [US1] Implementar no WebhookService: criação de registro Message (direction=inbound, status=received) quando event_type=message.received em `app/services/webhook_service.py`
- [X] T017 [US1] Implementar encaminhamento ao n8n para eventos message.received (chamar forwarder, registrar resultado) em `app/services/webhook_service.py`

### Tests for User Story 1

- [X] T018 [P] [US1] Teste unitário do classifier para mensagens recebidas (text e mídia) em `tests/unit/test_webhook_classifier.py`
- [X] T019 [P] [US1] Teste unitário do normalizer para mensagens de texto e mídia em `tests/unit/test_webhook_normalizer.py`
- [X] T020 [P] [US1] Teste unitário do WebhookService para fluxo de mensagem recebida em `tests/unit/test_webhook_service.py`
- [X] T021 [US1] Teste de integração: POST /v1/webhooks/evolution com mensagem de texto → verificar message criada e resposta 200 em `tests/integration/test_webhooks_api.py`

**Checkpoint**: Mensagens recebidas via webhook são salvas e encaminhadas ao n8n

---

## Phase 4: User Story 2 - Receber Atualização de Conexão (Priority: P2)

**Goal**: Receber evento de mudança de status de conexão e atualizar a instância correspondente

**Independent Test**: Enviar POST simulando connection.update e verificar que o status da instância foi atualizado

### Implementation for User Story 2

- [X] T022 [US2] Implementar classificação para `connection.update` → `connection.update` no classifier em `app/webhooks/classifier.py`
- [X] T023 [US2] Implementar normalização de eventos de conexão (extrair state, mapear para status interno) em `app/webhooks/normalizer.py`
- [X] T024 [US2] Implementar no WebhookService: atualização de status da instância (connected/disconnected/error, timestamps) em `app/services/webhook_service.py`
- [X] T025 [US2] Implementar encaminhamento ao n8n para eventos connection.update em `app/services/webhook_service.py`

### Tests for User Story 2

- [X] T026 [P] [US2] Teste unitário do classifier e normalizer para eventos de conexão em `tests/unit/test_webhook_classifier.py`
- [X] T027 [US2] Teste de integração: POST connection.update → verificar status da instância atualizado em `tests/integration/test_webhooks_api.py`

**Checkpoint**: Mudanças de conexão refletidas no status da instância

---

## Phase 5: User Story 3 - Receber Status de Entrega/Leitura (Priority: P3)

**Goal**: Receber eventos de delivery/read e atualizar status de mensagens outbound correspondentes

**Independent Test**: Enviar POST simulando status delivered/read e verificar que o status da mensagem outbound foi atualizado

### Implementation for User Story 3

- [X] T028 [US3] Implementar classificação para `messages.update` → `message.delivered` / `message.read` no classifier em `app/webhooks/classifier.py`
- [X] T029 [US3] Implementar normalização de eventos de status (extrair provider_message_id, novo status) em `app/webhooks/normalizer.py`
- [X] T030 [US3] Implementar no WebhookService: busca de mensagem por provider_message_id e atualização de status em `app/services/webhook_service.py`

### Tests for User Story 3

- [X] T031 [P] [US3] Teste unitário do classifier e normalizer para eventos de status em `tests/unit/test_webhook_classifier.py`
- [X] T032 [US3] Teste de integração: POST message.delivered → verificar status da mensagem atualizado em `tests/integration/test_webhooks_api.py`

**Checkpoint**: Status de mensagens outbound atualizado via webhook

---

## Phase 6: User Story 4 - Tratar Eventos Desconhecidos (Priority: P3)

**Goal**: Eventos não reconhecidos são salvos com payload bruto sem quebrar o sistema

**Independent Test**: Enviar POST com evento arbitrário e verificar que é salvo como "unknown" com resposta 202

### Implementation for User Story 4

- [X] T033 [US4] Implementar classificação fallback para eventos desconhecidos → `unknown` no classifier em `app/webhooks/classifier.py`
- [X] T034 [US4] Implementar no WebhookService: tratamento de instância não encontrada (salvar com metadados, registrar error_log) em `app/services/webhook_service.py`
- [X] T035 [US4] Implementar no WebhookService: resposta 202 Accepted para eventos unknown/ignored em `app/services/webhook_service.py`

### Tests for User Story 4

- [X] T036 [P] [US4] Teste unitário: evento desconhecido classificado como unknown em `tests/unit/test_webhook_classifier.py`
- [X] T037 [US4] Teste de integração: POST evento desconhecido → resposta 202, payload salvo em `tests/integration/test_webhooks_api.py`
- [X] T038 [US4] Teste de integração: POST com segredo inválido → resposta 401, nada salvo em `tests/integration/test_webhooks_api.py`

**Checkpoint**: Sistema resiliente a eventos desconhecidos e requisições não autorizadas

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Melhorias que afetam múltiplas user stories

- [X] T039 [P] Implementar classificação e encaminhamento para `send.error` no classifier/service em `app/webhooks/classifier.py` e `app/services/webhook_service.py`
- [X] T040 [P] Adicionar logging estruturado em pontos-chave do fluxo de webhook em `app/services/webhook_service.py`
- [X] T041 Validar fluxo completo com quickstart.md (teste manual end-to-end)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Sem dependências — iniciar imediatamente
- **Foundational (Phase 2)**: Depende de Phase 1 — BLOQUEIA todas as user stories
- **User Stories (Phase 3-6)**: Todas dependem de Phase 2 completa
  - US1 a US4 podem ser executadas em paralelo se desejado
  - Ou sequencialmente em ordem de prioridade (P1 → P2 → P3)
- **Polish (Phase 7)**: Depende de todas as user stories completas

### User Story Dependencies

- **User Story 1 (P1)**: Depende apenas de Phase 2 — sem dependências de outras stories
- **User Story 2 (P2)**: Depende apenas de Phase 2 — independente de US1
- **User Story 3 (P3)**: Depende apenas de Phase 2 — independente de US1/US2
- **User Story 4 (P3)**: Depende apenas de Phase 2 — independente de US1/US2/US3

### Within Each User Story

- Models/schemas antes de services
- Services antes de endpoints/integração
- Implementação antes de testes
- Story completa antes de avançar para próxima prioridade

### Parallel Opportunities

- T003 e T004 podem rodar em paralelo (Phase 1)
- Após Phase 2 completa, todas as stories podem iniciar simultaneamente
- Testes marcados [P] dentro de cada story podem rodar em paralelo
- US1-US4 são totalmente independentes entre si

---

## Parallel Example: User Story 1

```bash
# Após Phase 2, lançar implementação de US1:
Task T012: "Classificação de messages.upsert no classifier"
Task T013: "Normalização de mensagem de texto no normalizer"
Task T014: "Normalização de mensagens de mídia no normalizer"

# Após T012-T016, testes em paralelo:
Task T018: "Teste unitário do classifier"
Task T019: "Teste unitário do normalizer"
Task T020: "Teste unitário do WebhookService"
Task T021: "Teste de Integraçao entre as specs implementadas"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Completar Phase 1: Setup (migration + model + schemas)
2. Completar Phase 2: Foundational (classifier + normalizer + forwarder + service + rota)
3. Completar Phase 3: User Story 1 (mensagem recebida funcional)
4. **STOP e VALIDAR**: Testar webhook de mensagem recebida independentemente
5. Deploy/demo se pronto

### Incremental Delivery

1. Setup + Foundational → Infraestrutura de webhook pronta
2. User Story 1 → Mensagens recebidas ✓ (MVP!)
3. User Story 2 → Status de conexão atualizado ✓
4. User Story 3 → Delivery/read receipts ✓
5. User Story 4 → Resiliência a eventos desconhecidos ✓
6. Polish → Logging, send.error, validação end-to-end

---

## Notes

- [P] tasks = arquivos diferentes, sem dependências
- [Story] label mapeia task para user story específica
- Cada user story é independentemente completável e testável
- Commit após cada task ou grupo lógico
- Parar em qualquer checkpoint para validar story independentemente
