---
name: lint-and-validate
description: >-
  Use para escolher e executar validações nativas do repositório após alterações.
  Ative quando o usuário pedir "valida", "roda os checks", "garante que não
  quebrou", "roda testes", "passa o lint", "gera gate-report", "confere antes de
  finalizar" ou quando a entrega exigir evidência de terminal. Cobre lint,
  typecheck, testes, verificação nativa e gate-report. Não use para planejar
  estratégia de testes, investigar causa incerta ou validar UI no navegador quando
  a evidência exigir Playwright/screenshot.
---

# Lint And Validate

## Fundamentos

- **Confiança Cega é Falha:** Nunca entregue um código dizendo "Acredito que vai funcionar". Você deve executar lints e testes reais via terminal para comprovar.
- **Cheap First, Evidence Complete:** Comece pelos gates mais baratos de interpretar, mas execute a validação repo-native oficial declarada no repositório (`openspec/handoff.json`, `.pre-commit-config.yaml` ou `AGENTS.md`).
- **Isolamento:** Quando o TypeScript falhar, olhe apenas para o arquivo que você editou e os arquivos que dependem dele. Ignorar erros não relacionados ao escopo a menos que você os tenha causado.

## Procedimento

1. Identifique o artefato que precisa ser validado antes de escolher o comando:
   - diff comum do repositório: comando repo-native declarado em `openspec/handoff.json` (`validationCommand`) ou `pre-commit run --all-files`
   - skills gerais ou específicas: `python3 scripts/validate-skills.py` (ou `python3 scripts/validate-skills.py --skill <nome>`)
   - agents, manifests e protocolo `review-workflow`: `python3 scripts/validate-agent-protocols.py`
2. Execute a suíte de validação e os gates pertinentes à mudança sem pular verificações obrigatórias.
3. Leia o resultado das gates e garanta que todas passaram com código 0. Não trate gate não executada ou skipped como sucesso implícito.
4. Responda com evidência terminal mínima: comando, escopo, status, classificação da falha quando existir e próximo passo. Não declare sucesso sem output correspondente.

## Exemplos

### Caso positivo

**Entrada:** Após mudar frontend e backend, usuário pede validação antes de finalizar.
**Saída esperada:** Executar validação repo-native, resumir evidência e produzir gate-report quando exigido.

### Caso negativo

**Entrada:** Usuário pergunta qual arquitetura escolher antes de código existir.
**Por quê não:** Não há artefato para validar; use planejamento/arquitetura.

## Evals de trigger

Deve acionar:

- "roda validação depois das mudanças"
- "gera gate-report desse PR"
- "quero saber quais gates vão rodar antes"
- "uma gate falhou; resume o impacto"
- "essa mudança pequena precisa de E2E?"

Não deve acionar:

- "qual stack devo usar?"
- "desenha a arquitetura"
- "projete uma migration segura para este schema"
- "revise se este componente está com UX genérica"
- "implemente a feature inteira"
- "corrija automaticamente todos os problemas de lint"

## Evals de workflow

### Cenário 1 - diff comum

Entrada: repositório com `.pre-commit-config.yaml` configurado.

Assertions:

- [ ] escolhe a validação repo-native como entrypoint principal
- [ ] reporta status das gates executadas de forma determinística
- [ ] reporta falhas e saídas de terminal com clareza

### Cenário 2 - validação de skill

Entrada: pedido para validar apenas a skill `lint-and-validate`.

Assertions:

- [ ] usa `python3 scripts/validate-skills.py --skill lint-and-validate`
- [ ] não chama `validate-agent-protocols.py` como se cobrisse toda governança de skills
- [ ] reporta erro estrutural se o `SKILL.md` violar o contrato da `skill-governance`

### Cenário 3 - protocolo de agents

Entrada: pedido para validar agents, manifests e protocolo `review-workflow`.

Assertions:

- [ ] usa `python3 scripts/validate-agent-protocols.py`
- [ ] deixa claro que o escopo é protocolo de agents, não qualquer skill do repo
- [ ] reporta falha estrutural sem declarar sucesso parcial implícito

### Cenário 4 - falha externa

Entrada: comando oficial falha por ausência de ferramenta no ambiente.

Assertions:

- [ ] classifica a falha como ambiente ou `external_failure`
- [ ] não classifica o problema como erro de código sem evidência
- [ ] devolve comando e sintoma mínimo para reproduzir

### Cenário 5 - E2E proporcional

Entrada: mudança de texto em componente interno sem fluxo de navegador afetado.

Assertions:

- [ ] não força E2E sem necessidade quando a mudança é puramente textual ou interna
- [ ] usa os testes repo-native correspondentes
- [ ] deixa explícito se testes adicionais são recomendados

## Scripts

- O executor de verificação (`ai-verify`) pertence ao projeto consumidor:
  ele codifica os gates, caminhos e escalações daquele repositório. Este
  harness publica o contrato que ele precisa satisfazer
  (`schemas/ai-verify.schema.json` e `assets/verification-profiles.json`),
  não o executor.
- `scripts/normalize-skill-metadata.py`: remove metadados extras do frontmatter de skills em lote controlado.
- `scripts/validate-agent-protocols.py`: valida manifests, agents e protocol skills do fluxo de review.
- `scripts/check-max-lines.py`: gate portátil de tamanho de arquivo por
  responsabilidade (produção 400, teste 1000, documentação 500 linhas).
  Selecionar esta skill projeta a ferramenta em
  `.agents/scripts/check-max-lines.py` (via `tools/check-max-lines`); o
  consumidor executa `python .agents/scripts/check-max-lines.py` e adiciona
  o comando ao próprio gate roster — o harness nunca edita a configuração
  de hooks do consumidor. O repositório central usa
  `uv run python scripts/check-max-lines.py`.

## Referências

Leia apenas o arquivo relevante para o tipo de validação em mãos:

| Problema                                             | Arquivo                   |
| ---------------------------------------------------- | ------------------------- |
| Ver exemplos de gate-report e resposta final         | `references/examples.md`  |
| Confirmar contrato operacional do fluxo de validação | `references/reference.md` |
