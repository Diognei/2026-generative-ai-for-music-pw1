import argparse
import random

import pretty_midi


# ============================================================
# CONFIGURAÇÃO
# ============================================================

DEFAULT_BPM = 120.0


# A música é dividida em 8 partes.
# Cada valor representa a probabilidade de inserir
# uma nota naquela parte.

PART_PROBABILITIES = [
    0.00,  # Parte 1
    0.00,  # Parte 2
    0.10,  # Parte 3
    0.20,  # Parte 4
    0.40,  # Parte 5
    0.60,  # Parte 6
    0.70,  # Parte 7
    0.90,  # Parte 8
]


# Quantidade máxima de notas extras em relação
# à quantidade de notas originais.

MAX_ADDED_RATIO = 0.10


# Para pistas vazias.

EMPTY_TRACK_MAX_NOTES = 32


# Janela utilizada para detectar o acorde.
# 4 compassos em 4/4 = 16 beats.

CHORD_WINDOW_BEATS = 16


# Duração das notas adicionadas.

MIN_NOTE_DURATION = 0.08
MAX_NOTE_DURATION = 0.40


# Velocidade das notas adicionadas.

MIN_VELOCITY_FACTOR = 0.55
MAX_VELOCITY_FACTOR = 0.85


# ============================================================
# BATERIA - GENERAL MIDI
# ============================================================

KICK = 36
SNARE = 38
CLOSED_HH = 42
OPEN_HH = 46
CRASH = 49
TOM_LOW = 45
TOM_MID = 47
TOM_HIGH = 50


DRUM_ELEMENTS = [
    KICK,
    SNARE,
    CLOSED_HH,
    OPEN_HH,
    CRASH,
    TOM_LOW,
    TOM_MID,
    TOM_HIGH,
]


DRUM_WEIGHTS = [
    3.0,   # Kick
    2.5,   # Snare
    5.0,   # Closed Hi-Hat
    1.5,   # Open Hi-Hat
    0.5,   # Crash
    0.7,   # Low Tom
    0.7,   # Mid Tom
    0.7,   # High Tom
]


# ============================================================
# INSTRUMENTOS - GENERAL MIDI
# ============================================================
#
# Os números abaixo são os PROGRAM NUMBERS do General MIDI,
# começando em 0, como utilizado pelo pretty_midi.
#
# A seleção é feita a partir do nome do instrumento para
# facilitar a leitura e manutenção do código.
#
# ============================================================


def gm_program(name):
    """
    Retorna o program number General MIDI correspondente
    ao nome do instrumento.
    """

    return pretty_midi.instrument_name_to_program(name)


# ------------------------------------------------------------
# Strings
# ------------------------------------------------------------

STRING_INSTRUMENTS = [
    "Violin",
    "Viola",
    "Cello",
    "Contrabass",
    "Tremolo Strings",
    "Pizzicato Strings",
    "Orchestral Harp",
    "String Ensemble 1",
    "String Ensemble 2",
]


# String2 pode utilizar instrumentos que soam próximos
# de strings, incluindo alguns pads/synth strings.

STRING_SIMILAR_INSTRUMENTS = STRING_INSTRUMENTS + [
    "Synth Strings 1",
    "Synth Strings 2",
    "Choir Aahs",
    "Voice Oohs",
    "Warm Pad",
    "String Ensemble 1",
    "String Ensemble 2",
]


# ------------------------------------------------------------
# Bass
# ------------------------------------------------------------

BASS_INSTRUMENTS = [
    "Acoustic Bass",
    "Electric Bass (finger)",
    "Electric Bass (pick)",
    "Fretless Bass",
    "Slap Bass 1",
    "Slap Bass 2",
    "Synth Bass 1",
    "Synth Bass 2",
]


# Bass2 permite instrumentos graves próximos.

BASS_SIMILAR_INSTRUMENTS = BASS_INSTRUMENTS + [
    "Contrabass",
    "Tuba",
    "Muted Trumpet",
    "Baritone Sax",
]


