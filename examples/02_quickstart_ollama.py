"""02. Quickstart: Ollama Local Agent.

This example demonstrates how to create and chat with a 100% local, offline
AI agent using Ollama. No API keys are required.

Prerequisites:
    1. Install Ollama (https://ollama.com)
    2. Pull and run a local model: `ollama run llama3.2`

Run:
    python examples/02_quickstart_ollama.py
"""

import asyncio

from dotenv import load_dotenv
from rich import print as rprint

from createagents import CreateAgent

# Load environment variables (e.g. OLLAMA_HOST if custom)
load_dotenv()


async def main() -> None:
    """Run the Ollama quickstart example."""
    rprint(
        '[bold cyan]1. Initializing Local Ollama Agent (llama3.2)...[/bold cyan]'
    )

    # 1. Create the agent with Ollama provider
    agent = CreateAgent(
        provider='ollama',
        model='llama3.2',
        name='LocalAssistant',
        instructions='You are a fast, concise local AI assistant.',
    )

    rprint(
        f'[green]Agent created successfully:[/green] {agent.get_configs()["name"]}\n'
    )

    # 2. Send a message
    user_prompt = 'List 3 benefits of running local AI models on your own machine in bullet points.'
    rprint(f'[bold blue]User:[/bold blue] {user_prompt}')

    try:
        response = await agent.chat(user_prompt)
        rprint(f'[bold green]Agent:[/bold green] {response}')
    except (ConnectionError, RuntimeError, OSError) as exc:
        rprint(
            '\n[bold yellow]Could not reach Ollama server:[/bold yellow]\n'
            f'  Error: {exc}\n\n'
            'Please ensure the Ollama application is running and the model is downloaded:\n'
            '  1. Start Ollama: `ollama serve` (or open the Ollama app)\n'
            '  2. Pull the model: `ollama pull llama3.2`\n'
        )


if __name__ == '__main__':
    asyncio.run(main())
