# Research: Segurança com API Key

**Date**: 2026-08-19

## Decisão 1: Algoritmo de hash para API Keys

**Decision**: SHA256 com salt (já implementado)  
**Rationale**: Para API Keys de alta entropia (37 chars: `zapi_` + 32 hex), SHA256 com salt é suficiente. Bcrypt/Argon2 são preferíveis para senhas de baixa entropia, mas adicionam ~100ms por verificação desnecessariamente. API Keys com 128 bits de entropia não são vulneráveis a rainbow tables.  
**Alternatives considered**:
- Bcrypt: overhead de ~100ms por requisição sem benefício real para chaves de alta entropia
- Argon2: mesmo caso do bcrypt, overkill para este cenário
- HMAC-SHA256: válido, mas SHA256 com salt prefixado é equivalente para este caso de uso

## Decisão 2: Formato da API Key

**Decision**: `zapi_` + 32 caracteres hexadecimais = `token_hex(16)`  
**Rationale**: Prefixo `zapi_` permite identificação rápida em logs e scanners de secrets. 32 hex chars = 128 bits de entropia, suficiente para V1. Total: 37 caracteres.  
**Alternatives considered**:
- UUID v4: 122 bits de entropia mas formato verboso com hífens
- Base64: mais curto por bit mas chars especiais complicam headers
- token_hex(24) = 48 chars: entropia excessiva sem benefício prático

## Decisão 3: Proteção do endpoint de clientes

**Decision**: Header `X-Admin-Token` com token fixo configurado via variável de ambiente `ADMIN_TOKEN`  
**Rationale**: Mecanismo simples e consistente com o padrão do projeto (headers para auth). Suficiente para V1 onde a criação de clientes é rara e feita por administradores.  
**Alternatives considered**:
- Mesmo header X-API-Key com role check: mistura domínios
- Basic Auth: adiciona complexidade desnecessária
- Sem proteção (rede interna): inseguro se exposto acidentalmente

## Decisão 4: Comportamento para cliente inativo

**Decision**: Retornar 401 idêntico a "chave inexistente"  
**Rationale**: Não revelar existência de chaves previne enumeração. Atacante não consegue diferenciar entre chave inválida, inexistente ou desativada.  
**Alternatives considered**:
- 403 com mensagem: revela que a chave existe e está bloqueada (information leakage)
- 401 com mensagem diferente: timing side-channel pode revelar estado

## Decisão 5: Timing attack mitigation

**Decision**: Usar `secrets.compare_digest` para webhook secret (já implementado). Para API Keys, a busca por hash no banco é suficiente — o atacante não tem controle sobre o hash comparado.  
**Rationale**: O hash transforma a comparação em lookup no banco. Não há comparação direta string-a-string do input do usuário.  
**Alternatives considered**:
- Constant-time comparison do hash: desnecessário pois é DB lookup
- Rate limiting: fora do escopo V1, pode ser adicionado depois

## Decisão 6: Módulo de segurança compartilhado

**Decision**: Extrair `generate_api_key()` e `hash_api_key()` para `app/core/security.py`  
**Rationale**: Elimina duplicação entre `scripts/create_client.py` e o novo endpoint. Single source of truth para lógica de geração e hash.  
**Alternatives considered**:
- Manter inline em dependencies.py: funciona mas duplica com scripts
- Pacote separado: over-engineering para 2 funções
