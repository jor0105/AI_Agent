# Interactive CLI User Guide

The CreateAgents AI CLI (Command-Line Interface) provides a rich terminal experience to chat interactively with your AI agents.

______________________________________________________________________

## 🚀 Quick Start

```python
from createagents import CreateAgent

# Create agent
agent = CreateAgent(
    provider='openai',
    model='YOUR_MODEL',
    name='Assistant',
    instructions='You are a helpful assistant',
)

# Launch interactive CLI
agent.start_cli()
```

______________________________________________________________________

## ✨ Features

- **🎨 Formatted Interface**: ANSI rendering of Markdown elements (headers, bold, italics, lists, and tables)
- **⚡ Streaming Support**: Token-by-token output when `config={'stream': True}` is enabled
- **🎯 Built-in Commands**: 5 interactive commands (`/help`, `/metrics`, `/configs`, `/tools`, `/clear`) plus exit commands (`exit`/`quit`)
- **🔧 Status Indicators**: Displays `🤖 AI is thinking...` during tool execution and processing turns
- **📊 Session Metrics**: Instantly inspect accumulated call metrics table via `/metrics`

______________________________________________________________________

## 📋 Available Commands

### `/help` - Help

Displays the list of available commands and usage instructions.

```
You: /help
```

**Aliases**: `/help`, `help`

**Example Output**:

```text
Available Commands:

• /metrics  → Show agent performance metrics and statistics
• /configs  → Display current agent configuration settings
• /tools    → List all available tools and their descriptions
• /clear    → Clear conversation history and start fresh
• /help     → Show this help message

Type 'exit' or 'quit' to close the application.
```

### `/metrics` - Performance Metrics

Displays interaction performance statistics in a markdown table:

- Model used
- Duration / Latency in seconds
- Token counts (Prompt / Completion / Total)

```
You: /metrics
```

**Aliases**: `/metrics`, `get_metrics`

**Example Output (Illustrative)**:

```text
## Performance Metrics

| Model | Duration | Tokens (In/Out/Total) |
|-------|----------|-----------------------|
| YOUR_MODEL | 1.25s    | 45 / 105 / 150        |
| YOUR_MODEL | 0.98s    | 110 / 120 / 230       |
```

### `/configs` - Agent Configuration

Displays current configuration and history state:

- Name
- Provider and model
- Instructions
- Configuration dictionary
- Active configured tools on the instance
- Conversation history preview and count

```
You: /configs
```

**Aliases**: `/configs`, `get_configs`

**Example Output (Illustrative)**:

```text
## Agent Configuration

**provider:** openai
**model:** YOUR_MODEL
**name:** None
**instructions:** None
**config:** {}
**tools:** None
**history:** 2 messages in history

  - **user:** Hello!
  - **assistant:** Hello! How can I assist you today?

**history_max_size:** 10
```

> 💡 **Note**: `/configs` displays the tools **configured on the current agent instance** (`tools: None` by default in the quick start). If you instantiate the agent with `tools=['currentdate']`, they will be listed here. To inspect the full **catalog of tools available in the environment**, use `/tools`.

### `/tools` - Tools

Lists all tools available in the environment (system built-in and custom tools) alongside their descriptions.

```
You: /tools
```

**Aliases**: `/tools`, `get_tools`

**Example Output (Basic installation):**

```text
## Available Tools

**currentdate**
Get the current date and/or time in a specific timezone. Essential for answering 'What time is it?' or 'What day is it?' questions.
```

**Example Output (With `[file-tools]` extra installed):**

```text
## Available Tools

**currentdate**
Get the current date and/or time in a specific timezone. Essential for answering 'What time is it?' or 'What day is it?' questions.

**readlocalfile**
Use this tool to read local files from the system. Supports text files (txt, md, py, etc.), CSV, Excel, PDF and Parquet formats. The tool validates file size in tokens to prevent overload. Input must include the absolute or relative file path and optionally the maximum number of tokens allowed (default: 30000).
```

### `/clear` - Clear History

Clears the entire conversation history.

```
You: /clear
```

**Aliases**: `/clear`, `clear_history`

**Example Output**:

```text
Chat history cleared successfully!
```

### Regular Chat

Any input that is not a command is dispatched directly to the agent.

```
You: Explain Clean Architecture
```

If the agent is initialized with `config={'stream': True}`, the response is streamed token-by-token in real time. Without streaming enabled, the complete response is formatted and rendered once generation completes.

### `exit` / `quit` - Exit

Closes the CLI session gracefully.

