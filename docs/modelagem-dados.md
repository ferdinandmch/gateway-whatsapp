# 06 — Modelagem de Dados

## Objetivo do documento

Este documento define a modelagem inicial de dados da V1 do projeto **Z-API Própria / Gateway WhatsApp**.

A modelagem tem como objetivo sustentar os principais fluxos da primeira versão:

- cadastro e autenticação de clientes por API Key;
- criação e gestão de instâncias WhatsApp;
- envio de mensagens;
- recebimento de mensagens via webhook;
- armazenamento de eventos brutos e normalizados;
- encaminhamento de eventos para n8n;
- registro de erros e falhas de integração.

A modelagem foi pensada para uso com:

```txt
PostgreSQL
SQLAlchemy puro
Alembic
Pydantic
```

---

## Visão geral das entidades

A V1 terá as seguintes tabelas principais:

```txt
clients
instances
messages
webhook_events
error_logs
```

Relação geral:

```txt
clients
   ↓
instances
   ↓
messages

clients
   ↓
webhook_events

clients
   ↓
error_logs
```

Uma visão simplificada:

```txt
Client 1 ── N Instance
Client 1 ── N Message
Client 1 ── N WebhookEvent
Client 1 ── N ErrorLog

Instance 1 ── N Message
Instance 1 ── N WebhookEvent
Instance 1 ── N ErrorLog
```

---

## Estratégia geral de modelagem

A V1 deve priorizar uma modelagem simples, mas extensível.

Princípios adotados:

- cada cliente pode possuir várias instâncias;
- cada instância pertence a um cliente;
- mensagens enviadas e recebidas devem ser registradas;
- eventos recebidos por webhook devem preservar o payload bruto;
- erros relevantes devem ser persistidos;
- dados sensíveis não devem ser armazenados em texto puro;
- campos JSONB podem ser usados para payloads brutos e detalhes variáveis;
- a modelagem deve permitir evolução futura para múltiplos providers.

---

## Tipos de dados recomendados

## Identificadores

Recomendação:

```txt
UUID
```

Motivo:

- evita IDs sequenciais previsíveis;
- facilita distribuição futura;
- é adequado para APIs públicas;
- reduz exposição de volume interno do banco.

Campos principais:

```txt
id UUID PRIMARY KEY
```

---

## Datas

Usar timestamps com timezone:

```txt
TIMESTAMP WITH TIME ZONE
```

Campos padrão:

```txt
created_at
updated_at
```

Quando aplicável:

```txt
deleted_at
connected_at
disconnected_at
forwarded_at
```

---

## Payloads brutos

Usar:

```txt
JSONB
```

Campos típicos:

```txt
raw_payload
normalized_payload
provider_response
details
```

Motivo:

- webhooks e respostas externas podem variar;
- facilita depuração;
- preserva dados originais recebidos da Evolution API;
- permite consultas futuras em campos específicos se necessário.

---

## Enums

Na V1, os valores de status e tipos podem ser implementados como strings controladas pela aplicação.

Exemplo:

```txt
status VARCHAR
message_type VARCHAR
direction VARCHAR
provider VARCHAR
```

Motivo:

- simplifica migrations iniciais;
- evita rigidez excessiva;
- facilita ajustes durante a validação da V1.

Em versões futuras, pode-se avaliar uso de enums nativos do PostgreSQL.

---

# 1. Tabela `clients`

## Objetivo

Representa um cliente, projeto ou consumidor autorizado a utilizar a API.

Na V1, o cliente é usado principalmente para:

- autenticação por API Key;
- associação de instâncias;
- isolamento de dados;
- controle de status ativo/inativo.

---

## Campos

```txt
id UUID PRIMARY KEY
name VARCHAR NOT NULL
api_key_hash VARCHAR NOT NULL
status VARCHAR NOT NULL
created_at TIMESTAMP WITH TIME ZONE NOT NULL
updated_at TIMESTAMP WITH TIME ZONE NOT NULL
```

