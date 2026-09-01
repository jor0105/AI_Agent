# 📝 Guia de Logging

Este guia explica como configurar e utilizar o sistema de logging da biblioteca `CreateAgentsAI`, que agora segue **Clean Architecture** com interfaces de logging no domínio e implementações na infraestrutura.

______________________________________________________________________

## 🏗️ Arquitetura de Logging

### LoggerInterface (Domínio)

A biblioteca define uma **`LoggerInterface`** abstrata no domínio (`src/createagents/domain/interfaces/`), permitindo que as camadas de domínio e aplicação usem logging **sem depender** de implementações concretas de infraestrutura.

```python
from abc import ABC, abstractmethod


class LoggerInterface(ABC):
    """Interface abstrata para logging."""

    @abstractmethod
    def debug(self, message: str, *args, **kwargs) -> None:
        pass

    @abstractmethod
    def info(self, message: str, *args, **kwargs) -> None:
        pass

    @abstractmethod
    def warning(self, message: str, *args, **kwargs) -> None:
        pass

    @abstractmethod
    def error(self, message: str, *args, **kwargs) -> None:
        pass

    @abstractmethod
    def critical(self, message: str, *args, **kwargs) -> None:
        pass
```

### StandardLogger (Infraestrutura)

A implementação concreta está na camada de infraestrutura (`src/createagents/infra/config/`):

```python
class StandardLogger(LoggerInterface):
    """Implementação padrão do LoggerInterface usando Python logging."""

    def __init__(self, logger: logging.Logger):
        self._logger = logger

    def debug(self, message: str, *args, **kwargs) -> None:
        self._logger.debug(message, *args, **kwargs)

    # ...outros métodos
```

______________________________________________________________________

## 🔇 Comportamento Padrão

Ao importar e usar a biblioteca, nenhum log será exibido no console ou salvo em arquivo, a menos que você configure explicitamente o sistema de logging.

Isso é feito intencionalmente para evitar conflitos com a configuração de logging da aplicação que consome a biblioteca.

______________________________________________________________________

## 🛠️ Como Ativar Logs

### Opção 1: Configuração Rápida (Desenvolvimento)

Para desenvolvimento, testes ou scripts simples, use o helper `configure_for_development`:

```python
import logging
from createagents import LoggingConfig

# Ativa logs no nível INFO
LoggingConfig.configure_for_development(level=logging.INFO)

# Ou para ver tudo (DEBUG)
LoggingConfig.configure_for_development(level=logging.DEBUG)
```

Isso configurará a saída de logs legíveis no console (via `StreamHandler`) com sanitização automática de dados sensíveis.

### Opção 2: Configuração Padrão do Python

Se sua aplicação já configura o logging, a biblioteca respeitará essa configuração:

```python
import logging

# Configuração da sua aplicação
logging.basicConfig(level=logging.INFO)

# Agora os logs da biblioteca aparecerão
from createagents import CreateAgent
```

### Opção 3: Configuração Avançada

Para controlar apenas os logs da biblioteca:

```python
import logging

# Configura apenas o logger 'createagents'
logger = logging.getLogger('createagents')
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())
```

______________________________________________________________________

## 🎯 Uso em Componentes Customizados

Se você estiver **estendendo a biblioteca** (ex.: criando ferramentas customizadas ou handlers), pode usar a `LoggerInterface`:

### Exemplo: Ferramenta Customizada com Logging

```python
from createagents import BaseTool
from createagents.domain.interfaces import LoggerInterface


class MyCustomTool(BaseTool):
    name = 'my_tool'
    description = 'Minha ferramenta customizada'
    parameters = {...}

    def __init__(self, logger: LoggerInterface):
        self._logger = logger

    def execute(self, **kwargs) -> str:
        self._logger.info('Executando MyCustomTool com: %s', kwargs)
        try:
            result = self._do_something(kwargs)
            self._logger.debug('Resultado: %s', result)
            return result
        except Exception as e:
            self._logger.error('Erro em MyCustomTool: %s', str(e))
            raise
```

### Injeção de Dependência

```python
from createagents.infra.config import LoggingConfig, StandardLogger

# Criar logger
python_logger = LoggingConfig.get_logger(__name__)
logger_interface = StandardLogger(python_logger)

# Injetar na ferramenta
my_tool = MyCustomTool(logger=logger_interface)
```

