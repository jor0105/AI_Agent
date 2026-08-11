# COMMAND MAP

Use este mapa quando o pedido já estiver claramente dentro de OpenSpec/OPSX e você precisar escolher o workflow sem reabrir todos os prompts.

| Comando / intenção | Workflow canônico | Regra de seleção da change | Fonte de verdade do schema | Condição de parada |
|---|---|---|---|---|
| `/opsx:new` ou "cria uma change" | `.agents/workflows/opsx-new.prompt.md` | Não há seleção prévia; executa preflight spec check, valida/derive o nome da nova change | Default schema, salvo pedido explícito de outro schema | Para depois de mostrar o primeiro artefato `ready` |
| `/opsx:continue` ou "cria a próxima proposal/design/tasks" | `.agents/workflows/opsx-continue.prompt.md` | Sempre seleção explícita se o nome não vier no pedido | `openspec status --change "<name>" --json` e `openspec instructions <artifact-id> --change "<name>" --json` | Para após criar um único artefato `ready` |
| `/opsx:ff` ou "gera tudo até apply-ready" | `.agents/workflows/opsx-ff.prompt.md` | Nova change; executa preflight spec check; se o nome já existir, confirmar continuidade | Default schema ou schema explicitado pelo usuário | Para quando `apply.requires` estiver satisfeito |
| `/opsx:apply` ou "implementa as tasks da change" | `.agents/workflows/opsx-apply.prompt.md` | Exceção: pode inferir da conversa ou auto-selecionar se houver uma única change ativa segura; caso contrário, seleção explícita | `openspec status --change "<name>" --json` e `openspec instructions apply --change "<name>" --json` | Para se todas as tasks acabarem, surgir blocker, ou o usuário interromper |
| `/opsx:verify` ou "verifica antes de arquivar" | `.agents/workflows/opsx-verify.prompt.md` | Sempre seleção explícita se o nome não vier no pedido | `openspec status --change "<name>" --json` e `openspec instructions apply --change "<name>" --json` | Para após emitir o relatório de verificação |
| `/opsx:sync` ou "sincroniza delta specs" | `.agents/workflows/opsx-sync.prompt.md` | Sempre seleção explícita se o nome não vier no pedido | `openspec/changes/<name>/specs/*/spec.md` mais `openspec/specs/<capability>/spec.md` | Para após resumir os merges realizados |
| `/opsx:archive` ou "arquiva a change" | `.agents/workflows/opsx-archive.prompt.md` | Sempre seleção explícita se o nome não vier no pedido | `openspec status --change "<name>" --json` mais leitura de `tasks.md` e delta specs | Para após arquivar ou parar por conflito/decisão do usuário |
| `/opsx:bulk-archive` | `.agents/workflows/opsx-bulk-archive.prompt.md` | Sempre multi-seleção explícita; nunca auto-selecionar | `openspec list --json` e `openspec status --change "<name>" --json` por change | Para após processar todas as changes confirmadas |
| `/opsx:explore` ou "explora essa ideia/change" | `.agents/workflows/opsx-explore.prompt.md` | Use o nome da change apenas como contexto, não como autorização para aplicar ou arquivar | `openspec list --json` e artefatos da change, quando relevantes | Não há saída fixa; é modo de pensamento |
| `/opsx:onboard` | `.agents/workflows/opsx-onboard.prompt.md` | Não seleciona change existente; escolhe uma tarefa real e abre uma nova change durante a aula | Preflight via `openspec status --json`, depois o schema default salvo pedido contrário | Para se OpenSpec não estiver inicializado ou quando o ciclo guiado terminar |

## Notas rápidas

- O layout ativo principal é diretório por change: `openspec/changes/<name>/`.
- Não trate arquivos soltos `openspec/changes/*.md` como default operacional.
- Quando o schema não for `spec-driven`, o CLI manda mais que a memória.
