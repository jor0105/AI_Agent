"""08. Metrics, Observability, and Logging.

This example demonstrates how to inspect performance metrics (request latency,
token counts), export metrics in JSON and Prometheus formats, and configure
the library logging system.

Prerequisites:
    Set `OPENAI_API_KEY` in your `.env` file or environment.

Run:
    python examples/08_metrics_and_observability.py
"""

import asyncio
import logging
import os

from dotenv import load_dotenv
from rich import print as rprint
from rich.panel import Panel
from rich.syntax import Syntax

from createagents import CreateAgent, LoggingConfig

load_dotenv()


async def main() -> None:
    """Run the metrics and observability example."""
    if not os.getenv('OPENAI_API_KEY'):
        rprint(
            '[bold yellow]Warning:[/bold yellow] OPENAI_API_KEY is not set.\n'
            'Please configure OPENAI_API_KEY in your .env file.'
        )
        return

    # 1. Configure logging for the library
    rprint('[bold cyan]1. Configuring Logging...[/bold cyan]')
    LoggingConfig.configure_for_development(level=logging.INFO)

    # 2. Create the agent
    agent = CreateAgent(
        provider='openai',
        model='gpt-4o-mini',
        name='MetricsAgent',
        instructions='You are a concise AI assistant.',
    )

    # 3. Perform a couple of chat interactions
    rprint('\n[bold cyan]2. Performing Interactions...[/bold cyan]')
    await agent.chat('What is 2 + 2?')
    await agent.chat('Explain recursion in one short sentence.')

    # 4. Inspect collected ChatMetrics
    metrics = agent.get_metrics()
    rprint(
        f'\n[bold green]Total metric records collected:[/bold green] {len(metrics)}'
    )

    for idx, metric in enumerate(metrics, 1):
        rprint(
            f'  Interaction #{idx}: '
            f'Model={metric.model}, '
            f'Latency={metric.latency_ms:.2f}ms, '
            f'PromptTokens={metric.prompt_tokens}, '
            f'CompletionTokens={metric.completion_tokens}'
        )

    # 5. Export to JSON
    json_metrics = agent.export_metrics_json()
    rprint('\n[bold magenta]3. Exported Metrics (JSON Format):[/bold magenta]')
    rprint(
        Panel(Syntax(json_metrics, 'json', theme='monokai', line_numbers=True))
    )

    # 6. Export to Prometheus format
    prom_metrics = agent.export_metrics_prometheus()
    rprint(
        '[bold magenta]4. Exported Metrics (Prometheus Format):[/bold magenta]'
    )
    rprint(
        Panel(Syntax(prom_metrics, 'text', theme='monokai', line_numbers=True))
    )


if __name__ == '__main__':
    asyncio.run(main())
