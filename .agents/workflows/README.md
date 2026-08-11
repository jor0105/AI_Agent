# Workflows Directory

This directory contains executable workflows, slash commands, and standard operational procedures for AI agents.

## Structure

- **Raiz (`/`)**: Workflows ativos, comandos principais (como `/audit`) e comandos do OpenSpec (`opsx-*`).
- **`archive/`**: Workflows antigos, planos pontuais que já foram executados e não são mais comandos ativos.

## Política de Espelhos

Os workflows nesta pasta são considerados a fonte canônica.
No ecossistema OpenSpec local, a skill `openspec-workflow` existe apenas para
roteamento e guardrails; ela não deve duplicar o lifecycle descrito aqui.
Para integração com outras ferramentas:

- `.github/prompts/` deve conter cópias ou links simbólicos para integração com Copilot.
- `.opencode/commands/` deve espelhar os workflows para integração com o OpenCode.
  Qualquer alteração em um workflow ativo nesta pasta deve ser replicada em seus espelhos correspondentes.
- Use `python3 .agents/scripts/sync-workflows.py` para sincronizar os espelhos locais e `python3 .agents/scripts/sync-workflows.py --check` para detectar drift sem escrever.
