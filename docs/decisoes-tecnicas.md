# 09 — Decisões Técnicas

## Objetivo do documento

Este documento registra as decisões técnicas oficiais da V1 do projeto **Z-API Própria / Gateway WhatsApp**.

O objetivo é manter um histórico claro das escolhas feitas durante o planejamento, evitando rediscussões desnecessárias e garantindo que specs, plans, tasks e implementação sigam a mesma direção.

Este documento deve ser atualizado sempre que uma decisão técnica relevante for tomada, alterada ou substituída.

---

## Visão geral das decisões da V1

A V1 será construída como um backend próprio em Python, usando FastAPI, PostgreSQL, Redis, n8n e Evolution API como provider inicial.

A proposta não é reescrever a Evolution API, mas criar uma camada própria de controle sobre ela.

Fluxo geral:

```txt
Cliente externo / Sistema / n8n
        ↓
Backend FastAPI
        ↓
MessagingProvider
        ↓
EvolutionProvider
        ↓
Evolution API
        ↓
WhatsApp
```

Para webhooks:

```txt
WhatsApp
        ↓
Evolution API
        ↓
Backend FastAPI
        ↓
n8n
```

---

# DT-001 — Backend FastAPI como API principal

## Decisão

O backend principal do sistema será desenvolvido com:

```txt
Python + FastAPI
```

## Justificativa

FastAPI foi escolhido por oferecer:

- boa performance;
- suporte a aplicações assíncronas;
- integração nativa com Pydantic;
- geração automática de documentação OpenAPI/Swagger;
- boa produtividade para APIs REST;
- ecossistema adequado para integrações HTTP.

## Consequências

O backend será responsável por:

- expor a API pública;
- autenticar clientes;
- gerenciar instâncias;
- enviar mensagens;
- receber webhooks;
- persistir dados;
- encaminhar eventos para n8n;
- isolar o provider interno.

---

# DT-002 — Backend como ponto único de entrada

## Decisão

Clientes externos devem consumir apenas a API do backend próprio.

Fluxo correto:

```txt
Cliente externo
    ↓
Backend FastAPI
    ↓
Evolution API
```

Fluxo evitado:

```txt
Cliente externo
    ↓
Evolution API
```

## Justificativa

Essa decisão garante:

- autenticação própria;
- padronização dos contratos;
- logs centralizados;
- persistência própria;
- controle sobre segurança;
- integração controlada com n8n;
- menor acoplamento com Evolution API;
- possibilidade futura de cobrança e limites por cliente.

## Consequências

A Evolution API será tratada como serviço interno e não deverá ser exposta diretamente para consumidores externos.

---

# DT-003 — Evolution API como provider inicial

## Decisão

A V1 utilizará a **Evolution API** como provider inicial para comunicação com WhatsApp.

## Justificativa

A Evolution API já fornece recursos necessários para a primeira validação técnica:

- criação de instâncias;
- conexão via QR Code/status;
- desconexão/logout;
- envio de mensagens;
- recebimento de eventos;
- integração via API HTTP.

## Consequências

A Evolution API será encapsulada pelo backend.

O sistema não deve depender diretamente dos endpoints da Evolution API nas rotas públicas ou nas regras centrais.

---

# DT-004 — Usar versão anterior estável da Evolution API na V1

## Decisão

A V1 começará com a **Opção A**: usar uma versão anterior e estável da Evolution API, preferencialmente da linha `2.3.x`, para validar o sistema.

## Justificativa

Essa decisão reduz a complexidade inicial relacionada a fluxos mais recentes de licença/ativação e permite validar primeiro o núcleo técnico do projeto.

## Regras

- não usar `latest` sem confirmar a versão real da imagem;
- fixar a versão usada no Docker Compose;
- documentar a versão escolhida;
- testar criação, conexão, envio e webhook com a versão fixada.

## Consequências

O projeto começa mais simples, mas deve manter arquitetura preparada para atualização futura da Evolution API ou troca de provider.

---

# DT-005 — Provider abstrato com `MessagingProvider`

## Decisão

A comunicação com engines de mensageria será abstraída por uma interface interna chamada:

```txt
MessagingProvider
```

Na V1, haverá apenas uma implementação:

```txt
EvolutionProvider
```

## Justificativa

Essa decisão permite que o sistema possa futuramente migrar para:

- versão mais nova da Evolution API;
- Evolution Go;
- WhatsApp Cloud API;
- outro provider;
- engine própria.

## Consequências

Rotas e services não devem chamar diretamente endpoints da Evolution API.

Fluxo correto:

```txt
Route
    ↓
Service
    ↓
MessagingProvider
    ↓
EvolutionProvider
    ↓
Evolution API
```

---

# DT-006 — SQLAlchemy puro para ORM

## Decisão

A V1 utilizará:

```txt
SQLAlchemy puro
```

para modelagem e persistência no banco de dados.

## Justificativa

SQLAlchemy puro oferece:

- maior controle sobre modelos ORM;
- maior flexibilidade;
- melhor separação entre banco e API;
- bom suporte a relacionamentos;
- boa integração com Alembic;
- maior adequação para arquitetura modular.

## Consequências

Os modelos de banco serão definidos separadamente dos schemas da API.

---

# DT-007 — Pydantic para schemas e validação

## Decisão

A V1 utilizará:

```txt
Pydantic
```

para validação, serialização e contratos da API.

## Justificativa

Pydantic é o padrão natural em projetos FastAPI e será usado para:

- validar payloads de entrada;
- definir respostas da API;
- validar payloads normalizados;
- definir schemas internos;
- gerar documentação via OpenAPI.

## Consequências

Schemas da API não devem ser confundidos com modelos ORM do SQLAlchemy.

---

# DT-008 — Alembic para migrations

## Decisão

A V1 utilizará:

```txt
Alembic
```

para versionar alterações no schema do banco.

## Justificativa

Alembic é a ferramenta padrão para migrations em projetos que usam SQLAlchemy.

## Consequências

Toda mudança estrutural no banco deve ser feita por migration.

A primeira migration deve criar:

```txt
clients
instances
messages
webhook_events
error_logs
```

---

# DT-009 — Não usar SQLModel na V1

## Decisão

O projeto **não utilizará SQLModel na V1**.

## Justificativa

Apesar de SQLModel ser útil para projetos menores ou CRUDs simples, este projeto precisa de separação clara entre:

- modelos de banco;
- schemas de entrada;
- schemas de saída;
- payloads da Evolution API;
- payloads normalizados;
- payloads enviados ao n8n.

## Consequências

A stack oficial da V1 será:

```txt
SQLAlchemy puro + Pydantic + Alembic
```

---

# DT-010 — PostgreSQL como banco principal

## Decisão

O banco principal da V1 será:

```txt
PostgreSQL
```

## Justificativa

PostgreSQL foi escolhido por ser:

- robusto;
- confiável;
- amplamente usado;
- adequado para dados relacionais;
- compatível com JSONB;
- adequado para logs, eventos e payloads brutos;
- preparado para evolução futura do projeto.

## Consequências

A modelagem inicial terá cinco tabelas principais:

```txt
clients
instances
messages
webhook_events
error_logs
```

---

# DT-011 — Uso de UUIDs como identificadores

## Decisão

As entidades principais usarão:

```txt
UUID
```

como identificadores.

## Justificativa

UUIDs reduzem previsibilidade dos IDs e são adequados para APIs públicas.

## Consequências

As tabelas principais terão:

```txt
id UUID PRIMARY KEY
```

---

# DT-012 — JSONB para payloads brutos e dados variáveis

## Decisão

Campos de payload bruto, payload normalizado, respostas de provider e detalhes variáveis usarão:

```txt
JSONB
```

## Justificativa

Webhooks, respostas da Evolution API e payloads do n8n podem variar bastante.

JSONB permite preservar esses dados sem engessar a modelagem.

## Consequências

Campos como os seguintes poderão usar JSONB:

```txt
raw_payload
normalized_payload
provider_response
n8n_response
details
```

---

# DT-013 — Redis incluído desde a V1

## Decisão

O Redis será incluído no ambiente local desde a V1.

## Justificativa

Mesmo que seu uso inicial seja mínimo, Redis prepara o projeto para:

- filas;
- retries;
- cache;
- rate limiting futuro;
- processamento assíncrono.

