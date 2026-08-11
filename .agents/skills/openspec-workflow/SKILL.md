---
name: openspec-workflow
description: >
  Use para workflows OpenSpec/OPSX e mudanças que precisam de artefatos formais.
  Ative quando o usuário citar OpenSpec, OPSX, `/opsx:new`, `/opsx:continue`,
  `/opsx:apply`, `/opsx:verify`, `/opsx:sync`, `/opsx:archive`, `/opsx:ff`,
  `/opsx:bulk-archive`, `/opsx:explore`, `/opsx:onboard`, "cria uma change",
  "faz proposal/design/tasks", "valida spec" ou "sincroniza specs". Também use
  para refactors grandes, multi-fase ou com contrato duradouro. Não use para
  plano simples em `.md`, bug isolado, revisão/criação de skill ou refactor
  delimitado sem necessidade de rastreabilidade formal.
---

# OpenSpec Workflow

## Contrato

- `.agents/workflows/` e seus espelhos são a fonte canônica do lifecycle OPSX. Esta skill existe para roteamento e guardrails, não para duplicar o workflow inteiro.
- O formato ativo padrão de uma change é `openspec/changes/<name>/` com `proposal.md`, `specs/<capability>/spec.md`, `design.md`, `tasks.md` e, quando existir, `.openspec.yaml`.
- Arquivos soltos como `openspec/changes/*.md` devem ser tratados como artefatos legados ou especiais deste repositório, não como o modelo principal do workflow ativo.
- Quando o schema, o próximo artefato ou a ordem de execução não estiverem óbvios, consulte `openspec status --change "<name>" --json` e `openspec instructions <artifact-or-action> --change "<name>" --json` antes de orientar o usuário.

## Roteamento

| Intenção do usuário | Workflow canônico | Primeira ação |
|---|---|---|
| Criar uma nova change, iniciar OPSX, pedir `/opsx:new` | `.agents/workflows/opsx-new.prompt.md` | Executar preflight spec check, criar a change, mostrar o primeiro artefato `ready` e parar antes de gerar artefatos |
| Continuar uma change, criar `proposal.md`, `design.md`, `tasks.md` ou o próximo artefato | `.agents/workflows/opsx-continue.prompt.md` | Se o nome da change não vier no pedido, selecionar explicitamente a change e criar um único artefato `ready` |
| Fast-forward, gerar artefatos até ficar apply-ready, pedir `/opsx:ff` | `.agents/workflows/opsx-ff.prompt.md` | Executar preflight spec check, criar a change, respeitar o schema escolhido e avançar até satisfazer `apply.requires` |
| Implementar tarefas de uma change, pedir `/opsx:apply` | `.agents/workflows/opsx-apply.prompt.md` | Ler `status` e `instructions apply`; `apply` é a única exceção que pode inferir ou auto-selecionar a change quando isso for seguro |
| Verificar implementação antes de arquivar, pedir `/opsx:verify` | `.agents/workflows/opsx-verify.prompt.md` | Selecionar explicitamente a change e comparar implementação com tarefas, specs, cenários e decisões de design |
| Sincronizar delta specs com `openspec/specs`, pedir `/opsx:sync` | `.agents/workflows/opsx-sync.prompt.md` | Selecionar explicitamente a change, ler delta spec e main spec, e mesclar preservando conteúdo intocado |
| Arquivar uma change, pedir `/opsx:archive` | `.agents/workflows/opsx-archive.prompt.md` | Selecionar explicitamente a change, avaliar sync antes do `mv` e só então arquivar |
| Arquivar várias changes, pedir `/opsx:bulk-archive` | `.agents/workflows/opsx-bulk-archive.prompt.md` | Selecionar changes explicitamente, resolver conflitos de specs e arquivar em lote |
| Explorar ideias, trade-offs ou contexto de uma change, pedir `/opsx:explore` | `.agents/workflows/opsx-explore.prompt.md` | Investigar e pensar; não implementar nem inferir `apply`, `sync` ou `archive` |
| Aprender o fluxo completo em modo guiado, pedir `/opsx:onboard` | `.agents/workflows/opsx-onboard.prompt.md` | Rodar o onboarding completo, começando pelo preflight do OpenSpec |

## Guardrails

