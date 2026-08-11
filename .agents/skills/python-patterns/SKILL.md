---
name: python-patterns
description: >
  Use para implementar, refatorar ou revisar Python idiomático quando o problema
  central for typing, async/I/O, validação, Pydantic vs dataclass, serialização,
  tradução de exceções ou lifecycle de recursos. Ative com "tipa essa função",
  "async está bloqueando", "como trato esse erro sem engolir exceção?", "model
  Pydantic estranho", "JSON sai errado", "esse with faz sentido?" ou "refatora
  esse Python". Não use para schema de banco, API HTTP, E2E de browser,
  performance/query Polars ou debugging amplo cuja causa raiz ainda é incerta.
---

# Python Patterns

## Contexto nao-obvio

Problemas de Python quase sempre aparecem na fronteira errada: dado externo entrando
sem validacao, corrotina chamando API bloqueante, excecao de infraestrutura vazando
como erro de dominio, objeto interno vazando cru para JSON, ou tipagem espalhada em
detalhes locais enquanto o contrato publico continua ambiguo. A skill existe para
forcar a escolha do boundary certo antes de refatorar.

## Procedimento

1. Identifique a fronteira dominante: contrato publico, entrada externa, caminho
   async, ciclo de vida de recurso, ou traducao de erro. Corrigir o sintoma sem
   localizar a fronteira costuma espalhar regra pelo lugar errado.
2. Classifique o problema principal em uma categoria: typing, validacao,
   async/I/O, modelagem de dados, exceptions, ou cleanup de recurso. Nao tente
   resolver tudo com a mesma ferramenta.
3. Confirme a versao de Python e as bibliotecas ja adotadas pelo repositorio antes
   de sugerir sintaxe ou recurso novo. Consulte a configuracao real do projeto
   (`pyproject.toml`, lockfile, container, CI ou runtime declarado) e use o executor
   ja adotado pelo projeto. `X | None`, `TaskGroup`, `Self` ou Pydantic v2 so ajudam
   quando o runtime real suporta isso.
4. Tipa primeiro o contrato que cruza modulo, camada ou boundary externo. Tipar
   apenas variavel local obvia gera ruido; deixar funcao publica sem contrato gera
   regressao silenciosa.
5. Valide dados na entrada e modele a saida na borda certa, nao no miolo da regra de
   negocio. Escolha a ferramenta pela natureza do dado: Pydantic para dado externo
   ou DTO de saida, dataclass para estrutura interna simples, `TypedDict` quando o
   objeto continua sendo um dicionario, `Protocol` quando a fronteira e
   comportamental.
6. Em caminhos async, percorra a call stack inteira antes de editar. Uma coroutine
   que chama `requests`, `time.sleep`, cliente sync de banco ou parser pesado ainda
   bloqueia, mesmo com `async def`.
7. Trate excecoes por significado. Capture excecao especifica, traduza erro externo
   na borda apropriada, preserve causalidade com `raise ... from exc` quando fizer
   traducao, e so use `except Exception` quando houver logging, contexto e re-raise
   consciente.
8. Garanta lifecycle explicito para recursos. Arquivo, conexao, lock, sessao HTTP e
   stream devem ter ownership claro via `with`, `async with` ou objeto que fecha no
   lugar certo.
9. Valide no comportamento alterado: teste focado, comando do entrypoint ou fluxo
   que exercita serializacao, concorrencia ou tratamento de erro real, incluindo caso
   feliz e falha representativa. Para mudancas em um projeto existente, use os
   gates nativos: teste focado, lint/format, typecheck, smoke do entrypoint ou CI
   local equivalente, conforme o risco.

## Heuristicas de decisao

- Prefira stdlib e padroes ja presentes no projeto antes de introduzir mais uma
  camada de abstracao. Em Python, dependencia nova costuma custar mais em operacao
  do que no primeiro diff.
- Use `Pydantic` quando o dado vem de fora do modulo: HTTP, fila, env, arquivo,
  banco desserializado, ou integracao. Para estruturas internas simples e estaveis,
  `dataclass` costuma ser suficiente e mais leve.
- Use `dataclass` quando as invariantes ja sao garantidas por outra borda e o valor
  principal e legibilidade, imutabilidade opcional e semantica de estrutura. Se voce
  precisa coercao, validacao forte ou serializacao controlada na borda, provavelmente
  quer `Pydantic`, nao mais decoradores na `dataclass`.
- Use `TypedDict` quando o codigo precisa continuar falando em dicts por contrato ou
  interoperabilidade. Converter tudo em classe so para "ter tipos" pode aumentar o
  acoplamento sem ganho real.
- Use `Protocol` quando varias implementacoes compartilham comportamento e o caller
  nao precisa conhecer a classe concreta. Isso preserva duck typing sem abrir mao de
  contrato.
- Em boundaries JSON, fila ou cache, prefira schema/DTO explicito em vez de devolver
  objeto de ORM, entidade de dominio ou `dict` ad-hoc. Serializacao incidental tende
  a quebrar com `datetime`, `Decimal`, `UUID` e campos opcionais.
- `Any` e aceitavel na borda com biblioteca sem stubs ou payload altamente dinamico,
  desde que o tipo seja refinado antes de entrar no dominio. `Any` permanente no
  core apaga o valor da tipagem.
- Paralelize apenas I/O independente. `asyncio.gather` ou equivalente nao corrige
  CPU-bound, nao resolve dependencia de ordem e pode piorar observabilidade.
- Se a regra principal e "nao esquecer de fechar", um context manager explicito e
  melhor do que lembrar manualmente de chamar `.close()` em varios returns.
- Quando traduzir erro externo para erro de dominio, preserve a causa original e
  remova segredo, token ou payload sensivel do log. Perder a cadeia causal dificulta
  debug; vazar dado sensivel piora a operacao.
