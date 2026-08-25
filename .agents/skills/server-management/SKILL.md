---
name: server-management
description: >-
  Use para gerenciamento de servidores e runtimes locais/produção: processos,
  portas, health checks, workers, logs estruturados, monitoramento e scaling.
  Ative quando o usuário perguntar "servidor não sobe", "configura workers",
  "healthcheck", "PM2/systemd/docker", "porta ocupada", "como monitoro memória do
  worker?" ou "ajusta graceful shutdown". Não use para código de rotas e
  contratos de API (`api-patterns`), modelagem de banco (`database-design`) ou
  provisionamento amplo de nuvem/infraestrutura.
---

# Server Management

## Gestão de Processo

### Process Managers

| Ferramenta      | Quando usar                                                         |
| --------------- | ------------------------------------------------------------------- |
| **systemd**     | Linux nativo, serviços de longa duração, restart automático no boot |
| **supervisord** | Múltiplos processos, controle granular, logs centralizados          |
| **PM2**         | Node.js, cluster mode, hot reload                                   |
| **Docker**      | Isolamento, portabilidade, orchestração com Compose/Kubernetes      |

**Regra:** Qualquer processo de produção precisa de restart automático em falha. Nunca subir processo em background sem supervisor.

### Graceful Shutdown

```python
# Python — capturar SIGTERM para cleanup antes de encerrar
import signal, sys


def shutdown_handler(sig, frame):
    # Finalizar conexões abertas, flush de buffers, etc.
    logger.info('shutting down gracefully')
    sys.exit(0)


signal.signal(signal.SIGTERM, shutdown_handler)
signal.signal(signal.SIGINT, shutdown_handler)
```

______________________________________________________________________

## Workers e Concorrência

| Tipo de trabalho           | Estratégia                                           |
| -------------------------- | ---------------------------------------------------- |
| I/O bound (HTTP, DB)       | Async ou thread pool — muitos workers, pouca CPU     |
| CPU bound (ML, compressão) | Process pool — workers = núcleos disponíveis         |
| Mixed                      | Separar em serviços distintos se o volume justificar |

**Regra de worker count para Uvicorn/Gunicorn:**

```bash
# Fórmula base: (2 * núcleos) + 1
# Para servidor com 2 núcleos: 5 workers
uvicorn app:app --workers 5
```

______________________________________________________________________

## Health Checks

Todo serviço precisa de pelo menos dois endpoints:

```
GET /health        → liveness — processo está vivo? (retorna 200 se sim)
GET /health/ready  → readiness — pode receber tráfego? (verifica DB, deps)
```

```python
@app.get('/health')
async def liveness():
    return {'status': 'ok'}


@app.get('/health/ready')
async def readiness(db: DB = Depends(get_db)):
    try:
        await db.ping()
        return {'status': 'ready'}
    except Exception:
        raise HTTPException(status_code=503, detail='not ready')
```

**Liveness vs Readiness:**

- Liveness falha → reiniciar o processo
- Readiness falha → parar de enviar tráfego, mas não reiniciar

______________________________________________________________________

## Monitoramento

### Logs Estruturados

```python
import structlog

log = structlog.get_logger()

# Sempre logar com contexto — nunca strings brutas
log.info('request_completed', path='/api/items', status=200, duration_ms=45)
log.error('db_query_failed', query='SELECT...', error=str(e), user_id=user.id)
```

**Regra:** Nunca logar secrets, tokens, PII ou payloads completos de request. Estruture campos para que sejam filtráveis.

### Métricas Essenciais

| Métrica              | O que mede                        |
| -------------------- | --------------------------------- |
| Request rate         | Volume de tráfego por segundo     |
| Error rate           | % de respostas 5xx                |
| Latência p50/p95/p99 | Distribuição de tempo de resposta |
| Saturação            | CPU, memória, conexões de DB      |

______________________________________________________________________

## Scaling — Decisões

| Quando escalar verticalmente                 | Quando escalar horizontalmente              |
| -------------------------------------------- | ------------------------------------------- |
| O gargalo é CPU ou memória em uma instância  | O gargalo é throughput de requests          |
| Scaling rápido necessário                    | Disponibilidade e redundância são críticos  |
| Estado local é necessário (cache em memória) | Stateless e sem dependência de estado local |

**Regra:** Escale horizontalmente por padrão para novos serviços. Escale verticalmente apenas quando o bottleneck é comprovadamente de recurso, não de código.

______________________________________________________________________

## Checklist de Decisão

- [ ] O processo tem supervisor com restart automático?
- [ ] Graceful shutdown está implementado (SIGTERM handled)?
- [ ] Health checks de liveness e readiness existem?
- [ ] Logs são estruturados e sem dados sensíveis?
- [ ] O número de workers é proporcional ao tipo de trabalho (I/O vs CPU)?
- [ ] Scaling decision é baseada em métrica real, não em suposição?

## Procedimento

1. Identifique a topologia atual antes de mudar qualquer processo: comando de entrada, porta, worker model, healthcheck, logs e supervisor.
2. Inspecione primeiro o estado operacional com `status`, portas abertas e logs recentes; não troque configuração sem evidência do sintoma.
3. Ajuste concorrência, restart policy, monitoramento ou preview local com o menor blast radius possível.
4. Valide start, stop, status e healthcheck da superfície alterada para garantir que a mudança é operável, não só teoricamente correta.

## Scripts

- `scripts/auto_preview.py`: gerencia preview local start/stop/status.
- `scripts/session_manager.py`: inspeciona e gerencia sessões locais de servidor.

## Exemplos

### Caso positivo

**Entrada:** Usuário precisa configurar processo, healthcheck, workers, logs ou preview local.
**Saída esperada:** Orientar processo operacional com segurança, monitoramento, concorrência e rollback local quando aplicável.

### Caso negativo

**Entrada:** Usuário pede schema de banco.
**Por quê não:** Use `database-design`; schema, tipos, ownership ou migration nao sao problema operacional de servidor.

## Evals de trigger

Deve acionar:

- "configura healthcheck e workers"
- "processo local não sobe na porta"
- "como configuro o PM2 para reiniciar o processo?"
- "ajusta o graceful shutdown para SIGTERM"
- "quantos workers do uvicorn devo colocar?"

Não deve acionar:

- "desenha schema"
- "component React re-render"
- "como faço a rota de autenticação da API?"
- "audita vulnerabilidade de IDOR"
