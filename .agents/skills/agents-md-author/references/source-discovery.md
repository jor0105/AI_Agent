# Descoberta portátil de fontes

## Sumário

- Sequência de inspeção sem efeitos colaterais.
- Matriz de manifests e tooling por ecossistema.
- Regras para comandos, arquitetura, ownership e navegação.
- Escopo de monorepos e tratamento de conflitos.

## Sequência de inspeção

1. Descubra instruções aplicáveis e a forma do repositório:

   ```bash
   rg --files -g 'AGENTS.md' -g 'README*' -g 'CONTRIBUTING*' -g 'CODEOWNERS'
   ```

2. Liste manifests, task runners, CI e deploy config sem assumir linguagem:

   ```bash
   rg --files -g 'pyproject.toml' -g 'package.json' -g 'Cargo.toml' -g 'go.mod' -g 'pom.xml' -g 'build.gradle*' -g '*.csproj' -g '*.sln' -g 'Gemfile' -g 'composer.json' -g 'Package.swift' -g 'Makefile' -g 'Taskfile*' -g 'Dockerfile*' -g 'compose*.yml' -g '.github/workflows/*'
   ```

3. Abra apenas os candidatos relevantes. Confirme scripts, entrypoints, versões,
   paths e ferramentas dentro do arquivo; a presença do manifest identifica um
   ecossistema, não toda a arquitetura.

4. Localize documentação e decisões com `rg --files docs` quando `docs/` existir.
   Procure portais, arquitetura, operações, testes, runbooks, ADRs, RFCs e regras
   de governança. Use status e ownership declarados; não presuma canonicalidade
   por localização.

5. Confronte comandos declarados com CI e task runners. Não execute comandos com
   side effects para decidir qual texto escrever. `--help`, listagem de tasks e
   checks secos são aceitáveis quando o caminho foi inspecionado e é seguro.

6. Monte uma rota de navegação antes de redigir. Para cada pergunta recorrente
   (`como começar`, `como funciona`, `como executar`, `como testar`, `como operar`,
   `quem decidiu`), registre o primeiro arquivo, o owner dos detalhes e o próximo
   nível de leitura. Se não houver fonte, marque a lacuna em vez de preencher a
   rota com diretórios prováveis.

## Matriz por ecossistema

| Ecossistema     | Fontes primárias                                     | Confirme                                                             |
| --------------- | ---------------------------------------------------- | -------------------------------------------------------------------- |
| Python          | `pyproject.toml`, lockfile, módulos CLI, tox/nox     | versão, manager/runner, framework, entrypoints, lint, types e testes |
| Node/TypeScript | `package.json`, lockfile, workspace config, tsconfig | scripts, package manager, runtime, framework, build, lint e testes   |
| Rust            | `Cargo.toml`, `Cargo.lock`, workspace members        | crates, binários, features, framework, fmt, clippy e testes          |
| Go              | `go.mod`, `go.work`, `cmd/`, CI                      | módulos, framework/router, comandos, geração, lint e testes          |
| JVM             | `pom.xml`, Gradle files, wrapper, settings           | módulos, JDK, framework, wrapper, tasks, build e testes              |
| .NET            | solution/project files, props/targets, tool manifest | SDK, projects, framework, run, format e testes                       |
| Ruby            | `Gemfile`, gemspec, Rakefile                         | versão, framework, executáveis, tasks e testes                       |
| PHP             | `composer.json`, lockfile, framework console         | versão, manager, framework, autoload, lint e testes                  |
| Swift           | `Package.swift`, Xcode project/workspace, CI         | platforms, frameworks, schemes, build e testes                       |
| Infra/data      | Docker, Compose, Terraform, Helm, migration config   | boundaries, state owner, apply/deploy commands e safety gates        |

Um repositório pode combinar várias linhas. Registre evidência por componente em
vez de escolher uma stack “principal” sem contrato explícito.

## Como confirmar cada tipo de claim

