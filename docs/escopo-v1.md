# 02 — Escopo da V1

## Objetivo da V1

A V1 tem como objetivo validar a viabilidade técnica de uma API própria de mensageria para WhatsApp, utilizando um backend em Python com FastAPI, a Evolution API como provider inicial, PostgreSQL para persistência, Redis como apoio de infraestrutura e n8n para automação de fluxos.

A primeira versão não busca entregar um produto SaaS completo, mas sim uma base funcional capaz de provar o fluxo principal do sistema:

```txt
Backend próprio
↓
Evolution API
↓
WhatsApp
↓
Webhook recebido
↓
Backend próprio
↓
n8n
```

O foco da V1 é validar conexão, envio, recebimento, persistência, logs, segurança básica e encaminhamento de eventos.

---

## Princípio de escopo

A V1 deve ser simples, funcional e tecnicamente validável.

O projeto deve priorizar:

- funcionamento do fluxo principal;
- clareza arquitetural;
- baixo acoplamento com a Evolution API;
- integração controlada com n8n;
- registro básico de eventos e erros;
- segurança mínima por API Key;
- possibilidade de evolução futura.

A V1 não deve tentar resolver, neste momento, funcionalidades comerciais, painel visual, cobrança, CRM, atendimento humano ou automações avançadas.

---

## Escopo incluído

A V1 será composta pelas seguintes áreas principais:

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

Cada área será tratada posteriormente como spec individual no Spec Kit.

---

# 001 — Base do backend e infraestrutura local

## Objetivo

Criar a fundação técnica do projeto, permitindo que os serviços principais sejam executados localmente com Docker Compose.

## Incluído

- estrutura inicial do projeto FastAPI;
- organização inicial de pastas;
- configuração de variáveis de ambiente;
- arquivo `.env.example`;
- Dockerfile do backend;
- Docker Compose local;
- serviço do backend;
- serviço do PostgreSQL;
- serviço do Redis;
- serviço do n8n;
- serviço da Evolution API;
- endpoint de health check;
- configuração inicial de logs.

## Resultado esperado

Ao final desta parte, deve ser possível subir o ambiente local e acessar um endpoint simples de verificação do backend.

Exemplo:

```http
GET /health
```

Resposta esperada:

```json
{
  "status": "ok"
}
```

## Fora desta parte

- criação de instâncias;
- envio de mensagens;
- recebimento de webhooks;
- autenticação por API Key;
- modelagem completa do banco;
- integração funcional com n8n.

---

# 002 — Provider Evolution API

## Objetivo

Criar a camada interna responsável pela comunicação entre o backend e a Evolution API.

A Evolution API deve ser tratada como provider interno, e não como API diretamente exposta aos consumidores externos do sistema.

## Incluído

- criação da interface `MessagingProvider`;
- criação da implementação `EvolutionProvider`;
- cliente HTTP com HTTPX;
- configuração da URL da Evolution API;
- configuração do token interno da Evolution API;
- método para criar instância no provider;
- método para conectar instância;
- método para desconectar instância;
- método para consultar status da instância;
- método para envio de texto;
- método genérico ou específico para envio de mídia;
- tratamento inicial de erros;
- mapeamento básico das respostas da Evolution API para formatos internos.

## Resultado esperado

Ao final desta parte, o backend deve possuir uma camada interna capaz de chamar a Evolution API sem que as rotas públicas dependam diretamente dos endpoints dela.

Fluxo desejado:

```txt
Rota pública
↓
Service interno
↓
MessagingProvider
↓
EvolutionProvider
↓
Evolution API
```

## Fora desta parte

- painel administrativo;
- multi-provider real;
- implementação de outros providers;
- cobrança;
- regras comerciais;
- integração completa com banco;
- interface visual para QR Code.

---

# 003 — Persistência e modelagem inicial

## Objetivo

Criar a modelagem inicial do banco de dados e permitir persistência básica das principais entidades do sistema.

## Incluído

- configuração do PostgreSQL;
- configuração de conexão do backend com o banco;
- uso de SQLAlchemy ou SQLModel;
- configuração do Alembic;
- criação das migrations iniciais;
- tabela `clients`;
- tabela `instances`;
- tabela `messages`;
- tabela `webhook_events`;
- tabela `error_logs`;
- persistência básica de clientes;
- persistência básica de instâncias;
- persistência básica de mensagens;
- persistência básica de eventos de webhook;
- persistência básica de erros;
- consultas iniciais para logs.

## Entidades iniciais

