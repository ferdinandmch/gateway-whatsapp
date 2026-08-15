# 04 — Stack Técnica

## Objetivo do documento

Este documento define a stack técnica oficial da V1 do projeto **Z-API Própria / Gateway WhatsApp**.

A stack foi escolhida com foco em:

- simplicidade para iniciar;
- boa organização arquitetural;
- compatibilidade com FastAPI;
- facilidade de execução local com Docker;
- integração com Evolution API;
- persistência confiável com PostgreSQL;
- possibilidade de evolução futura para filas, painel, SaaS e múltiplos providers.

---

## Visão geral da stack

A V1 utilizará a seguinte stack principal:

```txt
Backend: Python + FastAPI
ORM: SQLAlchemy puro
Schemas e validação: Pydantic
Migrations: Alembic
Banco de dados: PostgreSQL
Cache/infra auxiliar: Redis
Comunicação HTTP externa: HTTPX
Engine WhatsApp: Evolution API
Automação: n8n
Infraestrutura local: Docker Compose
Testes: pytest
```

---

## Backend

## Tecnologia escolhida

```txt
Python + FastAPI
```

## Função no projeto

O backend será a aplicação principal do sistema.

Ele será responsável por:

- expor a API pública;
- autenticar clientes por API Key;
- gerenciar clientes;
- gerenciar instâncias de WhatsApp;
- enviar mensagens;
- receber webhooks;
- normalizar eventos;
- salvar dados no PostgreSQL;
- encaminhar eventos ao n8n;
- encapsular a comunicação com a Evolution API.

## Justificativa

FastAPI foi escolhido porque oferece:

- boa performance;
- suporte nativo a aplicações assíncronas;
- integração direta com Pydantic;
- geração automática de documentação OpenAPI/Swagger;
- boa experiência para construção de APIs REST;
- ecossistema maduro para projetos Python modernos.

---

## Linguagem

## Tecnologia escolhida

```txt
Python
```

## Função no projeto

Python será usado para implementar o backend principal.

## Justificativa

Python é adequado para este projeto porque:

- possui excelente ecossistema para APIs;
- integra bem com automações;
- possui boa produtividade;
- facilita integração com serviços externos;
- é compatível com FastAPI, SQLAlchemy, Alembic, HTTPX e pytest.

---

## Validação e schemas

## Tecnologia escolhida

```txt
Pydantic
```

## Função no projeto

Pydantic será usado para:

- validar payloads de entrada;
- definir contratos de resposta;
- serializar objetos para JSON;
- validar configurações da aplicação;
- representar payloads normalizados;
- documentar automaticamente a API via FastAPI.

## Exemplos de uso

```txt
- schemas de criação de instância;
- schemas de envio de mensagem;
- schemas de resposta da API;
- schemas de webhook normalizado;
- schemas de erro padronizado;
- schemas de configuração.
```

## Justificativa

Pydantic permite separar claramente:

```txt
modelo de entrada da API
modelo de resposta da API
modelo interno da aplicação
modelo de banco de dados
```

Essa separação é importante porque nem tudo que existe no banco deve ser exposto na API.

---

## ORM e persistência

## Tecnologia escolhida

```txt
SQLAlchemy puro
```

## Função no projeto

SQLAlchemy será usado para:

- definir modelos ORM;
- representar tabelas do banco;
- criar relacionamentos;
- executar consultas;
- controlar sessões;
- persistir entidades;
- lidar com transações.

## Entidades iniciais

```txt
clients
instances
messages
webhook_events
error_logs
```

## Justificativa

SQLAlchemy puro foi escolhido porque oferece:

- maior flexibilidade;
- maior controle da camada de persistência;
- separação clara entre banco e schemas da API;
- melhor adequação para arquitetura modular;
- bom suporte a relacionamentos;
- amplo uso em projetos Python profissionais.

---

## Migrations

## Tecnologia escolhida

```txt
Alembic
```

## Função no projeto

Alembic será usado para versionar a estrutura do banco de dados.

