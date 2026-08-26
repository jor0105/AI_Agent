# 📚 API Reference

Documentação completa da API pública do **Create Agents AI**.

______________________________________________________________________

## 🤖 CreateAgent

O controller principal para interação com agentes de IA.

### Construtor

```python
CreateAgent(
    provider: str,
    model: str,
    name: Optional[str] = None,
    instructions: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None,
    tools: Optional[Sequence[Union[str, BaseTool]]] = None,
    history_max_size: int = 10
)
```

**Parâmetros:**

| Parâmetro          | Tipo   | Descrição                                                | Obrigatório |
| ------------------ | ------ | -------------------------------------------------------- | ----------- |
| `provider`         | `str`  | Provider de IA: `"openai"` ou `"ollama"`                 | ✅ Sim      |
| `model`            | `str`  | Nome do modelo (ex: `"gpt-4.1-mini"`, `"llama2"`)        | ✅ Sim      |
| `name`             | `str`  | Nome do agente                                           | ❌ Não      |
| `instructions`     | `str`  | Instruções/personalidade do agente                       | ❌ Não      |
| `config`           | `dict` | Configurações do modelo (temperature, max_tokens, etc)   | ❌ Não      |
| `tools`            | `list` | Lista de ferramentas: `["currentdate", "readlocalfile"]` | ❌ Não      |
| `history_max_size` | `int`  | Tamanho máximo do histórico (padrão: 10)                 | ❌ Não      |

**Exemplo:**

```python
from createagents import CreateAgent

agent = CreateAgent(
    provider='openai',
    model='gpt-4.1-mini',
    instructions='Você é um assistente técnico',
    config={'temperature': 0.7, 'max_tokens': 2000},
    tools=['currentdate'],
    history_max_size=20,
)
```

______________________________________________________________________

### Métodos

#### chat()

Envia mensagem ao agente e retorna resposta.

```python
async def chat(message: str) -> Union[str, StreamingResponseDTO]
```

**Parâmetros:**

- `message` (str): Mensagem do usuário

**Retorna:** `Union[str, StreamingResponseDTO]` - Resposta do agente

**Exemplo:**

```python
import asyncio


async def main():
    resposta = await agent.chat('Como criar uma função em Python?')
    print(resposta)


asyncio.run(main())
```

______________________________________________________________________

#### get_configs()

Retorna configurações e histórico do agente.

```python
def get_configs() -> Dict[str, Any]
```

**Retorna:** `dict` com:

- `name`: Nome do agente
- `model`: Modelo usado
- `provider`: Provider (openai/ollama)
- `instructions`: Instruções
- `history`: Lista de mensagens
- `history_max_size`: Tamanho máximo do histórico
- `tools`: Lista com nomes das ferramentas disponíveis
- `config`: Configurações do modelo

**Exemplo:**

```python
config = agent.get_configs()
print(f'Modelo: {config["model"]}')
print(f'Histórico: {len(config["history"])} mensagens')
```

______________________________________________________________________

#### clear_history()

Limpa o histórico de mensagens.

```python
def clear_history() -> None
```

**Exemplo:**

```python
agent.clear_history()
print('Histórico limpo!')
```

______________________________________________________________________

#### get_all_available_tools()

Retorna todas as ferramentas disponíveis para este agente específico (ferramentas do sistema + ferramentas customizadas).

```python
def get_all_available_tools() -> Dict[str, str]
```

**Retorna:** `dict` mapeando nome da ferramenta para descrição

**Comportamento:**

- Inclui todas as ferramentas do sistema (built-in) disponíveis
- Inclui ferramentas customizadas adicionadas quando o agente foi criado
- Remove duplicatas automaticamente (se uma ferramenta do sistema foi explicitamente adicionada)

**Exemplo:**

