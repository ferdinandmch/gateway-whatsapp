# 03 — Arquitetura do Backend

## Objetivo do documento

Este documento define a arquitetura inicial do backend da V1 do projeto **Z-API Própria / Gateway WhatsApp**.

O objetivo é estabelecer uma organização clara para o código, separando responsabilidades entre rotas, regras de aplicação, persistência, providers externos, segurança, webhooks, logs e configurações de infraestrutura.

A arquitetura deve permitir que o sistema comece utilizando a **Evolution API** como provider inicial, mas sem ficar rigidamente acoplado a ela.

---

## Visão geral da arquitetura

O backend será desenvolvido em **Python** utilizando **FastAPI**.

Ele funcionará como uma camada intermediária entre consumidores externos, automações no n8n e a Evolution API.

A Evolution API será tratada como um serviço interno de mensageria, responsável pela comunicação direta com o WhatsApp.

O backend próprio será responsável por:

- expor uma API pública controlada;
- autenticar clientes por API Key;
- gerenciar clientes e instâncias;
- enviar mensagens por meio de um provider interno;
- receber webhooks da Evolution API;
- normalizar eventos recebidos;
- persistir mensagens, eventos e erros;
- encaminhar eventos para o n8n;
- isolar a Evolution API dos consumidores externos;
- permitir troca futura de provider.

---

## Fluxo geral do sistema

```txt
Cliente externo / Sistema / n8n
        ↓
Backend FastAPI
        ↓
Camada de aplicação
        ↓
MessagingProvider
        ↓
EvolutionProvider
        ↓
Evolution API
        ↓
WhatsApp
```

Para eventos recebidos:

```txt
WhatsApp
        ↓
Evolution API
        ↓
Webhook para Backend FastAPI
        ↓
Validação do evento
        ↓
Normalização do payload
        ↓
Persistência no PostgreSQL
        ↓
Encaminhamento para n8n
```

---

## Princípio arquitetural principal

O backend não deve depender diretamente da Evolution API nas rotas públicas ou nas regras centrais do sistema.

A comunicação com a Evolution API deve ficar isolada em uma camada de provider.

Forma incorreta:

```txt
Route
  ↓
Chamada direta para endpoint da Evolution API
```

Forma correta:

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

Esse princípio reduz acoplamento e permite que futuramente o sistema seja migrado para outra versão da Evolution API ou para outro provider de mensageria.

---

## Camadas do backend

A arquitetura inicial será organizada em camadas:

```txt
API Layer
Application / Service Layer
Provider Layer
Database Layer
Core Layer
```

---

# 1. API Layer

## Responsabilidade

A API Layer é responsável por expor os endpoints HTTP do backend.

Ela deve receber requisições, validar entradas com schemas, chamar os serviços internos e devolver respostas padronizadas.

## O que pertence a esta camada

- rotas FastAPI;
- validação inicial de payloads;
- dependências de autenticação;
- definição de status codes;
- respostas HTTP;
- agrupamento de endpoints por domínio.

## O que não deve pertencer a esta camada

- regras de negócio complexas;
- chamadas diretas para Evolution API;
- lógica de persistência detalhada;
- transformação complexa de payloads;
- decisões de provider.

## Exemplos de arquivos

```txt
app/api/v1/instances_routes.py
app/api/v1/messages_routes.py
app/api/v1/webhooks_routes.py
app/api/v1/logs_routes.py
```

---

# 2. Application / Service Layer

## Responsabilidade

A Service Layer é responsável pelas regras de aplicação do sistema.

Ela coordena as operações entre banco de dados, providers externos, regras de negócio e logs.

## O que pertence a esta camada

- criação de instâncias;
- envio de mensagens;
- processamento de webhooks;
- encaminhamento para n8n;
- controle de status;
- registro de logs;
- orquestração entre banco e provider.

## O que não deve pertencer a esta camada

- detalhes de endpoints HTTP;
- detalhes internos da Evolution API;
- consultas SQL espalhadas;
- acesso direto a variáveis de ambiente;
- validações que pertencem aos schemas de entrada.

## Exemplos de serviços

```txt
InstanceService
MessageService
WebhookService
N8nForwardingService
ClientService
LogService
```

---

# 3. Provider Layer

## Responsabilidade

A Provider Layer isola a comunicação com serviços externos de mensageria.

Na V1, será implementado apenas o provider da Evolution API.

