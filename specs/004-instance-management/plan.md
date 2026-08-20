# Implementation Plan: Gerenciamento de Instâncias WhatsApp

**Branch**: `004-instance-management` | **Date**: 2026-08-18 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `specs/004-instance-management/spec.md`

## Summary

Implementar o gerenciamento completo do ciclo de vida de instâncias WhatsApp — CRUD com listagem paginada, conexão via QR code, consulta de status, desconexão e remoção (soft delete) — com sincronização bidirecional entre backend e provider. O status é atualizado automaticamente via webhooks do provider. Limite fixo de 10 instâncias por cliente.

## Technical Context

**Language/Version**: Python 3.11+  
**Primary Dependencies**: FastAPI, SQLAlchemy, Pydantic, HTTPX  
**Storage**: PostgreSQL (async via asyncpg), Redis  
**Testing**: pytest + pytest-asyncio  
**Target Platform**: Linux server (Docker)  
**Project Type**: web-service  
**Performance Goals**: Operações em < 5s (criação), < 10s (conexão/QR code), < 3s (status/listagem)  
**Constraints**: Limite de 10 instâncias por cliente; soft delete para remoção  
**Scale/Scope**: V1 validação técnica — dezenas de clientes, centenas de instâncias

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Princípio | Status | Evidência |
|-----------|--------|-----------|
| 2.1 Backend como camada central | PASS | Todas as operações passam pelo backend, nunca diretamente ao provider |
| 2.2 Desacoplamento do provider | PASS | Usa interface `MessagingProvider` existente; `EvolutionProvider` implementa |
| 2.3 Contratos próprios | PASS | Schemas Pydantic próprios para request/response; payload do provider não exposto |
| 3.1 Monólito modular | PASS | Camadas separadas: routes → services → providers |
| 4 Stack aprovada | PASS | Apenas tecnologias da stack aprovada (FastAPI, SQLAlchemy, Pydantic, HTTPX) |
| 5.1 Autenticação | PASS | Rotas protegidas por API Key via header X-API-Key |
| 5.3 Isolamento entre clientes | PASS | Todas as queries filtradas por client_id; acesso negado com resposta genérica |
| 8.3 Erros padronizados | PASS | Formato {code, message, details} consistente |
| 13 Escopo V1 | PASS | "Gestão de instâncias" está explicitamente no escopo |
| 14 Simplicidade | PASS | Limite fixo no código (não configurável); soft delete simples; sem filas |

**Gate Result**: PASS — Nenhuma violação. Pode prosseguir.

## Project Structure

### Documentation (this feature)

```text
specs/004-instance-management/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── instances.md     # Endpoints de instâncias
│   └── errors.md       # Códigos de erro específicos
└── tasks.md             # Phase 2 output (/speckit-tasks)
```

### Source Code (repository root)

```text
app/
├── api/v1/routes/
│   └── instances.py         # Endpoints REST de instâncias
├── services/
│   └── instance_service.py  # Lógica de negócio de instâncias
├── schemas/
│   └── instance.py          # Pydantic schemas (request/response)
├── models/
│   └── instance.py          # Model SQLAlchemy (já existe)
├── providers/
│   ├── base.py              # Interface abstrata (já existe)
│   └── evolution/
│       └── provider.py      # Implementação Evolution (já existe)
└── core/
    └── dependencies.py      # DI (get_db, get_provider, get_current_client)

alembic/
└── versions/
    └── xxxx_add_instance_fields.py  # Migration para campos adicionais

tests/
├── unit/
│   └── test_instance_service.py
└── integration/
    └── test_instances_api.py
```

**Structure Decision**: Segue a estrutura existente do projeto (monólito modular FastAPI). Adição de rotas, service e schemas específicos para instâncias. O model já existe; precisa de migration para: renomear `name` → `display_name`, adicionar campos (`phone_number`, `provider`, `n8n_webhook_url`, `webhook_enabled`), estender enum de status. Campo `provider_instance_id` mantido como está (equivale ao `provider_instance_name` da spec).

## Complexity Tracking

Nenhuma violação — tabela não aplicável.