# ------------------------------------------------------------
# Guitar
# ------------------------------------------------------------

# Guitar1:
# somente instrumentos de cordas dedilhadas/cordas
# diretamente relacionados à guitarra.

GUITAR_INSTRUMENTS = [
    "Acoustic Guitar (nylon)",
    "Acoustic Guitar (steel)",
    "Electric Guitar (jazz)",
    "Electric Guitar (clean)",
    "Electric Guitar (muted)",
    "Overdriven Guitar",
    "Distortion Guitar",
    "Guitar Harmonics",
]


# Guitar2:
# guitarra + instrumentos de cordas que podem funcionar
# razoavelmente como uma voz harmônica/melódica semelhante.

GUITAR_SIMILAR_INSTRUMENTS = GUITAR_INSTRUMENTS + [
    "Violin",
    "Viola",
    "Cello",
    "Pizzicato Strings",
    "String Ensemble 1",
    "String Ensemble 2",
    "Orchestral Harp",
]


# ------------------------------------------------------------
# Harmony
# ------------------------------------------------------------

# Instrumentos melódicos/harmônicos razoáveis para uma
# pista de Harmony.
#
# Não incluí bateria, efeitos, ruídos, percussão etc.

HARMONY_INSTRUMENTS = [
    # Piano / teclas
    "Acoustic Grand Piano",
    "Bright Acoustic Piano",
    "Electric Grand Piano",
    "Electric Piano 1",
    "Electric Piano 2",
    "Harpsichord",
    "Clavinet",

    # Órgãos
    "Drawbar Organ",
    "Percussive Organ",
    "Rock Organ",
    "Church Organ",
    "Reed Organ",

    # Guitarras
    "Acoustic Guitar (nylon)",
    "Acoustic Guitar (steel)",
    "Electric Guitar (jazz)",
    "Electric Guitar (clean)",

    # Cordas
    "Violin",
    "Viola",
    "Cello",
    "Contrabass",
    "Pizzicato Strings",
    "String Ensemble 1",
    "String Ensemble 2",

    # Baixos
    "Acoustic Bass",
    "Electric Bass (finger)",
    "Electric Bass (pick)",

    # Metais
    "Trumpet",
    "Trombone",
    "French Horn",
    "Brass Section",

    # Madeiras
    "Flute",
    "Oboe",
    "Clarinet",
    "Bassoon",
    "Alto Sax",
    "Tenor Sax",

    # Sintetizadores melódicos
    "Lead 1 (square)",
    "Lead 2 (sawtooth)",
    "Lead 3 (calliope)",
    "Lead 4 (chiff)",
    "Lead 5 (charang)",
    "Lead 6 (voice)",
    "Lead 7 (fifths)",
    "Lead 8 (bass + lead)",

    # Pads relativamente apropriados para harmonia
    "Pad 1 (new age)",
    "Pad 2 (warm)",
    "Pad 3 (polysynth)",
    "Pad 4 (choir)",
    "Pad 5 (bowed)",
    "Pad 6 (metallic)",
]


# ============================================================
# CONVERSÃO DOS NOMES PARA PROGRAM NUMBERS
# ============================================================


def get_programs(instrument_names):
    """
    Converte uma lista de nomes General MIDI para program
    numbers válidos do pretty_midi.

    Remove duplicatas.
    """

    programs = []

    for name in instrument_names:

        try:
            program = gm_program(name)

        except ValueError:
            continue

        if program not in programs:
            programs.append(program)

    return programs


STRING_PROGRAMS = get_programs(
    STRING_INSTRUMENTS
)

STRING_SIMILAR_PROGRAMS = get_programs(
    STRING_SIMILAR_INSTRUMENTS
)

BASS_PROGRAMS = get_programs(
    BASS_INSTRUMENTS
)

BASS_SIMILAR_PROGRAMS = get_programs(
    BASS_SIMILAR_INSTRUMENTS
)

