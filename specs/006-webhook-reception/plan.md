# Implementation Plan: Recebimento de Webhooks

**Branch**: `006-webhook-reception` | **Date**: 2026-08-19 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `specs/006-webhook-reception/spec.md`

## Summary

Implementar o endpoint de recebimento de webhooks da Evolution API (`POST /v1/webhooks/evolution`) com validação de segredo compartilhado, persistência do payload bruto, identificação de instância/cliente, classificação de eventos, normalização para formato interno, registro de mensagens recebidas, atualização de status de mensagens e instâncias, e encaminhamento para o n8n quando configurado.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: FastAPI, Pydantic, SQLAlchemy, HTTPX
**Storage**: PostgreSQL (tabelas `webhook_events`, `messages`, `instances`, `error_logs` já existem)
**Testing**: pytest + pytest-asyncio
**Target Platform**: Linux server (Docker Compose)
**Project Type**: web-service
**Performance Goals**: Responder ao provider em < 3s para evitar retries
**Constraints**: Sem retry automático na V1; processamento síncrono; single WEBHOOK_SECRET para todas instâncias
**Scale/Scope**: Volume moderado de eventos; sem deduplicação na V1

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Princípio | Status | Evidência |
|-----------|--------|-----------|
| 2.1 Backend como camada central | ✅ Pass | Backend recebe webhooks diretamente do provider, n8n não recebe da Evolution API |
| 2.2 Desacoplamento do provider | ✅ Pass | Normalização converte payload da Evolution API para formato interno; classifier e normalizer encapsulam lógica específica do provider |
| 2.3 Contratos próprios | ✅ Pass | Resposta do webhook segue formato padronizado próprio; n8n recebe payload normalizado, não bruto |
| 4.1 SQLAlchemy + Pydantic separados | ✅ Pass | Model `WebhookEvent` (SQLAlchemy) separado dos schemas de processamento (Pydantic) |
| 5.2 Segredos | ✅ Pass | `WEBHOOK_SECRET` vem de variável de ambiente, já configurado em `AppSettings` |
| 6.1 Webhooks como entrada externa | ✅ Pass | Validação do segredo antes de qualquer processamento |
| 6.2 Autenticação de webhooks | ✅ Pass | Header `X-Webhook-Secret` validado; requisições inválidas rejeitadas |
| 6.3 Persistência de eventos | ✅ Pass | raw_payload salvo antes de processamento; evento preservado mesmo em falha |
| 6.4 Normalização | ✅ Pass | Normalizer converte para formato interno antes de encaminhar ao n8n |
| 6.5 Eventos desconhecidos | ✅ Pass | Classificados como "unknown", salvos, não derrubam a aplicação |
| 6.6 Falha no n8n | ✅ Pass | Evento já persistido; falha no n8n registrada mas não perde o evento |
| 7.1 Modelo interno | ✅ Pass | Mensagens usam `Message` model próprio; payload do provider em JSONB |
| 7.2 Identificador do provider | ✅ Pass | `provider_message_id` preservado para reconciliação |
| 8.3 Erros padronizados | ✅ Pass | Formato `{code, message, details}` consistente |
| 10 Observabilidade | ✅ Pass | Falhas registradas em `error_logs`; processing_status rastreado |
| 13 Escopo V1 | ✅ Pass | Recebimento de webhooks está no escopo |
| 14 Simplicidade | ✅ Pass | Sem retry, sem fila, sem deduplicação — processamento síncrono simples |

**Gate Result**: PASS — nenhuma violação detectada.

## Project Structure

### Documentation (this feature)

```text
specs/006-webhook-reception/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit-tasks)
```

### Source Code (repository root)

```text
app/
├── api/v1/routes/
│   ├── instances.py         # (existente)
│   ├── messages.py          # (existente)
│   └── webhooks.py          # NOVO — rota de webhook
├── services/
│   ├── instance_service.py  # (existente — atualizar status)
│   ├── message_service.py   # (existente)
│   └── webhook_service.py   # NOVO — orquestração do processamento
├── webhooks/
│   ├── __init__.py          # NOVO
│   ├── classifier.py        # NOVO — classificação de event_type
│   ├── normalizer.py        # NOVO — normalização para formato interno
│   └── forwarder.py         # NOVO — encaminhamento para n8n
├── schemas/
│   ├── instance.py          # (existente)
│   ├── message.py           # (existente)
│   └── webhook.py           # NOVO — schemas de request/response
├── models/
│   ├── webhook_event.py     # (existente — expandir campos)
│   ├── message.py           # (existente)
│   ├── instance.py          # (existente)
│   └── error_log.py         # (existente)
├── core/
│   ├── config.py            # (existente — WEBHOOK_SECRET já configurado)
│   └── dependencies.py      # (existente — adicionar verify_webhook_secret)

tests/
├── unit/
│   ├── test_webhook_classifier.py    # NOVO
│   ├── test_webhook_normalizer.py    # NOVO
│   └── test_webhook_service.py       # NOVO
└── integration/
    └── test_webhooks_api.py          # NOVO
```

**Structure Decision**: Segue a estrutura existente. Cria pacote `app/webhooks/` para componentes de processamento (classifier, normalizer, forwarder) separados da rota e do service. Isso mantém a camada de processamento desacoplada e testável independentemente.

## Field Mapping (spec → model)

O model `WebhookEvent` existente precisa ser expandido para incluir campos documentados em `docs/modelagem-dados.md`:

| Campo (docs) | Model atual | Ação |
|--------------|-------------|------|
| `client_id` | ausente | Adicionar (FK nullable para clients) |
| `provider` | ausente | Adicionar (VARCHAR, default "evolution") |
| `provider_instance_name` | ausente | Adicionar (VARCHAR nullable) |
| `normalized_payload` | ausente | Adicionar (JSONB nullable) |
| `forwarded_to_n8n` | ausente | Adicionar (BOOLEAN, default false) |
| `n8n_status_code` | ausente | Adicionar (INTEGER nullable) |
| `n8n_response` | ausente | Adicionar (JSONB nullable) |
| `received_at` | ausente | Adicionar (TIMESTAMP WITH TZ) |
| `forwarded_at` | ausente | Adicionar (TIMESTAMP WITH TZ nullable) |

O enum `WebhookProcessingStatus` precisa do valor `ignored` adicionado.

## Fluxo de Processamento

```text
1. Receber POST /v1/webhooks/evolution
2. Validar X-Webhook-Secret
3. Ler payload bruto
4. Criar registro inicial em webhook_events (status=received)
5. Extrair provider_instance_name do payload
6. Buscar instância pelo provider_instance_id
7. Preencher client_id e instance_id (se encontrado)
8. Classificar event_type (classifier.py)
9. Normalizar payload (normalizer.py)
10. Atualizar webhook_events com dados normalizados
11. Se message.received → registrar em messages (inbound)
12. Se message.delivered/read → atualizar status da mensagem
13. Se connection.update → atualizar status da instância
14. Se send.error → atualizar mensagem como failed
15. Encaminhar para n8n se aplicável (forwarder.py)
16. Atualizar status final do webhook_event
17. Retornar resposta HTTP
```

## Complexity Tracking

Nenhuma violação da Constitution — tabela não aplicável.
