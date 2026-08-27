# Exemplos Técnicos para Desenvolvedores

Veja exemplos avançados de uso, extensão e integração do Create Agents AI.

## Criar Ferramenta Customizada

```python
from createagents import BaseTool


class MyTool(BaseTool):
    name = 'my_tool'
    description = 'Minha ferramenta personalizada'
    parameters = {
        'type': 'object',
        'properties': {
            'input': {'type': 'string', 'description': 'Texto de entrada'}
        },
        'required': ['input'],
    }

    def execute(self, input: str) -> str:
        return f'Resultado: {input}'
```

## Novo Adapter de Provedor

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
        # Implementação para Claude
        pass

    def get_metrics(self) -> list[ChatMetrics]:
        return self.__metrics.copy()
```

## Testes Unitários

```python
import asyncio
import pytest
from unittest import TestCase
from unittest.mock import AsyncMock, patch
from createagents import CreateAgent


@pytest.mark.unit
class TestAgentChat(TestCase):
    @patch(
        'createagents.infra.factories.chat_adapter_factory.OpenAIChatAdapter'
    )
    def test_chat(self, mock_adapter_cls):
        # Configura o mock para simular resposta da API
        mock_adapter_instance = mock_adapter_cls.return_value
        mock_adapter_instance.chat = AsyncMock(return_value='Olá, mundo!')
        mock_adapter_instance.get_metrics.return_value = []

        agent = CreateAgent(provider='openai', model='YOUR_MODEL')
        response = asyncio.run(agent.chat('Teste'))
        self.assertEqual(response, 'Olá, mundo!')
```

## Integração com CI/CD

- Use `pytest` e `pytest-cov` para cobertura.

## Extensão de Métricas

```python
metrics = agent.get_metrics()
agent.export_metrics_json('metrics.json')
```

## Contribuindo

Veja [Como Contribuir](contribute.md).
