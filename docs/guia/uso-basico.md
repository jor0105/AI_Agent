# 🎯 Uso Básico

## Criar um Agente

```python
from src import AIAgent

agent = AIAgent(
    model="gpt-4",           # Modelo a usar
    name="Assistente",       # Nome do agente
    instructions="Você é um assistente útil."  # Comportamento
)
```

## Conversar

```python
# Primeira mensagem
response = agent.chat("Olá, como você está?")
print(response)

# O histórico é mantido automaticamente
response = agent.chat("Qual é a capital do Brasil?")
print(response)

# Usa contexto anterior
response = agent.chat("E qual é a população dessa cidade?")
print(response)
```

## Obter Configurações

```python
config = agent.get_configs()

print(f"Nome: {config['name']}")
print(f"Modelo: {config['model']}")
print(f"Mensagens no histórico: {len(config['history'])}")
```

## Personalizar Comportamento

```python
# Assistente de código
code_agent = AIAgent(
    model="gpt-4",
    name="Code Helper",
    instructions="""
    Você é um especialista em Python.
    Forneça código limpo e bem documentado.
    Explique suas decisões.
    """
)

# Tradutor
translator = AIAgent(
    model="gpt-3.5-turbo",
    name="Tradutor",
    instructions="Você é um tradutor profissional."
)
```

## Tratamento de Erros

```python
from src.domain.exceptions import ChatException, InvalidAgentConfigException

try:
    agent = AIAgent(model="gpt-4", name="Test", instructions="...")
    response = agent.chat("Hello!")

except InvalidAgentConfigException as e:
    print(f"Configuração inválida: {e}")

except ChatException as e:
    print(f"Erro no chat: {e}")
```

## Histórico de Conversas

O histórico mantém automaticamente as últimas **10 mensagens** para otimizar custos e performance.

```python
# Ver histórico
config = agent.get_configs()
for msg in config['history']:
    print(f"{msg['role']}: {msg['content']}")
```