```python
from createagents import BaseTool


# Ferramenta customizada
class MyTool(BaseTool):
    name = 'my_tool'
    description = 'Minha ferramenta personalizada'

    parameters = {
        'type': 'object',
        'properties': {
            'input': {
                'type': 'string',
                'description': 'Texto de entrada para a ferramenta',
            },
            'limit': {
                'type': 'integer',
                'description': '(Opcional) Limite de itens a retornar',
            },
        },
        'required': ['input'],
    }

    def execute(self, **kwargs) -> str:
        # Implementação da ferramenta (exemplo)
        input_val = kwargs.get('input', '')
        limit = kwargs.get('limit', None)
        return f'Resultado para: {input_val}' + (
            f' (limit={limit})' if limit is not None else ''
        )


# Criar agente com ferramentas
agent = CreateAgent(
    provider='openai', model='gpt-4', tools=['currentdate', MyTool()]
)

# Listar todas as ferramentas
tools = agent.get_all_available_tools()
for name, description in tools.items():
    print(f'- {name}: {description}')
```

______________________________________________________________________

#### get_system_available_tools()

Retorna apenas as ferramentas do sistema (built-in) disponíveis globalmente.

```python
def get_system_available_tools() -> Dict[str, str]
```

**Retorna:** `dict` mapeando nome da ferramenta do sistema para descrição

**Comportamento:**

- Retorna apenas ferramentas built-in do framework
- Não inclui ferramentas customizadas do agente
- Útil para verificar quais ferramentas opcionais estão instaladas

**Exemplo:**

```python
agent = CreateAgent(provider='openai', model='gpt-4')

# Listar apenas ferramentas do sistema
system_tools = agent.get_system_available_tools()

print('Ferramentas do sistema disponíveis:')
for name, description in system_tools.items():
    print(f'- {name}: {description[:50]}...')

# Verificar se ferramenta opcional está disponível
if 'readlocalfile' in system_tools:
    print('✅ ReadLocalFileTool está instalada')
else:
    print('❌ Execute: pip install createagents[file-tools]')
```

**Diferença entre os métodos:**

| Método                         | Inclui Ferramentas do Sistema | Inclui Ferramentas Customizadas | Quando Usar                                            |
| ------------------------------ | ----------------------------- | ------------------------------- | ------------------------------------------------------ |
| `get_all_available_tools()`    | ✅ Sim                        | ✅ Sim                          | Ver todas as ferramentas que o agente pode usar        |
| `get_system_available_tools()` | ✅ Sim                        | ❌ Não                          | Verificar quais ferramentas opcionais estão instaladas |

______________________________________________________________________

#### get_metrics()

Retorna métricas de performance.

```python
def get_metrics() -> List[ChatMetrics]
```

**Retorna:** `List[ChatMetrics]` com:

- `latency_ms` (float): Latência total em milissegundos
- `tokens_used` (int | None): Tokens consumidos
- `success` (bool): Status de sucesso da requisição
- `timestamp` (datetime): Momento da execução

**Exemplo:**

```python
metrics = agent.get_metrics()
for m in metrics:
    print(
        f'Tempo: {m.latency_ms:.2f}ms, Tokens: {m.tokens_used}, Sucesso: {m.success}'
    )
```

______________________________________________________________________

#### export_metrics_json()

Exporta métricas em formato JSON.

```python
def export_metrics_json(filepath: Optional[str] = None) -> str
```

**Parâmetros:**

- `filepath` (str, opcional): Caminho para salvar

**Retorna:** JSON string

______________________________________________________________________

#### export_metrics_prometheus()

Exporta métricas em formato Prometheus.

```python
def export_metrics_prometheus(filepath: Optional[str] = None) -> str
```

**Parâmetros:**

- `filepath` (str, opcional): Caminho para salvar

**Retorna:** String formato Prometheus

______________________________________________________________________

#### start_cli()

Inicia sessão interativa de chat no terminal.

```python
def start_cli() -> None
```

**Descrição:**

Lança uma interface CLI completa com:

- Interface colorida e formatada
- Comandos: `/help`, `/metrics`, `/configs`, `/tools`, `/clear`
- Streaming em tempo real
- Indicadores de status

**Exemplo:**

```python
agent = CreateAgent(provider='openai', model='gpt-4')
agent.start_cli()  # Inicia CLI interativa
```

> 📚 [Guia completo da CLI](../user-guide/cli-usage.md)

