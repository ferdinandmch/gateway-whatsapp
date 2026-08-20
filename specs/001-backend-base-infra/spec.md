# Feature Specification: Base do Backend e Infraestrutura Local

**Feature Branch**: `001-backend-base-infra`
**Created**: 2026-08-15
**Status**: Draft
**Input**: User description: "001 — Base do backend e infraestrutura local"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Subir ambiente local completo (Priority: P1)

Um desenvolvedor clona o repositório e deseja executar todo o ambiente localmente com um único comando para começar a trabalhar no projeto.

**Why this priority**: Sem o ambiente local funcional, nenhuma outra spec pode ser desenvolvida ou testada. Esta é a fundação de todo o projeto.

**Independent Test**: Executar `docker compose up` e verificar que todos os 5 serviços sobem com sucesso (backend, postgres, redis, n8n, evolution-api) e respondem em suas respectivas portas.

**Acceptance Scenarios**:

1. **Given** o repositório clonado e `.env` configurado a partir do `.env.example`, **When** o desenvolvedor executa `docker compose up`, **Then** todos os 5 serviços iniciam sem erros e ficam acessíveis nas portas configuradas.
2. **Given** o ambiente rodando, **When** o desenvolvedor para e reinicia os serviços, **Then** os dados persistidos no PostgreSQL são mantidos entre reinicializações.
3. **Given** o ambiente rodando, **When** o desenvolvedor executa `docker compose down`, **Then** todos os serviços são encerrados de forma limpa.

---

### User Story 2 - Verificar saúde do backend (Priority: P1)

Um desenvolvedor ou sistema de monitoramento deseja verificar se o backend está respondendo corretamente após subir o ambiente.

**Why this priority**: O health check é o primeiro endpoint funcional do sistema e valida que o backend FastAPI está operacional.

**Independent Test**: Enviar `GET /health` e receber resposta 200 com status "ok", nome do serviço e versão.

**Acceptance Scenarios**:

1. **Given** o backend rodando, **When** uma requisição `GET /health` é feita, **Then** a resposta é `200 OK` com corpo `{"status": "ok", "service": "whatsapp-gateway", "version": "0.1.0"}`.
2. **Given** o backend rodando, **When** uma requisição `GET /health` é feita sem headers de autenticação, **Then** a resposta é retornada normalmente (endpoint público).

---

### User Story 3 - Configurar variáveis de ambiente (Priority: P2)

Um desenvolvedor deseja configurar o projeto para seu ambiente local usando um arquivo de exemplo como referência.

**Why this priority**: A configuração por variáveis de ambiente é essencial para segurança e reprodutibilidade, mas depende da infraestrutura base já existir.

**Independent Test**: Copiar `.env.example` para `.env`, ajustar valores e verificar que o backend carrega todas as variáveis sem erros na inicialização.

**Acceptance Scenarios**:

1. **Given** o arquivo `.env.example` presente no repositório, **When** o desenvolvedor copia para `.env`, **Then** todas as variáveis necessárias estão documentadas com valores de exemplo.
2. **Given** uma variável obrigatória ausente no `.env`, **When** o backend tenta iniciar, **Then** uma mensagem de erro clara indica qual variável está faltando.
3. **Given** o `.env` corretamente preenchido, **When** o backend inicia, **Then** todas as configurações são carregadas e o serviço opera normalmente.

---

### User Story 4 - Acessar documentação automática da API (Priority: P3)

Um desenvolvedor deseja visualizar a documentação OpenAPI gerada automaticamente pelo FastAPI para entender os endpoints disponíveis.

**Why this priority**: Útil para desenvolvimento mas não bloqueia outras funcionalidades.

**Independent Test**: Acessar `/docs` no navegador e ver a interface Swagger funcional.

**Acceptance Scenarios**:

