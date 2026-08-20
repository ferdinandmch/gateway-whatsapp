# Feature Specification: Envio de Mensagens

**Feature Branch**: `005-message-sending`  
**Created**: 2026-08-18  
**Status**: Draft  
**Input**: User description: "Envio de mensagens de texto e mídia pelo backend próprio, utilizando a Evolution API como provider interno"

## Clarifications

### Session 2026-08-18

- Q: Quando o número de destino está em formato inválido, qual o comportamento? → A: Backend valida formato mínimo (só dígitos, 10-13 chars) e rejeita antes de chamar o provider.
- Q: Quando o provider retorna timeout ou está indisponível, qual o comportamento? → A: Falhar imediatamente, registrar como "failed" e retornar erro PROVIDER_ERROR ao cliente, sem retry.
- Q: Qual o timeout máximo para chamada HTTP ao provider? → A: 30 segundos.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Enviar mensagem de texto (Priority: P1)

Um cliente autenticado deseja enviar uma mensagem de texto para um número de WhatsApp usando uma instância conectada. O cliente informa o número de destino e o conteúdo da mensagem, e o backend encaminha a requisição ao provider, registra a tentativa e retorna o resultado.

**Why this priority**: É o caso de uso mais fundamental do sistema de mensageria — sem envio de texto, não há validação do fluxo principal.

**Independent Test**: Pode ser testado enviando uma requisição POST com instance_id, número de destino e mensagem, verificando que o backend registra a mensagem e retorna confirmação de envio.

**Acceptance Scenarios**:

1. **Given** um cliente autenticado com instância conectada, **When** envia POST /v1/messages/text com instance_id, to e message válidos, **Then** o sistema envia a mensagem via provider, registra no banco com status "sent" e retorna message_id e provider_message_id.
2. **Given** um cliente autenticado com instância desconectada, **When** tenta enviar mensagem de texto, **Then** o sistema retorna erro INSTANCE_DISCONNECTED sem chamar o provider.
3. **Given** um cliente autenticado, **When** envia mensagem com campos obrigatórios ausentes, **Then** o sistema retorna erro VALIDATION_ERROR.

---

### User Story 2 - Enviar mensagem de imagem (Priority: P2)

Um cliente autenticado deseja enviar uma imagem para um contato de WhatsApp, informando a URL da mídia e opcionalmente uma legenda.

**Why this priority**: Imagem é o tipo de mídia mais comum em mensageria e valida o fluxo de envio de mídia como um todo.

**Independent Test**: Pode ser testado enviando POST /v1/messages/image com media_url válida, verificando que o backend registra a mensagem com tipo "image" e retorna confirmação.

**Acceptance Scenarios**:

1. **Given** um cliente com instância conectada, **When** envia POST /v1/messages/image com instance_id, to e media_url válidos, **Then** o sistema envia a imagem via provider e registra com message_type "image".
2. **Given** um cliente com instância conectada, **When** envia imagem com caption, **Then** a legenda é incluída na mensagem enviada ao provider.
3. **Given** um cliente com instância conectada, **When** envia imagem sem media_url, **Then** o sistema retorna erro VALIDATION_ERROR.

---

### User Story 3 - Enviar áudio, documento e vídeo (Priority: P3)

Um cliente autenticado deseja enviar mídias de diferentes tipos (áudio, documento, vídeo) por meio do backend.

**Why this priority**: Completa a cobertura dos tipos de mídia previstos na V1, validando que o padrão de envio funciona para todos os formatos.

**Independent Test**: Pode ser testado enviando POST para cada endpoint (/v1/messages/audio, /v1/messages/document, /v1/messages/video) com payloads apropriados.

**Acceptance Scenarios**:

1. **Given** um cliente com instância conectada, **When** envia POST /v1/messages/audio com media_url válida, **Then** o sistema envia o áudio via provider e registra com message_type "audio".
2. **Given** um cliente com instância conectada, **When** envia POST /v1/messages/document com media_url e filename, **Then** o sistema envia o documento com o nome de arquivo correto.
3. **Given** um cliente com instância conectada, **When** envia POST /v1/messages/video com media_url e caption opcional, **Then** o sistema envia o vídeo via provider e registra com message_type "video".

---

### User Story 4 - Registro e rastreabilidade de envios (Priority: P2)

O sistema deve registrar toda tentativa de envio no banco de dados, permitindo rastreabilidade independentemente de sucesso ou falha.

**Why this priority**: Sem registro persistente, não há observabilidade sobre o que foi enviado, tornando depuração e auditoria impossíveis.

**Independent Test**: Pode ser testado verificando que após qualquer tentativa de envio (sucesso ou falha), existe um registro correspondente na tabela messages com os dados corretos.

**Acceptance Scenarios**:

1. **Given** um envio bem-sucedido, **When** consultado o banco, **Then** existe registro com direction "outbound", status "sent" e provider_message_id preenchido.
2. **Given** uma falha no provider durante envio, **When** consultado o banco, **Then** existe registro com status "failed" e o erro é registrado em error_logs.
3. **Given** um envio de mídia, **When** consultado o banco, **Then** o registro contém media_url, message_type correto e raw_payload da resposta do provider.

---

### Edge Cases

