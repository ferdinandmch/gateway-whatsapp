# Data Model: Base do Backend e Infraestrutura Local

**Date**: 2026-08-15
**Spec**: [spec.md](spec.md)

## Overview

A Spec 001 não cria entidades de domínio no banco de dados. A modelagem de dados será implementada na Spec 003 (Persistência e Modelagem Inicial).

Esta spec define apenas a entidade de configuração da aplicação (não persistida).

## Configuration Entity (Runtime, não persistida)

Representação das variáveis de ambiente carregadas via Pydantic Settings.

### AppSettings

| Campo | Tipo | Obrigatório | Default | Descrição |
|-------|------|-------------|---------|-----------|
| APP_ENV | str | Sim | "development" | Ambiente de execução |
| APP_PORT | int | Sim | 8000 | Porta do backend |
| LOG_LEVEL | str | Sim | "INFO" | Nível de logging |
| HTTP_TIMEOUT | int | Sim | 30 | Timeout para chamadas HTTP (segundos) |
| DATABASE_URL | str | Sim | - | Connection string do PostgreSQL |
| REDIS_URL | str | Sim | - | Connection string do Redis |
| EVOLUTION_API_URL | str | Sim | - | URL base da Evolution API |
| EVOLUTION_API_KEY | str | Sim | - | Chave global da Evolution API |
| WEBHOOK_SECRET | str | Sim | - | Segredo para validação de webhooks |
| API_KEY_SALT | str | Sim | - | Salt para hash de API Keys |
| N8N_DEFAULT_WEBHOOK_URL | str | Sim | - | URL fallback do webhook n8n |

### Validações

- `APP_ENV` deve ser um de: `development`, `staging`, `production`
- `APP_PORT` deve estar entre 1 e 65535
- `LOG_LEVEL` deve ser um de: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`
- `HTTP_TIMEOUT` deve ser positivo
- `DATABASE_URL` deve começar com `postgresql+asyncpg://`
- URLs devem ser válidas (formato HTTP/HTTPS)

## Docker Services (Infrastructure)

| Serviço | Imagem | Porta | Volume |
|---------|--------|-------|--------|
| backend | build local (Dockerfile) | 8000:8000 | ./app:/app (dev mount) |
| postgres | postgres:16 | 5432:5432 | pgdata (named volume) |
| redis | redis:7-alpine | 6379:6379 | - |
| n8n | docker.n8n.io/n8nio/n8n | 5678:5678 | n8ndata (named volume) |
| evolution-api | evoapicloud/evolution-api:v2.3.4 | 8080:8080 | evolution_instances (named volume) |

## State Transitions

Não aplicável a esta spec. Entidades com estado (instances, messages) serão definidas nas specs 003-004.

## Relationships

Não aplicável a esta spec. Relacionamentos entre entidades serão definidos na spec 003.
