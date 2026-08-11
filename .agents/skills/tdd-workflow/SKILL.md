---
name: tdd-workflow
description: >
  Use para Test-Driven Development e regressão antes da correção. Ative quando o
  usuário pedir "faz com TDD", "escreve o teste falhando primeiro", "cobre essa
  regressão antes de corrigir", "quero RED-GREEN-REFACTOR", "protege esse
  refactor com teste" ou "esse teste é tautológico?". Cobre acceptance criteria,
  RED/GREEN/REFACTOR e teste que falha sem o fix. Não use para apenas rodar
  suíte existente, desenhar estratégia ampla de testes ou E2E de navegador sem
  ciclo TDD explícito.
---

# TDD Workflow



## Fundamentos

- **A Armadilha do Teste Tautológico:** Nunca escreva um teste que verifica se o código faz exatamente o que a linha de código diz. Teste o *Comportamento* e o *Contrato* (ex: Dado A, a saída é B), e não a implementação interna.
- **Isolamento e Mocks:** Se um teste unitário precisa de 5 mocks diferentes de banco de dados, a arquitetura está acoplada demais. TDD serve para forçar você a escrever funções puras e separação de dependências.
- **Regressão Primeiro:** Ao corrigir um bug, é proibido alterar o código-fonte antes de escrever um teste que reproduza a falha atual. O teste deve quebrar no erro relatado. Só então você altera a implementação.

## Procedimento
Quando ancorado ao TDD Workflow, siga RIGOROSAMENTE este ciclo iterativo:

1. **Fase RED (Obrigatória):**
   - Escreva o teste que define o novo comportamento ou a regressão do bug.
   - Use `run_command` para rodar o teste (ex: `npm run test` ou `pytest`).
   - Você deve ver o teste falhar. Se ele passar de primeira, seu teste é inútil ou a feature já existe.
2. **Fase GREEN:**
   - Escreva o *mínimo* de código possível no código de produção para fazer o teste passar. Não otimize. Não faça over-engineering.
   - Rode os testes novamente. Eles devem passar.
3. **Fase REFACTOR:**
   - Agora, com a rede de segurança ativada, limpe o código. Remova duplicações, extraia métodos, melhore os nomes das variáveis.
   - O teste deve continuar passando a cada salvamento. Se quebrar, reverta imediatamente (`git checkout` ou desfaça a mudança).

## Exemplos

### Caso positivo
**Entrada:** Usuário quer corrigir bug ou implementar comportamento com teste primeiro.
**Saída esperada:** Escrever teste que falha, implementar mínimo, refatorar mantendo o teste como guarda real.

### Caso negativo
**Entrada:** Usuário pede só rodar a suíte existente.
**Por quê não:** Use `lint-and-validate`; não há ciclo red-green-refactor.

## Evals de trigger

Deve acionar:
- "faz TDD para esse bug"
- "escreve teste falhando antes da correção"

Não deve acionar:
- "roda testes existentes"
- "planeja arquitetura"
