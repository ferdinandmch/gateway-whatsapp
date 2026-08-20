# Feature Specification: Segurança com API Key

**Feature Branch**: `008-api-key-security`  
**Created**: 2026-08-19  
**Status**: Draft  
**Input**: User description: "Proteger os endpoints públicos do backend com autenticação por API Key"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Validação de requisição autenticada (Priority: P1)

Um cliente externo realiza uma requisição a qualquer endpoint protegido incluindo sua API Key no header `X-API-Key`. O sistema valida a chave, identifica o cliente associado e permite o acesso ao recurso.

**Why this priority**: Sem autenticação funcional, todos os endpoints públicos ficam abertos. Este é o mecanismo central de segurança da V1.

**Independent Test**: Pode ser testado enviando uma requisição com API Key válida a qualquer rota protegida e verificando que a resposta é bem-sucedida com o contexto do cliente correto.

**Acceptance Scenarios**:

1. **Given** um cliente com API Key válida, **When** envia requisição com header `X-API-Key` correto para `/v1/instances`, **Then** a requisição é processada normalmente e o cliente é identificado.
2. **Given** uma requisição sem header `X-API-Key`, **When** enviada para qualquer rota protegida, **Then** o sistema retorna erro 401 com mensagem clara.
3. **Given** uma requisição com API Key inválida ou inexistente, **When** enviada para qualquer rota protegida, **Then** o sistema retorna erro 401.

---

### User Story 2 - Geração de API Key para cliente (Priority: P1)

O sistema gera uma API Key única para um cliente no momento da criação. A chave é apresentada ao administrador uma única vez e armazenada internamente como hash.

**Why this priority**: Sem mecanismo de geração de chaves, não há como autenticar clientes. É pré-requisito da User Story 1.

**Independent Test**: Pode ser testado criando um novo cliente e verificando que uma API Key é retornada na resposta, e que requisições subsequentes com essa chave são aceitas.

**Acceptance Scenarios**:

1. **Given** uma solicitação de criação de cliente, **When** o cliente é criado com sucesso, **Then** uma API Key única é gerada e retornada na resposta.
2. **Given** uma API Key gerada, **When** consultada no banco de dados, **Then** apenas o hash da chave está armazenado (nunca o valor em texto plano).
3. **Given** uma API Key gerada, **When** utilizada em requisições futuras, **Then** o sistema consegue validar a chave comparando com o hash armazenado.

---

### User Story 3 - Proteção do webhook da Evolution API (Priority: P2)

O endpoint de webhook que recebe eventos da Evolution API é protegido por um segredo compartilhado, impedindo que terceiros enviem payloads falsos ao backend.

**Why this priority**: Sem proteção no webhook, qualquer pessoa que descubra a URL pode injetar eventos falsos no sistema. É crítico para integridade, porém secundário à autenticação de clientes.

**Independent Test**: Pode ser testado enviando requisições ao endpoint de webhook com e sem o segredo correto, verificando que apenas requisições autorizadas são processadas.

**Acceptance Scenarios**:

1. **Given** uma requisição ao endpoint de webhook com segredo válido, **When** processada, **Then** o evento é aceito e processado normalmente.
2. **Given** uma requisição ao endpoint de webhook sem segredo ou com segredo inválido, **When** recebida, **Then** o sistema retorna erro 401 e não processa o evento.

---

### User Story 4 - Isolamento entre API Key externa e token interno (Priority: P2)

O token utilizado para comunicação com a Evolution API é mantido como configuração interna do servidor e nunca exposto aos clientes externos. A API Key do cliente é completamente independente do token interno.

**Why this priority**: Garante que a segurança interna do provider não seja comprometida mesmo se uma API Key de cliente for vazada.

**Independent Test**: Pode ser testado verificando que nenhuma resposta da API expõe o token interno e que o comprometimento de uma API Key não dá acesso ao token do provider.

**Acceptance Scenarios**:

1. **Given** um cliente autenticado, **When** consulta qualquer endpoint da API, **Then** nenhuma resposta contém o token interno da Evolution API.
2. **Given** o token interno da Evolution API, **When** utilizado como valor no header `X-API-Key`, **Then** o sistema rejeita a autenticação (são domínios independentes).

---

### Edge Cases

