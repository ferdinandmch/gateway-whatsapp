# Feature Specification: Encaminhamento para n8n

**Feature Branch**: `007-n8n-forwarding`  
**Created**: 2026-08-19  
**Status**: Draft  
**Input**: User description: "Encaminhamento para n8n com base nos docs/"

## User Scenarios & Testing

### User Story 1 - Encaminhamento automático de mensagens recebidas (Priority: P1)

Como operador de atendimento com fluxos automatizados no n8n, quero que toda mensagem recebida no WhatsApp seja automaticamente encaminhada ao meu webhook n8n configurado na instância, para que meus fluxos de automação sejam acionados em tempo real.

**Why this priority**: Este é o caso de uso principal da feature — sem encaminhamento de mensagens recebidas, o n8n não pode reagir a conversas iniciadas pelos clientes finais.

**Independent Test**: Pode ser testado enviando uma mensagem para o WhatsApp conectado e verificando que o webhook n8n configurado recebe o payload normalizado dentro do tempo esperado.

**Acceptance Scenarios**:

1. **Given** uma instância conectada com `n8n_webhook_url` configurada e `webhook_enabled = true`, **When** uma mensagem é recebida (evento `message.received` processado pela spec 006), **Then** o sistema envia o payload normalizado via POST para a URL configurada e registra `forwarded_to_n8n = true` no evento.
2. **Given** uma instância com `webhook_enabled = false`, **When** uma mensagem é recebida, **Then** o sistema NÃO encaminha ao n8n e registra `forwarded_to_n8n = false`.
3. **Given** uma instância sem `n8n_webhook_url` configurada (valor nulo), **When** uma mensagem é recebida, **Then** o sistema NÃO tenta encaminhar e registra `forwarded_to_n8n = false`.

---

### User Story 2 - Encaminhamento de eventos de conexão (Priority: P2)

Como administrador de instâncias, quero ser notificado no n8n quando uma instância conecta ou desconecta, para que meus fluxos de monitoramento possam tomar ações automatizadas (como alertas ou reconexão).

**Why this priority**: Eventos de conexão são críticos para operação, mas menos frequentes que mensagens. Permitem monitoramento proativo da saúde das instâncias.

**Independent Test**: Pode ser testado simulando um evento `connection.update` e verificando que o n8n recebe a notificação com o status atualizado.

**Acceptance Scenarios**:

1. **Given** uma instância com webhook n8n ativo, **When** ocorre um evento `connection.update`, **Then** o sistema encaminha o payload normalizado ao n8n.
2. **Given** uma instância com webhook n8n ativo, **When** ocorre um evento `connection.update` indicando desconexão, **Then** o payload encaminhado contém o status correto e o timestamp do evento.

---

### User Story 3 - Encaminhamento de erros de envio (Priority: P2)

Como operador de automação, quero ser notificado no n8n quando uma mensagem que tentei enviar falha, para que meus fluxos possam tratar o erro (retentar, notificar o cliente, escalar).

**Why this priority**: Falhas de envio impactam a experiência do cliente final e precisam de tratamento rápido. Prioridade igual a eventos de conexão por serem ambos operacionais.

**Independent Test**: Pode ser testado simulando um evento `send.error` e verificando que o n8n recebe o payload com os detalhes do erro.

**Acceptance Scenarios**:

1. **Given** uma instância com webhook n8n ativo, **When** ocorre um evento `send.error`, **Then** o sistema encaminha o payload normalizado ao n8n incluindo o identificador da mensagem que falhou.

---

### User Story 4 - Resiliência a falhas do n8n (Priority: P1)

Como operador do sistema, quero que quando o n8n estiver indisponível ou retornar erro, o evento não seja perdido e a falha seja registrada, para que eu possa investigar e reprocessar manualmente se necessário.

**Why this priority**: A resiliência é tão importante quanto o encaminhamento em si — perder eventos silenciosamente compromete toda a automação.

**Independent Test**: Pode ser testado configurando uma URL de webhook inválida ou indisponível e verificando que o evento permanece salvo, a falha é registrada e a resposta à Evolution API não é impactada.

**Acceptance Scenarios**:

1. **Given** uma instância com webhook n8n ativo mas o n8n está indisponível, **When** o sistema tenta encaminhar um evento, **Then** o evento permanece salvo em `webhook_events`, `forwarded_to_n8n = false`, o código de erro e resposta são registrados, e um erro é registrado em `error_logs`.
2. **Given** o n8n retorna HTTP 500, **When** o sistema recebe essa resposta, **Then** registra `n8n_status_code = 500`, `forwarded_to_n8n = false`, e o processamento do webhook original não falha (a Evolution API recebe resposta de sucesso).
3. **Given** o n8n está com timeout (não responde em tempo hábil), **When** o sistema detecta o timeout, **Then** registra a falha sem impactar o fluxo principal de recebimento do webhook.

