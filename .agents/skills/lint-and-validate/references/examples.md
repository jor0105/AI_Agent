# examples.md

## Exemplo 1 - positivo

Pedido: "Alterei código e preciso validar o minimo antes do review."
Esperado: rodar a validação repo-native (`pre-commit run --all-files` ou `uv run python scripts/harness_verify.py`).

## Exemplo 2 - positivo

Pedido: "Gerar evidencia estruturada de gates para a change OpenSpec."
Esperado: usar `uv run python scripts/harness_verify.py --evidence-path openspec/changes/<change>/evidence/gate-report.json`.

## Exemplo 3 - positivo

Pedido: "Uma das validações falhou; resuma o impacto."
Esperado: reportar o gate que falhou, o comando executado, o exit code e o impacto.

## Exemplo 4 - positivo

Pedido: "Quero rodar apenas typecheck e linter."
Esperado: usar os comandos repo-native correspondentes (`uv run ruff check .` e `uv run mypy .` ou hooks do pre-commit).

## Exemplo 5 - positivo

Pedido: "Valide so a skill lint-and-validate contra a governance."
Esperado: usar `python3 scripts/validate-skills.py --skill lint-and-validate`.

## Exemplo 6 - positivo

Pedido: "Confere agents, manifests e protocolo review-workflow."
Esperado: usar `python3 scripts/validate-agent-protocols.py` e deixar claro que isso nao cobre toda skill do repo.

## Exemplo 7 - negativo

Pedido: "Quero desenhar a arquitetura da nova feature."
Esperado: nao acionar `lint-and-validate`; isso e planejamento, nao validacao.

## Exemplo 8 - negativo

Pedido: "Aplique ruff --fix no repo inteiro."
Esperado: nao acionar como fluxo padrao; autofix e mutacao ampla e precisa autorizacao explicita.
