"""09. Specialized Agent Personas & Hyperparameters.

This example demonstrates how to tailor agents for specific domains using
custom system instructions and generation hyperparameters (`temperature`,
`max_tokens`).

Prerequisites:
    Set `OPENAI_API_KEY` in your `.env` file or environment.

Run:
    python examples/09_specialized_personas.py
"""

import asyncio
import os

from dotenv import load_dotenv
from rich import print as rprint
from rich.panel import Panel

from createagents import CreateAgent

load_dotenv()


async def main() -> None:
    """Run the specialized personas example."""
    if not os.getenv('OPENAI_API_KEY'):
        rprint(
            '[bold yellow]Warning:[/bold yellow] OPENAI_API_KEY is not set.\n'
            'Please configure OPENAI_API_KEY in your .env file.'
        )
        return

    # Persona 1: Deterministic Code Reviewer (Low temperature for precision)
    rprint(
        Panel(
            '[bold cyan]Persona 1: Senior Python Code Reviewer[/bold cyan]\n'
            'Config: temperature=0.1, max_tokens=250',
            expand=False,
        )
    )
    code_reviewer = CreateAgent(
        provider='openai',
        model='gpt-4o-mini',
        name='PythonReviewer',
        instructions=(
            'You are a strict Senior Python Architect. Analyze code snippets '
            'and point out potential bugs or typing issues in 2-3 bullet points.'
        ),
        config={'temperature': 0.1, 'max_tokens': 250},
    )

    code_snippet = (
        'def process_items(items=[]):\n    items.append(1)\n    return items'
    )
    rprint(f'[bold blue]User Code:[/bold blue]\n{code_snippet}')
    review = await code_reviewer.chat(f'Review this function:\n{code_snippet}')
    rprint(f'[bold green]Reviewer:[/bold green]\n{review}\n')

    # Persona 2: Creative Technical Storyteller (High temperature for creativity)
    rprint(
        Panel(
            '[bold magenta]Persona 2: Creative Tech Storyteller[/bold magenta]\n'
            'Config: temperature=0.8, max_tokens=300',
            expand=False,
        )
    )
    storyteller = CreateAgent(
        provider='openai',
        model='gpt-4o-mini',
        name='SciFiStoryteller',
        instructions=(
            'You are an imaginative science fiction writer. Explain computing '
            'concepts as cosmic space adventures in 1-2 paragraphs.'
        ),
        config={'temperature': 0.8, 'max_tokens': 300},
    )

    story_prompt = 'Explain what a database deadlock is.'
    rprint(f'[bold blue]User:[/bold blue] {story_prompt}')
    story = await storyteller.chat(story_prompt)
    rprint(f'[bold green]Storyteller:[/bold green]\n{story}\n')


if __name__ == '__main__':
    asyncio.run(main())
