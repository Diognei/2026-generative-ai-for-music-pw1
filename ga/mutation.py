import random

from constants import *

from genotype import (
    ArpPattern,
    BassPattern,
    Gene,
    MChord,
    MelodyNote,
    MelodyPattern,
)

# ============================================================
# GERAÇÃO DE UM STEP DE BATERIA
# ============================================================

def generate_drum_step(position, profile="base"):
    """
    Gera um Gene de bateria para determinado step.
    """

    profile_values = {
        "base": (
            BAT1_EMPTY_STEP_PROBABILITY,
            BAT1_SECOND_NOTE_PROBABILITY,
            BAT1_THIRD_NOTE_PROBABILITY,
        ),
        "chorus": (
            BAT2_EMPTY_STEP_PROBABILITY,
            BAT2_SECOND_NOTE_PROBABILITY,
            BAT2_THIRD_NOTE_PROBABILITY,
        ),
        "intro": (
            BATI_EMPTY_STEP_PROBABILITY,
            BATI_SECOND_NOTE_PROBABILITY,
            BATI_THIRD_NOTE_PROBABILITY,
        ),
        "final": (
            BATF_EMPTY_STEP_PROBABILITY,
            BATF_SECOND_NOTE_PROBABILITY,
            BATF_THIRD_NOTE_PROBABILITY,
        ),
    }

    (
        empty_probability,
        second_note_probability,
        third_note_probability,
    ) = profile_values[profile]

    if random.random() < empty_probability:
        return Gene()

    candidates = []
    weights = []

    candidates.append(KICK)

    if position in (0, 4):
        weights.append(KICK_WEIGHT)
    elif position in (2, 6):
        weights.append(22)
    else:
        weights.append(8)

    candidates.append(SNARE)

    if position in (2, 6):
        weights.append(SNARE_WEIGHT)
    elif position in (1, 3, 5, 7):
        weights.append(5)
    else:
        weights.append(2)

    candidates.append(CLOSED_HIHAT)
    weights.append(CLOSED_HIHAT_WEIGHT)

    candidates.append(OPEN_HIHAT)

    if position in (3, 7):
        weights.append(OPEN_HIHAT_WEIGHT * 2)
    else:
        weights.append(OPEN_HIHAT_WEIGHT)

    candidates.append(CRASH)

    if position == 0:
        weights.append(CRASH_WEIGHT * 3)
    else:
        weights.append(1)

    first = random.choices(
        candidates,
        weights=weights,
        k=1
    )[0]

    notes = [first]

    if (
        Gene.MAX_NOTES >= 2
        and random.random() < second_note_probability
    ):
        available = [
            drum
            for drum in candidates
            if drum not in notes
        ]

        if available:
            available_weights = [
                weights[candidates.index(drum)]
                for drum in available
            ]

            second = random.choices(
                available,
                weights=available_weights,
                k=1
            )[0]

            if not (
                (
                    second == CLOSED_HIHAT
                    and OPEN_HIHAT in notes
                )
                or (
                    second == OPEN_HIHAT
                    and CLOSED_HIHAT in notes
                )
            ):
                notes.append(second)

    if (
        Gene.MAX_NOTES >= 3
        and random.random() < third_note_probability
    ):
        available = [
            drum
            for drum in candidates
            if drum not in notes
        ]

        if available:
            third = random.choice(available)

            if not (
                (
                    third == CLOSED_HIHAT
                    and OPEN_HIHAT in notes
                )
                or (
                    third == OPEN_HIHAT
                    and CLOSED_HIHAT in notes
                )
            ):
                notes.append(third)

    notes.sort()

    return Gene(notes)


# ============================================================
# MUTAÇÃO DE UM STEP DE BATERIA
# ============================================================