GUITAR_PROGRAMS = get_programs(
    GUITAR_INSTRUMENTS
)

GUITAR_SIMILAR_PROGRAMS = get_programs(
    GUITAR_SIMILAR_INSTRUMENTS
)

HARMONY_PROGRAMS = get_programs(
    HARMONY_INSTRUMENTS
)


# ============================================================
# BATERIA - PROGRAMS
# ============================================================

# Em General MIDI, bateria normalmente é identificada pelo
# canal MIDI e não pelo program. Ainda assim, o PrettyMIDI
# mantém um program associado ao Instrument.
#
# Mantemos alguns programas diferentes para permitir que
# arquivos que utilizem esse campo possam variar.

DRUM_PROGRAMS = [
    0,    # Acoustic Grand Piano
    24,   # Acoustic Guitar (nylon)
    32,   # Acoustic Bass
    40,   # Violin
    48,   # String Ensemble 1
]


# ============================================================
# PROBABILIDADE
# ============================================================


def get_probability(position, total_duration):
    """
    Retorna a probabilidade correspondente à parte da música.

    A música é dividida em 8 partes de duração igual.
    """

    if total_duration <= 0:
        return 0.0

    ratio = position / total_duration

    part = int(ratio * 8)

    # Proteção para o final exato da música.
    part = max(0, min(7, part))

    return PART_PROBABILITIES[part]


# ============================================================
# TEMPO
# ============================================================


def get_tempo(midi):
    """
    Obtém o BPM do MIDI.

    Caso não exista um tempo válido, utiliza DEFAULT_BPM.
    """

    tempos, _ = midi.get_tempo_changes()

    if len(tempos) == 0:
        return DEFAULT_BPM

    for tempo in tempos:

        if tempo > 0:
            return float(tempo)

    return DEFAULT_BPM


def get_beat_duration(midi):
    """
    Retorna a duração de um beat em segundos.
    """

    tempo = get_tempo(midi)

    if tempo <= 0:
        tempo = DEFAULT_BPM

    return 60.0 / tempo


def get_total_duration(midi):
    return midi.get_end_time()


# ============================================================
# ESCOLHA ALEATÓRIA
# ============================================================


def weighted_choice(items, weights):
    return random.choices(
        items,
        weights=weights,
        k=1,
    )[0]


# ============================================================
# HISTOGRAMA DE PITCH
# ============================================================


def pitch_class_histogram(notes):
    """
    Calcula a distribuição das 12 pitch classes.

    A duração da nota é utilizada como peso.
    """

    histogram = [0.0] * 12

    for note in notes:

        duration = max(
            note.end - note.start,
            0.01,
        )

        pitch_class = note.pitch % 12

        histogram[pitch_class] += duration

    return histogram


# ============================================================
# DETECÇÃO DE ACORDE
# ============================================================


def chord_score(histogram, root, major=True):
    """
    Mede o quanto o conjunto de notas se aproxima
    de uma tríade maior ou menor.
    """

    third = 4 if major else 3

    chord = {
        root % 12,
        (root + third) % 12,
        (root + 7) % 12,
    }

    total = sum(histogram)

    if total == 0:
        return 0.0

    score = 0.0

    for pc in range(12):

        if pc in chord:
            score += histogram[pc]

        else:
            score -= histogram[pc] * 0.20

    return score / total


def detect_chord(notes):
    """
    Detecta aproximadamente o acorde predominante.
    """

    if not notes:
        return None

    histogram = pitch_class_histogram(notes)

    best_root = None
    best_major = True
    best_score = float("-inf")

    for root in range(12):

        score_major = chord_score(
            histogram,
            root,
            major=True,
        )

        if score_major > best_score:
            best_score = score_major
            best_root = root
            best_major = True

        score_minor = chord_score(
            histogram,
            root,
            major=False,
        )

        if score_minor > best_score:
            best_score = score_minor
            best_root = root
            best_major = False

    return best_root, best_major


