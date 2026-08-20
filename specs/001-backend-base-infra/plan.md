# Implementation Plan: Base do Backend e Infraestrutura Local

**Branch**: `001-backend-base-infra` | **Date**: 2026-08-15 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `specs/001-backend-base-infra/spec.md`

## Summary

Criar a fundação técnica do projeto: estrutura de pastas FastAPI, Docker Compose com 5 serviços (backend, postgres, redis, n8n, evolution-api), endpoint de health check, configuração via variáveis de ambiente com Pydantic Settings, logging estruturado e documentação OpenAPI automática.

## Technical Context

**Language/Version**: Python 3.12
**Primary Dependencies**: FastAPI, Pydantic, Pydantic-Settings, Uvicorn
**Storage**: PostgreSQL 16 (provisionado, sem conexão ativa nesta spec)
**Testing**: pytest, pytest-asyncio, httpx (AsyncClient), pytest-cov
**Target Platform**: Linux container (Docker), desenvolvimento local Windows/Linux/macOS
**Project Type**: Web service (API REST)
**Performance Goals**: Health check < 100ms, startup < 30s
**Constraints**: Portas fixas (8000, 5432, 6379, 5678, 8080), Evolution API v2.3.4
**Scale/Scope**: Ambiente de desenvolvimento local, single-developer

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Princípio | Status | Verificação |
|-----------|--------|-------------|
| 2.1 Backend como camada central | PASS | Backend é o serviço principal exposto |
| 2.2 Desacoplamento do provider | PASS | Evolution API apenas provisionada, sem acoplamento |
| 3.1 Monólito modular | PASS | Estrutura modular com separação de responsabilidades |
| 3.2 Separação API/aplicação/infra | PASS | Diretórios separados por camada |
| 4 Stack aprovada | PASS | Apenas tecnologias da stack oficial |
| 5.2 Segredos via env vars | PASS | Pydantic Settings lê de .env |
| 13 Escopo V1 | PASS | Infraestrutura base, sem features fora do escopo |
| 14 Simplicidade | PASS | Mínimo necessário para fundação funcional |

Nenhuma violação. Gate aprovado.

## Project Structure

### Documentation (this feature)

```text
specs/001-backend-base-infra/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── health.md
└── tasks.md
```

### Source Code (repository root)

```text
app/
├── __init__.py
├── main.py
├── api/
│   ├── __init__.py
│   ├── routes/
│   │   └── health.py
│   └── v1/
│       ├── __init__.py
│       └── routes/
│           └── __init__.py
├── services/
│   └── __init__.py
├── providers/
│   ├── __init__.py
│   ├── base.py
│   └── evolution/
│       └── __init__.py
├── models/
│   └── __init__.py
├── schemas/
│   └── __init__.py
└── core/
    ├── __init__.py
    ├── config.py
    ├── logging.py
    ├── database.py
    └── redis.py

alembic/
├── env.py
├── versions/
└── alembic.ini (at root)

scripts/
└── __init__.py

tests/
├── __init__.py
├── unit/
│   └── __init__.py
└── integration/
    └── __init__.py

docker-compose.yml
Dockerfile
pyproject.toml
.env.example
.gitignore
```

**Structure Decision**: Projeto único (web service) seguindo DT-034 da documentação. Estrutura modular com separação por camada (api, services, providers, models, schemas, core). Diretórios criados vazios (com `__init__.py`) para specs futuras.

## Test Strategy

### Unit Tests (`tests/unit/`)

| Arquivo | Módulo Testado | Cobertura |
|---------|---------------|-----------|
| `conftest.py` | Fixtures | TestClient async, mock env vars |
| `test_config.py` | `app/core/config.py` | Defaults, validação APP_ENV/LOG_LEVEL/PORT, falha com var ausente |
| `test_logging.py` | `app/core/logging.py` | JSON em production, texto em dev, LOG_LEVEL respeitado |
| `test_health.py` | `app/api/routes/health.py` | 200 OK, body correto, endpoint público |
| `test_startup.py` | `app/main.py` | Falha limpa com variável obrigatória ausente |
| `test_openapi.py` | OpenAPI metadata | /docs 200, /openapi.json contém /health |

### Fixtures (`tests/unit/conftest.py`)

- `async_client`: httpx.AsyncClient com app de teste
- `mock_settings`: Monkeypatch de variáveis de ambiente com valores válidos
- `clean_env`: Remove todas env vars do app para testar ausência

### Execução

```bash
uv run pytest tests/unit/ -v
uv run pytest tests/unit/ --cov=app --cov-report=term-missing
```

## Complexity Tracking

Nenhuma violação de Constitution. Tabela não aplicável.
