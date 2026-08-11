# EVALS

## Trigger evals

Deve acionar:

- "cria uma change OpenSpec para essa feature"
- "/opsx:continue deploy"
- "sincroniza delta specs dessa change"
- "verifica essa implementação antes de arquivar"
- "quero fazer `/opsx:ff` para ficar apply-ready"
- "me mostra como rodar o onboard do OPSX"

Não deve acionar:

- "plano simples sem OpenSpec"
- "essa skill está fraca"
- "bug de CSS"
- "define a arquitetura dessa feature"
- "preciso melhorar essa proposal comercial"

## Workflow evals

### Cenário 1: `continue` sem nome de change

**Entrada:** "/opsx:continue"

- [ ] consulta `openspec list --json`
- [ ] pede seleção explícita da change
- [ ] usa `openspec status --change "<name>" --json`
- [ ] cria um único artefato `ready`
- [ ] mostra o próximo passo desbloqueado

### Cenário 2: `apply` sem nome de change

**Entrada:** "/opsx:apply"

- [ ] descreve `apply` como exceção de seleção
- [ ] pode inferir ou auto-selecionar somente quando seguro
- [ ] anuncia a change escolhida e como sobrescrever
- [ ] lê `openspec instructions apply --change "<name>" --json`
- [ ] para corretamente em `blocked`, `all_done` ou blocker real

### Cenário 3: `sync` com delta specs

**Entrada:** "sincroniza os delta specs da change deploy"

- [ ] lê delta spec e main spec
- [ ] preserva conteúdo não tocado pelo delta
- [ ] trata `ADDED`, `MODIFIED`, `REMOVED` e `RENAMED`
- [ ] resume capabilities e requisitos alterados

### Cenário 4: `archive` com delta specs e tasks incompletas

**Entrada:** "/opsx:archive deploy"

- [ ] checa `openspec status --change "deploy" --json`
- [ ] conta tasks completas e incompletas
- [ ] avalia sync antes do `mv`
- [ ] mostra warnings quando houver tasks ou artifacts incompletos
- [ ] preserva a possibilidade de arquivar com confirmação do usuário

### Cenário 5: near-miss de governança de skill

**Entrada:** "essa skill está fraca"

- [ ] não roteia para OpenSpec/OPSX
- [ ] indica `skill-governance` como caminho correto

### Cenário 6: near-miss de planning genérico

**Entrada:** "plano simples sem openspec"

- [ ] não roteia para OpenSpec/OPSX
- [ ] não sugere `archive`, `sync` ou `apply`
- [ ] encaminha para planning genérico

### Cenário 7: `new` / `ff` com preflight spec check

**Entrada:** "/opsx:new nova-feature"

- [ ] executa a checagem preflight de especificações ativas e un-synced
- [ ] alerta caso existam changes concluídas com delta specs pendentes de sync
- [ ] informa caso existam delta specs ativos em andamento
- [ ] prossegue com o scaffold da change após a verificação