## Interface principal

A interface interna planejada será chamada:

```txt
MessagingProvider
```

Ela define os métodos que qualquer provider de mensageria deve implementar.

## Provider inicial

```txt
EvolutionProvider
```

## Objetivo da abstração

O objetivo é permitir que o restante do sistema use operações genéricas, como:

- criar instância;
- conectar instância;
- desconectar instância;
- consultar status;
- enviar texto;
- enviar mídia.

Sem depender diretamente dos nomes, payloads e endpoints específicos da Evolution API.

## Exemplo conceitual

```python
from abc import ABC, abstractmethod


class MessagingProvider(ABC):
    @abstractmethod
    async def create_instance(self, instance_name: str):
        pass

    @abstractmethod
    async def connect_instance(self, instance_name: str):
        pass

    @abstractmethod
    async def disconnect_instance(self, instance_name: str):
        pass

    @abstractmethod
    async def get_instance_status(self, instance_name: str):
        pass

    @abstractmethod
    async def send_text(self, instance_name: str, to: str, message: str):
        pass

    @abstractmethod
    async def send_media(
        self,
        instance_name: str,
        to: str,
        media_url: str,
        media_type: str,
        caption: str | None = None
    ):
        pass
```

## Arquivos previstos

```txt
app/providers/base.py
app/providers/evolution/client.py
app/providers/evolution/provider.py
app/providers/evolution/schemas.py
app/providers/evolution/mapper.py
```

---

# 4. Database Layer

## Responsabilidade

A Database Layer é responsável pela comunicação com o PostgreSQL.

Ela deve concentrar modelos, sessões, migrations e repositórios quando necessário.

## O que pertence a esta camada

- configuração de conexão;
- modelos ORM;
- migrations com Alembic;
- repositórios;
- queries;
- persistência de entidades.

## Entidades principais da V1

```txt
clients
instances
messages
webhook_events
error_logs
```

## Decisão oficial da V1

Na V1, o projeto utilizará:

```txt
SQLAlchemy puro + Pydantic + Alembic
```

## Função de cada ferramenta

### SQLAlchemy

Será usado para:

- definir modelos ORM;
- mapear tabelas do PostgreSQL para classes Python;
- criar relacionamentos entre entidades;
- executar consultas;
- controlar sessões e transações;
- persistir dados no banco.

### Pydantic

Será usado para:

- validar payloads de entrada;
- definir schemas de resposta;
- serializar dados para JSON;
- documentar contratos no Swagger/OpenAPI do FastAPI;
- representar payloads internos, webhooks normalizados e respostas da API.

### Alembic

Será usado para:

- versionar alterações no banco;
- criar migrations;
- aplicar mudanças estruturais nas tabelas;
- manter histórico da evolução do schema do banco.

## Decisão sobre SQLModel

O projeto **não utilizará SQLModel na V1**.

## Justificativa

A escolha por SQLAlchemy puro + Pydantic + Alembic favorece:

- separação clara entre modelos de banco e schemas da API;
- maior controle sobre dados sensíveis, como API Keys;
- melhor organização para uma arquitetura modular;
- maior flexibilidade para webhooks, logs e integrações externas;
- melhor controle das migrations;
- melhor preparação para evolução futura do projeto.

---

# 5. Core Layer

## Responsabilidade

A Core Layer concentra configurações e recursos transversais do sistema.

## O que pertence a esta camada

- carregamento de variáveis de ambiente;
- configurações globais;
- segurança;
- exceptions customizadas;
- logging;
- utilitários comuns;
- constantes da aplicação.

## Arquivos previstos

```txt
app/core/config.py
app/core/security.py
app/core/exceptions.py
app/core/logging.py
```

---

## Estrutura inicial de pastas

A estrutura inicial recomendada para o backend é:

```txt
backend/
├── app/
│   ├── main.py
│   ├── core/
│   │   ├── config.py
│   │   ├── security.py
│   │   ├── exceptions.py
│   │   └── logging.py
│   ├── api/
│   │   └── v1/
│   │       ├── router.py
│   │       ├── instances_routes.py
│   │       ├── messages_routes.py
│   │       ├── webhooks_routes.py
│   │       └── logs_routes.py
│   ├── modules/
│   │   ├── clients/
│   │   │   ├── models.py
│   │   │   ├── schemas.py
│   │   │   ├── repository.py
│   │   │   └── service.py
│   │   ├── instances/
│   │   │   ├── models.py
│   │   │   ├── schemas.py
│   │   │   ├── repository.py
│   │   │   └── service.py
│   │   ├── messages/
│   │   │   ├── models.py
│   │   │   ├── schemas.py
│   │   │   ├── repository.py
│   │   │   └── service.py
│   │   ├── webhooks/
│   │   │   ├── models.py
│   │   │   ├── schemas.py
│   │   │   ├── repository.py
│   │   │   ├── normalizer.py
│   │   │   └── service.py
│   │   ├── logs/
│   │   │   ├── models.py
│   │   │   ├── schemas.py
│   │   │   ├── repository.py
│   │   │   └── service.py
│   │   └── n8n/
│   │       ├── schemas.py
│   │       ├── client.py
│   │       └── service.py
│   ├── providers/
│   │   ├── base.py
│   │   └── evolution/
│   │       ├── client.py
│   │       ├── provider.py
│   │       ├── schemas.py
│   │       └── mapper.py
│   └── database/
│       ├── session.py
│       ├── base.py
│       └── migrations/
├── tests/
├── Dockerfile
├── pyproject.toml
├── alembic.ini
├── .env.example
└── README.md
```

---

## Organização por módulos

O projeto será organizado por domínio funcional dentro de `app/modules`.

Cada módulo poderá conter:

```txt
models.py
schemas.py
repository.py
service.py
```

Quando necessário, módulos podem ter arquivos adicionais.

Exemplo para webhooks:

```txt
webhooks/
├── models.py
├── schemas.py
├── repository.py
├── normalizer.py
└── service.py
```

Essa estrutura evita que o projeto fique organizado apenas por tipo técnico e facilita a evolução por funcionalidade.

---

## Módulos iniciais

A V1 terá os seguintes módulos principais:

```txt
clients
instances
messages
webhooks
logs
n8n
```

---

# Módulo clients

## Responsabilidade

Gerenciar clientes consumidores da API.

Na V1, o cliente representa uma entidade autorizada a consumir o backend por meio de API Key.

## Funções principais

- cadastrar cliente inicial;
- armazenar hash da API Key;
- consultar cliente por API Key;
- controlar status ativo/inativo.

---

# Módulo instances

## Responsabilidade

Gerenciar instâncias de WhatsApp.

## Funções principais

- criar instância no backend;
- criar instância no provider;
- conectar instância;
- consultar status;
- desconectar;
- remover;
- atualizar status no banco.

---

# Módulo messages

## Responsabilidade

Gerenciar envio e registro de mensagens.

## Funções principais

- validar payloads de envio;
- enviar texto;
- enviar imagem;
- enviar áudio;
- enviar documento;
- enviar vídeo;
- registrar mensagens enviadas;
- atualizar status quando disponível.

---

# Módulo webhooks

## Responsabilidade

Receber, validar, salvar e normalizar eventos vindos da Evolution API.

## Funções principais

- receber webhook;
- identificar instância;
- salvar payload bruto;
- normalizar evento;
- registrar mensagem recebida;
- registrar erro de processamento;
- acionar encaminhamento para n8n.

---

# Módulo n8n

## Responsabilidade

Encaminhar eventos normalizados para webhooks do n8n.

## Funções principais

- enviar payload normalizado;
- registrar sucesso;
- registrar falha;
- armazenar resposta;
- executar retry simples ou marcar falha.

---

# Módulo logs

## Responsabilidade

Permitir consulta básica de logs da V1.

## Funções principais

- consultar mensagens;
- consultar eventos de webhook;
- consultar erros;
- apoiar depuração do sistema.

---

## Separação entre API pública e Evolution API

A Evolution API não deve ser exposta diretamente para consumidores externos.

Consumidores externos devem interagir somente com o backend próprio.

Correto:

```txt
Cliente externo
    ↓
Backend FastAPI
    ↓
Evolution API
```

Incorreto:

```txt
Cliente externo
    ↓
Evolution API
```

Essa decisão permite:

- maior controle de segurança;
- padronização dos payloads;
- logs próprios;
- independência da versão da Evolution API;
- integração controlada com n8n;
- possibilidade de cobrança futura;
- possibilidade de migração para outro provider.

---

## Comunicação com a Evolution API

A comunicação com a Evolution API será realizada via HTTP usando **HTTPX**.