def get_chord_notes(root, major):
    """
    Retorna as pitch classes da tríade.
    """

    third = 4 if major else 3

    return [
        root % 12,
        (root + third) % 12,
        (root + 7) % 12,
    ]


# ============================================================
# MAPA HARMÔNICO
# ============================================================


def build_chord_map(midi):
    """
    Divide a música em janelas de 4 compassos e detecta
    o acorde predominante em cada janela.
    """

    beat_duration = get_beat_duration(midi)

    window_duration = (
        CHORD_WINDOW_BEATS * beat_duration
    )

    total_duration = get_total_duration(midi)

    melodic_notes = []

    for instrument in midi.instruments:

        if instrument.is_drum:
            continue

        melodic_notes.extend(
            instrument.notes
        )

    chord_map = []

    current_start = 0.0

    while current_start < total_duration:

        current_end = min(
            current_start + window_duration,
            total_duration,
        )

        notes = [
            note
            for note in melodic_notes
            if note.start < current_end
            and note.end > current_start
        ]

        chord = detect_chord(notes)

        if chord is None:

            chord_pcs = None

        else:

            root, major = chord

            chord_pcs = get_chord_notes(
                root,
                major,
            )

        chord_map.append(
            (
                current_start,
                current_end,
                chord_pcs,
            )
        )

        current_start = current_end

    return chord_map


def get_chord_at_time(chord_map, time):
    """
    Retorna o acorde predominante em determinado instante.
    """

    for start, end, chord_pcs in chord_map:

        if start <= time < end:
            return chord_pcs

    return None


# ============================================================
# REFERÊNCIA HARMÔNICA PARA PISTAS VAZIAS
# ============================================================


def get_reference_instrument(midi):
    """
    Retorna a primeira pista não-bateria que possua notas.

    Essa pista serve como referência para pistas vazias.
    """

    for instrument in midi.instruments:

        if instrument.is_drum:
            continue

        if instrument.notes:
            return instrument

    return None


def get_reference_range(reference_instrument):
    """
    Obtém a tessitura da pista de referência.
    """

    if reference_instrument is None:
        return 48, 72

    pitches = [
        note.pitch
        for note in reference_instrument.notes
    ]

    if not pitches:
        return 48, 72

    return (
        min(pitches),
        max(pitches),
    )


# ============================================================
# TESSITURA
# ============================================================


def get_instrument_range(instrument):
    """
    Obtém a tessitura observada da pista.
    """

    if not instrument.notes:
        return 48, 72

    pitches = [
        note.pitch
        for note in instrument.notes
    ]

    return (
        min(pitches),
        max(pitches),
    )


# ============================================================
# GERAÇÃO DE PITCH
# ============================================================


def generate_pitch_from_chord(
    chord_pcs,
    minimum,
    maximum,
):
    """
    Escolhe uma nota pertencente ao acorde dentro
    da tessitura especificada.
    """

    if not chord_pcs:
        return None

    candidates = [
        pitch
        for pitch in range(
            minimum,
            maximum + 1,
        )
        if pitch % 12 in chord_pcs
    ]

    if not candidates:
        return None

    return random.choice(candidates)


# ============================================================
# VERIFICAÇÃO DE COLISÃO
# ============================================================


def note_collision(
    instrument,
    pitch,
    start,
    tolerance=0.05,
):
    """
    Evita inserir exatamente a mesma nota
    em um ponto já ocupado.
    """

    for note in instrument.notes:

        if note.pitch != pitch:
            continue

        if abs(note.start - start) <= tolerance:
            return True

    return False


# ============================================================
# DIVERSIFICAÇÃO DAS PISTAS MELÓDICAS
# ============================================================


