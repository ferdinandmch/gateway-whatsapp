# Implementation Plan: Encaminhamento para n8n

**Branch**: `007-n8n-forwarding` | **Date**: 2026-08-19 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `specs/007-n8n-forwarding/spec.md`

## Summary

Endurecer e completar a implementação do encaminhamento de eventos normalizados para o n8n, que já existe de forma básica na spec 006. As melhorias incluem: timeout dedicado configurável (`N8N_FORWARD_TIMEOUT`), validação de URL antes do encaminhamento, suporte a redirects HTTP, validação de URL na criação de instância, e cobertura completa de testes.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: FastAPI, Pydantic, SQLAlchemy, HTTPX
**Storage**: PostgreSQL (tabelas existentes: `webhook_events`, `instances`, `error_logs`)
**Testing**: pytest + pytest-asyncio
**Target Platform**: Linux server (Docker Compose)
**Project Type**: web-service
**Performance Goals**: Encaminhamento adiciona no máximo 5s ao processamento do webhook (SC-002)
**Constraints**: Sem retry automático na V1; processamento síncrono; timeout dedicado de 5s
**Scale/Scope**: Volume moderado; sem fila; chamada única por evento

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Princípio | Status | Evidência |
|-----------|--------|-----------|
| 2.1 Backend como camada central | ✅ Pass | Backend encaminha ao n8n; n8n nunca recebe diretamente da Evolution API |
| 2.2 Desacoplamento do provider | ✅ Pass | n8n recebe payload normalizado, não o formato da Evolution API |
| 2.3 Contratos próprios | ✅ Pass | Payload enviado ao n8n segue formato interno padronizado (`NormalizedEvent.to_n8n_payload()`) |
| 5.2 Segredos | ✅ Pass | `N8N_FORWARD_TIMEOUT` vem de variável de ambiente; URL do n8n é por instância |
| 6.4 Normalização | ✅ Pass | Normalizer converte antes de encaminhar; n8n não depende do formato da Evolution |
| 6.6 Falha no n8n | ✅ Pass | Evento já persistido antes da tentativa de forwarding; falha registrada sem perda |
| 9.2 n8n | ✅ Pass | n8n recebe formato definido pelo backend |
| 9.3 Chamadas externas | ✅ Pass | Chamada ao n8n encapsulada em `forwarder.py`, não em regra de negócio |
| 10 Observabilidade | ✅ Pass | Falhas registradas em `error_logs`; campos de tracking no `webhook_events` |
| 13 Escopo V1 | ✅ Pass | Integração com n8n está no escopo da V1 |
| 14 Simplicidade | ✅ Pass | Sem retry, sem fila, sem deduplicação — chamada síncrona com timeout |

**Gate Result**: PASS — nenhuma violação detectada.

## Project Structure

### Documentation (this feature)

```text
specs/007-n8n-forwarding/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── n8n-webhook.md   # Contrato de chamada ao n8n
└── tasks.md             # Phase 2 output (/speckit-tasks)
```

### Source Code (repository root)

```text
app/
├── webhooks/
│   └── forwarder.py         # MODIFICAR — timeout dedicado, validação URL, follow_redirects
├── services/
│   └── webhook_service.py   # MODIFICAR — adicionar validação de URL antes de forward
├── schemas/
│   ├── webhook.py           # (existente, sem alterações)
│   └── instance.py          # MODIFICAR — validar n8n_webhook_url com HttpUrl
├── core/
│   └── config.py            # MODIFICAR — adicionar N8N_FORWARD_TIMEOUT

tests/
├── unit/
│   ├── test_forwarder.py            # NOVO — testes do forwarder isolado
│   └── test_forwarder_integration.py # NOVO — testes de integração (se necessário)
└── integration/
    └── test_n8n_forwarding.py       # NOVO — testes end-to-end do fluxo
```

**Structure Decision**: Segue estrutura existente. Não cria novos módulos — modifica os existentes criados na spec 006. Adiciona testes dedicados ao encaminhamento.

## Alterações planejadas

### 1. `app/core/config.py` — Adicionar N8N_FORWARD_TIMEOUT

```python
N8N_FORWARD_TIMEOUT: int = 5  # segundos
```

Com validador para garantir valor positivo.

### 2. `app/webhooks/forwarder.py` — Melhorias

- Usar `N8N_FORWARD_TIMEOUT` ao invés de `HTTP_TIMEOUT` genérico
- Adicionar `follow_redirects=True` no client
- Adicionar validação de URL (scheme http/https, host não vazio) antes da chamada
- Retornar `ForwardResult(success=False, ...)` quando URL inválida, sem tentar a chamada

### 3. `app/schemas/instance.py` — Validar URL no schema de criação

- Adicionar validador Pydantic para `n8n_webhook_url` que aceita apenas URLs HTTP(S) válidas ou None
- Aplicável em `InstanceCreate` e `InstanceUpdate` schemas

### 4. Testes

- Testes unitários do `forwarder.py`: sucesso, timeout, erro HTTP, URL inválida, redirect
- Testes unitários do fluxo no `webhook_service.py`: evento encaminhável vs não-encaminhável, webhook desabilitado, URL ausente
- Testes de integração: fluxo completo de webhook → forward → registro

## Complexity Tracking

Nenhuma violação da Constitution — tabela não aplicável.
