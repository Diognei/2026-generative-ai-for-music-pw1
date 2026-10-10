#!/usr/bin/env python3
"""
summarize_midi.py

Exibe um resumo de um arquivo MIDI:
    - Número de trilhas (instrumentos)
    - Instrumento de cada trilha (nome General MIDI + programa; percussão = canal 10)
    - Duração total da música
    - Quantidade de compassos e duração por compasso (assumida uniforme)
    - BPM (andamentos, inclusive mudanças de tempo)

Uso:
    python summarize_midi.py <arquivo_midi>

Bibliotecas (recomendadas pela disciplina):
    - music21     : estrutura musical (compassos, andamento, duração)
    - pretty_midi : leitura das trilhas/instrumentos (programas reais do MIDI)
"""
from __future__ import annotations

import sys
from pathlib import Path

from music21 import converter
from music21 import instrument as m21instrument

import pretty_midi

DEFAULT_BPM = 90.0


# --------------------------------------------------------------------------- #
# Utilidades
# --------------------------------------------------------------------------- #
def fmt_time(seconds: float) -> str:
    """Formata segundos como MM:SS.mmm."""
    if seconds is None or seconds != seconds:  # None ou NaN
        return "n/a"
    minutes, secs = divmod(float(seconds), 60.0)
    return f"{int(minutes):02d}:{secs:06.3f}"


def build_tempo_segments(score):
    """
    Normaliza os "metronome mark boundaries" do music21 numa lista de
    segmentos (inicio_QL, fim_QL, bpm) que cobre todo o [0, highestTime].
    Assim conseguimos converter qualquer offset (QL) em segundos.
    """
    total_ql = float(score.highestTime)
    try:
        boundaries = list(score.metronomeMarkBoundaries())
    except Exception:
        boundaries = []

    raw = [(float(s), float(e), float(mm.number or DEFAULT_BPM))
           for (s, e, mm) in boundaries]
    if not raw:
        return [(0.0, total_ql, DEFAULT_BPM)], total_ql

    raw.sort()
    segments = []
    cursor = 0.0
    bpm = raw[0][2]
    for start, end, seg_bpm in raw:
        if start > cursor:                      # preenche lacunas
            segments.append((cursor, start, bpm))
        segments.append((start, end, seg_bpm))
        bpm = seg_bpm
        cursor = max(cursor, end)
    if cursor < total_ql:                       # trecho final sem andamento
        segments.append((cursor, total_ql, bpm))

    segments = [(s, e, b) for (s, e, b) in segments if e > s]
    return segments, total_ql


def offset_to_seconds(segments, offset: float) -> float:
    """Converte um offset (em QL) para segundos respeitando os andamentos."""
    seconds = 0.0
    for start, end, bpm in segments:
        if offset <= start:
            break
        seconds += (min(offset, end) - start) * (60.0 / bpm)
    return seconds


def gm_instrument_name(program: int) -> str:
    """Nome General MIDI (via music21) para um número de programa (0-127)."""
    try:
        inst = m21instrument.instrumentFromMidiProgram(int(program))
        if inst is not None:
            return inst.bestName()
    except Exception:
        pass
    return f"Programa {program}"


# --------------------------------------------------------------------------- #
# Relatório
# --------------------------------------------------------------------------- #
def summarize(midi_path: Path) -> None:
    score = converter.parse(str(midi_path))

    print("=" * 60)
    print(f"Arquivo: {midi_path}")
    print("=" * 60)

    parts = list(score.parts)

    # ---- 1) Número de trilhas/instrumentos (programas reais do MIDI) ------ #
    pm = pretty_midi.PrettyMIDI(str(midi_path))
    tracks = list(pm.instruments)

    print(f"\nNúmero de trilhas (instrumentos): {len(tracks)}")

    print("\nInstrumento de cada trilha:")
    if not tracks:
        print("  (nenhuma trilha de instrumento encontrada)")
    for idx, ins in enumerate(tracks, start=1):
        prog = int(ins.program)
        is_drum = bool(getattr(ins, "is_drum", False))
        if is_drum:
            label = "Bateria / Percussão"
            extra = f"programa MIDI {prog}, canal 10"   # canal 10 = percussão
        else:
            label = gm_instrument_name(prog)
            extra = f"programa MIDI {prog}"

        track_name = (ins.name or "").strip()
        name_txt = f" [trilha: {track_name!r}]" if track_name else ""

        print(f"  [{idx}] {label} ({extra}){name_txt} - notas: {len(ins.notes)}")

    # ---- 2) Andamentos / BPM --------------------------------------------- #
    segments, total_ql = build_tempo_segments(score)
    print("\nBPM (andamento):")
    shown = []
    for start, _end, bpm in segments:
        if not shown or shown[-1][1] != bpm:
            shown.append((start, bpm))
    for start, bpm in shown:
        secs = offset_to_seconds(segments, start)
        pos = f" (a partir de {fmt_time(secs)})" if start > 0 else ""
        print(f"  {bpm:.2f} BPM{pos}")

    # ---- 3) Duração total ------------------------------------------------- #
    total_seconds = offset_to_seconds(segments, total_ql)
    print(f"\nDuração total: {fmt_time(total_seconds)} "
          f"({total_seconds:.3f} s / {total_ql:.4g} semínimas)")

    # ---- 4) Compassos: quantidade e duração por compasso ----------------- #
    # Conta os compassos da parte com a maior grade (a grade costuma ser comum
    # a todas as partes) e assume que todos têm a mesma duração.
    n_measures = 0
    for part in parts:
        n_measures = max(n_measures,
                         len(list(part.getElementsByClass("Measure"))))

    print(f"\nNúmero de compassos: {n_measures}")
    if n_measures > 0:
        per_measure = total_seconds / n_measures
        print(f"Duração por compasso: {fmt_time(per_measure)} "
              f"({per_measure:.3f} s) [assumindo compassos de igual duração]")
    else:
        print("Duração por compasso: n/a (nenhum compasso encontrado)")

    print()


# --------------------------------------------------------------------------- #
def main(argv) -> int:
    if len(argv) != 2 or argv[1] in ("-h", "--help"):
        print("Uso: python summarize_midi.py <arquivo_midi>")
        return 1 if len(argv) != 2 else 0

    midi_path = Path(argv[1]).expanduser()
    if not midi_path.is_file():
        print(f"Erro: arquivo não encontrado: {midi_path}", file=sys.stderr)
        return 1

    try:
        summarize(midi_path)
    except Exception as exc:  # noqa: BLE001
        print(f"Erro ao processar '{midi_path}': {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