def diversify_melodic_track(
    instrument,
    chord_map,
    total_duration,
    beat_duration,
    reference_range,
):
    """
    Adiciona notas pertencentes ao acorde.

    Para pistas existentes:
        usa a tessitura da própria pista.

    Para pistas vazias:
        usa a tessitura da primeira pista
        não-bateria que possui notas.
    """

    is_empty = len(instrument.notes) == 0

    # --------------------------------------------------------
    # Tessitura
    # --------------------------------------------------------

    if is_empty:

        minimum_pitch, maximum_pitch = reference_range

    else:

        minimum_pitch, maximum_pitch = (
            get_instrument_range(instrument)
        )

    # --------------------------------------------------------
    # Limite de notas
    # --------------------------------------------------------

    if is_empty:

        max_added = EMPTY_TRACK_MAX_NOTES

    else:

        original_note_count = len(
            instrument.notes
        )

        max_added = max(
            1,
            int(
                original_note_count
                * MAX_ADDED_RATIO
            ),
        )

    added = 0

    # Meio beat
    step = beat_duration / 2.0

    current_time = 0.0

    while current_time < total_duration:

        if added >= max_added:
            break

        probability = get_probability(
            current_time,
            total_duration,
        )

        if random.random() < probability:

            chord_pcs = get_chord_at_time(
                chord_map,
                current_time,
            )

            if chord_pcs:

                pitch = generate_pitch_from_chord(
                    chord_pcs,
                    minimum_pitch,
                    maximum_pitch,
                )

                if pitch is not None:

                    duration = random.uniform(
                        MIN_NOTE_DURATION,
                        min(
                            MAX_NOTE_DURATION,
                            beat_duration,
                        ),
                    )

                    end = min(
                        current_time + duration,
                        total_duration,
                    )

                    # ------------------------------------------------
                    # Para pistas não vazias, evita duplicação.
                    # ------------------------------------------------

                    if not is_empty:

                        if note_collision(
                            instrument,
                            pitch,
                            current_time,
                        ):

                            current_time += step
                            continue

                    # ------------------------------------------------
                    # Velocity
                    # ------------------------------------------------

                    if instrument.notes:

                        existing_note = random.choice(
                            instrument.notes
                        )

                        velocity = int(
                            existing_note.velocity
                            * random.uniform(
                                MIN_VELOCITY_FACTOR,
                                MAX_VELOCITY_FACTOR,
                            )
                        )

                    else:

                        velocity = random.randint(
                            45,
                            80,
                        )

                    velocity = max(
                        1,
                        min(127, velocity),
                    )

                    new_note = pretty_midi.Note(
                        velocity=velocity,
                        pitch=pitch,
                        start=current_time,
                        end=end,
                    )

                    instrument.notes.append(
                        new_note
                    )

                    added += 1

        current_time += step

    return added


# ============================================================
# DIVERSIFICAÇÃO DA BATERIA
# ============================================================


def drum_note_exists(
    instrument,
    pitch,
    time,
    tolerance=0.05,
):
    """
    Verifica se já existe uma nota de bateria
    próxima do instante desejado.
    """

    for note in instrument.notes:

        if note.pitch != pitch:
            continue

        if abs(note.start - time) <= tolerance:
            return True

    return False


def diversify_drums(
    instrument,
    total_duration,
    beat_duration,
):
    """
    Adiciona elementos de bateria sobre a bateria existente.

    A probabilidade depende das 8 partes da música.
    """

    if not instrument.is_drum:
        return 0

    if not instrument.notes:
        return 0

    added = 0

    step = beat_duration / 2.0

    current_time = 0.0

    while current_time < total_duration:

        probability = get_probability(
            current_time,
            total_duration,
        )

        if random.random() < probability:

            element = weighted_choice(
                DRUM_ELEMENTS,
                DRUM_WEIGHTS,
            )

            # Crash aparece menos.
            if (
                element == CRASH
                and random.random() > 0.25
            ):

                current_time += step
                continue

            if not drum_note_exists(
                instrument,
                element,
                current_time,
            ):

                velocity = random.randint(
                    45,
                    90,
                )

                if element == CRASH:

                    velocity = random.randint(
                        60,
                        95,
                    )

                if element in (
                    KICK,
                    SNARE,
                ):

                    duration = random.uniform(
                        0.05,
                        0.15,
                    )

                else:

                    duration = random.uniform(
                        0.03,
                        0.10,
                    )

                note = pretty_midi.Note(
                    velocity=velocity,
                    pitch=element,
                    start=current_time,
                    end=min(
                        current_time + duration,
                        total_duration,
                    ),
                )

                instrument.notes.append(
                    note
                )

                added += 1

        current_time += step

    return added


