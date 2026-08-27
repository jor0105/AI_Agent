# Autoria de políticas e preferências

## Sumário

- Diferença entre fato técnico, política e preferência.
- Ordem exata para resolver o perfil operacional.
- Contratos de idioma, gerenciador, framework e qualidade.
- Composição de `Mandatory Rules` e `Execution Policy`.
- Conflitos, fallbacks e critérios de completude.

## Princípio

Um `AGENTS.md` útil não diz apenas “siga o projeto”. Ele nomeia as escolhas que
um agente precisa repetir corretamente: em qual idioma colaborar, qual manager e
runner usar, qual framework preservar, quais checks executar e quais mudanças
exigem parada.

Separe sempre três perguntas:

1. **O que existe?** Resposta factual do repositório.
2. **O que governa?** Política aplicável e autoridade do projeto.
3. **Como o usuário prefere trabalhar?** Decisão explícita de colaboração ou de
   direção, válida quando compatível com as duas anteriores.

Misturar as respostas produz dois erros opostos: uma preferência vira uma falsa
descrição do runtime ou um documento factual demais deixa de orientar o agente.

## Ordem de resolução

Para cada decisão do perfil operacional:

1. aplique constraints superiores que o documento não pode contrariar;
2. leia `AGENTS.md` ancestrais e políticas canônicas do escopo;
3. capture decisões e preferências explícitas do usuário;
4. confirme o estado técnico em manifests, lockfiles, config, scripts e CI;
5. confronte as fontes e marque `confirmed`, `unknown` ou `conflict`;
6. materialize uma regra direta somente quando ela não falsificar o projeto;
7. mantenha `Draft` se uma decisão essencial continuar sem autoridade.

Preferência explícita não precisa já existir em documento para ser registrada,
mas não substitui uma migração técnica. Exemplo: “fale em português” pode virar
política de chat imediatamente; “use outro framework” não torna o novo framework
parte do sistema antes da mudança correspondente.

## Registro mínimo

Antes de escrever `Mandatory Rules`, preencha internamente:

| Campo         | Pergunta que precisa de resposta                            | Fonte forte                                     |
| ------------- | ----------------------------------------------------------- | ----------------------------------------------- |
| Chat          | Em qual idioma o agente responde ao usuário?                | preferência explícita                           |
| Code          | Idioma de identificadores e código                          | política ou decisão explícita compatível        |
| Comments      | Idioma e quando comentários são aceitáveis                  | política ou decisão explícita                   |
| Documentation | Idioma da documentação                                      | política, corpus governado ou decisão explícita |
| Git           | Idioma/formato de commits, branches e PRs                   | contribuição ou decisão explícita               |
| Manager       | Qual ferramenta altera dependências e lockfile?             | manifest + lockfile + CI                        |
| Runner        | Qual prefixo executa comandos?                              | scripts, task runner e CI                       |
| Framework     | Qual framework existe e qual padrão deve ser preservado?    | manifest + runtime + arquitetura                |
| Quality       | Quais comandos provam format, lint, types, tests e release? | manifests, CI e harness oficial                 |
| Change style  | Clean cutover, compatibilidade, migração e tamanho de diff  | política ou preferência explícita               |

Uma mesma decisão pode ter mais de uma fonte. Registre o escopo: root,
subárvore, linguagem, serviço ou interação com o usuário.

## Política de idioma

Não trate “idioma” como um único campo. Resolva separadamente:

- chat com o usuário;
- código e identificadores;
- comentários;
- documentação;
- Git: commits, branches, PRs e tags.

Uma mensagem escrita em português ou inglês é evidência de comunicação atual,
não prova uma preferência durável para código ou Git. Procure instrução explícita
como “responda em português” ou política de contribuição. Se o usuário declarar
um agrupamento, preserve a forma concisa:

```markdown
- `Code/Git = English` and `Chat = Portuguese`.
```

Se docs ou comentários tiverem regra diferente, escreva-os separadamente. Não
infira idioma obrigatório apenas porque a maioria dos arquivos usa uma língua;
isso pode ser observação factual, mas não política.

## Gerenciador de dependências e command runner

Resolva o manager por convergência de evidências, nesta ordem prática:

1. campo explícito no manifest ou configuração de workspace;
2. lockfile vigente e único;
3. scripts oficiais e CI;
4. documentação operacional marcada como atual.

Ambiente local instalado e preferência pessoal isolada não provam o manager do
projeto. Quando as fontes convergem, nomeie a ferramenta e a forma de comando:

```markdown
- Use `uv run` for Python commands.
- Use `pnpm` for dependency and workspace commands; do not create npm or Yarn lockfiles.
- Use the checked-in Gradle wrapper (`./gradlew`), not a system Gradle installation.
```

Os exemplos mostram formato, não valores a copiar. Para repositório multi-stack,
defina o manager por subárvore. Se houver dois lockfiles concorrentes sem escopo
documentado, marque `CONFLICT`.

## Framework e padrões de contribuição

Distinga tecnologia existente de preferência para trabalho novo:

- **framework atual**: confirmado por manifest, imports centrais, entrypoint e
  configuração;
- **abstração/padrão owner**: confirmado por arquitetura, código dominante e
  decisões aceitas;
