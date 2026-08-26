# Referência de Comandos CLI

Referência completa de todos os comandos disponíveis na CLI interativa do CreateAgents AI.

______________________________________________________________________

## 📋 Visão Geral

A CLI oferece **7 comandos integrados** para controle total do agente:

| Comando     | Aliases                   | Descrição                         |
| ----------- | ------------------------- | --------------------------------- |
| `/help`     | `/help`, `help`           | Exibe ajuda e lista de comandos   |
| `/metrics`  | `/metrics`, `get_metrics` | Mostra métricas de performance    |
| `/configs`  | `/configs`, `get_configs` | Exibe configurações do agente     |
| `/tools`    | `/tools`, `get_tools`     | Lista ferramentas disponíveis     |
| `/clear`    | `/clear`, `clear_history` | Limpa histórico de conversação    |
| **Chat**    | (qualquer texto)          | Envia mensagem ao agente (padrão) |
| `exit/quit` | `exit`, `quit`            | Encerra a aplicação               |

______________________________________________________________________

## 🔧 Comandos Detalhados

### `/help` - Ajuda

**Descrição**: Exibe lista de comandos disponíveis e suas descrições.

**Aliases**: `/help`, `help`

**Uso**:

```
Você: /help
```

**Saída**:

```text
Available Commands:

• /metrics  → Show agent performance metrics and statistics
• /configs  → Display current agent configuration settings
• /tools    → List all available tools and their descriptions
• /clear    → Clear conversation history and start fresh
• /help     → Show this help message

Type 'exit' or 'quit' to close the application.
```

______________________________________________________________________

### `/metrics` - Métricas de Performance

**Descrição**: Mostra a tabela Markdown de métricas acumuladas até o momento da consulta (duração e tokens de cada turno).

**Aliases**: `/metrics`, `get_metrics`

**Uso**:

```
Você: /metrics
```

**Saída**:

```markdown
## Performance Metrics

| Model | Duration | Tokens (In/Out/Total) |
|-------|----------|-----------------------|
| gpt-4 | 1.23s | 100 / 150 / 250 |
| gpt-4 | 0.98s | 80 / 100 / 180 |
```

**Informações Exibidas**:

- Modelo usado
- Duração/latência da chamada (em segundos)
- Tokens consumidos: Prompt (In) / Completion (Out) / Total

______________________________________________________________________

### `/configs` - Configurações do Agente

**Descrição**: Exibe todas as configurações atuais do agente formatadas em Markdown.

**Aliases**: `/configs`, `get_configs`

**Uso**:

```
Você: /configs
```

**Saída**:

```markdown
## Agent Configuration

**provider:** openai
**model:** gpt-4
**name:** Code Assistant
**instructions:** Você é um especialista em Python.
**config:** {'temperature': 0.7, 'max_tokens': 2000}
**tools:** None
**history:** 2 messages in history
  - **user**: Olá
  - **assistant**: Olá! Como posso ajudar?
**history_max_size:** 10
```

> **Nota:** Caso ferramentas tenham sido passadas na criação do agente (`tools=['currentdate']`), a chave `tools` listará seus nomes. Ferramentas opcionais (como `readlocalfile`) dependem da instalação do extra `[file-tools]`.

**Informações Exibidas**:

- Nome do agente
- Provider e modelo
- Instruções do sistema
- Parâmetros de configuração (temperature, max_tokens, etc.)
- Ferramentas ativas configuradas na instância do agente (`tools`)
- Resumo do histórico e mensagens
- Tamanho máximo do histórico

______________________________________________________________________

### `/tools` - Catálogo de Ferramentas Disponíveis

**Descrição**: Executa `agent.get_all_available_tools()` e lista o catálogo de ferramentas disponíveis no ambiente para esta instância (ferramentas nativas do sistema somadas a quaisquer ferramentas customizadas associadas). Note que `ReadLocalFileTool` é condicional à instalação do extra `[file-tools]`. Para consultar as ferramentas ativas na instância atual, utilize o comando `/configs`.

**Aliases**: `/tools`, `get_tools`

**Uso**:

```
Você: /tools
```

**Saída (Instalação básica):**

```markdown
## Available Tools

**currentdate**
Get the current date and/or time in a specific timezone. Essential for answering 'What time is it?' or 'What day is it?' questions.
```

**Saída (Com o extra `[file-tools]` instalado):**

```markdown
## Available Tools

**currentdate**
Get the current date and/or time in a specific timezone. Essential for answering 'What time is it?' or 'What day is it?' questions.

**readlocalfile**
Use this tool to read local files from the system. Supports text files (txt, md, py, etc.), CSV, Excel, PDF and Parquet formats. The tool validates file size in tokens to prevent overload. Input must include the absolute or relative file path and optionally the maximum number of tokens allowed (default: 30000).
```

