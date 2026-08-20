# Data Model: Provider Evolution API

**Date**: 2026-08-16
**Spec**: [spec.md](spec.md)

## Overview

Esta spec não introduz modelos de banco de dados (persistência é responsabilidade da spec 003). Os modelos abaixo são **objetos internos em memória** usados pela camada de provider para comunicação com camadas superiores.

## Entities

### ProviderResult

Resultado padronizado de qualquer operação do provider.

| Field | Type | Description |
|-------|------|-------------|
| success | bool | Indica se a operação foi bem-sucedida |
| data | dict or None | Dados normalizados da resposta (varia por operação) |
| error | ProviderError or None | Erro mapeado, se falha |

### ProviderError

Representação interna de erro do provider.

| Field | Type | Description |
|-------|------|-------------|
| code | str | Código interno do erro (enum-like) |
| message | str | Mensagem descritiva para diagnóstico |

**Códigos de erro previstos**:

| Code | Descrição |
|------|-----------|
| `PROVIDER_TIMEOUT` | Timeout na chamada HTTP |
| `PROVIDER_UNAVAILABLE` | Connection refused / DNS failure |
| `PROVIDER_ERROR` | Erro HTTP 5xx da Evolution API |
| `INSTANCE_NOT_FOUND` | Instância não existe (404) |
| `INSTANCE_ALREADY_EXISTS` | Tentativa de criar instância duplicada |
| `INVALID_REQUEST` | Payload rejeitado pela Evolution API (4xx) |
| `UNEXPECTED_RESPONSE` | Resposta em formato inesperado |

### InstanceState (Enum)

Estados internos normalizados de uma instância.

| Value | Descrição |
|-------|-----------|
| `connected` | Instância conectada ao WhatsApp |
| `disconnected` | Instância desconectada |
| `connecting` | Em processo de conexão (aguardando scan do QR) |
| `not_found` | Instância não existe no provider |

### MessageType (Enum)

Tipos de mensagem suportados.

| Value | Descrição |
|-------|-----------|
| `text` | Mensagem de texto puro |
| `image` | Imagem com legenda opcional |
| `audio` | Arquivo de áudio |
| `document` | Documento com nome de arquivo |
| `video` | Vídeo com legenda opcional |

## Relationships

```text
EvolutionProvider
    ├── uses → ProviderResult (retorno de todas as operações)
    ├── uses → ProviderError (quando success=False)
    ├── uses → InstanceState (retorno de operações de status)
    └── uses → MessageType (parâmetro de envio de mídia)

MessagingProvider (ABC)
    └── implemented by → EvolutionProvider
```

## State Transitions (Instance)

```text
                    criar
    (não existe) ─────────→ disconnected
                                │
                      conectar  │
                                ▼
                           connecting
                                │
                      (scan QR) │
                                ▼
                            connected
                                │
                     desconectar│
                                ▼
                           disconnected
                                │
                      deletar   │
                                ▼
                          (não existe)
```

Nota: `not_found` não é um estado de transição — é o resultado de consultar uma instância que não existe ou foi deletada.
