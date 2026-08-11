#!/usr/bin/env bash
# bootstrap-skill.sh — cria o scaffold mínimo de uma nova skill
# Uso: bash .agents/scripts/bootstrap-skill.sh <skill-name> [base-dir]
#
# Anatomia gerada (conforme skill-governance/SKILL.md):
#   skill-name/
#   ├── SKILL.md        ← obrigatório, pré-preenchido com estrutura mínima
#   ├── scripts/        ← código executável reutilizável (opcional)
#   ├── references/     ← docs carregados sob demanda (opcional)
#   └── assets/         ← templates, fontes, ícones (opcional)
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Uso: $0 <skill-name> [base-dir]" >&2
  echo "  skill-name  nome em kebab-case (ex: minha-skill)" >&2
  echo "  base-dir    raiz do repositório (padrão: diretório atual)" >&2
  exit 1
fi

SKILL_NAME="$1"
BASE_DIR="${2:-.}"
TARGET_DIR="$BASE_DIR/.agents/skills/$SKILL_NAME"

# Validação do nome
if [[ ! "$SKILL_NAME" =~ ^[a-z0-9][a-z0-9-]*$ ]]; then
  echo "Erro: nome deve estar em kebab-case minúsculo (ex: minha-skill)." >&2
  exit 1
fi

if [[ -e "$TARGET_DIR" ]]; then
  echo "Erro: a pasta $TARGET_DIR já existe." >&2
  exit 1
fi

# Cria estrutura de pastas opcionais vazias
mkdir -p "$TARGET_DIR/scripts" "$TARGET_DIR/references" "$TARGET_DIR/assets"

# Gera SKILL.md com estrutura mínima conforme skill-governance/SKILL.md
cat > "$TARGET_DIR/SKILL.md" <<TEMPLATE
---
name: $SKILL_NAME
description: >
  [Descreva aqui: quando ativar, o que faz, variações de linguagem do usuário.
  Inclua pedidos informais e near-misses — é o único texto lido antes de disparar.]
---

# ${SKILL_NAME^}

## Procedimento

1. ...
2. ...

## Exemplos

### Caso positivo
**Entrada:** ...
**Saída esperada:** ...

### Caso negativo
**Entrada:** ...
**Por quê não:** ...

## Evals de trigger

Deve acionar:
- "[pedido formal]"
- "[pedido informal / edge case]"

Não deve acionar:
- "[near-miss — parece mas não é]"
- "[caso claramente fora do escopo]"
TEMPLATE

echo "✓ Skill criada em $TARGET_DIR"
echo ""
echo "Próximos passos:"
echo "  1. Preencha a 'description' com situações reais — é o gatilho de ativação"
echo "  2. Escreva o Procedimento com ordem que importa"
echo "  3. Adicione exemplos: positivo + negativo (obrigatório)"
echo "  4. Popule 'Evals de trigger' com near-misses, não só casos óbvios"
echo "  5. Valide: python3 .agents/scripts/validate-skills.py --skill $SKILL_NAME"
echo ""
find "$TARGET_DIR" -maxdepth 2 | sort
