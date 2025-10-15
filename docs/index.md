# AI Agent Creator

Sistema modular e profissional para criação de agentes de IA com suporte a múltiplos provedores.


## 🚀 Quick Start

```python
from src import AIAgent

# Criar agente
agent = AIAgent(
    model="gpt-4",
    name="Assistente",
    instructions="Você é um assistente útil."
)

# Conversar
response = agent.chat("Olá!")
print(response)
```

## 📦 Instalação

```bash
# Clonar repositório
git clone https://github.com/jor0105/AI_Agent.git
cd AI_Agent

# Instalar dependências
pip install -r requirements.txt

# Configurar API key
echo "OPENAI_API_KEY=sua-chave" > .env
```

## 📚 Documentação

- [Instalação](guia/instalacao.md) - Configure seu ambiente
- [Uso Básico](guia/uso-basico.md) - Aprenda a usar
- [Exemplos](guia/exemplos.md) - Casos de uso práticos
- [Arquitetura](arquitetura.md) - Entenda a estrutura
- [API](api.md) - Referência completa

## 🏗️ Arquitetura

O projeto segue **Clean Architecture** com separação clara de responsabilidades:

```
Presentation → Application → Domain ← Infrastructure
```

Saiba mais em [Arquitetura](arquitetura.md).

## 📄 Licença

MIT License - veja [LICENSE](https://github.com/jor0105/AI_Agent/blob/develop/LICENSE)
