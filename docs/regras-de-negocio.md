# 05 — Regras de Negócio

## Objetivo do documento

Este documento define as regras de negócio iniciais da V1 do projeto **Z-API Própria / Gateway WhatsApp**.

As regras aqui descritas devem orientar a implementação das specs, services, validações, persistência, webhooks, logs e integração com n8n.

O objetivo é evitar ambiguidades durante o desenvolvimento e garantir que o sistema mantenha comportamento consistente.

---

## Visão geral

A V1 do projeto será uma API própria de mensageria para WhatsApp, construída com FastAPI e integrada à Evolution API como provider inicial.

O backend próprio será responsável por:

- autenticar clientes;
- gerenciar instâncias;
- enviar mensagens;
- receber webhooks;
- normalizar eventos;
- salvar registros no banco;
- encaminhar eventos ao n8n;
- registrar erros;
- isolar a Evolution API dos consumidores externos.

A Evolution API será usada como motor interno de comunicação com WhatsApp, mas não deverá ser acessada diretamente pelos clientes externos.

---

# 1. Regras gerais do sistema

## RN-001 — Backend como ponto único de entrada

Clientes externos devem consumir apenas a API do backend próprio.

Fluxo correto:

```txt
Cliente externo
    ↓
Backend FastAPI
    ↓
Evolution API
```

Fluxo proibido na arquitetura da V1:

```txt
Cliente externo
    ↓
Evolution API
```

## Justificativa

Essa regra garante:

- controle de autenticação;
- padronização dos contratos;
- logs próprios;
- persistência dos eventos;
- independência futura de provider;
- possibilidade futura de cobrança;
- integração controlada com n8n.

---

## RN-002 — Evolution API como provider interno

A Evolution API deve ser tratada como um serviço interno de infraestrutura.

Ela será usada para:

- criar instâncias;
- conectar instâncias;
- desconectar instâncias;
- consultar status;
- enviar mensagens;
- emitir eventos via webhook.

O backend deve encapsular essa comunicação por meio do `EvolutionProvider`.

---

## RN-003 — Não acoplar regras centrais ao formato da Evolution API

As regras centrais do backend não devem depender diretamente dos nomes, payloads ou endpoints específicos da Evolution API.

O backend deve converter os dados externos para modelos internos próprios.

Exemplo:

```txt
Payload da Evolution API
    ↓
Normalizer / Mapper
    ↓
Payload interno padronizado
```

---

## RN-004 — Provider abstrato desde a V1

Mesmo que a V1 implemente apenas a Evolution API, o backend deve usar a interface interna `MessagingProvider`.

Isso permite futura migração para:

- outra versão da Evolution API;
- Evolution Go;
- WhatsApp Cloud API;
- outro provider de mensageria;
- implementação própria baseada em outra engine.

---

# 2. Regras de clientes

## RN-005 — Todo cliente deve possuir API Key

Todo cliente autorizado a consumir o backend deve possuir uma API Key.

A API Key será usada para autenticação nas rotas protegidas.

Header padrão:

```http
X-API-Key: chave_do_cliente
```

---

## RN-006 — API Key não deve ser armazenada em texto puro

A API Key deve ser armazenada no banco apenas como hash.

O valor original da chave poderá ser exibido somente no momento da criação, se houver endpoint ou comando administrativo para geração.

Campos esperados em `clients`:

```txt
id
name
api_key_hash
status
created_at
updated_at
```

---

## RN-007 — Cliente pode estar ativo ou inativo

O cliente deve possuir um status.

Status iniciais:

```txt
active
inactive
```

Somente clientes com status `active` podem consumir endpoints protegidos.

---

## RN-008 — Cliente inativo não pode consumir a API

Se um cliente estiver inativo, qualquer tentativa de uso da API deve ser bloqueada.

Resposta recomendada:

```json
{
  "code": "CLIENT_INACTIVE",
  "message": "Cliente inativo.",
  "details": {}
}
```

