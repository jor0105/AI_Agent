# Technical Examples for Developers

Advanced usage, extension, and testing patterns for Create Agents AI.

## Creating a Custom Tool

```python
from createagents import BaseTool


class MyTool(BaseTool):
    name = 'my_tool'
    description = 'My custom tool'
    parameters = {
        'type': 'object',
        'properties': {
            'input': {
                'type': 'string',
                'description': 'Input string to process',
            }
        },
        'required': ['input'],
    }

    def execute(self, input: str) -> str:
        return f'Processed: {input}'
```

## Adding a Custom Provider Adapter

```python
from collections.abc import AsyncGenerator
from typing import Any
from createagents.application.interfaces import ChatRepository
from createagents.domain import BaseTool, ChatMetrics


class ClaudeAdapter(ChatRepository):
    def __init__(self) -> None:
        self.__metrics: list[ChatMetrics] = []

    async def chat(
        self,
        model: str,
        instructions: str | None,
        config: dict[str, Any] | None,
        tools: list[BaseTool] | None,
        history: list[dict[str, str]],
        user_ask: str,
    ) -> str | AsyncGenerator[str, None]:
        # Implementation for Anthropic Claude
        pass

    def get_metrics(self) -> list[ChatMetrics]:
        return self.__metrics.copy()
```

## Unit Testing

```python
import asyncio
from unittest import TestCase
from unittest.mock import AsyncMock, patch
import pytest
from createagents import CreateAgent


@pytest.mark.unit
class TestAgentChat(TestCase):
    @patch(
        'createagents.infra.factories.chat_adapter_factory.OpenAIChatAdapter'
    )
    def test_chat(self, mock_adapter_cls):
        # Configure mock to simulate API response
        mock_adapter_instance = mock_adapter_cls.return_value
        mock_adapter_instance.chat = AsyncMock(return_value='Hello, world!')
        mock_adapter_instance.get_metrics.return_value = []

        agent = CreateAgent(provider='openai', model='YOUR_MODEL')
        response = asyncio.run(agent.chat('Test'))
        self.assertEqual(response, 'Hello, world!')
```

## CI/CD Integration

Use `pytest` with coverage tracking:

```bash
uv run --locked --no-sync pytest -m 'not integration and not slow' -ra --cov=src --cov-fail-under=85
```

## Extending Metrics

```python
metrics = agent.get_metrics()
agent.export_metrics_json('metrics.json')
agent.export_metrics_prometheus('metrics.prom')
```

## Contributing

See [How to Contribute](contribute.md).
