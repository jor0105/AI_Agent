---
name: agents-md-author
description: >
  Use para criar, recriar, revisar ou fortalecer um AGENTS.md que explique o
  projeto, ensine agentes a navegar nele e estabeleça políticas rigorosas de
  desenvolvimento, qualidade e execução. Ative quando o usuário pedir "cria um
  agents.md", "documenta este projeto para agentes", "define as rules dos
  agents", "inclui meu idioma/gerenciador/framework", "melhora a execution
  policy" ou exigir que arquitetura, comandos e preferências não sejam
  inventados. Cobre repositórios simples, monorepos e AGENTS.md locais. Não use
  para criar outra skill, escrever README comum ou decidir arquitetura sem
  produzir ou revisar AGENTS.md.
---

# AGENTS.md Author

## Contrato do artefato

Trate `AGENTS.md` como o manual operacional de maior precedência dentro do
escopo que ele governa. O documento precisa permitir que outro agente responda,
sem adivinhar:

1. o que o sistema faz, para quem e com quais invariantes;
2. onde começar e como navegar por código, documentação e operações;
3. como desenvolver neste projeto, inclusive idioma, gerenciador, framework,
   comandos oficiais e padrão de qualidade;
4. o que pode executar autonomamente, o que deve validar e onde deve parar.

O pacote desta skill é a autoridade de estrutura e política operacional base. O
repositório alvo fornece fatos técnicos e políticas locais; preferências
explícitas do usuário fornecem o modo de colaboração e podem definir regras de
desenvolvimento quando não falsificam o estado real do projeto.

Leia integralmente, antes de escrever:

- `assets/AGENTS.template.md`: headings, tabelas, regras gerais e Execution
  Policy completa;
- `references/content-contract.md`: conteúdo obrigatório e fontes por seção;
- `references/policy-authoring.md`: resolução de idioma, tooling, framework,
  qualidade e preferências do usuário;
- `references/source-discovery.md`: descoberta multi-stack, monorepos e
  navegação baseada em evidência.

Não procure um repositório externo para imitar e não use o projeto onde a skill
está instalada como fonte de fatos. A portabilidade vem de separar o baseline
bundled dos dados coletados no alvo, não de enfraquecer as regras.

## Procedimento

1. Resolva o escopo e a hierarquia de instruções.

   - Identifique o caminho exato do `AGENTS.md` alvo e a raiz governada por ele.
   - Leia todos os `AGENTS.md` ancestrais aplicáveis antes de propor texto.
   - Leia o arquivo alvo existente antes de editar e preserve regras válidas
     fora do pedido.
   - Em monorepos, mantenha políticas transversais no root. Crie arquivos locais
     somente quando stack, comandos, ownership, contratos ou riscos diferirem.
   - Um arquivo local herda o superior e registra diferenças; não replique a
     política inteira em toda subárvore.

2. Resolva o perfil operacional do usuário e do projeto antes da prosa.

   Construa esta matriz internamente:

   | Decisão | Valor | Fonte | Autoridade | Escopo | Estado |
   | --- | --- | --- | --- | --- | --- |
   | idioma de chat | ... | ... | ... | ... | confirmed/unknown/conflict |
   | idioma de código, comentários, docs e Git | ... | ... | ... | ... | ... |
   | gerenciador de dependências | ... | ... | ... | ... | ... |
   | command runner e validação oficial | ... | ... | ... | ... | ... |
   | framework atual e regra para novas implementações | ... | ... | ... | ... | ... |
   | formatter, lint, tipos e testes | ... | ... | ... | ... | ... |
   | estilo de mudança e compatibilidade | ... | ... | ... | ... | ... |

   - Use preferências explicitamente declaradas pelo usuário na conversa ou em
     instruções aplicáveis. O idioma usado casualmente na mensagem, sozinho,
     não define o idioma de código, documentação ou commits.
   - Use manifests, lockfiles, CI e scripts para confirmar o tooling real. Uma
     preferência não transforma um gerenciador ou framework ausente em fato.
   - Quando o usuário escolhe uma regra compatível com o projeto, registre-a
     como `USER_PREFERENCE` e escreva uma diretiva concreta em `Mandatory Rules`.
   - Quando preferência e contrato vigente colidem, mantenha o estado real,
     classifique `CONFLICT` e explique que adotar a preferência exige uma mudança
     separada. Não documente uma migração inexistente como política atual.
   - Se uma preferência essencial não estiver declarada, não invente. Para um
     draft, use uma regra conservadora baseada no repositório; para declarar o
     documento pronto para aprovação, obtenha a decisão faltante.