---

# 3. Regras de instâncias

## RN-009 — Toda instância pertence a um cliente

Uma instância de WhatsApp deve estar obrigatoriamente associada a um cliente.

Relacionamento:

```txt
client 1 ── n instances
```

Ou seja:

- um cliente pode ter várias instâncias;
- uma instância pertence a apenas um cliente.

---

## RN-010 — Instância representa uma sessão de WhatsApp

No contexto da V1, uma instância representa uma sessão de WhatsApp gerenciada pela Evolution API.

Ela pode estar em diferentes estados, como:

```txt
created
connecting
connected
disconnected
error
removed
```

---

## RN-011 — Toda instância deve possuir provider

Toda instância deve indicar qual provider está sendo usado.

Na V1, o valor será:

```txt
evolution
```

Campo esperado:

```txt
provider
```

Essa regra prepara o sistema para múltiplos providers no futuro.

---

## RN-012 — Toda instância deve armazenar o identificador no provider

Além do identificador interno do backend, a instância deve armazenar o nome ou identificador usado pela Evolution API.

Campo recomendado:

```txt
provider_instance_name
```

Isso evita depender apenas do ID interno do backend.

---

## RN-013 — O cliente não deve definir diretamente identificadores sensíveis do provider

O backend deve controlar como o nome da instância será criado no provider.

Exemplo recomendado:

```txt
client_slug + "_" + instance_slug
```

Ou:

```txt
inst_<uuid_curto>
```

A definição exata poderá ser feita na spec de gestão de instâncias.

---

## RN-014 — Uma instância deve ser salva no banco

Toda instância criada pelo backend deve ser registrada no PostgreSQL.

Mesmo que a criação no provider falhe, o sistema deve registrar o erro quando aplicável.

---

## RN-015 — Criação de instância deve sincronizar backend e provider

Ao criar uma instância, o backend deve:

1. validar o cliente;
2. criar o registro interno;
3. chamar o provider;
4. salvar o identificador do provider;
5. atualizar o status da instância;
6. registrar erro em caso de falha.

---

## RN-016 — Instância deve ter status atualizado

O status da instância deve ser atualizado com base nas ações realizadas e nos retornos do provider.

Exemplos:

```txt
created
connecting
connected
disconnected
error
```

---

## RN-017 — Não enviar mensagem por instância inexistente

Se a instância informada não existir, o backend deve bloquear o envio.

Resposta recomendada:

```json
{
  "code": "INSTANCE_NOT_FOUND",
  "message": "Instância não encontrada.",
  "details": {}
}
```

---

## RN-018 — Não enviar mensagem por instância de outro cliente

Um cliente só pode usar instâncias pertencentes a ele.

Se a instância existir, mas pertencer a outro cliente, o backend deve negar acesso.

Resposta recomendada:

```json
{
  "code": "INSTANCE_NOT_FOUND",
  "message": "Instância não encontrada.",
  "details": {}
}
```

Observação: para segurança, é melhor não revelar que a instância existe para outro cliente.

---

## RN-019 — Não enviar mensagem por instância desconectada

Se a instância estiver desconectada, o backend deve impedir ou registrar falha no envio.

Resposta recomendada:

```json
{
  "code": "INSTANCE_DISCONNECTED",
  "message": "A instância não está conectada.",
  "details": {}
}
```

---

## RN-020 — Remoção de instância depende de suporte do provider

A remoção de uma instância deve respeitar o que a Evolution API suportar.

Se o provider não suportar remoção total, o backend pode marcar a instância como:

```txt
removed
```

Ou:

```txt
inactive
```

A decisão detalhada ficará na spec de gestão de instâncias.

---

# 4. Regras de mensagens

## RN-021 — Toda mensagem enviada deve ser registrada

Toda tentativa de envio de mensagem deve ser registrada no banco, independentemente de sucesso ou falha.

Campos mínimos esperados:

```txt
id
client_id
instance_id
direction
message_type
remote_jid
content
media_url
status
raw_payload
created_at
```

---

## RN-022 — Toda mensagem recebida deve ser registrada quando identificável

Quando um webhook representar uma mensagem recebida, o backend deve registrar a mensagem na tabela `messages`.

Direção esperada:

```txt
inbound
```

---

## RN-023 — Direção da mensagem deve ser explícita

Toda mensagem deve possuir uma direção.

Valores iniciais:

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

## RN-024 — Tipo da mensagem deve ser explícito

Toda mensagem deve possuir um tipo.

Tipos da V1:

```txt
text
image
audio
document
video
```

Tipos futuros podem incluir:

```txt
location
contact
sticker
button
list
carousel
reaction
```

---

## RN-025 — Envio de texto exige conteúdo textual

Para mensagens de texto, o campo `message` ou `content` deve ser obrigatório.

Exemplo:

```json
{
  "instance_id": "inst_123",
  "to": "5586999999999",
  "message": "Olá, tudo bem?"
}
```

---

## RN-026 — Envio de mídia exige URL ou referência de mídia

Na V1, mensagens de mídia devem receber uma URL de mídia ou referência equivalente.

Tipos afetados:

```txt
image
audio
document
video
```

Campo recomendado:

```txt
media_url
```

---

## RN-027 — Número de destino deve ser normalizado

O número de destino deve ser recebido e convertido para formato aceito pelo provider.

Exemplo de entrada:

```txt
86999999999
```

Exemplo normalizado:

```txt
5586999999999
```

A regra exata de normalização deverá ser detalhada na spec de envio de mensagens.

---

## RN-028 — O cliente não chama o provider diretamente

O consumidor externo deve enviar mensagens usando endpoints próprios do backend.

Exemplo:

```http
POST /v1/messages/text
```

E não diretamente endpoints da Evolution API.

---

## RN-029 — Status inicial da mensagem deve ser registrado

Ao iniciar o envio, a mensagem pode ser registrada com status:

```txt
pending
```

Após resposta do provider, pode ser atualizada para:

```txt
sent
failed
```

Status futuros podem incluir:

```txt
delivered
read
```

Caso esses eventos sejam recebidos por webhook.

---

## RN-030 — Falhas de envio devem ser registradas

Se o provider retornar erro ao enviar mensagem, o backend deve:

1. atualizar status da mensagem como `failed`;
2. registrar erro em `error_logs`;
3. armazenar payload relevante da falha;
4. retornar erro padronizado ao cliente, quando aplicável.

---

# 5. Regras de webhooks

## RN-031 — Evolution API deve enviar webhook para o backend

Na V1, a Evolution API deve apontar seus webhooks para o backend próprio.

Fluxo correto:

```txt
Evolution API
    ↓
Backend FastAPI
```

---

## RN-032 — n8n não recebe webhook direto da Evolution API

Na V1, o n8n não deve receber webhooks diretamente da Evolution API.

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

---

## RN-033 — Todo evento recebido deve ser salvo como payload bruto

Todo webhook recebido da Evolution API deve ser salvo na tabela `webhook_events`, sempre que possível.

Mesmo que o evento ainda não seja reconhecido, o payload bruto deve ser preservado para análise.

Campo esperado:

```txt
raw_payload
```

---

## RN-034 — Webhook deve ser normalizado

Após receber o payload bruto, o backend deve tentar convertê-lo para um formato interno padronizado.

Exemplo de payload normalizado:

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

## RN-035 — Eventos não reconhecidos devem ser registrados

Se o backend receber um evento desconhecido, ele não deve quebrar o fluxo geral.

O sistema deve:

1. salvar o payload bruto;
2. classificar como evento desconhecido, quando possível;
3. registrar log para depuração;
4. evitar falha geral da aplicação.

Tipo sugerido:

```txt
unknown
```

---

