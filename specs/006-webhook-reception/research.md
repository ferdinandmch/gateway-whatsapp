# Research: Recebimento de Webhooks

**Feature**: 006-webhook-reception
**Date**: 2026-08-19

## Decisões Resolvidas

### 1. Estrutura do Payload da Evolution API

**Decisão**: O payload da Evolution API segue o formato `{event, instance, data}` conforme documentado em `docs/fluxos-webhook.md`.

**Racional**: A documentação do projeto já define exemplos concretos do formato esperado. O campo `event` contém o tipo do evento (e.g., `messages.upsert`), `instance` contém o nome da instância no provider, e `data` contém os dados variáveis do evento.

**Alternativas consideradas**: Nenhuma — formato definido pelo provider.

---

### 2. Mapeamento de Eventos Evolution → Tipos Internos

**Decisão**: Mapeamento baseado no campo `event` do payload:

| Evolution API `event` | Tipo interno |
|-----------------------|--------------|
| `messages.upsert` (fromMe=false) | `message.received` |
| `messages.upsert` (fromMe=true) | `message.sent` |
| `messages.update` (status=DELIVERY_ACK) | `message.delivered` |
| `messages.update` (status=READ) | `message.read` |
| `connection.update` | `connection.update` |
| `send.ack` (erro) | `send.error` |
| Qualquer outro | `unknown` |

**Racional**: Os nomes internos são normalizados e desacoplados dos nomes específicos da Evolution API. A classificação é feita pelo `classifier.py` que pode ser atualizado conforme a versão do provider muda.

**Alternativas consideradas**: Usar os nomes exatos da Evolution API — rejeitado por violar princípio 2.2 (desacoplamento do provider).

---

### 3. Estratégia de Lookup de Instância

**Decisão**: Buscar instância pelo campo `provider_instance_id` do model `Instance` usando o valor de `payload.instance`.

**Racional**: O model `Instance` já possui campo `provider_instance_id` (unique). O payload da Evolution API inclui o campo `instance` que corresponde diretamente a esse valor.

**Alternativas consideradas**:
- Lookup por `display_name` — rejeitado pois não é único nem confiável.
- Rota dedicada por instância (`/v1/webhooks/evolution/{instance_id}`) — rejeitado pois a Evolution API envia para um único endpoint.

---

### 4. Encaminhamento para n8n

**Decisão**: Encaminhar payload normalizado via HTTP POST para `instance.n8n_webhook_url` quando:
- `instance.webhook_enabled = true`
- `instance.n8n_webhook_url` não é nulo
- `event_type` é encaminhável (message.received, connection.update, send.error)

**Racional**: Alinhado com `docs/fluxos-webhook.md`. Eventos como `message.delivered` e `message.read` são salvos mas não encaminhados na V1.

**Alternativas consideradas**:
- Encaminhar todos os eventos — rejeitado para reduzir ruído no n8n.
- Usar fila (Redis) para encaminhamento assíncrono — rejeitado por complexidade desnecessária na V1.

---

### 5. Tratamento de Falha no n8n

**Decisão**: Tentar uma vez, registrar resultado. Se falhar:
- Marcar `forwarded_to_n8n = false`
- Registrar `n8n_status_code` e `n8n_response` quando disponíveis
- Registrar em `error_logs` com código `N8N_FORWARDING_ERROR`
- Não retentar

**Racional**: V1 prioriza simplicidade. O evento já está persistido. Retry com fila pode ser adicionado em versão futura.

**Alternativas consideradas**:
- Retry imediato (1x) — rejeitado por adicionar complexidade e latência.
- Dead letter queue — rejeitado como over-engineering para V1.

---

### 6. Processamento Síncrono vs Assíncrono

**Decisão**: Processamento síncrono dentro do handler da rota. Responder ao provider somente após concluir todo o fluxo (incluindo tentativa de encaminhamento ao n8n).

**Racional**: Simplicidade na V1. O timeout de 30s (HTTPX) é suficiente. O processamento total é rápido (lookup de instância + insert no banco + POST ao n8n).

**Alternativas consideradas**:
- Background task (FastAPI) para encaminhamento — rejeitado por dificultar rastreabilidade e testes.
- Worker com fila Redis — rejeitado para V1.

---

### 7. Expansão do Model WebhookEvent

**Decisão**: Adicionar campos faltantes via migration Alembic:
- `client_id` (UUID, FK nullable)
- `provider` (VARCHAR, default "evolution")
- `provider_instance_name` (VARCHAR nullable)
- `normalized_payload` (JSONB nullable)
- `forwarded_to_n8n` (BOOLEAN, default false)
- `n8n_status_code` (INTEGER nullable)
- `n8n_response` (JSONB nullable)
- `received_at` (TIMESTAMP WITH TZ)
- `forwarded_at` (TIMESTAMP WITH TZ nullable)
- Adicionar `ignored` ao enum `WebhookProcessingStatus`

**Racional**: O model existente é mínimo. Os campos documentados em `docs/modelagem-dados.md` são necessários para o fluxo completo.

**Alternativas consideradas**: Criar tabela separada para dados de n8n — rejeitado por fragmentação desnecessária.

---

### 8. Detecção de Tipo de Mensagem no Normalizer

**Decisão**: Detectar tipo de mensagem com base na presença de campos no payload:

| Campo presente em `data.message` | Tipo |
|----------------------------------|------|
| `conversation` ou `extendedTextMessage` | text |
| `imageMessage` | image |
| `audioMessage` | audio |
| `documentMessage` | document |
| `videoMessage` | video |
| Nenhum reconhecido | unknown |

**Racional**: A Evolution API usa chaves específicas no objeto `message` para indicar o tipo. O normalizer verifica a presença dessas chaves em ordem de prioridade.

**Alternativas consideradas**: Nenhuma viável — o formato é definido pelo provider.
