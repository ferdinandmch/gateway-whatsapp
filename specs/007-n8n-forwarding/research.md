# Research: Encaminhamento para n8n

## Decisão 1: Timeout dedicado para n8n

**Decisão**: Introduzir configuração `N8N_FORWARD_TIMEOUT` separada do `HTTP_TIMEOUT` geral.

**Racional**: O `HTTP_TIMEOUT` atual é 30s (usado para chamadas à Evolution API e outras). Para encaminhamento ao n8n, 5 segundos é o máximo aceitável (SC-002). Usar o mesmo timeout de 30s bloquearia o processamento de webhooks desnecessariamente.

**Alternativas consideradas**:
- Usar `HTTP_TIMEOUT` existente (30s) — rejeitado porque viola SC-002 e bloqueia processamento
- Hardcoded 5s no forwarder — rejeitado porque Constitution seção 5.2 exige configurabilidade

## Decisão 2: Validação de URL antes do encaminhamento

**Decisão**: Validar a `n8n_webhook_url` com `pydantic.HttpUrl` na entrada (criação/atualização de instância) e também com checagem leve (`urlparse`) antes de cada tentativa de forwarding.

**Racional**: Validação na entrada previne URLs inválidas no banco. Checagem antes do forward é defesa em profundidade para dados legados ou corrompidos.

**Alternativas consideradas**:
- Validar apenas na entrada (criação de instância) — rejeitado porque dados existentes podem não ter sido validados
- Apenas try/except no HTTPX — rejeitado porque seria mais custoso e obscurece a causa do erro

## Decisão 3: Comportamento com redirects HTTP

**Decisão**: Seguir redirects (comportamento padrão do HTTPX, `follow_redirects=True`), com limite padrão de 20 redirects.

**Racional**: Webhooks n8n podem estar atrás de proxies ou load balancers que fazem redirect. Não seguir causaria falhas silenciosas difíceis de diagnosticar.

**Alternativas consideradas**:
- Não seguir redirects (`follow_redirects=False`) — rejeitado porque cenários com proxy são comuns
- Limitar a 3 redirects — rejeitado, padrão do HTTPX (20) é suficiente e pragmático

## Decisão 4: Concorrência de encaminhamentos

**Decisão**: Cada webhook é processado e encaminhado de forma independente, sem garantia de ordenação. O encaminhamento é síncrono dentro do request handler de cada webhook.

**Racional**: Na V1, o processamento de webhooks já é síncrono (um por request). Múltiplos webhooks simultâneos são tratados por workers do servidor (uvicorn). Não há necessidade de fila ou lock.

**Alternativas consideradas**:
- Fila com garantia de ordem por instância — rejeitado pela Constitution seção 14 (simplicidade, sem fila na V1)
- Background task (fire-and-forget) — rejeitado porque impossibilita registrar resultado antes de responder

## Decisão 5: Abordagem de implementação (incremental sobre spec 006)

**Decisão**: A spec 007 NÃO cria o forwarder do zero — ele já existe em `app/webhooks/forwarder.py` e está integrado ao `WebhookService`. A implementação da spec 007 foca em:
1. Adicionar `N8N_FORWARD_TIMEOUT` ao config
2. Usar o timeout dedicado no forwarder
3. Adicionar validação de URL no forwarder
4. Habilitar `follow_redirects=True`
5. Adicionar testes unitários e de integração completos
6. Validar a URL na criação/atualização de instância (schema)

**Racional**: A base funcional já existe e está correta. Refazer seria desperdício e introduziria risco de regressão.

**Alternativas consideradas**:
- Reescrever o forwarder — rejeitado, já funcional e alinhado com requisitos
- Criar módulo separado para n8n — rejeitado, `app/webhooks/forwarder.py` já está bem posicionado
