# 07 — Contratos da API

## Objetivo do documento

Este documento define os contratos iniciais da API pública da V1 do projeto **Z-API Própria / Gateway WhatsApp**.

O objetivo é padronizar:

- rotas públicas;
- métodos HTTP;
- payloads de entrada;
- respostas esperadas;
- autenticação;
- erros;
- prefixos de versão;
- responsabilidades de cada endpoint.

A API será construída com **FastAPI** e exposta sob o prefixo `/v1`, exceto o endpoint de health check.

---

## Princípios gerais da API

A API deve seguir os seguintes princípios:

- usar contratos simples e previsíveis;
- proteger rotas sensíveis com API Key;
- não expor diretamente detalhes internos da Evolution API;
- usar respostas JSON;
- retornar erros padronizados;
- manter versionamento explícito com `/v1`;
- validar payloads com Pydantic;
- manter separação entre API pública e provider interno.

---

## Prefixo da API

Todos os endpoints públicos da V1 devem usar o prefixo:

```txt
/v1
```

Exemplos:

```http
POST /v1/instances
POST /v1/messages/text
POST /v1/webhooks/evolution
GET  /v1/logs/messages
```

Exceção:

```http
GET /health
```

O endpoint `/health` pode ficar fora do prefixo `/v1`, pois serve apenas para verificação básica da aplicação.

---

## Autenticação

## Estratégia da V1

A autenticação da API pública será feita por **API Key**.

Header padrão:

```http
X-API-Key: chave_do_cliente
```

## Rotas protegidas

As seguintes rotas devem exigir API Key:

```txt
/v1/instances/*
/v1/messages/*
/v1/logs/*
```

## Rotas com proteção específica

A rota de webhook da Evolution API não usará API Key do cliente.

Ela usará proteção própria via segredo compartilhado.

Header recomendado:

```http
X-Webhook-Secret: segredo_interno
```

Rota:

```http
POST /v1/webhooks/evolution
```

## Rotas públicas

```http
GET /health
```

---

## Formato padrão de erro

Todos os erros da API devem seguir o formato:

```json
{
  "code": "ERROR_CODE",
  "message": "Mensagem legível do erro.",
  "details": {}
}
```

## Exemplos de códigos de erro

```txt
UNAUTHORIZED
CLIENT_INACTIVE
VALIDATION_ERROR
INSTANCE_NOT_FOUND
INSTANCE_DISCONNECTED
MESSAGE_SEND_FAILED
PROVIDER_ERROR
WEBHOOK_UNAUTHORIZED
WEBHOOK_PROCESSING_ERROR
N8N_FORWARDING_ERROR
INTERNAL_ERROR
```

---

## Status HTTP recomendados

```txt
200 OK                  = operação concluída com sucesso
201 Created             = recurso criado
202 Accepted            = requisição aceita para processamento
400 Bad Request         = payload inválido ou regra violada
401 Unauthorized        = autenticação ausente ou inválida
403 Forbidden           = cliente autenticado, mas sem permissão/status inválido
404 Not Found           = recurso não encontrado
409 Conflict            = conflito de estado ou recurso duplicado
422 Unprocessable Entity = erro de validação do FastAPI/Pydantic
500 Internal Server Error = erro inesperado
502 Bad Gateway         = erro ao chamar provider externo
503 Service Unavailable = provider indisponível
```

---

# 1. Health check

## Endpoint

```http
GET /health
```

## Autenticação

Não exige API Key.

## Objetivo

Verificar se o backend está respondendo.

## Resposta de sucesso

Status:

```http
200 OK
```

Body:

```json
{
  "status": "ok",
  "service": "zapi-gateway",
  "version": "0.1.0"
}
```

## Observação

Esse endpoint não deve validar PostgreSQL, Redis, Evolution API ou n8n obrigatoriamente na V1.

Verificações mais profundas podem ser adicionadas futuramente em endpoint separado.

---

# 2. Instâncias

Os endpoints de instâncias permitem criar, conectar, consultar, desconectar e remover instâncias WhatsApp.

Todas as rotas desta seção exigem:

```http
X-API-Key: chave_do_cliente
```

---

## 2.1 Criar instância

## Endpoint

```http
POST /v1/instances
```

## Objetivo

Criar uma nova instância no backend e no provider interno, inicialmente a Evolution API.

## Autenticação

Exige API Key.

## Request body