## RN-036 — Webhook deve identificar a instância relacionada

O backend deve tentar identificar a instância relacionada ao evento.

A identificação poderá ocorrer por:

- nome da instância no provider;
- identificador informado no payload;
- rota dedicada;
- metadados enviados pela Evolution API.

A regra exata será definida na spec de webhooks, conforme o formato real da Evolution API usado na versão escolhida.

---

## RN-037 — Webhook deve possuir proteção própria

A rota de webhook da Evolution API deve exigir algum mecanismo de proteção.

Na V1, a recomendação é segredo compartilhado via header:

```http
X-Webhook-Secret: segredo_interno
```

---

## RN-038 — Falha no processamento do webhook deve ser registrada

Se o webhook for recebido, mas não puder ser processado corretamente, o backend deve registrar a falha em `error_logs`.

---

# 6. Regras de encaminhamento para n8n

## RN-039 — Eventos normalizados podem ser encaminhados ao n8n

Após salvar e normalizar um evento, o backend poderá encaminhá-lo para o webhook do n8n configurado.

---

## RN-040 — Webhook do n8n será preferencialmente por instância

Decisão recomendada para a V1:

```txt
n8n_webhook_url por instância
```

Motivos:

- permite fluxos diferentes por número;
- facilita testes;
- reduz ambiguidade;
- aproxima o sistema de uso real.

---

## RN-041 — Falha no n8n não deve apagar o evento recebido

Se o encaminhamento para o n8n falhar, o evento original deve permanecer salvo no banco.

O sistema deve registrar:

```txt
forwarded_to_n8n = false
```

E, se aplicável, registrar erro em `error_logs`.

---

## RN-042 — Retorno do n8n pode ser armazenado

Quando o n8n responder à chamada, o backend pode armazenar:

- status HTTP;
- corpo da resposta;
- horário do encaminhamento;
- indicação de sucesso/falha.

Esses dados serão úteis para depuração.

---

## RN-043 — Retry simples ou marcação de falha

Na V1, o backend pode optar por:

```txt
- realizar um retry simples;
- ou apenas marcar a falha para análise posterior.
```

A decisão final será detalhada na spec de encaminhamento para n8n.

---

# 7. Regras de logs e erros

## RN-044 — Erros relevantes devem ser registrados

Erros relevantes devem ser salvos na tabela `error_logs`.

Exemplos:

- falha ao chamar Evolution API;
- falha ao criar instância;
- falha ao conectar instância;
- falha ao enviar mensagem;
- falha ao processar webhook;
- falha ao encaminhar para n8n;
- erro inesperado.

---

## RN-045 — Logs não devem expor segredos

Logs não devem expor:

- API Keys;
- tokens da Evolution API;
- segredos de webhook;
- senhas;
- credenciais internas.

Quando necessário, valores sensíveis devem ser mascarados.

Exemplo:

```txt
zapi_************abcd
```

---

## RN-046 — Payload bruto pode ser armazenado com cautela

A V1 poderá armazenar payloads brutos de mensagens e webhooks para depuração.

Porém, deve-se evitar armazenar dados sensíveis desnecessários.

Essa regra poderá ser refinada em versões futuras com política de retenção de dados.

---

## RN-047 — Respostas de erro devem ser padronizadas

A API deve retornar erros em formato padronizado.

Formato recomendado:

```json
{
  "code": "ERROR_CODE",
  "message": "Mensagem legível do erro.",
  "details": {}
}
```

Exemplos de códigos:

```txt
UNAUTHORIZED
CLIENT_INACTIVE
INSTANCE_NOT_FOUND
INSTANCE_DISCONNECTED
VALIDATION_ERROR
PROVIDER_ERROR
WEBHOOK_PROCESSING_ERROR
N8N_FORWARDING_ERROR
INTERNAL_ERROR
```

---

# 8. Regras de segurança

## RN-048 — Rotas públicas sensíveis devem exigir API Key

