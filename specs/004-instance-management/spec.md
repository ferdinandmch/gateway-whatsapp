# Feature Specification: Gerenciamento de Instâncias WhatsApp

**Feature Branch**: `004-instance-management`  
**Created**: 2026-08-18  
**Status**: Draft  
**Input**: User description: "Gerenciamento de instâncias WhatsApp — CRUD completo com criação, conexão via QR code, consulta de status, desconexão e remoção, com sincronização entre backend e provider"

## Clarifications

### Session 2026-08-18

- Q: A spec deve incluir endpoint de listagem de instâncias (`GET /v1/instances`)? → A: Sim, incluir com paginação (limit/offset).
- Q: Há limite máximo de instâncias por cliente? → A: Sim, limite fixo de 10 instâncias por cliente no código.
- Q: Qual o estado da instância quando o provider falha durante criação? → A: Salvar com status "error" — operador pode tentar conectar depois ou remover.
- Q: Status da instância deve ser atualizado automaticamente via webhook do provider? → A: Sim, atualizar automaticamente quando webhook de conexão/desconexão chegar.
- Q: Instâncias com status "removed" devem aparecer na listagem? → A: Ocultar por padrão, permitir filtro `?include_removed=true`.

## User Scenarios & Testing

### User Story 1 - Criar instância WhatsApp (Priority: P1)

O operador do sistema precisa criar uma nova instância de WhatsApp para começar a usar o serviço de mensageria. Ele informa um nome amigável e opcionalmente uma URL de webhook do n8n. O sistema cria a instância internamente e sincroniza com o provider de mensageria.

**Why this priority**: Sem criação de instância, nenhuma outra operação é possível. É o ponto de partida obrigatório para qualquer uso do sistema.

**Independent Test**: Pode ser testado isoladamente enviando uma requisição de criação e verificando que a instância aparece com status "created" e possui identificador no provider.

**Acceptance Scenarios**:

1. **Given** um cliente autenticado e ativo, **When** ele envia uma requisição de criação com um nome amigável válido, **Then** o sistema cria a instância internamente, sincroniza com o provider, e retorna os dados da instância com status "created".
2. **Given** um cliente autenticado e ativo, **When** ele envia uma requisição de criação sem informar `display_name`, **Then** o sistema retorna erro de validação.
3. **Given** um cliente inativo, **When** ele tenta criar uma instância, **Then** o sistema retorna erro informando que o cliente está inativo.
4. **Given** um cliente que já possui 10 instâncias (excluindo removidas), **When** ele tenta criar uma nova instância, **Then** o sistema retorna erro indicando limite atingido.
5. **Given** um cliente autenticado e ativo, **When** a criação no provider falha, **Then** o sistema salva a instância com status "error", registra o erro e retorna falha ao cliente.

---

### User Story 2 - Conectar instância ao WhatsApp (Priority: P1)

O operador precisa conectar a instância criada ao WhatsApp para poder enviar e receber mensagens. Ao solicitar conexão, o sistema retorna os dados necessários para autenticação (QR code ou pairing code) fornecidos pelo provider.

**Why this priority**: Uma instância criada sem conexão não tem utilidade prática. A conexão é o segundo passo essencial do fluxo.

**Independent Test**: Pode ser testado criando uma instância e solicitando conexão, verificando que o sistema retorna dados de QR code ou pairing code e que o status muda para "connecting".

**Acceptance Scenarios**:

1. **Given** uma instância com status "created", "disconnected" ou "error" pertencente ao cliente autenticado, **When** ele solicita conexão, **Then** o sistema retorna QR code ou pairing code e atualiza status para "connecting".
2. **Given** uma instância que não pertence ao cliente autenticado, **When** ele tenta conectar, **Then** o sistema retorna erro de instância não encontrada (sem revelar existência para outro cliente).
3. **Given** uma instância com status "removed", **When** o cliente tenta conectar, **Then** o sistema retorna erro apropriado.

---

### User Story 3 - Consultar status da instância (Priority: P2)

O operador precisa verificar o estado atual de uma instância para saber se ela está conectada, desconectada ou com erro, antes de tentar enviar mensagens ou tomar ações corretivas.

**Why this priority**: Importante para monitoramento e tomada de decisão, mas não bloqueia o fluxo principal de criação e conexão.

**Independent Test**: Pode ser testado consultando o status de uma instância existente e verificando que os dados retornados refletem o estado real no provider.

**Acceptance Scenarios**:

1. **Given** uma instância conectada pertencente ao cliente, **When** ele consulta o status, **Then** o sistema retorna status "connected" com número de telefone e timestamps relevantes.
2. **Given** uma instância desconectada, **When** ele consulta o status, **Then** o sistema retorna status "disconnected" com timestamp de desconexão.
3. **Given** uma instância inexistente ou de outro cliente, **When** ele consulta o status, **Then** o sistema retorna erro de instância não encontrada.

