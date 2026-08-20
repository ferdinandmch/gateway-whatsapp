# API Contracts: Instâncias

## POST /v1/instances

Criar nova instância.

**Auth**: `X-API-Key` (required)

**Request**:
```json
{
  "display_name": "Atendimento Principal",
  "n8n_webhook_url": "https://n8n.exemplo.com/webhook/whatsapp",
  "webhook_enabled": true
}
```

| Campo | Tipo | Obrigatório | Default | Validação |
|-------|------|-------------|---------|-----------|
| display_name | string | Sim | — | 1-255 chars, trimmed |
| n8n_webhook_url | string | Não | null | URL válida (http/https) |
| webhook_enabled | boolean | Não | true | — |

**Response 201**:
```json
{
  "id": "1e1d7d4a-7b8e-4ef6-a6e7-dc7d4cfd9f91",
  "display_name": "Atendimento Principal",
  "provider": "evolution",
  "provider_instance_name": "inst_a1b2c3d4",
  "status": "created",
  "phone_number": null,
  "webhook_enabled": true,
  "n8n_webhook_url": "https://n8n.exemplo.com/webhook/whatsapp",
  "created_at": "2026-08-18T12:00:00Z",
  "updated_at": "2026-08-18T12:00:00Z"
}
```

**Errors**: `UNAUTHORIZED`, `CLIENT_INACTIVE`, `VALIDATION_ERROR`, `INSTANCE_LIMIT_REACHED`, `PROVIDER_ERROR`, `INTERNAL_ERROR`

---

## GET /v1/instances

Listar instâncias do cliente autenticado.

**Auth**: `X-API-Key` (required)

**Query Params**:

| Param | Tipo | Default | Validação |
|-------|------|---------|-----------|
| limit | integer | 20 | 1-100 |
| offset | integer | 0 | >= 0 |
| status | string | — | Enum válido (filtra por status) |
| include_removed | boolean | false | Se true, inclui removidas |

**Response 200**:
```json
{
  "items": [
    {
      "id": "1e1d7d4a-7b8e-4ef6-a6e7-dc7d4cfd9f91",
      "display_name": "Atendimento Principal",
      "provider": "evolution",
      "status": "connected",
      "phone_number": "5586999999999",
      "webhook_enabled": true,
      "created_at": "2026-08-18T12:00:00Z",
      "updated_at": "2026-08-18T12:05:00Z"
    }
  ],
  "total": 3,
  "limit": 20,
  "offset": 0
}
```

**Errors**: `UNAUTHORIZED`, `CLIENT_INACTIVE`

---

## PATCH /v1/instances/{instance_id}

Atualizar configurações de uma instância existente.

**Auth**: `X-API-Key` (required)

**Path Params**: `instance_id` (UUID)

**Request** (todos os campos opcionais — enviar apenas os que deseja alterar):
```json
{
  "display_name": "Novo Nome",
  "n8n_webhook_url": "https://n8n.exemplo.com/webhook/novo",
  "webhook_enabled": false
}
```

| Campo | Tipo | Obrigatório | Validação |
|-------|------|-------------|-----------|
| display_name | string | Não | 1-255 chars se presente |
| n8n_webhook_url | string\|null | Não | URL válida ou null para remover |
| webhook_enabled | boolean | Não | — |

**Response 200**:
```json
{
  "id": "1e1d7d4a-7b8e-4ef6-a6e7-dc7d4cfd9f91",
  "display_name": "Novo Nome",
  "provider": "evolution",
  "provider_instance_name": "inst_a1b2c3d4",
  "status": "connected",
  "phone_number": "5586999999999",
  "webhook_enabled": false,
  "n8n_webhook_url": "https://n8n.exemplo.com/webhook/novo",
  "created_at": "2026-08-18T12:00:00Z",
  "updated_at": "2026-08-18T14:00:00Z"
}
```

**Notes**: Não altera status nem conexão. Instâncias removidas retornam 404.

**Errors**: `UNAUTHORIZED`, `CLIENT_INACTIVE`, `VALIDATION_ERROR`, `INSTANCE_NOT_FOUND`, `INTERNAL_ERROR`

---

## POST /v1/instances/{instance_id}/connect

Iniciar conexão da instância ao WhatsApp.

**Auth**: `X-API-Key` (required)

**Path Params**: `instance_id` (UUID)

**Request**: Body vazio `{}`

**Response 200**:
```json
{
  "instance_id": "1e1d7d4a-7b8e-4ef6-a6e7-dc7d4cfd9f91",
  "status": "connecting",
  "qr_code": "base64-encoded-qr-data",
  "pairing_code": null,
  "provider_response": {}
}
```

**Errors**: `UNAUTHORIZED`, `CLIENT_INACTIVE`, `INSTANCE_NOT_FOUND`, `PROVIDER_ERROR`, `INTERNAL_ERROR`

**Notes**: Instância deve ter status "created", "disconnected" ou "error" para permitir conexão.

---

## GET /v1/instances/{instance_id}/status

Consultar status atual da instância.

**Auth**: `X-API-Key` (required)

**Path Params**: `instance_id` (UUID)

**Response 200**:
```json
{
  "instance_id": "1e1d7d4a-7b8e-4ef6-a6e7-dc7d4cfd9f91",
  "status": "connected",
  "provider": "evolution",
  "provider_status": "open",
  "phone_number": "5586999999999",
  "connected_at": "2026-08-18T12:05:00Z",
  "disconnected_at": null
}
```

**Errors**: `UNAUTHORIZED`, `CLIENT_INACTIVE`, `INSTANCE_NOT_FOUND`, `PROVIDER_ERROR`, `INTERNAL_ERROR`

---

## POST /v1/instances/{instance_id}/disconnect

Desconectar instância do WhatsApp.

**Auth**: `X-API-Key` (required)

**Path Params**: `instance_id` (UUID)

**Request**: Body vazio `{}`

**Response 200**:
```json
{
  "instance_id": "1e1d7d4a-7b8e-4ef6-a6e7-dc7d4cfd9f91",
  "status": "disconnected",
  "disconnected_at": "2026-08-18T12:30:00Z"
}
```

**Notes**: Operação idempotente — se já desconectada, retorna status atual sem erro.

**Errors**: `UNAUTHORIZED`, `CLIENT_INACTIVE`, `INSTANCE_NOT_FOUND`, `PROVIDER_ERROR`, `INTERNAL_ERROR`

---

## DELETE /v1/instances/{instance_id}

Remover instância (soft delete).

**Auth**: `X-API-Key` (required)

**Path Params**: `instance_id` (UUID)

**Response 200**:
```json
{
  "instance_id": "1e1d7d4a-7b8e-4ef6-a6e7-dc7d4cfd9f91",
  "status": "removed"
}
```

**Notes**: Remove no provider (se suportado), marca `deleted_at` e status "removed" no banco.

**Errors**: `UNAUTHORIZED`, `CLIENT_INACTIVE`, `INSTANCE_NOT_FOUND`, `PROVIDER_ERROR`, `INTERNAL_ERROR`
