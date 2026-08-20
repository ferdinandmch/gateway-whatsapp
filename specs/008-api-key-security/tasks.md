# Tasks: Segurança com API Key

**Input**: Design documents from `specs/008-api-key-security/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Incluídos conforme feedback do projeto (testes por spec).

**Organization**: Tasks agrupadas por user story para implementação e teste independentes.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Pode rodar em paralelo (arquivos diferentes, sem dependências)
- **[Story]**: User story à qual a task pertence (US1, US2, US3, US4)
- Caminhos exatos incluídos nas descrições

---

## Phase 1: Setup

**Purpose**: Criação de infraestrutura compartilhada de segurança

- [X] T001 [P] Criar módulo de segurança com funções generate_api_key() e hash_api_key() em app/core/security.py
- [X] T002 [P] Adicionar ADMIN_TOKEN como variável obrigatória em app/core/config.py
- [X] T003 [P] Criar schemas Pydantic de client (request/response) em app/schemas/client.py
- [X] T004 Atualizar .env.example com ADMIN_TOKEN

**Checkpoint**: Infraestrutura de segurança pronta para uso nas user stories.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Dependência verify_admin_token e correção do comportamento de cliente inativo

**⚠️ CRITICAL**: Nenhuma user story pode começar até esta fase estar completa.

- [X] T005 Criar dependência verify_admin_token em app/core/dependencies.py usando secrets.compare_digest
- [X] T006 Corrigir get_current_client em app/core/dependencies.py: cliente inativo deve retornar 401 (não 403) com mesma mensagem de chave inválida
- [X] T007 Refatorar get_current_client para usar hash_api_key() de app/core/security.py em vez de _hash_api_key() inline

**Checkpoint**: Foundation ready — implementação das user stories pode começar.

---

## Phase 3: User Story 1 - Validação de requisição autenticada (Priority: P1) 🎯 MVP

**Goal**: Garantir que todas as rotas protegidas rejeitam requisições sem API Key válida e identificam o cliente corretamente.

**Depende de**: T006 (correção 401 para inativo)

**Independent Test**: Enviar requisições com/sem API Key válida às rotas protegidas e verificar respostas 401/200.

### Tests for User Story 1

- [X] T008 [P] [US1] Teste unitário de hash_api_key() e generate_api_key() em tests/unit/test_security.py
- [X] T009 [P] [US1] Teste de integração: requisição sem header retorna 401 em tests/integration/test_auth.py
- [X] T010 [P] [US1] Teste de integração: requisição com API Key inválida retorna 401 em tests/integration/test_auth.py
- [X] T011 [P] [US1] Teste de integração: requisição com API Key válida retorna 200 e identifica cliente em tests/integration/test_auth.py
- [X] T012 [P] [US1] Teste de integração: requisição com API Key de cliente inativo retorna 401 em tests/integration/test_auth.py
- [X] T013 [P] [US1] Teste de integração: header X-API-Key presente mas vazio retorna 401 em tests/integration/test_auth.py

### Implementation for User Story 1

- [X] T014 [US1] Auditar e confirmar que todas as rotas /v1/instances/* usam Depends(get_current_client) em app/api/v1/routes/instances.py — se alguma rota não usar, adicionar a dependência
- [X] T015 [US1] Auditar e confirmar que todas as rotas /v1/messages/* usam Depends(get_current_client) em app/api/v1/routes/messages.py — se alguma rota não usar, adicionar a dependência

**Checkpoint**: User Story 1 completa — autenticação funcional e testada em todas as rotas protegidas.

---

## Phase 4: User Story 2 - Geração de API Key para cliente (Priority: P1)

**Goal**: Permitir criação de clientes via endpoint protegido por token admin, retornando API Key uma única vez.

**Independent Test**: Criar cliente via POST /v1/clients e usar a API Key retornada para acessar rotas protegidas.

### Tests for User Story 2

- [X] T016 [P] [US2] Teste de integração: POST /v1/clients sem X-Admin-Token retorna 401 em tests/integration/test_clients.py
- [X] T017 [P] [US2] Teste de integração: POST /v1/clients com token admin válido cria cliente e retorna api_key em tests/integration/test_clients.py
- [X] T018 [P] [US2] Teste de integração: API Key retornada na criação funciona em rotas protegidas em tests/integration/test_clients.py
- [X] T019 [P] [US2] Teste de integração: POST /v1/clients com body inválido retorna 422 em tests/integration/test_clients.py
- [X] T020 [P] [US2] Teste unitário: generate_api_key() retorna formato zapi_ + 32 hex chars em tests/unit/test_security.py
- [X] T020b [P] [US2] Teste unitário: ClientService rejeita criação se client já possui api_key_hash em tests/unit/test_client_service.py

### Implementation for User Story 2

- [X] T021 [US2] Criar ClientService com método create_client() em app/services/client_service.py — validar que client não possui api_key_hash existente antes de gerar nova key
- [X] T022 [US2] Criar rota POST /v1/clients protegida por verify_admin_token em app/api/v1/routes/clients.py
- [X] T023 [US2] Registrar router de clients no app principal em app/main.py
- [X] T024 [US2] Atualizar scripts/create_client.py: importar generate_api_key() e hash_api_key() de app/core/security.py, substituir token_hex(24) por generate_api_key() que usa token_hex(16)

**Checkpoint**: User Story 2 completa — clientes podem ser criados via API e suas API Keys funcionam.

---

## Phase 5: User Story 3 - Proteção do webhook (Priority: P2)

**Goal**: Garantir que o endpoint de webhook rejeita requisições sem segredo válido.

**Independent Test**: Enviar requisições ao webhook com/sem X-Webhook-Secret e verificar aceitação/rejeição.

### Tests for User Story 3

- [X] T025 [P] [US3] Teste de integração: POST /v1/webhooks/evolution sem segredo retorna 401 em tests/integration/test_webhook_auth.py
- [X] T026 [P] [US3] Teste de integração: POST /v1/webhooks/evolution com segredo inválido retorna 401 em tests/integration/test_webhook_auth.py
- [X] T027 [P] [US3] Teste de integração: POST /v1/webhooks/evolution com segredo válido processa evento em tests/integration/test_webhook_auth.py

### Implementation for User Story 3

- [X] T028 [US3] Verificar que verify_webhook_secret usa secrets.compare_digest (timing-safe) em app/core/dependencies.py

**Checkpoint**: User Story 3 completa — webhook protegido contra requisições não autorizadas.

---

## Phase 6: User Story 4 - Isolamento de tokens (Priority: P2)

**Goal**: Garantir separação completa entre API Key de cliente, token admin e token interno da Evolution API.

**Independent Test**: Usar token interno da Evolution API como X-API-Key e verificar rejeição. Verificar que nenhuma resposta expõe tokens internos.

### Tests for User Story 4

- [X] T029 [P] [US4] Teste de integração: token da Evolution API usado como X-API-Key retorna 401 em tests/integration/test_token_isolation.py
- [X] T030 [P] [US4] Teste de integração: ADMIN_TOKEN usado como X-API-Key retorna 401 em tests/integration/test_token_isolation.py
- [X] T031 [P] [US4] Teste de integração: nenhuma resposta de /v1/instances contém EVOLUTION_API_KEY em tests/integration/test_token_isolation.py

### Implementation for User Story 4

- [X] T032 [US4] Revisar todos os schemas de resposta para garantir que não expõem tokens internos em app/schemas/

**Checkpoint**: User Story 4 completa — domínios de credenciais completamente isolados.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Validação final e documentação

- [X] T033 [P] Atualizar .env.example com todas as variáveis de segurança documentadas
- [X] T034 [P] Executar quickstart.md como validação end-to-end
- [X] T035 Rodar suite completa de testes: uv run pytest tests/ -v

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Sem dependências — pode começar imediatamente
- **Foundational (Phase 2)**: Depende de Phase 1 (T001 especificamente) — BLOQUEIA todas as user stories
- **US1 (Phase 3)**: Depende de Phase 2
- **US2 (Phase 4)**: Depende de Phase 2 (independente de US1)
- **US3 (Phase 5)**: Depende de Phase 2 (independente de US1 e US2)
- **US4 (Phase 6)**: Depende de Phase 2 (independente das outras)
- **Polish (Phase 7)**: Depende de todas as user stories

### User Story Dependencies

- **US1 (P1)**: Independente — valida autenticação existente + correção inativo
- **US2 (P1)**: Independente — endpoint de criação de clientes
- **US3 (P2)**: Independente — proteção do webhook
- **US4 (P2)**: Independente — validação de isolamento

### Parallel Opportunities

- T001, T002, T003, T004 podem rodar em paralelo (Phase 1)
- US1, US2, US3, US4 podem rodar em paralelo após Phase 2
- Todos os testes marcados [P] dentro de cada story podem rodar em paralelo

---

## Parallel Example: User Story 2

```bash
# Testes em paralelo:
Task: "Teste POST /v1/clients sem admin token" (T016)
Task: "Teste POST /v1/clients com admin token" (T017)
Task: "Teste API Key funciona após criação" (T018)
Task: "Teste body inválido retorna 422" (T019)
Task: "Teste formato generate_api_key()" (T020)

