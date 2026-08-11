# 🛠️ Ferramentas (Tools)

Este guia explica as ferramentas disponíveis para seus agentes de IA e como usá-las.

______________________________________________________________________

## 📦 Visão Geral

Ferramentas são **capacidades adicionais** que seus agentes podem usar para executar tarefas específicas. Para manter o sistema leve, algumas ferramentas com dependências pesadas são **opcionais**.

______________________________________________________________________

## 🎯 Ferramentas Disponíveis

### ✅ CurrentDateTool (Sempre Disponível)

Obtém data e hora atuais em qualquer timezone.

**Dependências:** Nenhuma (biblioteca padrão Python)

**Uso:**

```python
import asyncio
from createagents import CreateAgent

async def main():
    agent = CreateAgent(
        provider="openai",
        model="gpt-4",
        tools=["currentdate"]
    )

    resposta = await agent.chat("Que dia é hoje?")
    print(resposta)

asyncio.run(main())
```

**Ações suportadas:**

- `date` - Data (YYYY-MM-DD)
- `time` - Hora (HH:MM:SS)
- `datetime` - Data e hora completos
- `timestamp` - Unix timestamp
- `date_with_weekday` - Data com dia da semana

______________________________________________________________________

### 🔧 ReadLocalFileTool (Opcional)

Lê arquivos locais em múltiplos formatos.

**Formatos:** TXT, MD, CSV, Excel (XLS/XLSX), PDF, Parquet, JSON, YAML

**Dependências:** `tiktoken`, `unstructured`, `pandas`, `openpyxl`, `pyarrow`, `chardet`

**Instalação:**

```bash
pip install createagents[file-tools]
```

**Uso:**

```python
import asyncio
from createagents import CreateAgent

async def main():
    agent = CreateAgent(
        provider="openai",
        model="gpt-4",
        tools=["readlocalfile"]
    )

    resposta = await agent.chat("Leia o arquivo report.pdf e resuma")
    print(resposta)

asyncio.run(main())
```

**Limites:**

- Tamanho máximo: 100MB
- Tokens máximos: Depende da AI utilizada

**Funcionalidades:**

- ✅ Validação de tamanho
- ✅ Detecção automática de encoding
- ✅ Suporte a múltiplos formatos
- ✅ Tratamento robusto de erros

______________________________________________________________________

## 🚀 Uso com Agentes

### Exemplo 1: Ferramenta de Data

```python
import asyncio

async def main():
    agent = CreateAgent(
        provider="openai",
        model="gpt-4",
        instructions="Você pode verificar data/hora quando necessário",
        tools=["currentdate"]
    )

    # O agente usa a ferramenta automaticamente
    resposta = await agent.chat("Que dia da semana é hoje?")
    print(resposta)

asyncio.run(main())
```

### Exemplo 2: Leitura de Arquivos

```python
import asyncio

async def main():
    # Certifique-se que instalou: pip install createagents[file-tools]
    agent = CreateAgent(
        provider="openai",
        model="gpt-4",
        instructions="Você pode ler arquivos locais",
        tools=["readlocalfile"]
    )

    resposta = await agent.chat("Resuma o documento relatorio.pdf")
    print(resposta)

asyncio.run(main())
```

### Exemplo 3: Múltiplas Ferramentas

```python
import asyncio

async def main():
    agent = CreateAgent(
        provider="openai",
        model="gpt-4",
        tools=["currentdate", "readlocalfile"]
    )

    # O agente escolhe qual ferramenta usar
    resposta1 = await agent.chat("Que dia é hoje?")  # Usa currentdate
    print(resposta1)

    resposta2 = await agent.chat("Leia notas.txt")   # Usa readlocalfile
    print(resposta2)

asyncio.run(main())
```

______________________________________________________________________

## 📋 Checklist de Instalação

### Instalação Básica ✅

```bash
pip install createagents
```

Inclui:

- [x] CurrentDateTool
- [x] Gerenciamento de histórico
- [x] Métricas de performance
- [x] OpenAI e Ollama adapters

### Instalação com File Tools 📁

```bash
pip install createagents[file-tools]
```

Inclui:

- [x] Tudo da instalação básica
- [x] ReadLocalFileTool
- [x] Suporte para PDF, Excel, CSV, Parquet

______________________________________________________________________

## 🔍 Verificar Ferramentas Disponíveis

### Verificar Ferramentas do Agente

Use `get_all_available_tools()` para ver todas as ferramentas disponíveis para um agente específico (inclui ferramentas do sistema + ferramentas customizadas adicionadas ao agente):

```python
from createagents import CreateAgent, BaseTool

class CustomTool(BaseTool):
    name = "custom_tool"
    description = "Minha ferramenta customizada"
    parameters = {
        "type": "object",
        "properties": {
            "input": {"type": "string", "description": "Texto de entrada para a ferramenta"}
        },
        "required": ["input"]
    }

    def execute(self, input: str) -> str:
        return f"Resultado para: {input}"

agent = CreateAgent(
    provider="openai",
    model="gpt-4",
    tools=["currentdate", CustomTool()]  # Ferramenta do sistema + customizada
)

# Obter todas as ferramentas deste agente
tools = agent.get_all_available_tools()

print("Ferramentas disponíveis neste agente:")
for name, description in tools.items():
    print(f"  - {name}: {description[:50]}...")

# Exemplo de saída:
# - currentdate: Get the current date and/or time...
# - readlocalfile: Use this tool to read local files...
# - custom_tool: Minha ferramenta customizada
```