- Se o sintoma for lentidao em `LazyFrame`, plano de query, `collect`, join Polars
  ou consumo de memoria em parquet/csv grande, resolva primeiro com
  `polars-optimization`. Tipagem Python pode ajudar a borda, mas nao substitui
  inspecao do plano.

## Anti-patterns a evitar

- Marcar funcao como `async` e continuar usando `requests`, `time.sleep`,
  `subprocess.run` bloqueante ou cliente sync no caminho quente.
- Capturar `Exception` e devolver `None`, `False` ou string generica sem preservar a
  causa real.
- Introduzir `Pydantic` em toda camada interna quando o problema e apenas estruturar
  estado em memoria.
- Serializar entidade, objeto de ORM ou excecao diretamente com `json.dumps(default=str)`
  para "fazer funcionar", escondendo contrato quebrado na borda.
- Tipar tudo com `Any` ou anotar cada local trivial enquanto o contrato publico segue
  implcito.
- Validar o mesmo payload em varias camadas com regras divergentes.
- Usar argumento mutavel padrao em lista ou dict compartilhado entre chamadas.
- Traduzir excecao externa para uma nova excecao generica sem `from`, perdendo a
  cadeia causal que explicava a falha original.
- Criar helper de cleanup manual quando `with`, `async with` ou `contextlib` ja
  resolveriam o ownership com menos risco.

## Formato de saida esperado

Quando a skill orientar uma resposta analitica, organize a conclusao em quatro
blocos curtos:

1. `Boundary`: onde o problema realmente esta.
2. `Padrao escolhido`: typing, Pydantic, dataclass, async, context manager, ou
   traducao de excecao.
3. `Por que`: risco evitado e trade-off principal.
4. `Validacao`: teste, comando ou fluxo que confirma o comportamento corrigido.

## Exemplos

### Caso positivo
**Entrada:** "Esse `async def` do FastAPI usa `requests` e a API ficou travando."
**Saida esperada:** Encontrar a chamada bloqueante no caminho async, decidir entre
cliente async, offload ou boundary sync explicito, e validar no endpoint real.

### Caso positivo
**Entrada:** "Tipa esse projeto Python sem encher de `Any`."
**Saida esperada:** Anotar contratos publicos, escolher `Protocol`, `TypedDict` ou
tipos concretos conforme a fronteira, e evitar ruido em variaveis locais obvias.

### Caso positivo
**Entrada:** "Esse model Pydantic aceita dado errado e depois quebra mais na frente."
**Saida esperada:** Mover a validacao para a entrada correta, ajustar modelo/campo ou
validator, e deixar claro por que o erro deve falhar cedo.

### Caso positivo
**Entrada:** "Meu endpoint Python retorna `datetime` e `Decimal`, e o JSON sai torto."
**Saida esperada:** Identificar a borda de serializacao, escolher DTO/schema explicito
e evitar serializacao incidental baseada em `default=str`.

### Caso negativo
**Entrada:** "Desenha a migration e os indices dessa tabela Postgres."
**Por que nao:** O foco e schema e persistencia; use `database-design`.

### Caso negativo
**Entrada:** "Revisa status code, cache e idempotencia desse endpoint."
**Por que nao:** O problema principal e contrato HTTP/API; use `api-patterns`.

### Caso negativo
**Entrada:** "Essa query Polars com `scan_parquet` e `join` estoura memoria."
**Por que nao:** O foco e plano Polars, materializacao e processamento vetorizado;
use `polars-optimization`.

## Evals de trigger

Deve acionar:
- "tipa essa funcao Python sem transformar tudo em `Any`"
- "meu `async def` usa `time.sleep` e o worker fica preso"
- "esse model Pydantic v2 esta aceitando string onde eu queria numero"
- "como trato esse erro em Python sem esconder a excecao original?"
- "isso deveria ser `dataclass`, `TypedDict` ou Pydantic?"
- "meu JSON Python com `datetime` e `Decimal` esta saindo errado"

Nao deve acionar:
- "faz a migration dessa tabela no Postgres"
- "me ajuda a escolher status code e paginacao da minha API"
- "testa esse fluxo no Playwright"
- "tem um bug intermitente estranho e eu nem sei por onde comecar"
- "otimiza esse join Polars em milhoes de linhas"

## Evals de workflow

### Cenario: caminho async ou concorrente
- [ ] output identifica a chamada bloqueante, dependencia de ordem ou gargalo real
- [ ] output nao trata `async def` como solucao suficiente por si so
- [ ] output escolhe paralelizacao apenas para operacoes independentes
- [ ] output menciona validacao no endpoint, worker ou comando que falhava

### Cenario: typing e validacao de dados
- [ ] output tipa contratos publicos antes de detalhes locais
- [ ] output escolhe entre `Pydantic`, `dataclass`, `TypedDict` ou `Protocol` com motivo
- [ ] output evita recomendar `Any` como atalho estrutural
- [ ] output deixa claro em que boundary a validacao deve acontecer

### Cenario: tratamento de erro e lifecycle
- [ ] output diferencia erro de dominio de erro de infraestrutura
- [ ] output evita `except Exception` silencioso
- [ ] output preserva causa original ao traduzir excecao ou justifica por que nao precisa
- [ ] output considera redacao de dados sensiveis em logs/erros
- [ ] output propoe `with`, `async with` ou ownership explicito para recursos
- [ ] output inclui uma forma concreta de validar a correcao

### Cenario: projeto Python com contrato publico
- [ ] output confirma a versao/bibliotecas reais antes de recomendar recurso novo
- [ ] output usa validacao nativa do projeto quando a mudanca afeta arquivos
- [ ] output nao muda contrato publico sem apontar caller, teste ou migracao afetada
