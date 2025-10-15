# 📦 Instalação

## Requisitos

- Python 3.10+
- pip

## Passo a Passo

### 1. Clonar o Repositório

```bash
git clone https://github.com/jor0105/AI_Agent.git
cd AI_Agent
```

### 2. Criar Ambiente Virtual

```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows
```

### 3. Instalar Dependências

```bash
pip install -r requirements.txt
```

### 4. Configurar Variáveis de Ambiente

Crie um arquivo `.env`:

```bash
# OpenAI
OPENAI_API_KEY=sk-proj-sua-chave-aqui
```

## Provedores de IA

### OpenAI

1. Acesse [platform.openai.com](https://platform.openai.com)
2. Crie uma API key
3. Adicione ao `.env`

### Ollama (Opcional)

Para usar modelos locais:

```bash
# Instalar Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Baixar modelo
ollama pull llama2
```

## Verificar Instalação

```python
from src import AIAgent

agent = AIAgent(
    model="gpt-4",
    name="Test",
    instructions="Teste"
)

print("✅ Instalação OK!")
```

## Problemas Comuns

**Erro: "OPENAI_API_KEY not found"**

- Verifique se criou o arquivo `.env`
- Certifique-se de que a chave está correta

**Erro: "ModuleNotFoundError"**

- Execute: `pip install -r requirements.txt`
