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

- `npm run ai:verify` para diff comum;
- `npm run skills:validate -- --skill <nome>` para uma skill especifica;
- `npm run skills:validate:central` para o pack central;
- `npm run agents:validate-protocols` para agents, manifests e protocol skills.

## O que fazer na pratica

1. Confirme se o pedido e de validacao, nao de implementacao ou arquitetura.
2. Escolha o entrypoint pelo artefato:
   - diff comum: `npm run ai:verify`
   - skill individual: `npm run skills:validate -- --skill <nome>`
   - skill central: `npm run skills:validate:central`
   - agents/protocolos: `npm run agents:validate-protocols`
3. Se o caminho for diff comum e a selecao de gates for parte da decisao, rode antes `npm run ai:verify -- --dry-run`.
4. Se houver review runtime, passe `--session-dir` no `ai:verify`.
5. No `ai:verify`, leia o resultado nesta ordem: `status`, `effectiveProfile`, `escalations`, `gates`, `summary`.

## O que nao fazer

- Nao substituir `review-workflow` ou `security-engineer`.
- Nao usar autofix amplo como comportamento padrao.
- Nao criar wrapper local se o script oficial do repo ja cobre a necessidade.
- Nao escolher perfil manualmente sem motivo claro.
- Nao usar `validate-agent-protocols` como se fosse validador geral de todas as skills.

## Perguntas que esta skill responde bem

- "Qual e o menor comando canonico para validar isso?"
- "Preciso executar ou basta um `--dry-run`?"
- "Essa falha e de codigo ou de ambiente?"
- "Preciso persistir artifacts para review?"
- "Isso e governanca de skill ou protocolo de agents?"

## Atalhos uteis

- Explicar o que vai rodar (lista hooks e stages do `.pre-commit-config.yaml`):
  `npm run ai:verify -- --dry-run`
- Diff comum (roda o stage `pre-commit` no escopo e o `pre-push` com testes/auditoria):
  `npm run ai:verify`
- Validacao reforcada (roda ambos os stages em todos os arquivos):
  `npm run ai:verify -- --profile high-risk`
- Forcar arquivo quando o diff local nao ajuda:
  `npm run ai:verify -- --changed-file src/features/auth/AuthProvider.tsx`
- Persistir para review:
  `npm run ai:verify -- --session-dir .agents/sessions/review-<id>`
- Validar uma skill:
  `npm run skills:validate -- --skill lint-and-validate`
- Validar skills centrais:
  `npm run skills:validate:central`
- Validar agents e protocol skills:
  `npm run agents:validate-protocols`

## Exemplos e guia amplo

- [examples.md](./examples.md): pedidos concretos e resposta esperada da skill.
- [verification-harness.md](../../verification-harness.md): runtime completo de `ai:verify`, perfis, output, artifacts e troubleshooting.
