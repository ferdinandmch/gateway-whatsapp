# 08 — Fluxos de Webhook

## Objetivo do documento

Este documento define os fluxos de webhook da V1 do projeto **Z-API Própria / Gateway WhatsApp**.

O objetivo é padronizar como o backend deve:

- receber eventos da Evolution API;
- validar a origem do webhook;
- salvar o payload bruto;
- identificar a instância relacionada;
- normalizar o evento;
- registrar mensagens recebidas;
- atualizar status quando aplicável;
- encaminhar eventos normalizados para o n8n;
- registrar sucesso ou falha no processamento.

Na V1, o backend será a camada intermediária obrigatória entre a Evolution API e o n8n.

---

## Regra principal

Na V1, a Evolution API deve enviar webhooks para o backend próprio.

Fluxo correto:

```txt
Evolution API
    ↓
Backend FastAPI
    ↓
n8n
```

Fluxo que deve ser evitado:

```txt
Evolution API
    ↓
n8n
```

O n8n não deve receber eventos diretamente da Evolution API na V1.

---

## Motivo da decisão

O backend precisa ficar no meio do fluxo para garantir:

- validação do webhook recebido;
- persistência do payload bruto;
- identificação da instância;
- identificação do cliente;
- normalização do evento;
- registro de mensagens;
- registro de logs;
- tratamento de erros;
- controle sobre o que é enviado ao n8n;
- possibilidade de retry ou marcação de falha;
- desacoplamento entre Evolution API e n8n.

---

## Visão geral do fluxo

```txt
1. WhatsApp gera evento.
2. Evolution API recebe o evento.
3. Evolution API envia webhook para o backend.
4. Backend valida o segredo do webhook.
5. Backend salva o payload bruto.
6. Backend identifica provider, instância e cliente.
7. Backend classifica o tipo de evento.
8. Backend normaliza o payload.
9. Backend registra mensagem ou status, se aplicável.
10. Backend encaminha evento normalizado para o n8n, se configurado.
11. Backend registra sucesso ou falha.
12. Backend responde à Evolution API.
```

---

## Endpoint de recebimento

```http
POST /v1/webhooks/evolution
```

---

## Proteção do webhook

A rota de webhook da Evolution API deve usar proteção própria.

A estratégia inicial da V1 será segredo compartilhado via header.

```http
X-Webhook-Secret: segredo_interno
```

O valor esperado deve vir de variável de ambiente:

```env
WEBHOOK_SECRET=
```

---

## Validação do segredo

Ao receber uma requisição no endpoint de webhook, o backend deve:

1. ler o header `X-Webhook-Secret`;
2. comparar com o valor configurado em `WEBHOOK_SECRET`;
3. rejeitar a requisição se o valor estiver ausente ou inválido;
4. registrar erro de segurança quando aplicável.

Resposta para segredo inválido:

```http
401 Unauthorized
```

Body recomendado:

```json
{
  "code": "WEBHOOK_UNAUTHORIZED",
  "message": "Webhook não autorizado.",
  "details": {}
}
```

---

## Payload bruto

Todo webhook recebido da Evolution API deve ser salvo como payload bruto sempre que possível.

Campo na tabela `webhook_events`:

```txt
raw_payload
```

Tipo recomendado:

```txt
JSONB
```

Motivo:

- preservar o evento original;
- permitir depuração;
- permitir ajuste posterior dos normalizers;
- evitar perda de informação caso o evento ainda não seja reconhecido.

---

## Estrutura genérica esperada

O formato exato do payload pode variar conforme a versão da Evolution API e o tipo de evento.

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

Como o formato pode variar, a implementação deve ser tolerante a campos ausentes e registrar eventos desconhecidos sem quebrar o fluxo principal.

---

## Identificação da instância

O backend deve tentar identificar a instância relacionada ao evento.

A identificação pode usar:

```txt
provider_instance_name
```

Na V1, a estratégia recomendada é mapear o campo de instância vindo da Evolution API para:

```txt
instances.provider_instance_name
```

Exemplo:

```json
{
  "instance": "inst_abc123"
}
```

Mapeamento:

```txt
payload.instance → instances.provider_instance_name
```

---

## Quando a instância for encontrada