def mutate_drum_step(track, index, profile="base"):
    """
    Muta um Gene de bateria.

    A mutação é deliberadamente agressiva:
    - remove elementos;
    - adiciona elementos;
    - troca elementos;
    - ou recria completamente o step.
    """

    old_notes = list(track[index].notes)

    action = random.random()

    # --------------------------------------------------------
    # Gene vazio
    # --------------------------------------------------------

    if not old_notes:

        # Em um Gene vazio, normalmente criamos algo novo.
        track[index] = generate_drum_step(
            index,
            profile=profile
        )

        return

    # --------------------------------------------------------
    # Recriação completa
    # --------------------------------------------------------

    if action < 0.35:

        new_gene = generate_drum_step(
            index,
            profile=profile
        )

        # Tenta evitar que a mutação não produza mudança.
        for _ in range(5):

            if new_gene.notes != old_notes:
                track[index] = new_gene
                return

            new_gene = generate_drum_step(
                index,
                profile=profile
            )

        track[index] = new_gene
        return

    # --------------------------------------------------------
    # Remoção
    # --------------------------------------------------------

    if action < 0.50:

        if old_notes:

            position = random.randrange(
                len(old_notes)
            )

            old_notes.pop(position)

        track[index] = Gene(
            sorted(set(old_notes))
        )

        return

    # --------------------------------------------------------
    # Adição
    # --------------------------------------------------------

    if action < 0.68:

        available = [
            drum
            for drum in DRUMS
            if drum not in old_notes
        ]

        if (
            available
            and len(old_notes) < Gene.MAX_NOTES
        ):

            random.shuffle(
                available
            )

            for new_drum in available:

                if (
                    new_drum == CLOSED_HIHAT
                    and OPEN_HIHAT in old_notes
                ):
                    continue

                if (
                    new_drum == OPEN_HIHAT
                    and CLOSED_HIHAT in old_notes
                ):
                    continue

                old_notes.append(
                    new_drum
                )

                break

        track[index] = Gene(
            sorted(set(old_notes))
        )

        return

    # --------------------------------------------------------
    # Substituição
    # --------------------------------------------------------

    if action < 0.88:

        if old_notes:

            position = random.randrange(
                len(old_notes)
            )

            current = old_notes[position]

            available = [
                drum
                for drum in DRUMS
                if drum != current
                and drum not in old_notes
            ]

            random.shuffle(
                available
            )

            for new_drum in available:

                other_notes = [
                    note
                    for i, note in enumerate(old_notes)
                    if i != position
                ]

                if (
                    new_drum == CLOSED_HIHAT
                    and OPEN_HIHAT in other_notes
                ):
                    continue

                if (
                    new_drum == OPEN_HIHAT
                    and CLOSED_HIHAT in other_notes
                ):
                    continue

                old_notes[position] = new_drum
                break

        track[index] = Gene(
            sorted(set(old_notes))
        )

        return

    # --------------------------------------------------------
    # Mutação extrema
    # --------------------------------------------------------

    track[index] = Gene()

    if random.random() < 0.75:
        track[index] = generate_drum_step(
            index,
            profile=profile
        )


# ============================================================
# MUTAÇÃO DE MCHORD
# ============================================================

def mutate_mchord(chord):
    """
    Gera outro MChord válido.

    A mutação é agressiva e pode alterar:
    - raiz;
    - tipo;
    - inversão;
    - raiz + tipo;
    - todos os componentes.
    """

    chord_types = tuple(
        MCHORD_INTERVALS
    )

    inversions = tuple(
        MCHORD_INVERSIONS
    )

    original = (
        chord.root,
        chord.chord_type,
        chord.inversion,
    )

    # --------------------------------------------------------
    # Tentativas de mutação
    # --------------------------------------------------------

    for _ in range(100):

        action = random.random()

        # ----------------------------------------------------
        # Alteração principalmente harmônica
        # ----------------------------------------------------

        if action < 0.30:

            root = random.randint(
                MCHORD_ROOT_MIN,
                MCHORD_ROOT_MAX
            )

            chord_type = random.choice(
                chord_types
            )

            inversion = chord.inversion

        # ----------------------------------------------------
        # Alteração de tipo + inversão
        # ----------------------------------------------------

        elif action < 0.50:

            root = chord.root

            chord_type = random.choice(
                chord_types
            )

            inversion = random.choice(
                inversions
            )

        # ----------------------------------------------------
        # Alteração da raiz
        # ----------------------------------------------------

        elif action < 0.70:

            root = random.randint(
                MCHORD_ROOT_MIN,
                MCHORD_ROOT_MAX
            )

            chord_type = chord.chord_type

            inversion = random.choice(
                inversions
            )

        # ----------------------------------------------------
        # Mutação completamente aleatória
        # ----------------------------------------------------

        else:

            root = random.randint(
                MCHORD_ROOT_MIN,
                MCHORD_ROOT_MAX
            )

            chord_type = random.choice(
                chord_types
            )

            inversion = random.choice(
                inversions
            )

        candidate = MChord(
            root,
            chord_type,
            inversion
        )

        candidate_signature = (
            candidate.root,
            candidate.chord_type,
            candidate.inversion,
        )

        if candidate_signature != original:
            return candidate

    # --------------------------------------------------------
    # Fallback
    # --------------------------------------------------------

    alternatives = [
        inversion
        for inversion in inversions
        if inversion != chord.inversion
    ]

    if alternatives:

        return MChord(
            chord.root,
            chord.chord_type,
            random.choice(alternatives)
        )

    return MChord(
        chord.root,
        chord.chord_type,
        chord.inversion
    )


