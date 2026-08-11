# Verification Harness

## O que e

`npm run ai:verify` e o harness canonico de validacao deterministica do caminho comum.
Este guia e a documentacao ampla do runtime: perfis, gates, escalacoes, saida e artifacts.

## Modelo mental

O harness faz cinco coisas:

1. Descobre `changedFiles`.
2. Resolve o `effectiveProfile`.
3. Seleciona as gates repo-native correspondentes.
4. Executa as gates na ordem declarada.
5. Devolve JSON estruturado e, quando pedido, persiste `gate-report`.

Ele nao substitui `review-workflow` ou `security-engineer`. Ele cobre a parte mecanica da validacao para que esses fluxos trabalhem com evidencia estavel.

## Fluxo

```text
diff atual ou --changed-file
  -> ai-verify.py
  -> resolve changedFiles
  -> resolve effectiveProfile
  -> escolhe gates
  -> executa gates
  -> JSON de resultado

se houver --session-dir
  -> artifacts/gate-report.json
  -> views/gate-report.md
  -> logs/ai-verify/<gate>.log
```

## Uso comum

- Validar o diff atual automaticamente:
  `npm run ai:verify`
- Explicar perfil e gates sem executar:
  `npm run ai:verify -- --dry-run`
- Validar um arquivo especifico quando o diff local nao representa bem a mudanca:
  `npm run ai:verify -- --changed-file src/features/auth/AuthProvider.tsx`
- Forcar um perfil quando o risco ja esta claro:
  `npm run ai:verify -- --profile high-risk`
- Persistir artifacts para uma sessao de review:
  `npm run ai:verify -- --session-dir .agents/sessions/review-<id>`

## Perfis

| profile | quando usar | gates padrao |
| --- | --- | --- |
| `quick` | docs/config e validacao rapida | roda os stages `pre-commit` e `pre-push` apenas nos arquivos modificados |
| `standard` | codigo comum de baixo ou medio risco | roda os stages `pre-commit` e `pre-push` apenas nos arquivos modificados |
| `high-risk` | contrato publico, store global, infra de agents e refactor amplo | roda os stages `pre-commit` e `pre-push` em todos os arquivos |
| `ui-flow` | inalcancavel neste repo; nenhum path-rule o aciona | roda os stages `pre-commit` e `pre-push` em todos os arquivos |
| `security-touch` | auth, boundary de API compartilhada e toque sensivel | roda os stages `pre-commit` e `pre-push` em todos os arquivos |

O perfil define apenas o **escopo de arquivos**. Quais gates rodam vem do
`.pre-commit-config.yaml` do projeto, nao de `verification-profiles.json`
(`schemaVersion` 2.0.0). O harness executa explicitamente os stages
`pre-commit` e `pre-push`; `validate-commit-msg` continua reservado ao stage
`commit-msg` do Git.

Regra mental simples:

- `quick` para mudanca leve.
- `standard` para codigo comum.
- `high-risk` para contrato ou infra sensivel.
- `security-touch` para auth e boundary de API.

## Como o perfil efetivo e resolvido

O harness monta `changedFiles` nesta ordem:

1. `--changed-file`
2. artifact `review-session.json` da `--session-dir`
3. `git diff --cached`
4. `git diff`
5. arquivos untracked via git

Os passos 3 a 5 passam pelo git, entao **arquivo ignorado pelo `.gitignore` nao
aparece** (o passo 5 usa `git ls-files --others --exclude-standard`). O proprio
harness esta nessa condicao: `.agents/` e ignorado por design, porque e tooling
interno de desenvolvimento e nao viaja com a biblioteca publicada. Para validar
uma mudanca no harness, passe os caminhos explicitamente:

```bash
npm run ai:verify -- --changed-file .agents/skills/<skill>/SKILL.md
```

Depois ele consulta `path-rules.json`.

- Se voce pedir `--profile auto`, o perfil mais forte que casar com o diff vence.
- Se voce pedir um perfil explicito mais fraco do que o diff exige, o harness eleva para o perfil detectado.
- Se nenhum arquivo alterado for detectado, `auto` cai em `standard`.

Regras relevantes no estado atual:

- `src/createagents/infra/adapters/**` e `src/createagents/infra/config/**` elevam para `security-touch` (credenciais de provedor, chamadas externas, logging e sanitizacao).
- `src/createagents/__init__.py`, `src/createagents/main/facade/**`, `src/createagents/domain/interfaces/**`, `src/createagents/main/composers/**`, `pyproject.toml`, `uv.lock`, `.pre-commit-config.yaml`, `.github/workflows/**`, `.agents/**`, `.claude/agents/**`, `.github/agents/**`, `.codex/agents/**`, `opencode.json` e `package.json` elevam para `high-risk`.
- `src/**/*.py` e `tests/**/*.py` resolvem para `standard`.
- `docs/**`, `mkdocs.yml` e `**/*.md` puxam para `quick` quando nenhuma regra mais forte se aplica.
- `ui-flow` continua definido no runtime, mas nenhum caminho deste repositorio o aciona: o projeto e uma biblioteca Python com CLI de terminal, sem browser nem Playwright.