## Consequências

O Docker Compose deve conter serviço Redis.

Na V1, ele pode ficar disponível mesmo que nem todos os fluxos dependam dele inicialmente.

---

# DT-014 — Docker Compose para ambiente local

## Decisão

A V1 usará:

```txt
Docker Compose
```

para orquestrar o ambiente local.

## Serviços previstos

```txt
backend
postgres
redis
n8n
evolution-api
```

## Justificativa

Docker Compose facilita:

- padronização do ambiente;
- execução local reproduzível;
- integração entre serviços;
- testes end-to-end;
- isolamento das dependências.

## Consequências

O projeto deve fornecer um `docker-compose.yml` funcional e um `.env.example`.

---

# DT-015 — HTTPX para chamadas HTTP externas

## Decisão

A V1 utilizará:

```txt
HTTPX
```

para chamadas HTTP externas.

## Usos principais

- chamar Evolution API;
- encaminhar eventos para n8n;
- consumir APIs externas futuras, se necessário.

## Justificativa

HTTPX suporta chamadas assíncronas e combina bem com FastAPI.

## Consequências

O provider da Evolution API deve usar um cliente HTTP interno baseado em HTTPX.

---

# DT-016 — n8n atrás do backend

## Decisão

Na V1, o n8n receberá eventos encaminhados pelo backend, e não diretamente pela Evolution API.

Fluxo correto:

```txt
Evolution API
    ↓
Backend FastAPI
    ↓
n8n
```

Fluxo evitado:

```txt
Evolution API
    ↓
n8n
```

## Justificativa

Essa decisão permite:

- salvar payload bruto;
- normalizar eventos;
- registrar mensagens;
- registrar erros;
- controlar encaminhamento;
- desacoplar Evolution API do n8n;
- aplicar regras de segurança.

## Consequências

A spec de webhooks deve implementar recebimento, persistência, normalização e só depois encaminhamento para n8n.

---

# DT-017 — Webhook do n8n preferencialmente por instância

## Decisão

Na V1, o webhook do n8n será preferencialmente configurado por instância.

Campo previsto:

```txt
instances.n8n_webhook_url
```

## Justificativa

Essa decisão permite:

- fluxos diferentes por número;
- maior flexibilidade;
- facilidade de testes;
- menor ambiguidade;
- melhor aderência a cenários reais.

## Consequências

Cada instância poderá ter uma URL própria de webhook do n8n.

---

# DT-018 — API Key para autenticação da V1

## Decisão

A autenticação dos clientes externos será feita por:

```txt
API Key
```

Header padrão:

```http
X-API-Key: chave_do_cliente
```

## Justificativa

API Key é suficiente para a V1, pois o uso previsto é integração servidor-servidor.

## Consequências

As rotas de instâncias, mensagens e logs devem exigir API Key.

---

# DT-019 — API Key armazenada apenas como hash

## Decisão

A API Key não deve ser armazenada em texto puro.

O banco deve armazenar apenas:

```txt
api_key_hash
```

## Justificativa

Reduz risco em caso de vazamento do banco.

## Consequências

A API Key original deve ser exibida apenas uma vez, no momento da criação do cliente.

---

# DT-020 — Webhook da Evolution API protegido por segredo próprio

## Decisão

A rota de webhook da Evolution API usará segredo compartilhado via header.

Header recomendado:

```http
X-Webhook-Secret: segredo_interno
```

## Justificativa

A chamada de webhook não representa um cliente externo usando a API, portanto não deve usar a API Key do cliente.

## Consequências

O endpoint abaixo deve validar `X-Webhook-Secret`:

```http
POST /v1/webhooks/evolution
```

---

# DT-021 — Resposta de erro padronizada

## Decisão

Erros da API devem seguir o formato:

```json
{
  "code": "ERROR_CODE",
  "message": "Mensagem legível do erro.",
  "details": {}
}
```

## Justificativa

Um padrão de erro facilita:

- depuração;
- consumo por clientes externos;
- integração com n8n;
- testes automatizados;
- evolução da API.

## Consequências

Services e rotas devem evitar respostas de erro soltas ou inconsistentes.

---

# DT-022 — Prefixo `/v1` para API pública

