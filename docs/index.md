# 🤖 Create Agents AI

> Framework Python orientado à produção para criar agentes de IA inteligentes com Clean Architecture, múltiplos provedores e ferramentas extensíveis.

> **Status do projeto:** Beta. As APIs e o comportamento podem evoluir à medida que o projeto amadurece.

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
pip install 'createagents[file-tools]'
```

### Configuração

**Instalação via PyPI:**

Crie um arquivo `.env` na raiz do seu projeto:

```env
OPENAI_API_KEY=sk-proj-sua-chave-aqui
```

*(Se estiver utilizando um clone do repositório, você pode copiar o modelo com `cp .env.example .env`).*

> **Nota:** OpenAI exige `OPENAI_API_KEY`. O Ollama não exige API key ao executar em `localhost` (consulte o [guia de instalação](user-guide/installation-user.md) para detalhes de ambiente). Substitua `"YOUR_MODEL"` pelo modelo desejado da OpenAI e `"YOUR_OLLAMA_MODEL"` por um modelo local instalado no Ollama.

### Primeiro Agente em 3 Linhas

```python
import asyncio
from createagents import CreateAgent


async def main():
    agent = CreateAgent(
        provider='openai',
        model='YOUR_MODEL',
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

# OpenAI
agent_openai = CreateAgent(provider='openai', model='YOUR_MODEL')

# Ollama (processamento local em localhost)
agent_local = CreateAgent(provider='ollama', model='YOUR_OLLAMA_MODEL')
```

### 🔧 Ferramentas Integradas

Adicione capacidades aos seus agentes com ferramentas prontas:

```python
import asyncio
from createagents import CreateAgent


async def main():
    agent = CreateAgent(
        provider='openai',
        model='YOUR_MODEL',
        tools=['currentdate'],  # 'readlocalfile' requer [file-tools]
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
  `pip install 'createagents[file-tools]'`)

**Criar ferramentas customizadas:**

```python
from createagents import BaseTool, CreateAgent


class WordCountTool(BaseTool):
    name = 'word_count'
    description = 'Conta o número de palavras em um texto'
    parameters = {
        'type': 'object',
        'properties': {
            'text': {
                'type': 'string',
                'description': 'Texto a ser analisado',
            }
        },
        'required': ['text'],
    }

    def execute(self, text: str) -> str:
        return str(len(text.split()))


# Usar ferramenta customizada
agent = CreateAgent(
    provider='openai',
    model='YOUR_MODEL',
    tools=['currentdate', WordCountTool()],  # Sistema + customizada
)

# Ver todas as ferramentas disponíveis (sistema + customizadas)
print(agent.get_all_available_tools().keys())
```

### 💬 Histórico Contextual

```python
import asyncio
from createagents import CreateAgent


async def main():
    agent = CreateAgent(provider='openai', model='YOUR_MODEL')

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

### 📊 Métricas e Exportação

```python
from createagents import CreateAgent

agent = CreateAgent(provider='openai', model='YOUR_MODEL')

# Coletar métricas
metrics = agent.get_metrics()

# Exportar em diferentes formatos (JSON ou formato Prometheus)
agent.export_metrics_json('metrics.json')
agent.export_metrics_prometheus('metrics.prom')
```

### ⚙️ Configurações Personalizadas

```python
from createagents import CreateAgent

agent = CreateAgent(
    provider='openai',
    model='YOUR_MODEL',
    instructions='Seja conciso e técnico',
    config={
        'temperature': 0.7,  # Faixa permitida: 0.0 a 2.0
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
- **[Uso da CLI](user-guide/cli-usage.md)** - Interface interativa de terminal
- **[Guia de Streaming](user-guide/streaming-guide.md)** - Respostas em tempo real e consumo assíncrono
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

- ✅ **Privacidade**: Opção de modelos locais em localhost com Ollama (sem custos de API e com dados retidos no ambiente local caso `OLLAMA_HOST` não aponte para um host externo)
- ✅ **Segurança**: Sanitização automática de dados sensíveis nos logs
- ✅ **Exportação de Métricas**: Exportação de métricas estruturadas em JSON e Prometheus
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
   uv run --locked --no-sync pytest -m 'not integration and not slow' -ra --cov
   ```

5. Verifique os demais gates descritos no guia.

6. Envie um Pull Request.

[Guia completo de contribuição →](dev-guide/contribute.md)

______________________________________________________________________

## 📞 Suporte

- 📧 **Email**: `estraliotojordan@gmail.com`
- 🔒 **Segurança**: Reporte vulnerabilidades de segurança de forma privada conforme nossa [Política de Segurança](https://github.com/jordanestralioto/Create-Agents-AI/blob/develop/SECURITY.md).

______________________________________________________________________

## 📄 Licença

MIT - Use livremente em seus projetos.

______________________________________________________________________

## 👨‍💻 Autor

**Jordan Estralioto**

- GitHub: [@jordanestralioto](https://github.com/jordanestralioto)
- Email: estraliotojordan@gmail.com

______________________________________________________________________

**Versão:** 0.3.0
**Última atualização:** 2026-08-27
**Status:** 🚀 Projeto publicado! Aberto para contribuições e sugestões.
