# 🏗️ Guia de Arquitetura para Desenvolvedores

Documentação completa da arquitetura do **Create Agents AI**, baseada em **Clean Architecture** e **princípios SOLID**.

______________________________________________________________________

## 📐 Estrutura de Camadas

```
┌─────────────────────────────────────┐
│       PRESENTATION                  │  CLI, UI (ChatCLIApplication)
│     (Interface do Usuário)          │  Command Handlers, Terminal UI
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│           MAIN                      │  Facade (CreateAgent),
│    (Composition Root)               │  AgentComposer, Factories
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│        APPLICATION                  │  Use Cases, DTOs,
│    (Lógica da Aplicação)            │  Ports/Interfaces (ChatRepository)
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│          DOMAIN                     │  Entities (Agent, History),
│    (Regras de Negócio)              │  Value Objects (ChatMetrics, Message),
└──────────────▲──────────────────────┘  Domain Services, LoggerInterface
               │
┌──────────────┴──────────────────────┐
│      INFRASTRUCTURE                 │  Adapters, Clients, Handlers,
│    (Detalhes Técnicos)              │  OpenAI, Ollama, Tools, Config
└─────────────────────────────────────┘
```

______________________________________________________________________

## 🎯 Camadas

### 1. Presentation (Apresentação)

**Localização:** `src/createagents/presentation/`

**Responsabilidade:** Interface de usuário e interação externa.

**Componentes:**

- **CLI Application:** `ChatCLIApplication` — aplicação CLI interativa para chat com agentes
- **Command Handlers:** Sistema baseado no **Command Pattern**
  - `ChatCommandHandler` — processamento de mensagens de chat
  - `HelpCommandHandler` — exibe ajuda e comandos disponíveis
  - `MetricsCommandHandler` — mostra métricas de performance
  - `ConfigsCommandHandler` — exibe configurações do agente
  - `ToolsCommandHandler` — lista ferramentas disponíveis
  - `ClearCommandHandler` — limpa histórico de conversação
- **UI Components:** `TerminalRenderer`, `TerminalFormatter`, `ColorScheme` — renderização colorida no terminal
- **I/O:** `InputReader` — leitura de entrada do usuário
- **Registry:** `CommandRegistry` — registro e resolução de comandos

______________________________________________________________________

### 2. Main (Composition Root & Facade)

**Localização:** `src/createagents/main/`

**Responsabilidade:** Compor o grafo de dependências e expor a fachada pública do pacote.

**Componentes:**

- **Facade (`main/facade/`):** `CreateAgent` — ponto de entrada unificado que expõe `chat` (async), `get_configs`, `get_all_available_tools`, `clear_history`, `export_metrics_*` e `start_cli`.
- **Composer (`main/composers/`):** `AgentComposer` — raiz de composição que instancia os use cases de aplicação, resolve o adapter de provider via fábrica de infraestrutura e injeta as dependências.

______________________________________________________________________

### 3. Application (Aplicação)

**Localização:** `src/createagents/application/`

**Responsabilidade:** Orquestrar casos de uso do sistema, dependendo apenas do domínio.

**Componentes:**

- **Use Cases (`application/use_cases`):**
  - `CreateAgentUseCase` — cria e valida agentes, resolvendo ferramentas via `ToolRegistry`.
  - `ChatWithAgentUseCase` — orquestra mensagens **assíncronas** entre `Agent` e a porta `ChatRepository`.
  - `GetAgentConfigUseCase` — retorna as configurações do agente.
  - `GetSystemAvailableToolsUseCase` — lista as ferramentas disponíveis no ambiente.
- **DTOs (`application/dtos`):** Objetos de transferência de dados:
  - `CreateAgentInputDTO`, `ChatInputDTO`, `AgentConfigOutputDTO`
  - **`StreamingResponseDTO`** — wrapper para `AsyncGenerator` que permite iteração assíncrona (`async for`) e `await` com cache do texto completo.
- **Interfaces / Ports (`application/interfaces`):**
  - `ChatRepository` — porta para adapters de provedores LLM
  - `ToolRegistry` — porta para catálogo de ferramentas

______________________________________________________________________

### 4. Domain (Domínio)

**Localização:** `src/createagents/domain/`

**Responsabilidade:** Regras de negócio puras, independentes de infraestrutura ou apresentação.

**Componentes:**

- **Entities:** `Agent` (entidade principal), `History` (entidade de histórico de conversação)
- **Value Objects:** `Message`, `MessageRole`, `ChatMetrics`, `SupportedConfigs`, `SupportedProviders`, `BaseTool`
- **Domain Services:** `ToolExecutor` (execução assíncrona/síncrona de ferramentas), `ToolExecutionResult`
- **Interfaces (`domain/interfaces`):** `LoggerInterface` — abstração de logging do domínio
- **Exceptions:** `domain.exceptions` (`AgentException`, `InvalidAgentConfigException`, etc.)

