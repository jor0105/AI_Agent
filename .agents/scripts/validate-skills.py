#!/usr/bin/env python3
"""Valida todas as SKILL.md do projeto contra as regras de skill-governance/SKILL.md.

Regras verificadas (fonte canônica: .agents/skills/skill-governance/SKILL.md):
  1. Frontmatter obrigatório: campos `name` e `description`.
  2. `description` deve conter linguagem ativável (> 40 chars — suficiente para
     capturar pelo menos uma situação real, não só um título).
  3. Corpo deve começar com `# <Título>`.
  4. Corpo deve conter `## Procedimento`.
  5. Corpo deve conter `## Exemplos` com pelo menos um caso negativo
     (detectado pela presença de "Por quê não:" ou "Caso negativo").
  6. Corpo deve conter `## Evals de trigger` com "Não deve acionar"
     (near-misses obrigatórios).
  7. Corpo não deve conter `## Quando usar` (proibido no corpo — pertence à description).
  8. Corpo não deve conter palavras em maiúsculas SEMPRE ou NUNCA fora de
     blocos de código (indica proibição sem raciocínio).
  9. SKILL.md deve ter menos de 500 linhas.
 10. Skills arquivadas devem declarar `replaced_by` apontando para uma skill ativa.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess  # nosec B404
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SKILLS_ROOT = REPO_ROOT / '.agents' / 'skills'

# Subpastas que não são skills raiz — skip no glob
SKIP_PARTS = {
    '__pycache__',
    'references',
    'assets',
    'scripts',
    'templates',
    'schemas',
    'data',
}

# Mínimo de chars na description para garantir que cobre pelo menos uma situação real
DESCRIPTION_MIN_CHARS = 40

# Limite de linhas do SKILL.md (regra explícita em SKILL.md l.65)
LINE_LIMIT = 500

# Limite de linhas dos arquivos em references/ (regra explícita em SKILL.md l.67)
REFERENCE_LINE_WARN = 300
ALLOWED_ACTIVE_FRONTMATTER = {'name', 'description'}
ALLOWED_ARCHIVED_FRONTMATTER = {'name', 'description', 'status', 'replaced_by'}


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------


def _parse_frontmatter_block(text: str) -> tuple[str, str]:
    """Retorna (bloco_yaml_raw, restante_do_corpo). Lança ValueError se ausente."""
    m = re.match(r'---\r?\n(.*?)\r?\n---\r?\n', text, re.S)
    if not m:
        raise ValueError(
            'frontmatter ausente ou malformado (esperado --- ... ---)'
        )
    return m.group(1), text[m.end() :]


def _parse_frontmatter(raw_block: str) -> dict[str, object]:
    """Parser mínimo de YAML plano — chaves de primeiro nível apenas."""
    meta: dict[str, object] = {}
    # Acumula blocos de string literal `>` (multiline folded)
    current_key: str | None = None
    current_lines: list[str] = []

    def flush() -> None:
        if current_key is not None:
            meta[current_key] = ' '.join(current_lines).strip()

    for line in raw_block.splitlines():
        if line.startswith((' ', '\t')) and current_key:
            # Continuação de bloco folded
            current_lines.append(line.strip())
            continue

        flush()
        current_key, current_lines = None, []

        if not line.strip() or ':' not in line:
            continue

        key, _, raw_value = line.partition(':')
        key = key.strip()
        val = raw_value.strip().strip('"\'')

        if val == '>':
            # Bloco folded — próximas linhas indentadas são o valor
            current_key = key
        elif val.startswith('[') and val.endswith(']'):
            inner = val[1:-1].strip()
            meta[key] = (
                [i.strip().strip('"\'') for i in inner.split(',') if i.strip()]
                if inner
                else []
            )
        else:
            meta[key] = val

    flush()
    return meta


# ---------------------------------------------------------------------------
# Descoberta
# ---------------------------------------------------------------------------


def _iter_skill_files() -> list[Path]:
    files: list[Path] = []
    for path in SKILLS_ROOT.rglob('SKILL.md'):
        parts = path.relative_to(SKILLS_ROOT).parts
        if any(p in SKIP_PARTS for p in parts):
            continue
        files.append(path)
    return sorted(files)


def _strip_code_blocks(text: str) -> str:
    """Remove blocos ```...``` para não checar regras de estilo dentro de exemplos."""
    return re.sub(r'```.*?```', '', text, flags=re.S)


# ---------------------------------------------------------------------------
# Validações individuais
# ---------------------------------------------------------------------------


def _check_frontmatter(
    path: Path, meta: dict[str, object], errors: list[str]
) -> None:
    name = meta.get('name', '')
    if not name:
        errors.append(f"{path}: frontmatter: campo 'name' ausente ou vazio")

    description = meta.get('description', '')
    if (
        not isinstance(description, str)
        or len(description.strip()) < DESCRIPTION_MIN_CHARS
    ):
        errors.append(
            f"{path}: frontmatter: 'description' muito curta ({len(str(description).strip())} chars). "
            f'Deve capturar pelo menos uma situação real com linguagem casual (mín. {DESCRIPTION_MIN_CHARS} chars).'
        )


def _check_frontmatter_contract(
    path: Path, meta: dict[str, object], errors: list[str]
) -> None:
    status = str(meta.get('status', 'active')).strip()
    allowed = (
        ALLOWED_ARCHIVED_FRONTMATTER
        if status == 'archived'
        else ALLOWED_ACTIVE_FRONTMATTER
    )
    extras = sorted(set(meta) - allowed)
    if extras:
        errors.append(
            f'{path}: frontmatter contém chaves extras fora do contrato mínimo da skill-governance: {extras}'
        )


def _check_body_structure(path: Path, body: str, errors: list[str]) -> None:
    stripped = body.lstrip()

    # Regra 3: começa com # Título
    if not stripped.startswith('# '):
        errors.append(
            f"{path}: corpo deve começar com '# <Título>' (nível H1)"
        )

    # Regra 4: ## Procedimento obrigatório
    if not re.search(r'^## Procedimento\s*$', body, re.M):
        errors.append(f"{path}: corpo deve conter seção '## Procedimento'")

    # Regra 5: ## Exemplos + caso negativo
    if not re.search(r'^## Exemplos\s*$', body, re.M):
        errors.append(f"{path}: corpo deve conter seção '## Exemplos'")
    elif not re.search(r'Por qu[eê] não|Caso negativo|caso negativo', body):
        errors.append(
            f"{path}: '## Exemplos' deve conter pelo menos um caso negativo ('Por quê não:' ou 'Caso negativo')"
        )

    # Regra 6: ## Evals de trigger + near-misses
    if not re.search(r'^## Evals de trigger\s*$', body, re.M):
        errors.append(f"{path}: corpo deve conter seção '## Evals de trigger'")
    elif not re.search(r'[Nn]ão deve acionar|Nao deve acionar', body):
        errors.append(
            f"{path}: '## Evals de trigger' deve conter 'Não deve acionar' (near-misses obrigatórios)"
        )

    # Regra 7: proibido ## Quando usar no corpo
    if re.search(r'^## Quando usar\s*$', body, re.M):
        errors.append(
            f"{path}: seção '## Quando usar' proibida no corpo — esse conteúdo pertence à 'description' no frontmatter"
        )


def _check_style(path: Path, body: str, errors: list[str]) -> None:
    """Regra 8: SEMPRE/NUNCA em maiúsculas fora de blocos de código.

    Linhas que citam as próprias palavras proibidas como exemplo de anti-pattern
    (ex: "escrevendo SEMPRE ou NUNCA em maiúsculas") são excluídas da checagem
    para não penalizar skills que ensinam essa regra.
    """
    clean = _strip_code_blocks(body)
    # Remove linhas que são meta-explicações da própria regra
    filtered_lines = [
        line
        for line in clean.splitlines()
        if not re.search(
            r'escrevendo\s+SEMPRE|SEMPRE\s+ou\s+NUNCA|\"SEMPRE\"|\"NUNCA\"',
            line,
        )
    ]
    filtered = '\n'.join(filtered_lines)
    if re.search(r'\bSEMPRE\b|\bNUNCA\b', filtered):
        errors.append(
            f"{path}: uso de 'SEMPRE' ou 'NUNCA' em maiúsculas detectado fora de blocos de código. "
            'Prefira explicar o raciocínio por trás da restrição.'
        )


def _check_size(path: Path, text: str, errors: list[str]) -> None:
    """Regra 9: limite de 500 linhas."""
    count = len(text.splitlines())
    if count > LINE_LIMIT:
        errors.append(
            f'{path}: {count} linhas — limite é {LINE_LIMIT}. '
            'Extraia seções para references/ com ponteiros de quando ler cada arquivo.'
        )


def _check_references_size(path: Path, errors: list[str]) -> None:
    """Regra de SKILL.md l.67: references/ > 300 linhas devem ter sumário no topo."""
    refs_dir = path.parent / 'references'
    if not refs_dir.is_dir():
        return
    for ref in refs_dir.glob('*.md'):
        lines = ref.read_text(encoding='utf-8').splitlines()
        if len(lines) > REFERENCE_LINE_WARN:
            # Sumário = presença de ## ou lista de tópicos nas primeiras 10 linhas
            header = '\n'.join(lines[:10])
            if not re.search(r'^##|^-\s+\[', header, re.M):
                errors.append(
                    f'{ref}: arquivo em references/ tem {len(lines)} linhas mas falta sumário nas primeiras 10 linhas'
                )


def _check_archived(
    path: Path,
    meta: dict[str, object],
    active_names: set[str],
    errors: list[str],
) -> None:
    """Regra 10: skill arquivada deve declarar replaced_by apontando para skill ativa."""
    replaced_by = str(meta.get('replaced_by', '')).strip()
    if not replaced_by:
        errors.append(
            f"{path}: skill arquivada deve declarar 'replaced_by' no frontmatter"
        )
    elif replaced_by not in active_names:
        errors.append(
            f"{path}: 'replaced_by: {replaced_by}' aponta para skill inexistente ou também arquivada"
        )


def _check_path_refs(path: Path, text: str, errors: list[str]) -> None:
    """Verifica que referências de caminho no corpo apontam para arquivos existentes."""
    absolute_refs = re.findall(
        r'\.agents/(?:skills|scripts)/[A-Za-z0-9._\-/]+\.(?:py|sh|md|json)',
        text,
    )
    relative_refs = re.findall(
        r'(?<![A-Za-z0-9._\-/])(?:scripts|references|assets|templates|schemas|data)/[A-Za-z0-9._\-/]+(?:\.[A-Za-z0-9._-]+)?',
        text,
    )

    errors.extend(
        f'{path}: referência de caminho não existe: {ref}'
        for ref in absolute_refs
        if not (REPO_ROOT / ref).exists()
    )
    errors.extend(
        f'{path}: referência relativa não existe na pasta da skill: {ref}'
        for ref in relative_refs
        if not (path.parent / ref).exists()
    )


def _check_skill_specific_contracts(path: Path, errors: list[str]) -> None:
    """Run bundled validators for skills with protocol-specific contracts."""
    if path.parent.name != 'openspec-workflow':
        return

    script = path.parent / 'scripts' / 'check_opsx_alignment.sh'
    if not script.exists():
        errors.append(f'{path}: validador específico ausente: {script}')
        return

    bash_path = shutil.which('bash')
    if not bash_path:
        errors.append(f'{path}: bash não encontrado no PATH')
        return

    result = subprocess.run(  # nosec B603
        [bash_path, str(script)],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()
        errors.append(
            f'{path}: falha no contrato OPSX ({script.name}): {detail}'
        )


# ---------------------------------------------------------------------------
# Validação de uma skill
# ---------------------------------------------------------------------------


def validate_skill(path: Path, active_names: set[str]) -> list[str]:
    errors: list[str] = []
    text = path.read_text(encoding='utf-8')

    try:
        raw_block, body = _parse_frontmatter_block(text)
        meta = _parse_frontmatter(raw_block)
    except ValueError as exc:
        return [f'{path}: {exc}']

    status = str(meta.get('status', 'active')).strip()

    _check_frontmatter(path, meta, errors)
    _check_frontmatter_contract(path, meta, errors)

    if status == 'archived':
        _check_archived(path, meta, active_names, errors)
        return errors  # skill arquivada não precisa das demais regras de corpo

    _check_body_structure(path, body, errors)
    _check_style(path, body, errors)
    _check_size(path, text, errors)
    _check_references_size(path, errors)
    _check_path_refs(path, text, errors)
    _check_skill_specific_contracts(path, errors)

    return errors


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(
        description='Valida SKILL.md contra as regras de skill-governance/SKILL.md.'
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='Valida todas as skills descobertas.',
    )
    parser.add_argument(
        '--skill',
        metavar='NOME',
        help='Valida uma skill pelo nome da pasta (ex: python-patterns).',
    )
    args = parser.parse_args()

    if not args.all and not args.skill:
        args.all = True

    all_files = _iter_skill_files()

    # Coleta nomes de skills ativas para validar replaced_by
    active_names: set[str] = set()
    for p in all_files:
        try:
            raw, _ = _parse_frontmatter_block(p.read_text(encoding='utf-8'))
            m = _parse_frontmatter(raw)
        except ValueError:
            continue
        if str(m.get('status', 'active')).strip() == 'active':
            active_names.add(str(m.get('name', p.parent.name)).strip())

    if args.skill:
        target = SKILLS_ROOT / args.skill / 'SKILL.md'
        skill_files = [target]
    else:
        skill_files = all_files

    errors: list[str] = []
    for path in skill_files:
        if not path.exists():
            errors.append(f'{path}: SKILL.md não encontrado')
            continue
        errors.extend(validate_skill(path, active_names))

    payload = {
        'status': 'ok' if not errors else 'error',
        'skills_checked': len(skill_files),
        'active_skills': len(active_names),
        'errors': errors,
    }
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == '__main__':
    raise SystemExit(main())
