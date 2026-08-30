"""05. Built-in System Tools.

This example demonstrates how to discover and enable built-in system tools
(like `currentdate`) to allow the agent to fetch real-world data during chat.

Prerequisites:
    Set `OPENAI_API_KEY` in your `.env` file or environment.

Run:
    python examples/05_built_in_tools.py
"""

import asyncio
import os

from dotenv import load_dotenv
from rich import print as rprint
from rich.table import Table

from createagents import CreateAgent

load_dotenv()


async def main() -> None:
    """Run the built-in tools example."""
    if not os.getenv('OPENAI_API_KEY'):
        rprint(
            '[bold yellow]Warning:[/bold yellow] OPENAI_API_KEY is not set.\n'
            'Please configure OPENAI_API_KEY in your .env file.'
        )
        return

    rprint('[bold cyan]1. Inspecting Built-in Tools Catalog...[/bold cyan]')

    # 1. Initialize agent with the built-in 'currentdate' tool
    agent = CreateAgent(
        provider='openai',
        model='gpt-4o-mini',
        name='DateAwareAssistant',
        instructions='You are a helpful assistant with access to real-time tools.',
        tools=['currentdate'],
    )

    # 2. Display available tools in a table
    all_tools = agent.get_all_available_tools()
    table = Table(title='Available Tools for this Agent')
    table.add_column('Tool Name', style='cyan', no_wrap=True)
    table.add_column('Description', style='white')

    for name, desc in all_tools.items():
        table.add_row(name, desc)

    rprint(table)
    rprint()

    # 3. Ask a question requiring real-time date knowledge
    prompt = "What is today's exact date and day of the week? Use your currentdate tool."
    rprint(f'[bold blue]User:[/bold blue] {prompt}')

    response = await agent.chat(prompt)
    rprint(f'[bold green]Agent:[/bold green] {response}')


if __name__ == '__main__':
    asyncio.run(main())
