#!/usr/bin/env python3
"""
filter_midi.py

Mantém somente as pistas de Piano e Bateria de um arquivo MIDI e grava o
resultado em um novo arquivo, preservando o andamento e a fórmula de
compasso originais.

Uso:
    python3 filter_midi.py <arquivo_entrada> <arquivo_saida>

Exemplo:
    python3 filter_midi.py entrada.mid saida.mid

Biblioteca: pretty_midi (recomendada pela disciplina).
"""
from __future__ import annotations

import sys
from pathlib import Path

import pretty_midi


# ============================================================
# CONFIGURAÇÃO
# ============================================================

# Rótulos (nomes das pistas) aceitos para cada instrumento.
PIANO_LABELS = {
    "piano",
    "grand piano",
    "acoustic grand piano",
    "bright acoustic piano",
    "electric grand piano",
}

DRUM_LABELS = {
    "drums",
    "drum",
    "drums 1",
    "bateria",
    "percussion",
    "percussao",
    "standard kit",
}

# Programas General MIDI tratados como piano (usados só como reserva,
# quando a pista não tem um rótulo reconhecido).
PIANO_PROGRAMS = {0, 1, 2}

KIND_NAMES = {"piano": "Piano", "drums": "Bateria"}


# ============================================================
# CLASSIFICAÇÃO DAS PISTAS
# ============================================================

def normalize(name) -> str:
    """Rótulo da pista em minúsculas e sem espaços das pontas."""
    return (name or "").strip().lower()


def classify(track) -> str | None:
    """
    Retorna "piano", "drums" ou None (pista que deve ser descartada).

    Ordem dos critérios (do mais confiável para o menos confiável):
        1. canal de percussão do MIDI (canal 10)  -> Bateria
        2. rótulo (nome) da pista                 -> Bateria / Piano
        3. programa General MIDI                  -> Piano
    """
    label = normalize(track.name)

    # 1) Percussão é sempre o canal 10 do padrão MIDI
    if track.is_drum or label in DRUM_LABELS:
        return "drums"

    # 2) Rótulo explícito da pista
    if label in PIANO_LABELS:
        return "piano"

    # 3) Reserva: programa General MIDI de piano
    if int(track.program) in PIANO_PROGRAMS:
        return "piano"

    return None


def filter_tracks(instrument):
    """
    Separa as pistas do arquivo em mantidas e descartadas.

    Retorna:
        kept    : lista de (pista, tipo)
        dropped : lista de (pista, motivo)
    """
    kept = []
    dropped = []

    for track in instrument.instruments:
        kind = classify(track)

        if kind is None:
            dropped.append((track, "sem correspondência"))
        else:
            kept.append((track, kind))

    return kept, dropped


# ============================================================
# FILTRAGEM
# ============================================================

def filter_midi(input_path: Path, output_path: Path) -> int:
    """
    Filtra as pistas de Piano e Bateria e grava o arquivo de saída.

    Retorna 0 em caso de sucesso e 1 em caso de erro.
    """
    try:
        midi = pretty_midi.PrettyMIDI(str(input_path))
    except Exception as exc:  # noqa: BLE001
        print(f"Erro ao ler '{input_path}': {exc}", file=sys.stderr)
        return 1

    kept, dropped = filter_tracks(midi)

    # ---- Relatório ------------------------------------------------------- #
    print("=" * 60)
    print(f"Entrada: {input_path}")
    print(f"Saída  : {output_path}")
    print("=" * 60)
    print(f"\nPistas na entrada: {len(midi.instruments)}")

    print("\nPistas mantidas:")
    if not kept:
        print("  (nenhuma pista de Piano ou Bateria encontrada)")

    for track, kind in kept:
        program = int(track.program)
        detail = f"programa {program}"
        if track.is_drum:
            detail += ", canal de percussão"
        print(f"  {KIND_NAMES[kind]:<8} | {track.name or '(sem rótulo)':<22} "
              f"| {detail} | {len(track.notes)} notas")

    print("\nPistas descartadas:")
    if not dropped:
        print("  (nenhuma)")

    for track, reason in dropped:
        print(f"  {track.name or '(sem rótulo)':<22} | "
              f"programa {int(track.program)} | {len(track.notes)} notas "
              f"| {reason}")

    # ---- Gravação --------------------------------------------------------- #
    # Substituir a lista de instrumentos preserva o andamento e a fórmula
    # de compasso que foram carregados do arquivo original.
    midi.instruments = [track for track, _kind in kept]

    try:
        midi.write(str(output_path))
    except Exception as exc:  # noqa: BLE001
        print(f"\nErro ao gravar '{output_path}': {exc}", file=sys.stderr)
        return 1

    n_kept_notes = sum(len(track.notes) for track, _kind in kept)
    print(f"\nResultado: {len(kept)} de {len(kept) + len(dropped)} "
          f"pistas mantidas ({n_kept_notes} notas)")
    print(f"Arquivo gravado em: {output_path}")
    print()

    if not kept:
        print("Aviso: nenhuma pista correspondeu aos filtros.", file=sys.stderr)

    return 0


# ============================================================
# MAIN
# ============================================================

def main(argv) -> int:
    if len(argv) != 3 or argv[1] in ("-h", "--help"):
        print("Uso: python3 filter_midi.py <arquivo_entrada> <arquivo_saida>")
        return 1 if len(argv) != 3 else 0

    input_path = Path(argv[1]).expanduser()
    output_path = Path(argv[2]).expanduser()

    if not input_path.is_file():
        print(f"Erro: arquivo não encontrado: {input_path}", file=sys.stderr)
        return 1

    return filter_midi(input_path, output_path)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))