Se a instância for encontrada, o backend deve preencher:

```txt
client_id
instance_id
provider
provider_instance_name
```

No registro de `webhook_events`.

---

## Quando a instância não for encontrada

Se o backend não conseguir identificar a instância, ele ainda deve salvar o evento quando possível.

Nesse caso:

```txt
client_id = null
instance_id = null
provider = evolution
provider_instance_name = valor recebido, se existir
event_type = unknown ou tipo detectado
processing_status = failed ou received
```

Também deve registrar erro em `error_logs`.

Código recomendado:

```txt
INSTANCE_NOT_FOUND_FOR_WEBHOOK
```

---

## Classificação de eventos

O backend deve tentar classificar os eventos recebidos em tipos internos.

Tipos iniciais:

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

## Eventos de mensagem recebida

Evento interno:

```txt
message.received
```

Critérios possíveis:

- payload indica mensagem recebida;
- `fromMe` é `false`;
- existe conteúdo de mensagem;
- existe remetente remoto.

Exemplo de payload bruto:

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

Payload normalizado esperado:

```json
{
  "event_type": "message.received",
  "provider": "evolution",
  "instance_id": "1e1d7d4a-7b8e-4ef6-a6e7-dc7d4cfd9f91",
  "provider_instance_name": "inst_abc123",
  "from": "5586999999999",
  "to": null,
  "remote_jid": "5586999999999@s.whatsapp.net",
  "message_type": "text",
  "content": "Olá",
  "media_url": null,
  "provider_message_id": "BAE5XXXXXXXX",
  "timestamp": "2026-05-26T12:50:00Z"
}
```

A mensagem também deve ser registrada em `messages` com:

```txt
direction = inbound
message_type = text
status = received
```

---

## Eventos de mensagem enviada

Evento interno:

```txt
message.sent
```

Critérios possíveis:

- payload indica mensagem enviada;
- `fromMe` é `true`;
- existe identificador de mensagem.

Esse evento pode ser usado para atualizar registros de mensagens outbound quando houver `provider_message_id`.

Na V1, se não for possível reconciliar com mensagem já salva, o evento ainda deve ser salvo em `webhook_events`.

---

## Eventos de entrega

Evento interno:

```txt
message.delivered
```

Critérios possíveis:

- provider informa status de entrega;
- existe identificador de mensagem;
- status indica entrega.

Na V1, esse evento pode atualizar o status da mensagem para:

```txt
delivered
```

Caso o registro original da mensagem seja encontrado.

Se não for encontrado, salvar apenas o evento.

---

## Eventos de leitura

Evento interno:

```txt
message.read
```

Critérios possíveis:

- provider informa status de leitura;
- existe identificador de mensagem;
- status indica leitura.

Na V1, esse evento pode atualizar o status da mensagem para:

```txt
read
```

Caso o registro original da mensagem seja encontrado.

Se não for encontrado, salvar apenas o evento.

---

## Eventos de conexão

Evento interno:

```txt
connection.update
```

Critérios possíveis:

- payload informa mudança de estado da instância;
- status de conexão foi atualizado;
- QR Code, conexão aberta, desconexão ou erro de conexão.

Esse evento deve atualizar o status da instância quando possível.

Mapeamento inicial recomendado:

```txt
provider open/connected       → connected
provider connecting/qrcode    → connecting
provider close/disconnected   → disconnected
provider error                → error
```

Os nomes exatos devem ser ajustados conforme o formato real retornado pela versão da Evolution API usada na V1.

---

## Eventos de erro de envio

Evento interno:

```txt
send.error
```

Critérios possíveis:

- provider informa erro ao enviar mensagem;
- existe identificador de mensagem;
- payload contém erro relacionado a envio.

Quando possível, o backend deve:

- atualizar mensagem como `failed`;
- registrar evento em `webhook_events`;
- registrar erro em `error_logs`.

---

## Eventos desconhecidos

Evento interno:

```txt
unknown
```

Quando o backend não conseguir classificar o evento, ele deve:

1. salvar o payload bruto;
2. marcar `event_type` como `unknown`;
3. definir `processing_status` como `received` ou `ignored`;
4. não quebrar a aplicação;
5. registrar log para depuração, se necessário.

