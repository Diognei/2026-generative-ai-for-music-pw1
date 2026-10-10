"""
fitness.py

Função de avaliação (fitness) para indivíduos musicais.

O indivíduo atual contém:

    Individual
        └── Genotype
              ├── BatI
              ├── Bat1
              ├── Bat2
              ├── BatF
              ├── 2 BassPatterns
              ├── 2 ArpPatterns
              └── 8 MChords

Cada Gene representa uma colcheia de um compasso 4/4.

Elementos de bateria:

    0 = Kick
    1 = Snare
    2 = Closed Hi-Hat
    3 = Open Hi-Hat
    4 = Crash

A fitness é baseada em regras de teoria musical e teoria
rítmica aplicadas aos quatro padrões de bateria, aos dois
padrões de baixo, aos dois padrões de arpejo e aos oito MChords.

Os componentes principais são:

    - tempos fortes
    - backbeat
    - padrão do kick
    - regularidade do hi-hat
    - síncope
    - densidade
    - variação
    - combinações entre instrumentos
    - estrutura interna
    - padrão de baixo
    - padrão de arpejo
    - harmonia
    - diversidade harmônica moderada
    - voice leading entre voicings reais

O resultado final está no intervalo [0, 1].

Uso:

    from fitness import calculate_fitness

    fitness = calculate_fitness(individual)

Para analisar os componentes:

    from fitness import fitness_details

    details = fitness_details(individual)
"""


import math
from constants import *


# ============================================================
# UTILITÁRIOS
# ============================================================

def clamp(
    value,
    minimum=0.0,
    maximum=1.0
):
    """
    Limita um valor ao intervalo [minimum, maximum].
    """

    return max(
        minimum,
        min(maximum, value)
    )


def get_bat1(individual):
    """
    Retorna o padrão Bat1 do indivíduo.
    """

    return individual.bat1


def get_bat2(individual):
    """Retorna o padrão Bat2, usado nas seções de refrão."""

    return individual.bat2


def get_bati(individual):
    return individual.bati


def get_batf(individual):
    return individual.batf


def bass_pattern_fitness(pattern):
    """Avalia uma estrutura rítmica de baixo sem usar alturas."""

    count_score = {
        2: 0.75,
        4: 1.0,
        8: 0.70,
    }[len(pattern.notes)]
    durations = [note.duration for note in pattern.notes]
    unique_durations = len(set(durations)) / len(durations)
    variation_score = 0.5 + 0.5 * unique_durations

    return clamp(0.70 * count_score + 0.30 * variation_score)


def arp_pattern_fitness(pattern):
    """
    Avalia a estrutura rítmica de um arpejo.

    A pontuação rítmica usa:

        - quantidade de notas
        - step entre as notas

    Como as notas são distribuídas uniformemente pelo compasso,
    a quantidade de notas é suficiente para avaliar sua estrutura rítmica.
    A diferença de ordem entre arp_patt1 e arp_patt2 é avaliada separadamente.
    """

    count_score = {
        1: 0.60,
        2: 0.75,
        4: 1.00,
        8: 1.00,
        16: 0.90,
        32: 0.75,
    }[pattern.note_count]

    return clamp(count_score)


def arp_order_diversity_fitness(pattern1, pattern2):
    """Pontua a diferença entre as ordens dos dois padrões de arpejo."""

    different_positions = sum(
        first != second
        for first, second in zip(
            pattern1.note_order,
            pattern2.note_order,
        )
    )
    return different_positions / len(pattern1.note_order)


