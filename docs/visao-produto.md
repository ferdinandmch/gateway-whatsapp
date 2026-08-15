# 01 — Visão do Produto

## Nome provisório

**Z-API Própria / Gateway WhatsApp**

---

## Descrição geral

O projeto consiste no desenvolvimento de um backend próprio em Python, utilizando FastAPI, com o objetivo de atuar como uma camada intermediária entre sistemas externos, fluxos de automação no n8n e uma engine de comunicação com WhatsApp.

Na primeira versão, a engine utilizada será a **Evolution API**, que ficará responsável pela comunicação direta com o WhatsApp, enquanto o backend próprio ficará responsável por organizar, proteger, padronizar e registrar as operações realizadas.

O sistema será inspirado no modelo de APIs de mensageria como a Z-API, mas com foco inicial em validação técnica, controle próprio da arquitetura e possibilidade de evolução futura.

---

## Problema

Soluções prontas de integração com WhatsApp geralmente apresentam algumas limitações, como:

- custo recorrente elevado;
- dependência de plataformas fechadas;
- baixa flexibilidade para customização;
- dificuldade de integração com fluxos próprios;
- pouca transparência sobre logs, falhas e eventos;
- dependência direta de serviços externos para operações essenciais.

Além disso, ao integrar automações com WhatsApp, é comum que o fluxo fique acoplado diretamente à ferramenta de mensageria utilizada. Isso dificulta manutenção, migração futura e controle sobre regras de negócio, segurança, logs e webhooks.

---

## Objetivo do projeto

Construir um backend próprio de mensageria para WhatsApp, capaz de:

- criar e gerenciar instâncias de WhatsApp;
- conectar e desconectar instâncias;
- enviar mensagens em diferentes formatos;
- receber eventos via webhook;
- normalizar dados recebidos;
- encaminhar eventos para o n8n;
- registrar mensagens, eventos e erros;
- proteger rotas por API Key;
- manter a Evolution API isolada como provider interno.

O objetivo principal da V1 é validar a viabilidade técnica do gateway, criando uma base funcional e extensível para futuras versões.

---

## Proposta de solução

A solução será composta por um backend em Python com FastAPI, responsável por expor uma API própria para clientes externos e automações.

A comunicação direta com o WhatsApp será realizada pela Evolution API, mas essa dependência será encapsulada em uma camada chamada **Provider**.

Dessa forma, o backend não ficará acoplado diretamente à Evolution API nas regras principais do sistema.

Fluxo geral:

```txt
Cliente externo / n8n
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

Essa abordagem permite que o sistema comece com a Evolution API, mas mantenha a possibilidade de migração futura para outra versão, outro provider ou outra engine de mensageria.

---

## Público-alvo inicial

A primeira versão do projeto é voltada para:

- desenvolvedores que desejam integrar WhatsApp com sistemas próprios;
- pequenos negócios que precisam automatizar mensagens;
- projetos internos que usam n8n para automações;
- usuários técnicos que desejam uma alternativa auto-hospedada;
- futuras soluções SaaS baseadas em mensageria.

Na V1, o foco não será ainda em usuários finais não técnicos, pois não haverá painel administrativo completo.

---

## Escopo da primeira versão

A V1 será uma prova de conceito funcional, focada no núcleo técnico do sistema.

Funcionalidades principais previstas:

- base do backend e infraestrutura local;
- integração inicial com Evolution API;
- persistência em PostgreSQL;
- gestão de instâncias WhatsApp;
- envio de mensagens de texto e mídia;
- recebimento de webhooks;
- encaminhamento de eventos para n8n;
- autenticação por API Key;
- registro básico de logs.

---

## Fora do escopo inicial

A V1 não terá:

- painel administrativo;
- sistema de cobrança;
- planos de assinatura;
- dashboard visual;
- CRM;
- atendimento humano;
- chatbot com IA;
- campanhas de disparo em massa;
- multi-provider implementado;
- aplicativo mobile;
- gestão avançada de usuários.

Esses recursos poderão ser considerados em versões futuras, após a validação do núcleo técnico.

---

## Diferencial do projeto

O diferencial do projeto não está apenas em chamar a Evolution API, mas em construir uma camada própria de controle.

O backend será responsável por:

- padronizar os contratos da API;
- proteger os acessos externos;
- registrar histórico de eventos;
- evitar exposição direta da Evolution API;
- controlar clientes e instâncias;
- normalizar webhooks;
- encaminhar eventos para automações;
- permitir evolução futura da arquitetura.

Assim, a Evolution API será tratada como um motor interno, enquanto o backend próprio será o produto principal.

---

## Estratégia técnica inicial

A estratégia inicial será utilizar a **Opção A**, ou seja, uma versão anterior e estável da Evolution API, preferencialmente da linha `2.3.x`, com o objetivo de validar a primeira versão do sistema com menor complexidade.

A arquitetura, porém, será planejada para não depender rigidamente dessa versão.

A V1 utilizará:

- Python;
- FastAPI;
- PostgreSQL;
- Redis;
- Docker Compose;
- Evolution API;
- n8n;
- HTTPX;
- Pydantic;
- SQLAlchemy ou SQLModel;
- Alembic.

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

Essas specs serão usadas como base para documentação, planejamento e implementação com Spec Kit.

---

## Resultado esperado da V1

Ao final da V1, espera-se que o sistema consiga:

1. subir localmente com Docker Compose;
2. expor uma API FastAPI funcional;
3. comunicar-se com a Evolution API;
4. criar e conectar uma instância de WhatsApp;
5. enviar mensagens de texto e mídia;
6. receber eventos via webhook;
7. salvar mensagens, eventos e erros no banco;
8. encaminhar eventos normalizados para o n8n;
9. proteger endpoints com API Key.

---

## Critério de sucesso

A V1 será considerada bem-sucedida se for possível executar o seguinte fluxo completo:

```txt
1. Subir backend, banco, Redis, n8n e Evolution API.
2. Criar uma instância pelo backend.
3. Conectar a instância ao WhatsApp.
4. Enviar uma mensagem pelo backend.
5. Receber uma mensagem no WhatsApp.
6. Capturar o evento via webhook.
7. Salvar o evento no PostgreSQL.
8. Encaminhar o evento para o n8n.
9. Registrar logs de sucesso ou falha.
```

Se esse fluxo funcionar, o projeto estará tecnicamente validado para evoluir para versões mais completas.

---

## Visão futura

Após a validação da V1, o projeto poderá evoluir para:

- painel administrativo;
- dashboard de instâncias;
- histórico visual de mensagens;
- gestão de clientes;
- múltiplos providers;
- sistema de cobrança;
- planos de assinatura;
- integração com IA;
- chatbot;
- CRM;
- atendimento humano;
- filas de mensagens;
- deploy em ambiente de produção;
- modelo SaaS.

Essas evoluções não fazem parte da V1, mas a arquitetura deve considerar sua possibilidade futura.

---

## Resumo

O projeto propõe a criação de uma API própria de mensageria para WhatsApp, utilizando FastAPI como backend principal e Evolution API como provider inicial.

A primeira versão terá foco em validação técnica, integração com n8n, envio e recebimento de mensagens, webhooks, persistência, logs e segurança básica por API Key.

O objetivo é construir uma base sólida, organizada e extensível, evitando acoplamento direto com a Evolution API e permitindo evolução futura para um produto mais completo.