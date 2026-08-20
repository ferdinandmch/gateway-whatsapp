# Quickstart: Envio de Mensagens

## Pré-requisitos

1. Ambiente local rodando via `docker-compose up -d`
2. Um client criado com API Key válida
3. Uma instância criada e com status `connected`

## Enviar mensagem de texto

```bash
curl -X POST http://localhost:8000/v1/messages/text \
  -H "X-API-Key: sua_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "instance_id": "uuid-da-instancia",
    "to": "5586999999999",
    "message": "Olá, tudo bem?"
  }'
```

## Enviar imagem

```bash
curl -X POST http://localhost:8000/v1/messages/image \
  -H "X-API-Key: sua_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "instance_id": "uuid-da-instancia",
    "to": "5586999999999",
    "media_url": "https://exemplo.com/imagem.jpg",
    "caption": "Minha imagem"
  }'
```

## Enviar documento

```bash
curl -X POST http://localhost:8000/v1/messages/document \
  -H "X-API-Key: sua_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "instance_id": "uuid-da-instancia",
    "to": "5586999999999",
    "media_url": "https://exemplo.com/arquivo.pdf",
    "filename": "arquivo.pdf",
    "caption": "Segue o documento"
  }'
```

## Enviar áudio

```bash
curl -X POST http://localhost:8000/v1/messages/audio \
  -H "X-API-Key: sua_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "instance_id": "uuid-da-instancia",
    "to": "5586999999999",
    "media_url": "https://exemplo.com/audio.mp3"
  }'
```

## Enviar vídeo

```bash
curl -X POST http://localhost:8000/v1/messages/video \
  -H "X-API-Key: sua_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "instance_id": "uuid-da-instancia",
    "to": "5586999999999",
    "media_url": "https://exemplo.com/video.mp4",
    "caption": "Vídeo de exemplo"
  }'
```

## Verificar erros comuns

- **401**: Verifique se o header `X-API-Key` está correto
- **404**: Verifique se `instance_id` é válido e pertence ao seu client
- **409**: Verifique se a instância está com status `connected` (use GET /v1/instances/{id}/status)
- **422**: Verifique se todos os campos obrigatórios estão presentes e o número tem 10-13 dígitos
- **502**: O provider (Evolution API) pode estar indisponível; verifique os logs