As seguintes rotas devem exigir API Key:

```txt
/v1/instances/*
/v1/messages/*
/v1/logs/*
```

---

## RN-049 — Health check não exige API Key

O endpoint de health check pode permanecer público para facilitar verificação local.

Endpoint:

```http
GET /health
```

---

## RN-050 — Webhook da Evolution API não usa API Key do cliente

A rota de webhook da Evolution API deve usar proteção própria, separada da API Key dos clientes.

Motivo:

- a chamada vem da Evolution API;
- não representa um cliente externo consumindo a API;
- precisa de mecanismo próprio de validação.

---

## RN-051 — Token da Evolution API é interno

O token da Evolution API deve ser usado apenas pelo backend.

Ele não deve ser exposto:

- nas respostas da API;
- nos logs;
- no n8n;
- para clientes externos.

---

## RN-052 — Segredos devem vir de variáveis de ambiente

Segredos e credenciais devem ser configurados via `.env`.

Exemplos:

```env
EVOLUTION_API_KEY=
WEBHOOK_SECRET=
DATABASE_URL=
REDIS_URL=
```

---

# 9. Regras de versionamento da API

## RN-053 — API pública deve usar prefixo `/v1`

Todos os endpoints públicos da V1 devem seguir o prefixo:

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

---

## RN-054 — Mudanças incompatíveis devem ser evitadas dentro da V1

Após definidos os contratos principais da V1, mudanças incompatíveis devem ser evitadas.

Se necessário, versões futuras poderão usar:

```txt
/v2
```

---

# 10. Regras fora do escopo da V1

## RN-055 — Não implementar painel administrativo na V1

A V1 será focada em backend e API.

Não faz parte da V1:

- painel web;
- dashboard;
- telas de login;
- visualização de QR Code em frontend próprio;
- gestão visual de clientes.

---

## RN-056 — Não implementar cobrança na V1

A V1 não terá:

- planos;
- assinaturas;
- cobrança recorrente;
- integração com gateway de pagamento;
- limite por plano.

---

## RN-057 — Não implementar chatbot com IA na V1

A V1 não terá chatbot com IA embutido.

Automatizações simples poderão ser feitas pelo n8n, mas a API não terá módulo próprio de IA nesta versão.

---

## RN-058 — Não implementar campanhas ou disparo em massa na V1

A V1 não terá módulo de campanhas, listas de disparo ou envio em massa.

O envio será feito por chamadas individuais aos endpoints de mensagem.

---

## RN-059 — Não implementar CRM ou atendimento humano na V1

A V1 não terá:

- caixa de entrada;
- painel de atendimento;
- agentes humanos;
- CRM;
- funil de vendas;
- histórico visual de conversas.

---

## RN-060 — Não implementar multi-provider real na V1

A V1 deve estar preparada arquiteturalmente para múltiplos providers, mas implementará apenas:

```txt
EvolutionProvider
```

---

## Critério geral de conformidade

Uma implementação estará alinhada a este documento se:

- clientes externos acessarem apenas o backend;
- Evolution API estiver encapsulada no provider;
- instâncias pertencerem a clientes;
- mensagens enviadas e recebidas forem registradas;
- webhooks forem salvos e normalizados;
- eventos puderem ser encaminhados ao n8n;
- erros relevantes forem registrados;
- API Keys forem usadas para rotas protegidas;
- segredos não forem expostos;
- funcionalidades fora da V1 não forem implementadas antecipadamente.

---

## Resumo

As regras de negócio da V1 definem um sistema enxuto, controlado e tecnicamente validável.

O backend será a camada central do projeto, responsável por autenticação, instâncias, mensagens, webhooks, logs, persistência e integração com n8n.

A Evolution API será usada apenas como provider interno, e o n8n será acionado somente após o backend receber, salvar e normalizar os eventos.

A V1 não busca entregar um SaaS completo, mas validar o núcleo funcional necessário para evolução futura.