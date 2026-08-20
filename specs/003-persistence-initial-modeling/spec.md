# Feature Specification: Persistência e Modelagem Inicial

**Feature Branch**: `003-persistence-initial-modeling`  
**Created**: 2026-08-16  
**Status**: Draft  
**Input**: User description: "Persistência e modelagem inicial de dados — definição dos modelos de domínio, configuração da conexão com banco de dados e criação das migrations iniciais"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Persistir dados de clientes no sistema (Priority: P1)

Um administrador do sistema precisa que os dados de clientes (consumidores da API) sejam armazenados de forma persistente para que o sistema possa identificar, autenticar e isolar recursos por cliente.

**Why this priority**: Sem a entidade cliente, nenhum recurso pode ser associado ou isolado. É a base de toda a cadeia de dados.

**Independent Test**: Pode ser testado criando um registro de cliente no banco e verificando que os dados são persistidos e recuperáveis corretamente.

**Acceptance Scenarios**:

1. **Given** o sistema com banco configurado, **When** um cliente é criado com nome e dados válidos, **Then** o registro é persistido com UUID, timestamps e pode ser recuperado.
2. **Given** um cliente existente, **When** seus dados são consultados, **Then** todas as informações armazenadas são retornadas corretamente.
3. **Given** um cliente existente, **When** ele é desativado, **Then** o status reflete a desativação sem perda de dados históricos.

---

### User Story 2 - Persistir dados de instâncias WhatsApp (Priority: P1)

O sistema precisa armazenar informações sobre as instâncias WhatsApp gerenciadas, associando cada instância a um cliente e mantendo seu estado de conexão.

**Why this priority**: Instâncias são o recurso central do gateway — sem persistência delas, não há gerenciamento possível.

**Independent Test**: Pode ser testado criando uma instância vinculada a um cliente e verificando a persistência do vínculo e dos metadados.

**Acceptance Scenarios**:

1. **Given** um cliente existente, **When** uma instância é criada para esse cliente, **Then** a instância é persistida com referência ao cliente, nome e status.
2. **Given** uma instância existente, **When** seu estado de conexão muda, **Then** o novo estado é registrado no banco.
3. **Given** um cliente com múltiplas instâncias, **When** as instâncias são consultadas, **Then** apenas as instâncias daquele cliente são retornadas.

---

### User Story 3 - Persistir mensagens enviadas e recebidas (Priority: P2)

O sistema precisa registrar as mensagens que transitam pela plataforma, tanto enviadas quanto recebidas, para rastreabilidade e reconciliação com o provider.

**Why this priority**: Mensagens são o core do produto, mas dependem de clientes e instâncias existirem primeiro.

**Independent Test**: Pode ser testado criando registros de mensagem com diferentes tipos e direções, verificando persistência e consulta.

**Acceptance Scenarios**:

1. **Given** uma instância ativa, **When** uma mensagem é enviada, **Then** o sistema persiste direção, tipo, conteúdo, destinatário, status e identificador do provider.
2. **Given** mensagens persistidas, **When** consultadas por instância, **Then** apenas mensagens daquela instância são retornadas.
3. **Given** uma mensagem enviada, **When** o provider retorna um identificador, **Then** o identificador externo é armazenado junto ao registro.

---

### User Story 4 - Persistir eventos de webhook recebidos (Priority: P2)

O sistema precisa armazenar os eventos recebidos via webhook da Evolution API para garantir rastreabilidade, permitir reprocessamento e diagnóstico.

**Why this priority**: Eventos são essenciais para o fluxo de recebimento, mas são complementares ao envio.

**Independent Test**: Pode ser testado criando registros de eventos com payloads variados e verificando que o payload bruto é preservado integralmente.

**Acceptance Scenarios**:

1. **Given** um webhook recebido, **When** o evento é persistido, **Then** o payload bruto original é preservado em formato flexível.
2. **Given** eventos persistidos, **When** consultados por instância ou tipo, **Then** são filtráveis e retornados corretamente.
3. **Given** um evento persistido, **When** o sistema precisa reprocessá-lo, **Then** o payload original está íntegro e disponível.

---

### User Story 5 - Executar migrations de forma reproduzível (Priority: P1)

O desenvolvedor precisa que as alterações no banco sejam versionadas e aplicáveis de forma automática e reproduzível em qualquer ambiente.

**Why this priority**: Sem migrations funcionais, nenhum dos modelos acima pode ser criado no banco de forma controlada.

**Independent Test**: Pode ser testado aplicando a migration inicial em um banco limpo e verificando que todas as tabelas são criadas com as colunas e constraints corretas.

**Acceptance Scenarios**:

1. **Given** um banco PostgreSQL limpo, **When** as migrations são executadas, **Then** todas as tabelas definidas são criadas com suas colunas, tipos, constraints e índices.
2. **Given** migrations aplicadas, **When** um rollback é executado, **Then** as alterações são revertidas de forma controlada.
3. **Given** um ambiente novo, **When** o comando de migration é executado, **Then** o banco atinge o estado esperado sem intervenção manual.

---