Ele será responsável por:

- criar migrations;
- aplicar migrations;
- reverter migrations quando necessário;
- manter histórico das alterações do banco;
- controlar evolução do schema do PostgreSQL.

## Justificativa

Como o projeto usará SQLAlchemy, Alembic é a escolha natural para migrations.

---

## Banco de dados

## Tecnologia escolhida

```txt
PostgreSQL
```

## Função no projeto

PostgreSQL será o banco principal da V1.

Ele armazenará:

- clientes;
- instâncias;
- mensagens enviadas;
- mensagens recebidas;
- eventos de webhook;
- logs de erro;
- configurações de webhook do n8n.

## Justificativa

PostgreSQL foi escolhido porque:

- é robusto;
- é confiável;
- suporta dados relacionais;
- suporta campos JSON/JSONB;
- é adequado para logs e payloads brutos;
- permite evolução futura para consultas mais complexas;
- é amplamente usado em aplicações SaaS.

---

## Cache e infraestrutura auxiliar

## Tecnologia escolhida

```txt
Redis
```

## Função no projeto

Redis será incluído na infraestrutura local desde a V1.

Uso inicial previsto:

- suporte futuro a filas;
- suporte futuro a retries;
- cache simples, se necessário;
- base para processamento assíncrono em versões futuras.

## Uso na V1

Na V1, o Redis poderá ter uso mínimo ou ficar disponível como infraestrutura auxiliar.

A presença do Redis desde o início evita mudanças maiores no Docker Compose quando o projeto evoluir para filas, tarefas assíncronas ou controle de retry mais robusto.

## Justificativa

Redis é uma boa escolha para:

- cache;
- filas leves;
- controle de estado temporário;
- rate limiting futuro;
- processamento assíncrono futuro.

---

## Comunicação HTTP externa

## Tecnologia escolhida

```txt
HTTPX
```

## Função no projeto

HTTPX será usado para comunicação HTTP com serviços externos.

Principais usos:

- chamar a Evolution API;
- encaminhar eventos para webhooks do n8n;
- consumir APIs externas futuras, se necessário.

## Justificativa

HTTPX foi escolhido porque:

- suporta chamadas assíncronas;
- combina bem com FastAPI;
- possui API moderna;
- permite timeouts, headers, tratamento de erros e clients reutilizáveis.

---

## Engine de WhatsApp

## Tecnologia escolhida

```txt
Evolution API
```

## Função no projeto

A Evolution API será o provider inicial responsável pela comunicação direta com o WhatsApp.

Ela será usada para:

- criar instâncias;
- conectar instâncias;
- desconectar instâncias;
- consultar status;
- enviar mensagens;
- receber eventos via webhook.

## Estratégia de uso

Na V1, a Evolution API será tratada como serviço interno.

Ela não deve ser exposta diretamente para clientes externos.

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

## Estratégia de versão

A estratégia inicial será usar uma versão anterior e estável da Evolution API, preferencialmente da linha `2.3.x`, para validar a primeira versão do sistema com menor complexidade.

Regra importante:

```txt
Não usar latest sem validar a versão real da imagem.
```

A versão usada deve ser fixada e documentada no projeto.

---

## Automação

## Tecnologia escolhida

```txt
n8n
```

## Função no projeto

O n8n será usado para executar fluxos de automação a partir de eventos recebidos pelo backend.

O backend será responsável por receber eventos da Evolution API, normalizar os dados e encaminhar para o webhook configurado no n8n.

Fluxo correto:

```txt
Evolution API
    ↓
Backend FastAPI
    ↓
n8n
```

## Regra da V1

Na V1, o n8n não deve receber eventos diretamente da Evolution API.

O backend deve ser a camada intermediária responsável por:

- validar;
- salvar;
- normalizar;
- registrar logs;
- encaminhar eventos.

---

## Infraestrutura local

## Tecnologia escolhida

```txt
Docker Compose
```

## Função no projeto

Docker Compose será usado para orquestrar o ambiente local de desenvolvimento.