**Informações Exibidas**:

- Nome da ferramenta em negrito
- Descrição completa da ferramenta cadastrada no catálogo

______________________________________________________________________

### `/clear` - Limpar Histórico

**Descrição**: Remove todo o histórico de conversação e inicia uma nova sessão limpa.

**Aliases**: `/clear`, `clear_history`

**Uso**:

```

Você: /clear

```

**Saída**:

```

Chat history cleared successfully!

```

**Efeito**:

- Remove todas as mensagens do histórico
- Preserva configurações e ferramentas do agente
- Próxima mensagem iniciará um novo contexto limpo

**Quando Usar**:

- Mudar completamente de assunto
- Resetar contexto após erro
- Liberar memória em conversas longas

______________________________________________________________________

### Chat (Comando Padrão)

**Descrição**: Envia mensagem ao agente de IA. Este é o comando padrão - qualquer texto que não seja um comando especial é enviado ao agente.

**Uso**:

```

Você: Explique o que é Clean Architecture

```

**Saída**:

```text
Clean Architecture é um padrão de arquitetura de software que separa...
```

*(Com `config={'stream': True}`, a resposta é exibida progressivamente em tempo real; sem essa configuração, a resposta completa é renderizada após a finalização).*

**Comportamento**:

- Processa entrada via `CreateAgent.chat()` (com streaming se configurado)
- Executa ferramentas automaticamente se o modelo solicitar
- Mantém contexto no histórico de conversação
- Adiciona o turno da conversa ao histórico após a resposta

______________________________________________________________________

### `exit` / `quit` - Sair

**Descrição**: Encerra a aplicação CLI.

**Aliases**: `exit`, `quit`

**Uso**:

```
Você: exit
```

ou

```
Você: quit
```

**Saída**:

```text
👋 Goodbye! Thanks for using AI Chat System.
```

**Efeito**:

- Encerra o loop da CLI
- Finaliza programa gracefully
- Não salva histórico (sessão é temporária)

______________________________________________________________________

## 🎨 Formatação e Interface

### Cores

A interface utiliza o seguinte esquema de cores ANSI:

- **Usuário**: Azul (`ColorScheme.BLUE`)
- **Respostas e Indicador de Processamento da IA**: Roxo (`ColorScheme.PURPLE`)
- **Mensagens de Sistema, Menus e Comandos**: Cyan (`ColorScheme.CYAN`)
- **Sucesso**: Verde (`ColorScheme.GREEN`)
- **Avisos e Interrupções**: Amarelo (`ColorScheme.YELLOW`)
- **Erros**: Vermelho (`ColorScheme.RED`)

### Indicadores

Durante o processamento e chamadas de ferramentas:

```text
🤖 AI is thinking...
```

______________________________________________________________________

## 🔄 Fluxo de Comandos

```
User Input
  ↓
CommandRegistry.find_handler()
  ↓
¿É comando especial? → Sim → Handler específico
  ↓                         (/help, /metrics, etc.)
  Não
  ↓
ChatCommandHandler (padrão)
  ↓
Streaming Response (ou resposta completa)
```

______________________________________________________________________

## 💡 Exemplos de Uso

### Fluxo Típico de Sessão

```
# Iniciar CLI
Você: /help
[Vê comandos disponíveis]

Você: /tools
[Verifica ferramentas]

Você: Que dia é hoje?
[Agent usa CurrentDateTool e responde]

Você: /metrics
[Vê estatísticas da chamada]

Você: /configs
[Revisa configurações]

Você: /clear
[Limpa histórico para novo tópico]

Você: Agora vamos falar sobre Python
[Nova conversa]

Você: exit
[Sai da CLI]
```

### Debugging

```bash
Você: [mensagem ao agente]
[Resposta parece estranha]

Você: /configs
[Verificar instruções e parâmetros]

Você: /tools
[Verificar se tool correto está disponível]

Você: /metrics
[Ver latência e tokens para identificar problemas]

Você: /clear
[Resetar contexto e tentar novamente]
```

______________________________________________________________________

## 🐛 Troubleshooting

### Comando não reconhecido

**Problema**: Digitou comando errado

**Solução**: Use `/help` para ver lista correta

### Métricas vazias

**Problema**: `/metrics` não mostra nada

**Solução**: Faça pelo menos uma chamada ao agente antes

### Clear não funciona

**Problema**: Histórico não limpa

**Solução**: Verifique que não há erro de digitação (`/clear`, não `/clean`)

______________________________________________________________________

## 📚 Veja Também

- [Guia de Uso da CLI](../user-guide/cli-usage.md)
- [Arquitetura CLI](../dev-guide/cli-architecture.md)
- [API Reference](api.md)

______________________________________________________________________

**Versão:** 0.2.0 | **Atualização:** 2026-08-25
