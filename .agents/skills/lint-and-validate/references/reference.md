# reference.md

## O que esta referencia faz

Esta referencia nao e mais o manual completo do harness.
Ela existe para ajudar a IA e humanos a decidir rapidamente quando usar a skill `lint-and-validate`, o que fazer primeiro e por que esse caminho e o certo.

O guia amplo do runtime fica em [verification-harness.md](../../verification-harness.md).

## Quando usar esta skill

Use `lint-and-validate` quando o trabalho principal for validacao objetiva de um artefato alterado:

- escolher o comando canonico de verificacao sem inventar fluxo local;
- validar diff comum com gates repo-native e `gate-report`;
- validar uma skill contra `skill-governance`;
- validar agents, manifests e o protocolo `review-workflow`.

## Por que usar esta skill

Ela existe para evitar tres erros comuns:

- escolher gates manualmente por intuicao;
- misturar falha de ambiente com falha de codigo;
- encerrar uma entrega sem evidencias reutilizaveis para `review-workflow` ou security.

Em vez disso, a skill separa o problema por entrypoint canonico:

- `uv run python scripts/harness_verify.py --evidence-path ...` ou `pre-commit run --all-files` para diff comum e gates do repo;
- `python3 scripts/validate-skills.py` (ou `--skill <nome>`) para governança e integridade de skills;
- `python3 scripts/validate-agent-protocols.py` para agents, manifests e protocol skills.

## O que fazer na pratica

1. Confirme se o pedido e de validacao, nao de implementacao ou arquitetura.
2. Escolha o entrypoint pelo artefato:
   - diff comum e gates: `pre-commit run --all-files` ou `uv run python scripts/harness_verify.py --evidence-path openspec/changes/<change>/evidence/gate-report.json`
   - skill individual ou todas: `python3 scripts/validate-skills.py [--skill <nome>]`
   - agents/protocolos: `python3 scripts/validate-agent-protocols.py`
3. Execute o comando e confira o exit code e o status de cada gate.
4. Responda com a evidencia terminal resumida.

## O que nao fazer

- Nao substituir `review-workflow` ou `security-engineer`.
- Nao usar autofix amplo como comportamento padrao.
- Nao criar wrapper local se o script oficial do repo ja cobre a necessidade.
- Nao usar `validate-agent-protocols` como se fosse validador geral de todas as skills.

## Perguntas que esta skill responde bem

- "Qual e o menor comando canonico para validar isso?"
- "Essa falha e de codigo ou de ambiente?"
- "Isso e governanca de skill ou protocolo de agents?"

## Atalhos uteis

- Executar todos os gates repo-native:
  `pre-commit run --all-files`
- Produzir evidencia estruturada per-change:
  `uv run python scripts/harness_verify.py --evidence-path openspec/changes/<change>/evidence/gate-report.json`
- Validar uma skill:
  `python3 scripts/validate-skills.py --skill lint-and-validate`
- Validar todas as skills:
  `python3 scripts/validate-skills.py`
- Validar agents e protocol skills:
  `python3 scripts/validate-agent-protocols.py`

## Exemplos e guia amplo

- [examples.md](./examples.md): pedidos concretos e resposta esperada da skill.
- [verification-harness.md](../../verification-harness.md): documentacao do verifier repo-native, contrato de gates e integridade de evidencia.