---

### Edge Cases

- O que acontece quando a URL do n8n está mal formatada (não é uma URL válida)?
- Como o sistema se comporta quando o payload normalizado excede limites de tamanho aceitáveis para o n8n?
- O que acontece quando múltiplos eventos chegam simultaneamente para a mesma instância com webhook n8n ativo?
- Como o sistema lida com redirecionamentos HTTP (301/302) retornados pelo n8n?

## Requirements

### Functional Requirements

- **FR-001**: O sistema DEVE encaminhar eventos do tipo `message.received`, `connection.update` e `send.error` para a URL de webhook n8n configurada na instância, quando `webhook_enabled = true` e `n8n_webhook_url` não for nulo.
- **FR-002**: O sistema DEVE enviar ao n8n o payload normalizado (formato interno padronizado), nunca o payload bruto da Evolution API.
- **FR-003**: O sistema DEVE registrar o resultado do encaminhamento nos campos `forwarded_to_n8n`, `n8n_status_code`, `n8n_response` e `forwarded_at` do registro de `webhook_events`.
- **FR-004**: O sistema DEVE continuar processando o webhook normalmente mesmo quando o encaminhamento para o n8n falha — a falha no n8n não pode impactar a resposta à Evolution API.
- **FR-005**: O sistema DEVE registrar falhas de encaminhamento em `error_logs` com o código `N8N_FORWARDING_ERROR`.
- **FR-006**: O sistema DEVE respeitar um timeout máximo ao aguardar resposta do n8n, para não bloquear o processamento de webhooks.
- **FR-007**: O sistema DEVE considerar como sucesso apenas respostas HTTP 2xx do n8n.
- **FR-008**: O sistema NÃO DEVE encaminhar eventos do tipo `message.delivered`, `message.read` e `unknown` ao n8n na V1.
- **FR-009**: O sistema DEVE validar que a `n8n_webhook_url` é uma URL válida antes de tentar o encaminhamento.
- **FR-010**: Na V1, o sistema DEVE tentar o encaminhamento uma única vez (sem retry automático) e registrar falha caso não tenha sucesso.

### Key Entities

- **Evento de Webhook (webhook_events)**: Registro do evento recebido, contendo campos de controle do encaminhamento (`forwarded_to_n8n`, `n8n_status_code`, `n8n_response`, `forwarded_at`).
- **Instância (instances)**: Contém a configuração de encaminhamento (`n8n_webhook_url`, `webhook_enabled`) que determina se e para onde encaminhar.
- **Registro de Erro (error_logs)**: Armazena falhas de encaminhamento com código, mensagem e contexto para depuração.

## Success Criteria

### Measurable Outcomes

- **SC-001**: 100% dos eventos encaminháveis com webhook ativo resultam em tentativa de encaminhamento ao n8n (nenhum evento é silenciosamente descartado).
- **SC-002**: O encaminhamento ao n8n adiciona no máximo 5 segundos ao tempo total de processamento do webhook (incluindo timeout).
- **SC-003**: Falhas no n8n não afetam a taxa de sucesso de recebimento de webhooks da Evolution API (0% de perda por causa do n8n).
- **SC-004**: 100% das falhas de encaminhamento são registradas e consultáveis via logs.
- **SC-005**: O operador consegue identificar eventos não encaminhados filtrando por `forwarded_to_n8n = false` nos logs de webhooks.

## Assumptions

- A spec 006 (Recebimento de webhooks) já está implementada e fornece o pipeline de recebimento, validação, classificação e normalização dos eventos.
- A instância já possui os campos `n8n_webhook_url` e `webhook_enabled` populados (definidos na spec 004).
- O n8n aceita payloads JSON via POST em webhooks genéricos.
- Na V1, não há necessidade de autenticação adicional no webhook do n8n (a URL é considerada suficiente como credencial — segurança por obscuridade da URL).
- Na V1, não há retry automático — uma tentativa única com registro de falha é suficiente.
- O timeout para chamadas ao n8n deve ser configurável, com valor padrão razoável (ex: 5 segundos).
- Eventos `message.delivered` e `message.read` podem ser encaminhados em versões futuras, mas não na V1.
