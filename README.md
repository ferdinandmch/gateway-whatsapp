# WhatsApp Gateway

API própria de mensageria para WhatsApp, construída com FastAPI e Evolution API como provider.

O projeto cria uma camada de controle entre clientes externos e a Evolution API, permitindo envio de mensagens, recebimento de webhooks, persistência de eventos e encaminhamento para automações no n8n.

---

## Arquitetura

```
Envio de mensagens:

Cliente externo
      ↓  (X-Api-Key)
Backend FastAPI
      ↓
EvolutionProvider
      ↓
Evolution API
      ↓
WhatsApp

Recebimento de eventos:

WhatsApp
      ↓
Evolution API
      ↓  (X-Webhook-Secret)
Backend FastAPI  →  PostgreSQL (persiste evento)
      ↓
n8n  →  resposta automática / automações
```

---

## Stack

| Camada | Tecnologia |
|--------|-----------|
| Backend | Python 3.12 + FastAPI |
| ORM | SQLAlchemy (puro) |
| Schemas | Pydantic |
| Migrations | Alembic |
| Banco | PostgreSQL 16 |
| Cache | Redis 7 |
| HTTP Client | HTTPX |
| Provider WhatsApp | Evolution API v2.3.4 |
| Automações | n8n |
| Infra local | Docker Compose |
| Testes | pytest + pytest-asyncio |
| Gerenciador Python | uv |

---

## Pré-requisitos

