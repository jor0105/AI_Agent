# 📚 API Reference

## AIAgent

Interface principal para criar e gerenciar agentes.

### Construtor

```python
AIAgent(
    model: str,
    name: str,
    instructions: str,
    local_ai: Optional[str] = None
)
```

**Parâmetros**:

- `model` (str): Modelo de IA ("gpt-4", "gpt-3.5-turbo", "llama2")
- `name` (str): Nome do agente
- `instructions` (str): Prompt que define comportamento
- `local_ai` (str, opcional): Provider local ("ollama")

**Exemplo**:

```python
agent = AIAgent(
    model="gpt-4",
    name="Assistente",
    instructions="Você é útil."
)
```

### Métodos

#### chat()

```python
def chat(message: str) -> str
```

Envia mensagem e retorna resposta.

**Parâmetros**:

- `message` (str): Mensagem do usuário

**Retorna**: str com a resposta

**Exemplo**:

```python
response = agent.chat("Olá!")
print(response)
```

#### get_configs()

```python
def get_configs() -> Dict[str, Any]
```

Retorna configurações do agente.

**Retorna**: Dicionário com:

- `name`: Nome do agente
- `model`: Modelo usado
- `instructions`: Prompt
- `history`: Lista de mensagens
- `local_ai`: Provider local

**Exemplo**:

```python
config = agent.get_configs()
print(config['name'])
```

## Exceções

### InvalidAgentConfigException

Lançada quando configuração é inválida.

```python
from src.domain.exceptions import InvalidAgentConfigException

try:
    agent = AIAgent(model="", name="Test", instructions="...")
except InvalidAgentConfigException as e:
    print(f"Erro: {e}")
```

### ChatException

Lançada quando há erro na comunicação.

```python
from src.domain.exceptions import ChatException

try:
    response = agent.chat("Hello")
except ChatException as e:
    print(f"Erro: {e}")
```

### InvalidModelException

Lançada quando modelo não é suportado.

```python
from src.domain.exceptions import InvalidModelException

try:
    agent = AIAgent(model="invalid", ...)
except InvalidModelException as e:
    print(f"Erro: {e}")
```

## Value Objects

### MessageRole

Enum para roles de mensagens:

```python
from src.domain import MessageRole

MessageRole.USER       # "user"
MessageRole.ASSISTANT  # "assistant"
MessageRole.SYSTEM     # "system"
```

### Message

Representa uma mensagem:

```python
from src.domain import Message, MessageRole

msg = Message(
    role=MessageRole.USER,
    content="Hello"
)

# Converter para dict
dict_msg = msg.to_dict()
# {"role": "user", "content": "Hello"}
```

### History

Gerencia histórico de mensagens:

```python
from src.domain import History

history = History(MAX_SIZE=10)
history.add_user_message("Hello")
history.add_assistant_message("Hi!")

# Converter para lista
messages = history.to_dict_list()
```

## Use Cases

### CreateAgentUseCase

Cria novos agentes:

```python
from src.application import CreateAgentUseCase, CreateAgentInputDTO

use_case = CreateAgentUseCase()
input_dto = CreateAgentInputDTO(
    model="gpt-4",
    name="Test",
    instructions="Test"
)
agent = use_case.execute(input_dto)
```

### ChatWithAgentUseCase

Gerencia conversas:

```python
from src.application import ChatWithAgentUseCase, ChatInputDTO

use_case = ChatWithAgentUseCase(chat_repository)
input_dto = ChatInputDTO(message="Hello")
output = use_case.execute(agent, input_dto)
print(output.response)
```

### GetAgentConfigUseCase

Obtém configurações:

```python
from src.application import GetAgentConfigUseCase

use_case = GetAgentConfigUseCase()
config = use_case.execute(agent)
print(config.to_dict())
```

## Tipos Disponíveis

```python
# Importações principais
from src import (
    AIAgent,           # Controller principal
    Agent,             # Entidade
    Message,           # Value Object
    MessageRole,       # Enum
    History,           # Value Object
)

# Use Cases
from src.application import (
    CreateAgentUseCase,
    ChatWithAgentUseCase,
    GetAgentConfigUseCase,
)

# DTOs
from src.application import (
    CreateAgentInputDTO,
    AgentConfigOutputDTO,
    ChatInputDTO,
    ChatOutputDTO,
)

# Exceções
from src.domain.exceptions import (
    InvalidAgentConfigException,
    InvalidModelException,
    ChatException,
    AdapterNotFoundException,
)
```