______________________________________________________________________

## 🔒 Segurança e Privacidade

A biblioteca inclui recursos automáticos de segurança nos logs:

- **Sanitização**: Chaves de API, senhas e tokens são mascarados automaticamente (ex: `[API_KEY_REDACTED]`).
- **Filtros**: Em produção, você pode configurar para logar apenas erros.

______________________________________________________________________

## ⚙️ Variáveis de Ambiente

Você pode controlar o logging através de variáveis de ambiente:

| Variável          | Descrição                                            | Padrão       |
| ----------------- | ---------------------------------------------------- | ------------ |
| `LOG_LEVEL`       | Nível de log (DEBUG, INFO, WARNING, ERROR, CRITICAL) | INFO         |
| `LOG_TO_FILE`     | Salvar logs em arquivo (true/false)                  | false        |
| `LOG_FILE_PATH`   | Caminho do arquivo de log                            | logs/app.log |
| `LOG_JSON_FORMAT` | Usar formato JSON estruturado                        | false        |

______________________________________________________________________

## 📊 Logs em JSON (Produção)

Para ambientes de produção com agregação de logs (Datadog, CloudWatch, ELK), ative o formato JSON:

```python
LoggingConfig.configure(json_format=True)
```

Ou via ambiente:

```bash
export LOG_JSON_FORMAT=true
```

Isso gerará logs estruturados fáceis de indexar:

```json
{
  "timestamp": "2026-08-25 10:00:00,000",
  "level": "INFO",
  "logger": "createagents.infra.adapters.openai.adapter",
  "message": "Chat request completed successfully",
  "module": "chat_adapter",
  "function": "chat",
  "line": 85
}
```

Quando houver uma exceção tratada via `exc_info=True`, o campo `"exception"` com o traceback completo sanitizado é adicionado ao JSON.

______________________________________________________________________

## 🔍 Componentes que Usam Logging

### Use Cases

Os use cases recebem um `LoggerInterface` injetado pelo `AgentComposer` e
caem em `NullLogger` quando nenhum é fornecido — é assim que a camada de
aplicação registra logs sem nunca importar `infra`:

```python
class ChatWithAgentUseCase:
    def __init__(
        self,
        chat_repository: ChatRepository,
        logger: LoggerInterface | None = None,
    ):
        self._logger = logger or NullLogger()
```

### ToolExecutor

O `ToolExecutor` no domínio usa `LoggerInterface` para logar execuções de ferramentas:

```python
class ToolExecutor:
    def __init__(self, tools: list[BaseTool], logger: LoggerInterface) -> None:
        self.__logger = logger

    async def execute_tool(self, tool_name: str, **kwargs):
        self.__logger.info("Attempting to execute tool: '%s'", tool_name)
        # ...
```

### Handlers (OpenAI/Ollama)

Os handlers de streaming usam logging para métricas e debugging:

```python
class OpenAIStreamHandler:
    def __init__(self, *args, **kwargs):
        self._logger = LoggingConfig.get_logger(__name__)

    async def handle_stream(self, *args, **kwargs):
        self._logger.debug('Starting streaming response')
        # ...
```

______________________________________________________________________

## 💡 Best Practices

1. **Use níveis apropriados**:

   - `DEBUG`: Detalhes de execução, valores de variáveis
   - `INFO`: Eventos normais (agent criado, ferramenta executada)
   - `WARNING`: Situações incomuns mas recuperáveis
   - `ERROR`: Erros que impedem operação
   - `CRITICAL`: Falhas graves do sistema

2. **Nunca logue dados sensíveis**:

   - A biblioteca sanitiza automaticamente, mas evite logar explicitamente senhas, tokens, etc.

3. **Use formatação lazy**:

   ```python
   # BOM - formatação lazy (não computa string se o nível estiver inativo)
   logger.debug('Processing %s items in %sms', len(items), duration_ms)

   # RUIM - concatenação direta / f-strings eager
   logger.debug(f'Processing {len(items)} items in {duration_ms}ms')
   ```

4. **Identifique a origem**:

   Use sempre `LoggingConfig.get_logger(__name__)` em vez de loggers genéricos para preservar módulo, função e linha exatos nos logs estruturados.

______________________________________________________________________

**Versão:** 0.3.0 | **Atualização:** 2026-08-27
