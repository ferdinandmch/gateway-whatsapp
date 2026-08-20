# Quickstart: Encaminhamento para n8n

## Pré-requisitos

- Spec 006 (Recebimento de webhooks) implementada e funcional
- PostgreSQL com tabelas `webhook_events`, `instances`, `error_logs` existentes
- n8n acessível com um webhook configurado

## Configuração

Adicionar ao `.env`:

```env
N8N_FORWARD_TIMEOUT=5
```

## Verificação rápida

1. Criar instância com webhook n8n configurado:
```json
POST /v1/instances
{
  "display_name": "Teste n8n",
  "n8n_webhook_url": "https://meu-n8n.exemplo.com/webhook/test",
  "webhook_enabled": true
}
```

2. Enviar um webhook simulado (ou aguardar mensagem real no WhatsApp)

3. Verificar nos logs de webhook que `forwarded_to_n8n = true`:
```json
GET /v1/logs/webhooks?forwarded_to_n8n=true
```

4. Verificar no n8n que o webhook foi recebido com o payload normalizado

## Teste de resiliência

1. Configurar uma URL inválida na instância:
```json
PATCH → atualizar n8n_webhook_url para "https://invalido.local/webhook"
```

2. Enviar webhook → verificar que:
   - Evento salvo normalmente
   - `forwarded_to_n8n = false`
   - Erro registrado em `error_logs`
   - Resposta à Evolution API não foi afetada

## Arquivos relevantes

| Arquivo | Responsabilidade |
|---------|-----------------|
| `app/webhooks/forwarder.py` | Lógica de encaminhamento HTTP |
| `app/services/webhook_service.py` | Orquestração (decide se/quando encaminhar) |
| `app/webhooks/classifier.py` | `is_forwardable()` — define eventos encaminháveis |
| `app/schemas/webhook.py` | `NormalizedEvent.to_n8n_payload()` — formato do payload |
| `app/core/config.py` | `N8N_FORWARD_TIMEOUT` — timeout configurável |
| `app/models/webhook_event.py` | Campos de tracking do encaminhamento |
