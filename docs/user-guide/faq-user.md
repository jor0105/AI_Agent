# FAQ do Usuário

## 1. Por que algumas ferramentas são opcionais?

Para manter o sistema leve. Instale apenas se precisar de leitura de arquivos (PDF, Excel, etc).

## 2. Como sei quais ferramentas estão disponíveis?

Use `agent.get_all_available_tools()` para listar.

## 3. O que acontece se eu tentar usar uma ferramenta não instalada?

Você receberá um erro claro indicando como instalar.

## 4. Posso criar minhas próprias ferramentas?

Sim! Basta estender `BaseTool` e seguir o padrão dos exemplos.

## 5. Como garantir privacidade dos meus dados?

Use modelos locais (Ollama) para que nada saia da sua máquina.

## 6. Como exportar métricas?

Use `agent.export_metrics_json()` ou `agent.export_metrics_prometheus()`.

## 7. Como limpar o histórico?

Chame `agent.clear_history()`.

## 8. Como reportar bugs ou pedir suporte?

Abra uma issue no GitHub ou envie email para estraliotojordan@gmail.com.

## 9. Como atualizar o framework?

Atualize via pip:

```bash
pip install --upgrade createagents
# OU com file-tools
pip install --upgrade createagents[file-tools]
```

## 10. Onde encontrar exemplos avançados?

Veja [Exemplos](examples-user.md) e a documentação avançada.

## 11. Como usar a CLI interativa?

Basta chamar o método `start_cli()` do agente:

```python
from createagents import CreateAgent

agent = CreateAgent(provider="openai", model="gpt-4")
agent.start_cli()  # Inicia CLI interativa
```

ℹ️ [Guia completo da CLI](cli-usage.md)

## 12. Como funciona o streaming?

O método `chat()` retorna um `StreamingResponseDTO` que pode ser:

- **Awaited**: `response_text = await agent.chat("mensagem")`
- **Iterado**: `async for token in await agent.chat("mensagem"): ...`

O streaming é controlado pelo parâmetro `stream` na configuração:

```python
# Habilitar streaming
agent = CreateAgent(provider="openai", model="gpt-4", config={"stream": True})

# Desabilitar streaming
agent = CreateAgent(provider="openai", model="gpt-4", config={"stream": False})
```

ℹ️ [Guia de Streaming](streaming-guide.md)

## 13. Posso desabilitar o streaming?

Sim! Configure `stream: False` ao criar o agente:

```python
agent = CreateAgent(
    provider="openai",
    model="gpt-4",
    config={"stream": False}  # Desabilita streaming
)

# Resposta completa sem streaming token-por-token
response = await agent.chat("mensagem")
print(response)
```

## 14. Quais comandos estão disponíveis na CLI?

- `/help` - Ajuda
- `/metrics` - Métricas de performance
- `/configs` - Configurações do agente
- `/tools` - Listar ferramentas
- `/clear` - Limpar histórico
- `exit` ou `quit` - Sair

## 15. Como contribuir com o projeto?

Veja o [guia de contribuição](../dev-guide/contribute.md).
