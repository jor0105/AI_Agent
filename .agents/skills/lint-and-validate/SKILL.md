---
name: lint-and-validate
description: >
  Use para escolher e executar validação repo-native depois de mudanças. Ative
  quando o usuário pedir "valida", "roda os checks", "garante que não quebrou",
  "roda testes", "passa o lint", "gera gate-report", "confere antes de
  finalizar" ou quando a entrega precisa evidência terminal. Cobre lint,
  typecheck, testes, `ai:verify`, perfis e gate-report. Não use para desenhar
  estratégia de testes nem para investigar root cause incerta.
---

# Lint And Validate

## Fundamentos

- **Confiança Cega é Falha:** Nunca entregue um código dizendo "Acredito que vai funcionar". Você deve executar lints e testes reais via terminal para comprovar.
- **Cheap First, Evidence Complete:** Comece pelos gates mais baratos de interpretar, mas preserve o resultado estruturado do fluxo canônico. Para diff comum, prefira `npm run ai:verify`; ele decide perfil, ordem de gates e escalonamentos sem inventar regra local.
- **Isolamento:** Quando o TypeScript falhar, olhe apenas para o arquivo que você editou e os arquivos que dependem dele. Ignorar erros não relacionados ao escopo a menos que você os tenha causado.

## Procedimento

1. Identifique o artefato que precisa ser validado antes de escolher o comando:
   - diff comum do repositório: `npm run ai:verify`
   - uma skill específica: `npm run skills:validate -- --skill <nome>`
   - skill central do pack principal: `npm run skills:validate:central`
   - agents, manifests e protocolo `review-workflow`: `npm run agents:validate-protocols`
2. Para diff comum, escolha o menor perfil que ainda cubra o risco da mudança. Use `assets/verification-profiles.json` como fonte de verdade dos gates e `npm run ai:verify -- --dry-run` quando a seleção de perfil fizer parte da decisão.
3. Leia a saída do `ai:verify` nesta ordem: `status`, `effectiveProfile`, `escalations`, `gates`, `summary`. Não trate gate `skipped` como sucesso implícito.
4. Responda com evidência terminal mínima: comando, escopo, status, classificação da falha quando existir e próximo passo. Não declare sucesso sem output correspondente.

## Exemplos

### Caso positivo

**Entrada:** Após mudar frontend e backend, usuário pede validação antes de finalizar.
**Saída esperada:** Resolver perfil, rodar comandos repo-native, resumir evidência e produzir gate-report quando exigido.

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

- [ ] escolhe `npm run ai:verify` como entrypoint principal
- [ ] usa o `effectiveProfile` resolvido, não um perfil inventado
- [ ] reporta gates bloqueantes e advisory separadamente

### Cenário 2 - validação de skill

Entrada: pedido para validar apenas a skill `lint-and-validate`.

Assertions:

- [ ] usa `npm run skills:validate -- --skill lint-and-validate`
- [ ] não chama `validate-agent-protocols.py` como se cobrisse toda governança de skills
- [ ] reporta erro estrutural se o `SKILL.md` violar o contrato da `skill-governance`

### Cenário 3 - protocolo de agents

Entrada: pedido para validar agents, manifests e protocolo `review-workflow`.

Assertions:

- [ ] usa `npm run agents:validate-protocols`
- [ ] deixa claro que o escopo é protocolo de agents, não qualquer skill do repo
- [ ] reporta falha estrutural sem declarar sucesso parcial implícito

### Cenário 4 - falha externa

Entrada: comando oficial existe, mas `npm` não está disponível no ambiente.

Assertions:

- [ ] classifica a falha como ambiente ou `external_failure`
- [ ] não classifica o problema como erro de código sem evidência
- [ ] devolve comando e sintoma mínimo para reproduzir

### Cenário 5 - E2E proporcional

Entrada: mudança de texto em componente interno sem fluxo de navegador afetado.

Assertions:

- [ ] não força E2E por padrão fora do perfil proporcional
- [ ] usa o perfil/gates resolvidos pelo harness, em vez de exigir browser manualmente
- [ ] deixa explícito se E2E ficou advisory ou `skipped`

## Scripts

- `scripts/ai-verify.py`: executa perfis repo-native e gera resultado de gates.
- `scripts/normalize-skill-metadata.py`: remove metadados extras do frontmatter de skills em lote controlado.
- `scripts/validate-agent-protocols.py`: valida manifests, agents e protocol skills do fluxo de review.

## Referências

Leia apenas o arquivo relevante para o tipo de validação em mãos:

| Problema                                             | Arquivo                   |
| ---------------------------------------------------- | ------------------------- |
| Ver exemplos de gate-report e resposta final         | `references/examples.md`  |
| Confirmar contrato operacional do fluxo de validação | `references/reference.md` |
