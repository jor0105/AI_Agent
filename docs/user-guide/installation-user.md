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
# Opção 1: Usando o módulo venv padrão do Python
python3 -m venv .venv

# Opção 2: Usando uv (caso utilize uv no seu ambiente)
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
pip install 'createagents[file-tools]'
```

> **Nota:** A opção `[file-tools]` adiciona suporte para leitura de arquivos PDF, Excel, CSV e Parquet.

A instalação básica traz `openai`, `ollama`, `python-dotenv`, `defusedxml` e
`rich` — esta última usada pelo CLI interativo (`start_cli()`).

______________________________________________________________________

### 3. Configurar Variáveis de Ambiente

Crie um arquivo `.env` na raiz do seu projeto com as suas credenciais:

```env
OPENAI_API_KEY=sk-proj-sua-chave
```

> **Dica:** Se estiver utilizando o repositório clonado do código-fonte, você pode copiar o arquivo modelo: `cp .env.example .env`.

Todas as variáveis reconhecidas pelo pacote são:

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
| `LOG_FILE_PATH`              | Destino quando `LOG_TO_FILE` está ativo             | `logs/app.log`           |
| `LOG_JSON_FORMAT`            | `true` emite logs em JSON                           | `false`                  |
| `FILE_TOOL_BASE_DIR`         | Diretório ao qual `ReadLocalFileTool` fica restrito | diretório atual          |

______________________________________________________________________

### 4. Testar Instalação

> **Nota:** Substitua `"YOUR_MODEL"` pelo modelo desejado da OpenAI.

```python
import asyncio
from createagents import CreateAgent


async def main():
    agent = CreateAgent(
        provider='openai',
        model='YOUR_MODEL',
        instructions='Você é um assistente útil.',
    )
    response = await agent.chat('Olá! Teste de instalação.')
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

Permite rodar modelos de IA **localmente** (processamento em `localhost` sem custos de API; se `OLLAMA_HOST` for configurado para um servidor remoto, as requisições seguirão para o host apontado).

### Instalar Ollama

- **Linux:** `curl -fsSL https://ollama.com/install.sh | sh` (ou baixe em [ollama.com/download/linux](https://ollama.com/download/linux))
- **macOS:** Baixe o instalador em [ollama.com/download/mac](https://ollama.com/download/mac) (ou execute `brew install ollama`)
- **Windows:** Baixe o instalador oficial em [ollama.com/download/windows](https://ollama.com/download/windows)

### Baixar Modelos

```bash
ollama pull YOUR_OLLAMA_MODEL
ollama list             # Ver modelos disponíveis
```

### Usar no Código

> **Nota:** Substitua `"YOUR_OLLAMA_MODEL"` por um modelo instalado no seu Ollama.

```python
import asyncio
from createagents import CreateAgent


async def main():
    agent = CreateAgent(
        provider='ollama',
        model='YOUR_OLLAMA_MODEL',
        instructions='Você é um assistente local.',
    )
    response = await agent.chat('Explique machine learning')
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

Se persistir, consulte a [FAQ](faq-user.md) ou entre em contato pelo email `estraliotojordan@gmail.com`.

______________________________________________________________________

## 👨‍💻 Instalação para Desenvolvimento (Contribuidores)

Se você deseja **contribuir** com o projeto ou precisa da versão de desenvolvimento:

### 1. Clonar o Repositório

```bash
git clone https://github.com/jordanestralioto/Create-Agents-AI.git
cd Create-Agents-AI
```

### 2. Instalar com uv

```bash
# Instale o uv se necessário
curl -LsSf https://astral.sh/uv/install.sh | sh

# Instalação básica respeitando o lockfile
uv sync --locked

# OU com suporte a file-tools
uv sync --locked --extra file-tools

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
uv sync --locked
uv run --locked --no-sync pre-commit install --install-hooks

# Executar checks manualmente
uv run --locked --no-sync pre-commit run --all-files
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

**Versão:** 0.2.0 | **Atualização:** 2026-08-27
