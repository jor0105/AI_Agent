# FAQ do Usuário

## 1. Por que algumas ferramentas são opcionais?

Para manter o sistema leve. Instale apenas se precisar de leitura de arquivos (PDF, Excel, etc).

## 2. Como sei quais ferramentas estão disponíveis?

Use `agent.get_all_available_tools()` para listar.

## 3. O que acontece se eu tentar usar uma ferramenta não instalada?

Você receberá um erro claro indicando a instalação: `pip install 'createagents[file-tools]'`.

## 4. Posso criar minhas próprias ferramentas?

Sim! Basta estender `BaseTool` e seguir o padrão dos exemplos.

## 5. Como garantir privacidade dos meus dados?

Use modelos locais com o provedor Ollama executando em `localhost` (ou na sua rede privada). Quando o servidor Ollama está local, as requisições não saem da sua máquina para APIs na nuvem. Vale lembrar que se você configurar a variável `OLLAMA_HOST` para um endereço remoto, as chamadas serão roteadas para aquele servidor específico.

## 6. Como exportar métricas?

Use `agent.export_metrics_json()` ou `agent.export_metrics_prometheus()`.

## 7. Como limpar o histórico?

Chame `agent.clear_history()`.

## 8. Como reportar bugs ou pedir suporte?

Para dúvidas gerais e suporte, envie email para `estraliotojordan@gmail.com`. Para vulnerabilidades de segurança, consulte a política em `SECURITY.md`.

## 9. Como atualizar o framework?

Atualize via pip:

```bash
pip install --upgrade createagents
# OU com file-tools
pip install --upgrade 'createagents[file-tools]'
```

## 10. Onde encontrar exemplos avançados?

Veja [Exemplos](examples-user.md) e a documentação avançada.

## 11. Como usar a CLI interativa?

Basta chamar o método `start_cli()` do agente:

```python
from createagents import CreateAgent

agent = CreateAgent(provider='openai', model='YOUR_MODEL')
agent.start_cli()  # Inicia CLI interativa
```

ℹ️ [Guia completo da CLI](cli-usage.md)

## 12. Como funciona o streaming?

O comportamento do método `chat()` depende do parâmetro `stream` em `config`:

- **Com streaming (`config={"stream": True}`)**: O método retorna um `StreamingResponseDTO`. Você pode:
  - **Iterar token a token**: `async for token in response:`
  - **Aguardar resposta completa**: `texto_completo = await response`
- **Sem streaming (`stream=False`, padrão)**: O método retorna diretamente uma string (`str`) com a resposta completa.

Exemplo de configuração:

```python
from createagents import CreateAgent

# Habilitar streaming
agent_stream = CreateAgent(
    provider='openai', model='YOUR_MODEL', config={'stream': True}
)

# Desabilitar streaming (padrão)
agent_sync = CreateAgent(
    provider='openai', model='YOUR_MODEL', config={'stream': False}
)
```

ℹ️ [Guia de Streaming](streaming-guide.md)

## 13. Posso desabilitar o streaming?

Sim! Por padrão o streaming já é desativado (`stream: False`), mas você também pode defini-lo explicitamente:

```python
import asyncio
from createagents import CreateAgent


async def main():
    agent = CreateAgent(
        provider='openai',
        model='YOUR_MODEL',
        config={'stream': False},  # Desabilita streaming
    )

    # Resposta direta em string (str)
    response = await agent.chat('mensagem')
    print(response)


asyncio.run(main())
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
