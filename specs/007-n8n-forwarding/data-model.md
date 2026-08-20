# Data Model: Encaminhamento para n8n

## Entidades impactadas

A spec 007 não cria novas tabelas. Trabalha sobre entidades existentes criadas nas specs 003, 004 e 006.

---

## webhook_events (existente — sem alterações de schema)

Campos relevantes para o encaminhamento (já criados na spec 006):

| Campo | Tipo | Nullable | Default | Descrição |
|-------|------|----------|---------|-----------|
| forwarded_to_n8n | BOOLEAN | NOT NULL | false | Se o evento foi encaminhado com sucesso |
| n8n_status_code | INTEGER | NULL | null | HTTP status code retornado pelo n8n |
| n8n_response | JSONB | NULL | null | Body da resposta do n8n (limitado) |
| forwarded_at | TIMESTAMP WITH TZ | NULL | null | Momento do encaminhamento |

**Índice existente**: `ix_webhook_event_forwarded_to_n8n` — permite consulta de eventos não encaminhados.

---

## instances (existente — sem alterações de schema)

Campos relevantes para configuração do encaminhamento (já criados na spec 004):

| Campo | Tipo | Nullable | Default | Descrição |
|-------|------|----------|---------|-----------|
| n8n_webhook_url | TEXT | NULL | null | URL do webhook n8n para esta instância |
| webhook_enabled | BOOLEAN | NOT NULL | true | Se encaminhamento está habilitado |

**Validação a adicionar**: `n8n_webhook_url` deve ser validada como URL HTTP(S) válida no schema Pydantic de criação/atualização de instância.

---

## error_logs (existente — sem alterações de schema)

Registra falhas de encaminhamento com:

| Campo | Valor para esta feature |
|-------|------------------------|
| context | `"webhook.n8n_forwarding"` |
| error_code (em details) | `"N8N_FORWARDING_ERROR"` |
| error_message | Descrição da falha (timeout, HTTP error, URL inválida) |

---

## Configuração (AppSettings)

Novo campo a adicionar:

| Campo | Tipo | Default | Descrição |
|-------|------|---------|-----------|
| N8N_FORWARD_TIMEOUT | int | 5 | Timeout em segundos para chamadas ao n8n |

---

## Diagrama de relacionamento (relevante)

```text
instances (1) ──── (N) webhook_events
    │                       │
    │ n8n_webhook_url       │ forwarded_to_n8n
    │ webhook_enabled       │ n8n_status_code
    │                       │ n8n_response
    │                       │ forwarded_at
    │                       │
    └── error_logs (quando forwarding falha)
```

---

## Fluxo de dados no encaminhamento

```text
webhook_events.normalized_payload
        ↓
    to_n8n_payload()
        ↓
    POST → instances.n8n_webhook_url
        ↓
    webhook_events.forwarded_to_n8n = true/false
    webhook_events.n8n_status_code = HTTP status
    webhook_events.n8n_response = body
    webhook_events.forwarded_at = now()
```