```json
{
  "display_name": "Atendimento Principal",
  "n8n_webhook_url": "https://n8n.exemplo.com/webhook/whatsapp-atendimento",
  "webhook_enabled": true
}
```

## Campos

```txt
display_name     = nome amigável da instância
n8n_webhook_url  = URL do webhook do n8n para eventos dessa instância
webhook_enabled  = indica se eventos devem ser encaminhados ao n8n
```

## Regras

- `display_name` é obrigatório.
- `n8n_webhook_url` pode ser nulo.
- `webhook_enabled` deve ter valor padrão `true`.
- O backend deve gerar o `provider_instance_name`.
- O cliente não deve definir diretamente o nome interno da instância no provider.
- A instância deve ser associada ao cliente autenticado.

## Resposta de sucesso

Status:

```http
201 Created
```

Body:

```json
{
  "id": "1e1d7d4a-7b8e-4ef6-a6e7-dc7d4cfd9f91",
  "display_name": "Atendimento Principal",
  "provider": "evolution",
  "provider_instance_name": "inst_abc123",
  "status": "created",
  "phone_number": null,
  "webhook_enabled": true,
  "n8n_webhook_url": "https://n8n.exemplo.com/webhook/whatsapp-atendimento",
  "created_at": "2026-05-26T12:00:00Z",
  "updated_at": "2026-05-26T12:00:00Z"
}
```

## Erros possíveis

```txt
UNAUTHORIZED
CLIENT_INACTIVE
VALIDATION_ERROR
PROVIDER_ERROR
INTERNAL_ERROR
```

---

## 2.2 Conectar instância

## Endpoint

```http
POST /v1/instances/{instance_id}/connect
```

## Objetivo

Iniciar o processo de conexão da instância ao WhatsApp.

Dependendo da resposta do provider, o backend pode retornar QR Code, código, status ou dados necessários para conexão.

## Autenticação

Exige API Key.

## Path params

```txt
instance_id UUID
```

## Request body

Na V1, pode ser vazio:

```json
{}
```

## Resposta de sucesso

Status:

```http
200 OK
```

Body recomendado:

```json
{
  "instance_id": "1e1d7d4a-7b8e-4ef6-a6e7-dc7d4cfd9f91",
  "status": "connecting",
  "qr_code": "base64-ou-string-retornada-pelo-provider",
  "pairing_code": null,
  "provider_response": {}
}
```

## Observações

- `qr_code` pode ser nulo se o provider retornar outro formato.
- `pairing_code` pode ser nulo.
- `provider_response` pode armazenar dados úteis do provider, mas não deve expor segredos.
- A estrutura exata poderá ser ajustada conforme a versão da Evolution API usada na V1.

## Erros possíveis

```txt
UNAUTHORIZED
CLIENT_INACTIVE
INSTANCE_NOT_FOUND
PROVIDER_ERROR
INTERNAL_ERROR
```

---

## 2.3 Consultar status da instância

## Endpoint

```http
GET /v1/instances/{instance_id}/status
```

## Objetivo

Consultar o status interno da instância e, quando aplicável, sincronizar ou consultar o status no provider.

## Autenticação

Exige API Key.

## Path params

```txt
instance_id UUID
```

## Resposta de sucesso

Status:

```http
200 OK
```

Body:

```json
{
  "instance_id": "1e1d7d4a-7b8e-4ef6-a6e7-dc7d4cfd9f91",
  "status": "connected",
  "provider": "evolution",
  "provider_status": "open",
  "phone_number": "5586999999999",
  "connected_at": "2026-05-26T12:05:00Z",
  "disconnected_at": null
}
```

## Status internos possíveis

```txt
created
connecting
connected
disconnected
error
removed
```

## Erros possíveis

```txt
UNAUTHORIZED
CLIENT_INACTIVE
INSTANCE_NOT_FOUND
PROVIDER_ERROR
INTERNAL_ERROR
```

---

## 2.4 Desconectar instância

## Endpoint

```http
POST /v1/instances/{instance_id}/disconnect
```

## Objetivo

Desconectar ou realizar logout da instância no provider.

## Autenticação

Exige API Key.

## Path params

```txt
instance_id UUID
```

## Request body

Na V1, pode ser vazio:

```json
{}
```

## Resposta de sucesso

Status:

```http
200 OK
```

Body:

