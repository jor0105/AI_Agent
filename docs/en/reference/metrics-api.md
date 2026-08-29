# Metrics API Reference

Comprehensive reference for the metrics subsystem in CreateAgents AI.

______________________________________________________________________

## `ChatMetrics`

**Namespace**: `createagents.domain`

Value Object dataclass storing telemetry for a single chat interaction.

### Structure

```python
@dataclass
class ChatMetrics:
    model: str
    latency_ms: float
    tokens_used: int | None = None
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    load_duration_ms: float | None = None  # Ollama
    prompt_eval_duration_ms: float | None = None  # Ollama
    eval_duration_ms: float | None = None  # Ollama
    timestamp: datetime = field(default_factory=datetime.now)
    success: bool = True
    error_message: str | None = None
```

### Fields

| Field                     | Type            | Description                         | Provider |
| ------------------------- | --------------- | ----------------------------------- | -------- |
| `model`                   | `str`           | Model identifier                    | All      |
| `latency_ms`              | `float`         | Interaction latency in milliseconds | All      |
| `success`                 | `bool`          | Successful request flag             | All      |
| `tokens_used`             | `int \| None`   | Total tokens consumed               | All      |
| `prompt_tokens`           | `int \| None`   | Prompt tokens                       | All      |
| `completion_tokens`       | `int \| None`   | Completion tokens                   | All      |
| `load_duration_ms`        | `float \| None` | Model load time (ms)                | Ollama   |
| `prompt_eval_duration_ms` | `float \| None` | Prompt evaluation duration (ms)     | Ollama   |
| `eval_duration_ms`        | `float \| None` | Token generation duration (ms)      | Ollama   |
| `timestamp`               | `datetime`      | Interaction timestamp               | All      |
| `error_message`           | `str \| None`   | Error details if `success=False`    | All      |

______________________________________________________________________

## `MetricsRecorder`

**Namespace**: `createagents.infra.adapters.common`

Abstract base for metrics aggregation across provider handlers:

- `OpenAIMetricsRecorder` — parses OpenAI `response.usage` (extracts `input_tokens`/`output_tokens` or `prompt_tokens`/`completion_tokens`, plus `total_tokens`; OpenAI does not report load durations)
- `OllamaMetricsRecorder` — parses Ollama usage (`prompt_eval_count`, `eval_count`) and converts nanosecond durations to milliseconds

### Methods

#### `__init__(metrics_list: List[ChatMetrics] | None = None)`

Initializes the recorder with an optional list of metrics. When omitted, creates a fresh internal list.

#### `record_success_metrics(model, start_time, response_api)`

Records metrics for a successful API call.

#### `record_error_metrics(model, start_time, error)`

Records metrics for a failed API call.

#### `get_metrics() -> List[ChatMetrics]`

Returns a shallow copy of the collected metrics list.

### Per-Agent Metrics Isolation

Metrics are scoped to the individual adapter instance assigned to each `CreateAgent`. Two distinct agent instances never share or overwrite each other's metrics:

```python
import asyncio
from createagents import CreateAgent


async def main():
    agent_a = CreateAgent(provider='ollama', model='YOUR_OLLAMA_MODEL')
    agent_b = CreateAgent(provider='ollama', model='YOUR_OLLAMA_MODEL')

    await agent_a.chat('Hello')

    print(len(agent_a.get_metrics()))  # 1
    print(len(agent_b.get_metrics()))  # 0


asyncio.run(main())
```

______________________________________________________________________

## Metrics Export

### JSON Export

```python
import asyncio
from createagents import CreateAgent


async def main():
    agent = CreateAgent(provider='openai', model='YOUR_MODEL')
    await agent.chat('test')

    # Export to string
    json_string = agent.export_metrics_json()

    # Export to file
    agent.export_metrics_json('metrics.json')


asyncio.run(main())
```

**JSON Output Format (Illustrative)**:

```json
{
  "summary": {
    "total_requests": 1,
    "successful": 1,
    "failed": 0,
    "success_rate": 100.0,
    "avg_latency_ms": 1234.56,
    "min_latency_ms": 1234.56,
    "max_latency_ms": 1234.56,
    "total_tokens": 250
  },
  "metrics": [
    {
      "model": "YOUR_MODEL",
      "latency_ms": 1234.56,
      "tokens_used": 250,
      "prompt_tokens": 100,
      "completion_tokens": 150,
      "load_duration_ms": null,
      "prompt_eval_duration_ms": null,
      "eval_duration_ms": null,
      "timestamp": "2026-08-25T20:00:00.000000",
      "success": true,
      "error_message": null
    }
  ]
}
```

### Prometheus Export

```python
# Export to string (Prometheus format)
prom_string = agent.export_metrics_prometheus()

# Export to file
agent.export_metrics_prometheus('metrics.prom')
```

**Prometheus Output Format (Illustrative)**:

```
# HELP chat_requests_total Total number of chat requests
# TYPE chat_requests_total counter
chat_requests_total 1

# HELP chat_requests_success_total Total number of successful chat requests
# TYPE chat_requests_success_total counter
chat_requests_success_total 1

# HELP chat_requests_failed_total Total number of failed chat requests
# TYPE chat_requests_failed_total counter
chat_requests_failed_total 0

# HELP chat_latency_ms_avg Average latency in milliseconds
# TYPE chat_latency_ms_avg gauge
chat_latency_ms_avg 1234.56

# HELP chat_latency_ms_min Minimum latency in milliseconds
# TYPE chat_latency_ms_min gauge
chat_latency_ms_min 1234.56

# HELP chat_latency_ms_max Maximum latency in milliseconds
# TYPE chat_latency_ms_max gauge
chat_latency_ms_max 1234.56

# HELP chat_tokens_total Total number of tokens used
# TYPE chat_tokens_total counter
chat_tokens_total 250

# HELP chat_requests_by_model Total requests by model
# TYPE chat_requests_by_model counter
chat_requests_by_model{model="YOUR_MODEL"} 1
```

______________________________________________________________________

## OpenAI vs Ollama Metrics

### OpenAI

- `model`
- `latency_ms`
- `tokens_used`
- `prompt_tokens`
- `completion_tokens`
- `success`

### Ollama

Includes all metrics above plus local compute durations:

- `load_duration_ms` — Model load time into memory/GPU
- `prompt_eval_duration_ms` — Prompt evaluation duration
- `eval_duration_ms` — Generation duration

______________________________________________________________________

## Complete Example

```python
import asyncio
from createagents import CreateAgent


async def main():
    agent = CreateAgent(provider='openai', model='YOUR_MODEL')

    # Execute calls
    await agent.chat('Question 1')
    await agent.chat('Question 2')
    await agent.chat('Question 3')

    # Retrieve metrics
    metrics = agent.get_metrics()

    for i, metric in enumerate(metrics, 1):
        print(f'Call #{i}')
        print(f'  Model: {metric.model}')
        print(f'  Latency: {metric.latency_ms:.2f}ms')
        print(f'  Success: {metric.success}')
        if metric.success:
            print(f'  Tokens: {metric.tokens_used}')
            print(f'    Prompt: {metric.prompt_tokens}')
            print(f'    Completion: {metric.completion_tokens}')
        else:
            print(f'  Error: {metric.error_message}')
        print()

    # Export
    agent.export_metrics_json('output.json')
    agent.export_metrics_prometheus('output.prom')


asyncio.run(main())
```

______________________________________________________________________

## See Also

- [CLI Usage Guide](../user-guide/cli-usage.md) - `/metrics` command
- [API Reference](api.md)

______________________________________________________________________

**Version:** 0.2.0 | **Updated:** 2026-08-27
