#!/usr/bin/env python3
"""
generate_refs.py

Gera INDIVÍDUOS DE REFERÊNCIA a partir de um arquivo MIDI, usando uma
janela deslizante: cada trecho de WINDOW_SIZE segundos da música vira um
Individual (com seu Genotype) espelhando o que existe naquela janela.

Uso:
    python3 utils/generate_refs.py <arquivo_midi> [pasta_saida]

Pasta de saída padrão: ./data/preproc/

Para cada janela são gravados dois arquivos:
    ref_000_000.0-010.0s.mid   -> a janela como música (dá para rodar a fitness)
    ref_000_000.0-010.0s.json  -> o genótipo em texto (dá para comparar estrutura)

O objetivo é obter indivíduos "ideais" de referência, extraídos de música
real, para comparar com os indivíduos gerados pelo algoritmo genético.

Notas de implementação:
    - A grade de tempo é a do AG: 120 BPM com 4 passos por batida
      (semicolcheias), logo 1 passo = 0,125 s.
    - Uma janela de 10 s tem 80 passos (5 compassos). Como o Genotype do AG
      tem 240 passos (30 s), usamos uma SUBCLASSSE que só muda o tamanho,
      sem alterar o código existente do AG.
    - Cada nota entra no gene do passo em que ela COMEÇA. Se um passo
      receber mais de Gene.MAX_NOTES notas, ficam as de maior velocidade.
    - Pistas de percussão (canal 10) vão para a trilha de drums; as demais
      vão para a trilha de piano (até 5 notas por passo).

Bibliotecas: pretty_midi + os módulos do AG (genotype, individual, ...).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pretty_midi

# Os módulos do AG usam imports "flat" (from genotype import ...), então a
# pasta ga/ precisa estar no sys.path.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
GA_DIR = PROJECT_ROOT / "ga"

if str(GA_DIR) not in sys.path:
    sys.path.insert(0, str(GA_DIR))

from genotype import Gene, Genotype  # noqa: E402
from individual import Individual  # noqa: E402
from generate_midi import generate_midi  # noqa: E402


# ============================================================
# CONFIGURAÇÃO
# ============================================================

WINDOW_SIZE = 10.0     # duração da janela, em segundos
HOP_SIZE = 5.0         # avanço entre janelas (50% de sobreposição)

DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "data" / "preproc"

# Grade do AG, usada apenas como fallback quando o arquivo de entrada
# não informa andamento.
DEFAULT_BPM = Genotype.BPM
STEPS_PER_BEAT = Genotype.STEPS_PER_BEAT


def source_tempo(midi, fallback=DEFAULT_BPM) -> float:
    """
    Andamento (BPM) gravado no arquivo MIDI.

    Usar o andamento REAL da música é essencial. A grade de passos precisa
    acompanhar as subdivisões reais (semicolcheia = 60/BPM/4). Se usarmos
    um andamento fixo (o do AG, 120 BPM) para uma música em 90 BPM, cada
    nota é encaixotada numa grade incompatível e o arquivo gerado sai com
    o intervalo entre as notas variando errado.
    """
    candidates = []

    try:
        changes = midi.get_tempo_changes()

        if isinstance(changes, tuple) and len(changes) == 2:
            candidates = list(changes[1])
    except Exception:
        candidates = []

    for value in candidates:
        try:
            value = float(value)
        except (TypeError, ValueError):
            continue

        if value > 0:
            return value

    return fallback


class ReferenceGenotype(Genotype):
    """
    Genotype de uma janela de referência, com tamanho configurável.

    O número de passos depende do andamento da música de origem: uma janela
    de 10 s tem 80 passos a 120 BPM, mas 60 passos a 90 BPM.
    """

    def __init__(self, piano=None, drums=None, steps=None):
        if steps is not None:
            self.STEPS = int(steps)

        super().__init__(piano=piano, drums=drums)


# ============================================================
# EXTRAÇÃO DAS JANELAS
# ============================================================

def build_windows(total_duration: float) -> list:
    """
    Devolve a lista de janelas (inicio, fim) cobrindo a música.

    Só entram janelas completas. Se sobrar um trecho no final com pelo menos
    metade de uma janela, ele vira uma última janela ancorada no fim.
    """
    windows = []

    start = 0.0
    while start + WINDOW_SIZE <= total_duration:
        windows.append((start, start + WINDOW_SIZE))
        start += HOP_SIZE

    # A sobra é medida a partir do FIM da última janela (e não do início),
    # senão uma janela final seria duplicada.
    last_end = windows[-1][1] if windows else 0.0
    remainder = total_duration - last_end

    if windows and remainder >= WINDOW_SIZE / 2:
        windows.append((total_duration - WINDOW_SIZE, total_duration))

    return windows


def collect_notes(midi, start: float, end: float):
    """
    Separa as notas que começam dentro da janela em:
        melodic    -> pistas normais (piano, cordas, ...)
        percussive -> pistas de percussão

    Cada nota vira a tupla (inicio, velocidade, pitch, fim).
    O fim é guardado para conseguir reconstruir a duração da nota.
    """
    melodic = []
    percussive = []

    for instrument in midi.instruments:
        target = percussive if instrument.is_drum else melodic

        for note in instrument.notes:
            # inclui também as notas que atravessam a borda da janela, senão
            # uma nota longa iniciada antes ficaria de fora
            if note.start < end and note.end > start:
                target.append(
                    (note.start, note.velocity, note.pitch, note.end)
                )

    return melodic, percussive


def notes_to_individual(melodic, percussive, window_start: float,
                        n_steps: int, seconds_per_step: float) -> Individual:
    """
    Converte as notas de uma janela em um Individual.

    Cada nota é colocada no gene do passo em que começa. O passo é
    ARREDONDADO (e não truncado), senão as notas que caem no meio de um
    passo seriam deslocadas para o passo anterior e o intervalo entre elas
    sairia irregular.

    Quando um passo recebe mais de Gene.MAX_NOTES notas, ficam as de maior
    velocidade.

    A duração original de cada nota também é preservada, em passos e entre
    Gene.MIN_DURATION e Gene.MAX_DURATION. Sem isso a referência seria
    tudo picotado enquanto o AG pode sustentar notas, e a comparação
    entre os dois perderia o sentido.
    """
    piano = [Gene() for _ in range(n_steps)]
    drums = [Gene() for _ in range(n_steps)]

    for notes, grid in ((melodic, piano), (percussive, drums)):
        buckets = {}

        for note_start, velocity, pitch, note_end in notes:
            index = round((note_start - window_start) / seconds_per_step)

            # notas que começaram antes da janela entram no primeiro passo
            index = min(max(index, 0), n_steps - 1)

            length = round((note_end - note_start) / seconds_per_step)

            length = min(
                max(length, Gene.MIN_DURATION),
                Gene.MAX_DURATION
            )

            buckets.setdefault(index, []).append((velocity, pitch, length))

        for index, items in buckets.items():
            # maior velocity primeiro; desempata pelo pitch
            items.sort(key=lambda item: (-item[0], item[1]))

            # a duração do gene vem da nota mais forte do passo
            duration = items[0][2]

            pitches = sorted({
                pitch for _v, pitch, _l in items[:Gene.MAX_NOTES]
            })

            grid[index] = Gene(pitches, duration=duration)

    return Individual(
        ReferenceGenotype(piano=piano, drums=drums, steps=n_steps)
    )


# ============================================================
# GRAVAÇÃO
# ============================================================

def window_name(index: int, start: float, end: float) -> str:
    """Nome padrão dos arquivos de uma janela."""
    return f"ref_{index:03d}_{start:06.1f}-{end:06.1f}s"


def individual_to_dict(individual, index, start, end, source,
                       bpm, n_steps, seconds_per_step) -> dict:
    """Serializa o genótipo do individual's em um dicionário JSON."""
    piano = [list(gene.notes) for gene in individual.piano]
    drums = [list(gene.notes) for gene in individual.drums]

    # As durações, em passos, ficam em listas paralelas às de notas.
    # Assim o formato antigo de "piano"/"drums" continua igual para quem
    # já consome esses JSON, e a duração vira um campo à parte.
    duracoes_piano = [gene.duration for gene in individual.piano]
    duracoes_drums = [gene.duration for gene in individual.drums]

    return {
        "origem": source,
        "janela": {
            "indice": index,
            "inicio_s": round(start, 3),
            "fim_s": round(end, 3),
            "duracao_s": round(end - start, 3),
        },
        "grade": {
            "bpm": round(bpm, 4),
            "passos_por_batida": STEPS_PER_BEAT,
            "passos_por_compasso": Genotype.STEPS_PER_BAR,
            "passos": n_steps,
            "compassos": round(n_steps / Genotype.STEPS_PER_BAR, 4),
            "segundos_por_passo": round(seconds_per_step, 6),
            "duracao_minima_passos": Gene.MIN_DURATION,
            "duracao_maxima_passos": Gene.MAX_DURATION,
        },
        "resumo": {
            "notas_piano": sum(len(notes) for notes in piano),
            "notas_drums": sum(len(notes) for notes in drums),
            "passos_com_nota_piano": sum(1 for notes in piano if notes),
            "passos_com_nota_drums": sum(1 for notes in drums if notes),
        },
        "piano": piano,
        "drums": drums,
        "duracoes_piano": duracoes_piano,
        "duracoes_drums": duracoes_drums,
    }


