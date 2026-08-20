# Research: Gerenciamento de Instâncias WhatsApp

## R-001: Modelo de instância — campos necessários vs. existentes

**Decision**: Estender o model `Instance` existente com campos adicionais para suportar a spec completa.

**Rationale**: O model atual (`app/models/instance.py`) possui apenas `id`, `client_id`, `name`, `status`, `provider_instance_id`. A spec exige campos adicionais para display_name, phone_number, configuração de webhook do n8n e webhook_enabled. A migration adicionará os campos faltantes.

**Campos a adicionar via migration**:
- `display_name` (String 255, NOT NULL) — nome amigável exibido ao operador
- `phone_number` (String 20, nullable) — preenchido quando conectada
- `n8n_webhook_url` (Text, nullable) — URL webhook do n8n por instância
- `webhook_enabled` (Boolean, default True) — flag para encaminhamento de eventos

**Campos a ajustar**:
- `status`: Adicionar estados `created`, `error`, `removed` ao enum `InstanceStatus`
- `name` → `provider_instance_name`: renomear para clareza (o campo existente `name` passa a ser `provider_instance_name` conforme a spec; `display_name` é o nome amigável)

**Alternatives considered**:
- Criar novo model separado: rejeitado por violar simplicidade e duplicar dados
- Usar JSON field para config: rejeitado por dificultar queries e validação

---

## R-002: Geração do provider_instance_name

**Decision**: Usar formato `inst_{uuid_short}` (primeiros 8 caracteres de UUID4 sem hífens).

**Rationale**: O nome precisa ser único, previsível em comprimento, e não revelar informações do cliente. UUID curto atende todos os requisitos sem colisão prática.

**Formato**: `inst_a1b2c3d4`

**Alternatives considered**:
- `client_slug_instance_slug`: expõe nome do cliente ao provider
- UUID completo: muito longo, dificulta debug na Evolution API
- Sequencial: requer coordenação/lock para unicidade

---

## R-003: Limite de 10 instâncias — implementação

**Decision**: Validação no service layer antes de criar. Contagem exclui instâncias com `deleted_at IS NOT NULL` (soft deleted/removed).

**Rationale**: Constante fixa `MAX_INSTANCES_PER_CLIENT = 10` no service. Simples, testável, sem overhead de consulta extra além da contagem.

**Query**: `SELECT COUNT(*) FROM instances WHERE client_id = :id AND deleted_at IS NULL`

**Alternatives considered**:
- Campo no client (max_instances): over-engineering para V1
- Variável de ambiente: não justificada para V1
- Check constraint no banco: não permite mensagem de erro customizada

---

## R-004: Atualização automática de status via webhook

**Decision**: Quando o webhook da Evolution API reportar evento de conexão (`connection.update`), o backend atualiza o status da instância correspondente identificada pelo `provider_instance_name`.

**Rationale**: O fluxo de webhooks será implementado na spec 006, mas esta spec precisa garantir que o service de instâncias expõe um método `update_status_from_webhook(provider_instance_name, new_status)` que a rota de webhook poderá chamar.

**Implementação nesta spec**: Expor método no `InstanceService` para atualizar status. A integração com a rota de webhook será feita na spec 006.

**Alternatives considered**:
- Polling periódico: rejeitado por latência e consumo de recursos
- Depender inteiramente de webhook: escolhido, com fallback de consulta explícita via GET /status

---

## R-005: Soft delete e listagem

**Decision**: Usar o `SoftDeleteMixin` existente (`deleted_at` timestamp). Instâncias com `deleted_at IS NOT NULL` são consideradas "removed". Listagem filtra `deleted_at IS NULL` por padrão; parâmetro `include_removed=true` remove o filtro.

**Rationale**: O mixin já existe no projeto. O status "removed" da spec será implementado como presença de `deleted_at`. Ao remover, o campo `deleted_at` recebe timestamp UTC e status muda para enum `removed` (mantendo ambos para queries eficientes).

**Alternatives considered**:
- Apenas status enum sem soft delete: perderia timestamps e padrão existente
- Hard delete: rejeitado por spec (rastreabilidade, auditoria)

---

## R-006: Autenticação e identificação do cliente

**Decision**: Implementar dependency `get_current_client` que extrai API Key do header `X-API-Key`, faz hash, consulta no banco e retorna o `Client` ou levanta `HTTPException(401)`.

**Rationale**: A spec 008 (segurança) fará a implementação completa, mas esta spec precisa de um mecanismo funcional para identificar o cliente. Implementar versão básica agora; a spec 008 poderá refiná-la.

**Implementação**: O client model já possui `is_active`. A dependency valida que `is_active=True` ou retorna 403 com código `CLIENT_INACTIVE`.

**Alternatives considered**:
- Middleware: rejeitado por não dar acesso fácil ao client no handler
- Decorator: rejeitado por não integrar com DI do FastAPI

---

## R-007: Paginação na listagem

**Decision**: Usar padrão limit/offset conforme definido em `docs/contratos-api.md`. Default limit=20, max limit=100, offset default=0.

**Rationale**: Padrão já definido no projeto. Resposta no formato `{items: [...], limit: N, offset: N, total: N}`.

**Alternatives considered**:
- Cursor-based: over-engineering para V1 com escala pequena
- Sem paginação: rejeitado pela spec (pode haver muitas instâncias)