---

## Campos detalhados

## `id`

Identificador interno do cliente.

Tipo:

```txt
UUID
```

Regra:

- gerado pelo backend;
- não deve ser sequencial;
- usado como chave primária.

---

## `name`

Nome do cliente ou projeto consumidor da API.

Tipo:

```txt
VARCHAR
```

Exemplos:

```txt
Cliente Teste
Restaurante X
Projeto Interno
```

---

## `api_key_hash`

Hash da API Key do cliente.

Tipo:

```txt
VARCHAR
```

Regra:

- nunca armazenar API Key em texto puro;
- armazenar apenas hash;
- a chave original só deve ser exibida no momento da criação.

---

## `status`

Status do cliente.

Tipo:

```txt
VARCHAR
```

Valores iniciais:

```txt
active
inactive
```

Regras:

- somente clientes `active` podem consumir rotas protegidas;
- clientes `inactive` devem ser bloqueados.

---

## `created_at`

Data de criação do registro.

---

## `updated_at`

Data da última atualização do registro.

---

## Índices recomendados

```txt
idx_clients_status
```

Para buscar clientes ativos/inativos.

Como API Key será armazenada com hash, pode ser necessário índice em:

```txt
api_key_hash
```

Recomendação:

```txt
UNIQUE(api_key_hash)
```

---

## Relacionamentos

```txt
clients 1 ── N instances
clients 1 ── N messages
clients 1 ── N webhook_events
clients 1 ── N error_logs
```

---

# 2. Tabela `instances`

## Objetivo

Representa uma instância de WhatsApp gerenciada pelo backend e vinculada a um cliente.

Na V1, a instância será criada no backend e também no provider inicial, a Evolution API.

---

## Campos

```txt
id UUID PRIMARY KEY
client_id UUID NOT NULL
provider VARCHAR NOT NULL
provider_instance_name VARCHAR NOT NULL
display_name VARCHAR NULL
phone_number VARCHAR NULL
status VARCHAR NOT NULL
n8n_webhook_url TEXT NULL
webhook_enabled BOOLEAN NOT NULL
created_at TIMESTAMP WITH TIME ZONE NOT NULL
updated_at TIMESTAMP WITH TIME ZONE NOT NULL
connected_at TIMESTAMP WITH TIME ZONE NULL
disconnected_at TIMESTAMP WITH TIME ZONE NULL
```

---

## Campos detalhados

## `id`

Identificador interno da instância no backend.

Tipo:

```txt
UUID
```

---

## `client_id`

Referência ao cliente dono da instância.

Tipo:

```txt
UUID
```

Chave estrangeira:

```txt
clients.id
```

Regra:

- toda instância pertence obrigatoriamente a um cliente.

---

## `provider`

Identifica o provider de mensageria usado pela instância.

Tipo:

```txt
VARCHAR
```

Valor da V1:

```txt
evolution
```

Valores futuros possíveis:

```txt
evolution_go
whatsapp_cloud
custom_baileys
```

---

## `provider_instance_name`

Nome ou identificador da instância no provider.

Tipo:

```txt
VARCHAR
```

Exemplo:

```txt
inst_abc123
cliente_teste_vendas
```

Regra:

- deve ser único por provider;
- não deve depender apenas do nome informado pelo usuário.

Recomendação:

```txt
UNIQUE(provider, provider_instance_name)
```

---

## `display_name`

Nome amigável da instância.

Tipo:

```txt
VARCHAR
```

Exemplo:

```txt
Atendimento Principal
Vendas
Suporte
```

Esse campo pode ser informado pelo usuário/cliente.

---

## `phone_number`

Número associado à instância após conexão.

Tipo:

```txt
VARCHAR
```

Exemplo:

```txt
5586999999999
```

Pode ser nulo antes da conexão.

---

## `status`

Status interno da instância.

Tipo:

```txt
VARCHAR
```

Valores iniciais:

```txt
created
connecting
connected
disconnected
error
removed
```

