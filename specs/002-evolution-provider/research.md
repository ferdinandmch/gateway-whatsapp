# Research: Provider Evolution API

**Date**: 2026-08-16
**Spec**: [spec.md](spec.md)

## Evolution API v2.3.4 — Endpoints Relevantes

**Decision**: Utilizar os endpoints REST da Evolution API v2.3.4 para todas as operações do provider.
**Rationale**: A v2.3.4 é a versão estável fixada no Docker Compose (DT-038). Endpoints HTTP são o mecanismo de comunicação padrão da Evolution API.
**Alternatives considered**:
- WebSocket: Não disponível para operações de envio na v2.3.4
- gRPC: Não suportado pela Evolution API

### Endpoints mapeados

| Operação | Método | Endpoint |
|----------|--------|----------|
| Criar instância | POST | `/instance/create` |
| Status da instância | GET | `/instance/connectionState/{instanceName}` |
| Conectar (QR code) | GET | `/instance/connect/{instanceName}` |
| Logout | DELETE | `/instance/logout/{instanceName}` |
| Deletar instância | DELETE | `/instance/delete/{instanceName}` |
| Enviar texto | POST | `/message/sendText/{instanceName}` |
| Enviar mídia | POST | `/message/sendMedia/{instanceName}` |

## HTTPX como Client HTTP

**Decision**: HTTPX async com timeout configurável via `HTTP_TIMEOUT` (padrão 30s)
**Rationale**: HTTPX é a escolha aprovada na stack (DT-015). Suporte nativo a async/await, tipagem forte, API semelhante ao requests.
**Alternatives considered**:
- aiohttp: Mais verboso, API menos intuitiva, não aprovado na stack
- requests: Síncrono, bloquearia o event loop

## Padrão de Abstração do Provider

**Decision**: Interface ABC (`MessagingProvider`) com implementação concreta (`EvolutionProvider`). O provider recebe configuração via injeção (URL + API key).
**Rationale**: Desacoplamento conforme Constitution 2.2 e DT-005. Permite testes via mock e futura substituição de provider.
**Alternatives considered**:
- Funções soltas: Sem contrato formal, dificulta mock e substituição
- Protocol (typing.Protocol): Válido, mas ABC é mais explícito e a base.py já usa ABC

## Modelo de Resultado do Provider

**Decision**: Retornar dataclass/Pydantic model `ProviderResult` com campos: `success: bool`, `data: dict | None`, `error: ProviderError | None`. O `ProviderError` tem `code: str` e `message: str`.
**Rationale**: Resultado tipado e previsível. Camadas superiores verificam `success` sem precisar tratar exceções de HTTP ou parsing. Erros mapeados para códigos internos (ex: `INSTANCE_NOT_FOUND`, `PROVIDER_TIMEOUT`, `PROVIDER_UNAVAILABLE`).
**Alternatives considered**:
- Exceções customizadas: Mais Pythônico para erros, mas `ProviderResult` com success/error é mais explícito para operações que podem falhar legitimamente (instância não encontrada não é "exceção")
- Tupla (data, error): Sem tipagem forte, fácil de confundir ordem

## Normalização de Telefone

**Decision**: Utilitário em `app/core/phone.py` que aplica as regras do DT-044: remover não-numéricos, prefixar "55" se ausente, sufixar `@s.whatsapp.net`.
**Rationale**: Centraliza lógica de normalização, reutilizável por qualquer service. O provider chama esse utilitário antes de enviar.
**Alternatives considered**:
- Normalizar no service: Duplicaria lógica se múltiplos services enviarem mensagens
- Normalizar na rota: Violaria separação de responsabilidades (Constitution 3.2)

## Webhook URL por Instância

**Decision**: Nova variável `WEBHOOK_BASE_URL` nas settings. O provider constrói `{WEBHOOK_BASE_URL}/v1/webhooks/evolution/{instance_name}` ao criar instância.
**Rationale**: Conforme DT-017 (webhook preferencialmente por instância) e clarificação da spec. URL dinâmica por instância permite roteamento preciso de eventos.
**Alternatives considered**:
- URL fixa: Simplicidade, mas dificulta identificação de origem do evento
- URL passada pelo chamador: Acoplamento desnecessário, service não deveria conhecer URLs de webhook

## Política de Falha

**Decision**: Falha imediata sem retry (DT-036). Em caso de erro HTTP, timeout ou resposta inesperada, retornar `ProviderResult(success=False, error=ProviderError(...))`.
**Rationale**: V1 prioriza previsibilidade. Retry dependeria de Redis/filas fora do escopo.
**Alternatives considered**:
- Retry com backoff: Complexidade fora do escopo V1
- Circuit breaker: Overkill para validação técnica

## Estados Internos de Instância

**Decision**: 4 estados internos: `connected`, `disconnected`, `connecting`, `not_found`. Mapeados a partir dos estados da Evolution API.
**Rationale**: Conforme clarificação da spec. Conjunto mínimo que cobre todos os cenários de uso da V1.
**Alternatives considered**:
- 3 estados (sem not_found): Tratar como erro perde semântica
- 5+ estados: Complexidade desnecessária para V1

### Mapeamento Evolution API → Estados Internos

| Estado Evolution API | Estado Interno |
|---------------------|---------------|
| `open` | `connected` |
| `close` | `disconnected` |
| `connecting` | `connecting` |
| `qrcode` | `connecting` |
| (instância inexistente / 404) | `not_found` |