## Decisão

A API pública da primeira versão usará o prefixo:

```txt
/v1
```

Exemplos:

```txt
/v1/instances
/v1/messages/text
/v1/webhooks/evolution
/v1/logs/messages
```

## Justificativa

Versionamento explícito facilita evolução futura da API.

## Consequências

Mudanças incompatíveis futuras poderão usar `/v2`.

---

# DT-023 — Health check público

## Decisão

O endpoint de health check será público e não exigirá API Key.

Endpoint:

```http
GET /health
```

## Justificativa

Facilita testes locais, Docker health checks e validação simples da aplicação.

## Consequências

Esse endpoint deve retornar apenas informações não sensíveis.

---

# DT-024 — Logs básicos persistidos

## Decisão

A V1 registrará logs básicos em banco, especialmente:

- mensagens enviadas;
- mensagens recebidas;
- eventos de webhook;
- erros relevantes.

## Justificativa

Logs são essenciais para validar integrações com Evolution API e n8n.

## Consequências

As tabelas `messages`, `webhook_events` e `error_logs` devem existir desde a V1.

---

# DT-025 — Payload bruto salvo com cautela

## Decisão

A V1 poderá salvar payloads brutos de webhooks, mensagens e respostas externas para depuração.

## Justificativa

Como a integração depende de formatos externos, preservar payloads brutos facilita ajustes e investigação de falhas.

## Cuidados

Payloads brutos podem conter dados sensíveis.

O sistema deve evitar expor esses dados desnecessariamente nas respostas públicas.

## Consequências

Versões futuras devem avaliar política de retenção, anonimização e adequação à LGPD.

---

# DT-026 — Não implementar painel administrativo na V1

## Decisão

A V1 não terá painel administrativo.

## Justificativa

O foco inicial é validar o backend, os fluxos de instância, mensagens, webhooks e n8n.

## Consequências

A gestão inicial será feita por API, scripts administrativos e logs básicos.

---

# DT-027 — Não implementar cobrança na V1

## Decisão

A V1 não terá sistema de cobrança, planos ou assinatura.

## Justificativa

Cobrança só faz sentido após validar o núcleo técnico do gateway.

## Consequências

Não haverá gateway de pagamento, planos, limites por plano ou módulo comercial na V1.

---

# DT-028 — Não implementar chatbot com IA na V1

## Decisão

A V1 não terá chatbot com IA embutido.

## Justificativa

O objetivo é primeiro validar mensageria, webhooks e integração com n8n.

## Consequências

Automatizações simples poderão ser feitas no n8n, mas o backend não terá módulo próprio de IA na V1.

---

# DT-029 — Não implementar campanhas ou disparo em massa na V1

## Decisão

A V1 não terá módulo de campanhas, disparos em massa ou listas de envio.

## Justificativa

Esses recursos aumentam risco técnico, operacional e de bloqueio de número.

## Consequências

A V1 terá apenas envio individual por endpoint.

---

# DT-030 — Não implementar multi-provider real na V1

## Decisão

A V1 terá arquitetura preparada para múltiplos providers, mas implementará apenas:

```txt
EvolutionProvider
```

## Justificativa

Implementar múltiplos providers desde o início aumentaria a complexidade sem necessidade para validação inicial.

## Consequências

A abstração `MessagingProvider` deve existir, mas apenas um provider concreto será implementado.

---

# DT-031 — Scripts administrativos para cliente inicial

## Decisão

A criação do cliente inicial e da API Key será feita preferencialmente por script administrativo.

Exemplo:

```bash
python scripts/create_client.py --name "Cliente Teste"
```

## Justificativa

A V1 não terá painel nem CRUD público de clientes.

## Consequências

O script deve criar um cliente, gerar a API Key e exibir a chave apenas uma vez.

---

# DT-032 — `uv` como gerenciador de dependências

## Decisão

A V1 usará preferencialmente:

```txt
uv
```

como gerenciador de dependências Python.

## Justificativa

`uv` é rápido, moderno e adequado para projetos Python atuais.

## Consequências

O projeto poderá usar `pyproject.toml` e comandos baseados em `uv`.

---

# DT-033 — Variáveis de ambiente obrigatórias

