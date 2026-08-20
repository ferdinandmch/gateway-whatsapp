# Quickstart: Base do Backend e Infraestrutura Local

**Date**: 2026-08-15
**Spec**: [spec.md](spec.md)

## Pré-requisitos

- Docker e Docker Compose v2 instalados
- `uv` instalado (gerenciador de pacotes Python)
- Portas disponíveis: 8000, 5432, 6379, 5678, 8080

## Setup Rápido

### 1. Clonar e configurar

```bash
git clone <repo-url>
cd z_api_2
cp .env.example .env
```

### 2. Subir o ambiente

```bash
docker compose up --build
```

Aguarde todos os 5 serviços ficarem "running":
- **backend**: http://localhost:8000
- **postgres**: localhost:5432
- **redis**: localhost:6379
- **n8n**: http://localhost:5678
- **evolution-api**: http://localhost:8080

### 3. Verificar saúde

```bash
curl http://localhost:8000/health
```

Resposta esperada:
```json
{"status": "ok", "service": "whatsapp-gateway", "version": "0.1.0"}
```

### 4. Acessar documentação

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Desenvolvimento Local (sem Docker para o backend)

```bash
uv sync
uv run uvicorn app.main:app --reload --port 8000
```

Nota: PostgreSQL, Redis, n8n e Evolution API ainda precisam rodar via Docker.

## Parar o ambiente

```bash
docker compose down
```

Para remover volumes (reset completo):
```bash
docker compose down -v
```

## Variáveis de Ambiente

Ver `.env.example` para a lista completa. Variáveis obrigatórias:

| Variável | Descrição | Exemplo |
|----------|-----------|---------|
| DATABASE_URL | PostgreSQL connection string | postgresql+asyncpg://user:pass@localhost:5432/db |
| REDIS_URL | Redis connection string | redis://localhost:6379/0 |
| EVOLUTION_API_URL | URL da Evolution API | http://localhost:8080 |
| EVOLUTION_API_KEY | Chave da Evolution API | sua-chave-aqui |
| WEBHOOK_SECRET | Segredo para webhooks | um-segredo-forte |
| API_KEY_SALT | Salt para hash de API Keys | um-salt-aleatorio |
| N8N_DEFAULT_WEBHOOK_URL | URL webhook n8n | http://localhost:5678/webhook/default |

## Troubleshooting

| Problema | Solução |
|----------|---------|
| Porta em uso | Verifique processos com `lsof -i :PORTA` ou `netstat -tulpn` |
| Backend não inicia | Verifique se `.env` existe e todas variáveis obrigatórias estão presentes |
| Imagem não encontrada | Verifique conexão com internet para download das imagens Docker |
