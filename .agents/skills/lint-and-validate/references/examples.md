# examples.md

## Exemplo 1 - positivo

Pedido: "Alterei código e preciso validar o minimo antes do review."
Esperado: rodar `npm run ai:verify` e usar o `effectiveProfile` resolvido.

## Exemplo 2 - positivo

Pedido: "Persistir gates desta sessao de review."
Esperado: usar `npm run ai:verify -- --session-dir ...` e persistir `gate-report`.

## Exemplo 3 - positivo

Pedido: "Uma das validações falhou; resuma o impacto."
Esperado: reportar `classification`, comando, gate e impacto no handoff.

## Exemplo 4 - positivo

Pedido: "Quero saber antes o que o harness vai rodar."
Esperado: usar `npm run ai:verify -- --dry-run` e explicar `effectiveProfile`, gates e escalacoes.

## Exemplo 5 - positivo

Pedido: "Meu diff nao esta bem refletido no git; valide esse arquivo especifico."
Esperado: usar `npm run ai:verify -- --changed-file src/domain/columns.py`.

## Exemplo 6 - positivo

Pedido: "Preciso anexar uma smoke customizada sem perder os gates normais."
Esperado: usar `npm run ai:verify -- --gate "smoke|Smoke|false|npm run smoke"` e manter defaults.

## Exemplo 7 - positivo

Pedido: "Quero rodar so uma gate customizada nesta sessao."
Esperado: usar `npm run ai:verify -- --skip-defaults --gate "schema|Schema|true|python3 scripts/check_schema.py"`.

## Exemplo 8 - positivo

Pedido: "Valide so a skill lint-and-validate contra a governance."
Esperado: usar `npm run skills:validate -- --skill lint-and-validate`.

## Exemplo 9 - positivo

Pedido: "Confere agents, manifests e protocolo review-workflow."
Esperado: usar `npm run agents:validate-protocols` e deixar claro que isso nao cobre toda skill do repo.

## Exemplo 10 - negativo

Pedido: "Quero desenhar a arquitetura da nova feature."
Esperado: nao acionar `lint-and-validate`; isso e planejamento, nao validacao.

## Exemplo 11 - negativo

Pedido: "Aplique ruff --fix no repo inteiro."
Esperado: nao acionar como fluxo padrao; autofix e mutacao ampla e precisa autorizacao explicita.
