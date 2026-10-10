import random
from copy import copy

from constants import *
from genotype import (
    ArpPattern,
    BassPattern,
    Genotype,
    MChord,
    MelodyNote,
    MelodyPattern,
)
from individual import Individual


# ============================================================
# CÓPIA DE GENES
# ============================================================

def clone_genes(genes):
    """
    Copia os Genes individualmente.

    Isso evita que pais e filhos compartilhem
    os mesmos objetos Gene.
    """

    return [
        copy(gene)
        for gene in genes
    ]


# ============================================================
# CRIAÇÃO DO FILHO
# ============================================================

def make_child(
    bat1,
    bat2=None,
    bati=None,
    batf=None,
    bass_patt1=None,
    bass_patt2=None,
    arp_patt1=None,
    arp_patt2=None,
    mel_patt1=None,
    mel_patt2=None,
    mchords=None
):
    """
    Cria um novo Individual a partir dos componentes
    fornecidos.
    """

    kwargs = {
        "bat1": clone_genes(bat1),
        "bat2": clone_genes(
            bat1 if bat2 is None else bat2
        ),
        "bati": clone_genes(
            bat1 if bati is None else bati
        ),
        "batf": clone_genes(
            bat1 if batf is None else batf
        ),
    }

    if bass_patt1 is not None:
        kwargs["bass_patt1"] = clone_bass_pattern(
            bass_patt1
        )

    if bass_patt2 is not None:
        kwargs["bass_patt2"] = clone_bass_pattern(
            bass_patt2
        )

    if arp_patt1 is not None:
        kwargs["arp_patt1"] = clone_arp_pattern(
            arp_patt1
        )

    if arp_patt2 is not None:
        kwargs["arp_patt2"] = clone_arp_pattern(
            arp_patt2
        )

    if mel_patt1 is not None:
        kwargs["mel_patt1"] = clone_melody_pattern(
            mel_patt1
        )

    if mel_patt2 is not None:
        kwargs["mel_patt2"] = clone_melody_pattern(
            mel_patt2
        )

    if mchords is not None:
        kwargs.update({
            f"mchord{index}": clone_chord(chord)
            for index, chord in enumerate(
                mchords,
                start=1
            )
        })

    return Individual(
        Genotype(**kwargs)
    )


# ============================================================
# CÓPIAS DOS ELEMENTOS
# ============================================================

def clone_chord(chord):
    """
    Cria uma cópia independente de um MChord válido.
    """

    return MChord(
        chord.root,
        chord.chord_type,
        getattr(chord, "inversion", 0),
    )


def clone_bass_pattern(pattern):
    """
    Copia um BassPattern sem compartilhar suas notas.
    """

    return BassPattern(
        [
            type(note)(
                note.position,
                note.duration
            )
            for note in pattern.notes
        ]
    )


def clone_arp_pattern(pattern):
    """
    Copia um ArpPattern sem compartilhar o objeto.
    """

    return ArpPattern(
        note_count=pattern.note_count,
        step=pattern.step,
        note_order=pattern.note_order,
    )


def clone_melody_pattern(pattern):
    """Copia o padrão e cada nota melódica sem compartilhar objetos."""

    return MelodyPattern(
        [
            MelodyNote(
                pitch=note.pitch,
                velocity=note.velocity,
                position=note.position,
                duration=note.duration,
            )
            for note in pattern.notes
        ]
    )


def clone_individual(individual):
    """
    Cria uma cópia completamente independente
    do indivíduo.
    """

    chord_kwargs = {
        f"mchord{index}": clone_chord(chord)
        for index, chord in enumerate(
            individual.genotype.mchords,
            start=1
        )
    }

    return Individual(
        Genotype(
            bati=clone_genes(
                individual.bati
            ),
            bat1=clone_genes(
                individual.bat1
            ),
            bat2=clone_genes(
                individual.bat2
            ),
            batf=clone_genes(
                individual.batf
            ),
            bass_patt1=clone_bass_pattern(
                individual.bass_patt1
            ),
            bass_patt2=clone_bass_pattern(
                individual.bass_patt2
            ),
            arp_patt1=clone_arp_pattern(
                individual.arp_patt1
            ),
            arp_patt2=clone_arp_pattern(
                individual.arp_patt2
            ),
            mel_patt1=clone_melody_pattern(
                individual.mel_patt1
            ),
            mel_patt2=clone_melody_pattern(
                individual.mel_patt2
            ),
            **chord_kwargs,
        )
    )


# ============================================================
# CROSSOVER DE BATERIA
# ============================================================