Descrição:

```txt
created      = instância criada no backend/provider
connecting   = instância aguardando conexão ou QR Code
connected    = instância conectada ao WhatsApp
disconnected = instância desconectada
error        = instância com falha
removed      = instância removida ou marcada como removida
```

---

## `n8n_webhook_url`

URL do webhook do n8n associada à instância.

Tipo:

```txt
TEXT
```

Regra recomendada:

- na V1, o webhook do n8n será preferencialmente configurado por instância;
- pode ser nulo se a instância ainda não encaminhar eventos para n8n.

---

## `webhook_enabled`

Indica se eventos recebidos para essa instância devem ser encaminhados ao n8n.

Tipo:

```txt
BOOLEAN
```

Valor padrão:

```txt
true
```

---

## `created_at`

Data de criação da instância.

---

## `updated_at`

Data da última atualização da instância.

---

## `connected_at`

Data/hora em que a instância foi marcada como conectada.

Pode ser nulo.

---

## `disconnected_at`

Data/hora em que a instância foi marcada como desconectada.

Pode ser nulo.

---

## Índices recomendados

```txt
idx_instances_client_id
idx_instances_status
idx_instances_provider_instance_name
```

Constraints recomendadas:

```txt
FOREIGN KEY (client_id) REFERENCES clients(id)
UNIQUE(provider, provider_instance_name)
```

---

## Relacionamentos

```txt
instances N ── 1 clients
instances 1 ── N messages
instances 1 ── N webhook_events
instances 1 ── N error_logs
```

---

# 3. Tabela `messages`

## Objetivo

Registra mensagens enviadas e recebidas pelo sistema.

Ela deve armazenar tanto mensagens outbound quanto inbound.

---

## Campos

```txt
id UUID PRIMARY KEY
client_id UUID NOT NULL
instance_id UUID NOT NULL
direction VARCHAR NOT NULL
message_type VARCHAR NOT NULL
remote_jid VARCHAR NOT NULL
content TEXT NULL
media_url TEXT NULL
caption TEXT NULL
provider_message_id VARCHAR NULL
status VARCHAR NOT NULL
raw_payload JSONB NULL
provider_response JSONB NULL
created_at TIMESTAMP WITH TIME ZONE NOT NULL
updated_at TIMESTAMP WITH TIME ZONE NOT NULL
sent_at TIMESTAMP WITH TIME ZONE NULL
received_at TIMESTAMP WITH TIME ZONE NULL
```

---

## Campos detalhados

## `id`

Identificador interno da mensagem.

Tipo:

```txt
UUID
```

---

## `client_id`

Cliente associado à mensagem.

Tipo:

```txt
UUID
```

Chave estrangeira:

```txt
clients.id
```

---

## `instance_id`

Instância usada para enviar ou receber a mensagem.

Tipo:

```txt
UUID
```

Chave estrangeira:

```txt
instances.id
```

---

## `direction`

Direção da mensagem.

Tipo:

```txt
VARCHAR
```

Valores:

```txt
inbound
outbound
```

Significado:

```txt
inbound  = mensagem recebida
outbound = mensagem enviada
```

---

## `message_type`

Tipo da mensagem.

Tipo:

```txt
VARCHAR
```

Valores da V1:

```txt
text
image
audio
document
video
```

Valores futuros possíveis:

```txt
location
contact
sticker
button
list
carousel
reaction
unknown
```

---

## `remote_jid`

Identificador remoto do contato/conversa.

Tipo:

```txt
VARCHAR
```

Pode conter:

```txt
5586999999999
5586999999999@s.whatsapp.net
```

A forma exata dependerá do provider e da normalização definida.

---

## `content`

Conteúdo textual da mensagem.

Tipo:

```txt
TEXT
```

Usado principalmente para mensagens de texto.

Pode ser nulo para mídias sem legenda.

---

## `media_url`

URL da mídia enviada ou recebida, quando aplicável.

Tipo:

