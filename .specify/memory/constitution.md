<!--
  Sync Impact Report
  ==================
  Version change: 0.0.0 (template) → 1.0.0
  Modified principles: N/A (initial ratification)
  Added sections: 22 sections (Propósito through Regra Final)
  Removed sections: All template placeholders replaced
  Templates requiring updates:
    - .specify/templates/plan-template.md ✅ aligned (Constitution Check section present)
    - .specify/templates/spec-template.md ✅ aligned (user stories, requirements, success criteria)
    - .specify/templates/tasks-template.md ✅ aligned (phased delivery, test-first optional)
  Follow-up TODOs: None
-->

# WhatsApp Gateway Constitution

## 1. Propósito

O projeto tem como objetivo construir uma API própria para integração com WhatsApp, funcionando como uma camada intermediária entre consumidores externos, o backend da aplicação, um provider de mensageria e o WhatsApp.

Na V1, a Evolution API será utilizada como provider de mensageria.

A API própria não deve expor a Evolution API diretamente aos consumidores.

Fluxo principal:

```txt
Cliente / Sistema externo
        ↓
API própria
        ↓
Backend
        ↓
Provider de mensageria
        ↓
Evolution API
        ↓
WhatsApp
```

Fluxo de recebimento de eventos:

```txt
WhatsApp
    ↓
Evolution API
    ↓
Backend
    ↓
n8n
```

## 2. Princípios Fundamentais

### 2.1 Backend próprio como camada central

O backend próprio é a camada central de controle do sistema.

Consumidores externos DEVEM utilizar a API própria e NÃO DEVEM depender diretamente da Evolution API.

Isso permite manter sob controle do projeto:

- autenticação;
- contratos da API;
- regras de negócio;
- persistência;
- normalização de dados;
- controle de acesso;
- integração com outros sistemas.

### 2.2 Desacoplamento do provider

A Evolution API DEVE ser tratada como provider, e NÃO como parte do domínio da aplicação.

A comunicação com o provider DEVE ser realizada através de uma abstração própria.

A V1 terá uma implementação para a Evolution API.

Conceitualmente:

```txt
Application
    ↓
MessagingProvider
    ↓
EvolutionProvider
    ↓
Evolution API
```

Regras de negócio NÃO DEVEM depender diretamente de endpoints, payloads, estados ou códigos de erro específicos da Evolution API.

### 2.3 Contratos próprios

A API DEVE possuir contratos próprios para entrada e saída de dados.

Payloads recebidos do provider DEVEM ser convertidos para modelos internos quando necessário.

Payloads enviados aos consumidores DEVEM seguir os contratos da API própria.

A Evolution API NÃO DEVE definir diretamente o contrato público da aplicação.

### 2.4 Evolução do provider

A arquitetura DEVE permitir uma futura substituição ou adição de providers sem exigir reescrita das regras centrais do domínio.

A abstração DEVE ser suficiente para desacoplar o domínio do provider atual, sem criar uma arquitetura genérica desnecessária para providers que ainda não existem.

## 3. Arquitetura

### 3.1 Monólito modular na V1

A V1 será construída como um backend único e modular.

NÃO serão utilizados microserviços como requisito inicial da V1.

A aplicação DEVE manter separação clara entre responsabilidades, incluindo:

- API;
- serviços de aplicação;
- domínio;
- providers;
- persistência;
- infraestrutura.

A estrutura interna poderá evoluir sem violar essa separação de responsabilidades.

### 3.2 Separação entre API, aplicação e infraestrutura

As rotas da API DEVEM permanecer responsáveis por receber requisições, validar entradas, autenticar, chamar os casos de uso apropriados e retornar respostas.

As regras de negócio DEVEM permanecer nos serviços e no domínio.

Integrações externas DEVEM permanecer isoladas em suas respectivas camadas.

## 4. Stack

A stack definida para a V1 é:

- Python;
- FastAPI;
- Pydantic;
- SQLAlchemy;
- Alembic;
- PostgreSQL;
- Redis;
- HTTPX;
- Evolution API;
- n8n;
- Docker Compose;
- pytest;
- pytest-asyncio;
- uv.