# ============================================================
# RANDOMIZAÇÃO DE INVERSÕES
# ============================================================

def randomize_chord_inversions(individual):
    """
    Atribui uma inversão aleatória a cada MChord.
    """

    for index, chord in enumerate(
        individual.genotype.mchords,
        start=1
    ):

        current_inversion = chord.inversion

        available = [
            inversion
            for inversion in MCHORD_INVERSIONS
            if inversion != current_inversion
        ]

        if available:
            inversion = random.choice(
                available
            )
        else:
            inversion = current_inversion

        setattr(
            individual.genotype,
            f"mchord{index}",
            MChord(
                chord.root,
                chord.chord_type,
                inversion,
            ),
        )


# ============================================================
# MUTAÇÃO DE TRACK DE BATERIA
# ============================================================

def mutate_track(
    track,
    mutation_rate,
    profile="base"
):
    """
    Aplica mutação independente a cada step.

    A probabilidade recebida em mutation_rate continua
    controlando quantos steps serão afetados.
    """

    for index in range(len(track)):

        if random.random() < mutation_rate:

            mutate_drum_step(
                track,
                index,
                profile=profile
            )


# ============================================================
# MUTAÇÃO DOS MCHORDS
# ============================================================

def mutate_mchords(individual):
    """
    Muta cada MChord independentemente.

    Vários acordes podem ser modificados na mesma rodada.
    """

    for index, chord in enumerate(
        individual.genotype.mchords,
        start=1
    ):

        if random.random() < MCHORD_MUTATION_RATE:

            setattr(
                individual.genotype,
                f"mchord{index}",
                mutate_mchord(chord)
            )


# ============================================================
# MUTAÇÃO DE BASS
# ============================================================

def mutate_bass_pattern(pattern):
    """
    Gera uma nova estrutura rítmica de baixo.

    A nova estrutura é independente da anterior.
    """

    # Na maioria das vezes, gera completamente
    # uma nova estrutura.
    if random.random() < 0.85:
        return BassPattern()

    # Pequena chance de simplesmente manter
    # a estrutura atual.
    return BassPattern(
        [
            type(note)(
                note.position,
                note.duration
            )
            for note in pattern.notes
        ]
    )


# ============================================================
# MUTAÇÃO DE ARP
# ============================================================

def mutate_arp_pattern(pattern):
    """
    Muta a estrutura rítmica ou a ordem dos tons do arpejo.
    """

    if random.random() < 0.85:
        return ArpPattern()

    note_order = list(pattern.note_order)
    first_index, second_index = random.sample(range(3), 2)
    note_order[first_index], note_order[second_index] = (
        note_order[second_index],
        note_order[first_index],
    )

    return ArpPattern(
        note_count=pattern.note_count,
        step=pattern.step,
        note_order=note_order,
    )


# ============================================================
# MUTAÇÃO DE MELODIA
# ============================================================