```txt
clients
instances
messages
webhook_events
error_logs
```

## Resultado esperado

Ao final desta parte, o sistema deve possuir banco estruturado e pronto para registrar clientes, instâncias, mensagens, eventos e erros.

## Fora desta parte

- relatórios avançados;
- dashboard visual;
- analytics;
- billing;
- auditoria completa;
- retenção avançada de dados;
- particionamento de tabelas;
- escalabilidade de banco para alto volume.

---

# 004 — Gestão de instâncias WhatsApp

## Objetivo

Permitir que clientes criem, conectem, consultem e desconectem instâncias de WhatsApp por meio do backend próprio.

## Incluído

- endpoint para criar instância;
- criação correspondente da instância na Evolution API;
- salvamento da instância no banco;
- endpoint para conectar instância;
- retorno de QR Code ou dados de conexão quando disponível;
- endpoint para consultar status da instância;
- endpoint para desconectar/logout da instância;
- endpoint para remover instância, se suportado pela Evolution API;
- atualização de status da instância no banco;
- associação da instância a um cliente.

## Endpoints previstos

```http
POST   /v1/instances
POST   /v1/instances/{instance_id}/connect
GET    /v1/instances/{instance_id}/status
POST   /v1/instances/{instance_id}/disconnect
DELETE /v1/instances/{instance_id}
```

## Resultado esperado

Ao final desta parte, deve ser possível criar uma instância pelo backend, conectá-la ao WhatsApp, consultar seu status e desconectá-la.

## Fora desta parte

- painel visual de QR Code;
- múltiplas sessões por usuário final;
- gestão avançada de dispositivos;
- rotação automática de instâncias;
- balanceamento entre instâncias;
- reconexão inteligente avançada.

---

# 005 — Envio de mensagens

## Objetivo

Permitir o envio de mensagens pelo backend próprio, utilizando a Evolution API como provider interno.

## Incluído

- envio de mensagem de texto;
- envio de imagem;
- envio de áudio;
- envio de documento;
- envio de vídeo;
- validação dos payloads;
- normalização dos dados recebidos pela API;
- chamada ao provider interno;
- registro básico da tentativa de envio;
- registro do status inicial da mensagem;
- armazenamento do payload bruto de resposta, quando necessário.

## Endpoints previstos

```http
POST /v1/messages/text
POST /v1/messages/image
POST /v1/messages/audio
POST /v1/messages/document
POST /v1/messages/video
```

## Tipos de mensagem da V1

```txt
text
image
audio
document
video
```

## Resultado esperado

Ao final desta parte, deve ser possível enviar mensagens de texto e mídia por meio do backend, sem chamar a Evolution API diretamente.

## Fora desta parte

- disparo em massa;
- campanhas;
- agendamento de mensagens;
- templates comerciais;
- botões;
- listas;
- carrossel;
- enquetes;
- mensagens interativas avançadas;
- controle sofisticado de fila;
- limitação de envio por plano.

---

# 006 — Recebimento de webhooks

## Objetivo

Receber eventos enviados pela Evolution API, identificar a instância relacionada, salvar o payload bruto e normalizar os dados para uso interno.

## Incluído

- endpoint de webhook para Evolution API;
- validação básica do evento recebido;
- identificação da instância;
- salvamento do payload bruto;
- normalização do payload;
- classificação do tipo de evento;
- registro de mensagem recebida quando aplicável;
- registro de alterações de status de conexão quando aplicável;
- registro de falhas quando o webhook não puder ser processado.

## Endpoint previsto

```http
POST /v1/webhooks/evolution
```

## Eventos iniciais esperados

- mensagem recebida;
- atualização de status de conexão;
- status de envio, entrega ou leitura, se disponível;
- erro de envio, se disponível.

## Resultado esperado

Ao final desta parte, o backend deve conseguir receber eventos da Evolution API, armazená-los e convertê-los para um formato interno padronizado.

## Fora desta parte

- lógica de chatbot;
- resposta automática;
- processamento semântico de mensagens;
- múltiplos webhooks externos por evento;
- criação automática de fluxos no n8n.

---

# 007 — Encaminhamento para n8n

## Objetivo

Encaminhar eventos normalizados para fluxos do n8n, mantendo o backend como intermediário entre Evolution API e automações.

## Incluído

- configuração de URL de webhook do n8n por cliente ou instância;
- envio do payload normalizado para o n8n;
- registro de sucesso no encaminhamento;
- registro de falha no encaminhamento;
- armazenamento do retorno do n8n, quando aplicável;
- retry simples ou marcação de falha;
- logs básicos de integração.