1. **Given** o backend rodando, **When** o desenvolvedor acessa `/docs`, **Then** a interface Swagger é exibida com o endpoint `/health` documentado.
2. **Given** o backend rodando, **When** o desenvolvedor acessa `/redoc`, **Then** a documentação ReDoc é exibida.

---

### Edge Cases

- O que acontece se o PostgreSQL não estiver acessível quando o backend inicia?
- O que acontece se a porta configurada já estiver em uso por outro processo?
- O que acontece se o Docker Compose não encontrar a imagem da Evolution API na versão especificada?
- O que acontece se o arquivo `.env` não existir ao tentar iniciar o backend?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema DEVE fornecer um `docker-compose.yml` funcional que orquestre 5 serviços: backend, postgres, redis, n8n e evolution-api.
- **FR-002**: O sistema DEVE fornecer um `Dockerfile` para o backend que permita build e execução da aplicação.
- **FR-003**: O sistema DEVE expor um endpoint `GET /health` público que retorne o status da aplicação sem exigir autenticação.
- **FR-004**: O sistema DEVE carregar configurações a partir de variáveis de ambiente, validando sua presença na inicialização.
- **FR-005**: O sistema DEVE fornecer um arquivo `.env.example` documentando todas as variáveis obrigatórias com valores de exemplo.
- **FR-006**: O sistema DEVE inicializar um logger estruturado para registrar eventos da aplicação.
- **FR-007**: O sistema DEVE gerar documentação OpenAPI automaticamente acessível em `/docs` e `/redoc`.
- **FR-008**: O sistema DEVE estruturar o projeto seguindo a organização de pastas definida na arquitetura (api, services, providers, models, schemas, core).
- **FR-009**: O sistema DEVE configurar o `pyproject.toml` com as dependências base do projeto.
- **FR-010**: O sistema DEVE fixar a versão da Evolution API em `v2.3.4` no Docker Compose.
- **FR-011**: O sistema DEVE possuir testes unitários cobrindo configuração, logging, health check, validação de startup e documentação OpenAPI.

### Key Entities

- **Configuração da Aplicação**: Representação das variáveis de ambiente obrigatórias (DATABASE_URL, REDIS_URL, EVOLUTION_API_URL, EVOLUTION_API_KEY, WEBHOOK_SECRET, API_KEY_SALT, N8N_DEFAULT_WEBHOOK_URL, APP_ENV, LOG_LEVEL, APP_PORT, HTTP_TIMEOUT).
- **Serviço Docker**: Cada serviço orquestrado (backend na porta 8000, postgres na 5432, redis na 6379, n8n na 5678, evolution-api na 8080).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: O ambiente local completo sobe com um único comando em menos de 2 minutos (após build inicial).
- **SC-002**: O endpoint `/health` responde com status 200 em menos de 100ms após o backend estar pronto.
- **SC-003**: Todos os 5 serviços do Docker Compose reportam status "healthy" ou "running" simultaneamente.
- **SC-004**: O backend rejeita a inicialização com mensagem clara quando qualquer variável obrigatória está ausente.
- **SC-005**: A documentação OpenAPI em `/docs` exibe pelo menos o endpoint `/health` com schema de resposta.
- **SC-006**: O projeto inicia sem erros usando `uv` para gerenciamento de dependências.
- **SC-007**: Todos os testes unitários passam com `pytest` sem falhas.

## Assumptions

- O desenvolvedor possui Docker e Docker Compose instalados localmente.
- O desenvolvedor possui `uv` instalado para gerenciamento de dependências Python.
- A rede local permite download das imagens Docker necessárias.
- As portas padrão (8000, 5432, 6379, 5678, 8080) estão disponíveis na máquina do desenvolvedor.
- O foco desta spec é apenas a infraestrutura base — nenhuma lógica de negócio, autenticação, persistência de dados ou integração funcional é implementada aqui.
- O backend nesta spec não se conecta ativamente ao PostgreSQL, Redis ou Evolution API — apenas garante que os serviços estão disponíveis na rede Docker.