def melody_pattern_fitness(pattern):
    """Avalia qualidade melódica, rítmica e dinâmica de um padrão."""

    notes = pattern.notes
    if not notes:
        return 0.0

    target_note_count = pattern.DEFAULT_NOTE_COUNT
    count_sigma = max(target_note_count / 2.0, 1.0)
    count_score = math.exp(
        -((len(notes) - target_note_count) ** 2) / (2 * count_sigma ** 2)
    )

    pitches = [note.pitch for note in notes]
    pitch_range = max(pitches) - min(pitches)
    range_score = math.exp(
        -((pitch_range - 18) ** 2) / (2 * 12.0 ** 2)
    )

    intervals = [
        abs(current - previous)
        for previous, current in zip(pitches, pitches[1:])
    ]
    if intervals:
        interval_scores = [
            0.45 if interval == 0
            else 1.0 if interval <= 7
            else 0.80 if interval <= 12
            else 0.50 if interval <= 19
            else 0.20
            for interval in intervals
        ]
        interval_score = sum(interval_scores) / len(interval_scores)
    else:
        interval_score = 0.40

    gaps = [
        current.position - previous.position
        for previous, current in zip(notes, notes[1:])
    ]
    if gaps:
        gap_variety = len(set(gaps)) / len(gaps)
        gap_spacing = math.exp(
            -((sum(gaps) / len(gaps) - 8) ** 2) / (2 * 7.0 ** 2)
        )
        rhythm_score = 0.50 * gap_variety + 0.50 * gap_spacing
    else:
        rhythm_score = 0.40

    # Favorece durações médio-longas, mantendo valor para notas curtas
    # e sem premiar automaticamente a duração máxima.
    duration_score = sum(
        math.exp(-((note.duration - 6.5) ** 2) / (2 * 3.0 ** 2))
        for note in notes
    ) / len(notes)

    velocities = [note.velocity for note in notes]
    velocity_range = max(velocities) - min(velocities)
    dynamics_score = math.exp(
        -((velocity_range - 18) ** 2) / (2 * 15.0 ** 2)
    )

    bars_used = len({note.position // pattern.BAR_UNITS for note in notes})
    coverage_score = min(bars_used / pattern.NUM_BARS, 1.0)

    return clamp(
        0.15 * count_score
        + 0.24 * interval_score
        + 0.16 * range_score
        + 0.13 * rhythm_score
        + 0.18 * duration_score
        + 0.08 * dynamics_score
        + 0.06 * coverage_score
    )


def melody_diversity_fitness(first, second):
    """Favorece diferenças moderadas de notas, ritmo e duração entre padrões."""

    first_notes = first.notes
    second_notes = second.notes
    if not first_notes or not second_notes:
        return 0.0

    aligned_count = max(len(first_notes), len(second_notes))
    position_scale = max(first.TOTAL_UNITS, second.TOTAL_UNITS) / 2.0
    pitch_distances = []
    position_distances = []
    duration_distances = []

    for index in range(aligned_count):
        if index >= len(first_notes) or index >= len(second_notes):
            pitch_distances.append(1.0)
            position_distances.append(1.0)
            duration_distances.append(1.0)
            continue

        first_note = first_notes[index]
        second_note = second_notes[index]
        pitch_class_distance = abs(
            (first_note.pitch % 12) - (second_note.pitch % 12)
        )
        pitch_distances.append(
            min(pitch_class_distance, 12 - pitch_class_distance) / 6.0
        )
        position_distances.append(
            min(
                abs(first_note.position - second_note.position) / position_scale,
                1.0,
            )
        )
        duration_distances.append(
            min(abs(first_note.duration - second_note.duration) / 8.0, 1.0)
        )

    distance = (
        0.50 * sum(pitch_distances) / aligned_count
        + 0.35 * sum(position_distances) / aligned_count
        + 0.15 * sum(duration_distances) / aligned_count
    )

    return clamp(
        math.exp(-((distance - 0.45) ** 2) / (2 * 0.25 ** 2))
    )


def melody_rhythm_alignment_fitness(pattern, drum_pattern):
    """Compara a distribuição dos intervalos de melodia e bateria."""

    if not pattern.notes or not drum_pattern:
        return 0.0

    units_per_drum_step = pattern.BAR_UNITS / len(drum_pattern)
    drum_onsets = sorted(
        bar_index * pattern.BAR_UNITS + step * units_per_drum_step
        for bar_index in range(pattern.NUM_BARS)
        for step, gene in enumerate(drum_pattern)
        if gene.notes
    )

    if not drum_onsets:
        return 0.0

    total_units = pattern.TOTAL_UNITS
    drum_gaps = [
        following - current
        for current, following in zip(drum_onsets, drum_onsets[1:])
    ]
    drum_gaps.append(drum_onsets[0] + total_units - drum_onsets[-1])
    drum_gaps = sorted(gap for gap in drum_gaps if gap > 0)

    melody_onsets = [note.position for note in pattern.notes]
    melody_gaps = [
        following - current
        for current, following in zip(melody_onsets, melody_onsets[1:])
    ]
    melody_gaps.append(
        melody_onsets[0] + total_units - melody_onsets[-1]
    )

    melody_gaps = sorted(gap for gap in melody_gaps if gap > 0)

    if not drum_gaps or not melody_gaps:
        return 0.0

    alignment_scores = []

    for index, melody_gap in enumerate(melody_gaps):
        quantile = (index + 0.5) / len(melody_gaps)
        drum_index = min(
            int(quantile * len(drum_gaps)),
            len(drum_gaps) - 1,
        )
        drum_gap = drum_gaps[drum_index]
        alignment_scores.append(
            math.exp(
                -abs(math.log(melody_gap / drum_gap)) / 0.5
            )
        )

    return clamp(sum(alignment_scores) / len(alignment_scores))


def edge_battery_fitness(individual, track_name):
    """Avalia uma entrada/saída curta sem dar peso de seção principal."""

    track = get_bati(individual) if track_name == "bati" else get_batf(individual)
    if not track:
        return 0.0

    active_steps = sum(1 for gene in track if gene.notes)
    density = sum(len(gene.notes) for gene in track) / (
        len(track) * GENE_MAX_NOTES
    )
    density_target = 0.20 if track_name == "bati" else 0.35
    density_score = math.exp(
        -((density - density_target) ** 2) / (2 * 0.20 ** 2)
    )
    activity_score = min(active_steps / len(track), 1.0)

    return clamp(0.70 * density_score + 0.30 * activity_score)


def chorus_bat2_fitness(individual):
    """
    Avalia se Bat2 tem características de refrão.

    O refrão recebe melhor pontuação quando possui atividade suficiente,
    caixa no backbeat e mais eventos que um padrão vazio, sem exigir
    todos os steps preenchidos.
    """

    bat2 = get_bat2(individual)
    if not bat2:
        return 0.0

    total_events = sum(len(gene.notes) for gene in bat2)
    density = total_events / (len(bat2) * GENE_MAX_NOTES)
    density_score = math.exp(-((density - 0.55) ** 2) / (2 * 0.20 ** 2))

    snare_positions = {
        index
        for index, gene in enumerate(bat2)
        if SNARE in gene.notes
    }
    backbeat_score = len(snare_positions.intersection({2, 6})) / 2.0

    active_steps = sum(1 for gene in bat2 if gene.notes)
    activity_score = min(active_steps / len(bat2), 1.0)

    return clamp(
        0.45 * density_score
        + 0.35 * backbeat_score
        + 0.20 * activity_score
    )


def get_active_steps(individual):
    """
    Retorna os índices dos steps que possuem pelo menos
    um elemento de bateria.
    """

    return [
        step
        for step, gene in enumerate(
            get_bat1(individual)
        )
        if gene.notes
    ]


def step_has(gene, drum):
    """
    Verifica se um determinado instrumento está presente
    em um Gene.
    """

    return drum in gene.notes


def drum_positions(individual, drum):
    """
    Retorna os steps onde determinado instrumento aparece.

    Exemplo:

        drum_positions(individual, KICK)

    pode retornar:

        [0, 2, 4, 6]
    """

    positions = []

    for step, gene in enumerate(
        get_bat1(individual)
    ):

        if step_has(gene, drum):
            positions.append(step)

    return positions


def count_drum(individual, drum):
    """
    Retorna a quantidade de ocorrências de um instrumento.
    """

    return len(
        drum_positions(individual, drum)
    )


# ============================================================
# TEMPOS FORTES
# ============================================================

def strong_beats_fitness(individual):
    """
    Avalia a presença de eventos nos tempos fortes.

    Em um compasso 4/4 dividido em colcheias:

        Step:       0   1   2   3   4   5   6   7
                    |       |       |       |
        Tempo:      1   &   2   &   3   &   4   &

    Os steps 0, 2, 4 e 6 representam as quatro pulsações
    principais do compasso.

    Um padrão musical geralmente possui maior estabilidade
    quando alguns eventos importantes estão alinhados a
    essas pulsações.

    Não exigimos que todos os tempos fortes tenham eventos,
    pois isso eliminaria padrões sincopados.
    """

    bat1 = get_bat1(individual)

    if not bat1:
        return 0.0

    strong_steps = {0, 2, 4, 6}

    active = set(
        get_active_steps(individual)
    )

    if not active:
        return 0.0

    strong_events = len(
        active.intersection(strong_steps)
    )

    ratio = strong_events / len(active)

    target = 0.50

    sigma = 0.30

    score = math.exp(
        -(
            (ratio - target) ** 2
        ) / (
            2 * sigma ** 2
        )
    )

    return clamp(score)


# ============================================================
# BACKBEAT
# ============================================================

def backbeat_fitness(individual):
    """
    Avalia o backbeat tradicional de 4/4.

    Em um padrão de 8 colcheias:

        Step:    0  1  2  3  4  5  6  7
        Beat:    1  &  2  &  3  &  4  &

    O backbeat normalmente coloca a caixa nos tempos:

        2 -> step 2
        4 -> step 6

    Como a representação atual possui somente um compasso,
    damos maior recompensa para a presença da caixa nesses
    dois pontos.
    """

    positions = drum_positions(
        individual,
        SNARE
    )

    if not positions:
        return 0.0

    score = 0.0

    for position in positions:

        if position in (2, 6):
            score += 1.0

        elif position in (1, 3, 5, 7):
            score += 0.45

        else:
            score += 0.20

    score /= len(positions)

    count = len(positions)

    if count == 2:
        score *= 1.0

    elif count == 1:
        score *= 0.75

    elif count == 3:
        score *= 0.85

    else:
        score *= 0.60

    return clamp(score)


# ============================================================
# KICK
# ============================================================

def kick_fitness(individual):
    """
    Avalia o padrão do bumbo.

    O kick possui forte relação com a métrica.

    Posições particularmente estáveis:

        0 -> tempo 1
        2 -> tempo 2
        4 -> tempo 3
        6 -> tempo 4

    Também permitimos síncopes em posições de contratempo,
    mas com recompensa menor.

    O objetivo não é exigir um único padrão, mas favorecer
    padrões ritmicamente plausíveis.
    """

    positions = drum_positions(
        individual,
        KICK
    )

    if not positions:
        return 0.0

    score = 0.0

    for position in positions:

        if position in (0, 4):
            score += 1.0

        elif position in (2, 6):
            score += 0.90

        else:
            score += 0.55

    score /= len(positions)

    count = len(positions)

    if count <= 4:
        density_factor = 1.0

    elif count == 5:
        density_factor = 0.90

    elif count == 6:
        density_factor = 0.75

    else:
        density_factor = 0.55

    return clamp(
        score * density_factor
    )


# ============================================================
# HI-HAT
# ============================================================

def hihat_fitness(individual):
    """
    Avalia a regularidade do Closed Hi-Hat.

    Em um padrão de bateria em colcheias, o hi-hat pode
    funcionar como marcador regular da subdivisão:

        X X X X X X X X

    Também aceitamos variações, pausas e combinações
    sincopadas.

    A avaliação considera:

        - quantidade
        - regularidade
        - espaçamento
        - continuidade
    """

    positions = drum_positions(
        individual,
        CLOSED_HIHAT
    )

    if not positions:
        return 0.0

    count = len(positions)

    if count == 8:
        count_score = 1.0

    elif count == 7:
        count_score = 0.95

    elif count == 6:
        count_score = 0.90

    elif count == 5:
        count_score = 0.80

    elif count == 4:
        count_score = 0.70

    elif count == 3:
        count_score = 0.55

    elif count == 2:
        count_score = 0.35

    else:
        count_score = 0.20

    if len(positions) <= 1:

        regularity_score = 0.40

    else:

        gaps = [
            current - previous
            for previous, current
            in zip(
                positions,
                positions[1:]
            )
        ]

        regularity_score = sum(
            1.0 if gap == 1
            else 0.70 if gap == 2
            else 0.40 if gap == 3
            else 0.20
            for gap in gaps
        ) / len(gaps)

    return clamp(
        0.55 * count_score
        + 0.45 * regularity_score
    )


# ============================================================
# SÍNCOPE
# ============================================================

def syncopation_fitness(individual):
    """
    Avalia síncope rítmica.

    Em 8 colcheias, os steps:

        1, 3, 5, 7

    são os contratempos.

    Síncope é musicalmente útil, mas excesso de síncope
    pode enfraquecer a sensação métrica.

    Portanto, buscamos uma quantidade moderada.
    """

    active_steps = get_active_steps(
        individual
    )

    if not active_steps:
        return 0.0

    offbeat_steps = {
        1, 3, 5, 7
    }

    offbeats = sum(
        1
        for step in active_steps
        if step in offbeat_steps
    )

    ratio = offbeats / len(active_steps)

    target = 0.35

    sigma = 0.25

    score = math.exp(
        -(
            (ratio - target) ** 2
        ) / (
            2 * sigma ** 2
        )
    )

    return clamp(score)


# ============================================================
# DENSIDADE
# ============================================================

def density_fitness(individual):
    """
    Avalia a densidade total de eventos.

    Cada step pode conter até 3 elementos.

    Para um groove de bateria de um compasso, buscamos
    densidade moderada.

    Exemplos:

        Muito baixa:
            poucos eventos -> padrão vazio

        Muito alta:
            quase todos os steps com 3 elementos
            -> padrão excessivamente carregado
    """

    bat1 = get_bat1(individual)

    if not bat1:
        return 0.0

    total_events = sum(
        len(gene.notes)
        for gene in bat1
    )

    max_events = (
        len(bat1) * 3
    )

    if max_events == 0:
        return 0.0

    density = (
        total_events / max_events
    )

    target = 0.35

    sigma = 0.18

    score = math.exp(
        -(
            (density - target) ** 2
        ) / (
            2 * sigma ** 2
        )
    )

    return clamp(score)


# ============================================================
# VARIAÇÃO
# ============================================================

def variation_fitness(individual):
    """
    Avalia a variação entre a primeira e a segunda metade
    do compasso.

    O padrão é dividido em:

        primeira metade: steps 0-3
        segunda metade:  steps 4-7

    Queremos que as duas partes tenham alguma relação,
    mas não sejam necessariamente idênticas.

    Isso favorece pequenas variações sem destruir a
    estrutura rítmica.
    """

    bat1 = get_bat1(individual)

    if len(bat1) < 8:
        return 0.5

    first = [
        tuple(sorted(gene.notes))
        for gene in bat1[:4]
    ]

    second = [
        tuple(sorted(gene.notes))
        for gene in bat1[4:8]
    ]

    matches = sum(
        1
        for a, b in zip(first, second)
        if a == b
    )

    similarity = matches / 4.0

    target = 0.50

    sigma = 0.30

    score = math.exp(
        -(
            (similarity - target) ** 2
        ) / (
            2 * sigma ** 2
        )
    )

    return clamp(score)


# ============================================================
# ESTRUTURA
# ============================================================

def structure_fitness(individual):
    """
    Avalia a estrutura interna do padrão.

    Verifica se existem pequenos padrões repetidos entre
    os steps.

    Por exemplo:

        Kick HH | HH
        Snare   | Snare

    Padrões completamente aleatórios tendem a possuir pouca
    repetição estrutural.

    Entretanto, repetição excessiva também é penalizada.
    """

    bat1 = get_bat1(individual)

    if not bat1:
        return 0.0

    patterns = [
        tuple(sorted(gene.notes))
        for gene in bat1
    ]

    unique_patterns = len(
        set(patterns)
    )

    total_patterns = len(patterns)

    if total_patterns == 0:
        return 0.0

    diversity = (
        unique_patterns / total_patterns
    )

    target = 0.50

    sigma = 0.25

    score = math.exp(
        -(
            (diversity - target) ** 2
        ) / (
            2 * sigma ** 2
        )
    )

    return clamp(score)


# ============================================================
# COMBINAÇÃO DOS INSTRUMENTOS
# ============================================================

def combination_fitness(individual):
    """
    Avalia combinações entre os instrumentos.

    Algumas combinações são musicalmente naturais:

        Kick + Hi-Hat
        Snare + Hi-Hat
        Kick + Snare
        Kick + Snare + Hi-Hat

    Algumas combinações são menos desejáveis:

        Closed Hi-Hat + Open Hi-Hat
        Crash + Closed Hi-Hat em excesso

    O objetivo não é proibir combinações, mas evitar
    configurações pouco naturais.
    """

    bat1 = get_bat1(individual)

    if not bat1:
        return 0.0

    score = 0.0

    for gene in bat1:

        notes = set(gene.notes)

        if len(notes) == 0:
            score += 0.70
            continue

        if (
            KICK in notes
            and CLOSED_HIHAT in notes
        ):
            score += 1.00

        elif (
            SNARE in notes
            and CLOSED_HIHAT in notes
        ):
            score += 1.00

        elif (
            KICK in notes
            and SNARE in notes
        ):
            score += 0.95

        elif len(notes) == 1:
            score += 0.85

        elif len(notes) == 2:
            score += 0.90

        elif len(notes) == 3:
            score += 0.80

        else:
            score += 0.60

        if (
            CLOSED_HIHAT in notes
            and OPEN_HIHAT in notes
        ):
            score -= 0.30

        if CRASH in notes:

            if (
                KICK in notes
                or SNARE in notes
            ):
                score += 0.10

            else:
                score -= 0.05

    score /= len(bat1)

    return clamp(score)


# ============================================================
# HARMONIA
# ============================================================

def get_mchords(individual):
    """Retorna todos os MChords na ordem musical."""

    return individual.genotype.mchords


def _pitch_classes(notes):
    """Retorna as classes de altura presentes nas notas."""

    return {
        note % 12
        for note in notes
    }


def _chord_intervals(chord):
    """
    Retorna os intervalos das notas do acorde em relação à
    fundamental, normalizados em semitons.
    """

    root = chord.root

    return {
        (note - root) % 12
        for note in chord.notes
    }


def _chord_quality(chord):
    """
    Identifica aproximadamente a qualidade harmônica do acorde.

    O método não depende do nome textual de chord_type.
    A classificação é feita pelos intervalos em relação à
    fundamental.

    Retorno:

        "major"
        "minor"
        "diminished"
        "augmented"
        "other"
    """

    intervals = _chord_intervals(chord)

    has_minor_third = 3 in intervals
    has_major_third = 4 in intervals
    has_tritone = 6 in intervals
    has_augmented_fifth = 8 in intervals
    has_perfect_fifth = 7 in intervals

    if has_minor_third and has_tritone:
        return "diminished"

    if has_major_third and has_augmented_fifth:
        return "augmented"

    if has_major_third:
        return "major"

    if has_minor_third:
        return "minor"

    if has_perfect_fifth:
        return "other"

    return "other"


def chord_validity_fitness(individual):
    """
    Verifica se cada MChord corresponde a uma estrutura válida.

    A checagem é mantida na fitness para proteger a avaliação
    mesmo quando um acorde for construído ou alterado
    externamente.
    """

    scores = []

    for chord in get_mchords(individual):

        notes = tuple(chord.notes)

        intervals = MCHORD_INTERVALS.get(
            chord.chord_type,
            ()
        )

        expected_pitch_classes = {
            (
                chord.root + interval
            ) % 12

            for interval in intervals
        }

        actual_pitch_classes = {
            note % 12
            for note in notes
        }

        inversion = getattr(chord, "inversion", 0)

        inversion_valid = (
            inversion in MCHORD_INVERSIONS
            and bool(intervals)
            and inversion < len(intervals)
        )

        # O baixo (menor nota real) deve corresponder à
        # posição da inversão escolhida: a inversão muda a
        # disposição, nunca a identidade harmônica.
        bass_matches = (
            inversion_valid
            and bool(notes)
            and min(notes) % 12
            == (chord.root + intervals[inversion]) % 12
        )

        valid = (
            MCHORD_MIN_NOTES
            <= len(notes)
            <= MCHORD_MAX_NOTES

            and len(notes)
            == len(set(notes))

            and all(
                isinstance(note, int)
                for note in notes
            )

            and all(
                MCHORD_MIN_MIDI_NOTE
                <= note
                <= MCHORD_MAX_MIDI_NOTE

                for note in notes
            )

            and actual_pitch_classes
            == expected_pitch_classes

            and inversion_valid

            and bass_matches
        )

        scores.append(
            1.0 if valid else 0.0
        )

    if not scores:
        return 0.0

    return sum(scores) / len(scores)


def _scale_pitch_classes(root, mode):
    """
    Retorna as classes de altura de uma escala maior ou menor.
    """

    if mode == "major":
        intervals = (
            0, 2, 4, 5,
            7, 9, 11
        )

    else:
        intervals = (
            0, 2, 3, 5,
            7, 8, 10
        )

    return {
        (root + interval) % 12
        for interval in intervals
    }


def _find_best_key(chords):
    """
    Procura a tonalidade que melhor explica os acordes.

    A escala maior recebe uma pequena preferência para evitar
    que a evolução genética tenda excessivamente para
    tonalidades menores.

    Retorno:

        (root, mode, score)
    """

    if not chords:
        return 0, "major", 0.0

    best_root = 0
    best_mode = "major"
    best_score = -1.0

    all_notes = [
        note
        for chord in chords
        for note in chord.notes
    ]

    all_pitch_classes = _pitch_classes(
        all_notes
    )

    for root in range(12):

        for mode in (
            "major",
            "minor"
        ):

            scale = _scale_pitch_classes(
                root,
                mode
            )

            if not all_pitch_classes:
                continue

            note_score = (
                len(
                    all_pitch_classes.intersection(
                        scale
                    )
                )
                / len(all_pitch_classes)
            )

            root_score = sum(
                1
                for chord in chords
                if chord.root in scale
            ) / len(chords)

            score = (
                0.70 * note_score
                + 0.30 * root_score
            )

            # Pequena preferência por tonalidade maior.
            #
            # Não é suficiente para obrigar a música a ser maior,
            # apenas evita que empates sejam resolvidos sempre
            # em favor do modo menor.

            if mode == "major":
                score += 0.03

            if score > best_score:
                best_score = score
                best_root = root
                best_mode = mode

    return (
        best_root,
        best_mode,
        clamp(best_score)
    )


def tonal_coherence_fitness(individual):
    """
    Avalia a coerência tonal da música inteira.

    A avaliação procura uma tonalidade que explique os oito
    MChords e mede:

        - cobertura das notas pela escala;
        - presença das fundamentais dentro da escala.

    A base e o refrão devem permanecer harmonicamente
    relacionados.
    """

    chords = get_mchords(individual)

    if not chords:
        return 0.0

    _root, _mode, score = _find_best_key(
        chords
    )

    return clamp(score)


def section_tonal_coherence_fitness(
    chords,
    global_root,
    global_mode
):
    """
    Avalia a coerência tonal de uma seção dentro da tonalidade
    global da música.
    """

    if not chords:
        return 0.0

    scale = _scale_pitch_classes(
        global_root,
        global_mode
    )

    notes = [
        note
        for chord in chords
        for note in chord.notes
    ]

    pitch_classes = _pitch_classes(
        notes
    )

    if not pitch_classes:
        return 0.0

    note_score = (
        len(
            pitch_classes.intersection(
                scale
            )
        )
        / len(pitch_classes)
    )

    root_score = (
        sum(
            1
            for chord in chords
            if chord.root in scale
        )
        / len(chords)
    )

    return clamp(
        0.70 * note_score
        + 0.30 * root_score
    )


def chord_quality_fitness(individual):
    """
    Avalia o equilíbrio entre acordes maiores e menores.

    Não queremos eliminar acordes menores, pois isso deixaria
    a música artificialmente alegre.

    O objetivo é evitar que o algoritmo gere uma sequência
    dominada por acordes menores.

    O alvo é aproximadamente:

        60-70% maiores
        30-40% menores

    Acordes diminutos recebem penalização maior.
    """

    chords = get_mchords(individual)

    if not chords:
        return 0.0

    qualities = [
        _chord_quality(chord)
        for chord in chords
    ]

    major_count = qualities.count(
        "major"
    )

    minor_count = qualities.count(
        "minor"
    )

    diminished_count = qualities.count(
        "diminished"
    )

    augmented_count = qualities.count(
        "augmented"
    )

    total = len(qualities)

    major_ratio = (
        major_count / total
    )

    minor_ratio = (
        minor_count / total
    )

    diminished_ratio = (
        diminished_count / total
    )

    augmented_ratio = (
        augmented_count / total
    )

    # Alvo de aproximadamente 65% de acordes maiores.

    major_score = math.exp(
        -(
            (major_ratio - 0.65) ** 2
        )
        / (
            2 * 0.20 ** 2
        )
    )

    # Excesso de menores começa a ser penalizado.

    if minor_ratio <= 0.45:
        minor_score = 1.0

    else:
        minor_score = math.exp(
            -(
                (minor_ratio - 0.35) ** 2
            )
            / (
                2 * 0.20 ** 2
            )
        )

    diminished_score = max(
        0.0,
        1.0
        - 1.5 * diminished_ratio
    )

    augmented_score = max(
        0.0,
        1.0
        - 0.5 * augmented_ratio
    )

    return clamp(
        0.45 * major_score
        + 0.30 * minor_score
        + 0.15 * diminished_score
        + 0.10 * augmented_score
    )


def section_quality_fitness(chords):
    """
    Avalia a distribuição de qualidades de acordes dentro de
    uma seção.

    Usada separadamente para base e refrão.
    """

    if not chords:
        return 0.0

    qualities = [
        _chord_quality(chord)
        for chord in chords
    ]

    major_count = qualities.count(
        "major"
    )

    minor_count = qualities.count(
        "minor"
    )

    diminished_count = qualities.count(
        "diminished"
    )

    total = len(qualities)

    major_ratio = (
        major_count / total
    )

    minor_ratio = (
        minor_count / total
    )

    diminished_ratio = (
        diminished_count / total
    )

    # Base:
    # preferimos uma sensação relativamente estável.

    major_score = math.exp(
        -(
            (major_ratio - 0.75) ** 2
        )
        / (
            2 * 0.20 ** 2
        )
    )

    minor_score = (
        1.0
        if minor_ratio <= 0.50
        else 0.50
    )

    diminished_score = max(
        0.0,
        1.0 - 2.0 * diminished_ratio
    )

    return clamp(
        0.55 * major_score
        + 0.30 * minor_score
        + 0.15 * diminished_score
    )


def root_motion_fitness(individual):
    """
    Avalia o movimento das fundamentais.

    São favorecidos movimentos comuns em progressões tonais:

        0  -> repetição
        2  -> movimento de segunda
        5  -> quarta
        7  -> quinta
        10 -> movimento descendente de segunda

    Outros movimentos continuam possíveis, mas recebem
    pontuação menor.
    """

    chords = get_mchords(individual)

    if len(chords) < 2:
        return 0.0

    preferred_intervals = {
        0: 1.00,
        2: 0.95,
        5: 1.00,
        7: 1.00,
        10: 0.90,
        9: 0.80,
        4: 0.75,
        3: 0.70,
    }

    scores = []

    for current, following in zip(
        chords,
        chords[1:]
    ):

        interval = (
            following.root
            - current.root
        ) % 12

        scores.append(
            preferred_intervals.get(
                interval,
                0.45
            )
        )

    return clamp(
        sum(scores)
        / len(scores)
    )


def functional_progression_fitness(
    chords,
    tonic
):
    """
    Avalia a função harmônica aproximada dos acordes.

    Em uma tonalidade maior, alguns graus possuem funções
    particularmente estáveis:

        I   -> tônica
        IV  -> subdominante
        V   -> dominante
        vi  -> relativo menor

    A função não exige uma progressão específica, mas favorece
    a presença de I, IV e V e penaliza sequências dominadas por
    acordes fora da tonalidade.
    """

    if not chords:
        return 0.0

    degrees = [
        (chord.root - tonic) % 12
        for chord in chords
    ]

    if not degrees:
        return 0.0

    scores = []

    for degree in degrees:

        if degree == 0:
            scores.append(1.00)

        elif degree == 5:
            scores.append(0.95)

        elif degree == 7:
            scores.append(1.00)

        elif degree == 9:
            scores.append(0.90)

        elif degree == 2:
            scores.append(0.85)

        elif degree == 4:
            scores.append(0.90)

        else:
            scores.append(0.55)

    return clamp(
        sum(scores)
        / len(scores)
    )


def base_stability_fitness(
    base,
    tonic,
    mode
):
    """
    Avalia a estabilidade da música base.

    A base deve estabelecer claramente o ambiente harmônico
    antes da entrada do refrão.
    """

    if not base:
        return 0.0

    scale_score = section_tonal_coherence_fitness(
        base,
        tonic,
        mode
    )

    quality_score = section_quality_fitness(
        base
    )

    functional_score = functional_progression_fitness(
        base,
        tonic
    )

    # O último acorde da base deve ter alguma relação forte
    # com a tonalidade, mas não precisa obrigatoriamente
    # ser a tônica.

    final_root = (
        base[-1].root
    )

    final_interval = (
        final_root - tonic
    ) % 12

    final_score = {
        0: 1.00,  # I
        5: 0.95,  # IV
        7: 0.90,  # V
        9: 0.85,  # vi
        2: 0.80,  # ii
        4: 0.80,  # iii
        11: 0.65,
    }.get(
        final_interval,
        0.45
    )

    return clamp(
        0.35 * scale_score
        + 0.25 * quality_score
        + 0.25 * functional_score
        + 0.15 * final_score
    )


def chorus_fitness(
    base,
    chorus,
    tonic,
    mode
):
    """
    Avalia especificamente o refrão.

    O refrão deve:

        - continuar na mesma tonalidade;
        - possuir algum contraste com a base;
        - possuir energia harmônica;
        - terminar com sensação de resolução.

    Não queremos que o refrão seja apenas uma cópia da base.
    """

    if not chorus:
        return 0.0

    tonal_score = section_tonal_coherence_fitness(
        chorus,
        tonic,
        mode
    )

    functional_score = functional_progression_fitness(
        chorus,
        tonic
    )

    quality_score = section_quality_fitness(
        chorus
    )

    # --------------------------------------------------------
    # CONTRASTE ENTRE BASE E REFRÃO
    # --------------------------------------------------------

    base_roots = [
        chord.root
        for chord in base
    ]

    chorus_roots = [
        chord.root
        for chord in chorus
    ]

    if base_roots and chorus_roots:

        same_positions = sum(
            1
            for base_root, chorus_root
            in zip(
                base_roots,
                chorus_roots
            )
            if base_root == chorus_root
        )

        similarity = (
            same_positions
            / min(
                len(base_roots),
                len(chorus_roots)
            )
        )

        # Queremos alguma diferença, mas não uma mudança
        # harmônica completa.

        if 0.25 <= similarity <= 0.75:
            contrast_score = 1.0

        elif similarity < 0.25:
            contrast_score = 0.70

        else:
            contrast_score = 0.65

    else:
        contrast_score = 0.5

    # --------------------------------------------------------
    # RESOLUÇÃO DO REFRÃO
    # --------------------------------------------------------

    final_chord = chorus[-1]

    final_interval = (
        final_chord.root - tonic
    ) % 12

    if final_interval == 0:
        resolution_score = 1.00

    elif final_interval == 7:
        resolution_score = 0.85

    elif final_interval == 5:
        resolution_score = 0.80

    elif final_interval == 9:
        resolution_score = 0.75

    else:
        resolution_score = 0.50

    # --------------------------------------------------------
    # RELAÇÃO ENTRE OS DOIS ÚLTIMOS ACORDES
    # --------------------------------------------------------

    if len(chorus) >= 2:

        penultimate = chorus[-2]

        interval = (
            final_chord.root
            - penultimate.root
        ) % 12

        if (
            final_interval == 0
            and interval == 7
        ):
            cadence_score = 1.00

        elif interval in (5, 7):
            cadence_score = 0.90

        elif interval in (2, 10):
            cadence_score = 0.80

        else:
            cadence_score = 0.55

    else:
        cadence_score = 0.5

    return clamp(
        0.25 * tonal_score
        + 0.20 * functional_score
        + 0.15 * quality_score
        + 0.15 * contrast_score
        + 0.15 * resolution_score
        + 0.10 * cadence_score
    )


def _voicing_distance(first, following):
    """
    Distância média, em semitons, entre as notas reais de
    dois acordes.

    Cada nota é comparada com a nota mais próxima do outro
    acorde, nas duas direções. Diferente da comparação por
    classe de altura, esta função enxerga o registro: duas
    voicings próximas no teclado produzem distância menor.

    Usada pelo voice_leading para favorecer inversões que
    aproximam acordes consecutivos.
    """

    if not first or not following:
        return 6.0

    distances = []

    for note in following:
        distances.append(
            min(
                abs(note - other)
                for other in first
            )
        )

    for note in first:
        distances.append(
            min(
                abs(note - other)
                for other in following
            )
        )

    return sum(distances) / len(distances)


def voice_leading_fitness(individual):
    """
    Favorece transições com notas comuns ou pequenos movimentos.

    Dois aspectos são combinados:

        - notas em comum entre os acordes (classes de altura);
        - distância real entre as voicings (registro efetivo).

    O segundo aspecto faz a fitness enxergar as inversões:
    voicings próximas entre acordes consecutivos recebem
    pontuação maior, então a evolução tende a escolher
    inversões que produzem transições suaves.
    """

    chords = get_mchords(individual)

    if len(chords) < 2:
        return 0.0

    scores = []

    for current, following in zip(
        chords,
        chords[1:]
    ):

        current_pitches = _pitch_classes(
            current.notes
        )

        following_pitches = _pitch_classes(
            following.notes
        )

        union_notes = len(
            current_pitches.union(
                following_pitches
            )
        )

        if union_notes == 0:
            common_score = 0.0

        else:
            common_notes = len(
                current_pitches.intersection(
                    following_pitches
                )
            )

            common_ratio = (
                common_notes
                / union_notes
            )

            common_score = (
                0.50
                + 0.50 * common_ratio
            )

        voicing_score = math.exp(
            -_voicing_distance(
                current.notes,
                following.notes
            )
            / 3.0
        )

        scores.append(
            0.50 * common_score
            + 0.50 * voicing_score
        )

    return clamp(
        sum(scores)
        / len(scores)
    )


def harmonic_diversity_fitness(individual):
    """
    Incentiva fortemente a diversidade dos 8 MChords.

    Um acorde é considerado igual a outro quando possui a mesma:
        - root
        - chord_type
        - inversion

    Como existem exatamente 8 MChords, a função recompensa
    progressivamente indivíduos com mais acordes distintos.

    Objetivo principal:
        8 acordes distintos -> 1.00
        7 acordes distintos -> pontuação muito alta
        6 acordes distintos -> alta
        5 acordes distintos -> moderada
        4 ou menos -> penalização forte
    """

    chords = get_mchords(individual)

    if not chords:
        return 0.0

    # --------------------------------------------------------
    # IDENTIDADE DOS ACORDES
    # --------------------------------------------------------

    unique_chords = set()

    for chord in chords:
        chord_id = (
            chord.root,
            chord.chord_type,
            getattr(chord, "inversion", 0)
        )

        unique_chords.add(chord_id)

    num_chords = len(chords)
    num_unique = len(unique_chords)

    # --------------------------------------------------------
    # DIVERSIDADE DOS 8 MCHORDS
    # --------------------------------------------------------

    unique_fraction = num_unique / num_chords

    # Recompensa fortemente a quantidade de acordes distintos.
    #
    # A exponencial faz com que indivíduos com poucos acordes
    # distintos sejam penalizados muito mais.
    #
    # 8/8 -> 1.00
    # 7/8 -> ~0.94
    # 6/8 -> ~0.78
    # 5/8 -> ~0.55
    # 4/8 -> ~0.30
    # 3/8 -> ~0.13
    # 2/8 -> ~0.04
    # 1/8 -> ~0.01

    diversity_score = (
        math.exp(
            3.0 * (unique_fraction - 1.0)
        )
    )

    # --------------------------------------------------------
    # PENALIZAÇÃO EXPLÍCITA DE REPETIÇÕES
    # --------------------------------------------------------

    repeated_count = num_chords - num_unique

    if repeated_count == 0:
        repetition_score = 1.00

    elif repeated_count == 1:
        repetition_score = 0.90

    elif repeated_count == 2:
        repetition_score = 0.70

    elif repeated_count == 3:
        repetition_score = 0.45

    elif repeated_count == 4:
        repetition_score = 0.25

    else:
        repetition_score = 0.10

    # --------------------------------------------------------
    # DIVERSIDADE DE TIPOS
    # --------------------------------------------------------

    types = {
        chord.chord_type
        for chord in chords
    }

    type_fraction = (
        len(types)
        / max(1, num_chords)
    )

    type_score = min(
        1.0,
        type_fraction
    )

    # --------------------------------------------------------
    # DIVERSIDADE DE RAÍZES
    # --------------------------------------------------------

    roots = {
        chord.root
        for chord in chords
    }

    root_fraction = (
        len(roots)
        / max(1, num_chords)
    )

    root_score = min(
        1.0,
        root_fraction
    )

    # --------------------------------------------------------
    # RESULTADO
    # --------------------------------------------------------

    return clamp(
        0.70 * diversity_score
        + 0.20 * repetition_score
        + 0.05 * root_score
        + 0.05 * type_score
    )

def harmony_details(individual):
    """
    Avalia a harmonia considerando explicitamente:

        MChord1-MChord4 -> base
        MChord5-MChord8 -> refrão
    """

    chords = get_mchords(
        individual
    )

    if not chords:
        return {
            "chord_validity": 0.0,
            "tonal_coherence": 0.0,
            "chord_quality": 0.0,
            "root_motion": 0.0,
            "voice_leading": 0.0,
            "base_stability": 0.0,
            "chorus": 0.0,
            "harmonic_diversity": 0.0,
            "harmony": 0.0,
        }

    base = chords[:4]
    chorus = chords[4:8]

    tonic, mode, _key_score = _find_best_key(
        chords
    )

    chord_validity = chord_validity_fitness(
        individual
    )

    tonal_coherence = tonal_coherence_fitness(
        individual
    )

    chord_quality = chord_quality_fitness(
        individual
    )

    root_motion = root_motion_fitness(
        individual
    )

    voice_leading = voice_leading_fitness(
        individual
    )

    base_stability = base_stability_fitness(
        base,
        tonic,
        mode
    )

    chorus_score = chorus_fitness(
        base,
        chorus,
        tonic,
        mode
    )

    harmonic_diversity = harmonic_diversity_fitness(
        individual
    )

    # Pesos internos da harmonia.
    #
    # A estabilidade da base e a qualidade geral recebem
    # bastante importância.
    #
    # O refrão também recebe peso elevado porque agora ele
    # possui função estrutural explícita.
    #
    # A diversidade harmônica moderada (raízes, tipos e
    # inversões distintos) recebe um peso próprio para
    # estimular variedude sem abandonar a coerência tonal.

    harmony = (
        0.10 * chord_validity
        + 0.15 * tonal_coherence
        + 0.15 * chord_quality
        + 0.10 * root_motion
        + 0.10 * voice_leading
        + 0.10 * base_stability
        + 0.10 * chorus_score
        + 0.20 * harmonic_diversity
    )

    return {
        "chord_validity": chord_validity,
        "tonal_coherence": tonal_coherence,
        "chord_quality": chord_quality,
        "root_motion": root_motion,
        "voice_leading": voice_leading,
        "base_stability": base_stability,
        "chorus": chorus_score,
        "harmonic_diversity": harmonic_diversity,
        "tonic": tonic,
        "mode": mode,
        "harmony": clamp(harmony),
    }

# ============================================================
# FITNESS BASEADO EM REFERÊNCIAS
# ============================================================

def reference_fitness(
    individual,
    refs_dir=None,
    limit=MAX_REFS
):
    """
    Fitness baseado em músicas de referência.

    Esta função mantém a interface do fitness original.

    No estágio atual do projeto, a avaliação é feita somente
    por teoria musical.

    Futuramente esta função poderá comparar Bat1 com padrões
    extraídos de arquivos MIDI de artistas específicos.

    Possíveis características:

        - distribuição de kicks
        - distribuição de snares
        - distribuição de hi-hats
        - densidade
        - síncope
        - distância entre eventos
        - padrões de 1/2 compasso
        - padrões de 1 compasso
        - frequência de crashes
        - combinações de instrumentos
    """

    if refs_dir is None:
        return 0.0

    return 0.0


# ============================================================
# FITNESS PRINCIPAL
# ============================================================

def calculate_fitness(
    individual,
    refs_dir=None,
    limit=MAX_REFS
):
    """
    Calcula o fitness de um indivíduo.

    O fitness é uma combinação ponderada de critérios
    musicais e rítmicos.

    Retorno:

        float no intervalo [0, 1]
    """

    strong_beats = strong_beats_fitness(
        individual
    )

    backbeat = backbeat_fitness(
        individual
    )

    kick = kick_fitness(
        individual
    )

    hihat = hihat_fitness(
        individual
    )

    syncopation = syncopation_fitness(
        individual
    )

    density = density_fitness(
        individual
    )

    variation = variation_fitness(
        individual
    )

    structure = structure_fitness(
        individual
    )

    combination = combination_fitness(
        individual
    )

    reference = reference_fitness(
        individual,
        refs_dir=refs_dir,
        limit=limit
    )

    theory_fitness = (

        FITNESS_WEIGHTS["strong_beats"]
        * strong_beats

        + FITNESS_WEIGHTS["backbeat"]
        * backbeat

        + FITNESS_WEIGHTS["kick"]
        * kick

        + FITNESS_WEIGHTS["hihat"]
        * hihat

        + FITNESS_WEIGHTS["syncopation"]
        * syncopation

        + FITNESS_WEIGHTS["density"]
        * density

        + FITNESS_WEIGHTS["variation"]
        * variation

        + FITNESS_WEIGHTS["structure"]
        * structure

        + FITNESS_WEIGHTS["combination"]
        * combination
    )

    rhythm_fitness = (
        BAT1_RHYTHM_WEIGHT * theory_fitness
        + BAT2_RHYTHM_WEIGHT * chorus_bat2_fitness(individual)
        + BATI_RHYTHM_WEIGHT * edge_battery_fitness(individual, "bati")
        + BATF_RHYTHM_WEIGHT * edge_battery_fitness(individual, "batf")
    )

    harmony = harmony_details(individual)

    arp_patt1 = arp_pattern_fitness(individual.arp_patt1)
    arp_patt2 = arp_pattern_fitness(individual.arp_patt2)
    arp_order_diversity = arp_order_diversity_fitness(
        individual.arp_patt1,
        individual.arp_patt2,
    )
    arp_total = (
        0.90 * (
            ARP_PATT1_WEIGHT * arp_patt1
            + ARP_PATT2_WEIGHT * arp_patt2
        )
        + 0.10
        * (ARP_PATT1_WEIGHT + ARP_PATT2_WEIGHT)
        * arp_order_diversity
    )

    base_fitness = (
        RHYTHM_WEIGHT * rhythm_fitness
        + HARMONY_WEIGHT * harmony["harmony"]
        + BASS_PATT1_WEIGHT * bass_pattern_fitness(
            individual.bass_patt1
        )
        + BASS_PATT2_WEIGHT * bass_pattern_fitness(
            individual.bass_patt2
        )
        + arp_total
    )

    mel_patt1 = melody_pattern_fitness(individual.mel_patt1)
    mel_patt2 = melody_pattern_fitness(individual.mel_patt2)
    melody_diversity = melody_diversity_fitness(
        individual.mel_patt1,
        individual.mel_patt2,
    )
    melody = (
        0.40 * mel_patt1
        + 0.40 * mel_patt2
        + 0.20 * melody_diversity
    )
    mel_patt1_rhythm_alignment = melody_rhythm_alignment_fitness(
        individual.mel_patt1,
        individual.bat1,
    )
    mel_patt2_rhythm_alignment = melody_rhythm_alignment_fitness(
        individual.mel_patt2,
        individual.bat2,
    )
    melody_rhythm_alignment = (
        0.50 * mel_patt1_rhythm_alignment
        + 0.50 * mel_patt2_rhythm_alignment
    )

    # Os pesos existentes somam 1.0. A qualidade melódica e seu
    # alinhamento rítmico acrescentam 0.10 cada, com normalização.
    fitness = (
        base_fitness
        + 0.10 * melody
        + 0.10 * melody_rhythm_alignment
    ) / 1.20

    return float(
        clamp(fitness)
    )


# ============================================================
# DETALHES DO FITNESS
# ============================================================

def fitness_details(
    individual,
    refs_dir=None,
    limit=MAX_REFS
):
    """
    Retorna todos os componentes do fitness.

    Útil para analisar por que determinado padrão recebeu
    determinada pontuação.
    """

    strong_beats = strong_beats_fitness(
        individual
    )

    backbeat = backbeat_fitness(
        individual
    )

    kick = kick_fitness(
        individual
    )

    hihat = hihat_fitness(
        individual
    )

    syncopation = syncopation_fitness(
        individual
    )

    density = density_fitness(
        individual
    )

    variation = variation_fitness(
        individual
    )

    structure = structure_fitness(
        individual
    )

    combination = combination_fitness(
        individual
    )

    harmony = harmony_details(individual)

    reference = reference_fitness(
        individual,
        refs_dir=refs_dir,
        limit=limit
    )

    theory = (

        FITNESS_WEIGHTS["strong_beats"]
        * strong_beats

        + FITNESS_WEIGHTS["backbeat"]
        * backbeat

        + FITNESS_WEIGHTS["kick"]
        * kick

        + FITNESS_WEIGHTS["hihat"]
        * hihat

        + FITNESS_WEIGHTS["syncopation"]
        * syncopation

        + FITNESS_WEIGHTS["density"]
        * density

        + FITNESS_WEIGHTS["variation"]
        * variation

        + FITNESS_WEIGHTS["structure"]
        * structure

        + FITNESS_WEIGHTS["combination"]
        * combination
    )

    rhythm = (
        BAT1_RHYTHM_WEIGHT * theory
        + BAT2_RHYTHM_WEIGHT * chorus_bat2_fitness(individual)
        + BATI_RHYTHM_WEIGHT * edge_battery_fitness(individual, "bati")
        + BATF_RHYTHM_WEIGHT * edge_battery_fitness(individual, "batf")
    )

    bass_patt1 = bass_pattern_fitness(
        individual.bass_patt1
    )

    bass_patt2 = bass_pattern_fitness(
        individual.bass_patt2
    )

    arp_patt1 = arp_pattern_fitness(
        individual.arp_patt1
    )

    arp_patt2 = arp_pattern_fitness(
        individual.arp_patt2
    )
    arp_order_diversity = arp_order_diversity_fitness(
        individual.arp_patt1,
        individual.arp_patt2,
    )
    arp_total = (
        0.90 * (
            ARP_PATT1_WEIGHT * arp_patt1
            + ARP_PATT2_WEIGHT * arp_patt2
        )
        + 0.10
        * (ARP_PATT1_WEIGHT + ARP_PATT2_WEIGHT)
        * arp_order_diversity
    )

    mel_patt1 = melody_pattern_fitness(individual.mel_patt1)
    mel_patt2 = melody_pattern_fitness(individual.mel_patt2)
    melody_diversity = melody_diversity_fitness(
        individual.mel_patt1,
        individual.mel_patt2,
    )
    melody = (
        0.40 * mel_patt1
        + 0.40 * mel_patt2
        + 0.20 * melody_diversity
    )
    mel_patt1_rhythm_alignment = melody_rhythm_alignment_fitness(
        individual.mel_patt1,
        individual.bat1,
    )
    mel_patt2_rhythm_alignment = melody_rhythm_alignment_fitness(
        individual.mel_patt2,
        individual.bat2,
    )
    melody_rhythm_alignment = (
        0.50 * mel_patt1_rhythm_alignment
        + 0.50 * mel_patt2_rhythm_alignment
    )

    base_total = (
        RHYTHM_WEIGHT * rhythm
        + HARMONY_WEIGHT * harmony["harmony"]
        + BASS_PATT1_WEIGHT * bass_patt1
        + BASS_PATT2_WEIGHT * bass_patt2
        + arp_total
    )
    total = (
        base_total
        + 0.10 * melody
        + 0.10 * melody_rhythm_alignment
    ) / 1.20

    return {
        "strong_beats": strong_beats,
        "backbeat": backbeat,
        "kick": kick,
        "hihat": hihat,
        "syncopation": syncopation,
        "density": density,
        "variation": variation,
        "structure": structure,
        "combination": combination,

        "reference": reference,

        "theory": theory,
        "bat2_chorus": chorus_bat2_fitness(individual),
        "bati_intro": edge_battery_fitness(individual, "bati"),
        "batf_final": edge_battery_fitness(individual, "batf"),
        "bass_patt1": bass_patt1,
        "bass_patt2": bass_patt2,
        "arp_patt1": arp_patt1,
        "arp_patt2": arp_patt2,
        "arp_order_diversity": arp_order_diversity,
        "mel_patt1_quality": mel_patt1,
        "mel_patt2_quality": mel_patt2,
        "melody_diversity": melody_diversity,
        "melody": melody,
        "mel_patt1_rhythm_alignment": mel_patt1_rhythm_alignment,
        "mel_patt2_rhythm_alignment": mel_patt2_rhythm_alignment,
        "melody_rhythm_alignment": melody_rhythm_alignment,
        "rhythm": rhythm,
        **harmony,
        "fitness": total,
        "total": total,
    }


# ============================================================
# DESCRIÇÃO DO PADRÃO
# ============================================================

def describe(individual):
    """
    Retorna uma descrição simples do padrão de bateria.

    Útil para debug do algoritmo genético.
    """

    bat1 = get_bat1(individual)

    result = []

    for step, gene in enumerate(bat1):

        names = [
            DRUM_NAMES_FITNESS[drum]
            for drum in sorted(gene.notes)
        ]

        result.append({
            "step": step,
            "drums": names,
        })

    return result
