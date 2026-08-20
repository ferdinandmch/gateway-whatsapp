# Error Codes: Instâncias

Todos os erros seguem o formato padrão:

```json
{
  "code": "ERROR_CODE",
  "message": "Mensagem legível.",
  "details": {}
}
```

## Códigos específicos desta feature

| Code | HTTP | Quando |
|------|------|--------|
| UNAUTHORIZED | 401 | API Key ausente ou inválida |
| CLIENT_INACTIVE | 403 | Cliente autenticado mas inativo |
| VALIDATION_ERROR | 422 | Payload inválido (display_name vazio, URL malformada, etc.) |
| INSTANCE_NOT_FOUND | 404 | Instância não existe ou pertence a outro cliente |
| INSTANCE_LIMIT_REACHED | 409 | Cliente atingiu limite de 10 instâncias ativas |
| INSTANCE_NOT_CONNECTABLE | 409 | Instância em estado que não permite conexão (removed) |
| PROVIDER_ERROR | 502 | Falha na comunicação com o provider |
| PROVIDER_TIMEOUT | 504 | Timeout na comunicação com o provider |
| INTERNAL_ERROR | 500 | Erro inesperado do sistema |

## Regras de segurança

- Quando a instância existe mas pertence a outro cliente, retornar `INSTANCE_NOT_FOUND` (não revelar existência).
- Nunca incluir detalhes do provider em `details` que exponham URLs internas, tokens ou payloads sensíveis.
- Campo `details` pode incluir `instance_id` quando a instância é do próprio cliente.
