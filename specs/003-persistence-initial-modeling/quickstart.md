# Quickstart: Persistência e Modelagem Inicial

## Pré-requisitos

- Docker Compose rodando (PostgreSQL disponível)
- Variável `DATABASE_URL` configurada no `.env` (formato: `postgresql+asyncpg://user:pass@host:5432/dbname`)
- `uv` instalado para gerenciamento de dependências

## Comandos

### Aplicar migrations

```bash
uv run alembic upgrade head
```

### Reverter última migration

```bash
uv run alembic downgrade -1
```

### Gerar nova migration (após alterar models)

```bash
uv run alembic revision --autogenerate -m "description"
```

### Verificar estado atual do banco

```bash
uv run alembic current
```

### Rodar testes

```bash
uv run pytest tests/unit/test_models.py -v
uv run pytest tests/integration/test_migrations.py -v
```

## Verificação Rápida

Após aplicar a migration, conectar no banco e verificar:

```sql
SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';
```

Deve listar: `clients`, `instances`, `messages`, `webhook_events`, `error_logs`, `alembic_version`
