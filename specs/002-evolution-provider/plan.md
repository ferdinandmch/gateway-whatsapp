# Implementation Plan: Provider Evolution API

**Branch**: `002-evolution-provider` | **Date**: 2026-08-16 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `specs/002-evolution-provider/spec.md`

## Summary

Implementar a camada de provider que abstrai toda comunicação com a Evolution API v2.3.4. Inclui: interface abstrata `MessagingProvider` (expandida da base.py existente), implementação concreta `EvolutionProvider` com operações de instância (criar, status, conectar, desconectar, deletar) e envio de mensagens (texto, imagem, áudio, documento, vídeo), modelos internos de resultado (`ProviderResult`, `ProviderError`), enums (`InstanceState`, `MessageType`), utilitário de normalização de telefone e testes unitários completos via mock HTTPX.

## Technical Context

**Language/Version**: Python 3.12
**Primary Dependencies**: FastAPI, HTTPX (async), Pydantic, pydantic-settings
**Storage**: N/A (esta spec não persiste dados — persistência é spec 003)
**Testing**: pytest, pytest-asyncio, pytest-httpx ou respx para mock HTTP
**Target Platform**: Linux container (Docker), desenvolvimento local Windows/Linux/macOS
**Project Type**: Web service (API REST) — camada interna de provider
**Performance Goals**: Operações do provider < 5s (bound pelo timeout HTTP de 30s)
**Constraints**: Falha imediata sem retry (DT-036), Evolution API v2.3.4 (DT-038)
**Scale/Scope**: Single provider, ~7 operações, ~50 testes unitários

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Princípio | Status | Verificação |
|-----------|--------|-------------|
| 2.1 Backend como camada central | PASS | Provider é camada interna, nunca exposta diretamente |
| 2.2 Desacoplamento do provider | PASS | Interface ABC + implementação concreta, sem acoplamento direto |
| 2.3 Contratos próprios | PASS | ProviderResult/ProviderError são modelos internos, não expostos à API pública |
| 2.4 Evolução do provider | PASS | Interface permite substituição sem alterar services/routes |
| 3.2 Separação API/aplicação/infra | PASS | Provider isolado em `app/providers/evolution/` |
| 4 Stack aprovada | PASS | HTTPX, Pydantic, pytest — todos na stack oficial |
| 5.2 Segredos via env vars | PASS | EVOLUTION_API_URL/KEY via settings, nunca hardcoded |
| 9.1 Evolution API encapsulada | PASS | Endpoints e payloads confinados ao provider |
| 12 Testabilidade | PASS | Interface ABC permite mock, testes sem Evolution API real |
| 13 Escopo V1 | PASS | Provider é item incluído no escopo |
| 14 Simplicidade | PASS | Falha imediata, sem retry, sem circuit breaker, sem filas |

Nenhuma violação. Gate aprovado.

## Project Structure

### Documentation (this feature)

```text
specs/002-evolution-provider/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   └── provider-interface.md
└── tasks.md             # Phase 2 output (/speckit-tasks)
```

### Source Code (repository root)

```text
app/
├── core/
│   └── phone.py                    # NEW: Normalização de telefone (DT-044)
├── providers/
│   ├── base.py                     # UPDATED: MessagingProvider ABC expandida
│   └── evolution/
│       ├── __init__.py             # UPDATED: exports
│       ├── provider.py             # NEW: EvolutionProvider implementation
│       └── schemas.py              # NEW: Schemas dos payloads da Evolution API
├── schemas/
│   └── provider.py                 # NEW: ProviderResult, ProviderError, InstanceState, MessageType

tests/
└── unit/
    └── test_provider/
        ├── __init__.py
        ├── conftest.py             # NEW: Fixtures para mock HTTPX e provider
        ├── test_evolution_provider.py  # NEW: Testes do EvolutionProvider
        └── test_phone.py           # NEW: Testes do utilitário de phone
```

**Structure Decision**: Mantém a estrutura definida na spec 001. Novos arquivos adicionados nos diretórios já existentes (`app/providers/evolution/`, `app/core/`, `app/schemas/`, `tests/unit/`).

## Complexity Tracking

Nenhuma violação — tabela não aplicável.

## Design Decisions

### D1 — WEBHOOK_BASE_URL como nova variável de ambiente

A configuração precisa de uma nova variável `WEBHOOK_BASE_URL` para construir URLs de webhook por instância. Será adicionada ao `AppSettings` e ao `.env.example`.

Valor padrão no .env.example: `http://host.docker.internal:8000`

### D2 — Schemas internos do provider separados dos schemas públicos

Os schemas em `app/providers/evolution/schemas.py` modelam os payloads específicos da Evolution API (request/response bodies). São internos ao provider e nunca expostos.

Os schemas em `app/schemas/provider.py` modelam os conceitos públicos da camada de provider (`ProviderResult`, `ProviderError`, `InstanceState`, `MessageType`) usados por services.

### D3 — MessagingProvider ABC expandida

A `base.py` atual tem apenas `send_message`. O método antigo será removido e substituído pelos 7 métodos abstratos definidos no contrato: `create_instance`, `get_instance_status`, `connect_instance`, `disconnect_instance`, `delete_instance`, `send_text`, `send_media`.

### D4 — Mock strategy para testes

Testes unitários usarão `respx` (mock de HTTPX) ou `pytest-httpx` para interceptar chamadas HTTP. Nenhum teste depende da Evolution API real.

## Post-Design Constitution Re-check

| Princípio | Status | Nota |
|-----------|--------|------|
| 2.2 Desacoplamento | PASS | Services chamarão apenas interface, nunca Evolution API diretamente |
| 2.3 Contratos próprios | PASS | `ProviderResult` é o contrato do provider → services |
| 9.3 Chamadas externas encapsuladas | PASS | HTTPX calls confinados em `EvolutionProvider` |
| 10 Observabilidade | PASS | Erros retornados com código + mensagem para logging |
| 11 Privacidade | PASS | Números de telefone normalizados, sem dados sensíveis em erros |

Gate pós-design aprovado. Pronto para `/speckit-tasks`.