## Serviços previstos

```txt
backend
postgres
redis
n8n
evolution-api
```

## Justificativa

Docker Compose permite:

- subir todo o ambiente local com um comando;
- padronizar configuração entre máquinas;
- isolar serviços;
- facilitar testes de integração;
- reduzir problemas de ambiente.

---

## Gerenciamento de dependências

## Recomendação

Para a V1, usar um gerenciador moderno de dependências Python.

Opções aceitáveis:

```txt
Poetry
uv
pip + requirements.txt
```

## Recomendação preferencial

```txt
uv
```

## Justificativa

`uv` é uma opção moderna, rápida e adequada para projetos Python atuais.

Ele pode ser usado para:

- criar ambiente virtual;
- instalar dependências;
- congelar dependências;
- executar comandos;
- facilitar builds reproduzíveis.

## Observação

Caso o foco inicial seja simplicidade máxima, o projeto também pode começar com `pip` e `requirements.txt`.

Decisão recomendada para a V1:

```txt
Usar uv.
```

---

## Testes

## Tecnologia escolhida

```txt
pytest
```

## Ferramentas auxiliares

```txt
pytest-asyncio
httpx AsyncClient
```

## Função no projeto

Os testes serão usados para validar principalmente:

- services;
- normalização de webhooks;
- autenticação por API Key;
- provider com mocks;
- endpoints principais;
- health check.

## Justificativa

pytest é uma ferramenta madura, simples e amplamente usada no ecossistema Python.

---

## Configuração de ambiente

## Arquivo principal

```txt
.env
```

## Arquivo de exemplo

```txt
.env.example
```

## Variáveis previstas

```env
APP_NAME=
APP_ENV=
APP_DEBUG=

DATABASE_URL=
REDIS_URL=

EVOLUTION_API_URL=
EVOLUTION_API_KEY=
EVOLUTION_API_VERSION=

N8N_BASE_URL=

WEBHOOK_SECRET=

API_KEY_PREFIX=
```

## Regra

O arquivo `.env` real não deve ser versionado.

O arquivo `.env.example` deve ser versionado para documentar as variáveis necessárias.

---

## Documentação automática da API

FastAPI irá gerar automaticamente:

```txt
/docs
/redoc
/openapi.json
```

Essas rotas serão úteis durante desenvolvimento e validação da V1.

Em produção futura, poderá ser avaliado restringir ou desabilitar acesso público a essas documentações.

---

## Padrão de API

A API pública da V1 seguirá o prefixo:

```txt
/v1
```

Exemplos:

```txt
GET  /health
POST /v1/instances
POST /v1/messages/text
POST /v1/webhooks/evolution
GET  /v1/logs/messages
```

---

## Segurança

## Estratégia da V1

```txt
API Key
```

## Header padrão

```http
X-API-Key: chave_do_cliente
```

## Função

A API Key será usada para proteger os endpoints públicos do backend.

## Regras

- API Keys devem ser armazenadas com hash.
- API Keys não devem ser salvas em texto puro.
- A API Key do cliente não deve ser confundida com o token interno da Evolution API.
- Rotas públicas sensíveis devem exigir API Key.
- Webhook da Evolution API deve usar proteção própria.

---

## Proteção de webhook

## Estratégia inicial

```txt
Segredo compartilhado via header
```

## Header recomendado

```http
X-Webhook-Secret: segredo_interno
```

## Função

Esse segredo será usado para validar chamadas recebidas no endpoint de webhook da Evolution API.

---

## Logs

## Estratégia

A V1 terá logs básicos para desenvolvimento e depuração.

Os logs devem registrar:

- inicialização da aplicação;
- chamadas relevantes ao provider;
- criação de instâncias;
- conexão/desconexão;
- envio de mensagens;
- recebimento de webhooks;
- encaminhamento para n8n;
- erros de integração;
- erros inesperados.

## Cuidados

Os logs não devem expor desnecessariamente:

- API Keys;
- tokens internos;
- dados sensíveis completos;
- segredos de webhook.

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
uv
```

---

## Tecnologias fora da V1

As seguintes tecnologias ou recursos não fazem parte da V1:

```txt
SQLModel
Django
Flask
Celery obrigatório
RabbitMQ obrigatório
Kafka
Kubernetes
Terraform
OAuth
JWT para usuários finais
Painel frontend
Next.js
React
Sistema de cobrança
Gateway de pagamento
CRM
IA/chatbot
```

Essas tecnologias poderão ser avaliadas futuramente, caso o projeto evolua para um produto mais completo.

---

## Decisões técnicas registradas

## DT-001 — FastAPI como backend

### Decisão

Usar FastAPI como framework principal do backend.

### Justificativa

FastAPI é adequado para APIs REST modernas, possui boa performance e integração direta com Pydantic.

---

## DT-002 — SQLAlchemy puro como ORM

### Decisão

Usar SQLAlchemy puro para modelagem e persistência.

### Justificativa

Permite maior controle, flexibilidade e separação clara entre banco e API.

---

## DT-003 — Pydantic para schemas

### Decisão

Usar Pydantic para validação e serialização de dados.

### Justificativa

É o padrão natural em projetos FastAPI e permite definir contratos claros para entrada e saída da API.

---

## DT-004 — Alembic para migrations

### Decisão

Usar Alembic para versionamento do schema do banco.

### Justificativa

É a ferramenta padrão para migrations em projetos com SQLAlchemy.

---

## DT-005 — PostgreSQL como banco principal

### Decisão

Usar PostgreSQL como banco relacional da V1.

### Justificativa

É robusto, confiável e adequado para armazenar entidades relacionais e payloads JSON.

---

## DT-006 — Redis como infraestrutura auxiliar

### Decisão

Incluir Redis desde a V1.

### Justificativa

Prepara o projeto para cache, filas, retries e processamento assíncrono futuro.

---

## DT-007 — HTTPX para chamadas externas

### Decisão

Usar HTTPX para comunicação com Evolution API e n8n.

### Justificativa

HTTPX suporta chamadas assíncronas e combina bem com FastAPI.

---

## DT-008 — Evolution API como provider inicial

### Decisão

Usar Evolution API como engine inicial de WhatsApp.

### Justificativa

Permite validar rapidamente criação de instâncias, conexão, envio e recebimento de mensagens.

---

## DT-009 — n8n para automação

### Decisão

Usar n8n como ferramenta de automação na V1.

### Justificativa

Permite acionar fluxos a partir de eventos recebidos no WhatsApp sem implementar motor próprio de automação.

---

## DT-010 — Docker Compose para desenvolvimento local

### Decisão

Usar Docker Compose para orquestrar o ambiente local.

### Justificativa

Facilita a execução integrada de backend, banco, Redis, n8n e Evolution API.

---

## DT-011 — uv como gerenciador Python

### Decisão

Usar `uv` como gerenciador de dependências Python na V1.

### Justificativa

É rápido, moderno e adequado para projetos Python atuais.

---

## Pendências de decisão

Antes da implementação, ainda devem ser confirmados:

```txt
1. Versão exata da Evolution API a ser fixada.
2. Porta local de cada serviço no Docker Compose.
3. Se Redis será apenas provisionado ou usado já em algum fluxo da V1.
4. Nome final do projeto/pacote Python.
5. Padrão de versionamento interno do projeto.
```

---

## Resumo

A V1 do projeto utilizará uma stack baseada em **Python, FastAPI, SQLAlchemy puro, Pydantic, Alembic, PostgreSQL, Redis, HTTPX, Evolution API, n8n e Docker Compose**.

Essa stack permite construir uma API própria de mensageria para WhatsApp com boa separação arquitetural, persistência confiável, integração com automações e possibilidade de evolução futura.

O foco da V1 é validar o núcleo técnico do sistema sem adicionar complexidade desnecessária de painel, cobrança, CRM, chatbot ou infraestrutura avançada.