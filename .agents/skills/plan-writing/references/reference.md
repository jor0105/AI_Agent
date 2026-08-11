# reference.md

## Contrato minimo

- Rode `bash .agents/skills/plan-writing/scripts/plan_guard.sh init-plan --task <snake_case_slug> --title "<titulo humano>" --author <agent>` antes de preencher qualquer plano.
- O plano completo vive no arquivo `<task>.md`; o chat fica restrito a resumo curto, caminho do arquivo, fase atual e proxima acao ou blocker.
- As tres passadas sao obrigatorias:
  - `Pass 1 - Discovery`: fatos, escopo e restricoes com evidencia
  - `Pass 2 - Critical Review`: cacar lacunas, riscos e decisoes escondidas
  - `Pass 3 - Final Refinement`: transformar o plano em checklist detalhado e executavel
- Apenas `Implementation Checklist` usa checkboxes. Ele deve cobrir os passos concretos da execucao inteira, inclusive os itens da fase final.
- `Objective`, `Context Summary`, `Scope In`, `Scope Out`, `Constraints`, `Assumptions / Defaults`, `Public APIs / Interfaces / Types`, `Validation Strategy`, `Final Phase (Obrigatória)`, `Risks / Blockers`, `Next Step` e `Completion Rule` devem ser preenchidos como texto descritivo.
- `Public APIs / Interfaces / Types` deve declarar mudancas publicas reais ou `Nenhuma`.
- `Final Phase (Obrigatória)` precisa registrar em texto descritivo os arquivos alterados, o `pre-commit` so neles, os testes existentes impactados, os testes novos criados e o resultado final sem erro pendente.

## Quando bloquear

- Falta evidencia para `Scope In`, `Scope Out`, risco ou validacao.
- O plano ainda exige que o implementador escolha a abordagem principal por conta propria.
- A fase final nao consegue provar que os checks realmente rodaram.
