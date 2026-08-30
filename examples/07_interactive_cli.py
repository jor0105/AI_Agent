"""07. Interactive Terminal CLI.

This example demonstrates how to launch the built-in rich interactive CLI
session. The CLI supports multi-turn chatting, streaming, color rendering,
and slash commands.

Slash Commands available in the CLI:
    /help     - Show available commands and keybindings
    /metrics  - Display real-time latency and token statistics
    /configs  - Show the current agent configurations
    /tools    - List active system and agent-specific tools
    /clear    - Clear conversation memory
    /exit     - Exit the interactive chat session

Prerequisites:
    Set `OPENAI_API_KEY` in your `.env` file or environment.

Run:
    python examples/07_interactive_cli.py
"""

import os

from dotenv import load_dotenv
from rich import print as rprint

from createagents import CreateAgent

load_dotenv()


def main() -> None:
    """Launch the interactive CLI chat application."""
    if not os.getenv('OPENAI_API_KEY'):
        rprint(
            '[bold yellow]Warning:[/bold yellow] OPENAI_API_KEY is not set.\n'
            'Please configure OPENAI_API_KEY in your .env file.'
        )
        return

    rprint(
        '[bold cyan]Starting Interactive Terminal Chat CLI...[/bold cyan]\n'
        'Type [bold green]/help[/bold green] to see commands or [bold red]/exit[/bold red] to quit.\n'
    )

    # Initialize agent with streaming and date tool
    agent = CreateAgent(
        provider='openai',
        model='gpt-4o-mini',
        name='TerminalAssistant',
        instructions='You are a helpful and concise terminal AI assistant.',
        tools=['currentdate'],
        config={'stream': True},
    )

    # Launch the interactive CLI
    agent.start_cli()


if __name__ == '__main__':
    main()
