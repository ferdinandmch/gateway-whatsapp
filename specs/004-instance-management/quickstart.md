# Quickstart: Gerenciamento de Instâncias

## Pré-requisitos

- Docker Compose rodando (PostgreSQL, Redis, Evolution API)
- Backend rodando (`uv run uvicorn app.main:app --reload`)
- Cliente criado via script (`python scripts/create_client.py --name "Teste"`)
- API Key obtida na criação do cliente

## Fluxo básico

### 1. Criar instância

```bash
curl -X POST http://localhost:8000/v1/instances \
  -H "X-API-Key: sua_api_key" \
  -H "Content-Type: application/json" \
  -d '{"display_name": "Meu WhatsApp"}'
```

Resposta: instância criada com `status: "created"` e `id` para próximos passos.

### 2. Conectar (obter QR code)

```bash
curl -X POST http://localhost:8000/v1/instances/{instance_id}/connect \
  -H "X-API-Key: sua_api_key"
```

Resposta: `qr_code` em base64. Escanear com WhatsApp no celular.

### 3. Verificar status

```bash
curl http://localhost:8000/v1/instances/{instance_id}/status \
  -H "X-API-Key: sua_api_key"
```

Após escanear QR, status será `"connected"` com `phone_number` preenchido.

### 4. Listar instâncias

```bash
curl http://localhost:8000/v1/instances \
  -H "X-API-Key: sua_api_key"
```

### 5. Desconectar

```bash
curl -X POST http://localhost:8000/v1/instances/{instance_id}/disconnect \
  -H "X-API-Key: sua_api_key"
```

### 6. Remover

```bash
curl -X DELETE http://localhost:8000/v1/instances/{instance_id} \
  -H "X-API-Key: sua_api_key"
```

## Testes

```bash
uv run pytest tests/ -v --tb=short
```

## Troubleshooting

- **PROVIDER_ERROR na criação**: Verificar se Evolution API está rodando e `EVOLUTION_API_URL` correto
- **INSTANCE_LIMIT_REACHED**: Cliente atingiu 10 instâncias — remova instâncias não usadas
- **QR code não aparece**: Instância pode já estar conectada — verificar status primeiro
- **Status não atualiza para connected**: Verificar se webhook da Evolution está apontando para o backend