Novas tecnologias ou dependências relevantes DEVEM possuir justificativa antes de serem incorporadas ao projeto.

### 4.1 SQLAlchemy e Pydantic

A V1 utilizará:

- SQLAlchemy para persistência e ORM;
- Pydantic para schemas, validação e contratos de dados.

SQLModel NÃO será utilizado na V1.

Modelos ORM e schemas públicos DEVEM permanecer separados:

```txt
SQLAlchemy Model ≠ Pydantic Schema
```

### 4.2 PostgreSQL

O PostgreSQL será o banco principal e a fonte persistente de verdade da aplicação.

O Redis NÃO substitui o PostgreSQL como armazenamento persistente principal.

### 4.3 Migrations

Alterações estruturais no banco DEVEM ser realizadas através de migrations do Alembic.

Alterações de schema DEVEM ser reproduzíveis e versionadas.

## 5. Segurança

### 5.1 Autenticação da API

A autenticação da API pública da V1 será baseada em API Key.

A chave será associada ao cliente consumidor.

A API Key original NÃO DEVE ser armazenada em texto puro. DEVE ser armazenada de forma protegida, utilizando hash.

### 5.2 Segredos

Segredos e credenciais DEVEM ser fornecidos por configuração ou variáveis de ambiente.

NÃO DEVEM ser armazenados no código-fonte ou versionados no Git.

Exemplos de configurações sensíveis incluem:

- DATABASE_URL
- REDIS_URL
- EVOLUTION_API_URL
- EVOLUTION_API_KEY
- WEBHOOK_SECRET
- N8N_*

### 5.3 Isolamento entre clientes

Recursos pertencentes a um cliente NÃO DEVEM ser acessíveis por outro cliente.

O controle de acesso DEVE ser realizado no backend e NÃO PODE depender apenas de identificadores fornecidos pelo consumidor.

## 6. Webhooks e Eventos

### 6.1 Webhooks como entrada externa

Webhooks provenientes da Evolution API DEVEM ser tratados como entrada externa não confiável até que sua autenticidade e estrutura sejam validadas.

### 6.2 Autenticação de webhooks

Os webhooks da Evolution API DEVEM utilizar um segredo próprio para autenticação.

Webhooks inválidos NÃO DEVEM ser processados nem encaminhados ao n8n.

### 6.3 Persistência de eventos

Eventos recebidos DEVEM ser persistidos antes de serem considerados processados.

Quando apropriado, o payload recebido DEVE ser preservado para permitir diagnóstico e reprocessamento.

### 6.4 Normalização

O n8n NÃO DEVE depender diretamente do formato da Evolution API.

O backend DEVE processar e normalizar o evento antes de encaminhá-lo ao n8n.

Fluxo:

```txt
Evolution Payload
        ↓
Webhook Processor
        ↓
Evento normalizado
        ↓
n8n
```

### 6.5 Eventos desconhecidos

Eventos desconhecidos NÃO DEVEM derrubar a aplicação.

DEVEM ser tratados de forma controlada, podendo ser registrados e classificados para posterior análise.

### 6.6 Falha no n8n

A indisponibilidade do n8n NÃO DEVE causar perda do evento que já foi recebido e persistido pelo backend.

A entrega ao n8n DEVE ser tratada como uma etapa posterior ao recebimento e persistência do evento.

Mecanismos adicionais de retry ou filas poderão ser introduzidos posteriormente quando houver necessidade.

## 7. Mensagens

### 7.1 Modelo interno

Mensagens DEVEM possuir representação própria dentro do sistema.

O domínio NÃO DEVE utilizar diretamente o payload da Evolution API como modelo interno.

Informações relevantes incluem, conforme aplicável:

- direção da mensagem;
- tipo;
- conteúdo;
- identificador do destinatário/remetente;
- identificador da mensagem no provider;
- status.

### 7.2 Identificador do provider

Quando o provider fornecer um identificador de mensagem, esse identificador DEVE ser preservado.