def save_reference(individual, index, start, end, source, output_dir,
                   bpm, n_steps, seconds_per_step):
    """
    Grava a janela como .mid (para ouvir e rodar a fitness) e como .json
    (para comparar a estrutura). Devolve (caminho_midi, dados).
    """
    name = window_name(index, start, end)

    midi_path = output_dir / f"{name}.mid"
    json_path = output_dir / f"{name}.json"

    # Grava com o andamento da música de origem: é isso que faz o arquivo
    # tocar no mesmo ritmo do original.
    generate_midi(individual, str(midi_path), bpm=bpm)

    data = individual_to_dict(
        individual, index, start, end, source,
        bpm, n_steps, seconds_per_step,
    )

    # A fitness não é gravada aqui de propósito: ela é calculada sob demanda
    # com utils/run_fitness.py, e não faria sentido avaliar uma referência
    # contra o próprio conjunto de referências.

    with open(json_path, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)

    return midi_path, data


# ============================================================
# PROCESSAMENTO
# ============================================================

def generate_references(input_path: Path, output_dir: Path) -> int:
    """Gera os indivíduos de referência e grava os arquivos."""
    try:
        midi = pretty_midi.PrettyMIDI(str(input_path))
    except Exception as exc:  # noqa: BLE001
        print(f"Erro ao ler '{input_path}': {exc}", file=sys.stderr)
        return 1

    total_duration = midi.get_end_time()

    # A grade das janelas segue o andamento REAL da música de origem.
    bpm = source_tempo(midi)
    seconds_per_step = (60.0 / bpm) / STEPS_PER_BEAT

    print("=" * 60)
    print(f"Entrada : {input_path}")
    print(f"Saída   : {output_dir}")
    print(f"Duração : {total_duration:.2f} s")
    print(f"Andamento: {bpm:.2f} BPM "
          f"({seconds_per_step:.4f} s por semicolcheia)")
    print(f"Janela  : {WINDOW_SIZE:.1f} s")
    print(f"Avanço  : {HOP_SIZE:.1f} s")
    print("=" * 60)

    if total_duration <= 0:
        print("Erro: o arquivo não contém notas.", file=sys.stderr)
        return 1

    windows = build_windows(total_duration)

    try:
        output_dir.mkdir(parents=True, exist_ok=True)
    except Exception as exc:  # noqa: BLE001
        print(f"Erro ao criar '{output_dir}': {exc}", file=sys.stderr)
        return 1

    print(f"\nJanelas geradas: {len(windows)}\n")
    print(f"{'#':>3}  {'inicio':>7}  {'fim':>7}  {'piano':>6}  "
          f"{'drums':>6}  {'passos':>7}  arquivo")

    saved = []

    for index, (start, end) in enumerate(windows):
        melodic, percussive = collect_notes(midi, start, end)

        if not melodic and not percussive:
            print(f"{index:>3}  {start:>7.1f}  {end:>7.1f}  "
                  f"(janela sem notas, ignorada)")
            continue

        # A grade da janela segue o andamento real da música: a quantidade
        # de passos varia com o BPM (10 s = 80 passos a 120 BPM, mas 60 a
        # 90 BPM).
        n_steps = max(
            1, int(round((end - start) / seconds_per_step))
        )

        individual = notes_to_individual(
            melodic, percussive, start, n_steps, seconds_per_step
        )

        midi_path, data = save_reference(
            individual, index, start, end, input_path.name, output_dir,
            bpm, n_steps, seconds_per_step,
        )

        saved.append(data)

        print(
            f"{index:>3}  {start:>7.1f}  {end:>7.1f}  "
            f"{data['resumo']['notas_piano']:>6}  "
            f"{data['resumo']['notas_drums']:>6}  "
            f"{n_steps:>7}  {midi_path.name}"
        )

    print()

    if not saved:
        print("Nenhum individual's foi gravado.", file=sys.stderr)
        return 1

    notas_piano = [d["resumo"]["notas_piano"] for d in saved]
    notas_drums = [d["resumo"]["notas_drums"] for d in saved]

    print(f"Referências gravadas em : {output_dir}")
    print(f"Total de arquivos       : {len(saved) * 2} "
          f"({len(saved)} .mid + {len(saved)} .json)")
    print(f"Grade                   : {bpm:.2f} BPM, "
          f"{seconds_per_step:.4f} s por semicolcheia")
    print(f"Notas no piano          : média "
          f"{sum(notas_piano) / len(notas_piano):.1f} por janela "
          f"(min {min(notas_piano)}, max {max(notas_piano)})")
    print(f"Notas na bateria        : média "
          f"{sum(notas_drums) / len(notas_drums):.1f} por janela "
          f"(min {min(notas_drums)}, max {max(notas_drums)})")
    print()

    return 0


# ============================================================
# MAIN
# ============================================================

def main(argv) -> int:
    if len(argv) not in (2, 3) or argv[1] in ("-h", "--help"):
        print("Uso: python3 utils/generate_refs.py <arquivo_midi> [pasta_saida]")
        return 1 if len(argv) not in (2, 3) else 0

    input_path = Path(argv[1]).expanduser()

    if not input_path.is_file():
        print(f"Erro: arquivo não encontrado: {input_path}", file=sys.stderr)
        return 1

    output_dir = (
        Path(argv[2]).expanduser() if len(argv) == 3
        else DEFAULT_OUTPUT_DIR
    )

    return generate_references(input_path, output_dir)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))