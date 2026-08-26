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
        provider='openai', model='gpt-4', tools=['currentdate']
    )

    resposta = await agent.chat('Que dia é hoje?')
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

**Formatos suportados:**

- **Texto e código:** TXT, LOG, MD, PY, JS, HTML, CSS, JSON, XML, YAML, YML, RST, INI, CFG, CONF, SH, BASH, ZSH
- **Tabelas e dados:** CSV, Excel (XLSX, XLSM, e legado XLS\*), Parquet
- **Documentos (via unstructured):** PDF, Word (DOC, DOCX), PowerPoint (PPT, PPTX), OpenDocument (ODT), EPUB, MSG, RTF

\* *Nota sobre Excel*: Arquivos OpenXML (`.xlsx`, `.xlsm`) usam o motor `openpyxl` incluído no extra `[file-tools]`. O formato legado Excel 97-2004 (`.xls`) requer a biblioteca opcional `xlrd` (`pip install xlrd`).

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
        provider='openai', model='gpt-4', tools=['readlocalfile']
    )

    resposta = await agent.chat('Leia o arquivo report.pdf e resuma')
    print(resposta)


async def main_run():
    await main()


asyncio.run(main_run())
```

**Limites e Segurança:**

- Tamanho máximo de arquivo: 100 MiB (limite fixo de segurança: 104.857.600 bytes)
- Limite padrão de tokens: 30.000 tokens (parâmetro `max_tokens`)
- Diretório seguro (sandbox): controlado pela variável de ambiente `FILE_TOOL_BASE_DIR` (padrão: diretório atual `.`). Caminhos fora do diretório base são bloqueados contra path traversal.

**Funcionalidades:**

- ✅ Validação de tamanho e limite de tokens
- ✅ Sandbox de diretório seguro contra path traversal
- ✅ Detecção automática de encoding
- ✅ Suporte a múltiplos formatos
- ✅ Tratamento robusto de erros

______________________________________________________________________

## 🚀 Uso com Agentes

### Exemplo 1: Ferramenta de Data

```python
import asyncio
from createagents import CreateAgent


async def main():
    agent = CreateAgent(
        provider='openai',
        model='gpt-4',
        instructions='Você pode verificar data/hora quando necessário',
        tools=['currentdate'],
    )

    # O agente usa a ferramenta automaticamente
    resposta = await agent.chat('Que dia da semana é hoje?')
    print(resposta)


asyncio.run(main())
```

### Exemplo 2: Leitura de Arquivos

```python
import asyncio
from createagents import CreateAgent


async def main():
    # Certifique-se que instalou: pip install createagents[file-tools]
    agent = CreateAgent(
        provider='openai',
        model='gpt-4',
        instructions='Você pode ler arquivos locais',
        tools=['readlocalfile'],
    )

    resposta = await agent.chat('Resuma o documento relatorio.pdf')
    print(resposta)


asyncio.run(main())
```

### Exemplo 3: Múltiplas Ferramentas

```python
import asyncio
from createagents import CreateAgent


async def main():
    agent = CreateAgent(
        provider='openai',
        model='gpt-4',
        tools=['currentdate', 'readlocalfile'],
    )

    # O agente escolhe qual ferramenta usar
    resposta1 = await agent.chat('Que dia é hoje?')  # Usa currentdate
    print(resposta1)

    resposta2 = await agent.chat('Leia notas.txt')  # Usa readlocalfile
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
    name = 'custom_tool'
    description = 'Minha ferramenta customizada'
    parameters = {
        'type': 'object',
        'properties': {
            'input': {
                'type': 'string',
                'description': 'Texto de entrada para a ferramenta',
            }
        },
        'required': ['input'],
    }

    def execute(self, input: str) -> str:
        return f'Resultado para: {input}'


agent = CreateAgent(
    provider='openai',
    model='gpt-4',
    tools=['currentdate', CustomTool()],  # Ferramenta do sistema + customizada
)

# Obter todas as ferramentas deste agente
tools = agent.get_all_available_tools()

print('Ferramentas disponíveis neste agente:')
for name, description in tools.items():
    print(f'  - {name}: {description[:50]}...')

# Exemplo de saída (instalação básica):
# - currentdate: Get the current date and/or time...
# - custom_tool: Minha ferramenta customizada
#
# (Com o extra [file-tools] instalado, 'readlocalfile' também é listado)
```

### Verificar Apenas Ferramentas do Sistema

Use `get_system_available_tools()` para ver apenas as ferramentas built-in disponíveis globalmente (não inclui ferramentas customizadas):

```python
from createagents import CreateAgent

agent = CreateAgent(provider='openai', model='gpt-4')

# Obter apenas ferramentas do sistema
system_tools = agent.get_system_available_tools()

print('Ferramentas do sistema disponíveis:')
for name, description in system_tools.items():
    print(f'  - {name}: {description[:50]}...')

