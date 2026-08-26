# 🤖 Create Agents AI

> Framework Python enterprise para criar agentes de IA inteligentes com arquitetura limpa, múltiplos provedores e ferramentas extensíveis.

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Clean Architecture](https://img.shields.io/badge/Architecture-Clean-brightgreen.svg)](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)

______________________________________________________________________

## 🎯 O que este sistema oferece?

**Create Agents AI** é um framework Python que permite criar agentes conversacionais inteligentes de forma profissional:

✅ **Múltiplos provedores**: OpenAI e Ollama (local) com fácil integração
✅ **Ferramentas extensíveis**: CurrentDateTool e ReadLocalFileTool (PDF, Excel, CSV e Parquet)
✅ **Histórico automático**: Conversas contextualizadas sem esforço
✅ **Métricas integradas**: Monitore performance em JSON ou Prometheus
✅ **Arquitetura limpa**: Código testável, manutenível e escalável seguindo SOLID

______________________________________________________________________

## 🚀 Quick Start

### Instalação

```bash
# Instalação básica via PyPI
pip install createagents

# OU com suporte a leitura de arquivos (PDF, Excel, CSV, Parquet)
pip install createagents[file-tools]
```

### Configuração

```bash
# Copy the variable-name template
cp .env.example .env

# Set OPENAI_API_KEY only in the local environment when using OpenAI.
# Never publish secret values.
export OPENAI_API_KEY
```

OpenAI exige `OPENAI_API_KEY`. Ollama não exige API key, mas exige um servidor
Ollama alcançável; consulte o
[guia de instalação](user-guide/installation-user.md) para a configuração de
cada provider.

### Primeiro Agente em 3 Linhas

```python
import asyncio
from createagents import CreateAgent


async def main():
    agent = CreateAgent(
        provider='openai',
        model='gpt-4',
        instructions='Você é um assistente útil',
    )

    response = await agent.chat('Olá!')
    print(response)


asyncio.run(main())
```

______________________________________________________________________

## ✨ Funcionalidades Principais

### 🤝 Múltiplos Provedores

```python
from createagents import CreateAgent

# OpenAI (GPT-4, GPT-4o, GPT-4o-mini)
agent_openai = CreateAgent(provider='openai', model='gpt-4')

# Ollama (llama3.2, mistral, deepseek - 100% local e privado)
agent_local = CreateAgent(provider='ollama', model='llama3.2')
```

### 🔧 Ferramentas Integradas

Adicione capacidades aos seus agentes com ferramentas prontas:

```python
import asyncio
from createagents import CreateAgent


async def main():
    agent = CreateAgent(
        provider='openai',
        model='gpt-4',
        tools=['currentdate'],  # Para 'readlocalfile', instale: pip install createagents[file-tools]
    )

    # O agente usa automaticamente as ferramentas quando necessário
    response = await agent.chat('Que dia é hoje?')  # Usa CurrentDateTool
    print(response)

    # Verificar ferramentas disponíveis
    all_tools = agent.get_all_available_tools()
    print(f'Total de ferramentas: {len(all_tools)}')

    # Ver apenas ferramentas do sistema
    system_tools = agent.get_system_available_tools()
    for name in system_tools.keys():
        print(f'  • {name}')


asyncio.run(main())
```

**Ferramentas Disponíveis:**

- `currentdate` - Data/hora em qualquer timezone (sempre disponível)
- `readlocalfile` - Lê PDF, Excel, CSV, Parquet, JSON, YAML, TXT (requer
  `pip install createagents[file-tools]`)

**Criar ferramentas customizadas:**

```python
import ast
from createagents import BaseTool, CreateAgent


class CalculatorTool(BaseTool):
    name = 'calculator'
    description = 'Performs mathematical calculations'
    parameters = {
        'type': 'object',
        'properties': {
            'expression': {
                'type': 'string',
                'description': 'Mathematical expression to evaluate',
            }
        },
        'required': ['expression'],
    }

    def execute(self, expression: str) -> str:
        return str(ast.literal_eval(expression))


# Usar ferramenta customizada
agent = CreateAgent(
    provider='openai',
    model='gpt-4',
    tools=['currentdate', CalculatorTool()],  # Sistema + customizada
)

# Ver todas as ferramentas disponíveis (sistema + customizadas)
print(agent.get_all_available_tools().keys())
```

### 💬 Histórico Contextual

```python
import asyncio
from createagents import CreateAgent


async def main():
    agent = CreateAgent(provider='openai', model='gpt-4')

    await agent.chat('Olá!')
    await agent.chat('Qual é a capital do Brasil?')  # Mantém contexto
    await agent.chat('E a população?')  # Usa contexto anterior

    # Ver histórico
    config = agent.get_configs()
    print(f'Histórico: {len(config["history"])} mensagens')

    # Limpar quando necessário
    agent.clear_history()


asyncio.run(main())
```

### 📊 Métricas e Monitoramento

```python
from createagents import CreateAgent

agent = CreateAgent(provider='openai', model='gpt-4')

# Coletar métricas
metrics = agent.get_metrics()

# Exportar em diferentes formatos
agent.export_metrics_json('metrics.json')
agent.export_metrics_prometheus('metrics.prom')
```

### ⚙️ Configurações Personalizadas

```python
from createagents import CreateAgent

agent = CreateAgent(
    provider='openai',
    model='gpt-4',
    instructions='Seja conciso e técnico',
    config={
        'temperature': 0.7,  # Criatividade (0-1)
        'max_tokens': 2000,  # Limite de resposta
    },
    history_max_size=20,  # Tamanho do histórico
)
```

______________________________________________________________________

## 📚 Documentação

### Para Usuários

- **[Instalação](user-guide/installation-user.md)** - Configure seu ambiente passo a passo
- **[Uso Básico](user-guide/basic-usage-user.md)** - Aprenda os fundamentos
- **[Exemplos Práticos](user-guide/examples-user.md)** - Casos de uso reais
- **[FAQ](user-guide/faq-user.md)** - Perguntas frequentes

### Para Desenvolvedores

- **[Arquitetura](dev-guide/architecture-developer.md)** - Clean Architecture e padrões de design
- **[Exemplos Técnicos](dev-guide/technical-examples.md)** - Exemplos avançados
- **[Como Contribuir](dev-guide/contribute.md)** - Guia de contribuição

### Referência

- **[API Reference](reference/api.md)** - Documentação completa da API
- **[Ferramentas](reference/tools.md)** - Guia completo das tools disponíveis
- **[Comandos](reference/commands.md)** - Referência de comandos

______________________________________________________________________

## 🏗️ Por Que Usar Este Framework?

### Para Empresas

- ✅ **Privacidade**: Opção de modelos 100% locais com Ollama
- ✅ **Segurança**: Sanitização automática de dados sensíveis nos logs
- ✅ **Monitoramento**: Métricas em tempo real para produção
- ✅ **Escalabilidade**: Arquitetura preparada para crescimento

### Para Desenvolvedores

- ✅ **Clean Architecture**: Código limpo, testável e manutenível
- ✅ **SOLID**: Fácil de estender com novos provedores e ferramentas
- ✅ **Type hints**: Suporte completo para IDEs
- ✅ **CI/CD**: Quality checks automáticos com GitHub Actions

______________________________________________________________________

## 📊 Arquitetura

O projeto segue **Clean Architecture** e **SOLID principles**:

```
┌────────────────────────────────────────────────────────────┐
│ MAIN                                                        │
│ CreateAgent: src/createagents/main/facade/client.py        │
│ AgentComposer (composition root)                           │
└──────────────────────────────┬─────────────────────────────┘
                               │ compõe e injeta dependências
        ┌──────────────────────┼──────────────────────┐
        │                      │                      │
        ▼                      ▼                      ▼
┌───────────────┐   ┌────────────────┐   ┌────────────────────────┐
│ PRESENTATION  │   │ APPLICATION    │   │ INFRA                   │
│ CLI           │──▶│ Use Cases      │◀──│ Adapters / Factories    │
└───────────────┘   └───────┬────────┘   └────────────────────────┘
                            │ depende de
                            ▼
                    ┌────────────────┐
                    │ DOMAIN         │
                    │ Entities/Rules │
                    └────────────────┘
```

**Benefícios**: Testável, Flexível, Escalável e Manutenível

`CreateAgent` não pertence à camada Presentation: a fachada pública vive em
`src/createagents/main/facade/`, enquanto a CLI vive em
`src/createagents/presentation/cli/`. O composition root é
`src/createagents/main/composers/agent_composer.py`. A aplicação depende apenas
do domínio; infraestrutura e apresentação implementam as portas consumidas
pelos casos de uso.

[Saiba mais sobre a arquitetura →](dev-guide/architecture-developer.md)

______________________________________________________________________

## 🤝 Contribuindo

Quer adicionar um novo provedor ou criar uma ferramenta?

1. Leia o [guia de contribuição](dev-guide/contribute.md).

2. Faça um fork e crie uma branch: `git checkout -b feature/add-provider`

3. Implemente seguindo os padrões existentes.

4. Execute os testes locais seguros:

   ```bash
   uv run --locked --no-sync pytest -m 'not integration and not slow' -ra \
       --cov=src --cov-fail-under=85
   ```

5. Verifique os demais gates descritos no guia.

6. Envie um Pull Request.

[Guia completo de contribuição →](dev-guide/contribute.md)

______________________________________________________________________

## 📞 Suporte

- 📧 **Email**: estraliotojordan@gmail.com
- 🐛 **Bugs**: [GitHub Issues](https://github.com/jordanestralioto/Create-Agents-AI/issues)
- 💬 **Discussões**: [GitHub Discussions](https://github.com/jordanestralioto/Create-Agents-AI/discussions)

______________________________________________________________________

## 📄 Licença

MIT - Use livremente em seus projetos.

______________________________________________________________________

## 👨‍💻 Autor

**Jordan Estralioto**

- GitHub: [@jordanestralioto](https://github.com/jordanestralioto)
- Email: estraliotojordan@gmail.com

______________________________________________________________________

**Versão:** 0.2.0
**Última atualização:** 07/08/2026
**Status:** 🚀 Projeto publicado! Aberto para contribuições e sugestões.
