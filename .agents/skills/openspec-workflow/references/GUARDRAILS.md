# GUARDRAILS

## Guardrails globais

- `.agents/workflows/` é a fonte canônica. A skill roteia e reforça regras; ela não substitui os prompts `OPSX`.
- Use `openspec status` e `openspec instructions` sempre que houver dúvida sobre schema, ordem de artefatos, estados `ready/blocked/done` ou arquivos de contexto.
- Não reintroduza instruções baseadas em arquivos flat em `openspec/changes/*.md` como caminho padrão de execução.
- Sempre que editar um prompt ativo em `.agents/workflows/`, sincronize os espelhos em `.github/prompts/` e `.opencode/commands/`, preferencialmente com `python3 .agents/scripts/sync-workflows.py`.

## Diferença crítica de seleção

- `apply` é a única operação OPSX que pode inferir ou auto-selecionar a change quando isso for seguro.
- `continue`, `sync`, `archive` e `verify` devem pedir seleção explícita se o nome não vier no pedido.
- `bulk-archive` sempre usa multi-seleção explícita.

## Guardrails por comando

### `new` e `ff`

- Executar o *Preflight Spec Consistency Check* antes de scaffoldar a mudança.
- Identificar changes ativas com delta specs e avisar se houver alterações de specs em andamento.
- Recomendar proativamente `/opsx:sync` e `/opsx:archive` caso exista alguma change concluída cujos delta specs não foram mesclados em `openspec/specs/`.

### `continue`

- Crie um único artefato `ready` por invocação.
- Leia dependências antes de escrever o artefato novo.
- Não pule artefatos nem force ordem manual quando o schema indicar outra sequência.

### `apply`

- Leia `openspec instructions apply --change "<name>" --json` antes de implementar.
- Se `state` for `blocked`, não invente trabalho; encaminhe para `continue`.
- Se `state` for `all_done`, pare e sugira `archive`.

### `verify`

- Trate tasks, specs, cenários e design como superfícies de verdade quando existirem.
- Não reduza verificação a "tudo marcado como done".

### `sync`

- Leia delta spec e main spec antes de editar.
- Preserve requisitos e cenários não tocados pelo delta.
- A operação precisa ser idempotente.

### `archive`

- Avalie artifacts, tasks e sync antes do `mv`.
- Quando existirem delta specs, avalie e resuma o sync antes de arquivar.

### `explore`

- Explore, investigue e formalize pensamento.
- Não implemente código de produção nem trate uma menção de change como autorização implícita para `apply`.