As configurações deverão ser lidas por variáveis de ambiente.

Variáveis previstas:

```env
EVOLUTION_API_URL=
EVOLUTION_API_KEY=
EVOLUTION_API_VERSION=
```

O backend deve tratar erros da Evolution API e convertê-los para erros internos ou respostas HTTP padronizadas.

---

## Comunicação com o n8n

O backend será responsável por encaminhar eventos normalizados para webhooks do n8n.

O n8n não deve receber eventos diretamente da Evolution API na V1.

Fluxo correto:

```txt
Evolution API
    ↓
Backend FastAPI
    ↓
n8n
```

O webhook do n8n poderá ser configurado por cliente ou por instância, conforme a modelagem da V1.

Decisão inicial recomendada:

```txt
Permitir webhook do n8n por instância.
```

Motivo:

- maior flexibilidade;
- permite fluxos diferentes para números diferentes;
- facilita testes;
- aproxima o modelo de uso real.

---

## Segurança inicial

A V1 terá segurança baseada em API Key.

Clientes externos deverão enviar a chave no header:

```http
X-API-Key: chave_do_cliente
```

O backend validará a chave antes de permitir acesso às rotas protegidas.

As chaves devem ser armazenadas com hash, e não em texto puro.

A chave externa do cliente não deve ser confundida com o token interno usado para comunicação com a Evolution API.

```txt
API Key do cliente:
usada para consumir o backend.

Token da Evolution API:
usado internamente pelo backend para chamar a Evolution API.
```

---

## Proteção do webhook da Evolution API

A rota de webhook da Evolution API deve possuir proteção própria.

Opções possíveis:

```txt
- token em header;
- query parameter secreto;
- segredo compartilhado;
- assinatura HMAC, se viável futuramente.
```

Decisão inicial recomendada para a V1:

```txt
Usar segredo compartilhado simples via header.
```

Exemplo:

```http
X-Webhook-Secret: segredo_interno
```

Essa abordagem é simples para a V1 e pode ser evoluída futuramente.

---

## Tratamento de erros

O backend deve padronizar o tratamento de erros.

Tipos iniciais de erro:

```txt
- erro de validação de payload;
- cliente não autenticado;
- cliente sem permissão;
- instância não encontrada;
- instância desconectada;
- erro ao chamar Evolution API;
- erro ao salvar no banco;
- erro ao encaminhar para n8n;
- erro inesperado.
```

Formato recomendado para respostas de erro:

```json
{
  "code": "INSTANCE_NOT_FOUND",
  "message": "Instância não encontrada.",
  "details": {}
}
```

Os erros relevantes devem ser registrados na tabela `error_logs`.

---

## Logs

A V1 deve possuir logs básicos para depuração.

Devem ser registrados:

- chamadas relevantes ao provider;
- criação de instâncias;
- conexão e desconexão;
- envio de mensagens;
- recebimento de webhooks;
- falhas ao processar eventos;
- falhas ao encaminhar para n8n;
- erros inesperados.

Logs devem ser úteis para desenvolvimento e validação, sem armazenar dados sensíveis desnecessários.

---

## Banco de dados

O banco principal da V1 será PostgreSQL.

Entidades iniciais:

```txt
clients
instances
messages
webhook_events
error_logs
```

A modelagem detalhada será definida no documento:

```txt
06-modelagem-dados.md
```

---

## Redis

O Redis será incluído na infraestrutura local desde a V1.

Uso inicial previsto:

- suporte futuro para filas;
- cache simples, se necessário;
- base para evoluir retries e processamento assíncrono.

Na V1, o Redis pode subir como serviço de infraestrutura mesmo que o uso ainda seja mínimo.

---

## Docker Compose

O ambiente local será executado com Docker Compose.

Serviços previstos:

```txt
backend
postgres
redis
n8n
evolution-api
```

O objetivo é permitir que o sistema completo suba de forma reproduzível em ambiente de desenvolvimento.

---

## Testes

A V1 deve permitir testes básicos, mesmo que a cobertura ainda não seja completa.

Tipos de teste recomendados:

- testes unitários de services;
- testes unitários de normalização de webhook;
- testes do provider com mocks;
- testes de health check;
- testes de validação de API Key.

Ferramentas possíveis:

```txt
pytest
pytest-asyncio
httpx AsyncClient
```