3. Faça descoberta somente de leitura.

   - Localize orientação, governança, manifests, lockfiles, entrypoints,
     configuração, scripts oficiais, CI, testes, documentação, ADRs, runbooks e
     ownership.
   - Meça o tamanho do código de produção. Ele define o orçamento de linhas em
     `references/content-contract.md`, seção `Proporcionalidade`, e decide
     quanto cada seção pode ocupar antes de virar cópia de outra fonte.
   - Confirme conteúdo dentro dos arquivos. Nomes de diretório são pistas, não
     prova de arquitetura ou responsabilidade.
   - Leia exemplos de ambiente e código de configuração para descobrir nomes de
     variáveis; não abra valores de `.env`, cofres ou credenciais.
   - Não execute build, deploy, migração, pipeline, acesso externo ou qualquer
     fluxo com efeitos colaterais apenas para descobrir como documentar.

4. Construa o ledger de evidências antes do texto final.

   | Claim | Classe | Fonte | Estado | Destino |
   | --- | --- | --- | --- | --- |
   | <afirmação> | <classe> | <arquivo:linha ou decisão> | <confirmed/unknown/conflict> | <seção> |

   Use somente estas classes:

   - `PORTABLE_BASELINE`: política copiada do template e independente de stack,
     domínio ou organização;
   - `REPO_FACT`: comportamento confirmado por código, manifest, CI, teste ou
     documentação vigente;
   - `REPO_POLICY`: regra confirmada por instrução aplicável, governança,
     CODEOWNERS ou decisão aceita;
   - `USER_PREFERENCE`: modo de trabalho explicitamente escolhido pelo usuário,
     como idiomas, ferramenta preferida ou estilo de mudança;
   - `USER_DECISION`: aprovação pontual, como owner ou status do documento;
   - `EXPLICIT_UNKNOWN`: informação procurada e não encontrada, representada por
     fallback declarado;
   - `CONFLICT`: fontes ou autoridades atuais discordam e exigem decisão.

   Nenhum comando, path, versão, métrica, componente, fase, owner, idioma,
   gerenciador ou framework entra no documento sem classe e fonte.

5. Produza um mapa de navegação, não apenas uma descrição.

   Confirme e registre:

   - o entrypoint humano: README, portal ou onboarding;
   - o entrypoint de runtime e o caminho macro até os componentes principais;
   - o documento de arquitetura e o owner de detalhes por domínio;
   - onde ficam configuração, testes, operações, runbooks, contratos e decisões;
   - quais fontes são canônicas, planejadas, geradas, exploratórias ou
     não canônicas, quando essa classificação existir;
   - a ordem de leitura para uma primeira mudança segura.

   `System Overview` explica identidade e limites. `Pipeline Architecture`
   explica fluxo, ownership e onde começar no código. `Related Documentation`
   fornece a rota de leitura por pergunta. Um agente não deve precisar varrer o
   repositório inteiro para descobrir o próximo documento.

6. Resolva os metadados sem transformar ausência em certeza.

   - `Owner`: use governança, CODEOWNERS ou decisão do usuário; caso contrário,
     use `Unassigned` e mantenha `Status: Draft`.
   - `Last reviewed`: use a data real da inspeção no formato `YYYY-MM-DD`.
   - `Status`: preserve status confirmado; sem vocabulário ou aprovação, use
     `Draft`.
   - `Knowledge class`: use a taxonomia documentada; sem ela, use `Agent policy`.

