## Idioma

Todas as respostas, specs, plans, tasks, documentação e artefatos gerados
devem ser escritos em **português brasileiro**. Não misturar inglês.

## Constitution (OBRIGATÓRIO)

Antes de tomar qualquer decisão técnica, arquitetural ou de implementação,
SEMPRE leia e siga a Constitution do projeto em `.specify/memory/constitution.md`.

A Constitution é o documento superior na hierarquia de decisões. Nenhuma
decisão de código, spec, plan ou task pode contradizê-la.

Regras de uso:

- Antes de implementar qualquer funcionalidade, verifique se está dentro do
  escopo da V1 (seção 13).
- Antes de adicionar dependência ou tecnologia, verifique a stack aprovada (seção 4).
- Antes de criar código que chame a Evolution API, verifique o princípio de
  desacoplamento do provider (seção 2.2).
- Antes de expor dados na API, verifique os princípios de contratos próprios (seção 2.3),
  segurança (seção 5) e privacidade (seção 11).
- Antes de tomar decisão arquitetural ambígua, siga a seção 17 (escalar/documentar).
- Sempre prefira a solução mais simples que atenda aos requisitos (seção 14).
- Nunca introduza funcionalidades fora do escopo sem decisão explícita do usuário.

## Documentação de Planejamento

Os documentos em `docs/` contêm decisões técnicas detalhadas (DT-001 a DT-045),
contratos de API, modelagem de dados, fluxos de webhook e regras de negócio.
Consulte-os como referência secundária à Constitution.

Hierarquia de decisões:
1. `.specify/memory/constitution.md` (superior)
2. `docs/decisoes-tecnicas.md` (decisões operacionais)
3. `docs/` demais documentos (detalhamento)
4. Specs/Plans/Tasks (por feature)
5. Código (implementação)

## Stack e Convenções

- Linguagem: Python
- Framework: FastAPI
- ORM: SQLAlchemy puro (NÃO usar SQLModel)
- Schemas: Pydantic
- Migrations: Alembic
- Banco: PostgreSQL
- HTTP client: HTTPX
- Testes: pytest + pytest-asyncio
- Gerenciador: uv
- Infra local: Docker Compose
- Pacote: whatsapp_gateway

## Estrutura do Projeto

```
app/
  api/v1/routes/
  services/
  providers/base.py
  providers/evolution/
  models/
  schemas/
  core/ (config, security, logging, database, redis)
alembic/
scripts/
tests/unit/
tests/integration/
```

