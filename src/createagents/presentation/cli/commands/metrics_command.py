from typing import TYPE_CHECKING, override

from .base_command import CommandHandler

if TYPE_CHECKING:
    from ..protocols import AgentFacade

_MILLISECONDS_PER_SECOND = 1000


class MetricsCommandHandler(CommandHandler):
    """Handles the /metrics command.

    Responsibility: Display agent performance metrics.
    This follows SRP by handling only metrics-related functionality.
    """

    @override
    def execute(self, agent: 'AgentFacade', user_input: str) -> None:
        """Execute the metrics command.

        Args:
            agent: The agent facade.
            user_input: The user's input string.

        """
        metrics = agent.get_metrics()
        if not metrics:
            self._renderer.render_system_message(
                'No metrics available yet. Start chatting to collect data!'
            )
            return

        rows = [
            '## Performance Metrics\n',
            '| Model | Duration | Tokens (In/Out/Total) |',
            '|-------|----------|-----------------------|',
        ]
        for metric in metrics:
            duration_s = (
                metric.latency_ms / _MILLISECONDS_PER_SECOND
                if metric.latency_ms
                else 0
            )
            rows.append(
                f'| {metric.model} | {duration_s:.2f}s | '
                f'{metric.prompt_tokens} / {metric.completion_tokens} / '
                f'{metric.tokens_used} |'
            )

        self._render_markdown('\n'.join(rows) + '\n')

    @override
    def get_aliases(self) -> list[str]:
        """Get metrics command aliases."""
        return ['/metrics', 'get_metrics']
