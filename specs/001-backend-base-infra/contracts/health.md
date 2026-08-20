# Contract: GET /health

**Date**: 2026-08-15
**Spec**: [spec.md](../spec.md)

## Endpoint

| Atributo | Valor |
|----------|-------|
| Method | GET |
| Path | `/health` |
| Auth | Nenhuma (endpoint público) |
| Rate Limit | Nenhum |
| Versioning | Fora do prefixo `/v1` (infra) |

## Request

Sem parâmetros, headers ou body obrigatórios.

```http
GET /health HTTP/1.1
Host: localhost:8000
```

## Response

### 200 OK

Backend operacional.

**Headers**:
```
Content-Type: application/json
```

**Body**:
```json
{
  "status": "ok",
  "service": "whatsapp-gateway",
  "version": "0.1.0"
}
```

**Schema**:
```json
{
  "type": "object",
  "required": ["status", "service", "version"],
  "properties": {
    "status": {
      "type": "string",
      "enum": ["ok"]
    },
    "service": {
      "type": "string",
      "const": "whatsapp-gateway"
    },
    "version": {
      "type": "string",
      "pattern": "^\\d+\\.\\d+\\.\\d+$"
    }
  },
  "additionalProperties": false
}
```

## Behavior

- Responde sem verificar conexão com banco, Redis ou serviços externos
- Não requer autenticação
- Tempo de resposta esperado: < 100ms
- Disponível assim que o processo Uvicorn estiver aceitando conexões

## Error Scenarios

Este endpoint não possui cenários de erro definidos na V1. Se o backend estiver inacessível, a conexão TCP falhará antes de chegar ao handler.

## OpenAPI Metadata

```yaml
tags:
  - Infrastructure
summary: Health check
description: Retorna status de saúde do backend
operationId: health_check
```