Resposta recomendada:

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

---

## Normalização do payload

Todo evento reconhecido deve ser convertido para um formato interno padronizado.

Formato base:

```json
{
  "event_type": "message.received",
  "provider": "evolution",
  "client_id": "uuid-do-cliente",
  "instance_id": "uuid-da-instancia",
  "provider_instance_name": "inst_abc123",
  "remote_jid": "5586999999999@s.whatsapp.net",
  "from": "5586999999999",
  "to": null,
  "message_type": "text",
  "content": "Olá",
  "media_url": null,
  "provider_message_id": "BAE5XXXXXXXX",
  "timestamp": "2026-05-26T12:50:00Z"
}
```

Nem todos os campos serão aplicáveis a todos os eventos.

Campos não aplicáveis podem ser `null` ou omitidos, conforme schema final definido na implementação.

---

## Tipos de mensagem normalizados

Na V1, os tipos de mensagem normalizados serão:

```txt
text
image
audio
document
video
unknown
```

Tipos futuros possíveis:

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

## Registro em `webhook_events`

Todo evento recebido deve gerar, quando possível, um registro em `webhook_events`.

Campos principais:

```txt
id
client_id
instance_id
provider
provider_instance_name
event_type
raw_payload
normalized_payload
processing_status
forwarded_to_n8n
n8n_status_code
n8n_response
received_at
processed_at
forwarded_at
created_at
```

---

## Status de processamento

Valores iniciais:

```txt
received
processed
failed
ignored
```

Uso recomendado:

```txt
received  = evento recebido e salvo
processed = evento processado com sucesso
failed    = houve falha no processamento
ignored   = evento reconhecido, mas sem ação necessária
```

---

## Registro em `messages`

Quando o evento representar uma mensagem recebida, o backend deve registrar uma linha em `messages`.

Campos esperados:

```txt
client_id
instance_id
direction
message_type
remote_jid
content
media_url
caption
provider_message_id
status
raw_payload
created_at
received_at
```

Valores:

```txt
direction = inbound
status = received
```

---

## Atualização de mensagens outbound

Quando o evento representar status de mensagem enviada, entregue ou lida, o backend deve tentar localizar a mensagem pelo:

```txt
provider_message_id
```

Se encontrar, pode atualizar:

```txt
status
updated_at
```

Possíveis status futuros:

```txt
sent
delivered
read
failed
```

Se não encontrar, o evento ainda deve permanecer salvo em `webhook_events`.

---

## Atualização de instâncias

Quando o evento representar atualização de conexão, o backend deve tentar atualizar a instância relacionada.

Campos possíveis:

```txt
status
phone_number
connected_at
disconnected_at
updated_at
```

Exemplo:

```txt
connection.update → connected
```

Atualização:

```txt
instances.status = connected
instances.connected_at = now()
```

---

## Encaminhamento para n8n

Após receber, salvar e normalizar o evento, o backend pode encaminhá-lo para o webhook do n8n configurado na instância.

Condição mínima:

```txt
instance.n8n_webhook_url não é nulo
instance.webhook_enabled = true
event_type é encaminhável
```

---

## Eventos encaminháveis para n8n

Na V1, recomenda-se encaminhar principalmente:

```txt
message.received
connection.update
send.error
```

Eventos como `message.delivered` e `message.read` podem ser salvos, mas não precisam necessariamente ser enviados ao n8n na V1.

Essa decisão pode ser ajustada na spec 007.

---

## Payload enviado ao n8n

O payload enviado ao n8n deve ser o payload normalizado, não o payload bruto da Evolution API.

Exemplo:

```json
{
  "event_type": "message.received",
  "provider": "evolution",
  "client_id": "2b78b2c1-8c60-43a4-9bb5-cb8930d1c3c4",
  "instance_id": "1e1d7d4a-7b8e-4ef6-a6e7-dc7d4cfd9f91",
  "provider_instance_name": "inst_abc123",
  "from": "5586999999999",
  "remote_jid": "5586999999999@s.whatsapp.net",
  "message_type": "text",
  "content": "Olá",
  "provider_message_id": "BAE5XXXXXXXX",
  "timestamp": "2026-05-26T12:50:00Z"
}
```

---

## Resposta do n8n