______________________________________________________________________

## 🛠️ Ferramentas (Tools)

### Ferramentas Disponíveis

#### CurrentDateTool

Obtém data/hora em qualquer timezone.

**Nome:** `"currentdate"`

**Uso:**

```python
import asyncio


async def main():
    agent = CreateAgent(
        provider='openai', model='gpt-4', tools=['currentdate']
    )

    resposta = await agent.chat('Que dia é hoje?')
    print(resposta)


asyncio.run(main())
```

**Ações:**

- `date`: Data (YYYY-MM-DD)
- `time`: Hora (HH:MM:SS)
- `datetime`: Data e hora
- `timestamp`: Unix timestamp
- `date_with_weekday`: Data com dia da semana

______________________________________________________________________

#### ReadLocalFileTool

Lê arquivos locais em múltiplos formatos.

**Nome:** `"readlocalfile"`

**Requer:** `pip install createagents[file-tools]`

**Formatos:**

- Texto: TXT, MD, CSV, JSON, YAML
- Documentos: PDF
- Planilhas: Excel (XLS, XLSX), Parquet

**Uso:**

```python
import asyncio


async def main():
    agent = CreateAgent(
        provider='openai', model='gpt-4', tools=['readlocalfile']
    )

    resposta = await agent.chat('Leia o arquivo report.pdf')
    print(resposta)


asyncio.run(main())
```

**Limites:**

- Tamanho máximo: 100MB
- Tokens máximos: Depende da AI utilizada

______________________________________________________________________

## 📊 Configurações do Modelo

Parâmetros para controlar o comportamento do modelo (OpenAI/Ollama):

```python
config = {
    'temperature': 0.7,  # 0.0–2.0: Criatividade
    'max_tokens': 2000,  # >0: Limite de tokens
    'top_p': 0.9,  # 0.0–1.0: Nucleus sampling
    'think': True,  # Ollama: bool / OpenAI: str ["low", "medium" or "high"]
    'top_k': 40,  # >0: (Ollama)
}

agent = CreateAgent(provider='openai', model='gpt-4.1-mini', config=config)
```

**Parâmetros suportados:**

| Nome          | Faixa/Tipo  | Descrição                                                                                                 |
| ------------- | ----------- | --------------------------------------------------------------------------------------------------------- |
| `temperature` | 0.0–2.0     | Controla aleatoriedade. 0=determinístico, 2=mais criativo                                                 |
| `max_tokens`  | >0 (int)    | Limite de tokens na resposta                                                                              |
| `top_p`       | 0.0–1.0     | Nucleus sampling                                                                                          |
| `think`       | bool ou str | Ollama: bool (ativa/desativa), OpenAI: string de opções avançadas ("low", "medium" ou "high" disponíveis) |
| `top_k`       | >0 (int)    | Número de tokens considerados no sampling (Ollama)                                                        |
| `stream`      | bool        | Ativa streaming de tokens em tempo real (`StreamingResponseDTO`)                                          |

______________________________________________________________________

## 💡 Exemplos de Uso

### Exemplo Básico

```python
import asyncio
from createagents import CreateAgent


async def main():
    agent = CreateAgent(provider='openai', model='gpt-4')
    resposta = await agent.chat('Olá!')
    print(resposta)


asyncio.run(main())
```

### Com Ferramentas

```python
import asyncio


async def main():
    agent = CreateAgent(
        provider='openai',
        model='gpt-4',
        tools=['currentdate', 'readlocalfile'],
    )

    resposta = await agent.chat('Que dia é hoje?')
    print(resposta)


asyncio.run(main())
```

### Local (Ollama)

```python
import asyncio


async def main():
    agent = CreateAgent(provider='ollama', model='llama3.2')
    resposta = await agent.chat('Explique IA')
    print(resposta)


asyncio.run(main())
```

### CLI Interativa

```python
agent = CreateAgent(provider='openai', model='gpt-4')
agent.start_cli()  # Interface completa no terminal
```

______________________________________________________________________

**Versão:** 0.2.0 | **Atualização:** 02/12/2025
