# Especificação da Feature: Recebimento de Webhooks

**Branch**: `006-webhook-reception`  
**Criado em**: 2026-08-19  
**Status**: Rascunho  
**Entrada**: Descrição do usuário: "Recebimento de webhooks da Evolution API — receber eventos, identificar instância, salvar payload bruto, normalizar dados para uso interno"

## Cenários de Uso & Testes *(obrigatório)*

### História 1 - Receber Evento de Mensagem Recebida (Prioridade: P1)

Quando um usuário do WhatsApp envia uma mensagem para uma instância conectada, o sistema recebe o evento do provider de mensageria, identifica a qual instância e cliente pertence, salva os dados brutos do evento, normaliza-os em um formato interno e registra a mensagem de entrada para consulta e encaminhamento posterior.

**Por que esta prioridade**: Este é o valor central do sistema de webhooks — sem receber e processar mensagens de entrada, nenhuma automação ou histórico de mensagens é possível.

**Teste independente**: Pode ser totalmente testado enviando uma mensagem WhatsApp para uma instância conectada e verificando que a mensagem aparece no histórico do sistema com remetente, conteúdo e tipo corretos.

**Cenários de aceitação**:

1. **Dado** uma instância conectada com um cliente conhecido, **Quando** o provider envia um evento de mensagem recebida com autenticação válida, **Então** o sistema salva o payload bruto, normaliza-o, registra a mensagem de entrada com direção "inbound" e status "received", e responde com sucesso.
2. **Dado** uma instância conectada, **Quando** um evento de mensagem de texto chega, **Então** os dados normalizados incluem número do remetente, conteúdo da mensagem, tipo "text" e timestamp.
3. **Dado** uma instância conectada, **Quando** um evento de mensagem de mídia chega (imagem, áudio, documento, vídeo), **Então** os dados normalizados incluem número do remetente, URL da mídia, tipo da mensagem, legenda (se presente) e timestamp.

---

### História 2 - Receber Atualização de Status de Conexão (Prioridade: P2)

Quando uma instância de WhatsApp muda seu estado de conexão (conectada, desconectada, erro), o sistema recebe este evento, identifica a instância e atualiza seu status de acordo, para que clientes e outros componentes do sistema tenham informação precisa sobre o estado da instância.

**Por que esta prioridade**: O status de conexão preciso é crítico para o sistema impedir o envio de mensagens por instâncias desconectadas e informar clientes sobre disponibilidade.

**Teste independente**: Pode ser totalmente testado desconectando uma instância WhatsApp e verificando que o sistema atualiza o status da instância para "disconnected" em poucos segundos.

**Cenários de aceitação**:

1. **Dado** uma instância conhecida, **Quando** um evento de atualização de conexão indica "connected", **Então** o status da instância é atualizado para "connected" e o timestamp de conexão é registrado.
2. **Dado** uma instância conhecida, **Quando** um evento de atualização de conexão indica "disconnected", **Então** o status da instância é atualizado para "disconnected" e o timestamp de desconexão é registrado.
3. **Dado** uma instância conhecida, **Quando** um evento de atualização de conexão indica "error", **Então** o status da instância é atualizado para "error" e um registro de falha é criado.

---

### História 3 - Receber Status de Entrega/Leitura de Mensagem (Prioridade: P3)

Quando uma mensagem enviada anteriormente é entregue ou lida pelo destinatário, o sistema recebe o evento de atualização de status e atualiza o registro correspondente da mensagem de saída, para que clientes possam acompanhar o progresso de entrega.

**Por que esta prioridade**: Confirmações de entrega e leitura fornecem feedback valioso para clientes sobre o alcance das mensagens, mas o sistema permanece totalmente funcional sem elas.

**Teste independente**: Pode ser totalmente testado enviando uma mensagem, fazendo o destinatário ler, e verificando que o status da mensagem atualiza de "sent" para "delivered" para "read".

**Cenários de aceitação**:

1. **Dado** uma mensagem enviada anteriormente existente no sistema, **Quando** um evento de status de entrega chega com o identificador da mensagem, **Então** o status da mensagem é atualizado para "delivered".
2. **Dado** uma mensagem enviada anteriormente existente no sistema, **Quando** um evento de status de leitura chega com o identificador da mensagem, **Então** o status da mensagem é atualizado para "read".
3. **Dado** um evento de status de entrega que chega mas nenhuma mensagem correspondente é encontrada, **Então** o evento ainda é salvo como evento bruto de webhook sem atualizar nenhum registro de mensagem.

---

### História 4 - Tratar Eventos Não Reconhecidos com Resiliência (Prioridade: P3)

Quando o provider de mensageria envia um tipo de evento que o sistema ainda não suporta ou reconhece, o sistema ainda salva o payload bruto para fins de depuração sem quebrar nenhum outro processamento, e responde confirmando o recebimento.

**Por que esta prioridade**: A resiliência a eventos desconhecidos previne falhas do sistema quando o provider introduz novos tipos de eventos ou envia dados inesperados.

**Teste independente**: Pode ser totalmente testado enviando um evento arbitrário com autenticação válida e verificando que o sistema responde com confirmação e salva os dados brutos.

**Cenários de aceitação**:

1. **Dado** uma requisição de webhook autenticada válida, **Quando** o tipo de evento não é reconhecido, **Então** o sistema salva o payload bruto, classifica como "unknown" e responde com confirmação de recebimento.
2. **Dado** um evento desconhecido, **Então** nenhum registro de mensagem ou atualização de instância é criado, e o sistema não gera resposta de erro para o provider.

---

### Casos de Borda

