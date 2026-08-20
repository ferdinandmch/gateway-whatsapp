# Research: Persistência e Modelagem Inicial

## 1. Connection Pool Sizing (SQLAlchemy 2.x + asyncpg)

**Decision**: pool_size=5, max_overflow=10 para V1 (ambiente de validação)

**Rationale**: O default do SQLAlchemy é pool_size=5, max_overflow=10. Para a V1 (validação técnica com escala moderada), os defaults são adequados. O asyncpg driver gerencia conexões eficientemente com estes valores. Configurar via variáveis de ambiente permite ajuste sem código.

**Alternatives considered**:
- pool_size=20: desnecessário para V1, consome mais conexões do PostgreSQL
- NullPool: inadequado para uso assíncrono em produção (cria conexão a cada request)

---

## 2. Alembic Autogenerate com Async

**Decision**: Manter o `env.py` existente (já configurado para async), apenas setar `target_metadata = Base.metadata` após importar todos os models.

**Rationale**: O `alembic/env.py` já usa `async_engine_from_config` e `pool.NullPool` (adequado para migrations). O padrão é importar os models antes de referenciar metadata para que o autogenerate detecte as tabelas.

**Alternatives considered**:
- Alembic síncrono: rejeitado pois DATABASE_URL já usa `postgresql+asyncpg://`
- Import dinâmico de models: rejeitado por fragilidade; import explícito no `__init__.py` é mais seguro

---

## 3. UUID Primary Key Pattern (SQLAlchemy 2.x Declarative)

**Decision**: Usar `mapped_column(Uuid, primary_key=True, default=uuid4)` com `uuid.uuid4` como default Python-side.

**Rationale**: SQLAlchemy 2.x tem tipo `Uuid` nativo que mapeia para `UUID` no PostgreSQL. Gerar UUID no Python (não server-side) simplifica testes e evita dependência de extensões PostgreSQL (`uuid-ossp` ou `pgcrypto`).

**Alternatives considered**:
- `server_default=text("gen_random_uuid()")`: requer PostgreSQL 13+ e adiciona dependência implícita; funciona mas é menos portável para testes
- `String(36)` com UUID como texto: rejeitado por desperdício de espaço e performance inferior em índices

---

## 4. Enum Storage Strategy

**Decision**: Usar `String` com Python `Enum` via SQLAlchemy `Enum` type com `native_enum=False` (armazena como VARCHAR).

**Rationale**: Evita criar ENUM types no PostgreSQL que complicam migrations ao adicionar novos valores (requer `ALTER TYPE ... ADD VALUE` que não pode ser revertido em transaction). VARCHAR com validação no modelo é mais simples para evolução.

**Alternatives considered**:
- PostgreSQL native ENUM: rejeitado por complexidade em migrations (adicionar valor requer DDL especial)
- Integer codes: rejeitado por falta de legibilidade no banco

---

## 5. Soft-Delete Pattern

**Decision**: Coluna `deleted_at: DateTime | None` (nullable). Registros deletados têm `deleted_at` preenchido. Queries de listagem filtram `WHERE deleted_at IS NULL` por padrão.

**Rationale**: Padrão simples e amplamente usado. Um mixin `SoftDeleteMixin` centraliza a lógica. Não adiciona complexidade de "lixeira" ou cleanup automático na V1.

**Alternatives considered**:
- `is_deleted: Boolean`: menos informativo (não registra quando foi deletado)
- Tabela de audit separada: overkill para V1