## Escalacoes

O resultado sempre traz:

- `reviewRequired`
- `securityRequired`
- `testerRecommended`
- `reasons`

Leitura pratica:

- `reviewRequired=true` significa que a mudanca nao deveria encerrar sem `review-workflow`.
- `securityRequired=true` significa que o diff tocou area que pede `security-engineer`.
- `testerRecommended=true` significa que a mudanca toca superficie visual ou fluxo que merece teste dedicado — hoje isso e responsabilidade direta do `developer-engineer`, apoiado pelas skills `tdd-workflow`/`testing-patterns`.

Mesmo quando nenhuma regra previa pedia review, uma gate com `failed` ou `external_failure` adiciona `reviewRequired=true`.

## Como ler a saida

Olhe nesta ordem:

1. `status`
2. `effectiveProfile`
3. `escalations`
4. `gates`
5. `summary`

Atalho de triagem:

- `status=passed` e nenhum escalonamento critico: diff validado mecanicamente.
- `status=failed`: algum gate bloqueante falhou por codigo.
- `status=external_failure`: a verificacao falhou por ambiente.
- `securityRequired=true`: trate como mudanca sensivel, nao como simples validacao local.

## Status e classification

Cada gate tem duas camadas de interpretacao:

- `status`: `passed`, `failed`, `skipped`, `external_failure`
- `classification`: `code`, `environment`, `not_configured`, `not_applicable`

Leitura rapida:

- `failed` + `code`: o codigo ou o teste falhou de verdade.
- `external_failure` + `environment`: faltou binario, timeout, browser do Playwright, permissao ou ambiente.
- `skipped` + `not_configured`: script ausente em gate opcional ou nao configurada.
- `skipped` + `not_applicable`: `dry-run` ou gate nao executada.

## Exit code

- Exit `0`: nenhum gate bloqueante falhou.
- Exit `1`: pelo menos um gate bloqueante terminou em `failed` ou `external_failure`.
- Gate advisory pode falhar e continuar visivel no JSON sem derrubar o comando sozinha.
- `--dry-run` sempre sai sem falha de gate.

## Gate-report e logs

Quando voce usa `--session-dir`, o harness persiste:

- `artifacts/gate-report.json`
- `views/gate-report.md`
- `logs/ai-verify/<gate>.log`

O `review-workflow` consome o JSON canonico. O Markdown e apenas view humana.

Campos importantes do `gate-report`:

- `profile`
- `effectiveProfile`
- `profileReason`
- `changedFiles`
- `escalations`
- `summary`
- `gates` com `gateId`, `status`, `classification`, `exitCode`, `durationMs`, `outcome` e `logPath`

## Formato da saida

O JSON top-level tem estes campos:

- `schemaVersion`
- `status`
- `profile`
- `effectiveProfile`
- `profileReason`
- `changedFiles`
- `gates`
- `escalations`
- `sessionDir`
- `summary`

Interpretacao do top-level:

- `passed`: nenhum gate bloqueante falhou.
- `failed`: pelo menos um gate bloqueante falhou por codigo.
- `external_failure`: pelo menos um gate bloqueante falhou por ambiente.
- `skipped`: `dry-run` ou nenhum gate executavel.

## Arquivos relacionados

- `.agents/skills/lint-and-validate/scripts/ai-verify.py`: harness primario.
- `.agents/skills/lint-and-validate/assets/verification-profiles.json`: define gates, labels, timeouts e perfis.
- `.agents/skills/lint-and-validate/assets/path-rules.json`: resolve perfil por diff.
- `.agents/skills/lint-and-validate/assets/escalation-rules.json`: resolve review, security e recomendacao de teste dedicado.
- `.agents/skills/lint-and-validate/schemas/ai-verify.schema.json`: contrato estavel da saida.
- `.agents/skills/lint-and-validate/references/examples.md`: exemplos de pedidos e uso da skill.

## Limites

- Nao assume `--fix` por padrao.
- Nao trata gate nao executada como `passed`.
- Nao enxerga arquivo ignorado pelo `.gitignore` na descoberta automatica.
- Nao substitui julgamento de seguranca quando `securityRequired=true`.
- Nao substitui estrategia de teste; quando `testerRecommended=true`, isso e um sinal para o `developer-engineer` dar atencao dedicada, nao uma execucao automatica.

## Troubleshooting

- O perfil parece errado:
  use `--dry-run` e confira `changedFiles` e `profileReason`.
- O diff real nao apareceu:
  passe `--changed-file` manualmente.
- O `review-workflow` nao encontrou gates:
  rode novamente com `--session-dir`.
- O comando falhou mas nao parece bug do codigo:
  confira `classification` e o `logPath` da gate.
- Mudei o harness e o diff saiu vazio:
  esperado. `.agents/` e ignorado pelo git; use `--changed-file`.
- Procurando a gate de E2E:
  nao existe neste repositorio. O projeto e uma biblioteca Python com CLI de
  terminal; nao ha browser, Playwright nem `test:e2e` no `package.json`. As
  gates de qualidade vem do `.pre-commit-config.yaml`.
