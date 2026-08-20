# Quickstart: Recebimento de Webhooks

**Feature**: 006-webhook-reception

## Pré-requisitos

- Ambiente rodando com `docker compose up`
- Instância criada e conectada (specs 004)
- `WEBHOOK_SECRET` configurado no `.env`
- Evolution API apontando webhooks para `{WEBHOOK_BASE_URL}/v1/webhooks/evolution`

## Teste Manual

### 1. Simular webhook de mensagem recebida

```bash
curl -X POST http://localhost:8000/v1/webhooks/evolution \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Secret: ${WEBHOOK_SECRET}" \
  -d '{
    "event": "messages.upsert",
    "instance": "inst_abc123",
    "data": {
      "key": {
        "remoteJid": "5586999999999@s.whatsapp.net",
        "fromMe": false,
        "id": "BAE5XXXXXXXX"
      },
      "message": {
        "conversation": "Olá, teste de webhook"
      },
      "messageTimestamp": 1779796800
    }
  }'
```

Resposta esperada (200 OK):

```json
{
  "received": true,
  "event_id": "...",
  "event_type": "message.received",
  "processing_status": "processed",
  "forwarded_to_n8n": true
}
```

### 2. Simular webhook de conexão

```bash
curl -X POST http://localhost:8000/v1/webhooks/evolution \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Secret: ${WEBHOOK_SECRET}" \
  -d '{
    "event": "connection.update",
    "instance": "inst_abc123",
    "data": {
      "state": "open"
    }
  }'
```

### 3. Simular webhook com segredo inválido

```bash
curl -X POST http://localhost:8000/v1/webhooks/evolution \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Secret: segredo_errado" \
  -d '{"event": "test"}'
```

Resposta esperada (401):

```json
{
  "code": "WEBHOOK_UNAUTHORIZED",
  "message": "Webhook não autorizado.",
  "details": {}
}
```

### 4. Verificar mensagem registrada

```bash
curl http://localhost:8000/v1/logs/messages?direction=inbound \
  -H "X-API-Key: ${API_KEY}"
```

### 5. Verificar eventos de webhook

```bash
curl http://localhost:8000/v1/logs/webhooks \
  -H "X-API-Key: ${API_KEY}"
```

## Fluxo Real com Evolution API

Para teste com fluxo completo:

1. Criar instância via `POST /v1/instances`
2. Conectar via `POST /v1/instances/{id}/connect`
3. Escanear QR code no WhatsApp
4. Enviar mensagem para o número conectado
5. Verificar que o webhook foi recebido e a mensagem registrada

## Configuração da Evolution API

A Evolution API deve ser configurada para enviar webhooks para:

```text
{WEBHOOK_BASE_URL}/v1/webhooks/evolution
```

Com o header:

```text
X-Webhook-Secret: {WEBHOOK_SECRET}
```

Isso é feito automaticamente durante `create_instance` no EvolutionProvider (spec 002/004).
