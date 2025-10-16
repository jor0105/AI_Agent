# 📺 Como os Logs Aparecem - Visual Guide

## 🎬 O Que Você Vê na Prática

---

## Cenário 1: Executando Seu Sistema Normalmente

### **Seu Código:**
```python
# main.py
from src.infra.config.logging_config import LoggingConfig
from src.presentation.agent_controller import AIAgent

LoggingConfig.configure()

agent = AIAgent(
    provider="openai",
    model="gpt-4",
    name="Assistente",
    instructions="Seja útil"
)

response = agent.chat("Olá!")
print(response)
```

### **O Que Você Vê no Terminal:**
```
$ python main.py

2025-10-16 15:30:45,123 - src.infra.adapters.OpenAI.openai_chat_adapter - INFO - OpenAI adapter inicializado (model: gpt-4)
2025-10-16 15:30:45,456 - src.application.use_cases.chat_with_agent - INFO - Executando chat com agente 'Assistente' (modelo: gpt-4)
2025-10-16 15:30:46,789 - src.infra.adapters.OpenAI.openai_chat_adapter - DEBUG - Iniciando chat com modelo gpt-4
2025-10-16 15:30:48,012 - src.application.use_cases.chat_with_agent - INFO - Chat executado com sucesso
2025-10-16 15:30:48,013 - src.application.use_cases.chat_with_agent - DEBUG - Resposta (primeiros 100 chars): Olá! Como posso ajudar você hoje? Estou aqui para responder suas perguntas e fornecer...

Olá! Como posso ajudar você hoje?
```

### **Traduzindo:**
```
[QUANDO] [ONDE NO CÓDIGO] [TIPO] [MENSAGEM]

15:30:45 → Adapter OpenAI    → INFO  → Adaptador iniciado com sucesso
15:30:45 → ChatWithAgent     → INFO  → Iniciando conversa com agente 'Assistente'
15:30:46 → Adapter OpenAI    → DEBUG → Enviando mensagem para API
15:30:48 → ChatWithAgent     → INFO  → Conversa concluída com sucesso
15:30:48 → ChatWithAgent     → DEBUG → Primeiros caracteres da resposta

[SUA RESPOSTA]
```

---

## Cenário 2: Quando Dá Erro

### **Seu Código:**
```python
# Tentando enviar mensagem vazia
response = agent.chat("")  # ❌ Vai dar erro
```

### **O Que Você Vê no Terminal:**
```
$ python main.py

2025-10-16 15:35:12,456 - src.application.use_cases.chat_with_agent - INFO - Executando chat com agente 'Assistente' (modelo: gpt-4)
2025-10-16 15:35:12,457 - src.application.use_cases.chat_with_agent - ERROR - Erro de validação: Mensagem vazia não é permitida
2025-10-16 15:35:12,458 - src.application.use_cases.chat_with_agent - ERROR - Erro de validação durante o chat: Mensagem não pode ser vazia
Traceback (most recent call last):
  File "main.py", line 15, in <module>
    response = agent.chat("")
  File "src/presentation/agent_controller.py", line 78, in chat
    output_dto = self.__chat_use_case.execute(self.__agent, input_dto)
  File "src/application/use_cases/chat_with_agent.py", line 35, in execute
    input_dto.validate()
ValueError: Mensagem não pode ser vazia

❌ ERRO: Mensagem não pode ser vazia
```

### **Traduzindo:**
```
INFO  → Tentou executar chat
ERROR → Detectou erro de validação
ERROR → Explicação do erro + stacktrace completo
        (mostra exatamente onde deu erro no código)

[SUA MENSAGEM DE ERRO]
```

---

## Cenário 3: Logs em Arquivo

### **Seu Código:**
```python
LoggingConfig.configure(
    log_to_file=True,
    log_file_path="logs/app.log"
)
```