def mutate_melody_pattern(pattern):
    """Muta notas ou a estrutura dentro dos oito compassos do padrão."""

    if random.random() < 0.10:
        return MelodyPattern()

    notes = [
        MelodyNote(
            pitch=note.pitch,
            velocity=note.velocity,
            position=note.position,
            duration=note.duration,
        )
        for note in pattern.notes
    ]

    action = random.random()

    if action < 0.15 and notes:
        notes.pop(random.randrange(len(notes)))

    elif action < 0.30 and len(notes) < pattern.DEFAULT_NOTE_COUNT * 3:
        position = random.randrange(MelodyPattern.TOTAL_UNITS)
        notes.append(
            MelodyNote(
                pitch=random.randint(48, 84),
                velocity=random.randint(50, 110),
                position=position,
                duration=random.randint(
                    1,
                    min(8, MelodyPattern.TOTAL_UNITS - position),
                ),
            )
        )

    elif notes:
        note = random.choice(notes)
        field = random.choice(("pitch", "velocity", "position", "duration"))

        if field == "pitch":
            note.pitch = max(48, min(84, note.pitch + random.choice((-5, -3, -2, -1, 1, 2, 3, 5))))

        elif field == "velocity":
            note.velocity = max(1, min(127, note.velocity + random.randint(-15, 15)))

        elif field == "position":
            latest_start = MelodyPattern.TOTAL_UNITS - note.duration
            note.position = max(
                0,
                min(latest_start, note.position + random.randint(-4, 4)),
            )

        else:
            max_duration = MelodyPattern.TOTAL_UNITS - note.position
            note.duration = max(
                1,
                min(max_duration, note.duration + random.randint(-3, 3)),
            )

    notes.sort(key=lambda note: note.position)
    return MelodyPattern(notes)


# ============================================================
# MUTAÇÃO PRINCIPAL
# ============================================================

def mutate(individual):
    """
    Aplica mutação independente a cada componente
    do indivíduo.

    A mutação é propositalmente agressiva para evitar
    convergência prematura da população.
    """

    # --------------------------------------------------------
    # BATERIA
    # --------------------------------------------------------

    mutate_track(
        individual.bat1,
        BAT1_MUTATION_RATE
    )

    mutate_track(
        individual.bat2,
        BAT2_MUTATION_RATE,
        profile="chorus"
    )

    mutate_track(
        individual.bati,
        BATI_MUTATION_RATE,
        profile="intro"
    )

    mutate_track(
        individual.batf,
        BATF_MUTATION_RATE,
        profile="final"
    )

    # --------------------------------------------------------
    # MCHORDS
    # --------------------------------------------------------

    mutate_mchords(
        individual
    )

    # --------------------------------------------------------
    # BASS PATTERN 1
    # --------------------------------------------------------

    if random.random() < BASS_PATT1_MUTATION_RATE:

        individual.bass_patt1 = (
            mutate_bass_pattern(
                individual.bass_patt1
            )
        )

    # --------------------------------------------------------
    # BASS PATTERN 2
    # --------------------------------------------------------

    if random.random() < BASS_PATT2_MUTATION_RATE:

        individual.bass_patt2 = (
            mutate_bass_pattern(
                individual.bass_patt2
            )
        )

    # --------------------------------------------------------
    # ARP PATTERN 1
    # --------------------------------------------------------

    if random.random() < ARP_PATT1_MUTATION_RATE:

        individual.arp_patt1 = (
            mutate_arp_pattern(
                individual.arp_patt1
            )
        )

    # --------------------------------------------------------
    # ARP PATTERN 2
    # --------------------------------------------------------

    if random.random() < ARP_PATT2_MUTATION_RATE:

        individual.arp_patt2 = (
            mutate_arp_pattern(
                individual.arp_patt2
            )
        )

    # --------------------------------------------------------
    # MELODY PATTERN 1
    # --------------------------------------------------------

    if random.random() < MEL_PATT1_MUTATION_RATE:
        individual.mel_patt1 = mutate_melody_pattern(
            individual.mel_patt1
        )

    # --------------------------------------------------------
    # MELODY PATTERN 2
    # --------------------------------------------------------

    if random.random() < MEL_PATT2_MUTATION_RATE:
        individual.mel_patt2 = mutate_melody_pattern(
            individual.mel_patt2
        )

    return individual
