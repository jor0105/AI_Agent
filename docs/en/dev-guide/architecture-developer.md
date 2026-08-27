# 🏗️ Architecture Guide for Developers

Comprehensive architectural documentation for **Create Agents AI**, based on **Clean Architecture** and **SOLID principles**.

______________________________________________________________________

## 📐 Layer Structure

```
┌─────────────────────────────────────┐
│       PRESENTATION                  │  CLI, UI (ChatCLIApplication)
│       (User Interface)              │  Command Handlers, Terminal UI
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│           MAIN                      │  Facade (CreateAgent),
│    (Composition Root)               │  AgentComposer, Factories
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│        APPLICATION                  │  Use Cases, DTOs,
│     (Application Logic)             │  Ports/Interfaces (ChatRepository)
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│          DOMAIN                     │  Entities (Agent, History),
│     (Business Rules)                │  Value Objects (ChatMetrics, Message),
└──────────────▲──────────────────────┘  Domain Services, LoggerInterface
               │
┌──────────────┴──────────────────────┐
│      INFRASTRUCTURE                 │  Adapters, Clients, Handlers,
│     (Technical Details)             │  OpenAI, Ollama, Tools, Config
└─────────────────────────────────────┘
```

______________________________________________________________________

## 🎯 Layer Breakdown

### 1. Presentation

**Location:** `src/createagents/presentation/`

**Responsibility:** User interface, interaction, and terminal presentation.

**Components:**

- **CLI Application:** `ChatCLIApplication` — interactive CLI application for chatting with agents
- **Command Handlers:** System based on the **Command Pattern**
  - `ChatCommandHandler` — chat message handling (fallback)
  - `HelpCommandHandler` — displays help and command index
  - `MetricsCommandHandler` — renders performance metrics
  - `ConfigsCommandHandler` — displays agent configuration
  - `ToolsCommandHandler` — lists available tools
  - `ClearCommandHandler` — clears conversation history
- **UI Components:** `TerminalRenderer`, `TerminalFormatter`, `ColorScheme` — ANSI and Rich rendering
- **I/O:** `InputReader` — user input reading
- **Registry:** `CommandRegistry` — handler registration and lookup

______________________________________________________________________

### 2. Main (Composition Root & Facade)

**Location:** `src/createagents/main/`

**Responsibility:** Composition root that wires dependencies together and provides the public facade.

**Components:**

- **Facade (`main/facade/`):** `CreateAgent` — developer-facing entrypoint exposing `chat` (async), `get_configs`, `get_all_available_tools`, `clear_history`, `export_metrics_*`, and `start_cli`.
- **Composer (`main/composers/`):** `AgentComposer` — wires application use cases with infrastructure adapters and dependencies.

______________________________________________________________________

### 3. Application

**Location:** `src/createagents/application/`

**Responsibility:** Orchestrating use cases and enforcing application flow, depending only on the domain layer.

**Components:**

- **Use Cases (`application/use_cases`):**
  - `CreateAgentUseCase` — creates and validates agents, resolving tool names via the `ToolRegistry` port.
  - `ChatWithAgentUseCase` — orchestrates **asynchronous** messages between `Agent` and the `ChatRepository` port.
  - `GetAgentConfigUseCase` — retrieves agent configuration.
  - `GetSystemAvailableToolsUseCase` — lists built-in framework tools.
- **DTOs (`application/dtos`):** Data transfer objects:
  - `CreateAgentInputDTO`, `ChatInputDTO`, `AgentConfigOutputDTO`
  - **`StreamingResponseDTO`** — wrapper for `AsyncGenerator` allowing both async iteration (`async for`) and `await` with cached response.
- **Interfaces (`application/interfaces`):** Ports implemented by infrastructure:
  - `ChatRepository` — contract for chat provider adapters.
  - `ToolRegistry` — tool catalog queries without coupling application to infrastructure.

______________________________________________________________________

### 4. Domain

**Location:** `src/createagents/domain/`

**Responsibility:** Pure enterprise business rules, independent of frameworks or external libraries.

**Components:**

- **Entities:** `Agent` (core entity), `History` (conversation history entity)
- **Value Objects:** `Message`, `MessageRole`, `ChatMetrics`, `SupportedConfigs`, `SupportedProviders`, `BaseTool`
- **Domain Services:** `ToolExecutor` (asynchronous/synchronous tool execution), `ToolExecutionResult`
- **Interfaces (`domain/interfaces`):** `LoggerInterface` — logging abstraction in the domain
- **Exceptions:** `domain.exceptions` (`AgentException`, `InvalidAgentConfigException`, etc.)

______________________________________________________________________

### 5. Infrastructure

**Location:** `src/createagents/infra/`

**Responsibility:** Technical details, external providers, file I/O, and platform implementations.

**Components:**

- **Adapters (Chat):**
  - `OpenAIChatAdapter` — OpenAI integration
  - `OllamaChatAdapter` — Ollama integration
- **Handlers (Async Streaming):**
  - `OpenAIHandler` / `OpenAIStreamHandler` — non-streaming and streaming OpenAI processors
  - `OllamaHandler` / `OllamaStreamHandler` — non-streaming and streaming Ollama processors
- **Clients:**
  - `OpenAIClient` — HTTP client wrapper for OpenAI
  - `OllamaClient` — HTTP client wrapper for Ollama
- **Common Adapters:**
  - `MetricsRecorder` — abstract base for metrics recording; `OpenAIMetricsRecorder` and `OllamaMetricsRecorder` implement provider-specific usage parsing
  - `BaseStreamHandler` / `StreamUsageTotals` — tool call iteration budget and streaming metrics accumulation
