# Guia de Uso da CLI Interativa

A CLI (Command-Line Interface) do CreateAgents AI oferece uma interface interativa profissional para conversar com seus agentes de IA.

______________________________________________________________________

## 🚀 Início Rápido

```python
from createagents import CreateAgent

# Criar agente
agent = CreateAgent(
    provider='openai',
    model='gpt-4',
    name='Assistente',
    instructions='Você é um assistente prestativo',
)

# Iniciar CLI interativa
agent.start_cli()
```

______________________________________________________________________

## ✨ Recursos

- **🎨 Interface Formatada**: Renderização ANSI de elementos Markdown (cabeçalhos, negrito, itálico, listas e tabelas)
- **⚡ Suporte a Streaming**: Respostas exibidas token a token quando `config={'stream': True}` está ativo
- **🎯 Comandos Integrados**: 5 comandos úteis (`/help`, `/metrics`, `/configs`, `/tools`, `/clear`) e comandos de saída (`exit`/`quit`)
- **🔧 Indicadores de Status**: Exibe `🤖 AI is thinking...` durante chamadas e processamento
- **📊 Métricas da Sessão**: Visualize a tabela de métricas acumuladas via `/metrics`

______________________________________________________________________

## 📋 Comandos Disponíveis

### `/help` - Ajuda

Exibe a lista de comandos disponíveis e instruções de uso.

```
Você: /help
```

**Aliases**: `/help`, `help`

**Exemplo de saída**:

```text
Available Commands:

• /metrics  → Show agent performance metrics and statistics
• /configs  → Display current agent configuration settings
• /tools    → List all available tools and their descriptions
• /clear    → Clear conversation history and start fresh
• /help     → Show this help message

Type 'exit' or 'quit' to close the application.
```

### `/metrics` - Métricas

Mostra estatísticas de performance das interações com o agente em formato tabular:

- Modelo utilizado
- Duração / Latência em segundos
- Tokens de entrada (Prompt), saída (Completion) e total

```
Você: /metrics
```

**Aliases**: `/metrics`, `get_metrics`

**Exemplo de saída**:

```text
## Performance Metrics

| Model | Duration | Tokens (In/Out/Total) |
|-------|----------|-----------------------|
| gpt-4 | 1.25s    | 45 / 105 / 150        |
| gpt-4 | 0.98s    | 110 / 120 / 230       |
```

### `/configs` - Configurações

Mostra as configurações atuais do agente:

- Nome
- Provider e modelo
- Instruções
- Parâmetros extras de configuração
- Ferramentas configuradas na instância
- Histórico com prévia de mensagens e contagem

```
Você: /configs
```

**Aliases**: `/configs`, `get_configs`

**Exemplo de saída**:

```text
## Agent Configuration

**provider:** openai
**model:** gpt-4
**name:** None
**instructions:** None
**config:** {}
**tools:** None
**history:** 2 messages in history

  - **user:** Olá!
  - **assistant:** Olá! Como posso ajudar você hoje?

**history_max_size:** 10
```

> 💡 **Nota**: `/configs` exibe as ferramentas **configuradas na instância atual** (`tools: None` por padrão). Se você instanciar o agente com `tools=['currentdate']`, elas serão listadas ali. Para consultar o **catálogo de ferramentas disponíveis no ambiente**, utilize o comando `/tools`.

### `/tools` - Ferramentas

Lista todas as ferramentas disponíveis no ambiente (sistema e customizadas) com suas descrições.

```
Você: /tools
```

**Aliases**: `/tools`, `get_tools`

**Exemplo de saída (Instalação básica):**

```text
## Available Tools

**currentdate**
Get the current date and/or time in a specific timezone. Essential for answering 'What time is it?' or 'What day is it?' questions.
```

**Exemplo de saída (Com o extra `[file-tools]` instalado):**

```text
## Available Tools

**currentdate**
Get the current date and/or time in a specific timezone. Essential for answering 'What time is it?' or 'What day is it?' questions.

**readlocalfile**
Use this tool to read local files from the system. Supports text files (txt, md, py, etc.), CSV, Excel, PDF and Parquet formats. The tool validates file size in tokens to prevent overload. Input must include the absolute or relative file path and optionally the maximum number of tokens allowed (default: 30000).
```

### `/clear` - Limpar Histórico

Limpa todo o histórico de conversação do agente.

```
Você: /clear
```

**Aliases**: `/clear`, `clear_history`

**Exemplo de saída**:

```text
Chat history cleared successfully!
```

### Chat Normal

Qualquer texto que não seja um comando é enviado como mensagem ao agente.

```
Você: Explique Clean Architecture
```

Se o agente for configurado com `config={'stream': True}`, a resposta é transmitida em tempo real (token a token). Sem a opção de streaming, a resposta completa é renderizada após o término do processamento.

### `exit` / `quit` - Sair

Encerra a aplicação CLI.

```
Você: exit
```