- Nunca instrua o agente a aplicar código a partir de um arquivo flat em `openspec/changes/*.md`; esse não é o modelo ativo principal.
- Não assuma `proposal -> specs -> design -> tasks` fora de um schema confirmado como `spec-driven`; para outros schemas, use o output do CLI como fonte de verdade.
- `new` e `ff` devem sempre executar o *Preflight Spec Consistency Check* para garantir que a proposta seja desenhada contra `openspec/specs/` atualizadas e avisar sobre delta specs ativos em andamento.
- `continue`, `sync`, `archive` e `verify` devem pedir seleção explícita da change quando o nome não vier no pedido. `apply` é a única exceção que pode inferir ou auto-selecionar quando isso for seguro, mas deve anunciar a escolha e como sobrescrevê-la.
- `continue` cria exatamente um artefato `ready` por invocação.
- `sync` deve ler delta spec e main spec antes de editar, preservar cenários e requisitos não tocados, e ser idempotente.
- `verify` deve comparar a implementação com todos os artefatos disponíveis da change, não apenas com a checklist de tarefas.
- `archive` deve avaliar artifacts, tasks e estado de sync antes de mover a change para `archive/`.
- Ao editar qualquer `opsx-*.prompt.md` em `.agents/workflows/`, atualize os espelhos correspondentes em `.github/prompts/` e `.opencode/commands/` no mesmo diff, preferencialmente com `python3 .agents/scripts/sync-workflows.py`.

## Procedimento

1. Classifique se o pedido e OpenSpec explicito ou um refactor complexo que precisa de artifact formal, rastreabilidade e lifecycle de change.
2. Se for um refactor delimitado que cabe em um unico plano `.md`, nao use esta skill; encaminhe para `plan-writing`.
3. Se for OpenSpec ou refactor complexo, mapeie a intencao do usuario para o workflow canonico correto em `.agents/workflows/opsx-*.prompt.md`.
4. Consulte o CLI do OpenSpec quando o schema, a change selecionada ou o proximo artefato nao estiverem obvios.
5. Oriente ou execute apenas o workflow correspondente, preservando os guardrails e sem misturar `continue`, `apply`, `sync`, `verify` ou `archive`.

## Exemplos

### Caso positivo

**Entrada:** "sincroniza os delta specs dessa change OpenSpec"
**Saída esperada:** Roteia para `opsx-sync`, exige seleção explícita da change se o nome não vier no pedido e preserva conteúdo não tocado do main spec.

### Caso positivo

**Entrada:** "/opsx:apply deploy"
**Saída esperada:** Roteia para `opsx-apply`, lê `openspec status` e `openspec instructions apply`, e implementa apenas as tasks pendentes da change `deploy`.

### Caso positivo

**Entrada:** "Preciso refatorar auth, permissões e onboarding em varias fases, com proposal, design, tasks e verificação rastreável antes de aplicar."
**Saída esperada:** Tratar como refactor complexo, abrir o workflow OpenSpec apropriado e produzir ou continuar os artifacts formais da change antes da implementação.

### Caso negativo

**Entrada:** "Monte um plano em checklist para refatorar um service isolado e ajustar os testes desse modulo."
**Por quê não:** Isso cabe em um plano direto e delimitado em `.md`; use `plan-writing`, nao `openspec-workflow`.

### Caso negativo

**Entrada:** "essa skill está fraca"
**Por quê não:** Isso é trabalho de governança ou autoria de skill; use `skill-governance`.

### Caso negativo

**Entrada:** "bug de CSS"
**Por quê não:** Não há workflow OpenSpec explícito nem lifecycle OPSX no pedido.

### Caso negativo

**Entrada:** "redesenha a arquitetura dessa feature"
**Por quê não:** Isso é arquitetura ou brainstorming, não roteamento OpenSpec.

## Evals de trigger

Deve acionar:

- "cria uma change OpenSpec"
- "/opsx:continue deploy"
- "sincroniza delta specs da minha change"
- "verifica essa implementação antes de arquivar"
- "quero fazer fast-forward de uma change OPSX"

Não deve acionar:

- "plano simples sem openspec"
- "essa skill está fraca"
- "bug de CSS"
- "define a arquitetura dessa feature"
- "me ajuda a escrever uma proposal comercial"

## Evals de workflow

Detalhe completo em `references/EVALS.md`.

### Cenário 1: `continue` sem nome de change

**Entrada:** "/opsx:continue"

- [ ] consulta `openspec list --json`
- [ ] pede seleção explícita da change
- [ ] cria no máximo um artefato `ready`

### Cenário 2: `apply` sem nome de change

**Entrada:** "/opsx:apply"

- [ ] documenta que `apply` pode inferir ou auto-selecionar quando seguro
- [ ] anuncia a change escolhida e como sobrescrever a seleção
- [ ] para se `state` for `blocked` ou `all_done`

## Referências

Leia apenas o arquivo necessário para o pedido atual:

| Situação | Arquivo |
|---|---|
| Confirmar roteamento comando -> workflow, inclusive exceções de seleção | `references/COMMAND_MAP.md` |
| Relembrar guardrails operacionais e diferenças entre `apply` e os outros comandos | `references/GUARDRAILS.md` |
| Revisar trigger evals e workflow evals detalhados | `references/EVALS.md` |

## Scripts

- `scripts/check_opsx_alignment.sh`: valida que os workflows OPSX citados por esta skill existem, que os espelhos em `.github/prompts/` e `.opencode/commands/` estão sincronizados e que o texto local não reintroduziu o padrão legado proibido.
