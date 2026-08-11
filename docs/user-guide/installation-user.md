# Guia de Instalação do Usuário

> Siga este passo a passo para instalar e configurar o **Create Agents AI** com segurança e confiabilidade no seu ambiente.

______________________________________________________________________

## 📝 Pré-requisitos

- **Python 3.12+** ([Download](https://www.python.org/downloads/))
- **pip** (geralmente incluído com Python)

> **Dica:** Recomenda-se usar ambientes virtuais para isolar as dependências do projeto.

______________________________________________________________________

## ⚡ Instalação Rápida

### 1. Criar Ambiente Virtual (Recomendado)

```bash
# Criar ambiente virtual
uv venv

# Ativar ambiente virtual
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate  # Windows
```

### 2. Instalar via PyPI

```bash
# Instalação básica
pip install createagents

# OU com suporte a arquivos (PDF, Excel, CSV, Parquet)
pip install createagents[file-tools]
```

> **Nota:** A opção `[file-tools]` adiciona suporte para leitura de arquivos PDF, Excel, CSV e Parquet.

A instalação básica traz `openai`, `ollama`, `python-dotenv`, `defusedxml` e
`rich` — esta última usada pelo CLI interativo (`start_cli()`).

______________________________________________________________________

### 3. Configurar Variáveis de Ambiente

```bash
cp .env.example .env
# Edite o arquivo .env e adicione sua chave OPENAI_API_KEY
```

Todas as variáveis reconhecidas estão listadas em `.env.example`. Apenas
`OPENAI_API_KEY` é obrigatória, e somente para o provider `openai`; as demais
têm padrão e podem ficar em branco:

| Variável                     | Efeito                                              | Padrão                   |
| ---------------------------- | --------------------------------------------------- | ------------------------ |
| `OPENAI_API_KEY`             | Credencial do provider `openai`                     | — (obrigatória)          |
| `OPENAI_TIMEOUT`             | Timeout por requisição, em segundos                 | `30`                     |
| `OPENAI_MAX_RETRIES`         | Tentativas do SDK da OpenAI                         | `3`                      |
| `OPENAI_MAX_TOOL_ITERATIONS` | Rodadas de tool calling por turno                   | `100`                    |
| `OLLAMA_HOST`                | Endereço do servidor Ollama                         | `http://localhost:11434` |
| `OLLAMA_MAX_RETRIES`         | Tentativas por chamada                              | `3`                      |
| `OLLAMA_MAX_TOOL_ITERATIONS` | Rodadas de tool calling por turno                   | `100`                    |
| `LOG_LEVEL`                  | Nível de log após `LoggingConfig.configure()`       | `INFO`                   |
| `LOG_TO_FILE`                | `true` grava em arquivo rotativo                    | `false`                  |
| `LOG_FILE_PATH`              | Destino quando `LOG_TO_FILE` está ativo             | —                        |
| `LOG_JSON_FORMAT`            | `true` emite logs em JSON                           | `false`                  |
| `FILE_TOOL_BASE_DIR`         | Diretório ao qual `ReadLocalFileTool` fica restrito | diretório atual          |

______________________________________________________________________

### 4. Testar Instalação

```python
import asyncio
from createagents import CreateAgent

async def main():
    agent = CreateAgent(
        provider="openai",
        model="gpt-4",
        instructions="Você é um assistente útil."
    )
    response = await agent.chat("Olá! Teste de instalação.")
    print(response)

asyncio.run(main())
```

Se o código acima rodar sem erros, a instalação está concluída!

______________________________________________________________________

## 🔑 Configuração OpenAI

1. Crie uma conta em [platform.openai.com](https://platform.openai.com)
2. Gere uma nova API Key em **API Keys**
3. Adicione ao arquivo `.env`:

```env
OPENAI_API_KEY=sk-proj-sua-chave
```

> **Atenção:** Nunca compartilhe sua chave em repositórios públicos.

______________________________________________________________________

## 🤖 Configuração Ollama (Opcional)

Permite rodar modelos de IA **localmente** (privacidade total, sem custos de API).

### Instalar Ollama

**Linux:**

```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

**macOS:**

```bash
brew install ollama
```

**Windows:**

Baixe em: [ollama.ai/download/windows](https://ollama.ai/download/windows)

### Baixar Modelos

```bash
ollama pull llama3.2:latest     # Modelo recomendado
ollama pull granite3-dense:latest     # Alternativo
ollama list             # Ver modelos disponíveis
```

### Usar no Código

```python
import asyncio
from createagents import CreateAgent

async def main():
    agent = CreateAgent(
        provider="ollama",
        model="llama3.2",
        instructions="Você é um assistente local."
    )
    response = await agent.chat("Explique machine learning")
    print(response)

asyncio.run(main())
```

> **Dica:** Rode `ollama serve` antes de usar para garantir que o servidor está ativo.

______________________________________________________________________

## 🔒 Segurança e Boas Práticas

- **Nunca** faça commit do arquivo `.env` (já está no `.gitignore`)
- Mantenha suas chaves privadas e rotacione periodicamente
- Use ambientes virtuais para isolar dependências
- Atualize dependências regularmente (`uv lock --upgrade` ou `pip install -U`)

______________________________________________________________________

## 🛠️ Solução de Problemas

### Erros Comuns

- **"OPENAI_API_KEY not found"**: Verifique se o arquivo `.env` está na raiz e a variável está correta, sem espaços ou aspas.
- **"ModuleNotFoundError"**: Ative o ambiente virtual e reinstale as dependências.
- **Ollama não conecta**: Rode `ollama serve` e verifique se o modelo está baixado.
- **Problemas de permissão**: Execute comandos com `sudo` apenas se necessário e nunca para instalar dependências Python no sistema global.

### Dicas de Diagnóstico

- Use `uv run python --version` ou `python --version` para checar a versão ativa.
- Use `uv tree` ou `pip list` para listar dependências instaladas.
- Consulte os logs de erro completos para identificar problemas específicos.

Se persistir, consulte a [FAQ](faq-user.md) ou abra uma issue no [GitHub](https://github.com/jor0105/Create-Agents-AI/issues).

______________________________________________________________________

## 👨‍💻 Instalação para Desenvolvimento (Contribuidores)

Se você deseja **contribuir** com o projeto ou precisa da versão de desenvolvimento:

### 1. Clonar o Repositório

```bash
git clone https://github.com/jor0105/Create-Agents-AI.git
cd Create-Agents-AI
```

### 2. Instalar com uv

```bash
# Instale o uv se necessário
curl -LsSf https://astral.sh/uv/install.sh | sh

# Instalação básica
uv sync

# OU com suporte a file-tools
uv sync --extra file-tools

# Ativar ambiente virtual
source .venv/bin/activate
```

### 3. Configurar Ambiente de Desenvolvimento

```bash
# Copiar arquivo de exemplo
cp .env.example .env

# Editar e adicionar sua chave
# OPENAI_API_KEY=sk-proj-sua-chave
```

### 4. Instalar Pre-commit Hooks

```bash
# Instalar hooks de qualidade de código
uv run pre-commit install --install-hooks

# Executar checks manualmente
uv run pre-commit run --all-files
```

📖 **Mais informações:** [Guia de Contribuição](../dev-guide/contribute.md)

______________________________________________________________________

## 🚀 Próximos Passos

- [Uso Básico](basic-usage-user.md)
- [Exemplos](examples-user.md)
- [FAQ](faq-user.md)
- [Referência de Ferramentas](../reference/tools.md)
- [API Reference](../reference/api.md)

______________________________________________________________________

**Versão:** 0.2.0 | **Atualização:** 07/08/2026