# ============================================================
# DIVERSIFICAÇÃO DE INSTRUMENTOS
# ============================================================


def get_track_name(instrument):
    """
    Retorna o nome da pista em formato normalizado.
    """

    if instrument.name is None:
        return ""

    return instrument.name.strip().lower()


def choose_different_program(
    current_program,
    candidate_programs,
):
    """
    Escolhe um programa diferente do atual sempre que
    houver outra opção disponível.
    """

    candidates = [
        program
        for program in candidate_programs
        if program != current_program
    ]

    if not candidates:
        return current_program

    return random.choice(candidates)


def diversify_instrument(
    instrument,
    candidate_programs,
):
    """
    Troca o instrumento/programa de uma pista.

    O nome da pista é preservado.
    """

    if not candidate_programs:
        return False

    old_program = instrument.program

    new_program = choose_different_program(
        old_program,
        candidate_programs,
    )

    if new_program == old_program:
        return False

    instrument.program = new_program

    return True


def diversify_instruments(midi):
    """
    Diversifica os instrumentos das pistas de acordo com
    o nome de cada pista.

    Grupos:

        Drums
        String1
        String2
        Bass1
        Bass2
        Guitar1
        Guitar2
        Harmony

    Pistas que não correspondem a nenhum desses nomes
    não são modificadas.
    """

    changed = 0

    for instrument in midi.instruments:

        track_name = get_track_name(
            instrument
        )

        # ----------------------------------------------------
        # DRUMS
        # ----------------------------------------------------

        if track_name == "drums":

            # Continua sendo uma pista de bateria.
            instrument.is_drum = True

            if diversify_instrument(
                instrument,
                DRUM_PROGRAMS,
            ):

                changed += 1

            continue

        # ----------------------------------------------------
        # STRING1
        # ----------------------------------------------------

        if track_name == "string1":

            if diversify_instrument(
                instrument,
                STRING_PROGRAMS,
            ):

                changed += 1

            continue

        # ----------------------------------------------------
        # STRING2
        # ----------------------------------------------------

        if track_name == "string2":

            if diversify_instrument(
                instrument,
                STRING_SIMILAR_PROGRAMS,
            ):

                changed += 1

            continue

        # ----------------------------------------------------
        # BASS1
        # ----------------------------------------------------

        if track_name == "bass1":

            if diversify_instrument(
                instrument,
                BASS_PROGRAMS,
            ):

                changed += 1

            continue

        # ----------------------------------------------------
        # BASS2
        # ----------------------------------------------------

        if track_name == "bass2":

            if diversify_instrument(
                instrument,
                BASS_SIMILAR_PROGRAMS,
            ):

                changed += 1

            continue

        # ----------------------------------------------------
        # GUITAR1
        # ----------------------------------------------------

        if track_name == "guitar1":

            if diversify_instrument(
                instrument,
                GUITAR_PROGRAMS,
            ):

                changed += 1

            continue

        # ----------------------------------------------------
        # GUITAR2
        # ----------------------------------------------------

        if track_name == "guitar2":

            if diversify_instrument(
                instrument,
                GUITAR_SIMILAR_PROGRAMS,
            ):

                changed += 1

            continue

        # ----------------------------------------------------
        # HARMONY
        # ----------------------------------------------------

        if track_name == "harmony":

            if diversify_instrument(
                instrument,
                HARMONY_PROGRAMS,
            ):

                changed += 1

            continue

    return changed


