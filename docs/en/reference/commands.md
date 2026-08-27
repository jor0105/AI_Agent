# CLI Commands Reference

Complete reference for all commands supported in the CreateAgents AI interactive terminal interface.

______________________________________________________________________

## 📋 Overview

The interactive CLI provides **7 built-in commands** for controlling agent state, inspecting performance, and configuring sessions:

| Command     | Aliases                   | Description                                    |
| ----------- | ------------------------- | ---------------------------------------------- |
| `/help`     | `/help`, `help`           | Displays available commands and help           |
| `/metrics`  | `/metrics`, `get_metrics` | Shows performance metrics table                |
| `/configs`  | `/configs`, `get_configs` | Displays current agent settings                |
| `/tools`    | `/tools`, `get_tools`     | Lists available tools catalog                  |
| `/clear`    | `/clear`, `clear_history` | Clears conversation history                    |
| **Chat**    | *(any text)*              | Dispatches message to agent (default fallback) |
| `exit/quit` | `exit`, `quit`            | Terminates the CLI session                     |

______________________________________________________________________

## 🔧 Detailed Commands

### `/help` - Help

**Description**: Displays list of available commands and usage instructions.

**Aliases**: `/help`, `help`

**Usage**:

```
You: /help
```

**Output**:

```text
Available Commands:

• /metrics  → Show agent performance metrics and statistics
• /configs  → Display current agent configuration settings
• /tools    → List all available tools and their descriptions
• /clear    → Clear conversation history and start fresh
• /help     → Show this help message

Type 'exit' or 'quit' to close the application.
```

______________________________________________________________________

### `/metrics` - Performance Metrics

**Description**: Shows detailed statistics of all calls accumulated up to the query time formatted as a Markdown table.

**Aliases**: `/metrics`, `get_metrics`

**Usage**:

```
You: /metrics
```

**Output (Illustrative)**:

```markdown
## Performance Metrics

| Model | Duration | Tokens (In/Out/Total) |
|---|---|---|
| YOUR_MODEL | 1.23s | 100 / 150 / 250 |
| YOUR_MODEL | 0.98s | 80 / 100 / 180 |
```

**Displayed Fields**:

- Model identifier
- Call duration/latency (in seconds)
- Token breakdown: Prompt (In) / Completion (Out) / Total

______________________________________________________________________

### `/configs` - Agent Configuration

**Description**: Displays all current configuration parameters of the agent formatted in Markdown.

**Aliases**: `/configs`, `get_configs`

**Usage**:

```
You: /configs
```

**Output (Illustrative)**:

```markdown
## Agent Configuration

**provider:** openai
**model:** YOUR_MODEL
**name:** Code Assistant
**instructions:** You are a Python expert.
**config:** {'temperature': 0.7, 'max_tokens': 2000}
**tools:** None
**history:** 2 messages in history
  - **user**: Hello
  - **assistant**: Hello! How can I help you today?
**history_max_size:** 10
```

> **Note:** If tools were passed during agent instantiation (`tools=['currentdate']`), the `tools` key lists their names. Optional file tools (such as `readlocalfile`) require the `[file-tools]` extra.

**Displayed Fields**:

- Agent name
- Provider and model
- System instructions
- Hyperparameters (`temperature`, `max_tokens`, etc.)
- Active configured tools on this agent instance (`tools`)
- Conversation history preview and count
- Maximum history size

______________________________________________________________________

### `/tools` - Available Tools Catalog

**Description**: Executes `agent.get_all_available_tools()` and lists the complete catalog of tools available to this agent in the environment (system built-in tools plus custom tools attached to this instance). Note that `ReadLocalFileTool` requires the `[file-tools]` extra. To inspect the active tools enabled on the current instance, use `/configs`.

**Aliases**: `/tools`, `get_tools`

**Usage**:

```
You: /tools
```

**Output (Basic installation):**

```markdown
## Available Tools

**currentdate**
Get the current date and/or time in a specific timezone. Essential for answering 'What time is it?' or 'What day is it?' questions.
```

**Output (With `[file-tools]` extra installed):**

```markdown
## Available Tools

**currentdate**
Get the current date and/or time in a specific timezone. Essential for answering 'What time is it?' or 'What day is it?' questions.

**readlocalfile**
Use this tool to read local files from the system. Supports text files (txt, md, py, etc.), CSV, Excel, PDF and Parquet formats. The tool validates file size in tokens to prevent overload. Input must include the absolute or relative file path and optionally the maximum number of tokens allowed (default: 30000).
```