## Decisão

O projeto utilizará as seguintes variáveis de ambiente, todas obrigatórias salvo indicação:

```bash
# Banco
DATABASE_URL=postgresql+asyncpg://user:pass@postgres:5432/zapi

# Redis
REDIS_URL=redis://redis:6379/0

# Evolution API
EVOLUTION_API_URL=http://evolution-api:8080
EVOLUTION_API_KEY=sua_chave_global_evolution

# Segurança
WEBHOOK_SECRET=segredo_compartilhado_evolution
API_KEY_SALT=salt_para_hash_das_api_keys

# n8n (fallback global — instância pode sobrescrever via n8n_webhook_url)
N8N_DEFAULT_WEBHOOK_URL=http://n8n:5678/webhook/zapi

# Aplicação
APP_ENV=development
LOG_LEVEL=INFO
APP_PORT=8000
HTTP_TIMEOUT=30
```

## Justificativa

Sem essa lista definida, o `docker-compose.yml`, o `.env.example` e o módulo de configuração (`core/config.py`) seriam escritos no improviso, gerando inconsistências entre specs.

`N8N_DEFAULT_WEBHOOK_URL` é mantida como fallback global: se uma instância não tiver `n8n_webhook_url` configurado, o backend precisa de algum destino — sem fallback, eventos seriam silenciados.

`API_KEY_SALT` é obrigatório para o mecanismo de hash definido em DT-019. Sem salt, hashes iguais expõem colisões.

## Consequências

A Spec 001 deve criar `core/config.py` lendo todas essas variáveis via Pydantic Settings.

O projeto deve fornecer um `.env.example` completo e atualizado com todas as variáveis listadas acima.

---

# DT-034 — Estrutura de diretórios do projeto

## Decisão

A estrutura de diretórios oficial do projeto é:

```txt
app/
  api/
    v1/
      routes/         → instances.py, messages.py, webhooks.py, logs.py
      dependencies/   → auth.py (valida X-API-Key), webhook_auth.py
  services/           → instance_service.py, message_service.py, webhook_service.py
  providers/
    base.py           → interface MessagingProvider (ABC)
    evolution/
      client.py       → cliente HTTPX para Evolution API
      provider.py     → EvolutionProvider implementando MessagingProvider
      normalizer.py   → normalização de payloads de webhook
  models/             → client.py, instance.py, message.py, webhook_event.py, error_log.py
  schemas/            → (mesma estrutura dos models, separado por domínio)
  core/
    config.py         → leitura de env vars via Pydantic Settings
    security.py       → hash/verificação de API Key
    logging.py        → configuração de logging
    database.py       → engine, session factory
    redis.py          → client Redis
alembic/
  versions/
scripts/
  create_client.py    → cria cliente e gera API Key (DT-031)
tests/
  unit/
  integration/
```

## Justificativa

Sem estrutura definida, cada spec pode criar pastas de forma inconsistente, quebrando a separação de camadas documentada em DT-005 e DT-006.

O `normalizer.py` fica dentro do provider intencionalmente: o DT-016 exige normalização antes do encaminhamento ao n8n, e isolar essa lógica no provider evita que `webhook_service` conheça detalhes da Evolution API.

## Consequências

A Spec 001 deve criar essa estrutura de diretórios base (mesmo que vazia) antes de qualquer implementação de lógica.

---

# DT-035 — Entrega da API Key ao cliente

## Decisão

O script administrativo suportará dois fluxos:

```bash
# Cria cliente e exibe API Key uma vez
python scripts/create_client.py --name "Nome do Cliente"

# Invalida key atual, gera nova e exibe uma vez
python scripts/create_client.py --rotate <client_id>
```

A chave original nunca é armazenada — apenas o hash (DT-019). Uma vez perdida, só pode ser substituída via `--rotate`.

## Justificativa

A Opção A (recriar cliente) foi descartada porque tornaria todos os dados históricos do cliente (instâncias, mensagens, logs) órfãos sem migração manual.

A Opção B não viola DT-019: a chave anterior é substituída no banco, e a nova é exibida uma única vez.

O DT-026 define que a gestão será feita por scripts na V1, portanto `--rotate` é o mecanismo correto sem precisar de painel.

