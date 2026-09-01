# 📚 API Reference

Documentação completa da API pública do **Create Agents AI**.

______________________________________________________________________

## 🤖 CreateAgent

O controller principal para interação com agentes de IA.

### Construtor

```python
def __init__(
    self,
    provider: str,
    model: str,
    name: str | None = None,
    instructions: str | None = None,
    config: Dict[str, Any] | None = None,
    tools: Sequence[Union[str, BaseTool]] | None = None,
    history_max_size: int = 10,
) -> None: ...
```

**Parâmetros:**

| Parâmetro          | Tipo   | Descrição                                                                             | Obrigatório |
| ------------------ | ------ | ------------------------------------------------------------------------------------- | ----------- |
| `provider`         | `str`  | Provider de IA: `"openai"` ou `"ollama"`                                              | ✅ Sim      |
| `model`            | `str`  | Nome do modelo (ex: `"YOUR_MODEL"`, `"YOUR_OLLAMA_MODEL"`)                            | ✅ Sim      |
| `name`             | `str`  | Nome do agente                                                                        | ❌ Não      |
| `instructions`     | `str`  | Instruções/personalidade do agente                                                    | ❌ Não      |
| `config`           | `dict` | Configurações do modelo (temperature, max_tokens, etc)                                | ❌ Não      |
| `tools`            | `list` | Lista de ferramentas (ex: `["currentdate"]`; `"readlocalfile"` requer `[file-tools]`) | ❌ Não      |
| `history_max_size` | `int`  | Tamanho máximo do histórico (padrão: 10)                                              | ❌ Não      |

**Exemplo:**

```python
from createagents import CreateAgent

agent = CreateAgent(
    provider='openai',
    model='YOUR_MODEL',
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
async def chat(message: str) -> Union[str, StreamingResponseDTO]: ...
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
def get_configs() -> Dict[str, Any]: ...
```

**Retorna:** `dict` com:

- `name`: Nome do agente
- `model`: Modelo usado
- `provider`: Provider (openai/ollama)
- `instructions`: Instruções
- `history`: Lista de mensagens
- `history_max_size`: Tamanho máximo do histórico
- `tools`: Lista com nomes das ferramentas configuradas e ativas no agente
- `config`: Configurações do modelo

**Exemplo:**

```python
config = agent.get_configs()
print(f'Modelo: {config["model"]}')
print(f'Histórico: {len(config["history"])} mensagens')
print(f'Tools ativas no agente: {config["tools"]}')
```

______________________________________________________________________

#### clear_history()

Limpa o histórico de mensagens.

```python
def clear_history() -> None: ...
```

**Exemplo:**

```python
agent.clear_history()
print('Histórico limpo!')
```

______________________________________________________________________

#### get_all_available_tools()

Retorna o catálogo de todas as ferramentas disponíveis no ambiente para este agente (ferramentas do sistema + ferramentas customizadas registradas).

> **Nota:** Para verificar quais ferramentas estão **efetivamente ativas no agente** para chamadas de chat, consulte `agent.get_configs()['tools']`.

```python
def get_all_available_tools() -> Dict[str, str]: ...
```

**Retorna:** `dict` mapeando nome da ferramenta para descrição

**Comportamento:**

- Inclui todas as ferramentas do sistema (built-in) disponíveis
- Inclui ferramentas customizadas adicionadas quando o agente foi criado
- Remove duplicatas automaticamente (se uma ferramenta do sistema foi explicitamente adicionada)

**Exemplo:**

```python
from createagents import BaseTool, CreateAgent


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
    provider='openai', model='YOUR_MODEL', tools=['currentdate', MyTool()]
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
def get_system_available_tools() -> Dict[str, str]: ...
```

**Retorna:** `dict` mapeando nome da ferramenta do sistema para descrição

**Comportamento:**

- Retorna apenas ferramentas built-in do framework
- Não inclui ferramentas customizadas do agente
- Útil para verificar quais ferramentas opcionais estão instaladas

**Exemplo:**

```python
from createagents import CreateAgent

agent = CreateAgent(provider='openai', model='YOUR_MODEL')

# Listar apenas ferramentas do sistema
system_tools = agent.get_system_available_tools()

print('Ferramentas do sistema disponíveis:')
for name, description in system_tools.items():
    print(f'- {name}: {description[:50]}...')

# Verificar se ferramenta opcional está disponível
if 'readlocalfile' in system_tools:
    print('✅ ReadLocalFileTool está instalada')
else:
    print("❌ Execute: pip install 'createagents[file-tools]'")
```

**Diferença entre os métodos:**

| Método                         | Inclui Ferramentas do Sistema | Inclui Ferramentas Customizadas | Quando Usar                                            |
| ------------------------------ | ----------------------------- | ------------------------------- | ------------------------------------------------------ |
| `get_all_available_tools()`    | ✅ Sim                        | ✅ Sim                          | Ver todas as ferramentas disponíveis no ambiente       |
| `get_system_available_tools()` | ✅ Sim                        | ❌ Não                          | Verificar quais ferramentas opcionais estão instaladas |

