# 💡 Exemplos Práticos

## Assistente de Código

```python
from src import AIAgent

code_assistant = AIAgent(
    model="gpt-4",
    name="Python Expert",
    instructions="""
    Você é um especialista em Python.
    Forneça código limpo seguindo PEP 8.
    Explique suas decisões de design.
    """
)

response = code_assistant.chat(
    "Como implementar um decorator de cache?"
)
print(response)
```

## Tradutor

```python
translator = AIAgent(
    model="gpt-3.5-turbo",
    name="Tradutor",
    instructions="""
    Você é um tradutor profissional.
    Traduza preservando tom e contexto.
    """
)

response = translator.chat(
    "Traduza para inglês: Olá, como você está?"
)
print(response)
```

## Analista de Dados

```python
data_analyst = AIAgent(
    model="gpt-4",
    name="Data Analyst",
    instructions="""
    Você é um analista de dados.
    Forneça insights acionáveis.
    Explique estatísticas de forma clara.
    """
)

data = "Vendas: Jan=100, Fev=150, Mar=120"
response = data_analyst.chat(f"Analise: {data}")
print(response)
```

## Chatbot Interativo

```python
from src import AIAgent

agent = AIAgent(
    model="gpt-4",
    name="Chatbot",
    instructions="Você é um assistente amigável."
)

print("Chatbot iniciado! Digite 'sair' para encerrar.\n")

while True:
    user_input = input("Você: ")

    if user_input.lower() == 'sair':
        break

    response = agent.chat(user_input)
    print(f"Bot: {response}\n")

# Mostrar estatísticas
config = agent.get_configs()
print(f"\nTotal de mensagens: {len(config['history'])}")
```

## IA Local com Ollama

```python
local_agent = AIAgent(
    model="llama2",
    name="Assistente Local",
    instructions="Você é um assistente útil.",
    local_ai="ollama"
)

# Privacidade total - roda localmente
response = local_agent.chat("Explique machine learning")
print(response)
```

## Sistema Multi-Agente

```python
from src import AIAgent

# Criar múltiplos agentes especializados
agents = {
    "python": AIAgent(
        model="gpt-4",
        name="Python Expert",
        instructions="Especialista em Python."
    ),
    "tradutor": AIAgent(
        model="gpt-3.5-turbo",
        name="Tradutor",
        instructions="Tradutor profissional."
    ),
}

# Usar agente específico
response = agents["python"].chat("Explique decorators")
print(response)

response = agents["tradutor"].chat("Traduza: Hello World")
print(response)
```

## Análise de Código

```python
code_reviewer = AIAgent(
    model="gpt-4",
    name="Code Reviewer",
    instructions="""
    Você revisa código seguindo Clean Code.
    Identifique problemas e sugira melhorias.
    """
)

code = """
def calc(a,b):
    return a+b
"""

review = code_reviewer.chat(f"Revise este código:\n\n{code}")
print(review)
```

## Assistente de Escrita

```python
writer = AIAgent(
    model="gpt-4",
    name="Writing Assistant",
    instructions="""
    Você ajuda a escrever textos profissionais.
    Corrija gramática e melhore clareza.
    """
)

text = "Eu preciso de ajuda para escrever um email profissional"
response = writer.chat(text)
print(response)
```
