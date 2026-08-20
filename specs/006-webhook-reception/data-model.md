# Data Model: Recebimento de Webhooks

**Feature**: 006-webhook-reception
**Date**: 2026-08-19

## Entidades Impactadas

### 1. WebhookEvent (expansão)

Model existente em `app/models/webhook_event.py`. Precisa de migration para adicionar campos.

#### Campos a Adicionar

| Campo | Tipo | Nullable | Default | Descrição |
|-------|------|----------|---------|-----------|
| `client_id` | UUID (FK → clients.id) | Sim | None | Cliente dono da instância |
| `provider` | VARCHAR(50) | Não | "evolution" | Provider de origem |
| `provider_instance_name` | VARCHAR(255) | Sim | None | Nome da instância no provider |
| `normalized_payload` | JSONB | Sim | None | Payload convertido para formato interno |
| `forwarded_to_n8n` | BOOLEAN | Não | false | Se foi encaminhado com sucesso |
| `n8n_status_code` | INTEGER | Sim | None | HTTP status retornado pelo n8n |
| `n8n_response` | JSONB | Sim | None | Resposta do n8n |
| `received_at` | TIMESTAMP WITH TZ | Não | now() | Momento do recebimento |
| `forwarded_at` | TIMESTAMP WITH TZ | Sim | None | Momento do encaminhamento |

#### Enum WebhookProcessingStatus (expandir)

```text
received    → evento recebido e salvo
processing  → (já existe) em processamento
processed   → processado com sucesso
failed      → falha no processamento
ignored     → NOVO — evento reconhecido sem ação necessária
```

#### Índices a Adicionar

```text
ix_webhook_event_client_id
ix_webhook_event_provider_instance_name
ix_webhook_event_forwarded_to_n8n
ix_webhook_event_received_at
```

---

### 2. Message (sem alteração estrutural)

Model existente em `app/models/message.py`. Não precisa de migration.

O webhook service criará registros `Message` para mensagens recebidas (inbound) usando os campos existentes:
- `direction` = "inbound"
- `content_type` = tipo detectado pelo normalizer
- `body` = conteúdo textual ou legenda
- `remote_jid` = remetente
- `status` = "received"
- `provider_message_id` = ID da mensagem no provider
- `media_url` = URL da mídia (se aplicável)
- `raw_payload` = payload bruto do evento

Para atualização de status (delivered/read/failed), o service buscará por `provider_message_id` e atualizará `status`.

---

### 3. Instance (sem alteração estrutural)

Model existente em `app/models/instance.py`. Não precisa de migration.

O webhook service atualizará `status`, `connected_at`, `disconnected_at` com base em eventos `connection.update`.

Mapeamento de status:

| Evento do provider | Status da instância | Campos atualizados |
|-------------------|--------------------|--------------------|
| connected/open | `connected` | `status`, `connected_at` |
| connecting/qrcode | `connecting` | `status` |
| disconnected/close | `disconnected` | `status`, `disconnected_at` |
| error | `error` | `status` |

---

### 4. ErrorLog (sem alteração estrutural)

Model existente em `app/models/error_log.py`. Não precisa de migration.

Será usado para registrar:
- `INSTANCE_NOT_FOUND_FOR_WEBHOOK` — instância não encontrada
- `WEBHOOK_PROCESSING_ERROR` — falha no processamento
- `N8N_FORWARDING_ERROR` — falha no encaminhamento ao n8n

---

## Formato Normalizado (Pydantic Schema)

O payload normalizado segue o formato definido em `docs/fluxos-webhook.md`:

```json
{
  "event_type": "message.received",
  "provider": "evolution",
  "client_id": "uuid-do-cliente",
  "instance_id": "uuid-da-instancia",
  "provider_instance_name": "inst_abc123",
  "remote_jid": "5586999999999@s.whatsapp.net",
  "from": "5586999999999",
  "to": null,
  "message_type": "text",
  "content": "Olá",
  "media_url": null,
  "provider_message_id": "BAE5XXXXXXXX",
  "timestamp": "2026-05-26T12:50:00Z"
}
```

Nem todos os campos se aplicam a todos os tipos de evento. Campos não aplicáveis são `null`.

---

## Migration Necessária

Uma migration Alembic será criada para:

1. Adicionar colunas ao `webhook_events`
2. Adicionar valor `ignored` ao enum `WebhookProcessingStatus`
3. Criar índices novos

A migration deve ser incremental e não recriar a tabela.
