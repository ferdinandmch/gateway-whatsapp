# Data Model: Envio de Mensagens

**Date**: 2026-08-18 | **Branch**: `005-message-sending`

## Entidades

### Message (existente — requer alteração)

Tabela: `messages`

| Campo | Tipo | Nullable | Notas |
|-------|------|----------|-------|
| id | UUID | NOT NULL | PK, default uuid4 |
| instance_id | UUID | NOT NULL | FK → instances.id |
| direction | Enum(inbound, outbound) | NOT NULL | |
| content_type | Enum(text, image, audio, document, video) | NOT NULL | |
| body | Text | NULL | Conteúdo textual (message para text, caption para mídia) |
| remote_jid | String(255) | NOT NULL | Número normalizado do destinatário/remetente |
| status | String(20) | NOT NULL | pending → sent / failed |
| provider_message_id | String(255) | NULL | ID retornado pelo provider |
| **media_url** | **Text** | **NULL** | **NOVO — URL da mídia enviada** |
| **filename** | **String(255)** | **NULL** | **NOVO — nome do arquivo (document)** |
| **raw_payload** | **JSONB** | **NULL** | **NOVO — resposta bruta do provider** |
| created_at | DateTime(tz) | NOT NULL | TimestampMixin |
| updated_at | DateTime(tz) | NOT NULL | TimestampMixin |

**Índices existentes**: `ix_message_instance_id`, `ix_message_created_at`, `ix_message_provider_message_id`

**Mapeamento spec→model**: `message_type`→`content_type`, `message`/`content`→`body`, `to`→`remote_jid`, `caption`→`body` (para mídia). O `client_id` não é coluna direta — derivado via `instance.client_id`.

### ErrorLog (existente — sem alteração)

Tabela: `error_logs`

| Campo | Tipo | Nullable | Notas |
|-------|------|----------|-------|
| id | UUID | NOT NULL | PK |
| context | String(255) | NOT NULL | Ex: "message.send_failed" |
| error_message | Text | NOT NULL | Descrição do erro |
| details | JSONB | NULL | Payload com instance_id, message_id, provider_error |
| created_at | DateTime(tz) | NOT NULL | |

### Instance (existente — sem alteração)

Referenciada via `instance_id` na Message. Usada para validação de ownership e status.

### Client (existente — sem alteração)

Referenciado indiretamente via Instance. Usado para autenticação e ownership.

## State Transitions

### Message Status

```
pending → sent     (provider retornou sucesso)
pending → failed   (provider retornou erro / timeout)
```

Na V1, transições são finais — não há re-tentativa nem atualização posterior (delivered/read ficam para spec de webhooks).

## Relacionamentos

```
Client 1 ── n Instance 1 ── n Message
```

## Migration Necessária

Adicionar 3 colunas à tabela `messages`:
- `media_url` (Text, nullable)
- `filename` (String(255), nullable)
- `raw_payload` (JSONB, nullable)

Alembic migration: `alembic revision --autogenerate -m "add media fields to messages"`