```txt
TEXT
```

Na V1, o envio de mídia será baseado em URL ou referência compatível com o provider.

---

## `caption`

Legenda associada à mídia, quando aplicável.

Tipo:

```txt
TEXT
```

---

## `provider_message_id`

Identificador da mensagem no provider.

Tipo:

```txt
VARCHAR
```

Exemplo:

```txt
BAE5...
```

Pode ser nulo se o provider não retornar ou se a mensagem falhar antes do envio.

---

## `status`

Status da mensagem.

Tipo:

```txt
VARCHAR
```

Valores iniciais para mensagens enviadas:

```txt
pending
sent
failed
```

Valores possíveis futuros:

```txt
delivered
read
```

Valores para mensagens recebidas:

```txt
received
```

---

## `raw_payload`

Payload bruto relacionado à mensagem.

Tipo:

```txt
JSONB
```

Pode armazenar:

- payload recebido no webhook;
- payload enviado ao provider;
- dados originais relevantes para depuração.

---

## `provider_response`

Resposta do provider ao enviar mensagem.

Tipo:

```txt
JSONB
```

Usado principalmente para mensagens outbound.

---

## `created_at`

Data de criação do registro.

---

## `updated_at`

Data da última atualização do registro.

---

## `sent_at`

Data/hora em que a mensagem foi enviada com sucesso, quando aplicável.

---

## `received_at`

Data/hora em que a mensagem foi recebida, quando aplicável.

---

## Índices recomendados

```txt
idx_messages_client_id
idx_messages_instance_id
idx_messages_direction
idx_messages_message_type
idx_messages_status
idx_messages_created_at
idx_messages_provider_message_id
```

Constraints recomendadas:

```txt
FOREIGN KEY (client_id) REFERENCES clients(id)
FOREIGN KEY (instance_id) REFERENCES instances(id)
```

---

## Regras importantes

- toda tentativa de envio deve gerar registro;
- toda mensagem recebida identificável deve gerar registro;
- mensagens de clientes diferentes não devem ser misturadas;
- mensagens devem sempre estar associadas a uma instância;
- falhas de envio devem atualizar status para `failed`.

---

# 4. Tabela `webhook_events`

## Objetivo

Registra eventos recebidos da Evolution API via webhook.

Essa tabela preserva o histórico dos eventos recebidos, mesmo quando o evento não for reconhecido ou não gerar uma mensagem.

---

## Campos

```txt
id UUID PRIMARY KEY
client_id UUID NULL
instance_id UUID NULL
provider VARCHAR NOT NULL
provider_instance_name VARCHAR NULL
event_type VARCHAR NOT NULL
raw_payload JSONB NOT NULL
normalized_payload JSONB NULL
processing_status VARCHAR NOT NULL
forwarded_to_n8n BOOLEAN NOT NULL
n8n_status_code INTEGER NULL
n8n_response JSONB NULL
received_at TIMESTAMP WITH TIME ZONE NOT NULL
processed_at TIMESTAMP WITH TIME ZONE NULL
forwarded_at TIMESTAMP WITH TIME ZONE NULL
created_at TIMESTAMP WITH TIME ZONE NOT NULL
```

---

## Campos detalhados

## `id`

Identificador interno do evento.

Tipo:

```txt
UUID
```

---

## `client_id`

Cliente associado ao evento.

Tipo:

```txt
UUID
```

Pode ser nulo se o backend não conseguir identificar o cliente a partir do payload recebido.

---

## `instance_id`

Instância associada ao evento.

Tipo:

```txt
UUID
```

Pode ser nulo quando:

- o payload não informa instância;
- a instância ainda não existe no banco;
- houve erro de identificação.

---

## `provider`

Provider que originou o evento.

Tipo:

```txt
VARCHAR
```

Valor da V1:

```txt
evolution
```

---

## `provider_instance_name`

Nome/identificador da instância no provider.

Tipo:

```txt
VARCHAR
```

