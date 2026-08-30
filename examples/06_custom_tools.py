"""06. Custom Tools with BaseTool.

This example demonstrates how to extend `BaseTool` to define custom capabilities
for the AI agent, such as mathematical calculations or external API integrations.

Prerequisites:
    Set `OPENAI_API_KEY` in your `.env` file or environment.

Run:
    python examples/06_custom_tools.py
"""

import asyncio
import os
from typing import Any, ClassVar

from dotenv import load_dotenv
from rich import print as rprint

from createagents import BaseTool, CreateAgent

load_dotenv()


class CalculatorTool(BaseTool):
    """A tool that performs basic arithmetic calculations."""

    name: str = 'calculate'
    description: str = 'Performs basic arithmetic operations: add, subtract, multiply, or divide.'
    parameters: ClassVar[dict[str, Any]] = {
        'type': 'object',
        'properties': {
            'operation': {
                'type': 'string',
                'enum': ['add', 'subtract', 'multiply', 'divide'],
                'description': 'The mathematical operation to perform.',
            },
            'a': {'type': 'number', 'description': 'First number.'},
            'b': {'type': 'number', 'description': 'Second number.'},
        },
        'required': ['operation', 'a', 'b'],
    }

    def execute(self, operation: str, a: float, b: float) -> str:
        """Execute the mathematical calculation."""
        rprint(
            f'  [dim]🔧 [CalculatorTool] Invoked: {operation}({a}, {b})[/dim]'
        )
        if operation == 'add':
            return str(a + b)
        if operation == 'subtract':
            return str(a - b)
        if operation == 'multiply':
            return str(a * b)
        if operation == 'divide':
            if b == 0:
                return 'Error: Division by zero.'
            return str(a / b)
        return f'Unknown operation: {operation}'


class WeatherSimulatorTool(BaseTool):
    """A tool that retrieves simulated live weather for a city."""

    name: str = 'get_weather'
    description: str = (
        'Get current weather conditions and temperature for a given city.'
    )
    parameters: ClassVar[dict[str, Any]] = {
        'type': 'object',
        'properties': {
            'city': {
                'type': 'string',
                'description': 'City name (e.g., Tokyo, London, São Paulo).',
            },
        },
        'required': ['city'],
    }

    def execute(self, city: str) -> str:
        """Execute the simulated weather lookup."""
        rprint(
            f'  [dim]🔧 [WeatherSimulatorTool] Invoked: lookup weather for {city}[/dim]'
        )
        mock_conditions: dict[str, str] = {
            'tokyo': 'Sunny, 22°C, Wind: 5km/h',
            'london': 'Rainy, 14°C, Wind: 15km/h',
            'new york': 'Partly Cloudy, 18°C, Wind: 10km/h',
            'são paulo': 'Clear skies, 26°C, Wind: 8km/h',
        }
        return mock_conditions.get(
            city.lower().strip(), f'Mild weather, 20°C in {city}'
        )


async def main() -> None:
    """Run the custom tools example."""
    if not os.getenv('OPENAI_API_KEY'):
        rprint(
            '[bold yellow]Warning:[/bold yellow] OPENAI_API_KEY is not set.\n'
            'Please configure OPENAI_API_KEY in your .env file.'
        )
        return

    rprint('[bold cyan]Creating Agent with Custom Tools...[/bold cyan]')

    calculator = CalculatorTool()
    weather = WeatherSimulatorTool()

    # Pass tool instances to the agent
    agent = CreateAgent(
        provider='openai',
        model='gpt-4o-mini',
        name='ToolPoweredAgent',
        instructions=(
            'You are a smart assistant. Use the calculate tool for all math '
            'and get_weather for all weather inquiries.'
        ),
        tools=[calculator, weather],
    )

    rprint(
        f'[green]Active tools:[/green] {", ".join(agent.get_all_available_tools().keys())}\n'
    )

    # 1. Test calculation tool calling
    prompt_1 = (
        'What is 347 multiplied by 28? Please compute it using your tool.'
    )
    rprint(f'[bold blue]User:[/bold blue] {prompt_1}')
    resp_1 = await agent.chat(prompt_1)
    rprint(f'[bold green]Agent:[/bold green] {resp_1}\n')

    # 2. Test weather tool calling
    prompt_2 = 'How is the weather in Tokyo right now?'
    rprint(f'[bold blue]User:[/bold blue] {prompt_2}')
    resp_2 = await agent.chat(prompt_2)
    rprint(f'[bold green]Agent:[/bold green] {resp_2}\n')


if __name__ == '__main__':
    asyncio.run(main())