7. Materialize o template e preencha cada contrato.

   Para arquivo novo, gere o scaffold sem sobrescrever destino existente:

   ```bash
   python3 <skill-directory>/scripts/init_agents_md.py --output <path/to/AGENTS.md>
   ```

   Para arquivo existente, não rode o scaffolder. Edite o documento preservando
   as regras válidas. Em ambos os casos:

   - mantenha os headings, metadados, tabelas e política completa do template;
   - remova todo comentário `AGENTS_AUTHOR` após resolver a instrução;
   - escreva missão, boundaries, entradas, saídas, consumidores e invariantes;
   - inclua somente métricas adotadas; sem metas, use `Not documented` e Draft;
   - descreva runtime, componentes, fluxo, gates, ownership e rota de navegação;
   - liste superfícies de configuração, variáveis públicas e comandos oficiais;
   - identifique linguagem, runtime, gerenciador, frameworks e tooling com
     versões quando confirmadas;
   - ordene a documentação por progressive disclosure e por autoridade;
   - respeite o orçamento de `Proporcionalidade`: quando uma seção passar dele,
     corte o que já tem dono (manifest, CI, doc de arquitetura) e deixe um
     ponteiro. Estrutura é obrigatória; volume não é.

8. Componha `Mandatory Rules` como política de desenvolvimento forte.

   Preserve todas as regras gerais preenchidas no template. Depois acrescente
   diretivas concretas, com fonte, para:

   - idioma de chat, código, comentários, documentação e Git;
   - gerenciador de dependências, command runner e proibição de misturar managers;
   - framework e padrões arquiteturais a preservar em novas implementações;
   - formatter, lint, typecheck, testes e comando de validação oficial;
   - invariantes de dados, segurança, ownership e contratos públicos;
   - preferência de compatibilidade, migração, legado e tamanho de mudança;
   - rota inicial para questões de arquitetura, operações e testes.

   Escreva valores exatos: `Use <manager>`, `Chat = <idioma>`, `Run <comando>`.
   Não escreva “use a ferramenta adequada” quando o projeto já revela qual é.
   Não transforme detalhes efêmeros de módulos em regras globais; a política
   deve orientar decisões repetidas e apontar para o documento owner dos detalhes.

9. Preserve `Execution Policy` próxima ao baseline completo.

   - Mantenha os oito subtítulos e todos os controles concretos do template.
   - Customize nomes de boundary (`repository`/`workspace`) somente para refletir
     o escopo real.
   - Uma política superior pode fortalecer ou substituir uma regra, mas registre
     a fonte e não remova silenciosamente hard blocks, proteção de segredos,
     alinhamento, validação, segurança ou tratamento de falhas.
   - Preferências do usuário podem tornar a autonomia mais restritiva; não podem
     autorizar bypass de permissões, exposição de segredos ou ação destrutiva sem
     consentimento exato.

10. Trate conflitos e lacunas proporcionalmente.

    - Um fato ausente não bloqueia tudo: use fallback explícito, `Status: Draft`
      e reporte a decisão pendente.
    - Um conflito sobre comando oficial, segurança, ownership, idioma obrigatório,
      contrato público, gerenciador ou topologia bloqueia a claim afetada.
    - Se arquitetura não estiver suficientemente documentada, descreva somente o
      fluxo comprovado e identifique onde faltam ownership e documentação.
    - Não declare `Canonical` enquanto houver `Unassigned`, `Not documented`,
      conflito material ou política essencial não aprovada.

11. Valide estrutura, política e fidelidade.

    ```bash
    python3 <skill-directory>/scripts/validate_agents_md.py --file <path/to/AGENTS.md>
    python3 <skill-directory>/scripts/validate_agents_md.py --file <path/to/AGENTS.md> --strict-governance --format json
    ```

    Confirme também que links locais existem, comandos têm fonte, o perfil
    operacional foi materializado, a navegação chega a arquivos reais e nenhum
    segredo foi copiado. O validador estrutural não prova fidelidade factual.

12. Entregue relatório auditável.

    ```markdown
    Action: CREATED|UPDATED|REVIEWED|BLOCKED
    File: <path>
    Document status: DRAFT|READY_FOR_APPROVAL|CONFIRMED
    Operational profile: <languages; manager; framework; validation>
    Portable policy: APPLIED|STRENGTHENED
    Confirmed facts: <summary with sources>
    User preferences applied: <list or "none declared">
    Explicit unknowns: <list or "none">
    Conflicts: <list or "none">
    Validation: <command and result>
    ```

## Anti-patterns

