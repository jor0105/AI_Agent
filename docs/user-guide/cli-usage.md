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

- **🎨 Interface Colorida**: Sintaxe highlight e formatação markdown
- **⚡ Streaming em Tempo Real**: Respostas aparecem token por token
- **🎯 Comandos Integrados**: 5 comandos úteis (`/help`, `/metrics`, `/configs`, `/tools`, `/clear`) mais comandos de saída
- **🔧 Indicadores de Status**: Mostra quando o agente está pensando
- **📊 Métricas em Tempo Real**: Visualize performance instantaneamente

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
- Ferramentas configuradas
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
**name:** Assistente
**instructions:** Você é um assistente prestativo
**config:** {'temperature': 0.7}
**tools:** ['currentdate']
**history:** 2 messages in history

  - **user:** Olá!
  - **assistant:** Olá! Como posso ajudar você hoje?

**history_max_size:** 10
```

### `/tools` - Ferramentas

Lista todas as ferramentas disponíveis (sistema e customizadas) com suas descrições.

```
Você: /tools
```

**Aliases**: `/tools`, `get_tools`

**Exemplo de saída**:

```text
## Available Tools

**currentdate**
Get the current date and/or time in a specific timezone. Essential for answering 'What time is it?' or 'What day is it?' questions.

**readlocalfile**
Use this tool to read local files from the system. Supports text files (txt, md, py, etc.), CSV, Excel, PDF and Parquet formats.
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

O agente responderá com streaming em tempo real.

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

A CLI usa um esquema de cores profissional:

- **Prompts**: Cor primária (cyan)
- **Respostas do Agente**: Verde
- **Mensagens do Sistema**: Amarelo
- **Erros**: Vermelho
- **Comandos**: Magenta

### Formatação Markdown

A renderização suporta:

- **Negrito**: `**texto**`
- _Itálico_: `*texto*`
- `Código inline`: `` `código` ``
- Blocos de código com syntax highlighting
- Listas e cabeçalhos

### Indicadores de Status

Durante o processamento:

```
⏳ Processando...
```

Durante streaming:

```
✨ [Agente está digitando...]
```

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
)

# Iniciar CLI interativa
code_assistant.start_cli()
```

**Interação**:

```
Você: Como criar um decorator em Python?
[Resposta em streaming...]

Você: /metrics
[Exibe estatísticas da chamada]

Você: /clear
[Limpa histórico para novo tópico]
```

### Exemplo 2: Agente com Ferramentas

```python
from createagents import CreateAgent

agent_with_tools = CreateAgent(
    provider='openai',
    model='gpt-4',
    tools=['currentdate'],  # Para 'readlocalfile', instale: pip install createagents[file-tools]
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

**Versão:** 0.2.0 | **Atualização:** 07/08/2026