# ============================================================
# ORDENAÇÃO
# ============================================================


def sort_notes(midi):
    """
    Ordena as notas de todas as pistas.
    """

    for instrument in midi.instruments:

        instrument.notes.sort(
            key=lambda note: (
                note.start,
                note.pitch,
                note.end,
            )
        )


# ============================================================
# PRINCIPAL
# ============================================================


def diversify_midi(
    input_path,
    output_path,
    diversify_midi_notes=False,
    diversify_midi_instruments=False,
    seed=None,
):
    """
    Diversifica um arquivo MIDI.

    diversify_midi_notes:
        Se True, adiciona notas como na implementação original.

    diversify_midi_instruments:
        Se True, altera os instrumentos das pistas de acordo
        com os grupos definidos acima.
    """

    if seed is not None:
        random.seed(seed)

    midi = pretty_midi.PrettyMIDI(
        input_path
    )

    total_duration = get_total_duration(
        midi
    )

    beat_duration = get_beat_duration(
        midi
    )

    # --------------------------------------------------------
    # Diversificação de instrumentos
    # --------------------------------------------------------
    #
    # Esta parte é independente da diversificação de notas.
    #
    # --------------------------------------------------------

    total_changed_instruments = 0

    if diversify_midi_instruments:

        total_changed_instruments = (
            diversify_instruments(midi)
        )

    # --------------------------------------------------------
    # Se a diversificação de notas estiver desativada,
    # não fazemos nenhuma operação relacionada a notas.
    # --------------------------------------------------------

    total_added_drums = 0
    total_added_melodic = 0

    if diversify_midi_notes:

        # ----------------------------------------------------
        # Referência para pistas vazias
        # ----------------------------------------------------

        reference_instrument = (
            get_reference_instrument(midi)
        )

        if reference_instrument:

            reference_range = (
                get_reference_range(
                    reference_instrument
                )
            )

        else:

            reference_range = (48, 72)

        # ----------------------------------------------------
        # Detecta acordes ANTES de adicionar notas.
        # ----------------------------------------------------

        chord_map = build_chord_map(midi)

        # ----------------------------------------------------
        # Diversificação das notas
        # ----------------------------------------------------

        for instrument in midi.instruments:

            if instrument.is_drum:

                added = diversify_drums(
                    instrument,
                    total_duration,
                    beat_duration,
                )

                total_added_drums += added

            else:

                added = diversify_melodic_track(
                    instrument,
                    chord_map,
                    total_duration,
                    beat_duration,
                    reference_range,
                )

                total_added_melodic += added

    # --------------------------------------------------------
    # Ordenação
    # --------------------------------------------------------

    sort_notes(midi)

    # --------------------------------------------------------
    # Salva
    # --------------------------------------------------------

    midi.write(output_path)

    return {
        "added_drums": total_added_drums,
        "added_melodic": total_added_melodic,
        "changed_instruments": total_changed_instruments,
    }


# ============================================================
# CLI
# ============================================================


def main():

    parser = argparse.ArgumentParser(
        description=(
            "Diversifica um arquivo MIDI "
            "adicionando notas e/ou alterando "
            "os instrumentos das pistas."
        )
    )

    parser.add_argument(
        "input",
        help="MIDI de entrada",
    )

    parser.add_argument(
        "output",
        help="MIDI de saída",
    )

    parser.add_argument(
        "--diversify-notes",
        action="store_true",
        help=(
            "Ativa a diversificação das notas."
        ),
    )

    parser.add_argument(
        "--diversify-instruments",
        action="store_true",
        help=(
            "Ativa a diversificação dos instrumentos."
        ),
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Seed para reproduzir o resultado",
    )

    args = parser.parse_args()

    diversify_midi(
        input_path=args.input,
        output_path=args.output,
        diversify_midi_notes=args.diversify_notes,
        diversify_midi_instruments=args.diversify_instruments,
        seed=args.seed,
    )


if __name__ == "__main__":
    main()