______________________________________________________________________

### 5. Infrastructure (Infraestrutura)

**Localização:** `src/createagents/infra/`

**Responsabilidade:** Implementar detalhes técnicos e integrações externas.

**Componentes:**

- **Adapters (Chat):**
  - `OpenAIChatAdapter` — integração com OpenAI
  - `OllamaChatAdapter` — integração com Ollama
- **Handlers (Async Streaming):**
  - `OpenAIHandler` / `OpenAIStreamHandler` — processamento de chamadas não-streaming e streaming OpenAI
  - `OllamaHandler` / `OllamaStreamHandler` — processamento de chamadas não-streaming e streaming Ollama
- **Clients:**
  - `OpenAIClient` — cliente HTTP para OpenAI
  - `OllamaClient` — cliente HTTP para Ollama
- **Common Adapters:**
  - `MetricsRecorder` — base abstrata da gravação de métricas; `OpenAIMetricsRecorder` e `OllamaMetricsRecorder` implementam apenas a leitura de uso específica de cada provider
  - `BaseStreamHandler` / `StreamUsageTotals` — orçamento de iterações de tools e acumulação de métricas no streaming
- **Tools:**
  - `AvailableTools` — catálogo das tools nativas, com carga preguiçosa das que dependem de extras
  - `AvailableToolsRegistry` — adapta o catálogo à porta `ToolRegistry`
  - `CurrentDateTool` — ferramenta de data/hora
  - `ReadLocalFileTool` — leitura de arquivos (PDF, Excel, CSV, Parquet, JSON, YAML, TXT)
- **Factory:** `ChatAdapterFactory` — resolve o provider para o adapter concreto. Cada chamada devolve uma instância nova: o adapter é dono das métricas da conversa, então compartilhá-lo faria um agente reportar as métricas de outro.
- **Config:** `EnvironmentConfig`, `LoggingConfig`, `StandardLogger` (implementação de `LoggerInterface`)

______________________________________________________________________

## 🎨 Princípios SOLID

### Single Responsibility (SRP)

Cada classe tem uma única responsabilidade:

```python
Agent  # Representa um agente
History  # Gerencia histórico
ChatWithAgentUseCase  # Orquestra conversa
```

### Open/Closed (OCP)

Aberto para extensão, fechado para modificação:

```python
# Adicionar novo provider sem modificar código existente
class ClaudeAdapter(ChatRepository):
    async def chat(self, *args, **kwargs):
        pass

    def get_metrics(self) -> list[ChatMetrics]:
        return []
```

### Liskov Substitution (LSP)

Adapters são intercambiáveis:

```python
# Qualquer adapter pode substituir outro
adapter: ChatRepository = OpenAIChatAdapter()
# ou
adapter: ChatRepository = OllamaChatAdapter()
```

### Interface Segregation (ISP)

Interfaces específicas e focadas:

```python
class ChatRepository(ABC):
    @abstractmethod
    async def chat(
        self,
        model: str,
        instructions: str | None,
        config: dict[str, Any] | None,
        tools: list[BaseTool] | None,
        history: list[dict[str, str]],
        user_ask: str,
    ) -> str | AsyncGenerator[str, None]:
        pass

    @abstractmethod
    def get_metrics(self) -> list[ChatMetrics]:
        pass
```

### Dependency Inversion (DIP)

Depende de abstrações, não de implementações:

```python
class ChatWithAgentUseCase:
    def __init__(self, chat_repository: ChatRepository):  # Interface
        self.__chat_repository = chat_repository


# Exemplo com LoggerInterface (DIP no domínio)
class ToolExecutor:
    def __init__(
        self, tools: list[BaseTool], logger: LoggerInterface
    ):  # Abstrações
        self.__logger = logger  # Não depende de StandardLogger diretamente
```

______________________________________________________________________

## 🔧 Padrões de Design

### Repository Pattern

```python
class ChatRepository(ABC):
    @abstractmethod
    async def chat(
        self,
        model: str,
        instructions: str | None,
        config: dict[str, Any] | None,
        tools: list[BaseTool] | None,
        history: list[dict[str, str]],
        user_ask: str,
    ) -> str | AsyncGenerator[str, None]:
        pass

    @abstractmethod
    def get_metrics(self) -> list[ChatMetrics]:
        pass


class OpenAIChatAdapter(ChatRepository):
    async def chat(self, *args, **kwargs):  # Implementação assíncrona
        ...

    def get_metrics(self) -> list[ChatMetrics]:
        return []
```

