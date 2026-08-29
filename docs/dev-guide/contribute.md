# Como Contribuir

Contribua para o desenvolvimento do **Create Agents AI** seguindo as diretrizes abaixo. Toda colaboração é bem-vinda!

______________________________________________________________________

## 🚦 Requisitos para Contribuição

- Python `>=3.12,<4.0` e uv instalados
- Conhecimento básico de Clean Architecture e SOLID
- Familiaridade com Git e GitHub
- Seguir o padrão de código, testes e documentação do projeto

______________________________________________________________________

## 🛠️ Passo a Passo para Contribuir

01. **Fork** o repositório no GitHub
02. **Clone** seu fork localmente:
    ```bash
    git clone https://github.com/jordanestralioto/Create-Agents-AI.git
    cd Create-Agents-AI
    ```
03. **Crie uma branch** descritiva:
    ```bash
    git checkout -b feature/add-provider
    ```
04. **Implemente** sua melhoria ou correção seguindo os padrões do projeto
05. **Adicione ou atualize testes** que comprovem comportamento, casos de borda
    e regressões relevantes
06. **Instale e execute os checks locais:**
    ```bash
    uv sync --locked
    uv run --locked --no-sync pre-commit install --install-hooks
    uv run --locked --no-sync pre-commit run --all-files
    uv run --locked --no-sync pre-commit run --all-files --hook-stage pre-push
    uv run --locked --no-sync pytest -m 'not integration and not slow' -ra --cov
    uv run --locked --no-sync mkdocs build --strict
    ```
07. **Atualize a documentação** se necessário (ex: novos parâmetros, exemplos, etc.)
08. **Faça um commit em inglês** seguindo o padrão Conventional Commits
    (ex: `feat:`, `fix:`, `docs:`)
09. **Envie seu Pull Request (PR)** para o branch `develop` com uma descrição clara
10. Aguarde revisão e responda a eventuais comentários dos mantenedores

______________________________________________________________________

## 🧪 Testes e Gates

O comando de testes local seguro seleciona testes unitários e outros testes que
não dependem de serviços externos:

```bash
uv run --locked --no-sync pytest -m 'not integration and not slow' -ra \
    --cov
```

Testes que acessam APIs externas devem ser marcados com
`@pytest.mark.integration` e só devem ser executados com autorização explícita.
Testes marcados como `slow` também ficam fora da execução local segura. Não use
quota de OpenAI ou Ollama nos checks locais padrão.

Além dos hooks, execute os gates direcionados quando a alteração os afetar:

```bash
uv run --locked --no-sync mypy src --pretty
uv run --locked --no-sync mypy tests scripts \
    --disable-error-code no-untyped-def --pretty
uv run --locked --no-sync ruff check src tests scripts
uv run --locked --no-sync bandit -c pyproject.toml -r src -ll
uv run --locked --no-sync pip-audit --timeout 60
```

O workflow completo de CI, incluindo lockfile, segurança, qualidade, tipos,
docstrings e cobertura, está em `.github/workflows/pipeline.yml`. A
configuração local possui 44 hooks em `.pre-commit-config.yaml`: 38 hooks
`pre-commit`, 4 `pre-push`, 1 `commit-msg` e 1 `manual`.

### Política dos gates locais

Os hooks de `pre-commit` são determinísticos e consultam o índice Git quando
decidem se um commit pode prosseguir. Eles não executam `uv sync`, `uv lock`,
resolvers ou atualizadores de dependências. A sincronização do ambiente é um
passo de bootstrap explícito (`uv sync --locked`); uma mudança de dependência
é deliberada, revisada e atualiza o lockfile fora do hook.

```bash
# Only when intentionally changing dependency resolution.
uv lock
uv sync --locked
```

O `quality-gate-policy` roda quando a configuração de hooks, `.gitleaks.toml`,
`.gitleaksignore`, os workflows ou qualquer módulo de quality gate muda. Ele
exige pins imutáveis para hooks remotos, impede sincronização/resolução de
dependências nos hooks e preserva os gates essenciais. O Ruff é responsável
por lint, complexidade, `print()` e docstrings; o Bandit é responsável pela
segurança Python. Não há um gate separado de pydocstyle.

O `diff-sanity` bloqueia `print()` por padrão, inclusive em scripts e na CLI.
Uma saída legítima precisa ser autorizada pelo argumento repetível
`--allow-print-file=<path>`, sempre apontando para um arquivo exato do
repositório. Debug, stubs, supressões e comandos de bypass não podem ser
liberados por comentários. As projeções geradas do harness e seus mirrors não
recebem auto-fix; o hash staged de `.agents/` é validado pelo verificador
dedicado.

`.agents/` permanece rastreado para transportar validadores portáveis. Os
diretórios `.codex/`, `.claude/`, `.opencode/` e `.github/prompts/` são mirrors
gerados, ignorados e não fazem parte do índice. Os hooks normais não dependem
de `central-skills`. A verificação opcional do mirror central só é executada
manualmente:

```bash
uv run --locked --no-sync harness-sync --check
```

Se `central-skills` não estiver instalado, essa verificação manual fica como
`skipped`; isso não transforma uma falha de hook normal em aprovação.