ou

```
Você: quit
```

______________________________________________________________________

## 🎨 Interface e Formatação

### Cores e Destaque

A CLI usa o seguinte esquema de cores ANSI no terminal:

- **Mensagens do Usuário**: Caixa alinhada à direita em Azul (`ColorScheme.BLUE`)
- **Respostas e Indicador de Processamento da IA**: Caixa alinhada à esquerda e texto de thinking em Roxo (`ColorScheme.PURPLE`)
- **Mensagens de Sistema, Menus e Comandos**: Cyan (`ColorScheme.CYAN`)
- **Marcadores de Sucesso**: Verde (`ColorScheme.GREEN`)
- **Avisos e Interrupções de Sessão**: Amarelo (`ColorScheme.YELLOW`)
- **Erros do Sistema**: Vermelho (`ColorScheme.RED`)

### Formatação Markdown no Terminal

O `MarkdownTerminalFormatter` converte elementos Markdown para visualização no terminal (não inclui syntax highlighting de código):

- **Cabeçalhos**: Níveis `#` e `##` em azul com barra de destaque; `###` e `####` em roxo; `#####` e `######` em cyan
- **Negrito**: `**texto**` ou `__texto__` com estilo ANSI bold
- **Itálico**: `*texto*` ou `_texto_` com estilo ANSI italic
- **Listas não-ordenadas**: Marcadores `•` em verde
- **Listas ordenadas**: Setas `→` em azul
- **Tabelas Markdown**: Formatadas automaticamente como pares rótulo-valor ou colunas com separadores
- **Sanitização de texto**: Sanitização automática de caracteres especiais para evitar travamento de renderização

### Indicadores de Status

Durante o processamento inicial e execução de ferramentas:

```text
🤖 AI is thinking...
```

Se o streaming estiver ativo (`config={'stream': True}`), o indicador é limpo assim que o primeiro token chega e os fragmentos de texto fluem na tela.

______________________________________________________________________

## 💡 Exemplos de Uso

### Exemplo 1: Assistente de Programação

```python
from createagents import CreateAgent

code_assistant = CreateAgent(
    provider='openai',
    model='gpt-4',
    name='Code Expert',
    instructions='Você é um especialista em Python. Sempre forneça exemplos.',
    config={'stream': True},  # Habilita streaming no chat
)

# Iniciar CLI interativa
code_assistant.start_cli()
```

**Interação**:

```
Você: Como criar um decorator em Python?
[Resposta em streaming...]

Você: /metrics
[Exibe tabela com estatísticas acumuladas até o momento]

Você: /clear
[Limpa histórico para novo tópico]
```

### Exemplo 2: Agente com Ferramentas

```python
from createagents import CreateAgent

agent_with_tools = CreateAgent(
    provider='openai',
    model='gpt-4',
    tools=['currentdate'],  # 'readlocalfile' requer [file-tools]
)

# Iniciar CLI
agent_with_tools.start_cli()
```

**Interação**:

```
Você: /tools
[Lista ferramentas disponíveis]

Você: Que dia é hoje?
[Agente usa CurrentDateTool automaticamente]
```

### Exemplo 3: Ollama Local

```python
from createagents import CreateAgent

local_agent = CreateAgent(
    provider='ollama', model='llama3.2', name='Assistente Local'
)

# Iniciar CLI
local_agent.start_cli()
```

______________________________________________________________________

## 🔧 Personalização

### Usando a CLI Programaticamente

A CLI é iniciada através do método `start_cli()` da facade `CreateAgent`:

```python
from createagents import CreateAgent

agent = CreateAgent(provider='openai', model='gpt-4')
agent.start_cli()  # Inicia loop interativo
```

Internamente, este método:

1. Importa `ChatCLIApplication` da camada de apresentação
2. Instancia a aplicação CLI com o agente
3. Executa o loop principal

______________________________________________________________________

## 🐛 Troubleshooting

### CLI não inicia

**Problema**: Erro ao chamar `agent.start_cli()`

**Solução**: Certifique-se de que está na versão mais recente:

```bash
pip install --upgrade createagents
```

### Caracteres especiais não aparecem

**Problema**: Emojis ou caracteres Unicode não renderizam

**Solução**: Use um terminal com suporte UTF-8 (Windows Terminal, iTerm2, etc.)

### Streaming muito lento

**Problema**: Tokens aparecem muito devagar

**Solução**:

1. Verifique sua conexão de internet (para OpenAI)
2. Para Ollama, verifique se o modelo está carregado
3. Considere usar um modelo menor/mais rápido

______________________________________________________________________

## 📚 Próximos Passos

- [Guia de Streaming](streaming-guide.md)
- [Arquitetura CLI (Desenvolvedores)](../dev-guide/cli-architecture.md)
- [API Reference](../reference/commands.md)

______________________________________________________________________

**Versão:** 0.2.0 | **Atualização:** 2026-08-25
