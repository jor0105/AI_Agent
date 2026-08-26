# 🛠️ Tools Reference

This guide explains the tools available for your AI agents and how to use, configure, and extend them.

______________________________________________________________________

## 📦 Overview

Tools are **additional capabilities** that your agents can use to perform specific tasks. To keep the framework lightweight, tools with heavy dependencies are packaged as **optional extras**.

______________________________________________________________________

## 🎯 Available Tools

### ✅ CurrentDateTool (Always Available)

Fetches the current date and time in any timezone.

**Dependencies:** None (Python standard library only)

**Usage:**

```python
import asyncio
from createagents import CreateAgent


async def main():
    agent = CreateAgent(
        provider='openai', model='gpt-4', tools=['currentdate']
    )

    response = await agent.chat('What day is today?')
    print(response)


asyncio.run(main())
```

**Supported Actions:**

- `date` - Date (`YYYY-MM-DD`)
- `time` - Time (`HH:MM:SS`)
- `datetime` - Full date and time
- `timestamp` - Unix timestamp
- `date_with_weekday` - Date including day of the week

______________________________________________________________________

### 🔧 ReadLocalFileTool (Optional Extra)

Reads local files across multiple structured and unstructured formats.

**Formats:** TXT, MD, CSV, Excel (`.xls`, `.xlsx`), PDF, Parquet, JSON, YAML

**Dependencies:** `tiktoken`, `unstructured`, `pandas`, `openpyxl`, `pyarrow`, `chardet`

**Installation:**

```bash
pip install createagents[file-tools]
```

**Usage:**

```python
import asyncio
from createagents import CreateAgent


async def main():
    agent = CreateAgent(
        provider='openai', model='gpt-4', tools=['readlocalfile']
    )

    response = await agent.chat('Read report.pdf and summarize it')
    print(response)


asyncio.run(main())
```

**Limits and Security:**

- Maximum file size: 100MB (configurable)
- Default token limit: 30,000 tokens (parameter `max_tokens`)
- Secure sandbox directory: controlled by the `FILE_TOOL_BASE_DIR` environment variable (default: current directory `.`)

**Features:**

- ✅ Size and token limit validation
- ✅ Secure directory sandbox against path traversal
- ✅ Automatic file encoding detection
- ✅ Multi-format support
- ✅ Robust error handling

______________________________________________________________________

## 🚀 Usage with Agents

### Example 1: Date Tool

```python
import asyncio
from createagents import CreateAgent


async def main():
    agent = CreateAgent(
        provider='openai',
        model='gpt-4',
        instructions='You can verify current date and time when necessary',
        tools=['currentdate'],
    )

    # The agent automatically invokes the tool
    response = await agent.chat('What day of the week is today?')
    print(response)


asyncio.run(main())
```

### Example 2: File Reading

```python
import asyncio
from createagents import CreateAgent


async def main():
    # Make sure you installed: pip install createagents[file-tools]
    agent = CreateAgent(
        provider='openai',
        model='gpt-4',
        instructions='You can read local files',
        tools=['readlocalfile'],
    )

    response = await agent.chat('Summarize the document report.pdf')
    print(response)


asyncio.run(main())
```

### Example 3: Multiple Tools

```python
import asyncio
from createagents import CreateAgent


async def main():
    agent = CreateAgent(
        provider='openai',
        model='gpt-4',
        tools=['currentdate', 'readlocalfile'],
    )

    # The agent selects the appropriate tool automatically
    response1 = await agent.chat('What day is today?')  # Uses currentdate
    print(response1)

    response2 = await agent.chat('Read notes.txt')  # Uses readlocalfile
    print(response2)


asyncio.run(main())
```

______________________________________________________________________

## 📋 Installation Checklist

### Basic Installation ✅

```bash
pip install createagents
```

Includes:

- [x] CurrentDateTool
- [x] Contextual history management
- [x] Performance metrics
- [x] OpenAI and Ollama adapters

### Installation with File Tools 📁

