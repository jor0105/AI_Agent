# Trigger Evals

## Deve acionar

### Caso 1

Pedido: "Essa feature precisa de unit, integration ou e2e?"

Assertions:

- [ ] aciona `testing-patterns`
- [ ] escolhe menor nivel confiavel
- [ ] explica trade-off de custo e confianca

### Caso 2

Pedido: "Quais mocks sao aceitaveis para cobrir este servico externo?"

Assertions:

- [ ] aciona `testing-patterns`
- [ ] diferencia boundary externa de logica sob teste
- [ ] nao recomenda mockar regra de negocio central

### Caso 3

Pedido: "Preciso cobrir tenant errado e auth expirada."

Assertions:

- [ ] aciona `testing-patterns`
- [ ] inclui teste negativo de seguranca
- [ ] pede fixtures com dois principals quando houver isolamento

## Nao deve acionar

### Caso 1

Pedido: "Rode a validação repo-native e testes."

Assertions:

- [ ] nao aciona `testing-patterns`
- [ ] usa `lint-and-validate`

### Caso 2

Pedido: "Modele o schema do banco desta feature."

Assertions:

- [ ] nao aciona `testing-patterns`
- [ ] usa `database-design`

### Caso 3

Pedido: "O fluxo ja esta coberto e so preciso reexecutar a suite."

Assertions:

- [ ] nao aciona `testing-patterns`
- [ ] trata como validacao operacional