### Edge Cases

- O que acontece quando se tenta criar um cliente com nome duplicado?
- Como o sistema se comporta quando o banco está indisponível durante uma operação de escrita?
- O que acontece com mensagens que referenciam uma instância soft-deleted? Dados são preservados; queries de listagem filtram instâncias deletadas por padrão, mas dados permanecem acessíveis via consulta explícita.
- Como eventos com payloads malformados ou excessivamente grandes são tratados?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema DEVE definir um modelo de dados para clientes com identificador UUID, nome, status ativo/inativo, timestamp de soft-delete (deleted_at) e timestamps de criação/atualização.
- **FR-002**: O sistema DEVE definir um modelo de dados para instâncias WhatsApp com identificador UUID, referência ao cliente proprietário, nome, estado de conexão (disconnected, connecting, connected, closed), identificador no provider e timestamps.
- **FR-003**: O sistema DEVE definir um modelo de dados para mensagens com identificador UUID, referência à instância, direção (inbound/outbound), tipo de conteúdo, corpo da mensagem, destinatário/remetente, status, identificador no provider e timestamps.
- **FR-004**: O sistema DEVE definir um modelo de dados para eventos de webhook com identificador UUID, referência à instância, tipo do evento, payload bruto preservado, status de processamento e timestamps.
- **FR-005**: O sistema DEVE definir um modelo de dados para logs de erro com identificador UUID, contexto da operação, mensagem de erro, detalhes adicionais e timestamp.
- **FR-006**: O sistema DEVE configurar a conexão com PostgreSQL de forma assíncrona, usando connection pooling.
- **FR-007**: O sistema DEVE gerar uma migration inicial que crie todas as tabelas definidas com suas constraints, índices e relacionamentos.
- **FR-008**: As migrations DEVEM ser reversíveis (suportar upgrade e downgrade).
- **FR-009**: O sistema DEVE garantir isolamento entre clientes — instâncias, mensagens e eventos DEVEM pertencer a um cliente específico via chave estrangeira.
- **FR-010**: Campos que armazenam payloads variáveis (raw_payload, detalhes) DEVEM usar formato flexível para dados semi-estruturados.

### Key Entities

- **Client**: Consumidor da API. Possui nome, status ativo/inativo, deleted_at para soft-delete, timestamps. Ponto de isolamento de dados. Nunca é removido fisicamente do banco.
- **Instance**: Instância WhatsApp gerenciada. Pertence a um Client. Possui nome, estado de conexão (disconnected → connecting → connected; connected → closed como estado terminal), referência ao provider.
- **Message**: Mensagem enviada ou recebida. Pertence a uma Instance. Possui direção, tipo, conteúdo, status, identificador externo.
- **WebhookEvent**: Evento recebido via webhook. Pertence a uma Instance. Possui tipo, payload bruto, status de processamento.
- **ErrorLog**: Registro de erro para diagnóstico. Possui contexto, mensagem, detalhes variáveis.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: As migrations podem ser aplicadas em um banco limpo em menos de 10 segundos, criando todas as tabelas corretamente.
- **SC-002**: O sistema suporta operações de leitura e escrita em todas as entidades sem erros de integridade.
- **SC-003**: Dados de um cliente não são acessíveis através de consultas de outro cliente (isolamento verificável por testes).
- **SC-004**: Payloads de até 1MB podem ser armazenados e recuperados integralmente nos campos flexíveis.
- **SC-005**: Rollback de migrations reverte o banco ao estado anterior sem perda de estrutura.

## Clarifications

### Session 2026-08-16

- Q: Quais são os estados possíveis de conexão de uma instância? → A: 4 estados — disconnected, connecting, connected, closed (terminal)
- Q: Como o sistema trata remoção de clientes/instâncias? → A: Soft-delete (flag ou deleted_at timestamp, dados preservados)
- Q: O que acontece com mensagens/eventos quando uma instância é soft-deleted? → A: Dados preservados; queries filtram instâncias soft-deleted por padrão
- Q: Como os estados do provider se mapeiam para os estados persistidos? → A: O DB mantém 4 estados (`disconnected`, `connecting`, `connected`, `closed`). O provider retorna `connected`, `disconnected`, `connecting`, `not_found`. O `not_found` não é um estado de DB — indica instância inexistente no provider; o service layer decide a ação. O `closed` é estado terminal interno (instância encerrada no sistema: admin removeu ou instância permanentemente indisponível no provider). Instâncias `closed` são combinadas com soft-delete. Ver DT-046.

## Assumptions

- O PostgreSQL está disponível via Docker Compose (configurado na spec 001).
- A conexão com o banco será configurada via variável de ambiente `DATABASE_URL`.
- Os modelos ORM serão separados dos schemas Pydantic da API (conforme Constitution seção 4.1).
- O Redis não faz parte desta spec — será utilizado em specs futuras.
- A API Key e hash de autenticação serão adicionados ao modelo Client na spec 008 (Segurança via API Key).
- Os índices iniciais cobrirão consultas por cliente e por instância; otimizações adicionais serão feitas conforme necessidade real.