Quando o backend encaminhar evento para o n8n, deve armazenar:

```txt
n8n_status_code
n8n_response
forwarded_to_n8n
forwarded_at
```

Se o n8n retornar status de sucesso, marcar:

```txt
forwarded_to_n8n = true
```

Se falhar, marcar:

```txt
forwarded_to_n8n = false
```

E registrar erro em `error_logs`.

---

## Falha no encaminhamento para n8n

Se o n8n estiver indisponível ou retornar erro, o backend não deve perder o evento.

O sistema deve:

1. manter o evento salvo em `webhook_events`;
2. marcar `forwarded_to_n8n = false`;
3. registrar `n8n_status_code`, se houver;
4. armazenar resposta de erro, se houver;
5. registrar `error_logs`;
6. responder à Evolution API sem necessariamente quebrar todo o fluxo.

Código de erro recomendado:

```txt
N8N_FORWARDING_ERROR
```

---

## Retry na V1

Na V1, o retry pode ser simples.

Opções possíveis:

```txt
1. tentar uma vez e marcar falha;
2. tentar uma segunda vez imediatamente;
3. deixar retry avançado para versão futura.
```

Recomendação para V1:

```txt
tentar uma vez e marcar falha
```

Motivo:

- reduz complexidade inicial;
- evita dependência forte de fila;
- mantém rastreabilidade pelo banco;
- permite validar fluxo principal.

Retry com Redis/fila pode ser implementado em versão futura.

---

## Ordem recomendada de processamento

A ordem recomendada para processar um webhook é:

```txt
1. Validar segredo do webhook.
2. Ler payload bruto.
3. Detectar provider.
4. Extrair provider_instance_name.
5. Criar registro inicial em webhook_events.
6. Buscar instância pelo provider_instance_name.
7. Identificar client_id e instance_id.
8. Classificar event_type.
9. Normalizar payload.
10. Atualizar webhook_events com dados normalizados.
11. Registrar mensagem recebida, se aplicável.
12. Atualizar mensagem outbound, se aplicável.
13. Atualizar instância, se aplicável.
14. Encaminhar para n8n, se aplicável.
15. Atualizar status final do webhook_event.
16. Retornar resposta HTTP.
```

---

## Fluxo detalhado: mensagem recebida

```txt
1. Usuário envia mensagem para o WhatsApp conectado.
2. Evolution API captura a mensagem.
3. Evolution API envia webhook ao backend.
4. Backend valida X-Webhook-Secret.
5. Backend salva raw_payload em webhook_events.
6. Backend identifica provider_instance_name.
7. Backend encontra a instância no banco.
8. Backend identifica o cliente dono da instância.
9. Backend classifica evento como message.received.
10. Backend normaliza remetente, conteúdo e tipo da mensagem.
11. Backend registra mensagem em messages.
12. Backend verifica n8n_webhook_url da instância.
13. Backend encaminha payload normalizado ao n8n.
14. Backend registra status do encaminhamento.
15. Backend responde 200 OK para Evolution API.
```

---

## Fluxo detalhado: atualização de conexão

```txt
1. Evolution API detecta mudança de conexão.
2. Evolution API envia webhook ao backend.
3. Backend valida X-Webhook-Secret.
4. Backend salva raw_payload.
5. Backend identifica instância.
6. Backend classifica evento como connection.update.
7. Backend normaliza status recebido.
8. Backend atualiza status da instância.
9. Backend encaminha evento ao n8n, se aplicável.
10. Backend responde 200 OK ou 202 Accepted.
```

---

## Fluxo detalhado: evento desconhecido

```txt
1. Evolution API envia evento não mapeado.
2. Backend valida X-Webhook-Secret.
3. Backend salva raw_payload.
4. Backend tenta identificar instância.
5. Backend não reconhece tipo do evento.
6. Backend define event_type = unknown.
7. Backend define processing_status = received ou ignored.
8. Backend não registra mensagem.
9. Backend não encaminha ao n8n, salvo decisão futura.
10. Backend responde 202 Accepted.
```

---

## Fluxo detalhado: falha no n8n