Usado para ajudar a identificar a instância interna.

---

## `event_type`

Tipo de evento normalizado ou classificado.

Tipo:

```txt
VARCHAR
```

Valores iniciais possíveis:

```txt
message.received
message.sent
message.delivered
message.read
connection.update
send.error
unknown
```

---

## `raw_payload`

Payload bruto recebido da Evolution API.

Tipo:

```txt
JSONB
```

Regra:

- deve ser salvo sempre que possível;
- deve preservar a estrutura original recebida.

---

## `normalized_payload`

Payload convertido para formato interno.

Tipo:

```txt
JSONB
```

Exemplo:

```json
{
  "event_type": "message.received",
  "instance_id": "inst_123",
  "from": "5586999999999",
  "message_type": "text",
  "content": "Olá",
  "timestamp": "2026-05-24T00:00:00Z"
}
```

---

## `processing_status`

Status do processamento interno do evento.

Tipo:

```txt
VARCHAR
```

Valores iniciais:

```txt
received
processed
failed
ignored
```

Descrição:

```txt
received  = evento recebido e salvo
processed = evento processado com sucesso
failed    = falha no processamento
ignored   = evento reconhecido, mas sem ação necessária
```

---

## `forwarded_to_n8n`

Indica se o evento foi encaminhado com sucesso para o n8n.

Tipo:

```txt
BOOLEAN
```

Valor padrão:

```txt
false
```

---

## `n8n_status_code`

Status HTTP retornado pelo webhook do n8n.

Tipo:

```txt
INTEGER
```

Pode ser nulo quando:

- o evento não foi encaminhado;
- o encaminhamento falhou antes de obter resposta;
- não há webhook configurado.

---

## `n8n_response`

Resposta retornada pelo n8n.

Tipo:

```txt
JSONB
```

Pode ser nulo.

---

## `received_at`

Data/hora em que o evento foi recebido pelo backend.

---

## `processed_at`

Data/hora em que o evento foi processado internamente.

---

## `forwarded_at`

Data/hora em que o evento foi encaminhado ao n8n.

---

## `created_at`

Data de criação do registro no banco.

---

## Índices recomendados

```txt
idx_webhook_events_client_id
idx_webhook_events_instance_id
idx_webhook_events_event_type
idx_webhook_events_processing_status
idx_webhook_events_forwarded_to_n8n
idx_webhook_events_received_at
```

Constraints recomendadas:

```txt
FOREIGN KEY (client_id) REFERENCES clients(id)
FOREIGN KEY (instance_id) REFERENCES instances(id)
```

Observação:

- `client_id` e `instance_id` podem ser nulos para preservar eventos não identificados.

---

# 5. Tabela `error_logs`

## Objetivo

Registra falhas relevantes ocorridas durante execução do sistema.

A tabela deve apoiar depuração e auditoria técnica da V1.

---

## Campos

```txt
id UUID PRIMARY KEY
client_id UUID NULL
instance_id UUID NULL
source VARCHAR NOT NULL
error_code VARCHAR NULL
error_message TEXT NOT NULL
details JSONB NULL
raw_payload JSONB NULL
created_at TIMESTAMP WITH TIME ZONE NOT NULL
```

---

## Campos detalhados

## `id`

Identificador interno do erro.

Tipo:

```txt
UUID
```

---

## `client_id`

Cliente relacionado ao erro, quando identificável.

Tipo:

```txt
UUID
```

Pode ser nulo.

---

## `instance_id`

Instância relacionada ao erro, quando identificável.

Tipo:

```txt
UUID
```

Pode ser nulo.

---

## `source`

Origem do erro.

Tipo:

```txt
VARCHAR
```

Valores iniciais:

```txt
backend
provider
evolution
webhook
n8n
database
security
unknown
```

---

## `error_code`

Código interno ou externo do erro.

Tipo:

```txt
VARCHAR
```

Exemplos:

```txt
PROVIDER_ERROR
INSTANCE_NOT_FOUND
N8N_FORWARDING_ERROR
WEBHOOK_PROCESSING_ERROR
DATABASE_ERROR
```

---

## `error_message`

Mensagem descritiva do erro.

Tipo:

```txt
TEXT
```

Regra:

- deve ser útil para depuração;
- não deve expor segredos;
- deve evitar armazenar tokens ou API Keys.

---

## `details`

Detalhes estruturados do erro.

Tipo:

```txt
JSONB
```

Pode conter:

```json
{
  "http_status": 500,
  "operation": "send_text",
  "provider": "evolution"
}
```

---

## `raw_payload`

Payload bruto associado ao erro, quando necessário.

Tipo:

```txt
JSONB
```

Deve ser usado com cautela para não armazenar dados sensíveis desnecessários.

---

## `created_at`

Data/hora do registro do erro.

---

## Índices recomendados

```txt
idx_error_logs_client_id
idx_error_logs_instance_id
idx_error_logs_source
idx_error_logs_error_code
idx_error_logs_created_at
```

Constraints recomendadas:

```txt
FOREIGN KEY (client_id) REFERENCES clients(id)
FOREIGN KEY (instance_id) REFERENCES instances(id)
```

---

## Diagrama lógico simplificado

```txt
clients
  ├── instances
  │     ├── messages
  │     ├── webhook_events
  │     └── error_logs
  │
  ├── messages
  ├── webhook_events
  └── error_logs
```

---

## Relações principais

## `clients` → `instances`

```txt
1 cliente possui N instâncias.
```

Implementação:

```txt
instances.client_id → clients.id
```

---

## `clients` → `messages`

```txt
1 cliente possui N mensagens.
```

Implementação:

```txt
messages.client_id → clients.id
```

---

## `instances` → `messages`

```txt
1 instância possui N mensagens.
```

Implementação:

```txt
messages.instance_id → instances.id
```

---

## `instances` → `webhook_events`

```txt
1 instância pode possuir N eventos de webhook.
```

Implementação:

```txt
webhook_events.instance_id → instances.id
```

---

## `instances` → `error_logs`

```txt
1 instância pode possuir N erros.
```

Implementação:

```txt
error_logs.instance_id → instances.id
```

---

## Campos sensíveis

## API Key

A API Key nunca deve ser armazenada em texto puro.

Armazenar apenas:

```txt
api_key_hash
```

---

## Tokens internos

Os seguintes valores não devem ser salvos em tabelas comuns nem aparecer em logs:

```txt
EVOLUTION_API_KEY
WEBHOOK_SECRET
DATABASE_URL completo
REDIS_URL com senha
```

---

## Payloads brutos

Payloads brutos podem conter dados sensíveis.

Na V1, eles podem ser armazenados para depuração, mas com cautela.

Versões futuras devem avaliar:

- política de retenção;
- anonimização;
- mascaramento;
- limpeza periódica;
- LGPD.

---

## Status e valores controlados

## Status de cliente

```txt
active
inactive
```

---

## Status de instância

```txt
created
connecting
connected
disconnected
error
removed
```

---

## Provider

```txt
evolution
```

Valores futuros possíveis:

```txt
evolution_go
whatsapp_cloud
custom
```

---

## Direção da mensagem

```txt
inbound
outbound
```

---

## Tipos de mensagem

V1:

```txt
text
image
audio
document
video
```

Futuro:

```txt
location
contact
sticker
button
list
carousel
reaction
unknown
```

---

## Status de mensagem

Para mensagens enviadas:

```txt
pending
sent
failed
```

Para mensagens recebidas:

```txt
received
```

Futuros:

```txt
delivered
read
```

---

## Tipos de evento de webhook

```txt
message.received
message.sent
message.delivered
message.read
connection.update
send.error
unknown
```

---

## Status de processamento de webhook

```txt
received
processed
failed
ignored
```

---

## Sources de erro

```txt
backend
provider
evolution
webhook
n8n
database
security
unknown
```