- **preferência do usuário**: direção para novas escolhas compatíveis ou uma
  mudança separada a planejar.

Uma regra forte combina fato e comportamento esperado:

```markdown
- Build UI changes with the existing React component and routing patterns; do not introduce a second UI framework.
- Use the project's service boundary for persistence; do not access the database directly from request handlers.
```

Não escreva “use React” apenas porque uma dependência aparece em pacote auxiliar.
Confirme o escopo. Não converta “prefiro Svelte” em política atual de um sistema
React; registre a preferência e trate uma migração como tarefa distinta.

## Padrão de qualidade

Descubra e nomeie, quando aplicável:

- formatter e comando;
- linter e comando;
- typechecker e comando;
- testes unitários, integração e E2E;
- scanner de segurança;
- build ou compilação;
- documentação estrita;
- harness/agregador oficial de validação.

Se existir um entrypoint agregador oficial, torne-o a regra principal e use
comandos individuais apenas para validação direcionada. A regra deve dizer qual
comando executar antes de concluir e como reportar falha ou skip.

Não invente “100% coverage”, benchmark ou SLO. Qualidade forte significa gates
reais, invariantes e comportamento de falha explícito, não números decorativos.

## Estilo de mudança e compatibilidade

Capture preferências que alteram decisões recorrentes:

- mudanças pequenas e verificáveis;
- clean cutover versus compatibilidade obrigatória;
- política para código morto, shims e deprecated paths;
- necessidade de plano antes de alteração ampla;
- atualização conjunta de código, testes, contratos e docs;
- limites de autonomia e quando pedir confirmação.

O baseline da skill favorece escopo pequeno, ausência de caminhos mortos após um
clean cutover concluído e atualização de contratos associados. Se o projeto
mantém compatibilidade pública obrigatória, essa política específica prevalece e
deve ser descrita com seu owner.

## Como compor `Mandatory Rules`

Mantenha a ordem:

1. higiene, disciplina de código (fatoração coesa, zero duplicação, sem dependências circulares) e verificação antes de editar;
2. idiomas e colaboração;
3. manager, runner e comandos oficiais;
4. framework, arquitetura e ownership;
5. qualidade, testes e documentação;
6. invariantes de dados e segurança;
7. estado atual versus estado planejado;
8. navegação e progressive disclosure.

Cada bullet deve orientar uma decisão. Prefira:

```markdown
- Use `cargo test --workspace` before concluding Rust behavior changes.
```

Evite:

```markdown
- Test appropriately.
```

Não repita detalhes que já pertencem a uma tabela ou manual, exceto quando a
forma imperativa muda como o agente deve agir.

## Como preservar `Execution Policy`

`Execution Policy` é baseline operacional, não uma lista opcional de sugestões.
Preserve os oito subtítulos e seu conteúdo concreto:

1. `Precedence`: ordem de autoridades e resolução de conflito;
2. `Hard Blocks`: operações destrutivas nomeadas, remote piping, escrita fora do
   escopo e bypass de controles;
3. `Secrets`: proibição de buscar/expor e procedimento ao encontrar;
4. `Repo Alignment`: contratos canônicos, padrões existentes e stop on conflict;
5. `Autonomy`: três condições cumulativas e situações de parada;
6. `Validation`: entrypoint oficial e declaração de falha/skip;
7. `Execution Safety`: impacto, target, dry run e passos legíveis;
8. `Failure Handling`: fail-closed para segurança, permissão e autenticação.

Customize somente boundaries e controles adicionais do alvo. Não resuma a lista
de Git para “evite comandos destrutivos”: o valor está em tornar as operações
inequívocas para um executor literal.

## Matriz de conflito

| Situação                                                     | Ação                                                                 |
| ------------------------------------------------------------ | -------------------------------------------------------------------- |
| usuário escolhe idioma de chat sem conflito                  | materialize `USER_PREFERENCE`                                        |
| usuário escolhe idioma de código e não há política contrária | materialize e mantenha Draft até aprovação se necessário             |
| manager/lockfile/CI convergem                                | documente como `REPO_FACT` e regra operacional                       |
| usuário prefere manager diferente                            | preserve estado real; `CONFLICT`; migração separada                  |
| framework existe, padrão não está documentado                | descreva framework como fato e use apenas padrões observáveis; Draft |
| duas políticas do mesmo nível divergem                       | não escolha; identifique fontes e peça decisão                       |
| preferência pede bypass de segurança/permissão               | rejeite; política superior prevalece                                 |

## Checklist de completude

- [ ] idiomas de chat, código, comentários, docs e Git foram resolvidos ou
  marcados explicitamente como pendentes;
- [ ] manager e runner têm fonte técnica e regra concreta;
- [ ] framework atual não foi confundido com preferência futura;
- [ ] comandos de qualidade foram confirmados em tooling vigente;
- [ ] preferência de compatibilidade e estilo de mudança foi considerada;
- [ ] `Mandatory Rules` preserva todo o baseline e adiciona regras específicas;
- [ ] `Execution Policy` mantém os oito subtítulos e hard blocks concretos;
- [ ] conflitos mantêm o documento em Draft e aparecem no relatório.