# Após testes falharem, implementação sequencial:
Task: "ClientService" (T021) → "Rota clients" (T022) → "Registrar router" (T023) → "Atualizar script" (T024)
```

---

## Implementation Strategy

### MVP First (User Story 1 + 2)

1. Complete Phase 1: Setup (módulo security, config, schemas)
2. Complete Phase 2: Foundational (verify_admin_token, fix 401, refator)
3. Complete Phase 3: US1 — Validação de auth existente + testes
4. Complete Phase 4: US2 — Endpoint de criação de clientes
5. **STOP and VALIDATE**: Testar fluxo completo (criar cliente → usar API Key)
6. Deploy/demo se pronto

### Incremental Delivery

1. Setup + Foundational → Infraestrutura de segurança pronta
2. US1 → Auth validada e testada → Deploy (MVP mínimo)
3. US2 → Criação de clientes via API → Deploy (MVP completo)
4. US3 → Webhook protegido → Deploy
5. US4 → Isolamento validado → Deploy (feature completa)

---

## Notes

- Projeto já possui ~70% implementado. Tasks focam em lacunas e testes.
- Correção principal: 403→401 para cliente inativo (FR impactado: FR-002)
- Formato API Key: `zapi_` + token_hex(16) = 37 chars total
- Script create_client.py usa token_hex(24) → corrigir para token_hex(16)
- Concorrência com mesma API Key: não testada na V1. SHA256 + DB lookup é stateless e thread-safe por natureza. Sem risco funcional.
- Falha de SHA256: cenário impossível em condições normais. Não requer teste dedicado.