```json
{
  "instance_id": "1e1d7d4a-7b8e-4ef6-a6e7-dc7d4cfd9f91",
  "status": "disconnected",
  "disconnected_at": "2026-05-26T12:30:00Z"
}
```

## Erros possíveis

```txt
UNAUTHORIZED
CLIENT_INACTIVE
INSTANCE_NOT_FOUND
PROVIDER_ERROR
INTERNAL_ERROR
```

---

## 2.5 Remover instância

## Endpoint

```http
DELETE /v1/instances/{instance_id}
```

## Objetivo

Remover a instância no provider, se suportado, e marcar a instância internamente como removida.

## Autenticação

Exige API Key.

## Path params

```txt
instance_id UUID
```

## Resposta de sucesso

Status recomendado:

```http
200 OK
```

Body:

```json
{
  "instance_id": "1e1d7d4a-7b8e-4ef6-a6e7-dc7d4cfd9f91",
  "status": "removed"
}
```

## Observação

Na V1, a remoção pode ser implementada como soft delete usando status:

```txt
removed
```

## Erros possíveis

```txt
UNAUTHORIZED
CLIENT_INACTIVE
INSTANCE_NOT_FOUND
PROVIDER_ERROR
INTERNAL_ERROR
```

---

# 3. Mensagens

Os endpoints de mensagens permitem enviar texto e mídias.

Todas as rotas desta seção exigem:

```http
X-API-Key: chave_do_cliente
```

Na V1, os tipos suportados serão:

```txt
text
image
audio
document
video
```

---

## 3.1 Enviar texto

## Endpoint

```http
POST /v1/messages/text
```

## Objetivo

Enviar uma mensagem de texto usando uma instância conectada.

## Autenticação

Exige API Key.

## Request body

```json
{
  "instance_id": "1e1d7d4a-7b8e-4ef6-a6e7-dc7d4cfd9f91",
  "to": "5586999999999",
  "message": "Olá, tudo bem?"
}
```

## Campos

```txt
instance_id = UUID da instância
to          = número de destino
message     = conteúdo textual
```

## Regras

- `instance_id` é obrigatório.
- `to` é obrigatório.
- `message` é obrigatório.
- O backend deve validar se a instância pertence ao cliente autenticado.
- O backend deve validar se a instância está conectada.
- O número deve ser normalizado antes de chamar o provider.
- A tentativa de envio deve ser registrada.

## Resposta de sucesso

Status:

```http
200 OK
```

Body:

```json
{
  "message_id": "6a2ccff0-fd57-4cb2-8966-3cdeadc8c93b",
  "instance_id": "1e1d7d4a-7b8e-4ef6-a6e7-dc7d4cfd9f91",
  "direction": "outbound",
  "message_type": "text",
  "to": "5586999999999",
  "status": "sent",
  "provider_message_id": "BAE5XXXXXXXX",
  "created_at": "2026-05-26T12:40:00Z"
}
```

## Erros possíveis

```txt
UNAUTHORIZED
CLIENT_INACTIVE
VALIDATION_ERROR
INSTANCE_NOT_FOUND
INSTANCE_DISCONNECTED
MESSAGE_SEND_FAILED
PROVIDER_ERROR
INTERNAL_ERROR
```

---

## 3.2 Enviar imagem

## Endpoint

```http
POST /v1/messages/image
```

## Objetivo

Enviar uma imagem por meio da instância informada.

## Autenticação

Exige API Key.

## Request body

```json
{
  "instance_id": "1e1d7d4a-7b8e-4ef6-a6e7-dc7d4cfd9f91",
  "to": "5586999999999",
  "media_url": "https://exemplo.com/imagem.jpg",
  "caption": "Imagem em anexo"
}
```

## Regras

- `instance_id` é obrigatório.
- `to` é obrigatório.
- `media_url` é obrigatório.
- `caption` é opcional.
- A instância deve pertencer ao cliente autenticado.
- A instância deve estar conectada.
- A tentativa de envio deve ser registrada.

## Resposta de sucesso

Status:

```http
200 OK
```

Body:

```json
{
  "message_id": "c1cc4f89-faca-45cd-8911-c27aa56978c0",
  "instance_id": "1e1d7d4a-7b8e-4ef6-a6e7-dc7d4cfd9f91",
  "direction": "outbound",
  "message_type": "image",
  "to": "5586999999999",
  "media_url": "https://exemplo.com/imagem.jpg",
  "caption": "Imagem em anexo",
  "status": "sent",
  "provider_message_id": "BAE5XXXXXXXX",
  "created_at": "2026-05-26T12:42:00Z"
}
```

