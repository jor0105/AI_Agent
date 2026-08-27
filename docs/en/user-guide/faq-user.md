# User FAQ

## 1. Why are some tools optional?

To keep the core package lightweight and fast to install. Install the `[file-tools]` extra only if you need parsing for PDF, Excel, and other document formats.

## 2. How do I know which tools are available?

Use `agent.get_all_available_tools()` to list all system and custom tools available to the agent.

## 3. What happens if I attempt to use an uninstalled optional tool?

You will receive an informative error directing you to install the corresponding extra: `pip install createagents[file-tools]`.

## 4. Can I create my own tools?

Yes! Subclass `BaseTool` and implement the `execute` method following the project patterns.

## 5. How can I ensure data privacy?

Use local models with the Ollama provider running on `localhost` (or within your private network). When the Ollama server is hosted locally, no data is sent to external cloud APIs. Note that if you configure `OLLAMA_HOST` to point to a remote server, requests will be routed to that designated host.

## 6. How do I export metrics?

Use `agent.export_metrics_json()` or `agent.export_metrics_prometheus()`.

## 7. How do I clear conversation history?

Call `agent.clear_history()`.

## 8. How do I report bugs or ask for support?

Open an issue on [GitHub Issues](https://github.com/jordanestralioto/Create-Agents-AI/issues) or email `estraliotojordan@gmail.com`.

## 9. How do I update the framework?

Update via pip:

```bash
pip install --upgrade createagents
# OR with file-tools
pip install --upgrade createagents[file-tools]
```

## 10. Where can I find advanced examples?

Refer to the [Practical Examples](examples-user.md) and [Technical Examples](../dev-guide/technical-examples.md).

## 11. How do I use the interactive CLI?

Call the `start_cli()` method on your agent:

```python
from createagents import CreateAgent

agent = CreateAgent(provider='openai', model='gpt-4')
agent.start_cli()  # Starts interactive CLI session
```

ℹ️ [Full CLI Guide](cli-usage.md)

## 12. How does streaming work?

The behavior of `chat()` depends on the `stream` parameter in `config`:

- **With streaming (`config={"stream": True}`)**: The method returns a `StreamingResponseDTO`. You can:
  - **Iterate token by token**: `async for token in response:`
  - **Await full response**: `full_text = await response`
- **Without streaming (`stream=False`, default)**: The method returns a standard `str` containing the complete response.

Configuration example:

```python
from createagents import CreateAgent

# Enable streaming
agent_stream = CreateAgent(
    provider='openai', model='gpt-4', config={'stream': True}
)

# Disable streaming (default)
agent_sync = CreateAgent(
    provider='openai', model='gpt-4', config={'stream': False}
)
```

ℹ️ [Streaming Guide](streaming-guide.md)

## 13. Can I disable streaming explicitly?

Yes. Streaming is disabled by default (`stream: False`), but can also be specified explicitly in `config`:

```python
import asyncio
from createagents import CreateAgent


async def main():
    agent = CreateAgent(
        provider='openai',
        model='gpt-4',
        config={'stream': False},  # Explicitly disabled
    )

    # Returns str
    response = await agent.chat('Hello')
    print(response)


asyncio.run(main())
```

## 14. What commands are available in the CLI?

- `/help` - Help and command summary
- `/metrics` - Performance statistics table
- `/configs` - Current agent configuration
- `/tools` - List available tools
- `/clear` - Clear conversation history
- `exit` or `quit` - Exit application

## 15. How do I contribute to the project?

See the [Contribution Guide](../dev-guide/contribute.md).