# Verificar se uma ferramenta específica está disponível
if 'readlocalfile' in system_tools:
    print('✅ ReadLocalFileTool disponível!')
else:
    print('⚠️ Instale com: pip install createagents[file-tools]')
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
    name = 'weather'
    description = 'Consulta previsão do tempo'
    parameters = {
        'type': 'object',
        'properties': {
            'city': {
                'type': 'string',
                'description': 'Nome da cidade para consulta',
            }
        },
        'required': ['city'],
    }

    def execute(self, city: str) -> str:
        return f'Previsão para {city}: Ensolarado'


# Agente sem ferramentas customizadas
agent1 = CreateAgent(provider='openai', model='gpt-4')
print('Agente 1:', list(agent1.get_all_available_tools().keys()))
# Saída básica: ['currentdate']
# Saída com extra [file-tools]: ['currentdate', 'readlocalfile']

# Agente com ferramentas customizadas
agent2 = CreateAgent(
    provider='openai', model='gpt-4', tools=['currentdate', WeatherTool()]
)
print('Agente 2:', list(agent2.get_all_available_tools().keys()))
# Saída básica: ['currentdate', 'weather']
# Saída com extra [file-tools]: ['currentdate', 'readlocalfile', 'weather']

# Ferramentas do sistema (global para o ambiente)
print('Sistema:', list(agent1.get_system_available_tools().keys()))
# Saída básica: ['currentdate']
# Saída com extra [file-tools]: ['currentdate', 'readlocalfile']
```

### Evitando Duplicatas

O sistema automaticamente evita duplicatas de ferramentas. Se você adicionar uma ferramenta do sistema à lista de tools do agente, ela aparecerá apenas uma vez:

```python
from createagents import CreateAgent

# Ferramenta do sistema adicionada explicitamente
agent = CreateAgent(
    provider='openai',
    model='gpt-4',
    tools=['currentdate'],  # Adiciona explicitamente uma ferramenta do sistema
)

# Não haverá duplicatas
tools = agent.get_all_available_tools()
# 'currentdate' aparece apenas UMA vez
print(list(tools.keys()))
# Saída básica: ['currentdate']
# Saída com extra [file-tools]: ['currentdate', 'readlocalfile']
```

______________________________________________________________________

## ⚡ Impacto de Dependências

- **Instalação básica (`pip install createagents`):** Apenas dependências essenciais do framework (`openai`, `ollama`, `python-dotenv`, `defusedxml`, `rich`).
- **Instalação com ferramentas de arquivo (`pip install createagents[file-tools]`):** Inclui bibliotecas adicionais (`tiktoken`, `unstructured`, `pandas`, `openpyxl`, `pyarrow`, `chardet`), importadas sob demanda apenas quando ferramentas de arquivo são utilizadas.

______________________________________________________________________

## 🎨 Criar Suas Próprias Ferramentas

### Ferramenta Própria

```python
import ast
import operator
from createagents import BaseTool

_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.USub: operator.neg,
}


def _safe_eval(node: ast.AST) -> float:
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return float(node.value)
    if isinstance(node, ast.BinOp) and type(node.op) in _OPERATORS:
        return _OPERATORS[type(node.op)](
            _safe_eval(node.left), _safe_eval(node.right)
        )
    if isinstance(node, ast.UnaryOp) and type(node.op) in _OPERATORS:
        return _OPERATORS[type(node.op)](_safe_eval(node.operand))
    raise ValueError('Operação não suportada')


class CalculatorTool(BaseTool):
    name = 'calculator'
    description = 'Realiza cálculos matemáticos básicos (+, -, *, /)'
    parameters = {
        'type': 'object',
        'properties': {
            'expression': {
                'type': 'string',
                'description': 'Expressão matemática segura (ex.: "2 + 2 * 3")',
            }
        },
        'required': ['expression'],
    }

    def execute(self, expression: str) -> str:
        parsed = ast.parse(expression.strip(), mode='eval')
        return str(_safe_eval(parsed.body))
```

______________________________________________________________________

## 🤔 FAQ

**P: Por que algumas ferramentas são opcionais?**
R: Para manter o sistema leve. Se você não precisa ler PDFs/Excel, não precisa instalar pandas, unstructured, etc.

**P: Como sei quais ferramentas estão disponíveis?**
R: Use `agent.get_all_available_tools()` para listar o catálogo disponível. Para ver as ferramentas configuradas no agente, use `agent.get_configs()['tools']`.

**P: O que acontece se eu tentar usar uma ferramenta não instalada?**
R: Você receberá erro claro: `pip install createagents[file-tools]`

**P: Posso criar minhas próprias ferramentas?**
R: Sim! Siga o padrão de ferramentas próprias e estenda `BaseTool`.

______________________________________________________________________

**Versão:** 0.2.0 | **Atualização:** 2026-08-25
