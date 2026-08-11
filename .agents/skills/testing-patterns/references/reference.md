# Testing Strategy Reference

Use this reference to choose test level, fixtures, mocks, and assertions.

## Heuristicas

- Escolha o menor teste que prova o comportamento mudado.
- Use mocks para isolamento de dependencias externas, nao para esconder logica ruim.
- Para seguranca, comece pelo teste negativo que reproduz o vetor original.
- Prove o controle no limite correto: middleware para auth, repository/RLS para tenant, serializer para erro/log.
- Um teste de fix deve falhar antes da remediacao e passar depois; se isso nao for possivel, declare o gate manual.

## Testes negativos de seguranca

| Vetor | Caso minimo |
| --- | --- |
| Usuario errado | User B tenta acessar recurso, sessao, stream ou trace de user A. |
| Tenant errado | Workspace B tenta ler ou mutar dado de workspace A. |
| Sessao expirada | Token expirado ou logout invalida bootstrap, stream e chamada subsequente. |
| Token ausente | Rota protegida rejeita antes de buscar dados ou chamar boundary externa. |
| API key invalida | `X-API-Key` invalida, revogada ou wrong-scope retorna erro sanitizado. |
| Log sem segredo | Erro com token, API key ou provider payload nao aparece em log/audit/error response. |
| Bypass original | O vetor reportado e uma variante adjacente continuam bloqueados. |

## Criterios de validacao

- Nomeie o comportamento protegido no teste, nao apenas a funcao.
- Use fixtures pequenas com dois usuarios/tenants quando o risco for isolamento.
- Verifique ausencia de payload sensivel em resposta, log ou audit artifact quando o vetor envolver segredo.
- Evite snapshots amplos para seguranca; asserts explicitos sao mais resistentes.
- Nao conte "teste passou" se o comando rodou no caminho errado, sem tests descobertos ou com skip inesperado.

## Limites

- Esta skill desenha estrategia de testes; execucao de gates pertence a `lint-and-validate`.
- Use `webapp-testing` quando a evidencia depender de navegador real ou Playwright.