---

### User Story 4 - Desconectar instância (Priority: P2)

O operador precisa desconectar uma instância do WhatsApp por motivos operacionais (troca de número, manutenção, etc.) sem perder os dados associados a ela.

**Why this priority**: Necessária para operações de manutenção, mas menos frequente que criação e conexão.

**Independent Test**: Pode ser testado desconectando uma instância conectada e verificando que o status muda para "disconnected" e que os dados da instância são preservados.

**Acceptance Scenarios**:

1. **Given** uma instância conectada pertencente ao cliente, **When** ele solicita desconexão, **Then** o sistema desconecta no provider, atualiza status para "disconnected" e retorna confirmação com timestamp.
2. **Given** uma instância já desconectada, **When** ele tenta desconectar novamente, **Then** o sistema retorna o status atual sem erro (operação idempotente).
3. **Given** uma instância de outro cliente, **When** ele tenta desconectar, **Then** o sistema retorna erro de instância não encontrada.

---

### User Story 5 - Remover instância (Priority: P3)

O operador precisa remover permanentemente uma instância que não será mais utilizada. A remoção deve sincronizar com o provider e marcar a instância como removida no sistema.

**Why this priority**: Operação destrutiva e menos frequente. Importante para limpeza, mas não bloqueia uso regular do sistema.

**Independent Test**: Pode ser testado removendo uma instância e verificando que seu status muda para "removed" e que ela não aparece mais na listagem padrão.

**Acceptance Scenarios**:

1. **Given** uma instância pertencente ao cliente (qualquer status exceto "removed"), **When** ele solicita remoção, **Then** o sistema remove no provider (se suportado), marca como "removed" internamente e retorna confirmação.
2. **Given** uma instância já removida, **When** ele tenta remover novamente, **Then** o sistema retorna erro de instância não encontrada.
3. **Given** falha ao remover no provider, **When** o sistema não consegue sincronizar a remoção, **Then** o erro é registrado e o cliente recebe resposta de erro do provider.

---

### User Story 6 - Listar instâncias (Priority: P2)

O operador precisa visualizar todas as suas instâncias para monitorar o estado geral do sistema, identificar instâncias com problemas e gerenciar seu parque de números WhatsApp.

**Why this priority**: Essencial para operação prática — sem listagem, o operador não consegue descobrir quais instâncias possui nem seus estados atuais.

**Independent Test**: Pode ser testado criando múltiplas instâncias e verificando que a listagem retorna todas elas com paginação correta e filtro de removidas.

**Acceptance Scenarios**:

1. **Given** um cliente com 3 instâncias ativas, **When** ele lista suas instâncias sem filtros, **Then** o sistema retorna as 3 instâncias com paginação (excluindo removidas).
2. **Given** um cliente com instâncias removidas, **When** ele lista com filtro `include_removed=true`, **Then** o sistema retorna todas as instâncias incluindo as removidas.
3. **Given** um cliente sem instâncias, **When** ele lista suas instâncias, **Then** o sistema retorna lista vazia com paginação.

---

### User Story 7 - Atualizar configurações da instância (Priority: P3)

O operador precisa alterar o nome amigável, a URL de webhook do n8n ou a flag de encaminhamento de eventos de uma instância sem precisar removê-la e recriá-la.

**Why this priority**: Conveniência operacional — evita perda de conexão ativa para uma simples mudança de configuração.

**Independent Test**: Pode ser testado enviando PATCH com novos valores e verificando que a instância retorna os dados atualizados sem alterar status ou conexão.

**Acceptance Scenarios**:

1. **Given** uma instância pertencente ao cliente (qualquer status exceto "removed"), **When** ele envia PATCH com `display_name` novo, **Then** o sistema atualiza apenas esse campo e retorna a instância completa.
2. **Given** uma instância pertencente ao cliente, **When** ele envia PATCH com `n8n_webhook_url` e `webhook_enabled`, **Then** ambos os campos são atualizados sem afetar status ou conexão.
3. **Given** uma instância removida ou de outro cliente, **When** ele tenta atualizar, **Then** o sistema retorna erro de instância não encontrada.

---

### Edge Cases

- O que acontece quando o provider está indisponível durante a criação? O sistema salva a instância com status "error", registra o erro e retorna falha ao cliente.
- O que acontece quando a sessão do QR code expira antes do usuário escanear? O cliente pode solicitar nova conexão para obter um novo QR code.
- O que acontece com tentativa de operação em instância com status "error"? O sistema permite reconexão mas bloqueia envio de mensagens.
- O que acontece quando o provider retorna dados inesperados na conexão? O sistema registra o erro, atualiza status para "error" e retorna erro padronizado ao cliente.
- O que acontece quando dois clientes tentam conectar a mesma instância simultaneamente? Impossível — cada instância pertence a exatamente um cliente, isolamento garantido pela autenticação.
- O que acontece quando o cliente atinge o limite de 10 instâncias? O sistema retorna erro indicando limite atingido. Instâncias com status "removed" não contam para o limite.
- O que acontece quando um webhook de status chega para uma instância que está sendo operada simultaneamente? O webhook atualiza o status de forma atômica; a operação em andamento consulta o estado mais recente.