---

## Estratégia de migrations

As alterações de banco serão controladas com Alembic.

A primeira migration deve criar as tabelas:

```txt
clients
instances
messages
webhook_events
error_logs
```

A primeira migration também deve criar:

- chaves primárias;
- chaves estrangeiras;
- constraints básicas;
- índices principais;
- campos de data;
- campos JSONB.

---

## Seed inicial

Para a V1, pode ser criado um mecanismo simples para gerar o primeiro cliente e API Key.

Opções possíveis:

```txt
1. comando CLI interno;
2. script Python;
3. endpoint administrativo temporário protegido por variável de ambiente;
4. seed manual no banco.
```

Recomendação inicial:

```txt
script Python para criar cliente inicial e exibir API Key uma única vez.
```

Exemplo conceitual:

```txt
python scripts/create_client.py --name "Cliente Teste"
```

Saída esperada:

```txt
Client created successfully.
API Key: zapi_xxxxxxxxxxxxxxxxx
Save this key now. It will not be shown again.
```

---

## Exclusão e retenção

Na V1, não haverá política avançada de retenção.

Regras iniciais:

- mensagens não serão apagadas automaticamente;
- eventos webhook não serão apagados automaticamente;
- error_logs não serão apagados automaticamente;
- instâncias removidas poderão ser marcadas como `removed`.

Em versões futuras, avaliar:

- limpeza periódica de logs;
- retenção por cliente;
- anonimização;
- exclusão definitiva;
- LGPD.

---

## Soft delete

Na V1, o uso de soft delete será limitado.

Recomendação:

- para `instances`, usar status `removed`;
- para `clients`, usar status `inactive`;
- para mensagens e logs, manter registros para auditoria técnica.

Não é obrigatório adicionar `deleted_at` em todas as tabelas na V1.

---

## Campos opcionais para evolução futura

Alguns campos podem ser considerados futuramente, mas não são obrigatórios na V1:

```txt
clients.plan
clients.rate_limit_per_minute
clients.monthly_message_limit

instances.metadata
instances.last_seen_at
instances.qr_code_last_generated_at

messages.delivered_at
messages.read_at
messages.reply_to_message_id

webhook_events.retry_count
webhook_events.next_retry_at

error_logs.resolved_at
error_logs.resolution_note
```

Esses campos não devem ser implementados antecipadamente sem necessidade.

---

## Modelo conceitual resumido

```txt
Client
- representa consumidor da API
- autentica via API Key
- possui instâncias

Instance
- representa sessão WhatsApp
- pertence a cliente
- usa provider evolution
- pode ter webhook do n8n

Message
- representa mensagem enviada ou recebida
- pertence a cliente e instância
- possui direção, tipo e status

WebhookEvent
- representa evento recebido da Evolution API
- preserva payload bruto
- pode ser normalizado
- pode ser encaminhado ao n8n

ErrorLog
- representa falha relevante
- pode estar ligado a cliente e instância
- apoia depuração
```

---

## Critérios de conformidade da modelagem

A modelagem estará adequada para a V1 se permitir:

- autenticar clientes por API Key;
- associar instâncias a clientes;
- armazenar identificador da instância no provider;
- registrar mensagens enviadas;
- registrar mensagens recebidas;
- salvar webhooks brutos;
- salvar webhooks normalizados;
- registrar envio ou falha para n8n;
- registrar erros relevantes;
- consultar logs básicos;
- evoluir para múltiplos providers no futuro.

---

## Resumo

A modelagem de dados da V1 será composta por cinco tabelas principais:

```txt
clients
instances
messages
webhook_events
error_logs
```

Essa estrutura cobre o núcleo técnico do sistema: clientes, instâncias, mensagens, webhooks e erros.

A modelagem usa PostgreSQL com UUIDs, timestamps, campos JSONB para payloads variáveis e strings controladas pela aplicação para status e tipos.

Essa abordagem mantém a V1 simples, mas preparada para evolução futura.