# Workflow Evals

## Cenario 1 - cobertura proporcional

Entrada: mudanca de negocio com risco medio e cobertura parcial existente.

Assertions:

- [ ] identifica comportamento protegido
- [ ] escolhe unit/integration/e2e com justificativa curta
- [ ] define fixtures e mocks necessarios
- [ ] inclui pelo menos um teste negativo quando ha risco de permissao ou estado
- [ ] aponta risco residual ou gate manual quando nao ha execucao possivel

## Cenario 2 - E2E excessivo

Entrada: owner quer adicionar e2e para tudo por inseguranca, sem evidencia de risco.

Assertions:

- [ ] evita E2E amplo por padrao
- [ ] recomenda testes mais baratos quando cobrem o mesmo contrato
- [ ] preserva E2E apenas para wiring, fluxo real ou regressao de navegador

## Cenario 3 - teste de seguranca

Entrada: usuario A nao pode acessar dados do usuario B.

Assertions:

- [ ] cria dois principals e recursos distintos
- [ ] assert verifica bloqueio e ausencia de payload protegido
- [ ] nao mocka o controle que precisa ser provado
- [ ] menciona comando de validacao ou motivo de bloqueio
