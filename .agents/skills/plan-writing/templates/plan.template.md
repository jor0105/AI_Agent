# Plan: __PLAN_TITLE__

- Plan Name: `__PLAN_NAME__`
- Date: `__PLAN_DATE__`
- Author: `__PLAN_AUTHOR__`
- Plan File Path: `__PLAN_FILE__`

> [!IMPORTANT]
> A refatoração só poderá ser considerada concluída após a execução e aprovação de todos os checks deste plano, incluindo a Final Phase, sem qualquer erro pendente.

## Objective

Resultado esperado:

Motivo do plano:

## Context Summary

Estado atual observado:

Evidência do repositório já coletada:

Dependências, callers ou integrações relevantes:

## Scope In

Itens explicitamente dentro do escopo:

## Scope Out

Itens explicitamente fora do escopo:

## Constraints

Restrições técnicas, operacionais ou de produto:

## Assumptions / Defaults

Assunções adotadas e por que são seguras:

## Pass 1 - Discovery

Descreva aqui os fatos levantados, os contratos e callers relevantes, e qualquer blocker encontrado durante a descoberta inicial.

## Pass 2 - Critical Review

Descreva aqui a revisão crítica do rascunho: decisões escondidas removidas, riscos reforçados e lacunas que ainda precisaram ser fechadas.

## Pass 3 - Final Refinement

Descreva aqui como o plano foi refinado até ficar decision-complete, com ordem clara de execução e sem depender de julgamentos implícitos do implementador.

## Implementation Checklist

- [ ] Substituir estes placeholders por passos concretos agrupados por comportamento ou subsistema.
- [ ] Explicitar o que muda, o que deve ser preservado e em que ordem executar.
- [ ] Registrar impactos em contratos, callers, entrypoints ou dados quando existirem.
- [ ] Final Phase: listar os arquivos alterados pela implementação.
- [ ] Final Phase: rodar `pre-commit run --files <arquivos alterados>`.
- [ ] Final Phase: rodar todos os testes existentes impactados pela mudança.
- [ ] Final Phase: rodar todos os testes novos criados para a mudança.
- [ ] Final Phase: registrar comando, escopo e resultado no próprio plano.
- [ ] Final Phase: confirmar que nenhum check final ficou pendente ou com erro.

## Public APIs / Interfaces / Types

Descreva aqui as mudanças públicas relevantes. Se não houver, escreva `Nenhuma`.

## Validation Strategy

Descreva aqui os comandos, cenários e critérios que validam cada bloco da implementação. Distingua o que é obrigatório do que é validação adicional por risco.

## Final Phase (Obrigatória)

Arquivos alterados pela implementação:

Comando de pre-commit nos arquivos alterados:

Testes existentes impactados:

Testes novos criados:

Resultado registrado dos checks finais:

Bloqueios remanescentes da fase final:

## Risks / Blockers

Riscos relevantes, dependências externas e blockers reais:

## Next Step

Próximo owner ou próxima ação concreta:

## Completion Rule

Não marque a refatoração como concluída antes de finalizar todos os checks.

A refatoração só poderá ser considerada concluída após a execução e aprovação de todos os checks deste plano, incluindo a Final Phase, sem qualquer erro pendente.
