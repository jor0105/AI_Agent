"""03. Multi-turn Conversation & History Management.

This example demonstrates how agents maintain conversational context across
multiple messages, how to inspect conversation history, configure history
size limits, and clear memory.

Prerequisites:
    Set `OPENAI_API_KEY` in your `.env` file or environment.

Run:
    python examples/03_multi_turn_and_history.py
"""

import asyncio
import os

from dotenv import load_dotenv
from rich import print as rprint
from rich.panel import Panel

from createagents import CreateAgent

load_dotenv()


async def main() -> None:
    """Run the multi-turn conversation and history example."""
    if not os.getenv('OPENAI_API_KEY'):
        rprint(
            '[bold yellow]Warning:[/bold yellow] OPENAI_API_KEY is not set.\n'
            'Please configure OPENAI_API_KEY in your .env file.'
        )
        return

    rprint(
        Panel(
            '[bold cyan]Multi-Turn Conversation & History Demo[/bold cyan]\n'
            'Demonstrating context retention, history inspection, and memory clearing.',
            expand=False,
        )
    )

    # 1. Initialize agent with a history limit of 10 messages
    agent = CreateAgent(
        provider='openai',
        model='gpt-4o-mini',
        name='MemoryAgent',
        instructions='You are a helpful assistant with excellent memory.',
        history_max_size=10,
    )

    # 2. Turn 1: Introduce a secret fact
    prompt_1 = (
        'My favorite programming language is Rust and my lucky number is 42.'
    )
    rprint(f'[bold blue]User (Turn 1):[/bold blue] {prompt_1}')
    resp_1 = await agent.chat(prompt_1)
    rprint(f'[bold green]Agent:[/bold green] {resp_1}\n')

    # 3. Turn 2: Query context
    prompt_2 = 'What is my favorite language and what is my lucky number?'
    rprint(f'[bold blue]User (Turn 2):[/bold blue] {prompt_2}')
    resp_2 = await agent.chat(prompt_2)
    rprint(f'[bold green]Agent:[/bold green] {resp_2}\n')

    # 4. Inspect current history
    configs = agent.get_configs()
    history = configs.get('history', [])
    rprint(f'[bold magenta]Messages in history:[/bold magenta] {len(history)}')
    for idx, msg in enumerate(history, 1):
        role = msg.get('role', 'unknown')
        content = msg.get('content', '')
        rprint(f'  {idx}. [{role.upper()}]: {content[:60]}...')

    # 5. Clear history
    rprint('\n[bold yellow]Clearing agent history...[/bold yellow]')
    agent.clear_history()
    rprint(
        f'[bold magenta]Messages in history after clear:[/bold magenta] {len(agent.get_configs().get("history", []))}\n'
    )

    # 6. Turn 3: Test memory after clearing
    prompt_3 = 'Do you remember my favorite language?'
    rprint(f'[bold blue]User (Turn 3):[/bold blue] {prompt_3}')
    resp_3 = await agent.chat(prompt_3)
    rprint(f'[bold green]Agent:[/bold green] {resp_3}\n')


if __name__ == '__main__':
    asyncio.run(main())
