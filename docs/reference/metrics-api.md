# API de Métricas

Referência completa do sistema de métricas do CreateAgents AI.

______________________________________________________________________

## ChatMetrics

**Namespace**: `createagents.infra.config`

Dataclass que armazena métricas de uma chamada de chat.

### Estrutura

```python
@dataclass
class ChatMetrics:
    model: str
    latency_ms: float
    success: bool
    tokens_used: Optional[int] = None
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    load_duration_ms: Optional[float] = None  # Ollama
    prompt_eval_duration_ms: Optional[float] = None  # Ollama
    eval_duration_ms: Optional[float] = None  # Ollama
    error_message: Optional[str] = None
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
| `error_message`           | str \| None   | Mensagem de erro (se `success=False`) | Todos    |

______________________________________________________________________

## MetricsRecorder

**Namespace**: `createagents.infra.adapters.Common`

Base abstrata para gravação de métricas nos handlers. Ler o uso reportado é a
única parte específica de cada provider, então as subclasses implementam
apenas isso:

- `OpenAIMetricsRecorder` — lê `response.usage` (a OpenAI não reporta durações)
- `OllamaMetricsRecorder` — lê as contagens do Ollama e converte as durações
  de nanossegundos para milissegundos

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
agent_a = CreateAgent(provider="ollama", model="llama3")
agent_b = CreateAgent(provider="ollama", model="llama3")

await agent_a.chat("Olá")

len(agent_a.get_metrics())  # 1
len(agent_b.get_metrics())  # 0
```

______________________________________________________________________

## Exportação de Métricas

### JSON

```python
import asyncio
from createagents import CreateAgent

async def main():
    agent = CreateAgent(provider="openai", model="gpt-4")
    await agent.chat("teste")

    # Exportar para string
    json_string = agent.export_metrics_json()

    # Exportar para arquivo
    agent.export_metrics_json("metrics.json")

asyncio.run(main())
```

**Formato**:

```json
[
  {
    "model": "gpt-4",
    "latency_ms": 1234.56,
    "success": true,
    "tokens_used": 250,
    "prompt_tokens": 100,
    "completion_tokens": 150,
    "error_message": null
  }
]
```

### Prometheus

```python
# Exportar para string (formato Prometheus)
prom_string = agent.export_metrics_prometheus()

# Exportar para arquivo
agent.export_metrics_prometheus("metrics.prom")
```

**Formato**:

```
# HELP createagents_chat_latency_milliseconds Chat latency in milliseconds
# TYPE createagents_chat_latency_milliseconds histogram
createagents_chat_latency_milliseconds{model="gpt-4"} 1234.56

# HELP createagents_chat_tokens_total Total tokens used
# TYPE createagents_chat_tokens_total counter
createagents_chat_tokens_total{model="gpt-4",type="total"} 250
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
    agent = CreateAgent(provider="openai", model="gpt-4")

    # Fazer algumas chamadas
    await agent.chat("Pergunta 1")
    await agent.chat("Pergunta 2")
    await agent.chat("Pergunta 3")

    # Obter métricas
    metrics = agent.get_metrics()

    for i, metric in enumerate(metrics, 1):
        print(f"Chamada #{i}")
        print(f"  Modelo: {metric.model}")
        print(f"  Latência: {metric.latency_ms:.2f}ms")
        print(f"  Sucesso: {metric.success}")
        if metric.success:
            print(f"  Tokens: {metric.tokens_used}")
            print(f"    Prompt: {metric.prompt_tokens}")
            print(f"    Completion: {metric.completion_tokens}")
        else:
            print(f"  Erro: {metric.error_message}")
        print()

    # Exportar
    agent.export_metrics_json("output.json")
    agent.export_metrics_prometheus("output.prom")

asyncio.run(main())
```

______________________________________________________________________

## Veja Também

- [Guia de Uso CLI](../user-guide/cli-usage.md) - Comando `/metrics`
- [API Reference](api.md)

______________________________________________________________________

**Versão:** 0.1.3 | **Atualização:** 01/12/2025
