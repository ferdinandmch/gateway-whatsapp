# Quickstart: Segurança com API Key

## Pré-requisitos

- Docker Compose rodando (`docker compose up -d`)
- Variáveis de ambiente configuradas no `.env`:
  - `API_KEY_SALT` — salt para hash de API Keys
  - `WEBHOOK_SECRET` — segredo para webhooks da Evolution API
  - `ADMIN_TOKEN` — token para endpoint administrativo de criação de clientes

## Criar um cliente

### Via endpoint (recomendado)

```bash
curl -X POST http://localhost:8000/v1/clients \
  -H "X-Admin-Token: $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Meu Cliente"}'
```

Resposta:
```json
{
  "id": "550e8400-...",
  "name": "Meu Cliente",
  "api_key": "zapi_a3f8b2c1d4e5f6a7b8c9d0e1f2a3b4c5",
  "is_active": true,
  "created_at": "2026-08-19T10:00:00Z"
}
```

**Salve a `api_key`** — ela não será exibida novamente.

### Via script CLI

```bash
uv run python scripts/create_client.py --name "Meu Cliente"
```

## Usar a API autenticada

```bash
curl http://localhost:8000/v1/instances \
  -H "X-API-Key: zapi_a3f8b2c1d4e5f6a7b8c9d0e1f2a3b4c5"
```

## Testar rejeição

```bash
# Sem header — deve retornar 401
curl -i http://localhost:8000/v1/instances

# Com key inválida — deve retornar 401
curl -i http://localhost:8000/v1/instances \
  -H "X-API-Key: zapi_invalida"
```

## Executar testes

```bash
uv run pytest tests/unit/test_security.py -v
uv run pytest tests/integration/test_auth.py -v
```