```
You: exit
```

or

```
You: quit
```

______________________________________________________________________

## 🎨 Interface and Styling

### Colors and Visual Scheme

The CLI uses the following ANSI terminal palette:

- **User Messages**: Right-aligned box in Blue (`ColorScheme.BLUE`)
- **AI Responses & Thinking Indicator**: Left-aligned box and thinking status in Purple (`ColorScheme.PURPLE`)
- **System Messages, Menus & Commands**: Cyan (`ColorScheme.CYAN`)
- **Success Markers**: Green (`ColorScheme.GREEN`)
- **System Warnings / Interrupts**: Yellow (`ColorScheme.YELLOW`)
- **Errors**: Red (`ColorScheme.RED`)

### Markdown Terminal Formatting

The `MarkdownTerminalFormatter` formats Markdown text for ANSI terminals (does not perform syntax highlighting):

- **Headers**: `#` and `##` in bold blue with accent bar; `###` and `####` in bold purple; `#####` and `######` in bold cyan
- **Bold**: `**text**` or `__text__` rendered in ANSI bold
- **Italics**: `*text*` or `_text_` rendered in ANSI italic
- **Unordered Lists**: `•` bullet markers in green
- **Ordered Lists**: `→` arrow markers in blue
- **Markdown Tables**: Automatically rendered as label-value pairs or aligned columns with clean borders
- **Text Sanitization**: Strips incompatible Unicode characters to avoid terminal rendering glitches

### Status Indicators

During initial processing and tool execution turns:

```text
🤖 AI is thinking...
```

If streaming is active (`config={'stream': True}`), the indicator clears once the first token arrives and tokens stream onto the screen.

______________________________________________________________________

## 💡 Usage Examples

### Example 1: Coding Assistant

```python
from createagents import CreateAgent

code_assistant = CreateAgent(
    provider='openai',
    model='YOUR_MODEL',
    name='Code Expert',
    instructions='You are a Python expert. Always provide clear examples.',
    config={'stream': True},  # Enables real-time streaming in chat
)

# Start CLI
code_assistant.start_cli()
```

**Interaction**:

```
You: How do I create a decorator in Python?
[Streaming response...]

You: /metrics
[Displays accumulated performance metrics table]

You: /clear
[Clears history for a new topic]
```

### Example 2: Agent with Tools

```python
from createagents import CreateAgent

agent_with_tools = CreateAgent(
    provider='openai',
    model='YOUR_MODEL',
    tools=['currentdate'],  # 'readlocalfile' requires [file-tools]
)

# Start CLI
agent_with_tools.start_cli()
```

**Interaction**:

```
You: /tools
[Lists available tools]

You: What day is today?
[Agent automatically uses CurrentDateTool]
```

### Example 3: Local Ollama Agent

```python
from createagents import CreateAgent

local_agent = CreateAgent(
    provider='ollama', model='YOUR_OLLAMA_MODEL', name='Local Assistant'
)

# Start CLI
local_agent.start_cli()
```

______________________________________________________________________

## 🔧 Programmatic Customization

The CLI is launched via `start_cli()` on the `CreateAgent` facade:

```python
from createagents import CreateAgent

agent = CreateAgent(provider='openai', model='YOUR_MODEL')
agent.start_cli()  # Launches main interactive loop
```

Internally, this method:

1. Imports `ChatCLIApplication` lazily from the presentation layer
2. Instantiates the application with the agent facade
3. Executes the main interactive loop

______________________________________________________________________

## 🐛 Troubleshooting

### CLI Does Not Start

**Issue**: Error when calling `agent.start_cli()`

**Solution**: Ensure you have the latest package installed:

```bash
pip install --upgrade createagents
```

### Unicode / Emojis Do Not Render

**Issue**: Box borders or emojis appear scrambled

**Solution**: Use a terminal emulator with full UTF-8 support (Windows Terminal, iTerm2, Alacritty, GNOME Terminal, etc.)

### Streaming Too Slow

**Issue**: Tokens stream very slowly

**Solution**:

1. Check your network latency (for OpenAI)
2. For Ollama, verify that the model fits into available memory/GPU
3. Consider using a smaller or faster model

______________________________________________________________________

## 📚 Next Steps

- [Streaming Guide](streaming-guide.md)
- [CLI Architecture (Developers)](../dev-guide/cli-architecture.md)
- [CLI Commands Reference](../reference/commands.md)

______________________________________________________________________

**Version:** 0.3.0 | **Updated:** 2026-08-27
