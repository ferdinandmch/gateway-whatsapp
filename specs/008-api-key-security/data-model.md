# Data Model: Segurança com API Key

**Date**: 2026-08-19

## Entidades

### Client (já existente — sem alteração de schema)

```
clients
├── id: UUID (PK, default uuid4)
├── name: VARCHAR(255) NOT NULL
├── api_key_hash: VARCHAR(255) UNIQUE, NULLABLE
├── is_active: BOOLEAN NOT NULL DEFAULT true
├── created_at: TIMESTAMP NOT NULL DEFAULT now()
├── updated_at: TIMESTAMP NOT NULL DEFAULT now()
└── deleted_at: TIMESTAMP NULLABLE (soft delete)
```

**Estado**: Modelo já implementado em `app/models/client.py`. Nenhuma migration adicional necessária.

**Observações**:
- `api_key_hash` é nullable para permitir criação de cliente antes da geração de key (cenário futuro). Na V1, sempre será preenchido na criação.
- `is_active` controla acesso sem deletar o registro
- Soft delete via `deleted_at` (herdado de SoftDeleteMixin)

### Relações

```
Client 1──* Instance (via client_id FK)
Client 1──* WebhookEvent (via client_id FK)
```

## Regras de Negócio

| Regra | Descrição |
|-------|-----------|
| API Key única | Cada api_key_hash é UNIQUE no banco |
| Um client, uma key | Client pode ter no máximo uma API Key ativa |
| Hash irreversível | Nunca se recupera a key original a partir do hash |
| Soft delete preserva | Client deletado (deleted_at != null) é excluído da busca |
| Inativo = inexistente | Client com is_active=false retorna 401 (não 403) |

## Configuração (Environment Variables)

| Variável | Descrição | Obrigatória |
|----------|-----------|-------------|
| API_KEY_SALT | Salt para SHA256 hash de API Keys | ✅ Sim (já existe) |
| WEBHOOK_SECRET | Segredo para autenticação de webhooks | ✅ Sim (já existe) |
| ADMIN_TOKEN | Token para proteger endpoint de criação de clientes | ✅ Sim (**NOVO**) |

## Fluxo de Autenticação

```
Requisição com X-API-Key header
        ↓
Extrair valor do header
        ↓
Se vazio/ausente → 401
        ↓
Calcular SHA256(salt + api_key)
        ↓
Buscar client com api_key_hash == hash E deleted_at IS NULL
        ↓
Se não encontrado → 401
        ↓
Se client.is_active == false → 401
        ↓
Retornar client ao handler
```

## Fluxo de Criação de Cliente

```
POST /v1/clients com X-Admin-Token header
        ↓
Validar ADMIN_TOKEN via compare_digest
        ↓
Gerar raw_key = "zapi_" + token_hex(16)
        ↓
Calcular hash = SHA256(salt + raw_key)
        ↓
Inserir Client(name=..., api_key_hash=hash)
        ↓
Retornar {id, name, api_key: raw_key}  (única vez)
```