### **Arquivo: logs/app.log**
```
2025-10-16 15:40:01,234 - src.infra.adapters.OpenAI.openai_chat_adapter - INFO - OpenAI adapter inicializado (model: gpt-4)
2025-10-16 15:40:01,567 - src.application.use_cases.chat_with_agent - INFO - Executando chat com agente 'Assistente' (modelo: gpt-4)
2025-10-16 15:40:03,890 - src.application.use_cases.chat_with_agent - INFO - Chat executado com sucesso
2025-10-16 15:42:15,123 - src.application.use_cases.chat_with_agent - INFO - Executando chat com agente 'Assistente' (modelo: gpt-4)
2025-10-16 15:42:17,456 - src.application.use_cases.chat_with_agent - ERROR - Erro ao comunicar com OpenAI: Connection timeout
```

### **Como Ver:**
```bash
# Ver todo o arquivo
$ cat logs/app.log

# Ver últimas 20 linhas
$ tail -20 logs/app.log

# Ver logs em tempo real
$ tail -f logs/app.log

# Ver só erros
$ grep ERROR logs/app.log

# Ver logs de hoje
$ grep "2025-10-16" logs/app.log
```

---

## Cenário 4: Dados Sensíveis Protegidos

### **Seu Código:**
```python
# Você acidentalmente tenta logar dados sensíveis
logger.info(f"User: usuario@email.com, Password: senha123")
```

### **O Que É Gravado (AUTOMÁTICO):**
```
2025-10-16 15:45:00,123 - main - INFO - User: [EMAIL_REDACTED], Password[PASSWORD_REDACTED]
```

### **Mais Exemplos:**
```python
# Você tenta logar:
logger.info(f"CPF: 123.456.789-00")
logger.info(f"Cartão: 4532-1234-5678-9010")
logger.info(f"API Key: sk-proj-abc123xyz789")

# O que é gravado:
# CPF: [CPF_REDACTED]
# Cartão: [CREDIT_CARD_REDACTED]
# API Key: [API_KEY_REDACTED]
```

**✅ 100% Automático e Seguro!**

---

## Cenário 5: Diferentes Níveis de Detalhe

### **Nível: ERROR (Menos logs)**
```python
LoggingConfig.configure(level=logging.ERROR)
```

**Terminal:**
```
$ python main.py

2025-10-16 16:00:12,456 - src.application.use_cases.chat_with_agent - ERROR - Erro ao comunicar com API

❌ Só mostra ERROS
```

### **Nível: INFO (Normal)**
```python
LoggingConfig.configure(level=logging.INFO)
```

**Terminal:**
```
$ python main.py

2025-10-16 16:00:45,123 - INFO - Executando chat com agente 'Assistente'
2025-10-16 16:00:48,456 - INFO - Chat executado com sucesso
2025-10-16 16:00:50,789 - ERROR - Erro ao processar

✅ Mostra INFO + WARNING + ERROR
```

### **Nível: DEBUG (Muito detalhe)**
```python
LoggingConfig.configure(level=logging.DEBUG)
```

**Terminal:**
```
$ python main.py

2025-10-16 16:01:01,234 - DEBUG - Adaptador inicializado
2025-10-16 16:01:01,567 - DEBUG - Configurações carregadas: {'temp': 0.7}
2025-10-16 16:01:01,890 - INFO  - Executando chat com agente 'Assistente'
2025-10-16 16:01:02,123 - DEBUG - Mensagem do usuário: Olá...
2025-10-16 16:01:04,456 - DEBUG - Resposta da API: Olá! Como posso...
2025-10-16 16:01:04,789 - INFO  - Chat executado com sucesso

🔍 Mostra TUDO (DEBUG + INFO + WARNING + ERROR)
```

---

## Cenário 6: Rotação de Arquivos

### **Estrutura Automática:**
```
logs/
├── app.log      ← 10MB (HOJE - arquivo atual)
├── app.log.1    ← 10MB (ONTEM)
├── app.log.2    ← 10MB (ANTEONTEM)
├── app.log.3    ← 10MB (3 dias atrás)
├── app.log.4    ← 10MB (4 dias atrás)
└── app.log.5    ← 10MB (5 dias atrás - mais antigo)

Total: 60MB de histórico
```