Ele poderá ser utilizado para reconciliação, atualização de status e rastreamento.

### 7.3 Formatos de mensagem

A V1 DEVE suportar os formatos definidos no planejamento do produto:

- texto;
- imagem;
- áudio;
- documento;
- vídeo.

O modelo de mensagens DEVE permitir evolução para outros formatos posteriormente sem exigir uma alteração estrutural desnecessária.

## 8. API Pública

### 8.1 Versionamento

A API pública utilizará versionamento.

A V1 será exposta sob:

```txt
/v1
```

Alterações incompatíveis DEVEM ser tratadas de forma explícita e NÃO DEVEM ocorrer silenciosamente.

### 8.2 Contratos

Endpoints públicos DEVEM possuir contratos claros de:

- entrada;
- saída;
- autenticação;
- códigos HTTP;
- erros.

A documentação OpenAPI DEVE refletir os contratos públicos.

### 8.3 Erros

Erros públicos DEVEM possuir formato consistente.

Estrutura de referência:

```json
{
  "code": "ERROR_CODE",
  "message": "Mensagem legível.",
  "details": {}
}
```

O campo `code` DEVE ser utilizado como identificador programático do erro.

Detalhes internos do provider NÃO DEVEM ser expostos diretamente aos consumidores.

## 9. Integrações Externas

### 9.1 Evolution API

A Evolution API será o provider utilizado na V1.

A versão utilizada DEVE ser controlada e registrada na configuração/documentação do projeto.

Diferenças específicas da Evolution API DEVEM permanecer encapsuladas na camada do provider.

### 9.2 n8n

O n8n será integrado através do backend.

O n8n DEVE receber eventos no formato definido pelo backend, e NÃO DEVE depender diretamente dos payloads da Evolution API.

### 9.3 Chamadas externas

Regras de negócio NÃO DEVEM realizar chamadas HTTP diretamente para serviços externos.

As integrações DEVEM ser encapsuladas por clientes, adapters ou providers apropriados.

## 10. Observabilidade

Falhas relevantes DEVEM ser rastreáveis.

Quando aplicável, o sistema DEVE registrar informações suficientes para diagnóstico, como:

- contexto da operação;
- cliente;
- instância;
- provider;
- endpoint;
- timestamp;
- identificadores de correlação;
- erro ocorrido.

Segredos e informações sensíveis NÃO DEVEM ser expostos desnecessariamente nos logs.

## 11. Privacidade e Dados

O sistema poderá processar mensagens, números de telefone, mídia e outros dados potencialmente pessoais.

O acesso e a exposição desses dados DEVEM ser limitados ao necessário para o funcionamento do produto.

Dados sensíveis NÃO DEVEM ser incluídos desnecessariamente em:

- logs;
- mensagens de erro;
- respostas públicas;
- configurações;
- código-fonte.

## 12. Testabilidade

Componentes relevantes DEVEM ser testáveis isoladamente.

A interface do provider DEVE permitir testes sem depender obrigatoriamente de uma instância real da Evolution API.

Os fluxos críticos DEVEM possuir testes adequados, incluindo:

- autenticação;
- criação e gerenciamento de instâncias;
- conexão;
- desconexão;
- envio de mensagens;
- recebimento de webhooks;
- processamento de eventos;
- integração com n8n.

## 13. Escopo da V1

A V1 DEVE permanecer concentrada no núcleo da plataforma.

### Incluído

- gestão de clientes;
- autenticação por API Key;
- gestão de instâncias;
- conexão;
- desconexão;
- status das instâncias;
- envio de mensagens;
- recebimento de mensagens;
- formatos de mensagens definidos;
- webhooks;
- normalização de eventos;
- persistência;
- logs;
- integração com Evolution API;
- integração com n8n.

### Fora do escopo inicial

As funcionalidades abaixo NÃO fazem parte do núcleo da V1:

- painel administrativo;
- billing;
- assinaturas;
- campanhas;
- disparos em massa;
- CRM;
- chatbot de IA nativo;
- analytics avançado;
- múltiplos providers em produção;
- arquitetura de microserviços.