- **Tools:**
  - `AvailableTools` — native tools catalog with lazy loading for extra dependencies
  - `AvailableToolsRegistry` — adapts the catalog to the `ToolRegistry` port
  - `CurrentDateTool` — date/time tool
  - `ReadLocalFileTool` — multi-format file reader (PDF, Excel, CSV, Parquet, JSON, YAML, TXT)
- **Factory:** `ChatAdapterFactory` — instantiates provider adapters. Each call creates a fresh adapter instance so metrics remain isolated per agent.
- **Config:** `EnvironmentConfig`, `LoggingConfig`, `StandardLogger` (implements `LoggerInterface`)

______________________________________________________________________

## 🎨 SOLID Principles

### Single Responsibility (SRP)

Each class has a single, well-defined reason to change:

```python
Agent  # Represents an agent entity and state
History  # Manages message history collection
ChatWithAgentUseCase  # Orchestrates conversation flow
```

### Open/Closed (OCP)

Open for extension, closed for modification:

```python
# Add a new provider without modifying existing code
class ClaudeAdapter(ChatRepository):
    async def chat(self, *args, **kwargs):
        pass

    def get_metrics(self) -> list[ChatMetrics]:
        return []
```

### Liskov Substitution (LSP)

Adapters conform to contracts and are interchangeable:

```python
# Any adapter satisfies ChatRepository
adapter: ChatRepository = OpenAIChatAdapter()
# or
adapter: ChatRepository = OllamaChatAdapter()
```

### Interface Segregation (ISP)

Focused, client-driven interfaces:

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

Depend on abstractions, not concrete implementations:

```python
class ChatWithAgentUseCase:
    def __init__(self, chat_repository: ChatRepository):  # Interface port
        self.__chat_repository = chat_repository


# Example with LoggerInterface (DIP in domain)
class ToolExecutor:
    def __init__(
        self, tools: list[BaseTool], logger: LoggerInterface
    ):  # Abstractions
        self.__logger = logger  # Does not depend on StandardLogger directly
```

______________________________________________________________________

## 🔧 Design Patterns

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
    async def chat(self, *args, **kwargs):  # Async implementation
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
# CreateAgent provides a unified, developer-friendly facade
class CreateAgent:
    def __init__(self, provider: str, model: str, *args, **kwargs):
        pass
```

### Value Object Pattern

```python
@dataclass(frozen=True)  # Immutable
class Message:
    role: MessageRole
    content: str
```

______________________________________________________________________

## 🔄 Data Flows

### 1. Default Non-Streaming Flow (`config={'stream': False}`)

```
User → CreateAgent.chat()
    → ChatWithAgentUseCase.execute() [async]
        → ChatRepository.chat() [async]
            → OpenAIChatAdapter / OllamaChatAdapter
                → OpenAIHandler / OllamaHandler (direct HTTP call)
                    → External API (OpenAI / Ollama)
                    ← Complete response from API
                ← Generated message + recorded metrics
            ← str (final response)
        ← str
    ← str
```

### 2. Streaming Flow with Complete Consumption (`await response`)

```
User → CreateAgent.chat() (with config={'stream': True})
    → ChatWithAgentUseCase.execute() [async]
        → ChatRepository.chat() [async]
            → OpenAIStreamHandler / OllamaStreamHandler
                → External API (OpenAI / Ollama)
                ← Stream chunks
            ← AsyncGenerator[str]
        ← StreamingResponseDTO(generator)
    ← await response
        → _consume() drains the generator, populates _full_response in cache
        ← str (complete cached string)
```

### 3. Streaming Flow with Progressive Iteration (`async for`)

```
User → CreateAgent.chat() (with config={'stream': True})
    → ChatWithAgentUseCase.execute() [async]
        → ChatRepository.chat() [async]
            → OpenAIStreamHandler / OllamaStreamHandler
                → External API (OpenAI / Ollama)
                ← Stream chunks
            ← AsyncGenerator[str]
        ← StreamingResponseDTO(generator)
    → async for token in response:
        → print(token, end='', flush=True)  # Output token by token
```

### 4. CLI Flow

```
Terminal → ChatCLIApplication.run()
    → CommandRegistry.find_handler(user_input)
        → CommandHandler.execute()
            → CreateAgent.chat() [if ChatCommandHandler]
                → await TerminalRenderer.render_ai_message_streaming(response)
```

______________________________________________________________________

## 💡 Architectural Benefits

### 🧪 Testability

```python
# Clean dependency mocking
mock_repo = Mock(spec=ChatRepository)
use_case = ChatWithAgentUseCase(mock_repo)
```

### 🔄 Flexibility

```python
# Seamless provider switching without code changes
from createagents import CreateAgent

agent = CreateAgent(provider='ollama', model='llama3.2')
```

### 📈 Scalability

- New providers added via adapters without modifying domain logic
- Tool contracts isolated from transport layers
- Production-ready metrics and logging hooks

### 🛡️ Maintainability

- Code cleanly segregated into independent layers
- Clear single responsibilities
- Straightforward to isolate and fix bugs

______________________________________________________________________

## 🔄 Asynchronous Patterns

### Streaming with `StreamingResponseDTO`

```python
from collections.abc import AsyncGenerator, Generator


class StreamingResponseDTO:
    """DTO wrapping an AsyncGenerator with caching and await support."""

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

**Version:** 0.2.0 | **Updated:** 2026-08-25