---

## 3.3 Enviar áudio

## Endpoint

```http
POST /v1/messages/audio
```

## Request body

```json
{
  "instance_id": "1e1d7d4a-7b8e-4ef6-a6e7-dc7d4cfd9f91",
  "to": "5586999999999",
  "media_url": "https://exemplo.com/audio.mp3"
}
```

## Resposta de sucesso

```json
{
  "message_id": "9ec665d9-955e-4170-92c0-331459202170",
  "instance_id": "1e1d7d4a-7b8e-4ef6-a6e7-dc7d4cfd9f91",
  "direction": "outbound",
  "message_type": "audio",
  "to": "5586999999999",
  "media_url": "https://exemplo.com/audio.mp3",
  "status": "sent",
  "provider_message_id": "BAE5XXXXXXXX",
  "created_at": "2026-05-26T12:44:00Z"
}
```

---

## 3.4 Enviar documento

## Endpoint

```http
POST /v1/messages/document
```

## Request body

```json
{
  "instance_id": "1e1d7d4a-7b8e-4ef6-a6e7-dc7d4cfd9f91",
  "to": "5586999999999",
  "media_url": "https://exemplo.com/documento.pdf",
  "filename": "documento.pdf",
  "caption": "Documento em anexo"
}
```

## Campos específicos

```txt
filename = nome do arquivo enviado
caption  = legenda opcional
```

## Resposta de sucesso

```json
{
  "message_id": "d83fcb1d-6707-41db-a601-272b2802e9c2",
  "instance_id": "1e1d7d4a-7b8e-4ef6-a6e7-dc7d4cfd9f91",
  "direction": "outbound",
  "message_type": "document",
  "to": "5586999999999",
  "media_url": "https://exemplo.com/documento.pdf",
  "filename": "documento.pdf",
  "caption": "Documento em anexo",
  "status": "sent",
  "provider_message_id": "BAE5XXXXXXXX",
  "created_at": "2026-05-26T12:46:00Z"
}
```

---

## 3.5 Enviar vídeo

## Endpoint

```http
POST /v1/messages/video
```

## Request body

```json
{
  "instance_id": "1e1d7d4a-7b8e-4ef6-a6e7-dc7d4cfd9f91",
  "to": "5586999999999",
  "media_url": "https://exemplo.com/video.mp4",
  "caption": "Vídeo em anexo"
}
```

## Resposta de sucesso

```json
{
  "message_id": "fcb740b2-15c5-4e9e-82f1-2e403c30f848",
  "instance_id": "1e1d7d4a-7b8e-4ef6-a6e7-dc7d4cfd9f91",
  "direction": "outbound",
  "message_type": "video",
  "to": "5586999999999",
  "media_url": "https://exemplo.com/video.mp4",
  "caption": "Vídeo em anexo",
  "status": "sent",
  "provider_message_id": "BAE5XXXXXXXX",
  "created_at": "2026-05-26T12:48:00Z"
}
```

---

## Erros comuns dos endpoints de mensagem

Formato:

```json
{
  "code": "INSTANCE_DISCONNECTED",
  "message": "A instância não está conectada.",
  "details": {
    "instance_id": "1e1d7d4a-7b8e-4ef6-a6e7-dc7d4cfd9f91"
  }
}
```

Códigos possíveis:

```txt
UNAUTHORIZED
CLIENT_INACTIVE
VALIDATION_ERROR
INSTANCE_NOT_FOUND
INSTANCE_DISCONNECTED
MESSAGE_SEND_FAILED
PROVIDER_ERROR
INTERNAL_ERROR
```

---

# 4. Webhooks

A V1 terá endpoint para receber eventos vindos da Evolution API.

---

## 4.1 Receber webhook da Evolution API

## Endpoint

```http
POST /v1/webhooks/evolution
```

## Objetivo

Receber eventos enviados pela Evolution API, salvar o payload bruto, identificar a instância, normalizar o evento e encaminhar para o n8n quando aplicável.

## Autenticação

Não usa API Key do cliente.

Usa segredo compartilhado:

```http
X-Webhook-Secret: segredo_interno
```

## Request body

O payload pode variar conforme o evento da Evolution API.

Exemplo genérico:

```json
{
  "event": "messages.upsert",
  "instance": "inst_abc123",
  "data": {
    "key": {
      "remoteJid": "5586999999999@s.whatsapp.net",
      "fromMe": false,
      "id": "BAE5XXXXXXXX"
    },
    "message": {
      "conversation": "Olá"
    },
    "messageTimestamp": 1779796800
  }
}
```

## Processamento esperado

Ao receber um webhook, o backend deve:

1. validar o segredo do webhook;
2. salvar o payload bruto;
3. identificar o provider;
4. identificar a instância;
5. identificar o cliente, quando possível;
6. classificar o tipo de evento;
7. normalizar o payload;
8. registrar mensagem recebida, se aplicável;
9. encaminhar evento normalizado para o n8n, se configurado;
10. registrar sucesso ou falha.

## Resposta de sucesso

Status:

```http
200 OK
```

Body:

```json
{
  "received": true,
  "event_id": "e6aee962-294c-4f38-b377-33ef2ad667fa",
  "event_type": "message.received",
  "processing_status": "processed",
  "forwarded_to_n8n": true
}
```

## Resposta para evento aceito mas não processado completamente

Status:

```http
202 Accepted
```

Body:

```json
{
  "received": true,
  "event_id": "e6aee962-294c-4f38-b377-33ef2ad667fa",
  "event_type": "unknown",
  "processing_status": "received",
  "forwarded_to_n8n": false
}
```

## Erros possíveis

```txt
WEBHOOK_UNAUTHORIZED
WEBHOOK_PROCESSING_ERROR
INTERNAL_ERROR
```

---

# 5. Logs

Os endpoints de logs permitem consultas básicas para depuração da V1.

Todas as rotas desta seção exigem:

```http
X-API-Key: chave_do_cliente
```

---

## 5.1 Listar mensagens

## Endpoint

```http
GET /v1/logs/messages
```

## Objetivo

Listar mensagens enviadas e recebidas associadas ao cliente autenticado.

## Query params opcionais

```txt
instance_id
direction
message_type
status
limit
offset
```

## Exemplo

```http
GET /v1/logs/messages?instance_id=1e1d7d4a-7b8e-4ef6-a6e7-dc7d4cfd9f91&direction=outbound&limit=20&offset=0
```

## Resposta de sucesso

```json
{
  "items": [
    {
      "id": "6a2ccff0-fd57-4cb2-8966-3cdeadc8c93b",
      "instance_id": "1e1d7d4a-7b8e-4ef6-a6e7-dc7d4cfd9f91",
      "direction": "outbound",
      "message_type": "text",
      "remote_jid": "5586999999999",
      "content": "Olá, tudo bem?",
      "status": "sent",
      "created_at": "2026-05-26T12:40:00Z"
    }
  ],
  "limit": 20,
  "offset": 0
}
```

---

## 5.2 Listar eventos de webhook

## Endpoint

```http
GET /v1/logs/webhooks
```

## Objetivo

Listar eventos de webhook recebidos para o cliente autenticado.

## Query params opcionais

```txt
instance_id
event_type
processing_status
forwarded_to_n8n
limit
offset
```

## Resposta de sucesso

```json
{
  "items": [
    {
      "id": "e6aee962-294c-4f38-b377-33ef2ad667fa",
      "instance_id": "1e1d7d4a-7b8e-4ef6-a6e7-dc7d4cfd9f91",
      "event_type": "message.received",
      "processing_status": "processed",
      "forwarded_to_n8n": true,
      "received_at": "2026-05-26T12:50:00Z"
    }
  ],
  "limit": 20,
  "offset": 0
}
```

---

## 5.3 Listar erros

## Endpoint

```http
GET /v1/logs/errors
```

## Objetivo

Listar erros registrados para o cliente autenticado.

## Query params opcionais

```txt
instance_id
source
error_code
limit
offset
```

## Resposta de sucesso

```json
{
  "items": [
    {
      "id": "c169fc49-e05f-4a08-a872-858890548e8a",
      "instance_id": "1e1d7d4a-7b8e-4ef6-a6e7-dc7d4cfd9f91",
      "source": "n8n",
      "error_code": "N8N_FORWARDING_ERROR",
      "error_message": "Falha ao encaminhar evento para o n8n.",
      "created_at": "2026-05-26T12:52:00Z"
    }
  ],
  "limit": 20,
  "offset": 0
}
```

---

# 6. Clientes