- [Docker](https://docs.docker.com/get-docker/) e Docker Compose
- [Git](https://git-scm.com/)

---

## Instalação

### 1. Clonar o repositório

```bash
git clone <url-do-repositorio>
cd z_api_2
```

### 2. Configurar variáveis de ambiente

```bash
cp .env.example .env
```

Edite o `.env` e preencha os valores:

```env
# Chave usada pela Evolution API internamente
EVOLUTION_API_KEY=sua-chave-aqui

# Segredo compartilhado para validar webhooks da Evolution API
WEBHOOK_SECRET=seu-segredo-aqui

# Salt para hash das API Keys dos clientes
API_KEY_SALT=seu-salt-aqui

# Token para criar clientes via script
ADMIN_TOKEN=seu-token-admin-aqui
```

> As demais variáveis podem ser mantidas com os valores padrão para ambiente local.

### 3. Subir os serviços

```bash
docker compose up -d
```

Serviços iniciados:
- **backend** — `http://localhost:8000`
- **postgres** — porta `5433`
- **redis** — porta `6379`
- **evolution-api** — `http://localhost:8080`
- **n8n** — `http://localhost:5678`

### 4. Criar o banco da Evolution API

Na primeira execução, crie o banco separado para a Evolution API:

```bash
docker compose exec postgres psql -U postgres -c "CREATE DATABASE evolution_api;"
```

### 5. Rodar as migrations

```bash
docker compose exec backend alembic upgrade head
```

### 6. Criar o primeiro cliente e obter a API Key

```bash
docker compose exec backend python scripts/create_client.py --name "Meu Cliente"
```

Guarde a API Key exibida — ela não será mostrada novamente.

```
Client created successfully.
ID:      xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
Name:    Meu Cliente
API Key: zapi_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### 7. Criar uma instância WhatsApp

```bash
curl -X POST http://localhost:8000/v1/instances \
  -H "Content-Type: application/json" \
  -H "X-Api-Key: SUA_API_KEY" \
  -d '{
    "display_name": "WhatsApp Principal",
    "n8n_webhook_url": "http://n8n:5678/webhook/whatsapp-gateway"
  }'
```

Anote o `instance_id` retornado.

### 8. Conectar ao WhatsApp

```bash
curl -X POST http://localhost:8000/v1/instances/SEU_INSTANCE_ID/connect \
  -H "X-Api-Key: SUA_API_KEY"
```

Acesse `http://localhost:8080/manager`, encontre sua instância e escaneie o QR Code com o WhatsApp.

### 9. Verificar status

```bash
curl http://localhost:8000/v1/instances/SEU_INSTANCE_ID/status \
  -H "X-Api-Key: SUA_API_KEY"
```

Resposta esperada quando conectado:

```json
{"state": "connected"}
```

---

## Configuração do n8n

Acesse `http://localhost:5678` e crie um novo workflow seguindo os passos:

### 1. Nó Webhook (trigger)

- **Tipo:** Webhook
- **HTTP Method:** POST
- **Path:** `whatsapp-gateway`
- Ativar o toggle **Active** (não apenas Test)

URL gerada: `http://localhost:5678/webhook/whatsapp-gateway`

### 2. Nó Switch (roteamento por tipo de evento)

- **Field:** `{{ $json.body.event_type }}`
- **Output 1 — message.received:** valor igual a `message.received`
- **Output 2 — connection.update:** valor igual a `connection.update`
- **Output 3 — Fallback:** qualquer outro evento

### 3. Nó HTTP Request (enviar resposta automática)

Conecte na saída `message.received` do Switch:

- **Method:** POST
- **URL:** `http://backend:8000/v1/messages/text`
- **Headers:**
  - `Content-Type`: `application/json`
  - `X-Api-Key`: sua API Key
- **Body (JSON):**

```json
{
  "instance_id": "{{ $json.body.instance_id }}",
  "to": "{{ $json.body.from }}",
  "message": "Olá! Recebi sua mensagem. Em que posso ajudar?"
}
```

### 4. Nó Respond to Webhook

Adicione um nó "Respond to Webhook" em cada saída do Switch com **Respond:** `When Last Node Finishes`.

### 5. Ativar o workflow

Clique em **Save** e ative o toggle no canto superior direito.

---

## Endpoints da API

Todos os endpoints (exceto `/health`) exigem o header `X-Api-Key`.

### Health

```
GET /health
```

### Instâncias

```
POST   /v1/instances                          → Criar instância
POST   /v1/instances/{id}/connect             → Obter QR Code
GET    /v1/instances/{id}/status              → Status da conexão
POST   /v1/instances/{id}/disconnect          → Desconectar
DELETE /v1/instances/{id}                     → Remover instância
```

### Mensagens

```
POST /v1/messages/text                        → Enviar texto
POST /v1/messages/image                       → Enviar imagem
POST /v1/messages/audio                       → Enviar áudio
POST /v1/messages/document                    → Enviar documento
POST /v1/messages/video                       → Enviar vídeo
```

### Logs

```
GET /v1/logs/messages                         → Listar mensagens
GET /v1/logs/webhook-events                   → Listar eventos de webhook
GET /v1/logs/errors                           → Listar erros
```

### Webhook (Evolution API → Backend)

```
POST /v1/webhooks/evolution/{instance_name}   → Receber eventos
```

Requer header `X-Webhook-Secret`.

A documentação interativa completa está disponível em `http://localhost:8000/docs`.

---

## Payload encaminhado ao n8n

Quando uma mensagem é recebida, o backend encaminha ao n8n:

```json
{
  "event_type": "message.received",
  "provider": "evolution",
  "client_id": "uuid-do-cliente",
  "instance_id": "uuid-da-instancia",
  "provider_instance_name": "inst_abc12345",
  "from": "5511999990000",
  "remote_jid": "5511999990000@s.whatsapp.net",
  "message_type": "text",
  "content": "Texto da mensagem",
  "media_url": null,
  "provider_message_id": "ID_DA_MENSAGEM",
  "connection_state": null,
  "timestamp": "2024-01-01T12:00:00+00:00"
}
```

No n8n, todos os campos ficam acessíveis via `{{ $json.body.<campo> }}`.

---

## Estrutura do projeto

```
app/
├── api/v1/routes/          → instances, messages, webhooks, logs
├── services/               → instance_service, message_service, webhook_service
├── providers/
│   ├── base.py             → interface MessagingProvider
│   └── evolution/          → EvolutionProvider, normalizer
├── models/                 → Client, Instance, Message, WebhookEvent, ErrorLog
├── schemas/                → Pydantic (request/response)
├── webhooks/               → classifier, normalizer, forwarder
└── core/                   → config, security, database, redis, logging
alembic/                    → migrations
scripts/                    → create_client.py
tests/
├── unit/                   → testes unitários por módulo
└── integration/            → testes end-to-end com banco real
```

---

## Testes

```bash
# Rodar todos os testes
docker compose exec backend pytest

# Com cobertura
docker compose exec backend pytest --cov=app

# Apenas unitários
docker compose exec backend pytest tests/unit/

# Apenas integração
docker compose exec backend pytest tests/integration/
```

---

## Variáveis de ambiente

| Variável | Descrição | Exemplo |
|----------|-----------|---------|
| `APP_ENV` | Ambiente de execução | `development` |
| `DATABASE_URL` | Conexão PostgreSQL | `postgresql+asyncpg://...` |
| `REDIS_URL` | Conexão Redis | `redis://redis:6379/0` |
| `EVOLUTION_API_URL` | URL da Evolution API | `http://evolution-api:8080` |
| `EVOLUTION_API_KEY` | Chave global da Evolution API | `sua-chave` |
| `WEBHOOK_SECRET` | Segredo para validar webhooks | `seu-segredo` |
| `API_KEY_SALT` | Salt para hash das API Keys | `seu-salt` |
| `ADMIN_TOKEN` | Token para criar clientes | `seu-token` |
| `WEBHOOK_BASE_URL` | URL base do backend (usada pela Evolution API) | `http://host.docker.internal:8000` |
| `N8N_DEFAULT_WEBHOOK_URL` | URL padrão do webhook n8n | `http://n8n:5678/webhook/...` |
| `N8N_FORWARD_TIMEOUT` | Timeout (s) para chamadas ao n8n | `5` |

---

## Retomando o desenvolvimento

### n8n incluído no compose (padrão)

```bash
docker compose up -d
```

Tudo sobe junto, incluindo o n8n na porta `5678`.

### n8n em container separado (caso você já tenha um n8n rodando em outro projeto)

Se você usa o n8n em um compose separado, siga estes passos toda vez que for retomar o desenvolvimento:

```bash
# 1. Subir o projeto
docker compose up -d

# 2. Subir o n8n (na pasta do seu compose separado)
cd <pasta-do-seu-n8n>
docker compose up -d

# 3. Conectar o n8n à rede deste projeto
docker network connect --alias n8n z_api_2_default <nome-do-container-n8n>
```

Para descobrir o nome do seu container n8n:

```bash
docker ps --filter "ancestor=docker.n8n.io/n8nio/n8n" --format "{{.Names}}"
```

Sem o passo 3, o backend não consegue resolver o endereço `n8n:5678` e o encaminhamento de eventos falha.

---

## Roadmap V2

- **Intervalo de auto-reply** — Cooldown configurável por contato para não reenviar saudação automaticamente em janelas curtas
- **Dashboard / Frontend web** — Interface visual para gerenciar clientes, instâncias, mensagens e automações