O Gitleaks é a exceção intencional: ele sempre percorre todos os arquivos
rastreados, inclusive `.agents/`, com saída redigida. Uma alteração de
dependência deve ocorrer fora dos hooks de validação, usando `uv lock` e depois
`uv sync --locked` de forma deliberada. Falha de DNS ou rede no `pip-audit` é
`external_failure`, nunca aprovação.

Antes de criar o commit, revise a saída dos hooks mutadores (`ruff-check`,
`ruff-format`, `mdformat` e correções de whitespace). Faça staging por caminhos
explícitos:

```bash
git add -- path/to/changed-file.py path/to/changed-test.py
git diff --cached --check
```

Em uma árvore de trabalho suja, não use `git add .` nem `git add -A`, pois isso
pode incluir arquivos que não pertencem à alteração revisada.

O limite de linhas é validado no pre-commit pelo hook `check-max-lines`
contra o baseline de dívida técnica (`.max-lines-baseline.json`), e também pode
ser executado sob demanda para auditorias estruturais:

```bash
uv run --locked --no-sync python .agents/scripts/check-max-lines.py src tests scripts
```

O `pre-push` roda os dois escopos de mypy, os testes seguros com `--cov` e o
`pip-audit --timeout 60`. Um erro externo da auditoria de dependências (por
exemplo, rede indisponível) deve ser reportado como `external_failure`, nunca
como aprovação.

______________________________________________________________________

## ✅ Checklist de Qualidade para PR

- [ ] Código segue Clean Architecture e SOLID
- [ ] Testes automatizados cobrindo a nova funcionalidade/correção
- [ ] Documentação atualizada (código e Markdown)
- [ ] Sem warnings/lints (Ruff, yamllint, mdformat)
- [ ] Gates direcionados (mypy, Ruff, Bandit e pip-audit) executados quando aplicáveis
- [ ] Build estrito da documentação (`uv run --locked --no-sync mkdocs build --strict`) aprovado
- [ ] Commits claros e atômicos
- [ ] PR descreve claramente o que foi feito e por quê

______________________________________________________________________

## 📝 Padrão de Commits

Use mensagens de commit em inglês no padrão
[Conventional Commits](https://www.conventionalcommits.org/pt-br/v1.0.0/):

- `feat:` Nova funcionalidade
- `fix:` Correção de bug
- `docs:` Mudança apenas na documentação
- `test:` Adição/melhoria de testes
- `refactor:` Refatoração sem alterar comportamento
- `chore:` Tarefas de manutenção

Exemplo:

```bash
git commit -m "feat: add support for provider XYZ"
```

______________________________________________________________________

## 🤖 Adicionar um Provedor

1. Crie o adapter em `src/createagents/infra/adapters/nome_provedor/`.
2. Implemente a porta `ChatRepository` da aplicação.
3. Registre o provider em
   `src/createagents/infra/factories/chat_adapter_factory.py`.
4. Adicione testes em `tests/infra/adapters/`, espelhando a camada alterada.

Não coloque a lógica de seleção de provider em um caso de uso. O composition
root injeta o adapter por meio da factory.

## ⌨️ Adicionar um Comando CLI

1. Crie o handler em `src/createagents/presentation/cli/commands/`.
2. Registre-o em
   `src/createagents/presentation/cli/application/chat_cli_app.py`, no método
   `_setup_commands`.
3. Mantenha o handler específico antes do `ChatCommandHandler`, que é o
   fallback para mensagens comuns.

Consulte a [arquitetura da CLI](cli-architecture.md) para o contrato do
registry, a ordem dos handlers e o fluxo de terminal.

______________________________________________________________________

## 📚 Exemplos de Contribuição

- Adicionar nova ferramenta (Tool) customizada
- Corrigir bug em adapter de provedor
- Melhorar cobertura de testes
- Atualizar exemplos na documentação
- Sugerir melhorias de performance ou segurança

______________________________________________________________________

## 🐞 Reportar Bugs e Sugerir Melhorias

- **Dúvidas Gerais e Sugestões**: Entre em contato com o mantenedor pelo email `estraliotojordan@gmail.com`.
- **Vulnerabilidades de Segurança**: Reporte de forma privada via email seguindo nossa [Política de Segurança](https://github.com/jordanestralioto/Create-Agents-AI/blob/develop/SECURITY.md).
- Ao relatar problemas, inclua detalhes completos, passos para reprodução, logs de erro e contexto do ambiente.

______________________________________________________________________

## 📖 Dicas para Documentação

- Sempre documente novas funções, classes e parâmetros com docstrings
- Atualize os arquivos Markdown relevantes em `docs/` (ex: exemplos, API, FAQ)
- Use português claro, técnico e acessível
- Inclua exemplos de uso sempre que possível

______________________________________________________________________

## 🤝 Contato e Suporte

- Email: `estraliotojordan@gmail.com`
- GitHub: [@jordanestralioto](https://github.com/jordanestralioto)

______________________________________________________________________

**Obrigado por contribuir! Seu apoio torna o projeto melhor para toda a comunidade.**
