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
│        APPLICATION                  │  Facade (CreateAgent)
│     (Application Logic)             │  Use Cases, DTOs, Services
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│          DOMAIN                     │  Entities, Rules, Interfaces
│     (Business Rules)                │  Agent, ToolExecutor, LoggerInterface
└──────────────▲──────────────────────┘
               │
┌──────────────┴──────────────────────┐
│      INFRASTRUCTURE                 │  Adapters, Handlers, Config
│     (Technical Details)             │  OpenAI, Ollama, Tools, Metrics
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

### 2. Application

**Location:** `src/createagents/application/`

**Responsibility:** Orchestrating use cases and enforcing application flow.

**Components:**

- **Facade / Controller:** `CreateAgent` — lives in `main/facade/`, exposes `chat` (async), `get_configs`, `get_all_available_tools`, `clear_history`, `export_metrics_*`.
- **Use Cases (`application/use_cases`):**
  - `CreateAgentUseCase` — creates and validates agents, resolving tool names via the `ToolRegistry` port (invoked by `AgentComposer`).
  - `ChatWithAgentUseCase` — orchestrates **asynchronous** messages between `Agent` and `ChatRepository` (adapters).
  - `GetAgentConfigUseCase` — retrieves agent configuration.
  - `GetSystemAvailableToolsUseCase` — lists built-in framework tools.
- **DTOs (`application/dtos`):** Data transfer objects:
  - `CreateAgentInputDTO`, `ChatInputDTO`, `AgentConfigOutputDTO` — data transfer between facade and use cases.
  - **`StreamingResponseDTO`** — wrapper for `AsyncGenerator` allowing both async iteration and await of streaming responses.
- **Interfaces (`application/interfaces`):** Ports implemented by infrastructure:
  - `ChatRepository` — contract for chat adapters, with **asynchronous** support.
  - `ToolRegistry` — tool catalog queries without coupling application to infrastructure.

______________________________________________________________________

### 3. Domain

**Location:** `src/createagents/domain/`

**Responsibility:** Pure enterprise business rules, independent of frameworks or external libraries.

**Components:**

- **Entities:** `Agent` (core entity)
- **Value Objects:** `Message`, `MessageRole`, `History`, `SupportedConfigs`, `SupportedProviders`, `BaseTool` (tools contract), `ChatMetrics`
- **Domain Services:** `ToolExecutor` (**asynchronous** tool execution), `ToolExecutionResult`
- **Interfaces (`domain/interfaces`):** **`LoggerInterface`** — logging abstraction in the domain (DIP - Dependency Inversion Principle)
- **Exceptions:** `domain.exceptions` (e.g. `AgentException`, `InvalidAgentConfigException`, `UnsupportedConfigException`)

______________________________________________________________________

### 4. Infrastructure

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
- **Config:** `EnvironmentConfig`, `LoggingConfig`, `StandardLogger` (implements `LoggerInterface`), `ChatMetrics`

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
    async def chat(self, ...):
        pass
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
    async def chat(self, ...):  # Async implementation
        ...

    def get_metrics(self) -> list[ChatMetrics]:
        ...
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
    def __init__(self, provider, model, ...):
        self.__agent = AgentComposer.create_agent(...)
        self.__chat_use_case = AgentComposer.create_chat_use_case(...)
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

### Synchronous Consumption Flow (`await response`)

```
User → CreateAgent.chat()
    → ChatWithAgentUseCase.execute() [async]
        → ChatRepository.chat() [async]
            → OpenAIHandler / OllamaHandler
                → StreamHandler (handles streaming)
                    → External API (OpenAI / Ollama)
                    ← Stream tokens
                ← Complete response string
            ← AsyncGenerator
        ← StreamingResponseDTO
    ← await response (complete string)
```

### Asynchronous Streaming Flow (`async for`)

```
User → CreateAgent.chat()
    → ChatWithAgentUseCase.execute() [async]
        → ChatRepository.chat() [async]
            → StreamHandler.handle_stream()
                → async for token in api_stream:
                    → yield token  # Real-time streaming
            ← AsyncGenerator[str]
        ← StreamingResponseDTO
    → async for token in response:
        → print(token, end='')  # Output token by token
```

### CLI Flow

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
agent = CreateAgent(provider='ollama', model='llama3.2')
```

### 📈 Scalability

- New providers added via adapters without modifying domain logic
- Tool contracts isolated from transport layers
- Production-ready metrics and logging hooks

______________________________________________________________________

## 🔄 Asynchronous Patterns

### Streaming with `StreamingResponseDTO`

```python
# Handlers yield tokens as an AsyncGenerator
async def handle_stream(self, ...) -> AsyncGenerator[str, None]:
    async for chunk in api_response:
        yield chunk


# DTO encapsulates the generator for flexible consumption
class StreamingResponseDTO:
    def __init__(self, generator: AsyncGenerator[str, None]):
        self._generator = generator

    def __aiter__(self):  # Allows async for
        return self

    async def __anext__(self):
        return await self._generator.__anext__()

    def __await__(self):  # Allows direct await
        async def _consume():
            return ''.join([token async for token in self])

        return _consume().__await__()
```

______________________________________________________________________

**Version:** 0.2.0 | **Updated:** 2026-08-25
