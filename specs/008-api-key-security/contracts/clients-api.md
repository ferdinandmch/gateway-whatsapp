# Contrato: API de Clientes

## POST /v1/clients

Cria um novo cliente e retorna a API Key gerada.

**Autenticação**: Header `X-Admin-Token` com valor igual à variável `ADMIN_TOKEN`.

### Request

**Headers**:
```
X-Admin-Token: <admin_token>
Content-Type: application/json
```

**Body**:
```json
{
  "name": "Nome do Cliente"
}
```

| Campo | Tipo | Obrigatório | Validação |
|-------|------|-------------|-----------|
| name | string | sim | 1-255 caracteres |

### Response 201 Created

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Nome do Cliente",
  "api_key": "zapi_a3f8b2c1d4e5f6a7b8c9d0e1f2a3b4c5",
  "is_active": true,
  "created_at": "2026-08-19T10:00:00Z"
}
```

**IMPORTANTE**: O campo `api_key` é retornado apenas nesta resposta. Não há como recuperá-lo depois.

### Response 401 Unauthorized

```json
{
  "code": "UNAUTHORIZED",
  "message": "Token administrativo ausente ou inválido.",
  "details": {}
}
```

### Response 422 Validation Error

```json
{
  "code": "VALIDATION_ERROR",
  "message": "Erro de validação.",
  "details": {
    "name": "Field required"
  }
}
```

---

## Autenticação de Rotas Protegidas

### Header

```
X-API-Key: zapi_a3f8b2c1d4e5f6a7b8c9d0e1f2a3b4c5
```

### Response 401 (ausente, vazia, inválida ou cliente inativo)

```json
{
  "code": "UNAUTHORIZED",
  "message": "API Key inválida.",
  "details": {}
}
```

**Nota**: Todas as situações de falha retornam a mesma resposta 401, sem diferenciar entre chave inexistente, inválida ou cliente inativo.

### Rotas protegidas por X-API-Key

- `POST /v1/instances`
- `POST /v1/instances/{id}/connect`
- `GET /v1/instances/{id}/status`
- `POST /v1/instances/{id}/disconnect`
- `DELETE /v1/instances/{id}`
- `GET /v1/instances`
- `PUT /v1/instances/{id}`
- `POST /v1/messages/text`
- `POST /v1/messages/image`
- `POST /v1/messages/audio`
- `POST /v1/messages/document`
- `POST /v1/messages/video`

---

## Autenticação do Webhook

### Header

```
X-Webhook-Secret: <webhook_secret>
```

### Response 401 (ausente ou inválido)

```json
{
  "code": "WEBHOOK_UNAUTHORIZED",
  "message": "Webhook não autorizado.",
  "details": {}
}
```

### Rota protegida por X-Webhook-Secret

- `POST /v1/webhooks/evolution`
