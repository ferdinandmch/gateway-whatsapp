# Contract: MessagingProvider Interface

**Date**: 2026-08-16
**Type**: Internal interface (provider abstraction layer)

## Overview

Define o contrato que qualquer provider de mensageria deve implementar. Na V1, apenas `EvolutionProvider` implementa esta interface.

## Interface Methods

### Instance Lifecycle

#### create_instance

Cria uma nova instância no provider.

- **Input**: `instance_name: str`
- **Output**: `ProviderResult`
  - success.data: `{"instance_name": str}` 
  - error codes: `INSTANCE_ALREADY_EXISTS`, `PROVIDER_ERROR`, `PROVIDER_UNAVAILABLE`, `PROVIDER_TIMEOUT`

#### get_instance_status

Consulta o status de conexão de uma instância.

- **Input**: `instance_name: str`
- **Output**: `ProviderResult`
  - success.data: `{"state": InstanceState}`
  - error codes: `PROVIDER_ERROR`, `PROVIDER_UNAVAILABLE`, `PROVIDER_TIMEOUT`

Nota: `not_found` é retornado como estado, não como erro.

#### connect_instance

Inicia processo de conexão (gera QR code/pairing code).

- **Input**: `instance_name: str`
- **Output**: `ProviderResult`
  - success.data: `{"qrcode": str | None, "pairingCode": str | None}`
  - error codes: `INSTANCE_NOT_FOUND`, `PROVIDER_ERROR`, `PROVIDER_UNAVAILABLE`, `PROVIDER_TIMEOUT`

#### disconnect_instance

Executa logout da instância.

- **Input**: `instance_name: str`
- **Output**: `ProviderResult`
  - success.data: `{"instance_name": str}`
  - error codes: `INSTANCE_NOT_FOUND`, `PROVIDER_ERROR`, `PROVIDER_UNAVAILABLE`, `PROVIDER_TIMEOUT`

#### delete_instance

Remove instância do provider.

- **Input**: `instance_name: str`
- **Output**: `ProviderResult`
  - success.data: `{"instance_name": str}`
  - error codes: `INSTANCE_NOT_FOUND`, `PROVIDER_ERROR`, `PROVIDER_UNAVAILABLE`, `PROVIDER_TIMEOUT`

---

### Messaging

#### send_text

Envia mensagem de texto.

- **Input**: `instance_name: str`, `to: str` (número bruto), `content: str`
- **Output**: `ProviderResult`
  - success.data: `{"provider_message_id": str}`
  - error codes: `INSTANCE_NOT_FOUND`, `PROVIDER_ERROR`, `PROVIDER_UNAVAILABLE`, `PROVIDER_TIMEOUT`, `INVALID_REQUEST`

#### send_media

Envia mensagem de mídia (imagem, áudio, documento, vídeo).

- **Input**: `instance_name: str`, `to: str` (número bruto), `media_type: MessageType`, `media_url: str`, `caption: str | None`, `filename: str | None`
- **Output**: `ProviderResult`
  - success.data: `{"provider_message_id": str}`
  - error codes: `INSTANCE_NOT_FOUND`, `PROVIDER_ERROR`, `PROVIDER_UNAVAILABLE`, `PROVIDER_TIMEOUT`, `INVALID_REQUEST`

---

## Common Behaviors

1. **Normalização de telefone**: Todos os métodos de envio normalizam `to` via utilitário de phone (DT-044) antes de chamar a Evolution API.
2. **Timeout**: Todas as chamadas HTTP respeitam `HTTP_TIMEOUT` das settings.
3. **Falha imediata**: Nenhum retry automático (DT-036).
4. **Mapeamento de erros**: Erros HTTP são convertidos para `ProviderError` com códigos internos — nunca expostos como exceções não tratadas.
5. **Headers**: Todas as requisições incluem `apikey: {EVOLUTION_API_KEY}` no header.
