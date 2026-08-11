# examples.md

## Exemplo 1 - nominal

Pedido: "Planeje o refactor do service de cache do backend e deixe tudo organizado em checklist."

Arquivo criado: `refatorar_service_cache.md`

Trecho esperado no arquivo:

```md
# Plan: Refatorar service de cache do backend

- Plan Name: `refatorar_service_cache`

## Objective

Resultado esperado:
Separar leitura, invalidacao e telemetria do service de cache sem mudar o contrato externo.

Motivo do plano:
Permitir implementacao segura e review rastreavel sem abrir artifact formal de change.

## Scope In

Refactor do service de cache atual e ajustes nos testes diretamente impactados por esse service.

## Scope Out

Mudancas de produto fora do fluxo de cache e reescrita do modulo inteiro de observabilidade.

## Pass 1 - Discovery

Mapear callers, contratos e testes que cobrem o service atual. Confirmar que o refactor permanece delimitado e nao exige artifact formal de change.

## Implementation Checklist

- [ ] Separar a logica de leitura do provider de cache da logica de invalidacao.
- [ ] Extrair pontos de telemetria para um helper dedicado, preservando o contrato atual.
- [ ] Atualizar os testes afetados pelo refactor sem expandir escopo para outros modulos.
- [ ] Final Phase: rodar `pre-commit run --files <arquivos alterados>` e os testes impactados antes de encerrar.

## Validation Strategy

Rodar os testes unitarios do service e dos callers impactados. Validar tambem que os imports publicos nao mudaram e que o refactor nao abriu escopo para outros modulos.

## Next Step

Developer Engineer implementa o checklist acima no mesmo escopo delimitado.
```

Resposta curta esperada no chat:

- `Objetivo: organizar o refactor do service de cache em handoff executavel`
- `Arquivo do plano: refatorar_service_cache.md`
- `Fase atual: Pass 1 - Discovery`
- `Proxima acao: mapear callers, contratos e validacao final antes do handoff`

## Exemplo 2 - blocker por falta de evidencia

Pedido: "Ja monta o plano do refactor, mesmo sem saber ainda quais modulos e contratos vao mudar."

Arquivo criado: `refactor_backend.md`

Trecho esperado no arquivo:

```md
## Pass 1 - Discovery

Ainda nao existe evidencia suficiente sobre quais modulos, contratos e testes entram no escopo real. O plano nao pode avancar para checklist executavel sem essa delimitacao.

## Risks / Blockers

Blocker ativo: `Scope In` e `Validation Strategy` ainda dependeriam de adivinhacao.

## Next Step

Coletar os modulos realmente afetados e os testes atuais antes de transformar isso em checklist executavel.
```

Resposta curta esperada no chat:

- `Objetivo: tentar estruturar o refactor em plano executavel`
- `Arquivo do plano: refactor_backend.md`
- `Fase atual: Pass 1 - Discovery`
- `Blocker: ainda faltam evidencias sobre modulos, contratos e testes afetados`

## Exemplo 3 - final phase impede conclusão

Pedido: implementação terminada, mas um dos arquivos alterados falhou no `pre-commit`.

Trecho esperado no arquivo:

```md
## Final Phase (Obrigatória)

Arquivos alterados pela implementação:
`backend/services/cache_service.py`, `backend/tests/test_cache_service.py`

Comando de pre-commit nos arquivos alterados:
`pre-commit run --files backend/services/cache_service.py backend/tests/test_cache_service.py`

Testes existentes impactados:
`pytest backend/tests/test_cache_service.py`

Testes novos criados:
Nenhum.

Resultado registrado dos checks finais:
Falha em `ruff-backend` no arquivo `backend/services/cache_service.py`.

Bloqueios remanescentes da fase final:
O erro de lint impede concluir a refatoracao.

## Completion Rule

Não marque a refatoração como concluída antes de finalizar todos os checks.

A refatoração só poderá ser considerada concluída após a execução e aprovação de todos os checks deste plano, incluindo a Final Phase, sem qualquer erro pendente.
```

Resposta curta esperada no chat:

- `Objetivo: fechar o refactor do cache com validacao final`
- `Arquivo do plano: refatorar_service_cache.md`
- `Fase atual: Final Phase (Obrigatória)`
- `Blocker: pre-commit ainda falha em backend/services/cache_service.py`
