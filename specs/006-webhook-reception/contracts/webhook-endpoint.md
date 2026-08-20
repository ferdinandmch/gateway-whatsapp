# Contrato: POST /v1/webhooks/evolution

## Endpoint

```http
POST /v1/webhooks/evolution
```

## Autenticação

Segredo compartilhado via header (NÃO usa API Key do cliente):

```http
X-Webhook-Secret: {valor de WEBHOOK_SECRET}
```

## Request

### Headers obrigatórios

| Header | Tipo | Descrição |
|--------|------|-----------|
| `X-Webhook-Secret` | string | Segredo compartilhado para autenticação |
| `Content-Type` | string | `application/json` |

### Body

Payload JSON variável conforme tipo de evento da Evolution API.

Estrutura genérica:

```json
{
  "event": "messages.upsert",
  "instance": "inst_abc123",
  "data": { ... }
}
```

O body é aceito como `dict[str, Any]` sem validação de schema estrito (entrada externa tolerante).

---

## Responses

### 200 OK — Evento processado com sucesso

```json
{
  "received": true,
  "event_id": "e6aee962-294c-4f38-b377-33ef2ad667fa",
  "event_type": "message.received",
  "processing_status": "processed",
  "forwarded_to_n8n": true
}
```

### 202 Accepted — Evento recebido mas não totalmente processado

Usado para eventos desconhecidos ou quando encaminhamento ao n8n não é aplicável.

```json
{
  "received": true,
  "event_id": "e6aee962-294c-4f38-b377-33ef2ad667fa",
  "event_type": "unknown",
  "processing_status": "received",
  "forwarded_to_n8n": false
}
```

### 401 Unauthorized — Segredo inválido ou ausente

```json
{
  "code": "WEBHOOK_UNAUTHORIZED",
  "message": "Webhook não autorizado.",
  "details": {}
}
```

### 500 Internal Server Error — Falha interna de processamento

```json
{
  "code": "WEBHOOK_PROCESSING_ERROR",
  "message": "Erro ao processar webhook.",
  "details": {}
}
```

---

## Response Schema (Pydantic)

```python
class WebhookResponse(BaseModel):
    received: bool
    event_id: UUID
    event_type: str
    processing_status: str
    forwarded_to_n8n: bool
```

---

## Tipos de evento classificados

| event_type interno | Descrição |
|-------------------|-----------|
| `message.received` | Mensagem recebida de contato externo |
| `message.sent` | Confirmação de mensagem enviada |
| `message.delivered` | Mensagem entregue ao destinatário |
| `message.read` | Mensagem lida pelo destinatário |
| `connection.update` | Mudança de status de conexão da instância |
| `send.error` | Erro no envio de mensagem |
| `unknown` | Evento não reconhecido |

---

## Eventos encaminháveis ao n8n

Na V1, apenas estes tipos são encaminhados:

```text
message.received
connection.update
send.error
```

---

## Payload enviado ao n8n

O n8n recebe o payload **normalizado** (não o bruto):

```json
{
  "event_type": "message.received",
  "provider": "evolution",
  "client_id": "2b78b2c1-8c60-43a4-9bb5-cb8930d1c3c4",
  "instance_id": "1e1d7d4a-7b8e-4ef6-a6e7-dc7d4cfd9f91",
  "provider_instance_name": "inst_abc123",
  "from": "5586999999999",
  "remote_jid": "5586999999999@s.whatsapp.net",
  "message_type": "text",
  "content": "Olá",
  "provider_message_id": "BAE5XXXXXXXX",
  "timestamp": "2026-05-26T12:50:00Z"
}
```
