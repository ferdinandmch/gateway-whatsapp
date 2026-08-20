# Research: Base do Backend e Infraestrutura Local

**Date**: 2026-08-15
**Spec**: [spec.md](spec.md)

## Python Version

**Decision**: Python 3.12
**Rationale**: Última versão estável com suporte LTS, melhor performance, suporte completo a type hints modernos, compatível com FastAPI, SQLAlchemy, Pydantic.
**Alternatives considered**:
- Python 3.11: Estável mas sem melhorias de performance do 3.12
- Python 3.13: Muito recente, risco de incompatibilidade com dependências

## FastAPI + Uvicorn Setup

**Decision**: FastAPI com Uvicorn como ASGI server
**Rationale**: Combinação padrão para APIs Python assíncronas. Uvicorn oferece hot reload em desenvolvimento e bom throughput em produção.
**Alternatives considered**:
- Hypercorn: Menos popular, sem vantagens claras para este caso
- Gunicorn + Uvicorn workers: Overkill para V1 local, pode ser adicionado depois

## Configuração via Pydantic Settings

**Decision**: pydantic-settings com BaseSettings para carregar variáveis de ambiente
**Rationale**: Validação automática de tipos, valores default, integração nativa com FastAPI, falha rápida se variáveis obrigatórias estiverem ausentes.
**Alternatives considered**:
- python-dotenv direto: Sem validação de tipos, sem defaults tipados
- dynaconf: Mais complexo, não necessário para V1

## Docker Compose Strategy

**Decision**: Docker Compose v2 com 5 serviços, sem healthchecks complexos na V1
**Rationale**: Simplicidade. O backend não depende funcionalmente dos outros serviços nesta spec (apenas provisiona). Healthchecks de dependência serão adicionados em specs futuras quando houver conexão ativa.
**Alternatives considered**:
- depends_on com condition: service_healthy: Requer healthcheck em cada serviço, complexidade desnecessária na V1
- Docker Compose profiles: Útil futuramente para rodar subsets, mas over-engineering para V1

## Dockerfile Strategy

**Decision**: Multi-stage build com imagem base python:3.12-slim
**Rationale**: Imagem menor, mais segura, build reproduzível. Stage de build instala dependências, stage final copia apenas o necessário.
**Alternatives considered**:
- Single-stage com python:3.12: Imagem maior (~900MB vs ~200MB)
- Alpine-based: Problemas conhecidos com compilação de dependências Python

## Logging

**Decision**: logging stdlib do Python com configuração via dictConfig, formato JSON em produção, texto legível em desenvolvimento
**Rationale**: Sem dependência extra. LOG_LEVEL controlado por env var. JSON facilita parsing por ferramentas de observabilidade.
**Alternatives considered**:
- structlog: Excelente mas dependência extra não justificada na V1
- loguru: Popular mas não é stdlib, dificulta integração com libs que usam logging padrão

## Gerenciamento de Dependências

**Decision**: uv com pyproject.toml
**Rationale**: Definido em DT-032. Rápido, moderno, resolve e instala dependências significativamente mais rápido que pip/poetry.
**Alternatives considered**:
- Poetry: Mais lento, mais complexo
- pip + requirements.txt: Menos reproduzível

## Evolution API Image

**Decision**: `evoapicloud/evolution-api:v2.3.4`
**Rationale**: Definido em DT-038. Versão estável da linha 2.3.x sem fluxos de licença complexos.
**Alternatives considered**:
- latest: Proibido por DT-004 (risco de breaking changes silenciosas)
- v2.2.x: Funcional mas com menos recursos

## n8n Image

**Decision**: `docker.n8n.io/n8nio/n8n:latest` (tag fixa em momento do desenvolvimento)
**Rationale**: n8n é consumidor de eventos, não provider crítico. Breaking changes no n8n não afetam o backend.
**Alternatives considered**:
- Versão fixa: Possível mas menos prioritário que fixar Evolution API

## Resoluções de NEEDS CLARIFICATION

Nenhum item pendente. Todas as decisões técnicas estavam previamente definidas nos documentos do projeto (DT-001 a DT-045).