### **Como Funciona:**
```
1. app.log cresce até 10MB
2. Sistema cria app.log.1 (renomeia o atual)
3. Cria novo app.log vazio
4. Continua logando no novo app.log
5. Quando app.log.5 enche, é deletado
6. Sempre mantém últimos 50-60MB
```

### **Ver Logs Antigos:**
```bash
# Hoje
$ cat logs/app.log

# Ontem
$ cat logs/app.log.1

# Anteontem
$ cat logs/app.log.2

# Todos juntos
$ cat logs/app.log*
```

---

## Cenário 7: Logs JSON (Para Ferramentas)

### **Configuração:**
```python
LoggingConfig.configure(
    json_format=True,
    log_to_file=True
)
```

### **Arquivo: logs/app.log**
```json
{"timestamp": "2025-10-16 16:15:01", "level": "INFO", "logger": "src.application.use_cases.chat_with_agent", "message": "Executando chat com agente 'Assistente'", "module": "chat_with_agent", "function": "execute", "line": 38}
{"timestamp": "2025-10-16 16:15:03", "level": "INFO", "logger": "src.application.use_cases.chat_with_agent", "message": "Chat executado com sucesso", "module": "chat_with_agent", "function": "execute", "line": 62}
{"timestamp": "2025-10-16 16:15:05", "level": "ERROR", "logger": "src.application.use_cases.chat_with_agent", "message": "Erro ao comunicar: timeout", "module": "chat_with_agent", "function": "execute", "line": 89, "exception": "Traceback..."}
```

**✅ Cada linha é um JSON válido**
**✅ Fácil de processar com ferramentas**
**✅ Pode importar no Excel, ELK, Splunk, etc**

---

## 📊 Resumo Visual

### **Linha do Tempo de uma Requisição:**

```
VOCÊ CHAMA:
┌─────────────────────────────────┐
│ response = agent.chat("Olá!")   │
└─────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────┐
│ 15:30:45 INFO - Executando chat com agente             │ ← Log 1
└─────────────────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────┐
│ 15:30:46 DEBUG - Iniciando chat com modelo gpt-4       │ ← Log 2
└─────────────────────────────────────────────────────────┘
              │
              ▼
    [Aguardando API...]
              │
              ▼
┌─────────────────────────────────────────────────────────┐
│ 15:30:48 INFO - Chat executado com sucesso             │ ← Log 3
└─────────────────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────┐
│ RETORNA: "Olá! Como posso ajudar?"                     │
└─────────────────────────────────────────────────────────┘
```

---

## 🎯 Tudo É Automático!

### **Você NÃO precisa:**
- ❌ Adicionar logs manualmente
- ❌ Se preocupar com segurança
- ❌ Gerenciar tamanho de arquivos
- ❌ Proteger dados sensíveis

### **O sistema JÁ faz:**
- ✅ Loga operações importantes
- ✅ Mostra no terminal
- ✅ Salva em arquivo
- ✅ Protege dados sensíveis
- ✅ Rotaciona arquivos
- ✅ Formata logs bonitos

---

## 🚀 Quick Start Visual

```
┌──────────────────────────────────────────────────────────┐
│ 1. CONFIGURE (uma vez no início)                        │
├──────────────────────────────────────────────────────────┤
│ from src.infra.config.logging_config import LoggingConfig│
│ LoggingConfig.configure(log_to_file=True)                │
└──────────────────────────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────┐
│ 2. USE SEU SISTEMA NORMALMENTE                          │
├──────────────────────────────────────────────────────────┤
│ agent = AIAgent(...)                                     │
│ response = agent.chat("Olá!")                            │
└──────────────────────────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────┐
│ 3. LOGS APARECEM AUTOMATICAMENTE                        │
├──────────────────────────────────────────────────────────┤
│ • No terminal (tempo real)                               │
│ • No arquivo logs/app.log                                │
│ • Protegidos e seguros                                   │
└──────────────────────────────────────────────────────────┘
                         │
                         ▼
                  ✅ PRONTO!
```

---

**Versão:** 1.0.0 - Visual Guide
**Para:** Desenvolvedores que querem VER como funciona
**Status:** ✅ 100% Visual e Prático
