# 🏗️ Arquitetura

## Estrutura de Camadas

```
┌─────────────────────────────────────┐
│        PRESENTATION                 │
│     (AIAgent Controller)            │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│        APPLICATION                  │
│    (Use Cases, DTOs)                │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│          DOMAIN                     │
│  (Entities, Value Objects)          │
└──────────────▲──────────────────────┘
               │
┌──────────────┴──────────────────────┐
│      INFRASTRUCTURE                 │
│  (Adapters, Config, Factory)        │
└─────────────────────────────────────┘
```

## Camadas

### Domain (Domínio)

**Localização**: `src/domain/`

Contém as regras de negócio puras:

- **Agent**: Entidade principal
- **Message**: Value Object para mensagens
- **History**: Value Object para histórico
- **Exceções**: Erros de domínio

**Características**:

- Zero dependências externas
- Lógica de negócio pura
- Totalmente testável

### Application (Aplicação)

**Localização**: `src/application/`

Orquestra os casos de uso:

- **Use Cases**: CreateAgent, ChatWithAgent, GetAgentConfig
- **DTOs**: Transferência de dados entre camadas
- **Interfaces**: Contratos (ex: ChatRepository)

**Características**:

- Coordena entidades
- Define interfaces para infraestrutura
- Independente de frameworks

### Infrastructure (Infraestrutura)

**Localização**: `src/infra/`

Implementa detalhes técnicos:

- **Adapters**: OpenAI, Ollama
- **Factory**: Criação de adapters
- **Config**: Gerenciamento de ambiente

**Características**:

- Implementa interfaces da Application
- Substituível sem afetar regras de negócio

### Presentation (Apresentação)

**Localização**: `src/presentation/`

Interface com o usuário:

- **AIAgent**: Controller principal (fachada simplificada)

**Características**:

- Facilita o uso do sistema
- Pode ser substituída (CLI, API, GUI)

## Princípios SOLID

### Single Responsibility (SRP)

Cada classe tem uma única responsabilidade:

- `Agent`: Representa um agente
- `History`: Gerencia histórico
- `ChatWithAgentUseCase`: Orquestra conversa

### Open/Closed (OCP)

Aberto para extensão, fechado para modificação. Novos adapters podem ser adicionados criando novas classes que implementam `ChatRepository`.

### Liskov Substitution (LSP)

Adapters são intercambiáveis:

```python
# Qualquer adapter pode substituir outro
adapter: ChatRepository = OpenAIChatAdapter()
# ou
adapter: ChatRepository = OllamaChatAdapter()
```

### Interface Segregation (ISP)

Interfaces específicas:

```python
class ChatRepository(ABC):
    @abstractmethod
    def chat(self, ...) -> str:
        pass
```

### Dependency Inversion (DIP)

Depende de abstrações:

```python
class ChatWithAgentUseCase:
    def __init__(self, chat_repository: ChatRepository):  # ← Interface
        self.__chat_repository = chat_repository
```

## Padrões de Design

### Value Object

```python
@dataclass(frozen=True)
class Message:
    role: MessageRole
    content: str
```

### Repository

```python
class ChatRepository(ABC):
    @abstractmethod
    def chat(self, ...) -> str:
        pass
```

### Factory

```python
class ChatAdapterFactory:
    @staticmethod
    def create(model: str, local_ai: Optional[str] = None) -> ChatRepository:
        # Se local_ai especificado, usa Ollama
        # Se modelo contém 'gpt', usa OpenAI
        # Caso contrário, usa Ollama
```

### Singleton

```python
class EnvironmentConfig:
    _instance = None
    # Carrega .env apenas uma vez
```

## Fluxo de Dados

```
User → AIAgent.chat()
    → ChatWithAgentUseCase.execute()
        → ChatRepository.chat()
            → OpenAIChatAdapter/OllamaChatAdapter
                → OpenAI API / Ollama
            ← Response
        ← ChatOutputDTO
    ← response string
```

## Benefícios

### Testabilidade

```python
# Fácil mockar dependências
mock_repo = Mock(spec=ChatRepository)
use_case = ChatWithAgentUseCase(mock_repo)
```

### Flexibilidade

```python
# Trocar provider sem mudar código
factory.create(model="llama2", local_ai="ollama")
```

### Manutenibilidade

- Código organizado em camadas
- Responsabilidades claras
- Fácil localizar bugs

### Escalabilidade

- Adicionar providers facilmente
- Extensível via interfaces
- Preparado para crescimento