______________________________________________________________________

#### get_metrics()

Retorna métricas de performance.

```python
def get_metrics() -> List[ChatMetrics]: ...
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

Exporta o histórico de métricas em formato JSON (string ou arquivo).

```python
def export_metrics_json(filepath: str | None = None) -> str: ...
```

- **`filepath`** (str, opcional): Caminho do arquivo destino.
- **Retorna:** `str` (conteúdo JSON).

______________________________________________________________________

#### export_metrics_prometheus()

Exporta métricas formatadas para coleta pelo Prometheus (string ou arquivo).

```python
def export_metrics_prometheus(filepath: str | None = None) -> str: ...
```

- **`filepath`** (str, opcional): Caminho do arquivo destino.
- **Retorna:** `str` (formato Prometheus).

______________________________________________________________________

#### start_cli()

Inicia sessão interativa de chat no terminal com interface ANSI, comandos (`/help`, `/metrics`, `/configs`, `/tools`, `/clear`), streaming e indicador de status.

```python
def start_cli() -> None: ...
```

**Exemplo:**

```python
from createagents import CreateAgent

agent = CreateAgent(
    provider='openai', model='YOUR_MODEL', config={'stream': True}
)
agent.start_cli()  # Inicia CLI interativa com streaming
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
from createagents import CreateAgent


async def main():
    agent = CreateAgent(
        provider='openai', model='YOUR_MODEL', tools=['currentdate']
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

Lê arquivos locais em múltiplos formatos com teto fixo de segurança de 100 MiB (104.857.600 bytes).

**Nome:** `"readlocalfile"`

**Requer:** `pip install 'createagents[file-tools]'`

**Formatos Suportados (32 extensões):**

- **Texto e código:** TXT, LOG, MD, PY, JS, HTML, CSS, JSON, XML, YAML, YML, RST, INI, CFG, CONF, SH, BASH, ZSH
- **Tabelas e dados:** CSV, Excel (XLSX, XLSM e legado XLS com `xlrd`), Parquet
- **Documentos:** PDF, Word (DOC, DOCX), PowerPoint (PPT, PPTX), OpenDocument (ODT), EPUB, MSG, RTF

**Uso:**

```python
import asyncio
from createagents import CreateAgent


async def main():
    agent = CreateAgent(
        provider='openai', model='YOUR_MODEL', tools=['readlocalfile']
    )

    resposta = await agent.chat('Leia o arquivo report.pdf')
    print(resposta)


asyncio.run(main())
```

**Limites:**

- Tamanho máximo de arquivo: 100 MiB (104.857.600 bytes)
- Tokens máximos: Depende da janela de contexto do modelo utilizado

______________________________________________________________________

## 📊 Configurações do Modelo

Parâmetros para controlar o comportamento do modelo (OpenAI/Ollama):

```python
from createagents import CreateAgent

config = {
    'temperature': 0.7,  # 0.0–2.0: Criatividade
    'max_tokens': 2000,  # >0: Limite de tokens
    'top_p': 0.9,  # 0.0–1.0: Nucleus sampling
    'think': 'medium',  # OpenAI: "low"|"medium"|"high"; Ollama: bool ou "low"|"medium"|"high"
    'top_k': 40,  # >0: (Ollama)
}

agent = CreateAgent(provider='openai', model='YOUR_MODEL', config=config)
```

**Parâmetros suportados:**

| Nome          | Faixa/Tipo  | Descrição                                                                                                 |
| ------------- | ----------- | --------------------------------------------------------------------------------------------------------- |
| `temperature` | 0.0–2.0     | Controla aleatoriedade; no OpenAI depende do modelo (GPT-5, GPT-5 Mini e GPT-5 nano não aceitam)          |
| `max_tokens`  | >0 (int)    | Limite de tokens na resposta                                                                              |
| `top_p`       | 0.0–1.0     | Nucleus sampling; no OpenAI depende do modelo (GPT-5, GPT-5 Mini e GPT-5 nano não aceitam)                |
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
    agent = CreateAgent(provider='openai', model='YOUR_MODEL')
    resposta = await agent.chat('Olá!')
    print(resposta)


asyncio.run(main())
```

### Com Ferramentas

```python
import asyncio
from createagents import CreateAgent


async def main():
    agent = CreateAgent(
        provider='openai',
        model='YOUR_MODEL',
        tools=['currentdate'],  # use 'readlocalfile' com [file-tools]
    )

    resposta = await agent.chat('Que dia é hoje?')
    print(resposta)


asyncio.run(main())
```

### Local (Ollama)

```python
import asyncio
from createagents import CreateAgent


async def main():
    agent = CreateAgent(provider='ollama', model='YOUR_OLLAMA_MODEL')
    resposta = await agent.chat('Explique IA')
    print(resposta)


asyncio.run(main())
```

### CLI Interativa

```python
from createagents import CreateAgent

agent = CreateAgent(provider='openai', model='YOUR_MODEL')
agent.start_cli()  # Interface completa no terminal
```

______________________________________________________________________

**Versão:** 0.2.0 | **Atualização:** 2026-08-27
