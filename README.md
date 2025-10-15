# AI Agent Creator

Sistema modular para criação de agentes de IA com suporte a múltiplos provedores (OpenAI, Ollama).

## 🏗️ Arquitetura

Este projeto segue os princípios de **Clean Architecture**, **SOLID** e **Clean Code**.

### Estrutura de Camadas

```
src/
├── domain/              # Camada de Domínio (Regras de Negócio)
│   ├── entities/        # Entidades do domínio
│   └── exceptions/      # Exceções de negócio
│
├── application/         # Camada de Aplicação (Casos de Uso)
│   ├── use_cases/       # Use Cases
│   ├── dtos/            # Data Transfer Objects
│   └── interfaces/      # Contratos/Abstrações
│
├── infra/               # Camada de Infraestrutura (Detalhes Técnicos)
│   ├── adapters/        # Implementações de adapters externos
│   ├── config/          # Configurações
│   └── factories/       # Factories para criação de objetos
│
├── main/                # Camada de Composição
│   └── composers/       # Composers para Dependency Injection
│
└── presentation/        # Camada de Apresentação (Interface)
    └── agent_controller.py
```

## 🚀 Uso

### Exemplo básico

```python
from src.presentation import AIAgent

# Criar agente
agent = AIAgent(
    model="gpt-4",
    name="Assistente",
    instructions="Você é um assistente útil"
)

# Conversar
response = agent.chat("Olá, como você está?")
print(response)

# Ver configurações
config = agent.get_configs()
print(config)
```

### Usando Ollama

```python
agent = AIAgent(
    model="llama2",
    name="Assistente Local",
    instructions="Você é um assistente útil",
    local_ai="ollama"
)
```

## 📦 Componentes Principais

### Domain Layer

- **Agent**: Entidade que representa um agente de IA
- **Exceptions**: Exceções customizadas do domínio

### Application Layer

- **CreateAgentUseCase**: Criação de agentes
- **ChatWithAgentUseCase**: Comunicação com agentes
- **GetAgentConfigUseCase**: Obtenção de configurações
- **DTOs**: Objetos de transferência de dados

### Infrastructure Layer

- **OpenAIChatAdapter**: Implementação para OpenAI
- **OllamaChatAdapter**: Implementação para Ollama
- **ChatAdapterFactory**: Factory para criar adapters
- **EnvironmentConfig**: Gerenciamento de variáveis de ambiente

### Main Layer

- **AgentComposer**: Orquestra criação e injeção de dependências

### Presentation Layer

- **AIAgentController**: Interface principal para usuários

## 🔒 Exceções

- `AgentException`: Base para exceções de agente
- `InvalidAgentConfigException`: Configuração inválida
- `InvalidModelException`: Modelo não suportado
- `ChatException`: Erro na comunicação
- `AdapterNotFoundException`: Adapter não encontrado

## 📋 Variáveis de Ambiente

Crie um arquivo `.env`:

```
OPENAI_API_KEY=sua_chave_aqui
```

## 🤝 Contribuindo

Ao adicionar novos adapters:

1. Implemente a interface `ChatRepository`
2. Adicione ao `MODELS_AI` em `ChatAdapterFactory`
3. Crie testes unitários

## 📚 Referências

- [Clean Architecture - Robert C. Martin](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [SOLID Principles](https://en.wikipedia.org/wiki/SOLID)
- [Clean Code - Robert C. Martin](https://www.amazon.com/Clean-Code-Handbook-Software-Craftsmanship/dp/0132350882)
