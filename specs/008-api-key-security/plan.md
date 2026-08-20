# Implementation Plan: Segurança com API Key

**Branch**: `008-api-key-security` | **Date**: 2026-08-19 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `specs/008-api-key-security/spec.md`

## Summary

Consolidar e completar a camada de segurança da V1: endpoint de criação de clientes protegido por token admin, correção do comportamento para cliente inativo (401 em vez de 403), padronização do formato de API Key (`zapi_` + 32 hex chars), e adição de testes automatizados abrangentes.

## Technical Context

**Language/Version**: Python 3.12  
**Primary Dependencies**: FastAPI, SQLAlchemy, Pydantic, HTTPX  
**Storage**: PostgreSQL (via asyncpg)  
**Testing**: pytest + pytest-asyncio  
**Target Platform**: Linux server (Docker)  
**Project Type**: Web service (REST API)  
**Performance Goals**: Overhead de autenticação < 200ms por requisição  
**Constraints**: Hash com SHA256 + salt (já implementado); segredos via env vars  
**Scale/Scope**: V1, cliente único → poucos clientes simultâneos

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Princípio | Status | Observação |
|-----------|--------|------------|
| 2.1 Backend como camada central | ✅ Pass | Auth é responsabilidade do backend |
| 2.2 Desacoplamento do provider | ✅ Pass | API Keys são independentes do token Evolution |
| 2.3 Contratos próprios | ✅ Pass | Endpoints com schemas Pydantic próprios |
| 4 Stack aprovada | ✅ Pass | Sem novas dependências |
| 5.1 Autenticação por API Key | ✅ Pass | Implementação direta do princípio |
| 5.2 Segredos via env vars | ✅ Pass | ADMIN_TOKEN, API_KEY_SALT, WEBHOOK_SECRET em .env |
| 5.3 Isolamento entre clientes | ✅ Pass | Cada cliente tem sua API Key |
| 8.3 Formato de erro padrão | ✅ Pass | Erros 401 seguem formato `{code, message, details}` |
| 13 Escopo V1 | ✅ Pass | Funcionalidade prevista no escopo |
| 14 Simplicidade | ✅ Pass | SHA256 + salt, sem over-engineering |

**Gate result: PASS** — Nenhuma violação.

## Project Structure

### Documentation (this feature)

```text
specs/008-api-key-security/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit-tasks)
```

### Source Code (repository root)

```text
app/
├── api/v1/routes/
│   ├── clients.py          # NOVO: endpoint POST /v1/clients
│   ├── instances.py        # EXISTENTE: já usa get_current_client
│   ├── messages.py         # EXISTENTE: já usa get_current_client
│   └── webhooks.py         # EXISTENTE: já usa verify_webhook_secret
├── core/
│   ├── config.py           # MODIFICAR: adicionar ADMIN_TOKEN
│   ├── dependencies.py     # MODIFICAR: corrigir 403→401 para inativo; add verify_admin_token
│   └── security.py         # NOVO: funções de geração/hash de API Key
├── models/
│   └── client.py           # EXISTENTE: modelo já completo
├── schemas/
│   └── client.py           # NOVO: schemas de request/response para clientes
├── services/
│   └── client_service.py   # NOVO: lógica de criação de clientes
scripts/
│   └── create_client.py    # EXISTENTE: atualizar para usar novo formato
tests/
├── unit/
│   └── test_security.py    # NOVO: testes de hash, geração, validação
└── integration/
    └── test_auth.py        # NOVO: testes e2e de autenticação
```

**Structure Decision**: Projeto monolítico existente. Adicionar módulos pontuais (security.py, client routes/service/schemas) sem alterar estrutura geral.

## Estado Atual (Inventário)

O que **já existe** e funciona:

| Componente | Arquivo | Status |
|------------|---------|--------|
| Modelo Client com api_key_hash | `app/models/client.py` | ✅ Completo |
| Dependência `get_current_client` | `app/core/dependencies.py` | ⚠️ Retorna 403 para inativo (deve ser 401) |
| Dependência `verify_webhook_secret` | `app/core/dependencies.py` | ✅ Completo |
| Hash SHA256 + salt | `app/core/dependencies.py` | ✅ Funcional |
| Config API_KEY_SALT, WEBHOOK_SECRET | `app/core/config.py` | ✅ Completo |
| Proteção rotas instances | `app/api/v1/routes/instances.py` | ✅ Usa get_current_client |
| Proteção rotas messages | `app/api/v1/routes/messages.py` | ✅ Usa get_current_client |
| Proteção webhook | `app/api/v1/routes/webhooks.py` | ✅ Usa verify_webhook_secret |
| Script create_client | `scripts/create_client.py` | ⚠️ Usa token_hex(24) = 48 chars, deveria ser 32 |
| Endpoint POST /v1/clients | — | ❌ Não existe |
| Token admin | — | ❌ Não existe |
| Schemas de client | — | ❌ Não existe |
| Testes de segurança | — | ❌ Não existe |

## O que precisa ser feito

1. **Corrigir `get_current_client`**: cliente inativo deve retornar 401 (mesmo que inexistente), não 403.
2. **Adicionar `ADMIN_TOKEN`** em config.py como variável de ambiente obrigatória.
3. **Criar `verify_admin_token`** em dependencies.py para proteger endpoint de clientes.
4. **Extrair lógica de segurança** para `app/core/security.py` (gerar API Key, hash).
5. **Criar endpoint `POST /v1/clients`** protegido por admin token.
6. **Criar schemas Pydantic** para request/response de clientes.
7. **Criar `client_service.py`** com lógica de criação.
8. **Corrigir formato da API Key**: `zapi_` + 32 hex chars (token_hex(16), não 24).
9. **Atualizar `scripts/create_client.py`** para usar módulo de segurança compartilhado.
10. **Adicionar migration** se necessário (modelo já tem api_key_hash, verificar se precisa de algo).
11. **Criar testes unitários** para funções de segurança.
12. **Criar testes de integração** para fluxo de autenticação completo.

## Complexity Tracking

> Nenhuma violação de constitution — tabela não aplicável.
