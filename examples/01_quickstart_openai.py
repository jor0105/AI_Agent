"""01. Quickstart: OpenAI Agent.

This example demonstrates how to create and chat with a minimal AI agent
using OpenAI.

Prerequisites:
    Set the `OPENAI_API_KEY` environment variable in your `.env` file or shell.

Run:
    python examples/01_quickstart_openai.py
"""

import asyncio
import os

from dotenv import load_dotenv
from rich import print as rprint

from createagents import CreateAgent

# Load environment variables from .env file
load_dotenv()


async def main() -> None:
    """Run the OpenAI quickstart example."""
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        rprint(
            '[bold yellow]Warning:[/bold yellow] OPENAI_API_KEY is not set.\n'
            'Please set it in your .env file or environment to run this example:\n'
            '  export OPENAI_API_KEY="sk-..."'
        )
        return

    rprint('[bold cyan]1. Initializing OpenAI Agent...[/bold cyan]')

    # 1. Create the agent
    agent = CreateAgent(
        provider='openai',
        model='gpt-4o-mini',
        name='QuickstartAssistant',
        instructions='You are a helpful and concise software engineering mentor.',
    )

    rprint(
        f'[green]Agent created successfully:[/green] {agent.get_configs()["name"]}\n'
    )

    # 2. Send a message
    user_prompt = (
        'In 2 short sentences, explain why Clean Architecture is useful.'
    )
    rprint(f'[bold blue]User:[/bold blue] {user_prompt}')

    response = await agent.chat(user_prompt)

    rprint(f'[bold green]Agent:[/bold green] {response}')


if __name__ == '__main__':
    asyncio.run(main())