- Número de destino em formato inválido (não-dígitos ou comprimento fora de 10-13): sistema rejeita com VALIDATION_ERROR antes de chamar o provider.
- Provider retorna timeout (>30s) ou está indisponível: sistema registra mensagem como "failed" e retorna PROVIDER_ERROR, sem retry.
- Instância pertence a outro cliente: sistema retorna INSTANCE_NOT_FOUND (não revela existência para outro cliente).
- media_url inacessível ou inválida: na V1, URL é passada ao provider sem validação prévia; se o provider falhar, registra como "failed".
- Provider retorna erro desconhecido: sistema registra como "failed", salva raw_payload do erro em error_logs e retorna PROVIDER_ERROR.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Sistema DEVE permitir envio de mensagem de texto informando instance_id, número de destino e conteúdo textual.
- **FR-002**: Sistema DEVE permitir envio de imagem informando instance_id, número de destino e URL da mídia, com legenda opcional.
- **FR-003**: Sistema DEVE permitir envio de áudio informando instance_id, número de destino e URL da mídia.
- **FR-004**: Sistema DEVE permitir envio de documento informando instance_id, número de destino, URL da mídia e nome do arquivo, com legenda opcional.
- **FR-005**: Sistema DEVE permitir envio de vídeo informando instance_id, número de destino e URL da mídia, com legenda opcional.
- **FR-006**: Sistema DEVE validar que a instância informada pertence ao cliente autenticado antes de prosseguir com o envio.
- **FR-007**: Sistema DEVE validar que a instância está com status "connected" antes de chamar o provider.
- **FR-008**: Sistema DEVE normalizar o número de destino para o formato aceito pelo provider (código do país + DDD + número). Deve validar formato mínimo (apenas dígitos, comprimento entre 10-13 caracteres) e rejeitar com VALIDATION_ERROR antes de chamar o provider.
- **FR-009**: Sistema DEVE registrar toda tentativa de envio na tabela messages, independentemente de sucesso ou falha.
- **FR-010**: Sistema DEVE registrar o status inicial da mensagem como "pending" e atualizar para "sent" ou "failed" conforme resposta do provider.
- **FR-011**: Sistema DEVE armazenar o provider_message_id retornado pelo provider quando disponível.
- **FR-012**: Sistema DEVE registrar erros de envio na tabela error_logs com payload relevante da falha.
- **FR-013**: Sistema DEVE retornar erros padronizados conforme formato definido (code, message, details).
- **FR-014**: Sistema DEVE validar campos obrigatórios antes de chamar o provider, retornando VALIDATION_ERROR quando inválidos.
- **FR-015**: Sistema DEVE usar timeout de 30 segundos para chamadas HTTP ao provider. Se excedido, registra mensagem como "failed" e retorna PROVIDER_ERROR.
- **FR-016**: Sistema NÃO DEVE realizar retry automático em caso de falha do provider na V1. A mensagem é marcada como "failed" imediatamente.

### Key Entities

- **Message**: Representa uma tentativa de envio de mensagem. Atributos principais: id, instance_id, direction (outbound), content_type (text/image/audio/document/video), body, remote_jid, media_url, filename, status (pending/sent/failed), provider_message_id, raw_payload, created_at. O client é derivado via instance (sem FK direta).
- **Instance**: Instância de WhatsApp já existente no sistema. Relação: uma mensagem pertence a uma instância.
- **Client**: Cliente autenticado dono da instância. Relação: uma mensagem pertence a um cliente.
- **ErrorLog**: Registro de falha quando o envio falha. Atributos: referência à mensagem, payload de erro, timestamp.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Clientes conseguem enviar mensagens de texto com sucesso em menos de 5 segundos após a requisição.
- **SC-002**: Clientes conseguem enviar os 4 tipos de mídia (imagem, áudio, documento, vídeo) com sucesso.
- **SC-003**: 100% das tentativas de envio são registradas no banco, incluindo falhas.
- **SC-004**: Quando a instância não está conectada, o sistema bloqueia o envio sem chamar o provider em 100% dos casos.
- **SC-005**: Quando campos obrigatórios estão ausentes, o sistema retorna erro de validação sem chamar o provider.
- **SC-006**: O número de destino é normalizado corretamente para o formato internacional em 100% dos envios.

## Assumptions

- A instância já foi criada e conectada por meio dos endpoints de gestão de instâncias (spec 004).
- O provider (Evolution API) está disponível e configurado corretamente no ambiente.
- A autenticação por API Key já está implementada ou será implementada em spec separada (spec 008); para esta spec, assume-se que o client_id é derivável da requisição autenticada.
- As tabelas messages e error_logs já existem conforme modelagem da spec 003.
- O formato de número brasileiro é o padrão inicial (código país 55 + DDD + número), com possibilidade de extensão futura para outros países.
- Na V1, não há fila de envio — as mensagens são enviadas de forma síncrona ao provider e o resultado é retornado ao cliente.
- Na V1, não há validação de acessibilidade da media_url; a URL é passada diretamente ao provider.
- Na V1, não há retry automático — falhas são imediatas e definitivas.
- Timeout de 30 segundos para chamadas ao provider cobre cenários de envio de mídia sem bloquear excessivamente o cliente.