def _crossover_genes(parent1, parent2):
    """
    Crossover multi-ponto entre duas sequências de Genes.

    Os cortes acontecem somente entre Genes.
    """

    total_steps = min(
        len(parent1),
        len(parent2)
    )

    if total_steps < 2:
        return clone_genes(parent1)

    max_points = min(6, total_steps - 1)

    number_of_points = random.randint(
        2,
        max_points
    )

    points = sorted(
        random.sample(
            range(1, total_steps),
            number_of_points
        )
    )

    points = [0] + points + [total_steps]

    child = []

    for index in range(len(points) - 1):
        start = points[index]
        end = points[index + 1]

        source = (
            parent1
            if index % 2 == 0
            else parent2
        )

        child.extend(
            source[start:end]
        )

    return clone_genes(child)


def _crossover_drums(parent1, parent2):
    """
    Faz crossover independente para cada pista de bateria.

    Isso evita que Bat1, Bat2, BatI e BatF
    fiquem sempre geneticamente acoplados.
    """

    bat1 = _cross_or_copy(
        BAT1_CROSSOVER_RATE, _crossover_genes,
        parent1.bat1, parent2.bat1, clone_genes,
    )
    bat2 = _cross_or_copy(
        BAT2_CROSSOVER_RATE, _crossover_genes,
        parent1.bat2, parent2.bat2, clone_genes,
    )
    bati = _cross_or_copy(
        BATI_CROSSOVER_RATE, _crossover_genes,
        parent1.bati, parent2.bati, clone_genes,
    )
    batf = _cross_or_copy(
        BATF_CROSSOVER_RATE, _crossover_genes,
        parent1.batf, parent2.batf, clone_genes,
    )

    return bat1, bat2, bati, batf


# ============================================================
# CROSSOVER DE BASS
# ============================================================

def _mix_bass_pattern(parent1, parent2):
    """
    Mistura dois BassPatterns.

    O BassPattern precisa continuar preenchendo
    exatamente um compasso, portanto são testadas
    combinações válidas antes da criação do objeto.
    """

    if random.random() < 0.25:
        return BassPattern()

    candidates = [
        parent1,
        parent2,
    ]

    if random.random() < 0.5:
        source = random.choice(candidates)
        return clone_bass_pattern(source)

    count = random.choice(
        BassPattern.NOTE_COUNTS
    )

    source = random.choice(candidates)

    if len(source.notes) == count:
        notes = [
            type(note)(
                note.position,
                note.duration
            )
            for note in source.notes
        ]

        return BassPattern(notes)

    return BassPattern()


# ============================================================
# CROSSOVER DE ARP
# ============================================================

def _mix_arp_pattern(parent1, parent2):
    """
    Mistura note_count e step dos dois pais.

    Também existe uma chance de gerar um ArpPattern
    completamente novo.
    """

    if random.random() < 0.25:
        return ArpPattern()

    note_count = random.choice([
        parent1.note_count,
        parent2.note_count,
    ])

    step = random.choice([
        parent1.step,
        parent2.step,
    ])
    note_order = random.choice([
        parent1.note_order,
        parent2.note_order,
    ])

    try:
        return ArpPattern(
            note_count=note_count,
            step=step,
            note_order=note_order,
        )
    except ValueError:
        return ArpPattern()


def _mix_melody_pattern(parent1, parent2):
    """Recombina segmentos temporais de dois padrões de melodia."""

    if random.random() < 0.15:
        return MelodyPattern()

    if random.random() < 0.25:
        return clone_melody_pattern(random.choice((parent1, parent2)))

    cut = random.randint(1, MelodyPattern.TOTAL_UNITS - 1)
    notes = [
        note
        for note in parent1.notes
        if note.position < cut
    ]
    notes.extend(
        note
        for note in parent2.notes
        if note.position >= cut
    )
    notes.sort(key=lambda note: note.position)

    return clone_melody_pattern(MelodyPattern(notes))


def _cross_or_copy(rate, crossover_fn, parent1, parent2, clone_fn):
    """Aplica crossover com a taxa do componente; caso contrário copia um pai."""

    if random.random() < rate:
        return crossover_fn(parent1, parent2)

    return clone_fn(random.choice((parent1, parent2)))


# ============================================================
# CROSSOVER DE ACORDES
# ============================================================

def _chord_signature(chord):
    return (
        chord.root,
        chord.chord_type,
        getattr(chord, "inversion", 0),
    )


def _new_random_chord():
    """
    Cria um MChord novo, independente dos pais.
    """

    root = random.randint(
        MChord.ROOT_MIN_MIDI_NOTE,
        MChord.ROOT_MAX_MIDI_NOTE
    )

    chord_type = random.choice(
        tuple(
            MChord.CHORD_INTERVALS.keys()
        )
    )

    inversion = random.choice(
        tuple(MChord.INVERSIONS)
    )

    return MChord(
        root,
        chord_type,
        inversion
    )