- Produzir um inventário de pastas sem explicar fluxo, ownership ou ordem de
  leitura. Navegação precisa responder onde começar e quando abrir cada fonte.
- Escrever “siga os padrões do projeto” quando linguagem, manager, framework e
  checks já podem ser nomeados exatamente.
- Tratar preferência como fato: gostar de `pnpm` não prova que um projeto `npm`
  já migrou. Registre o conflito e separe a possível migração.
- Inferir preferência de idioma pela língua de uma única mensagem. Use decisão
  explícita para chat, código, docs e Git.
- Reduzir `Execution Policy` a frases genéricas e apagar a lista concreta de
  operações bloqueadas.
- Copiar stack, paths, métricas ou nomes de componentes de outro projeto.
- Inflar o documento além do que o repositório sustenta. Reproduzir versões do
  manifest, gates do CI ou o design que o doc de arquitetura já explica cria
  duas verdades e cobra contexto em toda sessão. Cumprir a estrutura não é
  licença para encher cada seção.
- Escolher silenciosamente entre README, manifest e CI conflitantes.
- Declarar `Canonical` apenas porque o texto foi concluído.

## Exemplos

### Caso positivo

**Entrada:** “Crie o AGENTS.md. Fale comigo em português, mantenha código e Git
em inglês, use o gerenciador já adotado e preserve o framework atual.”

**Saída esperada:** confirmar manager e framework em manifests/lockfiles/CI,
registrar os idiomas como `USER_PREFERENCE`, materializar regras exatas em
`Mandatory Rules`, mapear a navegação real e preservar a Execution Policy
completa.

### Caso negativo

**Entrada:** “Crie uma skill para padronizar documentação de API.”

**Por quê não:** o artefato pedido é outra skill; use `skill-governance`.

## Evals de trigger

Deve acionar:

- “Cria um AGENTS.md forte para este projeto.”
- “Documenta o projeto e ensina os agentes onde começar.”
- “Inclui minhas preferências de idioma, package manager e framework nas rules.”
- “Revisa a Mandatory Rules e a Execution Policy deste AGENTS.md.”
- “Meu monorepo precisa de AGENTS.md raiz e por pacote?”
- “Remove regras inventadas, mas deixa políticas de qualidade completas.”

Não deve acionar:

- “Cria uma skill com frontmatter e evals.” → `skill-governance`.
- “Qual arquitetura devo escolher?” → `architecture`.
- “Escreve um README de onboarding.” → documentação geral.
- “Troca npm por pnpm neste projeto.” → mudança de tooling, não documentação.

## Evals de workflow

### Eval A — preferências explícitas e tooling confirmado

Entrada: “Crie o AGENTS.md deste projeto. Chat em português; código, docs e Git
em inglês. Use o manager e o framework já configurados.”

Assertions:

- [ ] separa `USER_PREFERENCE` de `REPO_FACT`;
- [ ] nomeia idiomas, manager, framework e comando oficial sem frases genéricas;
- [ ] `Mandatory Rules` contém regras concretas para os quatro itens;
- [ ] `Execution Policy` preserva os oito subtítulos e os hard blocks concretos;
- [ ] o mapa de navegação aponta apenas para caminhos existentes;
- [ ] o validador normal termina com código 0.

### Eval B — preferência incompatível com o repositório

Entrada: “Eu prefiro pnpm, então documente pnpm”, em projeto cujo manifest,
lockfile e CI confirmam outro manager e não existe migração aplicada.

Assertions:

- [ ] registra a preferência e o estado real separadamente;
- [ ] classifica a adoção imediata como `CONFLICT`;
- [ ] não escreve pnpm como comando atual;
- [ ] mantém `Status: Draft` e relata que migração é uma mudança separada.

### Eval C — monorepo com navegação e políticas locais

Entrada: “Crie instruções para um monorepo com stacks e comandos diferentes em
dois serviços, mas com a mesma política de qualidade.”

Assertions:

- [ ] o root contém política transversal, mapa macro e comandos globais;
- [ ] arquivos locais registram somente diferenças de stack, commands e riscos;
- [ ] cada serviço tem entrypoint e rota de documentação comprovados;
- [ ] a política geral não é duplicada em cada subárvore;
- [ ] todos os arquivos produzidos passam no validador normal.
