# Interactive CLI User Guide

The CreateAgents AI CLI (Command-Line Interface) provides a rich terminal experience to chat interactively with your AI agents.

______________________________________________________________________

## 🚀 Quick Start

```python
from createagents import CreateAgent

# Create agent
agent = CreateAgent(
    provider='openai',
    model='gpt-4',
    name='Assistant',
    instructions='You are a helpful assistant',
)

# Launch interactive CLI
agent.start_cli()
```

______________________________________________________________________

## ✨ Features

- **🎨 Colored Interface**: Syntax highlighting and Markdown formatting
- **⚡ Real-Time Streaming**: Tokens appear in real time as they are generated
- **🎯 Built-in Commands**: 5 useful commands (`/help`, `/metrics`, `/configs`, `/tools`, `/clear`) plus exit commands
- **🔧 Status Indicators**: Visual feedback when the agent is thinking
- **📊 Real-Time Metrics**: Instantly inspect execution performance

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

**Example Output**:

```text
## Performance Metrics

| Model | Duration | Tokens (In/Out/Total) |
|-------|----------|-----------------------|
| gpt-4 | 1.25s    | 45 / 105 / 150        |
| gpt-4 | 0.98s    | 110 / 120 / 230       |
```

### `/configs` - Agent Configuration

Displays current configuration and history state:

- Name
- Provider and model
- Instructions
- Configuration dictionary
- Available tools
- Conversation history preview and count

```
You: /configs
```

**Aliases**: `/configs`, `get_configs`

**Example Output**:

```text
## Agent Configuration

**provider:** openai
**model:** gpt-4
**name:** Assistant
**instructions:** You are a helpful assistant
**config:** {'temperature': 0.7}
**tools:** ['currentdate']
**history:** 2 messages in history

  - **user:** Hello!
  - **assistant:** Hello! How can I assist you today?

**history_max_size:** 10
```

### `/tools` - Tools

Lists all available tools (system and custom) alongside their descriptions.

```
You: /tools
```

**Aliases**: `/tools`, `get_tools`

**Example Output**:

```text
## Available Tools

**currentdate**
Get the current date and/or time in a specific timezone. Essential for answering 'What time is it?' or 'What day is it?' questions.

**readlocalfile**
Use this tool to read local files from the system. Supports text files (txt, md, py, etc.), CSV, Excel, PDF and Parquet formats.
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

The agent will stream its answer in real time.

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

### Colors

The CLI uses a clean terminal palette:

- **User Prompts**: Primary Cyan
- **Agent Responses**: Green
- **System Messages**: Yellow
- **Errors**: Red
- **Commands**: Magenta

### Markdown Formatting

The renderer supports:

- **Bold**: `**text**`
- *Italics*: `*text*`
- `Inline code`: `` `code` ``
- Code blocks with syntax highlighting
- Lists, headers, and markdown tables

### Status Indicators

During processing:

```
⏳ Processing...
```

During streaming:

```
✨ [Agent is typing...]
```

______________________________________________________________________

## 💡 Usage Examples

### Example 1: Coding Assistant

```python
from createagents import CreateAgent

code_assistant = CreateAgent(
    provider='openai',
    model='gpt-4',
    name='Code Expert',
    instructions='You are a Python expert. Always provide clear examples.',
)

# Start CLI
code_assistant.start_cli()
```

**Interaction**:

```
You: How do I create a decorator in Python?
[Streaming response...]

You: /metrics
[Displays call statistics]

You: /clear
[Clears history for a new topic]
```

### Example 2: Agent with Tools

```python
from createagents import CreateAgent

agent_with_tools = CreateAgent(
    provider='openai',
    model='gpt-4',
    tools=['currentdate'],  # For 'readlocalfile', install: pip install createagents[file-tools]
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
    provider='ollama', model='llama3.2', name='Local Assistant'
)

# Start CLI
local_agent.start_cli()
```

______________________________________________________________________

## 🔧 Programmatic Customization

The CLI is launched via `start_cli()` on the `CreateAgent` facade:

```python
from createagents import CreateAgent

agent = CreateAgent(provider='openai', model='gpt-4')
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
3. Consider using a smaller model (e.g. `llama3.2:1b` or `gpt-4o-mini`)

______________________________________________________________________

## 📚 Next Steps

- [Streaming Guide](streaming-guide.md)
- [CLI Architecture (Developers)](../dev-guide/cli-architecture.md)
- [CLI Commands Reference](../reference/commands.md)

______________________________________________________________________

**Version:** 0.2.0 | **Updated:** 2026-08-25