def _select_parent_chord(
    parent1,
    parent2,
    index,
    used
):
    """
    Seleciona um acorde com maior diversidade.

    Há três possibilidades:

    1. acorde da mesma posição;
    2. acorde de qualquer posição dos pais;
    3. novo acorde gerado aleatoriamente.
    """

    # Chance relativamente alta de criar
    # algo que não existia nos pais.
    if random.random() < 0.30:
        for _ in range(10):
            chord = _new_random_chord()

            if _chord_signature(chord) not in used:
                return chord

    candidates = []

    # Acordes da mesma posição.
    candidates.extend([
        parent1.genotype.mchords[index],
        parent2.genotype.mchords[index],
    ])

    # Acordes de outras posições.
    if random.random() < 0.70:
        candidates.extend(
            chord
            for parent in (parent1, parent2)
            for chord in parent.genotype.mchords
        )

    # Remove duplicados.
    unique = {}

    for chord in candidates:
        unique[
            _chord_signature(chord)
        ] = chord

    candidates = list(
        unique.values()
    )

    unused = [
        chord
        for chord in candidates
        if _chord_signature(chord)
        not in used
    ]

    if unused:
        return random.choice(
            unused
        )

    return random.choice(
        candidates
    )


# ============================================================
# CROSSOVER PRINCIPAL
# ============================================================

def crossover(parent1, parent2):
    """
    Crossover agressivo entre dois indivíduos.

    O objetivo é produzir filhos com maior diversidade
    genética, mantendo a validade estrutural do Genotype.
    """

    # --------------------------------------------------------
    # BATERIA
    # --------------------------------------------------------

    bat1, bat2, bati, batf = _crossover_drums(
        parent1,
        parent2
    )

    # --------------------------------------------------------
    # BASS
    # --------------------------------------------------------

    bass_patt1 = _cross_or_copy(
        BASS_PATT1_CROSSOVER_RATE,
        _mix_bass_pattern,
        parent1.bass_patt1,
        parent2.bass_patt1,
        clone_bass_pattern,
    )

    bass_patt2 = _cross_or_copy(
        BASS_PATT2_CROSSOVER_RATE,
        _mix_bass_pattern,
        parent1.bass_patt2,
        parent2.bass_patt2,
        clone_bass_pattern,
    )

    # --------------------------------------------------------
    # ARP
    # --------------------------------------------------------

    arp_patt1 = _cross_or_copy(
        ARP_PATT1_CROSSOVER_RATE,
        _mix_arp_pattern,
        parent1.arp_patt1,
        parent2.arp_patt1,
        clone_arp_pattern,
    )

    arp_patt2 = _cross_or_copy(
        ARP_PATT2_CROSSOVER_RATE,
        _mix_arp_pattern,
        parent1.arp_patt2,
        parent2.arp_patt2,
        clone_arp_pattern,
    )

    # --------------------------------------------------------
    # MELODIAS
    # --------------------------------------------------------

    mel_patt1 = _cross_or_copy(
        MEL_PATT1_CROSSOVER_RATE,
        _mix_melody_pattern,
        parent1.mel_patt1,
        parent2.mel_patt1,
        clone_melody_pattern,
    )

    mel_patt2 = _cross_or_copy(
        MEL_PATT2_CROSSOVER_RATE,
        _mix_melody_pattern,
        parent1.mel_patt2,
        parent2.mel_patt2,
        clone_melody_pattern,
    )

    # --------------------------------------------------------
    # MCHORDS
    # --------------------------------------------------------

    chords = []
    used = set()

    for index in range(NUM_MCHORDS):

        if random.random() < MCHORD_CROSSOVER_RATE:
            chord = _select_parent_chord(
                parent1,
                parent2,
                index,
                used
            )
        else:
            chord = clone_chord(
                random.choice((
                    parent1.genotype.mchords[index],
                    parent2.genotype.mchords[index],
                ))
            )

        chord = clone_chord(
            chord
        )

        chords.append(
            chord
        )

        used.add(
            _chord_signature(chord)
        )

    # --------------------------------------------------------
    # FILHO
    # --------------------------------------------------------

    return make_child(
        bat1,
        bat2=bat2,
        bati=bati,
        batf=batf,
        bass_patt1=bass_patt1,
        bass_patt2=bass_patt2,
        arp_patt1=arp_patt1,
        arp_patt2=arp_patt2,
        mel_patt1=mel_patt1,
        mel_patt2=mel_patt2,
        mchords=chords,
    )
