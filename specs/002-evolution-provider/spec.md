# Feature Specification: Provider Evolution API

**Feature Branch**: `002-evolution-provider`  
**Created**: 2026-08-16  
**Status**: Draft  
**Input**: User description: "spec 002 — Provider Evolution API"

## User Scenarios & Testing

### User Story 1 - Enviar mensagem de texto via provider (Priority: P1)

O desenvolvedor (ou serviço de aplicação) solicita o envio de uma mensagem de texto para um número WhatsApp através da camada de provider. O provider encapsula toda a comunicação com a Evolution API, devolvendo um resultado normalizado.

**Why this priority**: O envio de mensagens de texto é a operação mais fundamental do gateway. Validar que a abstração do provider funciona corretamente para esta operação desbloqueia todos os demais formatos e garante o desacoplamento da Evolution API.

**Independent Test**: Chamar o método de envio de texto do provider com um número e conteúdo, verificar que a comunicação com a Evolution API é feita corretamente e que o resultado retornado segue o formato interno do sistema.

**Acceptance Scenarios**:

1. **Given** uma instância conectada ao WhatsApp, **When** o serviço solicita envio de texto com número e conteúdo válidos, **Then** o provider chama a Evolution API, retorna o identificador da mensagem no provider e status de sucesso.
2. **Given** uma instância conectada, **When** a Evolution API retorna erro (timeout, 500, etc.), **Then** o provider retorna um resultado de falha com informações suficientes para diagnóstico, sem expor detalhes internos da Evolution API para camadas superiores.
3. **Given** um número de telefone em formato não-padrão, **When** o envio é solicitado, **Then** o provider normaliza o número antes de enviar à Evolution API.

---

### User Story 2 - Enviar mensagem de mídia via provider (Priority: P1)

O serviço solicita envio de uma mensagem de mídia (imagem, áudio, documento ou vídeo) via provider. O provider trata as especificidades de cada tipo conforme a Evolution API exige.

**Why this priority**: Suporte a mídia é requisito da V1 e compartilha a mesma infraestrutura do envio de texto. Implementá-lo junto garante cobertura completa dos formatos definidos.

**Independent Test**: Chamar o método de envio de mídia para cada formato suportado (imagem, áudio, documento, vídeo), verificar que o payload correto é enviado à Evolution API e o resultado é normalizado.

**Acceptance Scenarios**:

1. **Given** uma instância conectada, **When** o serviço solicita envio de imagem com URL e legenda opcional, **Then** o provider envia o payload correto e retorna resultado normalizado.
2. **Given** uma instância conectada, **When** o serviço solicita envio de áudio com URL, **Then** o provider envia no formato esperado pela Evolution API.
3. **Given** uma instância conectada, **When** o serviço solicita envio de documento com URL e nome de arquivo, **Then** o provider envia corretamente e retorna resultado normalizado.
4. **Given** uma instância conectada, **When** o serviço solicita envio de vídeo com URL e legenda opcional, **Then** o provider envia corretamente e retorna resultado normalizado.
5. **Given** qualquer envio de mídia, **When** a Evolution API retorna erro, **Then** o provider retorna resultado de falha uniforme, seguindo a mesma política de falha imediata do envio de texto.

---

### User Story 3 - Verificar status de conexão de uma instância (Priority: P2)

O serviço consulta o provider para saber se uma instância específica está conectada, desconectada ou em processo de conexão.

**Why this priority**: Saber o estado da instância é pré-requisito para operações seguras de envio e para exibir status ao usuário final.

**Independent Test**: Chamar o método de status do provider com um nome de instância, verificar que o status retornado é normalizado para valores internos do sistema.

**Acceptance Scenarios**:

1. **Given** uma instância existente na Evolution API, **When** o serviço consulta o status, **Then** o provider retorna o estado normalizado como um dos 4 valores internos: `connected`, `disconnected`, `connecting`, `not_found`.
2. **Given** uma instância que não existe na Evolution API, **When** o serviço consulta o status, **Then** o provider retorna estado `not_found`.

---

### User Story 4 - Criar instância no provider (Priority: P2)

O serviço solicita ao provider a criação de uma nova instância WhatsApp na Evolution API, com configurações adequadas (incluindo webhook).

**Why this priority**: Criar instâncias é o primeiro passo do ciclo de vida. Sem isso, não há como conectar ou enviar mensagens.

**Independent Test**: Chamar o método de criação de instância com nome e configuração de webhook, verificar que a Evolution API é chamada corretamente e o resultado é normalizado.

**Acceptance Scenarios**:

1. **Given** um nome de instância válido, **When** o serviço solicita criação, **Then** o provider constrói automaticamente a URL de webhook (`{WEBHOOK_BASE_URL}/v1/webhooks/evolution/{instance_name}`), cria a instância na Evolution API e retorna o resultado normalizado com identificação da instância.
2. **Given** um nome de instância que já existe na Evolution API, **When** o serviço solicita criação, **Then** o provider retorna erro indicando duplicidade.

---

### User Story 5 - Conectar e desconectar instância (Priority: P2)

O serviço solicita ao provider que inicie o processo de conexão (gerar QR code ou pairing code) ou que desconecte/faça logout de uma instância.

**Why this priority**: Conexão e desconexão são operações essenciais no ciclo de vida de uma instância WhatsApp.

**Independent Test**: Chamar os métodos de conexão e desconexão do provider, verificar que os dados de conexão (QR code/pairing code) são retornados corretamente e que o logout é executado.

**Acceptance Scenarios**:

1. **Given** uma instância criada mas desconectada, **When** o serviço solicita conexão, **Then** o provider retorna os dados necessários para pareamento (QR code ou código de pareamento).
2. **Given** uma instância conectada, **When** o serviço solicita desconexão, **Then** o provider executa logout na Evolution API e retorna confirmação.
3. **Given** uma instância que não existe, **When** o serviço solicita conexão, **Then** o provider retorna erro indicando instância não encontrada.

---

### User Story 6 - Deletar instância no provider (Priority: P3)

O serviço solicita ao provider a remoção completa de uma instância na Evolution API.

**Why this priority**: Necessário para limpeza e gerenciamento, mas menos frequente que criação e conexão.

**Independent Test**: Chamar o método de deleção do provider e verificar que a instância é removida na Evolution API.

**Acceptance Scenarios**:

1. **Given** uma instância existente, **When** o serviço solicita deleção, **Then** o provider remove a instância na Evolution API e retorna confirmação.
2. **Given** uma instância inexistente, **When** o serviço solicita deleção, **Then** o provider retorna erro indicando não encontrada.

---

### Edge Cases

- O que acontece quando a Evolution API está completamente indisponível (connection refused)?
- Como o provider se comporta quando recebe um payload inesperado da Evolution API?
- O que acontece quando o timeout HTTP é atingido durante uma operação?
- Como o provider lida com respostas da Evolution API em formato inesperado ou com campos faltando?
- O que acontece quando o número de telefone contém caracteres inválidos?
- O que acontece quando a `media_url` fornecida é inválida ou inacessível? (Evolution API retorna 400 → provider mapeia para INVALID_REQUEST)

## Requirements

### Functional Requirements

- **FR-001**: O sistema DEVE possuir uma interface abstrata `MessagingProvider` que define o contrato para todas as operações de mensageria.
- **FR-002**: O sistema DEVE possuir uma implementação `EvolutionProvider` que realize todas as operações via Evolution API HTTP.
- **FR-003**: O provider DEVE suportar envio de mensagens nos formatos: texto, imagem, áudio, documento e vídeo.
- **FR-004**: O provider DEVE normalizar números de telefone antes de enviá-los à Evolution API (remover caracteres especiais, garantir formato esperado).
- **FR-005**: O provider DEVE retornar resultados em formato interno próprio, nunca expondo payloads brutos da Evolution API para camadas superiores.
- **FR-006**: O provider DEVE preservar o identificador de mensagem retornado pela Evolution API para fins de reconciliação.
- **FR-007**: O provider DEVE implementar política de falha imediata — sem retry automático. Erros são retornados ao chamador com informações de diagnóstico.
- **FR-008**: O provider DEVE suportar operações de ciclo de vida de instância: criar, verificar status, conectar, desconectar e deletar.
- **FR-009**: O provider DEVE utilizar HTTPX como cliente HTTP para comunicação com a Evolution API.
- **FR-010**: O provider DEVE respeitar um timeout configurável para chamadas HTTP (padrão definido em configuração do sistema).
- **FR-011**: O provider DEVE mapear erros da Evolution API para tipos de erro internos, sem expor detalhes do provider.
- **FR-012**: O provider DEVE ser instanciável com configuração de URL base e chave de API da Evolution API.
- **FR-013**: A interface do provider DEVE permitir testes sem depender de uma instância real da Evolution API (testável via mocks).
- **FR-014**: Cada funcionalidade implementada no provider DEVE possuir testes unitários que cubram os cenários de sucesso, falha e edge cases definidos nas acceptance scenarios.

### Key Entities

- **MessagingProvider**: Interface abstrata que define o contrato de todas as operações de mensageria (envio, instâncias, status). Ponto de extensão para futuros providers.
- **EvolutionProvider**: Implementação concreta do MessagingProvider que se comunica com a Evolution API via HTTP. Encapsula endpoints, payloads e mapeamento de erros.
- **ProviderResult**: Representação interna do resultado de uma operação no provider (sucesso/falha, dados normalizados, erro mapeado).
- **ProviderError**: Representação interna de erros do provider, com código próprio e mensagem — sem expor detalhes da Evolution API.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Todas as operações de envio (texto, imagem, áudio, documento, vídeo) podem ser executadas com sucesso em menos de 5 segundos em condições normais de rede.
- **SC-002**: Camadas superiores (services, routes) não possuem nenhuma referência direta a endpoints, payloads ou códigos de erro específicos da Evolution API.
- **SC-003**: 100% das operações do provider podem ser testadas unitariamente sem conexão real à Evolution API.
- **SC-004**: Erros da Evolution API são mapeados para representações internas em 100% dos cenários previstos, sem vazamento de detalhes internos do provider.
- **SC-005**: A substituição futura do provider por outra implementação exigiria apenas a criação de uma nova classe que implemente a interface, sem alteração em services ou routes.

## Clarifications

### Session 2026-08-16

- Q: Quais estados internos o sistema deve reconhecer para uma instância? → A: 4 estados: `connected`, `disconnected`, `connecting`, `not_found`
- Q: Como a URL de webhook deve ser determinada ao criar instância? → A: Construída automaticamente por instância a partir de base configurável (`{WEBHOOK_BASE_URL}/v1/webhooks/evolution/{instance_name}`)

## Assumptions

- A Evolution API está disponível no ambiente local via Docker Compose (já configurado na spec 001).
- A versão utilizada da Evolution API é v2.3.4, conforme fixado no Docker Compose.
- O provider será utilizado exclusivamente por services internos — nunca diretamente por rotas da API.
- A normalização de números de telefone segue o padrão: remover espaços, parênteses, hifens; manter apenas dígitos e o prefixo "+".
- O provider receberá configuração (URL e API Key da Evolution API) via injeção de dependência a partir das settings do sistema.
- Redis não será utilizado pelo provider na V1 (conforme DT-042).
- Retry automático não será implementado na V1 (conforme DT-036).
