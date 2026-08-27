# 🤖 Create Agents AI

<div align="center">

**Framework Python enterprise para criar agentes de IA inteligentes com arquitetura limpa, múltiplos provedores e ferramentas extensíveis.**

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![PyPI version](https://img.shields.io/pypi/v/createagents.svg)](https://pypi.org/project/createagents/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Code style: Ruff](https://img.shields.io/badge/code%20style-Ruff-D7FF64.svg)](https://docs.astral.sh/ruff/)
[![Checked with mypy](https://img.shields.io/badge/mypy-checked-blue)](http://mypy-lang.org/)

[Documentação](docs/index.md) • [Exemplos](#-exemplos-de-uso) • [API Reference](docs/reference/api.md) • [Contribuir](docs/dev-guide/contribute.md)

</div>

______________________________________________________________________

## 🎯 Sobre

**Create Agents AI** é um framework Python modular e extensível para construção de agentes conversacionais inteligentes, seguindo os princípios de **Clean Architecture** e **SOLID**. Projetado para ambientes enterprise, oferece suporte a múltiplos provedores de IA (OpenAI, Ollama), ferramentas extensíveis e métricas integradas.

### Por que usar?

- ✅ **Arquitetura Limpa**: Código testável, manutenível e escalável
- ✅ **Múltiplos Provedores**: OpenAI e Ollama (local e privado quando em localhost)
- ✅ **Ferramentas Extensíveis**: Sistema de tools com suporte a customização
- ✅ **Histórico Contextual**: Gerenciamento automático de conversas
- ✅ **Métricas Integradas**: Monitoramento em JSON e Prometheus
- ✅ **Type Safety**: Suporte completo a type hints
- ✅ **CI/CD Profissional**: Quality checks automáticos com GitHub Actions

______________________________________________________________________

## ✨ Features

### 🤖 Provedores de IA

| Provedor   | Status     |
| ---------- | ---------- |
| **OpenAI** | ✅ Estável |
| **Ollama** | ✅ Estável |

### 🔧 Ferramentas Built-in

| Ferramenta            | Descrição                                    | Instalação                             |
| --------------------- | -------------------------------------------- | -------------------------------------- |
| **CurrentDateTool**   | Data/hora em qualquer timezone               | Padrão                                 |
| **ReadLocalFileTool** | Lê PDF, Excel, CSV, Parquet, JSON, YAML, TXT | `pip install createagents[file-tools]` |

### 📊 Recursos Avançados

- **Histórico Automático**: Gerenciamento de contexto conversacional
- **Métricas de Performance**: Exportação em JSON e Prometheus
- **Sanitização de Logs**: Proteção automática de dados sensíveis
- **Logging Configurável**: Silencioso por padrão, ativável para debug
- **Ferramentas Customizadas**: Interface `BaseTool` para extensões
- **Configuração Flexível**: Temperature, max_tokens, top_p, think mode e mais.

### 📝 Logging

A biblioteca é **silenciosa por padrão** (não emite logs). Para ver logs durante o desenvolvimento:

```python
import logging
from createagents import LoggingConfig

# Ativar logs para debug
LoggingConfig.configure_for_development(level=logging.INFO)
```

📖 [Guia completo de Logging](docs/dev-guide/logging_guide.md)

______________________________________________________________________

## 🚀 Instalação Rápida

### Pré-requisitos

- Python 3.12 ou superior
- pip (geralmente incluído com Python) ou uv

### Instalação via PyPI (Usuários)

```bash
# Instalação básica
pip install createagents

# OU com suporte a leitura de arquivos (PDF, Excel, CSV, Parquet)
pip install createagents[file-tools]
```

#### Configuração para Usuários PyPI

Crie um arquivo `.env` na raiz do seu projeto (ou configure as variáveis no seu ambiente):

```env
OPENAI_API_KEY=sk-proj-sua-chave-aqui
```

*Nota: Para Ollama rodando localmente em `localhost`, nenhuma chave de API é necessária.*

### Instalação para Desenvolvimento (Contribuidores)

Se você deseja contribuir com o projeto a partir do código-fonte:

```bash
# Clone o repositório
git clone https://github.com/jordanestralioto/Create-Agents-AI.git
cd Create-Agents-AI

# Instale com uv respeitando o lockfile
uv sync --locked

# OU com suporte a file-tools
uv sync --locked --extra file-tools

# Configure o ambiente copiando o template do repositório
cp .env.example .env
# Edite .env localmente com a sua chave sem versionar seu valor
```

📖 [Guia completo para contribuidores →](docs/dev-guide/contribute.md)

______________________________________________________________________

## 💡 Quick Start

### Exemplo Básico

```python
import asyncio
from createagents import CreateAgent


async def main():
    # Criar agente
    agent = CreateAgent(
        provider='openai',
        model='gpt-4',
        instructions='Você é um assistente técnico especializado em Python',
    )

    # Conversar
    response = await agent.chat('Como criar uma função recursiva?')
    print(response)


asyncio.run(main())
```

### Com Ferramentas

```python
import asyncio
from createagents import CreateAgent


async def main():
    # Agente com ferramentas
    agent = CreateAgent(
        provider='openai', model='gpt-4', tools=['currentdate']
    )

    # O agente usa ferramentas automaticamente
    response = await agent.chat('Que dia é hoje?')  # Usa CurrentDateTool
    print(response)


asyncio.run(main())
```

### Ollama (Local)

```bash
# Instalar Ollama
curl -fsSL https://ollama.com/install.sh | sh
# Links diretos: Linux (https://ollama.com/download/linux)
# macOS (https://ollama.com/download/mac) ou brew install ollama
# Windows (https://ollama.com/download/windows)

# Baixar modelo e executar
ollama pull llama3.2:latest
ollama serve
```

### Agente Local com Ollama

```python
import asyncio
from createagents import CreateAgent


async def main():
    agent = CreateAgent(
        provider='ollama',
        model='llama3.2',
        instructions='Você é um assistente local',
    )

    response = await agent.chat('Explique Clean Architecture')
    print(response)


asyncio.run(main())
```

______________________________________________________________________

## 📋 Exemplos de Uso

Os exemplos completos foram separados por cenário para manter esta página
curta e fácil de consultar:

- [Exemplos práticos para usuários](docs/user-guide/examples-user.md)
- [API e ferramentas](docs/reference/api.md)
- [Exemplos técnicos para contribuidores](docs/dev-guide/technical-examples.md)

______________________________________________________________________

## 🏗️ Arquitetura

Este projeto segue **Clean Architecture** e **SOLID Principles**:

```
src/
└─ createagents/                         # Pacote principal
    ├─ domain/                            # Regras de negócio
    ├─ application/                       # Casos de uso, DTOs e portas
    ├─ infra/                             # Adapters, factories e configuração
    ├─ main/                              # Facade e composição de dependências
    │   ├─ facade/                        # CreateAgent
    │   └─ composers/                     # AgentComposer
    ├─ presentation/                     # CLI e interface de terminal
    └─ utils/                             # Utilitários compartilhados
```

### Diagrama de Camadas

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

`CreateAgent` não pertence à camada Presentation: a fachada pública vive em
`src/createagents/main/facade/`, enquanto a CLI vive em
`src/createagents/presentation/cli/`. O composition root é
`src/createagents/main/composers/agent_composer.py`. A aplicação depende apenas
do domínio; infraestrutura e apresentação implementam as portas consumidas
pelos casos de uso.

**Benefícios**: Testável, Flexível, Escalável e Manutenível

📖 [Documentação completa da arquitetura](docs/dev-guide/architecture-developer.md)

______________________________________________________________________

- 📖 **Para Usuários**: [Instalação](docs/user-guide/installation-user.md) • [Uso Básico](docs/user-guide/basic-usage-user.md) • [Exemplos Práticos](docs/user-guide/examples-user.md) • [FAQ](docs/user-guide/faq-user.md)
- 🏗️ **Para Desenvolvedores**: [Arquitetura](docs/dev-guide/architecture-developer.md) • [Exemplos Técnicos](docs/dev-guide/technical-examples.md) • [Contribuir](docs/dev-guide/contribute.md)
- 📚 **Referência**: [API Reference](docs/reference/api.md) • [Ferramentas](docs/reference/tools.md) • [Comandos](docs/reference/commands.md)

### Build Local da Documentação

```bash
uv run --locked --no-sync mkdocs serve
# Acesse: http://localhost:8000
```

______________________________________________________________________

## 🔧 Configuração

### Variáveis de Ambiente

No clone do repositório, copie `.env.example` para `.env`. Na instalação via PyPI, configure as variáveis diretamente no seu ambiente ou em um arquivo `.env` local. Nunca inclua valores secretos no código ou no repositório.

```bash
# OpenAI: obrigatório somente quando o provider é "openai".
export OPENAI_API_KEY
```

| Contexto   | Variáveis                                                                              | Comportamento                                                                                  |
| ---------- | -------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------- |
| OpenAI     | `OPENAI_API_KEY`, `OPENAI_TIMEOUT`, `OPENAI_MAX_RETRIES`, `OPENAI_MAX_TOOL_ITERATIONS` | Requer `OPENAI_API_KEY`; as demais controlam timeout, retries e iterações de tools.            |
| Ollama     | `OLLAMA_HOST`, `OLLAMA_MAX_RETRIES`, `OLLAMA_MAX_TOOL_ITERATIONS`                      | Não requer API key, mas requer um servidor Ollama alcançável.                                  |
| Logging    | `LOG_LEVEL`, `LOG_TO_FILE`, `LOG_FILE_PATH`, `LOG_JSON_FORMAT`                         | A biblioteca permanece silenciosa até `LoggingConfig.configure()` ser chamado pelo consumidor. |
| File tools | `FILE_TOOL_BASE_DIR`                                                                   | Restringe o diretório usado pela `ReadLocalFileTool`.                                          |

### Configuração do Modelo

```python
from createagents import CreateAgent

config = {
    'temperature': 0.7,  # Criatividade (0-1)
    'max_tokens': 1000,  # Limite de resposta
    'top_p': 0.9,  # Nucleus sampling
    'think': True,  # Ollama: bool / OpenAI: "low"|"medium"|"high"
}

agent = CreateAgent(
    provider='openai',
    model='gpt-4',
    name='Assistente',
    instructions='Seja conciso',
    config=config,
    history_max_size=20,
)
```

______________________________________________________________________

## 📊 API Reference

A referência completa das assinaturas, métodos, ferramentas e configurações
está em [docs/reference/api.md](docs/reference/api.md).

______________________________________________________________________

## 🤝 Contribuindo

Contribuições são bem-vindas! Siga os passos:

1. **Fork** o repositório

2. **Crie uma branch**: `git checkout -b feature/add-provider`

3. **Implemente** seguindo os padrões existentes

4. **Adicione testes** que comprovem o comportamento, os casos de borda e as
   regressões relevantes

5. **Execute os checks**:

   ```bash
   # Install pre-commit hooks from the locked environment
   uv run --locked --no-sync pre-commit install --install-hooks

   # Run pre-commit hooks
   uv run --locked --no-sync pre-commit run --all-files

   # Run pre-push hooks
   uv run --locked --no-sync pre-commit run --all-files --hook-stage pre-push

   # Run safe local tests (no external APIs)
   uv run --locked --no-sync pytest -m 'not integration and not slow' -ra --cov=src --cov-fail-under=85
   ```

6. **Faça um commit em inglês** usando Conventional Commits, por exemplo
   `feat: add support for provider XYZ`

7. **Atualize a documentação** quando comportamento, contratos ou exemplos
   mudarem

8. **Envie um Pull Request**

### Adicionando um Novo Provedor

1. Crie um novo adapter em `src/createagents/infra/adapters/NomeProvedor/`
2. Implemente a porta `ChatRepository` da aplicação
3. Registre o provider em `src/createagents/infra/factories/chat_adapter_factory.py`
4. Adicione testes espelhando a camada em `tests/infra/adapters/`

Novos handlers da CLI ficam em `src/createagents/presentation/cli/commands/` e
são registrados em
`src/createagents/presentation/cli/application/chat_cli_app.py`, no método
`_setup_commands`.

Exemplo:

```python
from collections.abc import AsyncGenerator
from typing import Any
from createagents.application.interfaces import ChatRepository
from createagents.domain import BaseTool


class MeuAdapter(ChatRepository):
    async def chat(
        self,
        model: str,
        instructions: str | None,
        config: dict[str, Any] | None,
        tools: list[BaseTool] | None,
        history: list[dict[str, str]],
        user_ask: str,
    ) -> str | AsyncGenerator[str, None]:
        # Implementation
        pass
```

📖 [Guia completo de contribuição](docs/dev-guide/contribute.md)

______________________________________________________________________

## 🧪 CI/CD & Workflows

Este projeto tem automação profissional com GitHub Actions:

### Quality Checks (CI)

- **Executa em**: Push/PR para `develop` ou `main`
- **Matrix**: Python 3.12, 3.13, 3.14
- **Checks**:
  - ✅ Lint & Format (Ruff)
  - ✅ Type checking (mypy)
  - ✅ Security (Bandit, gitleaks, pip-audit, zizmor)
  - ✅ Tests com cobertura mínima de 85%
  - ✅ Docstring validation (pydocstyle)

O workflow completo está em
[`.github/workflows/pipeline.yml`](.github/workflows/pipeline.yml).

### Hooks locais

O projeto configura 41 hooks: 37 na etapa `pre-commit`, 3 na etapa `pre-push`
e 1 na etapa `commit-msg` para validar Conventional Commits.

```bash
uv sync --locked
uv run --locked --no-sync pre-commit install --install-hooks
uv run --locked --no-sync pre-commit run --all-files
uv run --locked --no-sync pre-commit run --all-files --hook-stage pre-push
```

Os hooks não sincronizam o ambiente nem reescrevem `uv.lock`; veja a política e o fluxo de atualização deliberada no [guia de contribuição](docs/dev-guide/contribute.md).

______________________________________________________________________

## 📄 Licença

Este projeto está licenciado sob a **MIT License** - veja o arquivo [LICENSE](LICENSE) para detalhes.

______________________________________________________________________

## 📞 Suporte

- 📖 [Documentação Completa](docs/index.md)
- 🐛 [Reportar Bugs](https://github.com/jordanestralioto/Create-Agents-AI/issues)
- 💬 [Discussões](https://github.com/jordanestralioto/Create-Agents-AI/discussions)
- 📧 Email: estraliotojordan@gmail.com

______________________________________________________________________

## 👨‍💻 Autor

**Jordan Estralioto**

- GitHub: [@jordanestralioto](https://github.com/jordanestralioto)
- Email: estraliotojordan@gmail.com

______________________________________________________________________

## 📚 Referências

- [Clean Architecture - Robert C. Martin](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [OpenAI API Documentation](https://platform.openai.com/docs)
- [Ollama Documentation](https://github.com/ollama/ollama)
- [SOLID Principles](https://en.wikipedia.org/wiki/SOLID)

______________________________________________________________________

<div align="center">

**Versão:** 0.2.0 • **Última atualização:** 2026-08-25 • **Status:** 🚀 Projeto publicado!

⭐ Se este projeto foi útil, considere dar uma estrela no GitHub!

</div>