### Factory Pattern

```python
class ChatAdapterFactory:
    @classmethod
    def create(
        cls,
        provider: str,
    ) -> ChatRepository:
        provider_lower = provider.lower()
        adapter: ChatRepository

        if provider_lower == 'openai':
            adapter = OpenAIChatAdapter()
        elif provider_lower == 'ollama':
            adapter = OllamaChatAdapter()
        else:
            raise ValueError(f'Invalid provider: {provider}.')
        return adapter
```

### Facade Pattern

```python
# CreateAgent é uma fachada simplificada
class CreateAgent:
    def __init__(self, provider: str, model: str, *args, **kwargs):
        # Esconde a complexidade da composição
        pass
```

### Value Object Pattern

```python
@dataclass(frozen=True)  # Imutável
class Message:
    role: MessageRole
    content: str
```

______________________________________________________________________

## 🔄 Fluxo de Dados

### 1. Fluxo Padrão Não-Streaming (`config={'stream': False}`)

```
User → CreateAgent.chat()
    → ChatWithAgentUseCase.execute() [async]
        → ChatRepository.chat() [async]
            → OpenAIChatAdapter / OllamaChatAdapter
                → OpenAIHandler / OllamaHandler (chamada HTTP direta)
                    → API Externa (OpenAI / Ollama)
                    ← Resposta completa da API
                ← Mensagem gerada + métricas consolidadas
            ← str (resposta final)
        ← str
    ← str
```

### 2. Fluxo Streaming com Consumo Completo (`await response`)

```
User → CreateAgent.chat() (com config={'stream': True})
    → ChatWithAgentUseCase.execute() [async]
        → ChatRepository.chat() [async]
            → OpenAIStreamHandler / OllamaStreamHandler
                → API Externa (OpenAI / Ollama)
                ← Chunks em streaming
            ← AsyncGenerator[str]
        ← StreamingResponseDTO(generator)
    ← await response
        → _consume() itera sobre o gerador, preenche _full_response e grava no cache
        ← str (resposta completa em cache)
```

### 3. Fluxo Streaming com Iteração Progressiva (`async for`)

```
User → CreateAgent.chat() (com config={'stream': True})
    → ChatWithAgentUseCase.execute() [async]
        → ChatRepository.chat() [async]
            → OpenAIStreamHandler / OllamaStreamHandler
                → API Externa (OpenAI / Ollama)
                ← Chunks em streaming
            ← AsyncGenerator[str]
        ← StreamingResponseDTO(generator)
    → async for token in response:
        → print(token, end='', flush=True)  # Exibe token por token
```

### 4. Fluxo CLI

```
Terminal → ChatCLIApplication.run()
    → CommandRegistry.find_handler(user_input)
        → CommandHandler.execute()
            → CreateAgent.chat() [se ChatCommandHandler]
                → await TerminalRenderer.render_ai_message_streaming(response)
```

______________________________________________________________________

## 💡 Benefícios da Arquitetura

### 🧪 Testabilidade

```python
# Mock fácil de dependências
mock_repo = Mock(spec=ChatRepository)
use_case = ChatWithAgentUseCase(mock_repo)
```

### 🔄 Flexibilidade

```python
# Trocar provider sem mudar código
from createagents import CreateAgent

agent = CreateAgent(provider='ollama', model='YOUR_OLLAMA_MODEL')
```

### 📈 Escalabilidade

- Adicionar novos providers facilmente
- Extensível via interfaces
- Preparado para crescimento

### 🛡️ Manutenibilidade

- Código organizado em camadas
- Responsabilidades claras
- Fácil localizar e corrigir bugs

______________________________________________________________________

## 🔄 Padrões Assíncronos

### Streaming com AsyncGenerator

```python
from collections.abc import AsyncGenerator, Generator


class StreamingResponseDTO:
    """DTO para encapsular geradores assíncronos com suporte a cache e await."""

    def __init__(self, generator: AsyncGenerator[str, None]) -> None:
        self._generator = generator
        self._consumed: bool = False
        self._full_response: str = ''

    def __aiter__(self) -> 'StreamingResponseDTO':
        return self

    async def __anext__(self) -> str:
        if self._consumed:
            raise StopAsyncIteration
        try:
            token = await self._generator.__anext__()
        except StopAsyncIteration:
            self._consumed = True
            raise
        self._full_response += token
        return token

    def __await__(self) -> Generator[object, None, str]:
        async def _consume() -> str:
            if self._consumed:
                return self._full_response
            async for _ in self:
                pass
            return self._full_response

        return _consume().__await__()
```

______________________________________________________________________

**Versão:** 0.2.0 | **Atualização:** 2026-08-27
