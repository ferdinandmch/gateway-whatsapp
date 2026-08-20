# Quickstart: Provider Evolution API

**Date**: 2026-08-16

## Pré-requisitos

- Spec 001 completa (ambiente Docker rodando)
- `docker compose up` com Evolution API respondendo em `http://localhost:8080`

## Verificação Rápida

```bash
# 1. Garantir ambiente rodando
docker compose up -d

# 2. Rodar testes unitários do provider
uv run pytest tests/unit/test_provider/ -v

# 3. Verificar que a interface está implementada
uv run python -c "from app.providers.evolution.provider import EvolutionProvider; print('OK')"

# 4. Verificar utilitário de telefone
uv run python -c "from app.core.phone import normalize_phone; print(normalize_phone('86999999999'))"
# Esperado: 5586999999999@s.whatsapp.net
```

## Validação de Integração (manual, com Evolution API real)

```bash
# Criar instância de teste
curl -X POST http://localhost:8080/instance/create \
  -H "apikey: YOUR_EVOLUTION_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"instanceName": "inst_test1234", "webhook": "http://host.docker.internal:8000/v1/webhooks/evolution/inst_test1234", "webhookByEvents": false}'

# Verificar status
curl http://localhost:8080/instance/connectionState/inst_test1234 \
  -H "apikey: YOUR_EVOLUTION_API_KEY"

# Limpar
curl -X DELETE http://localhost:8080/instance/delete/inst_test1234 \
  -H "apikey: YOUR_EVOLUTION_API_KEY"
```

## Estrutura de Arquivos Criados

```text
app/
├── core/
│   └── phone.py                    # Normalização de telefone (DT-044)
├── providers/
│   ├── base.py                     # MessagingProvider ABC (atualizado)
│   └── evolution/
│       ├── __init__.py
│       ├── provider.py             # EvolutionProvider (implementação)
│       └── schemas.py              # Schemas internos do provider (payloads Evolution)
├── schemas/
│   └── provider.py                 # ProviderResult, ProviderError, InstanceState, MessageType

tests/
└── unit/
    └── test_provider/
        ├── __init__.py
        ├── test_evolution_provider.py
        ├── test_phone.py
        └── conftest.py             # Fixtures: mock httpx, provider instance
```