---

## Convenções iniciais

## Nomeação de rotas

As rotas públicas devem seguir o padrão:

```txt
/v1/recurso
```

Exemplos:

```txt
/v1/instances
/v1/messages/text
/v1/webhooks/evolution
/v1/logs/messages
```

## Versionamento da API

A V1 da API será exposta sob o prefixo:

```txt
/v1
```

## Schemas

Schemas de entrada e saída devem ser definidos com Pydantic.

## Configurações

Configurações sensíveis devem ser lidas por variáveis de ambiente.

## Migrations

Alterações de banco devem ser feitas com Alembic.

---

## Decisões arquiteturais da V1

## DA-001 — Backend como camada principal

### Decisão

O backend FastAPI será a API principal do sistema.

### Justificativa

Permite controle próprio sobre segurança, logs, contratos, integração com n8n e evolução futura.

---

## DA-002 — Evolution API como provider interno

### Decisão

A Evolution API será usada como provider inicial, mas não será exposta diretamente aos clientes externos.

### Justificativa

Reduz acoplamento, melhora segurança e permite troca futura de provider.

---

## DA-003 — Provider abstrato

### Decisão

Criar uma interface `MessagingProvider`.

### Justificativa

Permite que outras engines sejam implementadas futuramente sem reescrever toda a aplicação.

---

## DA-004 — n8n atrás do backend

### Decisão

O n8n receberá eventos encaminhados pelo backend, e não diretamente pela Evolution API.

### Justificativa

Permite persistência, normalização, segurança, logs e controle centralizado dos eventos.

---

## DA-005 — API Key na V1

### Decisão

A autenticação inicial será feita por API Key.

### Justificativa

É simples, suficiente para a V1 técnica e adequada para integrações servidor-servidor.

---

## DA-006 — Docker Compose para desenvolvimento

### Decisão

A infraestrutura local será orquestrada com Docker Compose.

### Justificativa

Facilita execução local dos serviços necessários: backend, PostgreSQL, Redis, n8n e Evolution API.

---

## DA-007 — PostgreSQL como banco principal

### Decisão

O PostgreSQL será o banco relacional da V1.

### Justificativa

É robusto, amplamente utilizado e adequado para persistir clientes, instâncias, mensagens, webhooks e logs.

---

## DA-008 — Redis como serviço auxiliar

### Decisão

O Redis será incluído desde a V1 como infraestrutura auxiliar.

### Justificativa

Permite evolução futura para filas, cache, controle de retry e processamento assíncrono.

---

## DA-009 — SQLAlchemy puro + Pydantic + Alembic

### Decisão

Na V1, o projeto utilizará **SQLAlchemy puro** para modelagem e persistência no banco de dados, **Pydantic** para validação e serialização dos contratos da API e **Alembic** para controle de migrations.

### Justificativa

Essa decisão favorece separação clara entre banco e API, maior controle sobre dados sensíveis, melhor organização modular e maior flexibilidade para webhooks, logs e integrações externas.

### Consequência

O projeto não utilizará SQLModel na V1.

---

## Pendências de decisão

As seguintes decisões ainda podem ser confirmadas antes da implementação:

```txt
1. Definir se o webhook do n8n será por cliente, por instância ou ambos.
2. Definir o formato exato do segredo de proteção do webhook da Evolution API.
3. Definir se Redis será usado já na V1 ou apenas deixado disponível.
4. Definir padrão final de resposta de erro da API.
```

Recomendações iniciais:

```txt
1. Webhook do n8n por instância.
2. Header X-Webhook-Secret.
3. Redis disponível desde a V1, com uso mínimo inicialmente.
4. Resposta de erro padronizada com code, message e details.
```

---

## Resumo

A arquitetura do backend será baseada em FastAPI, com separação clara entre rotas, serviços, providers, banco de dados e configurações centrais.

A Evolution API será utilizada como provider inicial, encapsulada por uma camada própria chamada `EvolutionProvider`, que implementará a interface `MessagingProvider`.

O backend será a única API exposta para consumidores externos, garantindo controle sobre segurança, logs, persistência, webhooks e integração com n8n.

Na V1, a persistência será implementada com **SQLAlchemy puro**, os contratos da API serão definidos com **Pydantic** e as migrations serão controladas com **Alembic**.

Essa arquitetura permite validar a V1 sem comprometer a evolução futura do projeto.