Na V1, não haverá painel administrativo nem sistema completo de gestão de clientes.

Mesmo assim, será necessário criar pelo menos um cliente inicial para uso da API.

## Estratégia recomendada

Criar cliente inicial via script administrativo.

Exemplo:

```bash
python scripts/create_client.py --name "Cliente Teste"
```

Saída esperada:

```txt
Client created successfully.
API Key: zapi_xxxxxxxxxxxxxxxxx
Save this key now. It will not be shown again.
```

## Observação

Endpoints públicos para CRUD de clientes não fazem parte da V1.

A gestão completa de clientes poderá ser adicionada futuramente.

---

# 7. Padrões de resposta

## Resposta de recurso único

```json
{
  "id": "uuid",
  "field": "value"
}
```

## Resposta de lista

```json
{
  "items": [],
  "limit": 20,
  "offset": 0
}
```

## Resposta de erro

```json
{
  "code": "ERROR_CODE",
  "message": "Mensagem legível.",
  "details": {}
}
```

---

# 8. Paginação

Endpoints de listagem devem usar paginação simples com:

```txt
limit
offset
```

## Valores recomendados

```txt
limit padrão: 20
limit máximo: 100
offset padrão: 0
```

Exemplo:

```http
GET /v1/logs/messages?limit=20&offset=0
```

---

# 9. Normalização de número

Endpoints de envio devem aceitar números em formato simples, mas o backend deve normalizar antes de chamar o provider.

Exemplo de entrada:

```txt
86999999999
```

Exemplo normalizado:

```txt
5586999999999
```

## Regra inicial recomendada

Na V1, assumir Brasil como padrão quando o número não vier com DDI.

Exemplo:

```txt
86999999999 → 5586999999999
```

Se o número já vier com DDI:

```txt
5586999999999 → 5586999999999
```

Essa regra pode ser refinada futuramente.

---

# 10. Campos que não devem ser expostos

A API não deve retornar:

```txt
api_key_hash
EVOLUTION_API_KEY
WEBHOOK_SECRET
tokens internos
senhas
DATABASE_URL
REDIS_URL
payloads sensíveis completos sem necessidade
```

Payloads brutos podem aparecer em endpoints de logs futuramente, mas na V1 recomenda-se evitar exposição completa por padrão.

---

# 11. Contratos previstos por spec

## 001 — Base do backend e infraestrutura local

```http
GET /health
```

---

## 002 — Provider Evolution API

Não expõe endpoint público próprio.

Cria camada interna usada pelas demais specs.

---

## 003 — Persistência e modelagem inicial

Pode apoiar endpoints de logs e scripts administrativos.

Não exige endpoint público obrigatório além dos logs definidos.

---

## 004 — Gestão de instâncias WhatsApp

```http
POST   /v1/instances
POST   /v1/instances/{instance_id}/connect
GET    /v1/instances/{instance_id}/status
POST   /v1/instances/{instance_id}/disconnect
DELETE /v1/instances/{instance_id}
```

---

## 005 — Envio de mensagens

```http
POST /v1/messages/text
POST /v1/messages/image
POST /v1/messages/audio
POST /v1/messages/document
POST /v1/messages/video
```

---

## 006 — Recebimento de webhooks

```http
POST /v1/webhooks/evolution
```

---

## 007 — Encaminhamento para n8n

Não exige endpoint público próprio na V1.

O encaminhamento ocorre internamente após recebimento de webhook.

---

## 008 — Segurança com API Key

Afeta todas as rotas protegidas.

---

## Critérios de conformidade da API

A API estará alinhada com este documento se:

- usar `/v1` nos endpoints públicos;
- proteger instâncias, mensagens e logs com API Key;
- proteger webhook da Evolution API com segredo próprio;
- não expor Evolution API diretamente;
- retornar erros padronizados;
- validar payloads com Pydantic;
- registrar tentativas de envio;
- registrar webhooks recebidos;
- consultar logs apenas do cliente autenticado;
- não expor segredos ou hashes.

---

## Resumo

A API da V1 será enxuta e focada nos fluxos essenciais:

```txt
health check
gestão de instâncias
envio de mensagens
recebimento de webhooks
consulta básica de logs
```

A API não incluirá CRUD público de clientes, painel administrativo, cobrança, chatbot, campanhas ou gestão comercial.

Os contratos definidos neste documento servirão como base para as specs, plans e tasks do Spec Kit.