- O que acontece quando um webhook chega para uma instância que não existe no sistema? O sistema salva o evento bruto com um marcador de falha e registra o problema, mas não quebra.
- O que acontece quando o segredo de autenticação do webhook está ausente ou inválido? O sistema rejeita a requisição imediatamente sem salvar nada.
- O que acontece quando o payload do evento é malformado ou com campos obrigatórios ausentes? O sistema tenta salvar os dados brutos recebidos, marca como falha e registra o erro.
- O que acontece quando dois eventos idênticos chegam em rápida sucessão (duplicados)? Ambos são salvos; deduplicação não é necessária na V1.
- O que acontece quando o payload é excessivamente grande? O sistema deve impor um limite razoável de tamanho e rejeitar payloads que o excedam.

## Requisitos *(obrigatório)*

### Requisitos Funcionais

- **RF-001**: O sistema DEVE receber eventos do provider de mensageria por meio de um endpoint dedicado de webhook.
- **RF-002**: O sistema DEVE validar a autenticidade de cada requisição de webhook recebida usando um mecanismo de segredo compartilhado antes de processar.
- **RF-003**: O sistema DEVE salvar o payload bruto completo do evento para toda requisição autenticada válida, independentemente de o evento ser reconhecido.
- **RF-004**: O sistema DEVE identificar a qual instância e cliente o evento pertence usando o identificador de instância presente no payload.
- **RF-005**: O sistema DEVE classificar cada evento em um dos tipos internos reconhecidos: message.received, message.sent, message.delivered, message.read, connection.update, send.error ou unknown.
- **RF-006**: O sistema DEVE normalizar eventos reconhecidos em um formato interno padronizado contendo: tipo do evento, identificador da instância, remetente/destinatário, tipo da mensagem, conteúdo, referência de mídia, identificador de mensagem do provider e timestamp.
- **RF-007**: O sistema DEVE registrar mensagens de entrada (direção "inbound", status "received") no armazenamento de mensagens quando um evento de mensagem recebida é identificado.
- **RF-008**: O sistema DEVE atualizar o status de mensagens enviadas anteriormente quando eventos de entrega, leitura ou erro de envio são recebidos e a mensagem original pode ser encontrada pelo identificador do provider.
- **RF-009**: O sistema DEVE atualizar o status de conexão da instância quando eventos de connection.update são recebidos.
- **RF-010**: O sistema DEVE rejeitar requisições não autenticadas ou incorretamente autenticadas com uma resposta de erro apropriada.
- **RF-011**: O sistema DEVE registrar falhas de processamento em um log de erros quando eventos não podem ser totalmente processados.
- **RF-012**: O sistema DEVE responder ao provider prontamente (em poucos segundos) para evitar retentativas por timeout do provider.
- **RF-013**: O sistema DEVE tratar eventos para instâncias não reconhecidas salvando o payload bruto com metadados apropriados e registrando o problema, sem quebrar.
- **RF-014**: O sistema DEVE rastrear o status de processamento de cada evento de webhook (received, processed, failed, ignored).

### Entidades Principais

- **Evento de Webhook**: Representa um único evento recebido do provider de mensageria. Contém payload bruto, payload normalizado, tipo do evento, status de processamento, referências de instância e cliente associados, e timestamps de recebimento e processamento.
- **Mensagem (entrada)**: Representa uma mensagem WhatsApp recebida por uma instância conectada. Contém remetente, conteúdo/mídia, tipo da mensagem, direção, status e timestamps.
- **Instância (atualização de status)**: Entidade de instância existente cujo status de conexão é atualizado com base em eventos de conexão.
- **Log de Erro**: Registro de falhas de processamento incluindo contexto do erro, referência ao evento de origem e timestamp.

## Critérios de Sucesso *(obrigatório)*

### Resultados Mensuráveis

- **CS-001**: 100% dos eventos autenticados válidos do provider são salvos (sem perda de dados) mesmo que o processamento falhe a jusante.
- **CS-002**: 95% dos eventos reconhecidos são totalmente processados (normalizados, mensagem/status atualizados) em até 3 segundos após o recebimento.
- **CS-003**: Tipos de eventos não reconhecidos não causam erros no sistema ou indisponibilidade — a disponibilidade do sistema permanece inalterada.
- **CS-004**: O status de conexão da instância reflete o estado real em até 5 segundos após um evento de mudança de conexão.
- **CS-005**: Todas as mensagens de entrada são recuperáveis do histórico de mensagens com remetente, conteúdo, tipo e timestamp corretos.
- **CS-006**: Requisições não autenticadas são rejeitadas 100% das vezes sem nenhum dado salvo ou processamento disparado.
- **CS-007**: O sistema classifica corretamente pelo menos 4 tipos distintos de eventos (mensagem recebida, atualização de conexão, status de entrega, desconhecido).

## Premissas

- O provider de mensageria envia eventos via HTTP POST para um único endpoint configurado durante a criação da instância.
- O segredo compartilhado para autenticação do webhook é configurado como variável de ambiente (segredo único para todas as instâncias na V1).
- Eventos podem chegar fora de ordem; o sistema processa cada um independentemente sem exigir ordenação estrita.
- Eventos duplicados podem chegar; a V1 salva ambos sem lógica de deduplicação.
- O provider inclui o identificador da instância em todo payload de evento.
- URLs de mídia em eventos de mensagem recebida são acessíveis diretamente (sem autenticação adicional necessária para referenciá-las).
- Lógica de retry para processamento falho está fora do escopo da V1 — eventos com falha são registrados mas não automaticamente reprocessados.
- O sistema precisa lidar com apenas um provider de mensageria na V1.
- O tamanho do payload é esperado abaixo de 1 MB para eventos normais; um limite razoável de 5 MB é assumido.
