---
name: plan-writing
description: >
  Use para transformar uma mudança delimitada em plano executável ou handoff.
  Ative quando o usuário pedir "monta um plano", "quebra em etapas", "faz um
  checklist", "planeja a implementação", "organiza o handoff" ou descrever um
  objetivo já claro que precisa virar passos. Não use para ideação vaga, escolha
  entre opções ainda nebulosa, implementação imediata já autorizada, ou refactor
  amplo com `proposal`, `design`, `tasks` ou OpenSpec; prefira `brainstorming`
  ou `openspec-workflow`.
---

# Plan Writing

## Por que planos falham

- O agent planeja cedo demais e preenche lacunas no chute.
- O plano fica so no chat e se perde quando a execucao comeca.
- A validacao final fica vaga e a implementacao termina sem evidência real.

## Procedimento

1. Antes de escrever o plano, rode `bash .agents/skills/plan-writing/scripts/plan_guard.sh init-plan --task <snake_case_slug> --title "<titulo humano>" --author <agent>`. Isso cria `<task>.md` a partir de `templates/plan.template.md`.
2. Grave o plano completo no arquivo `.md`. No chat, responda apenas com quatro linhas curtas: `Objetivo:`, `Arquivo do plano:`, `Fase atual:`, `Proxima acao:` ou `Blocker:`.
3. Faça a **Pass 1 - Discovery** dentro do arquivo:
   - confirme `Objective`, `Context Summary`, `Scope In`, `Scope Out`, `Constraints` e `Assumptions / Defaults`;
   - registre fatos do repo, callers, contratos e dependencias que realmente sustentam o plano;
   - se faltar evidencia para qualquer campo material, pare e trate isso como blocker explicito.
4. Faça a **Pass 2 - Critical Review** antes de considerar o plano pronto:
   - procure decisoes escondidas, passos sem ordem, riscos omitidos e validacao fraca;
   - revise se algum passo ainda exige julgamento arquitetural do implementador;
   - marque blockers reais em vez de disfarcar incerteza como checklist.
5. Faça a **Pass 3 - Final Refinement** para transformar o rascunho em handoff executavel:
   - deixe `Objective`, `Context Summary`, `Scope In`, `Scope Out`, `Constraints`, `Assumptions / Defaults`, `Public APIs / Interfaces / Types`, `Validation Strategy`, `Risks / Blockers`, `Next Step` e `Completion Rule` como texto descritivo;
   - concentre os checkboxes apenas em `Implementation Checklist`, que deve cobrir os passos concretos da execucao inteira, inclusive a fase final;
   - preencha `Public APIs / Interfaces / Types` com mudancas publicas reais, ou registre `Nenhuma` quando nao houver;
   - deixe `Next Step` claro o bastante para o proximo owner agir sem reabrir planejamento.
6. Preencha `Final Phase (Obrigatória)` no proprio arquivo. Ela so fecha quando o plano exigir e registrar:
   - em texto descritivo, a lista dos arquivos alterados pela implementacao;
   - em texto descritivo, o `pre-commit run --files <arquivos alterados>`;
   - em texto descritivo, todos os testes existentes impactados;
   - em texto descritivo, todos os testes novos criados para a mudanca;
   - em texto descritivo, comando, escopo e resultado de cada check, sem erro pendente.
   - a mensagem fixa `A refatoração só poderá ser considerada concluída após a execução e aprovação de todos os checks deste plano, incluindo a Final Phase, sem qualquer erro pendente.`
7. Nao replique o plano inteiro no chat depois de atualizar o arquivo. Se o ambiente externo exigir um wrapper formal, use-o apenas para resumir o objetivo, o caminho do arquivo e o estado atual.

## Exemplos

### Caso positivo

**Entrada:** "Monte um plano detalhado para refatorar o service de cache do backend e ajustar os testes, mas sem abrir proposal nem design formal."
**Saída esperada:** Rodar `init-plan`, criar um arquivo como `refatorar_service_cache.md`, preencher as tres passadas no arquivo e devolver no chat apenas o resumo curto com caminho do plano e proxima acao.

### Caso positivo

**Entrada:** "Quebre a implementacao dessa feature em checklist detalhado, mas bloqueie se faltar evidencia do codigo atual."
**Saída esperada:** Criar o arquivo do plano, registrar a descoberta, e devolver blocker explicito se `Scope In`, contratos afetados, risco ou validacao dependerem de adivinhacao.

### Caso negativo

**Entrada:** "Nao sei ainda qual abordagem seguir; me ajuda a pensar nas opcoes."
**Por quê não:** Isso ainda e ideacao. Use `brainstorming` antes de `plan-writing`.

### Caso negativo

**Entrada:** "Preciso refatorar auth, workspaces e auditoria em varias fases, com migracao, rollout e proposal/design/tasks rastreaveis."
**Por quê não:** Isso ja ultrapassa um plano direto em `.md`. E um refactor amplo e multi-fase que pede artifact formal de change; use `openspec-workflow`.

### Caso negativo

**Entrada:** "Faz essa correcao pequena no componente agora."
**Por quê não:** O trabalho ja esta suficientemente claro para execucao direta; nao transforme correcao pequena em planejamento desnecessario.

## Evals de trigger

Deve acionar:

- "monte um plano executavel para essa mudanca"
- "quebre a implementacao em checklist detalhado"
- "faca o handoff tecnico dessa feature"
- "planeje a implementacao e grave em arquivo"
- "organize esse refactor em etapas verificaveis"

Não deve acionar:

- "me ajuda a pensar nas opcoes antes de decidir"
- "cria a change do openspec"
- "roda os checks dessa branch"
- "faz essa correcao pequena agora"
- "desenha a arquitetura desse sistema novo sem plano de execucao ainda"

## Evals de workflow

### Cenario 1 - plano nominal com arquivo persistido

**Entrada:** "Planeje a implementacao do refactor do backend e deixe tudo em checklist."

- [ ] roda `plan_guard.sh init-plan` antes de preencher o plano
- [ ] cria `<nome-do-plano>.md` ou outro slug `snake_case` equivalente ao objetivo estabilizado
- [ ] grava o plano completo no arquivo, nao no chat
- [ ] responde no chat com `Objetivo`, `Arquivo do plano`, `Fase atual` e `Proxima acao`

### Cenario 2 - falta de evidencia

**Entrada:** "Quero o plano, mas ainda nao sabemos quais modulos realmente serao afetados."

- [ ] registra a lacuna durante `Pass 1 - Discovery`
- [ ] nao transforma a lacuna em passo generico
- [ ] devolve `Blocker` curto no chat em vez de fingir plano completo

### Cenario 3 - fase final bloqueante

**Entrada:** plano pronto para handoff depois de uma implementacao com arquivos alterados e testes novos.

- [ ] `Implementation Checklist` inclui os passos da fase final
- [ ] `Final Phase (Obrigatória)` registra em texto descritivo o `pre-commit run --files <arquivos alterados>`
- [ ] exige testes existentes impactados e testes novos criados
- [ ] registra comando, escopo e resultado no proprio arquivo
- [ ] impede conclusao se qualquer check final estiver pendente ou falhando

## Scripts

- `scripts/plan_guard.sh`: inicializa o arquivo do plano a partir do template oficial.

## Referências

Leia apenas o arquivo relevante para o momento:

| Situacao | Arquivo |
|---|---|
| Confirmar o contrato minimo do arquivo e das tres passadas | `references/reference.md` |
| Ver exemplos de resposta curta e de `Final Phase` bloqueante | `references/examples.md` |
| Confirmar a estrutura do artefato persistido | `templates/plan.template.md` |