## Fluxo correto

```txt
Evolution API
↓
Backend FastAPI
↓
Normalização do evento
↓
n8n
```

## Regra principal

Na V1, o n8n não deve receber webhooks diretamente da Evolution API.

O backend deve ser responsável por receber, validar, salvar, normalizar e só então encaminhar o evento ao n8n.

## Resultado esperado

Ao final desta parte, mensagens ou eventos recebidos no WhatsApp devem conseguir acionar fluxos do n8n a partir do backend.

## Fora desta parte

- criação automática de workflows no n8n;
- editor visual de fluxos;
- painel para configurar múltiplas automações;
- roteamento avançado por tipo de evento;
- versionamento de workflows;
- integração profunda com API interna do n8n.

---

# 008 — Segurança com API Key

## Objetivo

Proteger os endpoints públicos do backend e separar o acesso dos clientes externos do token interno usado para comunicação com a Evolution API.

## Incluído

- modelo de cliente com API Key;
- geração inicial de API Key;
- armazenamento da API Key com hash;
- validação da API Key nas rotas protegidas;
- dependência ou middleware de autenticação;
- proteção das rotas de instâncias;
- proteção das rotas de mensagens;
- proteção das rotas de logs;
- separação entre API Key externa e token interno da Evolution API;
- proteção específica do webhook da Evolution API com token, segredo compartilhado ou mecanismo equivalente.

## Header previsto

```http
X-API-Key: chave_do_cliente
```

## Rotas protegidas

```txt
/v1/instances/*
/v1/messages/*
/v1/logs/*
```

## Resultado esperado

Ao final desta parte, somente clientes com API Key válida devem conseguir consumir os endpoints públicos do backend.

## Fora desta parte

- login com usuário e senha;
- painel administrativo;
- OAuth;
- JWT para usuários finais;
- permissões avançadas por papel;
- multiusuário;
- autenticação social;
- recuperação de senha.

---

## Fora do escopo geral da V1

A V1 não incluirá:

- painel administrativo;
- dashboard visual;
- sistema de cobrança;
- planos de assinatura;
- gestão comercial de clientes;
- CRM;
- atendimento humano;
- chatbot com IA;
- campanhas de disparo em massa;
- agendamento de mensagens;
- multi-provider implementado;
- aplicativo mobile;
- frontend público;
- relatórios avançados;
- deploy em produção com alta disponibilidade.

Esses recursos poderão ser planejados em versões futuras após a validação técnica do núcleo.

---

## Critério de conclusão da V1

A V1 será considerada concluída quando o seguinte fluxo completo estiver funcionando:

```txt
1. Subir backend, PostgreSQL, Redis, n8n e Evolution API com Docker Compose.
2. Criar cliente inicial com API Key.
3. Criar instância pelo backend.
4. Criar instância correspondente na Evolution API.
5. Conectar instância ao WhatsApp.
6. Consultar status da instância.
7. Enviar mensagem de texto pelo backend.
8. Enviar mensagem de mídia pelo backend.
9. Receber evento da Evolution API via webhook.
10. Salvar evento bruto no PostgreSQL.
11. Normalizar evento recebido.
12. Registrar mensagem recebida quando aplicável.
13. Encaminhar evento normalizado para o n8n.
14. Registrar sucesso ou falha do encaminhamento.
15. Proteger endpoints públicos com API Key.
```

---

## Critérios de sucesso técnico

A V1 será considerada tecnicamente validada se:

- o ambiente local subir com Docker Compose;
- o backend FastAPI responder corretamente;
- a Evolution API for acessível internamente;
- uma instância puder ser criada e conectada;
- mensagens puderem ser enviadas;
- webhooks puderem ser recebidos;
- eventos puderem ser salvos no banco;
- eventos normalizados puderem ser encaminhados ao n8n;
- endpoints públicos estiverem protegidos por API Key;
- erros principais forem registrados em logs.

---

## Resumo

A V1 do projeto será uma prova de conceito funcional de uma API própria de mensageria para WhatsApp.

O objetivo não é criar um SaaS completo neste momento, mas validar a base técnica do sistema: backend próprio, provider Evolution API, persistência, webhooks, n8n, logs e segurança básica.

Com esse escopo validado, o projeto poderá evoluir posteriormente para painel administrativo, cobrança, múltiplos providers, chatbot, CRM, atendimento humano e modelo SaaS.