# API Contract: Messages

**Prefix**: `/v1/messages`  
**Auth**: `X-API-Key` header (obrigatório)

---

## POST /v1/messages/text

### Request

```json
{
  "instance_id": "uuid",
  "to": "5586999999999",
  "message": "Olá, tudo bem?"
}
```

| Campo | Tipo | Obrigatório | Validação |
|-------|------|-------------|-----------|
| instance_id | UUID | Sim | Deve existir e pertencer ao client |
| to | String | Sim | Apenas dígitos, 10-13 chars após strip |
| message | String | Sim | Não vazio |

### Response 200

```json
{
  "message_id": "uuid",
  "instance_id": "uuid",
  "direction": "outbound",
  "message_type": "text",
  "to": "5586999999999",
  "status": "sent",
  "provider_message_id": "BAE5XXXXXXXX",
  "created_at": "2026-08-18T12:00:00Z"
}
```

---

## POST /v1/messages/image

### Request

```json
{
  "instance_id": "uuid",
  "to": "5586999999999",
  "media_url": "https://exemplo.com/imagem.jpg",
  "caption": "Legenda opcional"
}
```

| Campo | Tipo | Obrigatório | Validação |
|-------|------|-------------|-----------|
| instance_id | UUID | Sim | |
| to | String | Sim | 10-13 dígitos |
| media_url | String (URL) | Sim | Não vazio |
| caption | String | Não | |

### Response 200

```json
{
  "message_id": "uuid",
  "instance_id": "uuid",
  "direction": "outbound",
  "message_type": "image",
  "to": "5586999999999",
  "media_url": "https://exemplo.com/imagem.jpg",
  "caption": "Legenda opcional",
  "status": "sent",
  "provider_message_id": "BAE5XXXXXXXX",
  "created_at": "2026-08-18T12:00:00Z"
}
```

---

## POST /v1/messages/audio

### Request

```json
{
  "instance_id": "uuid",
  "to": "5586999999999",
  "media_url": "https://exemplo.com/audio.mp3"
}
```

| Campo | Tipo | Obrigatório |
|-------|------|-------------|
| instance_id | UUID | Sim |
| to | String | Sim |
| media_url | String (URL) | Sim |

### Response 200

```json
{
  "message_id": "uuid",
  "instance_id": "uuid",
  "direction": "outbound",
  "message_type": "audio",
  "to": "5586999999999",
  "media_url": "https://exemplo.com/audio.mp3",
  "status": "sent",
  "provider_message_id": "BAE5XXXXXXXX",
  "created_at": "2026-08-18T12:00:00Z"
}
```

---

## POST /v1/messages/document

### Request

```json
{
  "instance_id": "uuid",
  "to": "5586999999999",
  "media_url": "https://exemplo.com/doc.pdf",
  "filename": "doc.pdf",
  "caption": "Documento"
}
```

| Campo | Tipo | Obrigatório |
|-------|------|-------------|
| instance_id | UUID | Sim |
| to | String | Sim |
| media_url | String (URL) | Sim |
| filename | String | Não (recomendado) |
| caption | String | Não |

### Response 200

```json
{
  "message_id": "uuid",
  "instance_id": "uuid",
  "direction": "outbound",
  "message_type": "document",
  "to": "5586999999999",
  "media_url": "https://exemplo.com/doc.pdf",
  "filename": "doc.pdf",
  "caption": "Documento",
  "status": "sent",
  "provider_message_id": "BAE5XXXXXXXX",
  "created_at": "2026-08-18T12:00:00Z"
}
```

---

## POST /v1/messages/video

### Request

```json
{
  "instance_id": "uuid",
  "to": "5586999999999",
  "media_url": "https://exemplo.com/video.mp4",
  "caption": "Vídeo"
}
```

| Campo | Tipo | Obrigatório |
|-------|------|-------------|
| instance_id | UUID | Sim |
| to | String | Sim |
| media_url | String (URL) | Sim |
| caption | String | Não |

### Response 200

```json
{
  "message_id": "uuid",
  "instance_id": "uuid",
  "direction": "outbound",
  "message_type": "video",
  "to": "5586999999999",
  "media_url": "https://exemplo.com/video.mp4",
  "caption": "Vídeo",
  "status": "sent",
  "provider_message_id": "BAE5XXXXXXXX",
  "created_at": "2026-08-18T12:00:00Z"
}
```

---

## Erros Comuns (todos os endpoints)

| HTTP | Code | Quando |
|------|------|--------|
| 401 | UNAUTHORIZED | API Key ausente ou inválida |
| 403 | CLIENT_INACTIVE | Cliente inativo |
| 404 | INSTANCE_NOT_FOUND | Instância não existe ou pertence a outro client |
| 409 | INSTANCE_DISCONNECTED | Instância não está connected (conflito de estado) |
| 422 | VALIDATION_ERROR | Campos obrigatórios ausentes ou formato inválido |
| 502 | PROVIDER_ERROR | Provider falhou (timeout, indisponível, erro) |
| 500 | INTERNAL_ERROR | Erro inesperado |

### Formato de erro

```json
{
  "code": "INSTANCE_DISCONNECTED",
  "message": "A instância não está conectada.",
  "details": {}
}
```