### Verificar Apenas Ferramentas do Sistema

Use `get_system_available_tools()` para ver apenas as ferramentas built-in disponíveis globalmente (não inclui ferramentas customizadas):

```python
from createagents import CreateAgent

agent = CreateAgent(provider="openai", model="gpt-4")

# Obter apenas ferramentas do sistema
system_tools = agent.get_system_available_tools()

print("Ferramentas do sistema disponíveis:")
for name, description in system_tools.items():
    print(f"  - {name}: {description[:50]}...")

# Verificar se uma ferramenta específica está disponível
if "readlocalfile" in system_tools:
    print("✅ ReadLocalFileTool disponível!")
else:
    print("⚠️ Instale com: pip install createagents[file-tools]")
```

### Diferença Entre os Métodos

| Método                         | Retorna                                         | Quando Usar                                                 |
| ------------------------------ | ----------------------------------------------- | ----------------------------------------------------------- |
| `get_all_available_tools()`    | Ferramentas do sistema + customizadas do agente | Para ver todas as ferramentas que o agente pode usar        |
| `get_system_available_tools()` | Apenas ferramentas do sistema (built-in)        | Para verificar quais ferramentas opcionais estão instaladas |

### Exemplo Prático

```python
from createagents import CreateAgent, BaseTool

# Ferramenta customizada
class WeatherTool(BaseTool):
    name = "weather"
    description = "Consulta previsão do tempo"
    parameters = {
        "type": "object",
        "properties": {
            "city": {"type": "string", "description": "Nome da cidade para consulta"}
        },
        "required": ["city"]
    }

    def execute(self, city: str) -> str:
        return f"Previsão para {city}: Ensolarado"

# Agente sem ferramentas customizadas
agent1 = CreateAgent(provider="openai", model="gpt-4")
print("Agente 1:", agent1.get_all_available_tools().keys())
# Saída: dict_keys(['currentdate', 'readlocalfile'])

# Agente com ferramentas customizadas
agent2 = CreateAgent(
    provider="openai",
    model="gpt-4",
    tools=["currentdate", WeatherTool()]
)
print("Agente 2:", agent2.get_all_available_tools().keys())
# Saída: dict_keys(['currentdate', 'readlocalfile', 'weather'])

# Ferramentas do sistema (sempre igual para todos os agentes)
print("Sistema:", agent1.get_system_available_tools().keys())
# Saída: dict_keys(['currentdate', 'readlocalfile'])
```

### Evitando Duplicatas

O sistema automaticamente evita duplicatas de ferramentas. Se você adicionar uma ferramenta do sistema à lista de tools do agente, ela aparecerá apenas uma vez:

```python
# Ferramenta do sistema adicionada explicitamente
agent = CreateAgent(
    provider="openai",
    model="gpt-4",
    tools=["currentdate"]  # Adiciona explicitamente uma ferramenta do sistema
)

# Não haverá duplicatas
tools = agent.get_all_available_tools()
# 'currentdate' aparece apenas UMA vez
print(list(tools.keys()))  # ['currentdate', 'readlocalfile']
```

______________________________________________________________________

## ⚡ Performance

### Uso de Memória

| Instalação     | Memória Base | Com ReadLocalFileTool |
| -------------- | ------------ | --------------------- |
| Básica         | ~50MB        | N/A                   |
| Com file-tools | ~50MB        | ~200MB (quando usada) |

______________________________________________________________________

## 🎨 Criar Suas Próprias Ferramentas

### Ferramenta Própria

```python
from createagents import BaseTool

class CalculatorTool(BaseTool):
    name = "calculator"
    description = "Realiza cálculos matemáticos"
    parameters = {
        "type": "object",
        "properties": {
            "expression": {"type": "string", "description": "Expressão matemática"}
        },
        "required": ["expression"]
    }

    def execute(self, expression: str) -> str:
        return str(eval(expression))
```

______________________________________________________________________

## 🤔 FAQ

**P: Por que algumas ferramentas são opcionais?**
R: Para manter o sistema leve. Se você não precisa ler PDFs/Excel, não precisa instalar pandas, unstructured, etc.

**P: Como sei quais ferramentas estão disponíveis?**
R: Use `agent.get_all_available_tools()` para listar.

**P: O que acontece se eu tentar usar uma ferramenta não instalada?**
R: Você receberá erro claro: `pip install createagents[file-tools]`

**P: Posso criar minhas próprias ferramentas?**
R: Sim! Siga o padrão de ferramentas próprias e estenda `BaseTool`.

______________________________________________________________________

**Última atualização:** 02/12/2025
