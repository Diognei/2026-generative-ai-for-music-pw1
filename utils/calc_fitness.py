#!/usr/bin/env python3
"""
run_fitness.py

Calcula a fitness (similaridade com os indivíduos de referência) de um
indivíduo salvo em JSON, sem precisar rodar o algoritmo genético.

Uso:
    python3 run_fitness.py <input_json> [opções]

Opções:
    --refs PASTA   pasta com os .json de referência
                   (padrão: ./data/preproc)
    --limite N     máximo de referências usadas (padrão: MAX_REFS do fitness.py)
    --sim          lista a similaridade com CADA referência, da melhor para
                   a pior
    --json         imprime o resultado em JSON, para usar em outros scripts

Exemplos:
    python3 run_fitness.py data/preproc/ref_000_0000.0-0010.0s.json
    python3 run_fitness.py meu_individuo.json --sim
    python3 run_fitness.py meu_individuo.json --json

O .json de entrada deve ter o formato gerado por utils/generate_refs.py,
ou seja, com as chaves "piano" e "drums" (listas de pitches por passo).

Bibliotecas: o módulo ga/fitness.py + biblioteca padrão do Python.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# O módulo de fitness fica em ga/ e usa imports "flat", então a pasta
# precisa estar no sys.path.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
GA_DIR = PROJECT_ROOT / "ga"

if str(GA_DIR) not in sys.path:
    sys.path.insert(0, str(GA_DIR))

from fitness import (  # noqa: E402
    MAX_REFS,
    REFS_DIR,
    WEIGHTS,
    compare,
    describe,
    fitness_breakdown,
    load_references,
    reference_files,
    reset_references,
)


# ============================================================
# ARGUMENTOS
# ============================================================

def parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Calcula a fitness de um indivíduo salvo em JSON.",
    )

    parser.add_argument(
        "input_json",
        help="arquivo .json do indivíduo",
    )
    parser.add_argument(
        "--refs",
        default=None,
        help=f"pasta de referências (padrão: {REFS_DIR})",
    )
    parser.add_argument(
        "--limite",
        type=int,
        default=MAX_REFS,
        help=f"máximo de referências (padrão: {MAX_REFS})",
    )
    parser.add_argument(
        "--sim",
        action="store_true",
        help="lista a similaridade com cada referência",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="as_json",
        help="imprime o resultado em JSON",
    )

    return parser.parse_args(argv[1:])


def load_individual(path: Path) -> dict:
    """Lê o .json do indivíduo no formato piano/drums."""
    with open(path, "r", encoding="utf-8") as file:
        data = json.load(file)

    return {
        "piano": data.get("piano", []),
        "drums": data.get("drums", []),
    }


def score_against_references(individual, refs_dir, limit):
    """
    Similaridade do indivíduo contra cada referência.

    Devolve uma lista de (nome_do_arquivo, score, parcelas) ordenada da
    maior para a menor similaridade.
    """
    references = load_references(refs_dir, limit)

    profile = describe(individual["piano"], individual["drums"])

    rows = []

    for reference in references:
        similarities = compare(profile, reference)

        score = sum(
            WEIGHTS[name] * similarities[name] for name in WEIGHTS
        )

        rows.append((
            reference.get("fonte", "(sem nome)"),
            score,
            similarities,
        ))

    rows.sort(key=lambda row: -row[1])

    return rows


# ============================================================
# SAÍDA
# ============================================================

def print_human(path: Path, result: dict, rows: list) -> None:
    print("=" * 62)
    print(f"Fitness de: {path}")
    print("=" * 62)

    diagnostics = result.get("diagnostics", {})

    if not diagnostics:
        print("  Nenhuma referência foi carregada.")
        print("  Rode utils/generate_refs.py para gerar ./data/preproc/*.json")
        print()
        return

    print(f"  referências usadas : {diagnostics['referencias']}")
    print(f"  notas / passos     : "
          f"{diagnostics['notas']} / {diagnostics['passos']}")
    print(f"  densidade          : "
          f"{diagnostics['densidade_notas_s']} notas/s")

    print()
    print(f"  {'parcela':<10} {'valor':>8} {'peso':>6} {'contribuição':>14}")

    for name in WEIGHTS:
        weight = WEIGHTS[name]
        value = result[name]
        print(f"  {name:<10} {value:>8.4f} {weight:>6.2f} {weight * value:>14.4f}")

    print()
    print(f"  FITNESS = {result['fitness']:.4f}")
    print(f"  melhor referência  : {diagnostics['melhor_referencia']} "
          f"({diagnostics['similaridade_melhor_ref']:.4f})")

    if rows:
        print()
        print("  melhores referências:")
        for name, score, _ in rows[:5]:
            print(f"    {name:<36} {score:.4f}")

    print()


def print_all_similarities(rows: list) -> None:
    """Lista todas as referências, da mais similar para a menos."""
    print("  todas as referências (da melhor para a pior):")

    for name, score, similarities in rows:
        detail = "  ".join(
            f"{key}={similarities[key]:.3f}" for key in WEIGHTS
        )
        print(f"    {name:<36} {score:.4f}  {detail}")

    print()


def print_json(path: Path, result: dict, rows: list) -> None:
    """Saída em JSON, para consumo por outros scripts."""
    output = {"arquivo": str(path), **result}

    if rows:
        output["similaridades"] = [
            {"referencia": name, "score": round(score, 6)}
            for name, score, _ in rows
        ]

    print(json.dumps(output, ensure_ascii=False, indent=2))


# ============================================================
# MAIN
# ============================================================

def main(argv) -> int:
    args = parse_args(argv)

    path = Path(args.input_json).expanduser()

    if not path.is_file():
        print(f"Erro: arquivo não encontrado: {path}", file=sys.stderr)
        return 1

    try:
        individual = load_individual(path)
    except Exception as exc:  # noqa: BLE001
        print(f"Erro ao ler '{path}': {exc}", file=sys.stderr)
        return 1

    if not individual["piano"] and not individual["drums"]:
        print(f"Aviso: '{path.name}' não tem notas em piano nem drums.",
              file=sys.stderr)

    if not reference_files(args.refs, args.limite):
        print(f"Aviso: nenhum .json de referência em "
              f"{args.refs or REFS_DIR}. Rode utils/generate_refs.py.",
              file=sys.stderr)

    # Garante que as opções --refs/--limite sejam respeitadas
    reset_references()

    result = fitness_breakdown(individual, args.refs, args.limite)

    rows = (
        score_against_references(individual, args.refs, args.limite)
        if args.sim else []
    )

    if args.as_json:
        print_json(path, result, rows)
    else:
        print_human(path, result, rows)

        if rows:
            print_all_similarities(rows)

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))