Funcionalidades fora do escopo somente DEVEM ser adicionadas mediante decisão explícita e atualização do planejamento.

## 14. Simplicidade e Não Antecipação

O projeto DEVE evitar complexidade desnecessária.

Entre soluções adequadas, DEVE ser preferida a solução mais simples que atenda aos requisitos.

NÃO DEVEM ser introduzidos antecipadamente serviços, frameworks, filas, microserviços ou outras infraestruturas apenas por uma necessidade hipotética futura.

A arquitetura DEVE ser preparada para extensões conhecidas, mas NÃO DEVE ser superdimensionada.

## 15. Desenvolvimento Orientado a Specs

O projeto utilizará desenvolvimento orientado a especificações.

Fluxo:

```txt
Constitution
    ↓
Specification
    ↓
Clarificações
    ↓
Plan
    ↓
Tasks
    ↓
Implementação
    ↓
Testes
    ↓
Validação
```

Toda funcionalidade relevante DEVE possuir uma specification antes da implementação.

## 16. Hierarquia dos Documentos

A hierarquia de decisões do projeto será:

```txt
Constitution
    ↓
Documentação de planejamento
    ↓
Specification
    ↓
Plan
    ↓
Tasks
    ↓
Código
```

Uma camada inferior NÃO DEVE contradizer uma decisão superior.

Quando uma decisão superior precisar mudar, a documentação correspondente DEVE ser atualizada antes ou junto da implementação da mudança.

## 17. Ambiguidades e Decisões

Decisões arquiteturais relevantes NÃO DEVEM ser inventadas durante a implementação quando houver ambiguidade significativa.

A ambiguidade DEVE ser:

- identificada;
- esclarecida;
- documentada;
- refletida na documentação ou specification correspondente.

Decisões técnicas relevantes DEVEM possuir justificativa suficiente para preservar o contexto da decisão.

## 18. Critérios Gerais de Qualidade

O projeto DEVE priorizar:

- segurança;
- correção;
- simplicidade;
- manutenibilidade;
- testabilidade;
- observabilidade;
- desacoplamento;
- isolamento entre clientes;
- evolução controlada.

Performance e extensibilidade NÃO DEVEM justificar complexidade desnecessária sem uma necessidade concreta.

## 19. Critérios de Pronto

Uma funcionalidade DEVE ser considerada concluída somente quando:

- estiver definida na specification;
- atender aos requisitos;
- atender aos critérios de aceitação;
- possuir implementação concluída;
- possuir os testes relevantes;
- possuir tratamento de erros adequado;
- tiver os aspectos de segurança considerados;
- tiver documentação atualizada quando necessário;
- tiver migrations quando necessárias;
- tiver configuração documentada quando necessária;
- tiver sua integração validada.

## 20. Governança

Esta Constitution é a referência superior para as decisões do projeto.

Alterações relevantes DEVEM ser deliberadas e documentadas.

Uma alteração da Constitution DEVE registrar, quando aplicável:

- princípio alterado;
- decisão anterior;
- nova decisão;
- motivo;
- impacto;
- documentos afetados;
- specifications afetadas.

## 21. Versionamento da Constitution

A Constitution utiliza versionamento semântico:

```txt
MAJOR.MINOR.PATCH
```

- **MAJOR**: Alteração incompatível em princípios fundamentais.
- **MINOR**: Adição de novos princípios ou regras sem alteração incompatível dos princípios existentes.
- **PATCH**: Correções de redação, esclarecimentos ou ajustes que não alterem o significado das decisões.

## 22. Regra Final

O projeto DEVE construir o que a V1 realmente necessita, mantendo uma arquitetura organizada e desacoplada que permita evolução futura sem introduzir complexidade antes da hora.

A regra fundamental é:

> Construir apenas o necessário para a V1, mas preservar as decisões arquiteturais que permitem sua evolução.

---

**Version**: 1.0.0 | **Ratified**: 2026-08-15 | **Last Amended**: 2026-08-15
