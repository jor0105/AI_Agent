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
| `/tools`    | `/tools`, `get_tools`     | Lists active tools with descriptions           |
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

```markdown
## Available Commands

- **/help** - Display available commands and system information
- **/metrics** - View performance and usage metrics
- **/configs** - Display current agent configurations
- **/tools** - View available agent tools
- **/clear** - Clear current conversation history
- **exit/quit** - Exit the interactive chat CLI
```

______________________________________________________________________

### `/metrics` - Performance Metrics

**Description**: Shows detailed statistics of all calls executed during the current session formatted as a Markdown table.

**Aliases**: `/metrics`, `get_metrics`

**Usage**:

```
You: /metrics
```

**Output**:

```markdown
## Performance Metrics

| Model | Duration | Tokens (In/Out/Total) |
|---|---|---|
| gpt-4 | 1.23s | 100 / 150 / 250 |
| gpt-4 | 0.98s | 80 / 100 / 180 |
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

**Output**:

```markdown
## Agent Configuration

**provider:** openai
**model:** gpt-4
**name:** Code Assistant
**instructions:** You are a Python expert.
**config:** {'temperature': 0.7, 'max_tokens': 2000}
**tools:** ['currentdate', 'readlocalfile']
**history:** 2 messages in history
  - **user**: Hello
  - **assistant**: Hello! How can I help you today?
**history_max_size:** 10
```

**Displayed Fields**:

- Agent name
- Provider and model
- System instructions
- Hyperparameters (`temperature`, `max_tokens`, etc.)
- Registered tools
- Conversation history preview and count
- Maximum history size

______________________________________________________________________

### `/tools` - Available Tools

**Description**: Lists all tools (built-in and custom) that the agent is capable of invoking.

**Aliases**: `/tools`, `get_tools`

**Usage**:

```
You: /tools
```

**Output**:

```markdown
## Available Tools

**currentdate**
Get the current date and/or time in a specific timezone. Essential for answering 'What time is it?' or 'What day is it?' questions.

**readlocalfile**
Use this tool to read local files from the system. Supports text files (txt, md, py, etc.), CSV, Excel, PDF and Parquet formats.
```

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

```
✨ [Streaming response generated in real time...]
```

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
👋 Goodbye! Thank you for using CreateAgents AI.
```

______________________________________________________________________

## 🎨 Styling and Colors

- **Prompts**: Cyan
- **Agent Responses**: Green
- **System**: Yellow
- **Errors**: Red
- **Commands**: Magenta

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
Streaming Response
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

**Version:** 0.2.0 | **Updated:** 2026-08-25
