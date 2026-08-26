# API de Métricas

Referência completa do sistema de métricas do CreateAgents AI.

______________________________________________________________________

## ChatMetrics

**Namespace**: `createagents.domain`

Dataclass (Value Object) que armazena métricas de uma chamada de chat.

### Estrutura

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

### Campos

| Campo                     | Tipo          | Descrição                             | Provider |
| ------------------------- | ------------- | ------------------------------------- | -------- |
| `model`                   | str           | Nome do modelo usado                  | Todos    |
| `latency_ms`              | float         | Latência total em ms                  | Todos    |
| `success`                 | bool          | Se chamada foi bem-sucedida           | Todos    |
| `tokens_used`             | int \| None   | Total de tokens                       | Todos    |
| `prompt_tokens`           | int \| None   | Tokens do prompt                      | Todos    |
| `completion_tokens`       | int \| None   | Tokens da resposta                    | Todos    |
| `load_duration_ms`        | float \| None | Tempo de carregamento do modelo (ms)  | Ollama   |
| `prompt_eval_duration_ms` | float \| None | Tempo de avaliação do prompt (ms)     | Ollama   |
| `eval_duration_ms`        | float \| None | Tempo de geração da resposta (ms)     | Ollama   |
| `timestamp`               | datetime      | Data e hora da interação              | Todos    |
| `error_message`           | str \| None   | Mensagem de erro (se `success=False`) | Todos    |

______________________________________________________________________

## MetricsRecorder

**Namespace**: `createagents.infra.adapters.Common`

Base abstrata para gravação de métricas nos handlers. Ler o uso reportado é a
única parte específica de cada provider, então as subclasses implementam
apenas isso:

- `OpenAIMetricsRecorder` — lê `response.usage` (extrai `input_tokens`/`output_tokens` ou `prompt_tokens`/`completion_tokens`, além de `total_tokens`; a OpenAI não reporta durações de modelo)
- `OllamaMetricsRecorder` — lê as contagens do Ollama (`prompt_eval_count`, `eval_count`) e converte as durações de nanossegundos para milissegundos

### Métodos

#### `__init__(metrics_list: Optional[List[ChatMetrics]] = None)`

Inicializa o recorder com lista opcional de métricas. Quando omitida, cria a
própria lista.

#### `record_success_metrics(model, start_time, response_api)`

Grava métricas para operação bem-sucedida.

**Parâmetros**:

- `model` (str): Nome do modelo
- `start_time` (float): Timestamp do início
- `response_api` (Any): Resposta da API

#### `record_error_metrics(model, start_time, error)`

Grava métricas para operação com erro.

**Parâmetros**:

- `model` (str): Nome do modelo
- `start_time` (float): Timestamp do início
- `error` (Any): Erro ocorrido

#### `get_metrics() -> List[ChatMetrics]`

Retorna cópia da lista de métricas.

### Isolamento entre agentes

As métricas pertencem ao adapter, e cada `CreateAgent` recebe o seu próprio.
Dois agentes com o mesmo provider e modelo têm métricas independentes:

```python
import asyncio
from createagents import CreateAgent


async def main():
    agent_a = CreateAgent(provider='ollama', model='llama3')
    agent_b = CreateAgent(provider='ollama', model='llama3')

    await agent_a.chat('Olá')

    print(len(agent_a.get_metrics()))  # 1
    print(len(agent_b.get_metrics()))  # 0


asyncio.run(main())
```

______________________________________________________________________

## Exportação de Métricas

### JSON

```python
import asyncio
from createagents import CreateAgent


async def main():
    agent = CreateAgent(provider='openai', model='gpt-4')
    await agent.chat('teste')

    # Exportar para string
    json_string = agent.export_metrics_json()

    # Exportar para arquivo
    agent.export_metrics_json('metrics.json')


asyncio.run(main())
```

**Formato**:

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
      "model": "gpt-4",
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

### Prometheus

```python
# Exportar para string (formato Prometheus)
prom_string = agent.export_metrics_prometheus()

# Exportar para arquivo
agent.export_metrics_prometheus('metrics.prom')
```

**Formato**:

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
chat_requests_by_model{model="gpt-4"} 1
```

______________________________________________________________________

## Métricas OpenAI vs Ollama

### OpenAI

Métricas disponíveis:

- `model`
- `latency_ms`
- `tokens_used`
- `prompt_tokens`
- `completion_tokens`
- `success`

### Ollama

Métricas disponíveis (todas do OpenAI +):

- `load_duration_ms` - Tempo para carregar modelo
- `prompt_eval_duration_ms` - Tempo para processar prompt
- `eval_duration_ms` - Tempo para gerar resposta

______________________________________________________________________

## Exemplo Completo

```python
import asyncio
from createagents import CreateAgent


async def main():
    agent = CreateAgent(provider='openai', model='gpt-4')

    # Fazer algumas chamadas
    await agent.chat('Pergunta 1')
    await agent.chat('Pergunta 2')
    await agent.chat('Pergunta 3')

    # Obter métricas
    metrics = agent.get_metrics()

    for i, metric in enumerate(metrics, 1):
        print(f'Chamada #{i}')
        print(f'  Modelo: {metric.model}')
        print(f'  Latência: {metric.latency_ms:.2f}ms')
        print(f'  Sucesso: {metric.success}')
        if metric.success:
            print(f'  Tokens: {metric.tokens_used}')
            print(f'    Prompt: {metric.prompt_tokens}')
            print(f'    Completion: {metric.completion_tokens}')
        else:
            print(f'  Erro: {metric.error_message}')
        print()

    # Exportar
    agent.export_metrics_json('output.json')
    agent.export_metrics_prometheus('output.prom')


asyncio.run(main())
```

______________________________________________________________________

## Veja Também

- [Guia de Uso CLI](../user-guide/cli-usage.md) - Comando `/metrics`
- [API Reference](api.md)

______________________________________________________________________

**Versão:** 0.2.0 | **Atualização:** 2026-08-25
