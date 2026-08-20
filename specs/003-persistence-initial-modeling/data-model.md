# Data Model: Persistência e Modelagem Inicial

## Mixins

### TimestampMixin

| Field | Type | Constraints |
|-------|------|-------------|
| created_at | DateTime (UTC) | NOT NULL, default=now |
| updated_at | DateTime (UTC) | NOT NULL, default=now, onupdate=now |

### SoftDeleteMixin

| Field | Type | Constraints |
|-------|------|-------------|
| deleted_at | DateTime (UTC) | NULLABLE, default=NULL |

---

## Entities

### Client

Consumidor da API. Ponto raiz de isolamento de dados.

| Field | Type | Constraints |
|-------|------|-------------|
| id | UUID | PK, default=uuid4 |
| name | String(255) | NOT NULL |
| is_active | Boolean | NOT NULL, default=True |
| created_at | DateTime | (via TimestampMixin) |
| updated_at | DateTime | (via TimestampMixin) |
| deleted_at | DateTime | (via SoftDeleteMixin) |

**Indexes**: `ix_client_is_active`

---

### Instance

Instância WhatsApp gerenciada. Pertence a um Client.

| Field | Type | Constraints |
|-------|------|-------------|
| id | UUID | PK, default=uuid4 |
| client_id | UUID | FK → clients.id, NOT NULL |
| name | String(255) | NOT NULL |
| status | String(20) | NOT NULL, default='disconnected' |
| provider_instance_id | String(255) | NULLABLE, UNIQUE |
| created_at | DateTime | (via TimestampMixin) |
| updated_at | DateTime | (via TimestampMixin) |
| deleted_at | DateTime | (via SoftDeleteMixin) |

**Status values**: `disconnected`, `connecting`, `connected`, `closed` (terminal — instância encerrada no sistema, combinado com soft-delete. Ver DT-046 para mapeamento provider ↔ DB)

**Indexes**: `ix_instance_client_id`, `ix_instance_status`

**Relationships**: `client` → Client (many-to-one)

---

### Message

Mensagem enviada ou recebida via instância.

| Field | Type | Constraints |
|-------|------|-------------|
| id | UUID | PK, default=uuid4 |
| instance_id | UUID | FK → instances.id, NOT NULL |
| direction | String(10) | NOT NULL ('inbound' ou 'outbound') |
| content_type | String(20) | NOT NULL ('text', 'image', 'audio', 'document', 'video') |
| body | Text | NULLABLE |
| remote_jid | String(255) | NOT NULL (destinatário/remetente) |
| status | String(20) | NOT NULL, default='pending' |
| provider_message_id | String(255) | NULLABLE |
| created_at | DateTime | (via TimestampMixin) |
| updated_at | DateTime | (via TimestampMixin) |

**Status values (outbound)**: `pending`, `sent`, `delivered`, `read`, `failed`
**Status values (inbound)**: `received`, `processed`

**Indexes**: `ix_message_instance_id`, `ix_message_created_at`, `ix_message_provider_message_id`

**Relationships**: `instance` → Instance (many-to-one)

---

### WebhookEvent

Evento recebido via webhook da Evolution API.

| Field | Type | Constraints |
|-------|------|-------------|
| id | UUID | PK, default=uuid4 |
| instance_id | UUID | FK → instances.id, NULLABLE |
| event_type | String(100) | NOT NULL |
| raw_payload | JSONB | NOT NULL |
| processing_status | String(20) | NOT NULL, default='received' |
| processed_at | DateTime | NULLABLE |
| created_at | DateTime | (via TimestampMixin) |

**Processing status values**: `received`, `processing`, `processed`, `failed`

**Indexes**: `ix_webhook_event_instance_id`, `ix_webhook_event_event_type`, `ix_webhook_event_created_at`

**Relationships**: `instance` → Instance (many-to-one, nullable — evento pode chegar antes de associar à instância)

---

### ErrorLog

Registro de erro para diagnóstico.

| Field | Type | Constraints |
|-------|------|-------------|
| id | UUID | PK, default=uuid4 |
| context | String(255) | NOT NULL (ex: 'send_message', 'webhook_processing') |
| error_message | Text | NOT NULL |
| details | JSONB | NULLABLE |
| created_at | DateTime | NOT NULL, default=now |

**Indexes**: `ix_error_log_context`, `ix_error_log_created_at`

---

## Relationships Diagram

```text
Client (1) ──── (N) Instance (1) ──── (N) Message
                         │
                         └──── (N) WebhookEvent

ErrorLog (standalone)
```

## Conventions

- Todos os nomes de tabela em snake_case plural: `clients`, `instances`, `messages`, `webhook_events`, `error_logs`
- UUIDs gerados no Python (uuid4), não server-side
- Timestamps sempre em UTC
- JSONB para dados semi-estruturados variáveis
- Soft-delete apenas em Client e Instance (entidades gerenciáveis); Message e WebhookEvent são append-only (registros históricos)