## Requirements

### Functional Requirements

- **FR-001**: Sistema DEVE permitir criar instâncias associadas ao cliente autenticado, gerando automaticamente o identificador interno no provider.
- **FR-002**: Sistema DEVE sincronizar criação de instância entre backend e provider. Quando o provider falhar, a instância deve ser salva com status "error".
- **FR-003**: Sistema DEVE retornar dados de conexão (QR code ou pairing code) ao solicitar conexão de uma instância.
- **FR-004**: Sistema DEVE atualizar o status da instância conforme as ações realizadas e retornos do provider (created, connecting, connected, disconnected, error, removed).
- **FR-005**: Sistema DEVE permitir consulta de status que reflita o estado real da instância, incluindo informações como número de telefone quando conectada.
- **FR-006**: Sistema DEVE permitir desconexão de instância, sincronizando com o provider e preservando dados internos.
- **FR-007**: Sistema DEVE permitir remoção de instância (soft delete), sincronizando com provider quando suportado.
- **FR-008**: Sistema DEVE garantir que cada instância pertence a exatamente um cliente, impedindo acesso por outros clientes.
- **FR-009**: Sistema DEVE registrar erros de provider em log de erros quando operações de sincronização falharem.
- **FR-010**: Sistema DEVE validar que apenas clientes ativos podem realizar operações em instâncias.
- **FR-011**: Sistema DEVE armazenar o identificador do provider (`provider_instance_name`) junto com a instância interna.
- **FR-012**: Sistema DEVE permitir configurar URL de webhook do n8n por instância no momento da criação.
- **FR-013**: Sistema DEVE permitir listar instâncias do cliente autenticado com paginação (limit/offset), ocultando instâncias removidas por padrão.
- **FR-014**: Sistema DEVE impor limite máximo de 10 instâncias por cliente (excluindo removidas na contagem).
- **FR-015**: Sistema DEVE atualizar status da instância automaticamente quando webhooks de conexão ou desconexão chegarem do provider.
- **FR-016**: Sistema DEVE permitir atualizar configurações de uma instância existente (display_name, n8n_webhook_url, webhook_enabled) sem necessidade de recriar a instância.

### Key Entities

- **Instância (Instance)**: Representa uma sessão de WhatsApp gerenciada pelo sistema. Possui nome amigável, status, provider associado, identificador no provider, número de telefone (quando conectada), configuração de webhook, e pertence a um cliente. Limite: 10 instâncias ativas por cliente.
- **Cliente (Client)**: Entidade proprietária de instâncias. Possui API Key para autenticação e status ativo/inativo. Já modelado na spec 003.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Operadores podem criar uma nova instância e obter confirmação em menos de 5 segundos.
- **SC-002**: Operadores podem iniciar conexão e receber dados de QR code em menos de 10 segundos.
- **SC-003**: Consulta de status retorna informação atualizada em menos de 3 segundos.
- **SC-004**: 100% das operações em instâncias de outros clientes são bloqueadas com resposta genérica (sem vazamento de informação).
- **SC-005**: Falhas de comunicação com o provider são registradas em 100% dos casos sem perda silenciosa.
- **SC-006**: Todas as transições de status são rastreáveis — cada mudança de estado é refletida no campo `updated_at` da instância.
- **SC-007**: Listagem de instâncias retorna resultados paginados em menos de 2 segundos.
- **SC-008**: Status da instância é atualizado automaticamente em menos de 5 segundos após recebimento de webhook do provider.

## Assumptions

- O provider de mensageria (Evolution API) está disponível e acessível na rede interna durante operações normais.
- A modelagem de dados (tabelas de instâncias e clientes) já foi definida na spec 003 de persistência.
- A autenticação via API Key já está funcional, implementada na infraestrutura base.
- A abstração de provider (`MessagingProvider`) já existe e o `EvolutionProvider` implementa as operações de criação, conexão, status, desconexão e remoção de instâncias.
- Remoção de instância é implementada como soft delete (status "removed") no backend, independentemente do suporte do provider a remoção total.
- O formato do QR code ou pairing code depende da resposta do provider — o backend repassa os dados sem transformação adicional.
- O limite de 10 instâncias por cliente é fixo no código na V1; pode ser tornado configurável em versões futuras.
- Webhooks de status do provider (conexão/desconexão) já são recebidos pela rota de webhooks definida na spec 006, mas a atualização de status da instância é responsabilidade desta spec.
