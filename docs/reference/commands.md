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

```markdown
## Available Commands

- **/help** - Display available commands and system information
- **/metrics** - View performance and usage metrics
- **/configs** - Display current agent configurations
- **/tools** - View available agent tools
- **/clear** - Clear current conversation history
- **exit/quit** - Exit the interactive chat CLI
```

______________________________________________________________________

### `/metrics` - Métricas de Performance

**Descrição**: Mostra estatísticas detalhadas de todas as chamadas realizadas em tabela Markdown.

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
**tools:** ['currentdate', 'readlocalfile']
**history:** 2 messages in history
  - **user**: Olá
  - **assistant**: Olá! Como posso ajudar?
**history_max_size:** 10
```

**Informações Exibidas**:

- Nome do agente
- Provider e modelo
- Instruções do sistema
- Parâmetros de configuração (temperature, max_tokens, etc.)
- Ferramentas disponíveis
- Resumo do histórico e mensagens
- Tamanho máximo do histórico

______________________________________________________________________

### `/tools` - Ferramentas Disponíveis

**Descrição**: Lista todas as ferramentas que o agente pode usar.

**Aliases**: `/tools`, `get_tools`

**Uso**:

```
Você: /tools
```

**Saída**:

```markdown
## Available Tools

**currentdate**
Get the current date and/or time in a specific timezone. Essential for answering 'What time is it?' or 'What day is it?' questions.

**readlocalfile**
Use this tool to read local files from the system. Supports text files (txt, md, py, etc.), CSV, Excel, PDF and Parquet formats.
```

**Informações Exibidas**:

- Nome da ferramenta em destaque
- Descrição completa da ferramenta

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

```
✨ [Resposta em streaming]

Clean Architecture é um padrão de design de software que separa...
[texto continua em tempo real]
```

**Comportamento**:

- Processa entrada com streaming em tempo real
- Executa ferramentas automaticamente se necessário
- Mantém contexto com histórico de conversação
- Adiciona mensagem ao histórico

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

```
👋 Até logo! Obrigado por usar CreateAgents AI.
```

**Efeito**:

- Encerra o loop da CLI
- Finaliza programa gracefully
- Não salva histórico (sessão é temporária)

______________________________________________________________________

## 🎨 Formatação e Interface

### Cores

Comandos usam esquema de cores profissional:

- **Prompts**: Cyan
- **Respostas**: Verde
- **Sistema**: Amarelo
- **Erros**: Vermelho
- **Comandos**: Magenta

### Indicadores

Durante processamento:

```
⏳ Processando...
✨ [Agente está digitando...]
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
Streaming Response
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

**Versão:** 0.1.3 | **Atualização:** 01/12/2025
