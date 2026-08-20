# Implementation Plan: Persistência e Modelagem Inicial

**Branch**: `003-persistence-initial-modeling` | **Date**: 2026-08-16 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `specs/003-persistence-initial-modeling/spec.md`

## Summary

Definir os modelos SQLAlchemy para as 5 entidades de domínio (Client, Instance, Message, WebhookEvent, ErrorLog), configurar o Alembic para autogenerate com metadata do Base, e gerar a migration inicial que cria todas as tabelas no PostgreSQL com UUIDs, JSONB, soft-delete e índices adequados.

## Technical Context

**Language/Version**: Python 3.12
**Primary Dependencies**: SQLAlchemy 2.x (async), Alembic, asyncpg, Pydantic (schemas separados dos models)
**Storage**: PostgreSQL (via Docker Compose, já configurado)
**Testing**: pytest + pytest-asyncio
**Target Platform**: Linux server (Docker)
**Project Type**: web-service (FastAPI)
**Performance Goals**: Migrations em <10s, operações CRUD sem degradação sob uso normal
**Constraints**: Modelos ORM separados de Pydantic schemas (Constitution 4.1), soft-delete, isolamento por cliente
**Scale/Scope**: V1 — validação técnica, escala moderada

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Gate | Constitution Section | Status |
|------|---------------------|--------|
| Escopo V1 | §13 — Incluído: persistência, gestão de clientes, gestão de instâncias | PASS |
| Stack aprovada | §4 — SQLAlchemy, Alembic, PostgreSQL | PASS |
| SQLAlchemy puro (não SQLModel) | §4.1 — SQLModel NÃO será utilizado | PASS |
| Modelos ORM ≠ Pydantic Schemas | §4.1 — Separação explícita | PASS |
| Migrations via Alembic | §4.3 — Alterações reproduzíveis e versionadas | PASS |
| PostgreSQL como fonte de verdade | §4.2 — Redis não substitui PostgreSQL | PASS |
| Isolamento entre clientes | §5.3 — Recursos de um cliente não acessíveis por outro | PASS |
| Simplicidade | §14 — Solução mais simples que atende requisitos | PASS |
| Segredos via env | §5.2 — DATABASE_URL via variável de ambiente | PASS |

**Result**: All gates PASS. No violations.

## Project Structure

### Documentation (this feature)

```text
specs/003-persistence-initial-modeling/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (N/A — no new public endpoints)
└── tasks.md             # Phase 2 output (/speckit-tasks)
```

### Source Code (repository root)

```text
app/
├── core/
│   ├── config.py        # (existing) DATABASE_URL already configured
│   └── database.py      # (existing) Base, engine, session factory — enhance with pool config
├── models/
│   ├── __init__.py      # (existing) import all models for Alembic metadata
│   ├── base.py          # (new) mixin classes: TimestampMixin, SoftDeleteMixin
│   ├── client.py        # (new) Client model
│   ├── instance.py      # (new) Instance model
│   ├── message.py       # (new) Message model
│   ├── webhook_event.py # (new) WebhookEvent model
│   └── error_log.py     # (new) ErrorLog model
├── schemas/             # (future specs — not in scope here)
└── services/            # (future specs — not in scope here)

alembic/
├── env.py              # (existing) update target_metadata to use Base.metadata
└── versions/
    └── 001_initial_schema.py  # (new) migration inicial

tests/
├── unit/
│   └── test_models.py   # (new) testes de modelos e constraints
└── integration/
    └── test_migrations.py  # (new) testes de migration up/down
```

**Structure Decision**: Mantém a estrutura existente do projeto. Models em `app/models/` com um arquivo por entidade. Mixins em `base.py` para reutilizar campos comuns (timestamps, soft-delete).

## Complexity Tracking

> No violations — table not needed.

---

## Phase 0: Research

### Research Tasks

1. **Connection pool sizing**: Best practices for asyncpg pool with SQLAlchemy 2.x async
2. **Alembic autogenerate setup**: Proper async configuration with target_metadata
3. **UUID primary key pattern**: SQLAlchemy 2.x declarative UUID column with server-default

### Findings

See [research.md](research.md) for consolidated findings.

---

## Phase 1: Design

### Data Model

See [data-model.md](data-model.md) for complete entity definitions.

### Key Design Decisions

1. **Mixins for DRY**: `TimestampMixin` (created_at, updated_at) e `SoftDeleteMixin` (deleted_at) como mixins reutilizáveis
2. **Enum para estados**: `InstanceStatus` como Python Enum mapeado para varchar no banco (evita dependência de ENUM type do PostgreSQL para simplificar migrations)
3. **JSONB nativo**: Campos variáveis usam `sqlalchemy.dialects.postgresql.JSONB`
4. **Índices**: FK columns + status + created_at indexados para queries comuns
5. **Alembic target_metadata**: Aponta para `Base.metadata` importando todos os models no `__init__.py`

### Contracts

N/A — esta spec não adiciona endpoints públicos. Os modelos serão consumidos por specs futuras (004-008).

---

## Implementation Strategy

### Order of Implementation

1. `app/models/base.py` — mixins (TimestampMixin, SoftDeleteMixin)
2. `app/models/client.py` — entidade raiz
3. `app/models/instance.py` — depende de Client
4. `app/models/message.py` — depende de Instance
5. `app/models/webhook_event.py` — depende de Instance
6. `app/models/error_log.py` — standalone
7. `app/models/__init__.py` — re-export all models
8. `app/core/database.py` — adicionar pool_size, max_overflow, dependency injection
9. `alembic/env.py` — conectar target_metadata ao Base
10. Migration inicial — `alembic revision --autogenerate`
11. Testes unitários e de integração

### Dependencies Between Tasks

```text
base.py (mixins)
    ↓
client.py → instance.py → message.py
                        → webhook_event.py
error_log.py (standalone)
    ↓
models/__init__.py (imports all)
    ↓
database.py (pool config)
    ↓
alembic/env.py (metadata)
    ↓
migration
    ↓
tests
```
