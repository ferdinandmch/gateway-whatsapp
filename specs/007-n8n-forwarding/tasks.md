# Tasks: Encaminhamento para n8n

**Input**: Design documents from `specs/007-n8n-forwarding/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Incluídos conforme diretriz do projeto (testes por spec).

**Organization**: Tasks agrupadas por user story para implementação e teste independentes.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Pode executar em paralelo (arquivos diferentes, sem dependências)
- **[Story]**: User story relacionada (US1, US2, US3, US4)
- Paths exatos incluídos nas descrições

---

## Phase 1: Setup (Configuração)

**Purpose**: Adicionar configuração de timeout dedicado para n8n

- [x] T001 Adicionar campo `N8N_FORWARD_TIMEOUT: int = 5` com validador positivo em `app/core/config.py`
- [x] T002 Adicionar `N8N_FORWARD_TIMEOUT=5` ao `.env.example`

---

## Phase 2: Foundational (Melhorias no Forwarder)

**Purpose**: Endurecimento do forwarder que é pré-requisito para TODOS os cenários de encaminhamento

**⚠️ CRITICAL**: Todas as user stories dependem destas melhorias

- [x] T003 Atualizar `app/webhooks/forwarder.py` para usar `N8N_FORWARD_TIMEOUT` ao invés de `HTTP_TIMEOUT` no `httpx.AsyncClient(timeout=...)`
- [x] T004 [P] Adicionar `follow_redirects=True` no `httpx.AsyncClient` em `app/webhooks/forwarder.py`
- [x] T005 [P] Adicionar validação de URL (scheme http/https, host não vazio) em `app/webhooks/forwarder.py` antes da chamada HTTP, retornando `ForwardResult(success=False, status_code=None, response={"error": "invalid_url"})` para URLs inválidas
- [x] T006 [P] Adicionar validação de `n8n_webhook_url` como `HttpUrl | None` no schema `InstanceCreate` em `app/schemas/instance.py`
- [x] T007 [P] Adicionar validação de `n8n_webhook_url` como `HttpUrl | None` no schema `InstanceUpdate` em `app/schemas/instance.py` (se existir)

**Checkpoint**: Forwarder melhorado — pronto para testes por user story

---

## Phase 3: User Story 1 + User Story 4 - Encaminhamento de mensagens + Resiliência (Priority: P1) 🎯 MVP

**Goal**: Garantir que mensagens recebidas são encaminhadas ao n8n com resiliência a falhas

**Independent Test**: Enviar mensagem ao WhatsApp e verificar que n8n recebe payload normalizado; simular falha do n8n e verificar que evento não é perdido

### Testes para US1 + US4

- [x] T008 [P] [US1] Criar teste unitário em `tests/unit/test_forwarder.py`: cenário de sucesso — mock HTTPX retorna 200, verifica `ForwardResult.success == True` e `status_code == 200`
- [x] T009 [P] [US4] Criar teste unitário em `tests/unit/test_forwarder.py`: cenário de timeout — mock HTTPX levanta `TimeoutException`, verifica `ForwardResult.success == False` e `response == {"error": "timeout"}`
- [x] T010 [P] [US4] Criar teste unitário em `tests/unit/test_forwarder.py`: cenário de erro HTTP 500 — mock HTTPX retorna 500, verifica `ForwardResult.success == False` e `status_code == 500`
- [x] T011 [P] [US4] Criar teste unitário em `tests/unit/test_forwarder.py`: cenário de URL inválida — passar URL sem scheme, verifica `ForwardResult.success == False` e `response == {"error": "invalid_url"}`
- [x] T012 [P] [US4] Criar teste unitário em `tests/unit/test_forwarder.py`: cenário de connection error — mock HTTPX levanta `ConnectError`, verifica `ForwardResult.success == False`
- [x] T013 [P] [US1] Criar teste unitário em `tests/unit/test_forwarder.py`: cenário de resposta 2xx não-200 (201) — verifica `ForwardResult.success == True`
- [x] T013b [P] [US4] Criar teste unitário em `tests/unit/test_forwarder.py`: cenário de payload grande (~50KB) — verifica que o forwarder não falha internamente e envia normalmente
- [x] T014 [US1] Criar teste unitário em `tests/unit/test_webhook_service_forward.py`: evento `message.received` com instância com webhook ativo — verifica que `_forward` é chamado e `forwarded_to_n8n == True`
- [x] T015 [P] [US1] Criar teste unitário em `tests/unit/test_webhook_service_forward.py`: evento `message.received` com `webhook_enabled = false` — verifica que `_forward` NÃO é chamado
- [x] T016 [P] [US1] Criar teste unitário em `tests/unit/test_webhook_service_forward.py`: evento `message.received` com `n8n_webhook_url = None` — verifica que `_forward` NÃO é chamado
- [x] T017 [US4] Criar teste unitário em `tests/unit/test_webhook_service_forward.py`: falha no n8n — verifica que `processing_status` permanece `processed` (não vira `failed`), e `ErrorLog` é criado com código `N8N_FORWARDING_ERROR`
- [x] T018 [US1] Criar teste de integração em `tests/integration/test_n8n_forwarding.py`: fluxo completo — POST webhook com evento message.received → verifica resposta 200, `forwarded_to_n8n == true` no banco, e chamada HTTP ao n8n com payload correto

**Checkpoint**: Encaminhamento de mensagens e resiliência testados e funcionais

---

## Phase 4: User Story 2 + User Story 3 - Eventos de conexão e erros de envio (Priority: P2)

**Goal**: Garantir que eventos de conexão e erros de envio também são encaminhados corretamente

**Independent Test**: Simular evento `connection.update` e `send.error` e verificar que n8n recebe payload normalizado com dados corretos

### Testes para US2 + US3

- [x] T019 [P] [US2] Criar teste unitário em `tests/unit/test_webhook_service_forward.py`: evento `connection.update` com instância com webhook ativo — verifica que `_forward` é chamado e payload contém `connection_state`
- [x] T020 [P] [US3] Criar teste unitário em `tests/unit/test_webhook_service_forward.py`: evento `send.error` com instância com webhook ativo — verifica que `_forward` é chamado e payload contém `provider_message_id`
- [x] T021 [P] [US1] Criar teste unitário em `tests/unit/test_webhook_service_forward.py`: evento `message.delivered` — verifica que `_forward` NÃO é chamado (não encaminhável na V1)
- [x] T022 [P] [US1] Criar teste unitário em `tests/unit/test_webhook_service_forward.py`: evento `unknown` — verifica que `_forward` NÃO é chamado
- [x] T023 [US2] Criar teste de integração em `tests/integration/test_n8n_forwarding.py`: fluxo completo com evento `connection.update` → verifica payload no mock n8n contém `connection_state`
- [x] T024 [US3] Criar teste de integração em `tests/integration/test_n8n_forwarding.py`: fluxo completo com evento `send.error` → verifica payload no mock n8n contém `provider_message_id` da mensagem que falhou

**Checkpoint**: Todos os tipos de eventos encaminháveis cobertos por testes

---

## Phase 5: Polish & Validação

**Purpose**: Validação cruzada e ajustes finais

- [x] T025 Validar que `app/schemas/instance.py` rejeita URLs sem scheme HTTP(S) e que `AppSettings` rejeita `N8N_FORWARD_TIMEOUT <= 0` em teste unitário `tests/unit/test_instance_schema_url.py`
- [x] T026 [P] Executar suite completa de testes (`pytest`) e corrigir falhas — 191/191 passando
- [ ] T027 Executar validação do `specs/007-n8n-forwarding/quickstart.md` manualmente (verificar fluxo end-to-end)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Sem dependências — pode iniciar imediatamente
- **Foundational (Phase 2)**: Depende de Phase 1 (T001) — BLOQUEIA user stories
- **US1+US4 (Phase 3)**: Depende de Phase 2 — MVP
- **US2+US3 (Phase 4)**: Depende de Phase 2 — pode executar em paralelo com Phase 3
- **Polish (Phase 5)**: Depende de Phases 3 e 4

### User Story Dependencies

- **US1 + US4 (P1)**: Pode iniciar após Phase 2 — nenhuma dependência em outras stories
- **US2 + US3 (P2)**: Pode iniciar após Phase 2 — independente de US1/US4 (usa mesmo mecanismo)

### Within Each Phase

- Testes marcados [P] podem executar em paralelo
- T003/T004/T005 na Phase 2 são paralelos (arquivos diferentes ou seções independentes do mesmo arquivo)
- T006/T007 são paralelos entre si

### Parallel Opportunities

- Phase 2: T004, T005, T006, T007 são todos paralelos
- Phase 3: T008-T013 (testes do forwarder) são todos paralelos; T015, T016 paralelos
- Phase 4: T019-T022 são todos paralelos
- Phase 3 e Phase 4 podem executar em paralelo após Phase 2

---

## Parallel Example: Phase 3 (MVP)

```bash
# Todos os testes do forwarder em paralelo:
Task: T008 "teste sucesso forwarder"
Task: T009 "teste timeout forwarder"
Task: T010 "teste erro HTTP 500"
Task: T011 "teste URL inválida"
Task: T012 "teste connection error"
Task: T013 "teste 2xx não-200"

# Testes do service em paralelo:
Task: T015 "teste webhook_enabled=false"
Task: T016 "teste n8n_webhook_url=None"
```

---

## Implementation Strategy

### MVP First (US1 + US4)

1. Complete Phase 1: Config (T001-T002)
2. Complete Phase 2: Forwarder improvements (T003-T007)
3. Complete Phase 3: Testes de mensagem + resiliência (T008-T018)
4. **STOP and VALIDATE**: Executar testes, verificar cenários de sucesso e falha
5. Deploy/demo se pronto

### Incremental Delivery

1. Setup + Foundational → Forwarder melhorado
2. US1+US4 → Teste cenário principal + resiliência → Deploy (MVP!)
3. US2+US3 → Teste eventos de conexão e erro → Deploy
4. Polish → Validação final → Completo

---

## Notes

- A implementação base (forwarder + integração no service) já existe da spec 006
- Esta spec foca em melhorias incrementais (timeout, validação, testes)
- Nenhuma migration necessária (schema do banco já completo)
- Nenhum endpoint novo (encaminhamento é interno)
- Bug corrigido no normalizer: send.error com data em formato lista (messages.update) agora extrai provider_message_id corretamente
