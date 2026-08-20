# Data Model: Gerenciamento de Instâncias

## Entities

### Instance (extensão do model existente)

**Tabela**: `instances`

| Campo | Tipo | Nullable | Default | Notas |
|-------|------|----------|---------|-------|
| id | UUID | NO | uuid4() | PK |
| client_id | UUID | NO | — | FK → clients.id |
| display_name | String(255) | NO | — | Nome amigável (input do operador) |
| provider_instance_id | String(255) | YES | NULL | Identificador no provider (gerado: `inst_{uuid8}`). Campo já existe no model atual |
| status | Enum | NO | "created" | created, connecting, connected, disconnected, error, removed |
| phone_number | String(20) | YES | NULL | Preenchido quando conectada |
| provider | String(50) | NO | "evolution" | Provider usado |
| n8n_webhook_url | Text | YES | NULL | URL webhook n8n para esta instância |
| webhook_enabled | Boolean | NO | True | Se eventos devem ser encaminhados |
| created_at | DateTime(tz) | NO | now() | TimestampMixin |
| updated_at | DateTime(tz) | NO | now() | TimestampMixin, onupdate |
| deleted_at | DateTime(tz) | YES | NULL | SoftDeleteMixin |

**Índices**:
- `ix_instance_client_id` (client_id) — já existe
- `ix_instance_status` (status) — já existe
- `uq_instance_provider_instance_name` (provider_instance_name) — UNIQUE, já existe

**Mudanças vs. model atual**:
- Renomear `name` → `display_name` (migration — campo passa a ser o nome amigável)
- Manter `provider_instance_id` como está (equivale ao `provider_instance_name` da spec; nome do campo preservado para evitar migration destrutiva)
- Adicionar: `phone_number`, `provider`, `n8n_webhook_url`, `webhook_enabled`
- Estender enum `InstanceStatus`: adicionar `created`, `error`, `removed`; remover `closed`
- Remover default `disconnected` do status; novo default será `created`

### Client (já existente — sem alterações)

**Tabela**: `clients`

| Campo | Tipo | Nullable | Default |
|-------|------|----------|---------|
| id | UUID | NO | uuid4() |
| name | String(255) | NO | — |
| is_active | Boolean | NO | True |
| created_at | DateTime(tz) | NO | now() |
| updated_at | DateTime(tz) | NO | now() |
| deleted_at | DateTime(tz) | YES | NULL |

## State Transitions

```text
[criar] → created
    ├── [provider falha] → error
    └── [provider OK] → created
          │
          ├── [conectar] → connecting
          │     ├── [QR escaneado / webhook] → connected
          │     └── [timeout / erro] → error
          │
          └── [remover] → removed (soft delete)

connected
    ├── [desconectar] → disconnected
    ├── [webhook desconexão] → disconnected
    └── [remover] → removed

disconnected
    ├── [conectar] → connecting
    └── [remover] → removed

error
    ├── [conectar] → connecting (retry)
    └── [remover] → removed

removed → (terminal, sem transições)
```

## Validation Rules

- `display_name`: obrigatório, 1-255 caracteres, trim whitespace. Atualizável via PATCH.
- `n8n_webhook_url`: opcional, se presente deve ser URL válida (http/https). Atualizável via PATCH.
- `webhook_enabled`: default True. Atualizável via PATCH.
- Limite: máximo 10 instâncias ativas (deleted_at IS NULL) por client_id
- `provider_instance_name`: gerado automaticamente, formato `inst_{8 hex chars}`
- `phone_number`: atualizado apenas via webhook/consulta ao provider, nunca input direto

## Relationships

```text
Client 1 ──── N Instance
Instance 1 ──── N Message (futuro, spec 005)
Instance 1 ──── N WebhookEvent (futuro, spec 006)
```