```bash
pip install createagents[file-tools]
```

Includes:

- [x] Everything in basic installation
- [x] ReadLocalFileTool
- [x] Support for PDF, Excel, CSV, Parquet

______________________________________________________________________

## 🔍 Inspecting Available Tools

### Inspecting Agent Tools

Use `get_all_available_tools()` to see all tools available for a specific agent instance (system built-in tools + custom tools):

```python
from createagents import BaseTool, CreateAgent


class CustomTool(BaseTool):
    name = 'custom_tool'
    description = 'My custom tool'
    parameters = {
        'type': 'object',
        'properties': {
            'input': {
                'type': 'string',
                'description': 'Input text for the tool',
            }
        },
        'required': ['input'],
    }

    def execute(self, input: str) -> str:
        return f'Result for: {input}'


agent = CreateAgent(
    provider='openai',
    model='gpt-4',
    tools=['currentdate', CustomTool()],  # System + custom tool
)

# Retrieve all tools for this agent
tools = agent.get_all_available_tools()

print('Tools available for this agent:')
for name, description in tools.items():
    print(f'  - {name}: {description[:50]}...')
```

### Inspecting System-Only Tools

Use `get_system_available_tools()` to check built-in framework tools:

```python
from createagents import CreateAgent

agent = CreateAgent(provider='openai', model='gpt-4')

system_tools = agent.get_system_available_tools()

print('System tools available:')
for name, description in system_tools.items():
    print(f'  - {name}: {description[:50]}...')

# Check if optional tool is available
if 'readlocalfile' in system_tools:
    print('✅ ReadLocalFileTool is available!')
else:
    print('⚠️ Install with: pip install createagents[file-tools]')
```

### Method Comparison

| Method                         | Returns                           | When to Use                                          |
| ------------------------------ | --------------------------------- | ---------------------------------------------------- |
| `get_all_available_tools()`    | System tools + agent custom tools | To inspect all tools this agent can execute          |
| `get_system_available_tools()` | System built-in tools only        | To check which optional built-in tools are installed |

### Deduplication

The system automatically deduplicates tools. If a system tool is explicitly provided in the `tools` list, it appears only once:

```python
agent = CreateAgent(
    provider='openai',
    model='gpt-4',
    tools=['currentdate'],  # Explicitly added system tool
)

tools = agent.get_all_available_tools()
# 'currentdate' appears only ONCE
print(list(tools.keys()))  # ['currentdate', 'readlocalfile']
```

______________________________________________________________________

## ⚡ Performance

### Memory Usage

| Installation        | Base Memory | With ReadLocalFileTool |
| ------------------- | ----------- | ---------------------- |
| Basic               | ~50MB       | N/A                    |
| With `[file-tools]` | ~50MB       | ~200MB (when active)   |

______________________________________________________________________

## 🎨 Building Custom Tools

```python
import ast
from createagents import BaseTool


class CalculatorTool(BaseTool):
    name = 'calculator'
    description = 'Performs mathematical calculations'
    parameters = {
        'type': 'object',
        'properties': {
            'expression': {
                'type': 'string',
                'description': 'Mathematical expression',
            }
        },
        'required': ['expression'],
    }

    def execute(self, expression: str) -> str:
        return str(ast.literal_eval(expression))
```

______________________________________________________________________

## 🤔 FAQ

**Q: Why are some tools optional?**\
A: To keep the base library lightweight. If your agent does not need document parsing, you don't need heavy dependencies like pandas or unstructured.

**Q: How do I know which tools are available?**\
A: Use `agent.get_all_available_tools()` to list available tools.

**Q: What happens if I invoke an uninstalled tool?**\
A: You will receive an informative error directing you to install the corresponding extra: `pip install createagents[file-tools]`.

**Q: Can I create my own custom tools?**\
A: Yes! Simply subclass `BaseTool` and implement the `execute` method.

______________________________________________________________________

**Version:** 0.2.0 | **Updated:** 2026-08-25