**Displayed Fields**:

- Tool name in bold
- Full description registered in the tools catalog

______________________________________________________________________

### `/clear` - Clear History

**Description**: Wipes the entire conversation history buffer, starting a fresh contextual session.

**Aliases**: `/clear`, `clear_history`

**Usage**:

```

You: /clear

```

**Output**:

```text
Chat history cleared successfully!
```

**Effects**:

- Clears message history buffer
- Preserves agent configuration and tools
- Next message starts from a clean context

**When to Use**:

- Changing topics completely
- Resetting conversation after an erroneous turn
- Freeing memory in long sessions

______________________________________________________________________

### Chat (Default Command)

**Description**: Dispatches input to the agent. Any text that is not a special command is routed as a user message.

**Usage**:

```
You: Explain Clean Architecture
```

**Output**:

```text
Clean Architecture is a software architectural pattern that separates...
```

*(When initialized with `config={'stream': True}`, responses stream progressively in real time; otherwise, the full message renders upon completion).*

**Behavior**:

- Routes message through `CreateAgent.chat()` (with streaming if configured)
- Executes tool calls automatically if requested by the LLM
- Retains conversational context in history
- Appends interaction turn to conversation history

______________________________________________________________________

### `exit` / `quit` - Exit

**Description**: Terminates the CLI session.

**Aliases**: `exit`, `quit`

**Usage**:

```
You: exit
```

or

```
You: quit
```

**Output**:

```text
👋 Goodbye! Thanks for using AI Chat System.
```

**Effects**:

- Terminates the CLI loop
- Exits the application gracefully
- History buffer is discarded (in-memory temporary session)

______________________________________________________________________

### Colors

The CLI uses the following ANSI terminal palette:

- **User Messages**: Right-aligned box in Blue (`ColorScheme.BLUE`)
- **AI Responses & Thinking Indicator**: Left-aligned box and thinking status in Purple (`ColorScheme.PURPLE`)
- **System Messages, Menus & Commands**: Cyan (`ColorScheme.CYAN`)
- **Success Markers**: Green (`ColorScheme.GREEN`)
- **System Warnings / Interrupts**: Yellow (`ColorScheme.YELLOW`)
- **Errors**: Red (`ColorScheme.RED`)

### Status Indicators

During processing and tool execution turns:

```text
🤖 AI is thinking...
```

______________________________________________________________________

## 🔄 Command Flow

```
User Input
  ↓
CommandRegistry.find_handler()
  ↓
Is special command? → Yes → Specific handler (/help, /metrics, etc.)
  ↓
No
  ↓
ChatCommandHandler (default fallback)
  ↓
Streaming Response (or complete formatted response)
```

______________________________________________________________________

## 💡 Usage Scenarios

### Typical Session Flow

```text
# Launch CLI
You: /help
[View commands index]

You: /tools
[Verify registered tools]

You: What day is today?
[Agent uses CurrentDateTool and responds]

You: /metrics
[Inspect latency and token metrics]

You: /configs
[Review agent parameters]

You: /clear
[Reset context for new topic]

You: Let's talk about Python typing
[New conversation starts]

You: exit
[Exits CLI]
```

### Debugging Session

```text
You: [message to agent]
[Response seems unexpected]

You: /configs
[Verify active prompt and parameters]

You: /tools
[Ensure correct tool is available]

You: /metrics
[Inspect latency and token consumption]

You: /clear
[Reset context and retry]
```

______________________________________________________________________

## 🐛 Troubleshooting

### Command Not Recognized

**Problem**: Misspelled command\
**Solution**: Run `/help` to see exact command names and aliases.

### Empty Metrics

**Problem**: `/metrics` shows no entries\
**Solution**: Ensure you have executed at least one chat turn before requesting metrics.

### Clear Not Working

**Problem**: History is not wiped\
**Solution**: Verify command spelling (`/clear`, not `/clean`).

______________________________________________________________________

## 📚 See Also

- [CLI User Guide](../user-guide/cli-usage.md)
- [CLI Architecture](../dev-guide/cli-architecture.md)
- [API Reference](api.md)

______________________________________________________________________

**Version:** 0.2.0 | **Updated:** 2026-08-27
