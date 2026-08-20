# Research: Envio de Mensagens

**Date**: 2026-08-18 | **Branch**: `005-message-sending`

## Resumo

Nenhum "NEEDS CLARIFICATION" permaneceu no Technical Context. A pesquisa abaixo documenta decisões técnicas derivadas da análise do código existente e das clarificações da spec.

---

## 1. Provider já implementa envio

**Decision**: Usar os métodos `send_text` e `send_media` já existentes em `MessagingProvider` / `EvolutionProvider`.

**Rationale**: O provider já possui implementação completa de envio de texto e mídia, incluindo normalização de telefone e extração de `provider_message_id`. Nenhuma alteração é necessária na camada de provider.

**Alternatives considered**:
- Criar métodos separados por tipo de mídia no provider → rejeitado por violar DRY e o design existente que usa `MessageType` enum.

---

## 2. Modelo Message já existe

**Decision**: Usar o modelo `Message` existente em `app/models/message.py`. Adicionar campos `media_url`, `caption` e `filename` que estão na spec mas ausentes no modelo atual.

**Rationale**: O modelo já possui `id`, `instance_id`, `direction`, `content_type`, `body`, `remote_jid`, `status`, `provider_message_id`. Faltam campos para mídia que são necessários para rastreabilidade.

**Alternatives considered**:
- Armazenar dados de mídia apenas no `raw_payload` JSON → rejeitado por dificultar consultas e auditoria.

---

## 3. Validação de número de telefone

**Decision**: Adicionar validação de formato mínimo em `app/core/phone.py` (apenas dígitos, 10-13 caracteres após strip de não-dígitos) antes da normalização existente.

**Rationale**: A clarificação da spec define que o backend rejeita números inválidos antes de chamar o provider. A função `normalize_phone` existente apenas adiciona prefixo 55, sem validação.

**Alternatives considered**:
- Validar no schema Pydantic → rejeitado porque a lógica é reutilizada pelo service e deve ficar no módulo phone.
- Validar DDDs válidos → rejeitado na clarificação (apenas formato mínimo).

---

## 4. Padrão de Service

**Decision**: Criar `MessageService` seguindo o padrão de `InstanceService` — recebe `db: AsyncSession` e `provider: MessagingProvider` no construtor.

**Rationale**: Consistência com o padrão já estabelecido no projeto. Facilita testes com mock do provider.

**Alternatives considered**:
- Funções standalone → rejeitado por inconsistência com o pattern do projeto.

---

## 5. Timeout e tratamento de erro

**Decision**: O timeout de 30s já está configurado no `EvolutionProvider` (parâmetro `timeout` no construtor, default=30). A configuração vem de `settings.HTTP_TIMEOUT`. Quando timeout ocorre, `_make_request` retorna `ProviderResult(success=False, error=PROVIDER_TIMEOUT)`.

**Rationale**: O provider já trata timeout e connectivity errors. O service precisa apenas interpretar `success=False` como falha de envio.

**Alternatives considered**:
- Adicionar retry no service → rejeitado na clarificação (sem retry na V1).

---

## 6. Registro de erros em error_logs

**Decision**: Quando o envio falha, registrar um `ErrorLog` com context="message.send_failed", incluindo instance_id, message_id e error details no campo `details` (JSONB).

**Rationale**: Segue o padrão de observabilidade da Constitution (seção 10). O modelo `ErrorLog` já existe com campos `context`, `error_message` e `details` (JSONB).

**Alternatives considered**:
- Apenas logging em stdout → insuficiente para rastreabilidade persistente conforme RN-030.