- Quando um cliente desativado tenta usar sua API Key, o sistema retorna 401 idêntico ao de chave inexistente (sem revelar existência).
- Como o sistema se comporta quando múltiplas requisições simultâneas usam a mesma API Key?
- O que acontece se o header `X-API-Key` estiver presente mas com valor vazio?
- Como o sistema responde se o algoritmo de hash não conseguir processar (falha interna)?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema DEVE validar o header `X-API-Key` em todas as rotas protegidas (`/v1/instances/*`, `/v1/messages/*`, `/v1/logs/*`).
- **FR-002**: O sistema DEVE retornar erro 401 (Unauthorized) quando a API Key estiver ausente, vazia ou inválida.
- **FR-003**: O sistema DEVE gerar API Keys únicas e criptograficamente seguras no formato `zapi_` + 32 caracteres hexadecimais aleatórios.
- **FR-004**: O sistema DEVE armazenar API Keys apenas como hash (nunca em texto plano).
- **FR-005**: O sistema DEVE identificar o cliente associado à API Key validada e disponibilizar essa informação para os handlers das rotas.
- **FR-006**: O sistema DEVE proteger o endpoint de webhook da Evolution API com um segredo compartilhado configurável.
- **FR-007**: O sistema DEVE manter separação completa entre API Keys de clientes e o token interno de comunicação com a Evolution API.
- **FR-008**: O sistema DEVE permitir que um cliente possua uma API Key ativa por vez.
- **FR-009**: O sistema DEVE retornar a API Key em texto plano apenas uma vez, no momento da criação do cliente.
- **FR-010**: O sistema NÃO DEVE expor o token interno da Evolution API em nenhuma resposta da API pública.
- **FR-011**: O sistema DEVE proteger o endpoint de criação de clientes (`/v1/clients`) com um token administrativo no header `X-Admin-Token`, configurado via variável de ambiente `ADMIN_TOKEN`.
- **FR-012**: O token administrativo DEVE ser independente das API Keys de clientes e do token interno da Evolution API.

### Key Entities

- **Client (Cliente)**: Entidade que possui uma API Key associada. Representa o consumidor externo da API. Atributos principais: identificador, nome, hash da API Key, status (ativo/inativo), data de criação.
- **API Key**: Credencial de acesso do cliente. Formato: `zapi_` + 32 hex chars. Gerada pelo sistema, apresentada uma vez, armazenada como hash. Vinculada a exatamente um cliente.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% das rotas protegidas rejeitam requisições sem API Key válida.
- **SC-002**: Clientes autenticados conseguem acessar os recursos em menos de 200ms adicionais de overhead por validação.
- **SC-003**: Nenhuma API Key é armazenada em texto plano no sistema.
- **SC-004**: O endpoint de webhook rejeita 100% das requisições sem segredo válido.
- **SC-005**: O token interno da Evolution API não aparece em nenhuma resposta da API pública.

## Clarifications

### Session 2026-08-19

- Q: Como o endpoint de criação de clientes é protegido (bootstrap)? → A: Endpoint `/v1/clients` protegido por token administrativo separado (variável de ambiente), independente das API Keys de clientes.
- Q: Qual o comportamento quando um cliente desativado tenta usar sua API Key? → A: Retornar 401 idêntico a chave inexistente (não revelar existência da chave).
- Q: Qual o formato da API Key? → A: Prefixo identificável `zapi_` + 32 caracteres hexadecimais aleatórios (ex: `zapi_a3f8b2c1d4e5f6a7b8c9d0e1f2a3b4c5`).
- Q: Qual o nome do header para token administrativo? → A: `X-Admin-Token`.

## Assumptions

- A tabela `clients` já existe no banco (criada na spec 003) e será estendida com campos de API Key.
- O hash será feito com algoritmo adequado para credenciais (bcrypt, argon2 ou similar definido na implementação).
- A criação de clientes será feita via endpoint `/v1/clients` protegido por token admin (variável de ambiente), sem necessidade de interface visual.
- O segredo do webhook da Evolution API será configurado via variável de ambiente.
- Não há necessidade de rotação automática de API Keys na V1 (pode ser feita manualmente recriando o cliente).
- Rate limiting e throttling estão fora do escopo desta spec.

## Scope Boundaries

### Incluído

- Validação de API Key por header em rotas protegidas
- Geração e armazenamento seguro de API Keys
- Proteção do webhook com segredo compartilhado
- Identificação do cliente nas requisições autenticadas
- Separação entre credenciais externas e internas

### Excluído

- Login com usuário e senha
- Painel administrativo
- OAuth / OAuth2
- JWT para usuários finais
- Permissões por papel (RBAC)
- Multiusuário (múltiplos usuários por cliente)
- Autenticação social
- Recuperação de senha
- Rotação automática de API Keys
- Rate limiting / throttling