```txt
1. Backend recebe webhook válido.
2. Backend salva e normaliza evento.
3. Backend tenta encaminhar ao n8n.
4. n8n retorna erro ou fica indisponível.
5. Backend mantém evento salvo.
6. Backend define forwarded_to_n8n = false.
7. Backend registra erro em error_logs.
8. Backend responde à Evolution API.
```

---

## Respostas HTTP para Evolution API

## Sucesso completo

```http
200 OK
```

```json
{
  "received": true,
  "event_id": "e6aee962-294c-4f38-b377-33ef2ad667fa",
  "event_type": "message.received",
  "processing_status": "processed",
  "forwarded_to_n8n": true
}
```

---

## Evento recebido, mas não totalmente processado

```http
202 Accepted
```

```json
{
  "received": true,
  "event_id": "e6aee962-294c-4f38-b377-33ef2ad667fa",
  "event_type": "unknown",
  "processing_status": "received",
  "forwarded_to_n8n": false
}
```

---

## Webhook não autorizado

```http
401 Unauthorized
```

```json
{
  "code": "WEBHOOK_UNAUTHORIZED",
  "message": "Webhook não autorizado.",
  "details": {}
}
```

---

## Erro interno de processamento

```http
500 Internal Server Error
```

```json
{
  "code": "WEBHOOK_PROCESSING_ERROR",
  "message": "Erro ao processar webhook.",
  "details": {}
}
```

---

## Cuidados com dados sensíveis

O backend deve evitar expor ou registrar indevidamente:

```txt
API Keys
EVOLUTION_API_KEY
WEBHOOK_SECRET
tokens internos
headers sensíveis
dados pessoais desnecessários
```

Payloads brutos podem ser salvos na V1 para depuração, mas isso deve ser tratado com cautela.

Em versões futuras, avaliar:

- mascaramento;
- retenção;
- anonimização;
- limpeza periódica;
- adequação à LGPD.

---

## Responsabilidades por módulo

## `webhooks`

Responsável por:

- receber webhook;
- validar segredo;
- salvar payload bruto;
- classificar evento;
- normalizar payload;
- registrar mensagens;
- atualizar eventos;
- chamar serviço de encaminhamento.

## `instances`

Responsável por:

- localizar instância por `provider_instance_name`;
- atualizar status da instância;
- fornecer dados de cliente e webhook n8n.

## `messages`

Responsável por:

- registrar mensagens recebidas;
- atualizar mensagens enviadas, se aplicável;
- manter histórico básico de mensagens.

## `n8n`

Responsável por:

- enviar payload normalizado ao webhook configurado;
- registrar retorno;
- indicar sucesso ou falha.

## `logs`

Responsável por:

- registrar falhas em `error_logs`;
- permitir consulta posterior.

---

## Relação com as specs da V1

Este documento impacta diretamente:

```txt
006 — Recebimento de webhooks
007 — Encaminhamento para n8n
003 — Persistência e modelagem inicial
005 — Envio de mensagens
004 — Gestão de instâncias WhatsApp
008 — Segurança com API Key
```

---

## Fora do escopo da V1

Não fazem parte da V1:

- múltiplos webhooks por instância;
- roteamento avançado por tipo de evento;
- painel visual de eventos;
- reprocessamento manual de webhooks;
- retry avançado com fila;
- dead-letter queue;
- assinatura HMAC obrigatória;
- filtros configuráveis por cliente;
- criação automática de workflows no n8n.

---

## Critérios de conformidade

A implementação estará alinhada a este documento se:

- Evolution API enviar webhooks para o backend;
- webhook for protegido por `X-Webhook-Secret`;
- payload bruto for salvo em `webhook_events`;
- instância for identificada quando possível;
- evento for classificado;
- payload reconhecido for normalizado;
- mensagem recebida for registrada em `messages`;
- eventos relevantes forem encaminhados ao n8n;
- falhas de processamento forem registradas;
- eventos desconhecidos não quebrarem a aplicação;
- n8n não receber eventos diretamente da Evolution API.

---

## Resumo

Na V1, o backend será o responsável por centralizar todo o fluxo de webhook.

A Evolution API enviará eventos para o backend, o backend validará, salvará, normalizará e encaminhará eventos relevantes para o n8n.

Essa decisão mantém o sistema mais controlado, auditável e preparado para evolução futura.