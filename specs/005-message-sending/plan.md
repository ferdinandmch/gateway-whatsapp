# Implementation Plan: Envio de Mensagens

**Branch**: `005-message-sending` | **Date**: 2026-08-18 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `specs/005-message-sending/spec.md`

## Summary

Implementar os endpoints de envio de mensagens (texto, imagem, áudio, documento, vídeo) seguindo o padrão já estabelecido pelo InstanceService. O MessageService orquestrará validações (instância do cliente, status connected, formato do número), chamará o provider via interface abstrata, registrará a tentativa no banco e retornará o resultado ao cliente.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: FastAPI, Pydantic, SQLAlchemy, HTTPX
**Storage**: PostgreSQL (tabelas `messages`, `error_logs` já existem)
**Testing**: pytest + pytest-asyncio
**Target Platform**: Linux server (Docker Compose)
**Project Type**: web-service
**Performance Goals**: < 5s por envio (inclui chamada ao provider)
**Constraints**: Timeout de 30s para chamadas ao provider; sem retry automático na V1
**Scale/Scope**: Uso individual por cliente, sem disparo em massa

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Princípio | Status | Evidência |
|-----------|--------|-----------|
| 2.1 Backend como camada central | ✅ Pass | Mensagens enviadas via API própria, não diretamente ao provider |
| 2.2 Desacoplamento do provider | ✅ Pass | Service usa `MessagingProvider` (interface abstrata); `send_text`/`send_media` já definidos |
| 2.3 Contratos próprios | ✅ Pass | Schemas Pydantic próprios para request/response; provider_message_id preservado mas payload não exposto |
| 4.1 SQLAlchemy + Pydantic separados | ✅ Pass | Model `Message` (SQLAlchemy) separado dos schemas de API (Pydantic) |
| 5.1 Autenticação | ✅ Pass | Endpoints protegidos por `get_current_client` dependency |
| 5.3 Isolamento entre clientes | ✅ Pass | Validação de que instance pertence ao client antes de enviar |
| 7.1 Modelo interno | ✅ Pass | `Message` model com campos próprios; payload do provider em `raw_payload` se necessário |
| 7.3 Formatos | ✅ Pass | text, image, audio, document, video suportados |
| 8.3 Erros padronizados | ✅ Pass | Formato `{code, message, details}` consistente |
| 13 Escopo V1 | ✅ Pass | Envio de mensagens está no escopo |
| 14 Simplicidade | ✅ Pass | Sem retry, sem fila, sem validação de media_url — modelo síncrono simples |

**Gate Result**: PASS — nenhuma violação detectada.

## Project Structure

### Documentation (this feature)

```text
specs/005-message-sending/
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
│   └── messages.py          # NOVO — rotas de mensagens
├── services/
│   ├── instance_service.py  # (existente)
│   └── message_service.py   # NOVO — lógica de envio
├── schemas/
│   ├── instance.py          # (existente)
│   └── message.py           # NOVO — request/response schemas
├── models/
│   ├── message.py           # (existente — já tem Message model)
│   └── error_log.py         # (existente)
├── providers/
│   └── base.py              # (existente — send_text, send_media já definidos)
├── core/
│   └── phone.py             # (existente — normalize_phone; adicionar validação)

tests/
├── unit/
│   ├── test_message_service.py   # NOVO
│   └── test_phone_validation.py  # NOVO
└── integration/
    └── test_messages_api.py      # NOVO
```

**Structure Decision**: Segue a estrutura existente. Novos arquivos apenas em `routes/messages.py`, `services/message_service.py`, `schemas/message.py` e testes correspondentes.

## Field Mapping (spec → model)

Os schemas Pydantic (contratos públicos) usam terminologia da spec. Internamente, o model SQLAlchemy usa nomes diferentes:

| Spec/Contract | Model (SQLAlchemy) | Notas |
|---------------|-------------------|-------|
| `message_type` | `content_type` | Enum: text, image, audio, document, video |
| `message` / `content` | `body` | Text field |
| `to` | `remote_jid` | Normalizado com prefixo 55 + @s.whatsapp.net |
| `caption` | `body` (para mídia) | Armazenado no mesmo campo `body` |

O `client_id` não existe na tabela `messages` — o client é derivado via `instance.client_id`. A validação de ownership é feita pelo MessageService consultando Instance com filtro de `client_id`.

## Complexity Tracking

Nenhuma violação da Constitution — tabela não aplicável.