## Consequências

A Spec 008 deve implementar os dois fluxos do script e documentar o comportamento esperado em cada um.

---

# DT-036 — Política de retry e falha para chamadas à Evolution API

## Decisão

A V1 usará **falha imediata** (Opção A):

```txt
1. Chama Evolution API
2. Se falhar → registra status "failed" na tabela messages
             → registra detalhes em error_logs
3. Retorna erro padronizado ao cliente (DT-021)
4. Cliente decide se tenta novamente
```

## Justificativa

Retry assíncrono (Opção C) dependeria do Redis, cujo papel na V1 ainda está em aberto (decisão pendente #5). Introduzir essa dependência antes de definir o escopo do Redis adicionaria complexidade sem necessidade.

A V1 é validação técnica — comportamento previsível e simples é mais valioso do que resiliência automática que pode mascarar falhas da Evolution API durante o desenvolvimento.

A tabela `messages` já prevê o campo `status` com valor `failed`, portanto a infraestrutura para Opção A já está na modelagem.

Retry automático poderá entrar em versão futura, usando Redis, quando o papel do Redis estiver definido.

## Consequências

A Spec 002 deve implementar esse comportamento de forma uniforme em todas as operações do `EvolutionProvider` (texto, imagem, áudio, documento, vídeo).

---

# DT-037 — Paginação nos endpoints de listagem

## Decisão

A V1 usará **paginação por offset** (Opção A):

```txt
GET /v1/logs/messages?page=1&limit=50
GET /v1/logs/webhook-events?page=1&limit=50
GET /v1/logs/errors?page=1&limit=50
```

Formato de resposta padrão:

```json
{
  "data": [...],
  "pagination": {
    "page": 1,
    "limit": 50,
    "total": 320
  }
}
```

## Justificativa

Cursor pagination (Opção B) depende de campo ordenável sequencialmente. Com UUIDs como PKs (DT-011), exigiria ordenar por `created_at` com cuidados extras para evitar duplicatas em timestamps iguais — complexidade desnecessária para a V1.

Limite fixo sem paginação (Opção C) foi descartado: a tabela `webhook_events` pode acumular centenas de registros por hora em uso real, tornando o endpoint inutilizável rapidamente.

Paginação por offset é o padrão mais direto para uso manual e para consumo via n8n, que é o principal consumidor dos logs na V1.

## Consequências

A paginação por offset deve ser aplicada uniformemente em todos os endpoints de listagem. O `limit` máximo por requisição deve ser definido na implementação (sugestão: 100).

---

# DT-038 — Versão exata da Evolution API

## Decisão

A V1 utilizará a versão fixa:

```txt
evoapicloud/evolution-api:v2.3.4
```

## Justificativa

É a última patch estável da linha 2.3.x, com menor complexidade e sem fluxos recentes de licença/ativação.

## Consequências

O `docker-compose.yml` deve fixar essa imagem. Não usar `latest`.

---

# DT-039 — Portas locais do Docker Compose

## Decisão

As portas expostas localmente serão:

```txt
backend:        8000
postgres:       5432
redis:          6379
n8n:            5678
evolution-api:  8080
```

## Justificativa

São as portas convencionais de cada serviço, facilitando uso sem configuração adicional.

## Consequências

O `.env.example` e o `docker-compose.yml` devem usar essas portas como padrão.

---

# DT-040 — Nome final do pacote Python

## Decisão

O pacote/projeto Python se chamará:

```txt
whatsapp_gateway
```

## Justificativa

Nome genérico, não vincula à marca Z-API, descritivo do propósito do projeto.

## Consequências

O `pyproject.toml` deve usar `name = "whatsapp_gateway"`. O diretório principal da aplicação permanece `app/`.

---

# DT-041 — Formato do provider_instance_name

## Decisão

O `provider_instance_name` será gerado pelo backend no formato:

```txt
inst_{uuid_short}
```

Onde `uuid_short` são os primeiros 8 caracteres de um UUID v4.

Exemplo:

```txt
inst_a1b2c3d4
```

## Justificativa

Único, sem risco de colisão prática, sem dados do cliente expostos, sem caracteres especiais.

## Consequências

O `InstanceService` deve gerar esse valor automaticamente na criação. O cliente não define esse campo.

---

# DT-042 — Redis apenas provisionado na V1

## Decisão

O Redis será incluído no Docker Compose da V1, mas **não será usado ativamente** em nenhum fluxo.

## Justificativa

Mantém a infraestrutura preparada para evoluções futuras (filas, cache, rate limiting) sem adicionar complexidade à implementação da V1.

## Consequências

O código da V1 não deve depender do Redis para funcionar. A connection string deve existir no `.env.example`, mas nenhum service ou provider a utiliza.

---

# DT-043 — Retry para n8n: apenas marcação de falha

## Decisão

Na V1, o encaminhamento para o n8n terá **uma única tentativa**. Se falhar:

```txt
1. Marca forwarded_to_n8n = false
2. Registra n8n_status_code e n8n_response quando disponíveis
3. Registra erro em error_logs com código N8N_FORWARDING_ERROR
4. Não tenta novamente
```

## Justificativa

Comportamento previsível e simples. Retry automático dependeria de fila (Redis) ou lógica assíncrona que está fora do escopo da V1.

## Consequências

O `WebhookService` ou `N8nForwardingService` deve implementar esse fluxo linear. O cliente ou operador pode consultar falhas via `/v1/logs/errors`.

---

# DT-044 — Normalização de números de telefone

## Decisão

O backend aplicará a seguinte normalização antes de enviar ao provider:

```txt
1. Remover caracteres não numéricos (+, -, espaços, parênteses)
2. Se o número resultante NÃO começar com "55", adicionar "55" como prefixo
3. Enviar ao provider no formato: {número}@s.whatsapp.net
```

Exemplos:

```txt
Entrada: 86999999999     → Normalizado: 5586999999999@s.whatsapp.net
Entrada: 5586999999999   → Normalizado: 5586999999999@s.whatsapp.net
Entrada: +5586999999999  → Normalizado: 5586999999999@s.whatsapp.net
```

## Justificativa

Assume Brasil como padrão (DDI 55). Regra simples e funcional para a V1. O sufixo `@s.whatsapp.net` é exigido pela Evolution API.

## Consequências

Um utilitário de normalização deve ser criado em `app/core/phone.py` ou similar. Endpoints de envio devem normalizar antes de chamar o provider.

---

# DT-045 — Schemas Pydantic definidos durante implementação

## Decisão

Os schemas Pydantic de cada endpoint serão definidos **durante a implementação de cada spec**, seguindo os contratos já documentados em `07-contratos-api.md`.

## Justificativa

Os contratos (payloads de request/response) já estão definidos com exemplos JSON. Escrever schemas Pydantic antecipadamente em documento separado geraria retrabalho caso os contratos evoluam durante a implementação.

## Consequências

Cada spec deve criar seus schemas em `app/schemas/` seguindo fielmente os contratos do doc 07. Os schemas não precisam de documento adicional prévio.

---

# DT-046 — Mapeamento de estados provider ↔ persistence

## Decisão

Os estados de instância no provider (retornados pela Evolution API) e os estados persistidos no banco de dados são conjuntos distintos com mapeamento explícito:

**Provider (spec 002)** retorna: `connected`, `disconnected`, `connecting`, `not_found`
**DB (spec 003)** armazena: `disconnected`, `connecting`, `connected`, `closed`

Mapeamento:
- Provider `connected` → DB `connected`
- Provider `disconnected` → DB `disconnected`
- Provider `connecting` → DB `connecting`
- Provider `not_found` → Não é um estado de DB. Indica instância inexistente no provider. O service layer decide a ação (pode marcar como `closed` ou `disconnected` conforme contexto).
- DB `closed` → Estado terminal interno. Instância encerrada no sistema. Ocorre quando: (a) admin remove a instância, ou (b) instância detectada como permanentemente indisponível no provider. Instâncias `closed` são combinadas com soft-delete (`deleted_at`).

## Justificativa

Provider states são respostas externas de uma API terceira; DB states representam o ciclo de vida interno da entidade. `not_found` é uma resposta, não um estado persistível. `closed` é um conceito de negócio (encerramento definitivo) que não existe na Evolution API.

## Consequências

- Spec 002 não precisa de alteração — seus estados estão corretos como "retorno do provider"
- Spec 003 mantém `closed` como 4º estado terminal
- O service layer (spec 004+) será responsável por traduzir respostas do provider em transições de estado no DB

---

## Alteração — DT implementada durante integração com Evolution API v2.3.4

Durante a integração real com a Evolution API v2.3.4, foram identificados comportamentos que geraram ajustes em relação ao planejamento:

**Criação de instância com webhook separado:**
A Evolution API v2.3.4 não aceita o campo `webhook` embutido no payload de `POST /instance/create`. O webhook deve ser configurado em chamada separada via `POST /webhook/set/{instanceName}` após a criação.

**Formato de eventos no payload do webhook:**
A Evolution API v2.3.4 envia eventos em formato `MESSAGES_UPSERT` (maiúsculo com underscore), não em `messages.upsert` (minúsculo com ponto) como documentado em versões anteriores. O classifier (`app/webhooks/classifier.py`) normaliza o campo `event` antes de comparar:

```python
event = payload.get("event", "").upper().replace(".", "_")
```

Isso garante compatibilidade com qualquer variação de formato do campo de evento.

**Headers do webhook por instância:**
A configuração de segredo no webhook é feita via campo `headers` no payload do `/webhook/set/{instanceName}`, não via campo `secret`.

---

## Stack oficial da V1

A stack oficial da V1 fica definida como:

```txt
Python
FastAPI
Pydantic
SQLAlchemy puro
Alembic
PostgreSQL
Redis
HTTPX
Evolution API
n8n
Docker Compose
pytest
pytest-asyncio
uv
```

---

## Lista oficial de specs da V1

A V1 será organizada nas seguintes specs:

```txt
001 — Base do backend e infraestrutura local
002 — Provider Evolution API
003 — Persistência e modelagem inicial
004 — Gestão de instâncias WhatsApp
005 — Envio de mensagens
006 — Recebimento de webhooks
007 — Encaminhamento para n8n
008 — Segurança com API Key
```

---

## Decisões pendentes

Todas as decisões pendentes foram fechadas e registradas como DT-038 a DT-045.

---

## Mudança de decisões

Caso alguma decisão deste documento seja alterada futuramente, a alteração deve ser registrada com:

```txt
- decisão anterior;
- nova decisão;
- motivo da mudança;
- impacto nas specs, plans e tasks.
```

Exemplo:

```md
## Alteração — DT-004

### Decisão anterior
Usar Evolution API 2.3.x.

### Nova decisão
Migrar para Evolution API 2.4.x.

### Motivo
Necessidade de recurso disponível apenas na versão mais nova.

### Impacto
Atualizar Docker Compose, provider, testes de integração e documentação de ativação/licença.
```

---

## Critérios de conformidade

O projeto estará alinhado a este documento se:

- usar FastAPI como backend principal;
- expor apenas o backend para clientes externos;
- encapsular Evolution API em `EvolutionProvider`;
- usar `MessagingProvider` como abstração;
- usar SQLAlchemy puro, Pydantic e Alembic;
- usar PostgreSQL como banco principal;
- incluir Redis e n8n na infraestrutura local;
- proteger rotas públicas com API Key;
- proteger webhook da Evolution API com segredo próprio;
- salvar mensagens, webhooks e erros;
- não implementar painel, cobrança, chatbot ou campanhas na V1;
- manter a lista oficial de specs como base do planejamento.

---

## Resumo

Este documento consolida as principais decisões técnicas da V1 do projeto.

A V1 será uma API própria de mensageria para WhatsApp, construída com FastAPI, PostgreSQL, SQLAlchemy, Pydantic, Alembic, Redis, Evolution API, n8n e Docker Compose.

A Evolution API será usada como provider inicial, mas ficará encapsulada em uma camada própria para evitar acoplamento.

O backend será o ponto único de entrada para clientes externos, responsável por segurança, instâncias, mensagens, webhooks, logs, persistência e encaminhamento para n8n.

A V1 não incluirá painel, cobrança, chatbot, campanhas ou multi-provider real, mantendo o foco na validação técnica do núcleo do sistema.