| Claim                | Evidência forte                                                 | Evidência insuficiente isoladamente       |
| -------------------- | --------------------------------------------------------------- | ----------------------------------------- |
| nome e missão        | package metadata + README vigente + entrypoint                  | nome do diretório                         |
| owner                | governança, CODEOWNERS, catálogo de serviços, decisão explícita | autor mais frequente do Git               |
| comando oficial      | manifest/task runner + CI ou doc operacional vigente            | snippet antigo no README                  |
| dependency manager   | campo de manifest/workspace + lockfile + CI                     | ferramenta instalada localmente           |
| framework atual      | manifest + entrypoint/imports estruturais + config              | dependência transitiva ou pacote auxiliar |
| idioma de chat       | preferência explícita do usuário                                | idioma casual de uma mensagem             |
| idioma de código/Git | política de contribuição ou decisão explícita                   | maioria estatística dos arquivos          |
| arquitetura          | runtime/entrypoints + ADR/doc aceita                            | nomes de pastas                           |
| versão               | manifest, lockfile ou CI                                        | versão instalada na máquina do agente     |
| variável pública     | config code ou env example                                      | valor em `.env` real                      |
| métrica              | SLO, config, teste de gate ou observabilidade                   | recomendação genérica do setor            |
| consumidor           | import/dependency, deploy config ou doc aceita                  | comentário isolado                        |
| documento canônico   | governança, portal ou metadata de status                        | estar dentro de `docs/`                   |

Para transformar esses fatos em regras, aplique
`references/policy-authoring.md`. Descoberta confirma o estado; autoria de
política decide como o agente deve agir.

## Mapa de navegação

Construa o mapa por perguntas, não por extensão de arquivo:

| Pergunta                           | Evidência procurada                       | Resultado no AGENTS.md                       |
| ---------------------------------- | ----------------------------------------- | -------------------------------------------- |
| O que é o projeto?                 | portal/README + metadata + entrypoint     | identidade e boundaries em `System Overview` |
| Como o runtime flui?               | entrypoint + wiring + deploy/architecture | fluxo em `Pipeline Architecture`             |
| Onde altero cada responsabilidade? | docs owner + módulos implementados        | ownership e próximo arquivo a abrir          |
| Como executo e valido?             | manifest + scripts + CI/harness           | comandos exatos em `Configuration & Runtime` |
| Como opero ou diagnostico?         | operations, runbooks, observability       | rota em `Related Documentation`              |
| Qual decisão governa?              | governance + ADR/RFC status               | classe e autoridade da fonte                 |

Um link só entra na rota quando existe e seu propósito foi lido. Ordene fontes
humanas por progressive disclosure: orientação antes de arquitetura detalhada;
arquitetura antes de referência especializada; operação antes de incidente
específico. Código pode ser a autoridade factual, mas não substitui a rota de
leitura quando documentação owner existe.

## Monorepos e hierarquia

- Leia a cadeia de `AGENTS.md` da raiz até o alvo. A instrução mais próxima só
  deve especializar o que muda naquela subárvore.
- Mantenha no root: políticas transversais, mapa macro, comandos globais,
  perfil operacional compartilhado, navegação e regras de segurança.
- Mantenha localmente: stack exclusiva, comandos do pacote, ownership local,
  contratos e riscos que não valem para os demais componentes.
- Evite copiar o baseline inteiro para cada pacote. O arquivo local herda a
  política superior e registra somente diferenças.
- Se duas ferramentas de workspace coexistirem, documente o escopo de cada uma;
  não escolha uma como padrão global sem evidência.
- Preferências de idioma e colaboração podem permanecer no root. Manager,
  framework e comandos pertencem ao menor escopo em que são verdadeiros.

## Conflitos e stop rules

Classifique como `CONFLICT` quando fontes atuais discordarem sobre:

- comando oficial de build, test, deploy ou migration;
- dependency manager, lockfile owner, framework ou idioma obrigatório;
- owner ou boundary de componente;
- status de documento ou decisão;
- contrato público, persisted format ou política de segurança;
- runtime, entrypoint ou topologia de produção.

Registre caminho e afirmação de cada fonte. Pare apenas a claim afetada, mantenha
o documento como `Draft` e peça decisão. Continue coletando fatos independentes
quando isso não aumentar o risco nem mascarar a divergência.

## Checklist de descoberta

- [ ] cadeia de `AGENTS.md` lida;
- [ ] orientação e governança inspecionadas;
- [ ] manifests e lockfiles identificados;
- [ ] scripts oficiais e CI confrontados;
- [ ] manager, runner, framework e quality tooling confirmados por escopo;
- [ ] preferências explícitas do usuário registradas separadamente de fatos;
- [ ] entrypoints e boundaries confirmados;
- [ ] config pública inspecionada sem abrir segredos;
- [ ] testes e gates identificados;
- [ ] docs e status classificados;
- [ ] rota de navegação por pergunta materializada;
- [ ] facts, unknowns e conflicts registrados no ledger.
