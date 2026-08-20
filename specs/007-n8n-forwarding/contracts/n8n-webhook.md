# Contrato: Encaminhamento para n8n

## Direção

Backend → n8n (outbound)

A spec 007 não expõe endpoints públicos novos. O encaminhamento é uma chamada HTTP interna do backend para o webhook do n8n configurado na instância.

---

## Chamada HTTP ao n8n

### Request

```http
POST {instance.n8n_webhook_url}
Content-Type: application/json
User-Agent: zapi-gateway/0.1.0
```

### Payload (corpo JSON)

Formato normalizado — nunca o payload bruto da Evolution API:

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
  "media_url": null,
  "provider_message_id": "BAE5XXXXXXXX",
  "connection_state": null,
  "timestamp": "2026-05-26T12:50:00+00:00"
}
```

### Campos do payload

| Campo | Tipo | Presença | Descrição |
|-------|------|----------|-----------|
| event_type | string | sempre | Tipo do evento: `message.received`, `connection.update`, `send.error` |
| provider | string | sempre | Provider de origem (sempre `"evolution"` na V1) |
| client_id | string (UUID) ou null | quando disponível | ID do cliente dono da instância |
| instance_id | string (UUID) ou null | quando disponível | ID da instância |
| provider_instance_name | string ou null | quando disponível | Nome da instância no provider |
| from | string ou null | em mensagens recebidas | Número do remetente (sem @s.whatsapp.net) |
| remote_jid | string ou null | em mensagens | JID completo do contato remoto |
| message_type | string ou null | em mensagens | Tipo: `text`, `image`, `audio`, `document`, `video`, `unknown` |
| content | string ou null | em mensagens de texto | Conteúdo textual da mensagem |
| media_url | string ou null | em mensagens de mídia | URL da mídia |
| provider_message_id | string ou null | quando disponível | ID da mensagem no provider |
| connection_state | string ou null | em eventos de conexão | Estado: `connected`, `connecting`, `disconnected`, `error` |
| timestamp | string (ISO 8601) ou null | quando disponível | Timestamp do evento |

---

## Critérios de sucesso da chamada

| HTTP Status | Interpretação | Ação |
|-------------|---------------|------|
| 2xx | Sucesso | `forwarded_to_n8n = true` |
| 3xx (redirect) | Seguido automaticamente (follow_redirects=True) | — |
| 4xx | Falha do lado do n8n | `forwarded_to_n8n = false`, registra erro |
| 5xx | Erro do n8n | `forwarded_to_n8n = false`, registra erro |
| Timeout | n8n não respondeu no prazo | `forwarded_to_n8n = false`, registra erro |
| Connection error | n8n indisponível | `forwarded_to_n8n = false`, registra erro |

---

## Timeout

- Configurável via `N8N_FORWARD_TIMEOUT` (default: 5 segundos)
- Inclui connection timeout + read timeout

---

## Eventos encaminháveis (V1)

| Evento | Encaminha ao n8n |
|--------|-----------------|
| message.received | Sim |
| connection.update | Sim |
| send.error | Sim |
| message.sent | Não |
| message.delivered | Não |
| message.read | Não |
| unknown | Não |

---

## Condições para encaminhamento

Todas as condições abaixo devem ser verdadeiras:

1. `instance` encontrada (não null)
2. `instance.webhook_enabled == true`
3. `instance.n8n_webhook_url` não é null e não é vazio
4. `instance.n8n_webhook_url` é uma URL HTTP(S) válida
5. `event_type` está na lista de eventos encaminháveis
