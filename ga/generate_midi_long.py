import random

import pretty_midi

from constants import *


def melody_pitch_range():
    """Converte os limites configuráveis em nomes de nota para pitches MIDI."""

    return (
        pretty_midi.note_name_to_number(MIN_MELODY_PIT),
        pretty_midi.note_name_to_number(MAX_MELODY_PIT),
    )


def move_pitch_into_range(pitch):
    """Move o pitch por oitavas, preservando sua classe dentro do range."""

    min_pitch, max_pitch = melody_pitch_range()
    candidates = [
        candidate
        for candidate in range(min_pitch, max_pitch + 1)
        if candidate % 12 == pitch % 12
    ]

    return min(candidates, key=lambda candidate: abs(candidate - pitch))


def tune_pitch_to_chord(pitch, chord):
    """Retorna o pitch MIDI mais próximo pertencente ao MChord, em qualquer oitava."""

    chord_pitch_classes = {
        chord_note % 12
        for chord_note in chord.notes
    }
    min_pitch, max_pitch = melody_pitch_range()
    candidates = [
        candidate
        for candidate in range(min_pitch, max_pitch + 1)
        if candidate % 12 in chord_pitch_classes
    ]

    return min(candidates, key=lambda candidate: abs(candidate - pitch))


def lower_chord_tone(pitch, chord):
    """Retorna o tom de acorde mais próximo abaixo do pitch recebido."""

    chord_pitch_classes = {
        chord_note % 12
        for chord_note in chord.notes
    }
    min_pitch, _ = melody_pitch_range()
    candidates = [
        candidate
        for candidate in range(min_pitch, pitch)
        if candidate % 12 in chord_pitch_classes
    ]

    return max(candidates) if candidates else None


def chord_voice_pair(pitch, chord):
    """Busca um par de notas do acorde no range configurado, com voz inferior."""

    chord_pitch_classes = {
        chord_note % 12
        for chord_note in chord.notes
    }
    min_pitch, max_pitch = melody_pitch_range()
    chord_pitches = [
        candidate
        for candidate in range(min_pitch, max_pitch + 1)
        if candidate % 12 in chord_pitch_classes
    ]
    pairs = [
        (upper, lower)
        for upper in chord_pitches
        for lower in chord_pitches
        if lower < upper
    ]

    if not pairs:
        return None

    return min(
        pairs,
        key=lambda pair: (abs(pair[0] - pitch), pair[0] - pair[1]),
    )


def extend_notes_to_next_onset(notes):
    """Estende notas selecionadas até o próximo ataque distinto da pista."""

    ordered_starts = sorted({note[0] for note in notes})
    next_start_by_start = {
        current: following
        for current, following in zip(
            ordered_starts,
            ordered_starts[1:],
        )
    }

    extended_notes = []

    for note in notes:
        start, end = note[:2]
        next_start = next_start_by_start.get(start)

        if (
            next_start is not None
            and end < next_start
            and random.random() < EXTEND_PROBABILITY
        ):
            end = next_start

        extended_notes.append((start, end, *note[2:]))

    return extended_notes


def resolve_same_pitch_overlaps(notes):
    """Evita note-offs ambíguos entre notas iguais sobrepostas na Melody."""

    notes_by_pitch = {}
    for start, end, pitch, velocity in notes:
        notes_by_pitch.setdefault(pitch, []).append(
            (start, end, pitch, velocity)
        )

    resolved_notes = []

    for pitch_notes in notes_by_pitch.values():
        pitch_notes.sort(key=lambda note: (note[0], note[1]))
        resolved_pitch_notes = []

        for start, end, pitch, velocity in pitch_notes:
            if resolved_pitch_notes and start == resolved_pitch_notes[-1][0]:
                previous = resolved_pitch_notes[-1]
                resolved_pitch_notes[-1] = (
                    start,
                    max(previous[1], end),
                    pitch,
                    max(previous[3], velocity),
                )
                continue

            if resolved_pitch_notes and start < resolved_pitch_notes[-1][1]:
                previous = resolved_pitch_notes[-1]
                resolved_pitch_notes[-1] = (
                    previous[0],
                    start,
                    previous[2],
                    previous[3],
                )

            resolved_pitch_notes.append((start, end, pitch, velocity))

        resolved_notes.extend(resolved_pitch_notes)

    return sorted(resolved_notes, key=lambda note: (note[0], note[2]))


# ============================================================
# TRILHAS EM MEMÓRIA
# ============================================================

def build_tracks(
    individual,
    seconds_per_step=SECONDS_PER_STEP,
    repetitions=NUM_BAT1,
    group_repetitions=GROUP_REPETITIONS
) -> list:

    tracks = []

    bar_duration = (
        STEPS_PER_BAR
        * seconds_per_step
    )

    # ========================================================
    # FINAL DA FORMA MUSICAL
    # ========================================================

    total_music_bars = sum(
        number_of_bars
        for _section_name, number_of_bars
        in DRUM_SECTIONS
    )

    music_end = (
        total_music_bars
        * bar_duration
    )

    # ========================================================
    # DRUMS
    # ========================================================

    drum_notes = []

    drum_patterns = {
        "bati": individual.bati,
        "bat1": individual.bat1,
        "bat2": individual.bat2,
        "batf": individual.batf,
    }

    bar_index = 0

    for section_name, number_of_bars in DRUM_SECTIONS:

        drum_pattern = drum_patterns[section_name]

        for _ in range(number_of_bars):

            bar_offset = (
                bar_index
                * STEPS_PER_BAR
                * seconds_per_step
            )

            bar_index += 1

            for step, gene in enumerate(drum_pattern):

                start = (
                    bar_offset
                    + step * seconds_per_step
                )

                end = (
                    start
                    + seconds_per_step
                )

                for drum in gene.notes:

                    if drum not in DRUM_PITCHES:
                        raise ValueError(
                            f"Elemento de bateria inválido: {drum}"
                        )

                    pitch = DRUM_PITCHES[drum]

                    drum_notes.append(
                        (start, end, pitch)
                    )

    tracks.append({
        "name": "Drums",
        "program": 0,
        "is_drum": True,
        "velocity": DRUM_TRACK_VELOCITY,
        "notes": drum_notes,
    })

    # ========================================================
    # STRING1
    # ========================================================

    string_notes = []

    chords = individual.genotype.mchords

    group1 = chords[:MCHORDS_PER_GROUP]
    group2 = chords[MCHORDS_PER_GROUP:]
    chord_by_bar = {}

    bar_index = 0

    for section_name, number_of_bars in STRING_SECTIONS:

        if section_name is None:

            bar_index += number_of_bars
            continue

        group = (
            group1
            if section_name == "group1"
            else group2
        )

        for local_bar in range(number_of_bars):

            chord = group[
                local_bar % len(group)
            ]

            chord_by_bar[bar_index] = chord

            start = (
                bar_index
                * bar_duration
            )

            end = (
                start
                + bar_duration
            )

            bar_index += 1

            for pitch in chord.notes:

                string_notes.append(
                    (start, end, pitch)
                )

    tracks.append({
        "name": "String1",
        "program": STRING_PROGRAM,
        "is_drum": False,
        "velocity": STRING_TRACK_VELOCITY,
        "notes": string_notes,
    })

    # ========================================================
    # STRING2
    #
    # Dobra String1 uma oitava acima.
    # ========================================================

    string2_notes = []

    string2_bar_index = 0

    for section_group, number_of_bars in STRING2_SECTIONS:

        if section_group is None:

            string2_bar_index += number_of_bars
            continue

        string2_group = (
            group1
            if section_group == "group1"
            else group2
        )

        string2_chord_index = 0

        for _ in range(number_of_bars):

            chord = string2_group[
                string2_chord_index
                % len(string2_group)
            ]

            string2_chord_index += 1

            start = (
                string2_bar_index
                * bar_duration
            )

            end = (
                start
                + bar_duration
            )

            for pitch in chord.notes[:3]:

                string2_notes.append(
                    (
                        start,
                        end,
                        pitch + STRING2_OCTAVE_SHIFT
                    )
                )

            string2_bar_index += 1

    tracks.append({
        "name": "String2",
        "program": STRING2_PROGRAM,
        "is_drum": False,
        "velocity": STRING2_TRACK_VELOCITY,
        "notes": string2_notes,
        "control_changes": [],
    })

    # ========================================================
    # BASS1
    # ========================================================

    bass_notes = []

    bass_bar_index = 0

    for section_name, number_of_bars in BASS_SECTIONS:

        if section_name is None:

            bass_bar_index += number_of_bars
            continue

        group = (
            group1
            if section_name == "group1"
            else group2
        )

        bass_pattern = (
            individual.bass_patt1
            if section_name == "group1"
            else individual.bass_patt2
        )

        for local_bar in range(number_of_bars):

            chord = group[
                local_bar % len(group)
            ]

            chord_notes = chord.notes

            bar_start = (
                bass_bar_index
                * bar_duration
            )

            bass_bar_index += 1

            for note_index, (
                bass_note,
                start_position
            ) in enumerate(
                zip(
                    bass_pattern.notes,
                    bass_pattern.start_positions
                )
            ):

                start = (
                    bar_start
                    + (
                        start_position
                        / BASS_BAR_UNITS
                        * bar_duration
                    )
                )

                end = (
                    start
                    + (
                        bass_note.duration
                        / BASS_BAR_UNITS
                        * bar_duration
                    )
                )

                pitch = chord_notes[
                    note_index % len(chord_notes)
                ]

                bass_notes.append(
                    (start, end, pitch)
                )

    tracks.append({
        "name": "Bass1",
        "program": BASS_PROGRAM,
        "is_drum": False,
        "velocity": BASS_TRACK_VELOCITY,
        "notes": bass_notes,
    })

    # ========================================================
    # BASS2
    #
    # Copia a nota mais grave da String1 uma oitava abaixo.
    # ========================================================

    bass2_notes = []

    grouped_string_notes = {}

    for start, end, pitch in string_notes:

        key = round(start, 6)

        if key not in grouped_string_notes:
            grouped_string_notes[key] = []

        grouped_string_notes[key].append(
            (start, end, pitch)
        )

    for notes_at_time in grouped_string_notes.values():

        lowest_note = min(
            notes_at_time,
            key=lambda note: note[2]
        )

        start, end, pitch = lowest_note

        bass2_notes.append(
            (
                start,
                end,
                pitch - 12
            )
        )

    tracks.append({
        "name": "Bass2",
        "program": BASS2_PROGRAM,
        "is_drum": False,
        "velocity": BASS2_TRACK_VELOCITY,
        "notes": bass2_notes,
        "control_changes": [],
    })

    # ========================================================
    # GUITAR1 / ARPEGGIO
    #
    # Entra após 9 compassos de silêncio.
    # ========================================================

    arpeggio_notes = []

    arpeggio_bar_index = 0

    pedal_events = []

    for section_name, number_of_bars in ARPEGGIO_SECTIONS:

        if section_name is None:

            arpeggio_bar_index += number_of_bars
            continue

        group = (
            group1
            if section_name == "group1"
            else group2
        )

        arp_pattern = (
            individual.arp_patt1
            if section_name == "group1"
            else individual.arp_patt2
        )

        for local_bar in range(number_of_bars):

            chord = group[
                local_bar % len(group)
            ]

            chord_notes = chord.notes

            bar_start = (
                arpeggio_bar_index
                * bar_duration
            )

            arpeggio_bar_index += 1

            # ------------------------------------------------
            # Pedal de sustentação
            # ------------------------------------------------

            pedal_events.append(
                (
                    SUSTAIN_PEDAL_CC,
                    SUSTAIN_PEDAL_ON,
                    bar_start
                )
            )

            pedal_events.append(
                (
                    SUSTAIN_PEDAL_CC,
                    SUSTAIN_PEDAL_OFF,
                    bar_start + bar_duration
                )
            )

            # ------------------------------------------------
            # Notas do arpejo
            # ------------------------------------------------

            for note_index, start_position in enumerate(
                arp_pattern.start_positions
            ):

                start = (
                    bar_start
                    + (
                        start_position
                        / ARP_BAR_UNITS
                        * bar_duration
                    )
                )

                end = (
                    start
                    + (
                        arp_pattern.step
                        / ARP_BAR_UNITS
                        * bar_duration
                    )
                )

                chord_tone_index = arp_pattern.note_order[
                    note_index % len(arp_pattern.note_order)
                ]
                pitch = chord_notes[chord_tone_index]

                arpeggio_notes.append(
                    (start, end, pitch)
                )

    tracks.append({
        "name": "Guitar1",
        "program": ARPEGGIO_PROGRAM,
        "is_drum": False,
        "velocity": ARPEGGIO_TRACK_VELOCITY,
        "notes": arpeggio_notes,
        "control_changes": pedal_events,
    })

    # ========================================================
    # GUITAR2
    #
    # REGRA:
    #
    # A partir do compasso onde String2 começa a tocar,
    # copia EXATAMENTE as notas da Guitar1 que acontecem
    # a partir desse ponto.
    #
    # A única alteração é:
    #
    #     Guitar1 pitch + 12
    #
    # NÃO:
    #   - deslocar a Guitar1
    #   - reiniciar a sequência
    #   - usar atraso aleatório
    #   - alterar o ritmo
    #
    # Exemplo:
    #
    # Guitar1:
    #
    # compasso 10: C4 E4 G4
    # compasso 11: D4 F4 A4
    # compasso 12: E4 G4 B4
    #
    # String2 começa no compasso 11.
    #
    # Guitar2:
    #
    # compasso 11: D5 F5 A5
    # compasso 12: E5 G5 B5
    #
    # Ou seja, os tempos das notas são preservados.
    # ========================================================

    guitar2_notes = []

    if string2_notes and arpeggio_notes:

        # ----------------------------------------------------
        # Primeiro instante em que String2 toca
        # ----------------------------------------------------

        string2_start = min(
            start
            for start, _end, _pitch
            in string2_notes
        )

        # ----------------------------------------------------
        # Copia somente as notas da Guitar1 que começam
        # a partir do início da String2.
        #
        # O tempo NÃO é deslocado.
        # ----------------------------------------------------

        for start, end, pitch in arpeggio_notes:

            if start < string2_start:
                continue

            # ------------------------------------------------
            # Mantém exatamente o mesmo início e fim.
            #
            # Apenas sobe uma oitava.
            # ------------------------------------------------

            new_start = start
            new_end = end
            new_pitch = pitch + 12

            # ------------------------------------------------
            # Segurança: não ultrapassar o final da música.
            # ------------------------------------------------

            if new_start >= music_end:
                continue

            if new_end > music_end:
                new_end = music_end

            if new_end <= new_start:
                continue

            guitar2_notes.append(
                (
                    new_start,
                    new_end,
                    new_pitch
                )
            )

    tracks.append({
        "name": "Guitar2",
        "program": ARPEGGIO2_PROGRAM,
        "is_drum": False,
        "velocity": ARPEGGIO2_TRACK_VELOCITY,
        "notes": guitar2_notes,
        "control_changes": [],
    })

    # ========================================================
    # MELODY
    #
    # A distribuição das seções é configurada em MELODY_SECTIONS.
    # ========================================================

    melody_notes = []
    melody_patterns = {
        "mel_patt1": (individual.mel_patt1, individual.bat1),
        "mel_patt2": (individual.mel_patt2, individual.bat2),
    }

    melody_bar_index = 0

    for section_name, number_of_bars in MELODY_SECTIONS:

        if section_name is None:
            melody_bar_index += number_of_bars
            continue

        pattern, drum_pattern = melody_patterns[section_name]

        for pattern_offset in range(
            0,
            number_of_bars,
            pattern.NUM_BARS,
        ):

            active_bars = min(
                pattern.NUM_BARS,
                number_of_bars - pattern_offset,
            )
            active_units = active_bars * pattern.BAR_UNITS
            pattern_start = (
                melody_bar_index + pattern_offset
            ) * bar_duration
            section_end = pattern_start + active_bars * bar_duration

            section_notes = [
                note
                for note in pattern.notes
                if note.position < active_units
            ]

            drum_onsets = sorted(
                (
                    bar_index * pattern.BAR_UNITS
                    + (step * pattern.BAR_UNITS) // len(drum_pattern),
                    bar_index,
                    step,
                )
                for bar_index in range(active_bars)
                for step, gene in enumerate(drum_pattern)
                if gene.notes
            )

            note_count = len(section_notes)

            for note_index, note in enumerate(section_notes):

                position = note.position
                aligned_drum_onset = None

                if (
                    AUTOCOMP_MELODY
                    and note_count > 0
                    and random.random() < COMP_PROBABILITY
                ):
                    uniform_position = (
                        note_index * active_units
                    ) // note_count

                    if drum_onsets:
                        aligned_drum_onset = min(
                            drum_onsets,
                            key=lambda onset: abs(
                                onset[0] - uniform_position
                            ),
                        )
                        position = aligned_drum_onset[0]
                    else:
                        position = uniform_position

                if aligned_drum_onset is not None:
                    relative_bar, drum_step = aligned_drum_onset[1:]
                    note_bar_index = (
                        melody_bar_index
                        + pattern_offset
                        + relative_bar
                    )
                    start = (
                        note_bar_index
                        * STEPS_PER_BAR
                        * seconds_per_step
                        + drum_step * seconds_per_step
                    )
                else:
                    start = (
                        pattern_start
                        + position
                        / pattern.BAR_UNITS
                        * bar_duration
                    )
                    note_bar_index = (
                        melody_bar_index
                        + pattern_offset
                        + position // pattern.BAR_UNITS
                    )

                note_duration = min(
                    note.duration,
                    active_units - note.position,
                )
                end = min(
                    start
                    + note_duration
                    / pattern.BAR_UNITS
                    * bar_duration,
                    section_end,
                )

                pitch = note.pitch
                chord = chord_by_bar.get(note_bar_index)

                if (
                    AUTOTUNE_MELODY
                    and chord is not None
                    and random.random() < TUNE_PROBABILITY
                ):
                    pitch = tune_pitch_to_chord(pitch, chord)

                pitch = move_pitch_into_range(pitch)

                velocity = max(
                    MIN_MELODY_VEL,
                    min(MAX_MELODY_VEL, note.velocity),
                )

                melody_notes.append(
                    (
                        start,
                        end,
                        pitch,
                        velocity,
                    )
                )

        melody_bar_index += number_of_bars

    # A segunda voz começa quando termina a primeira seção group2
    # dos MChords e a harmonia retorna a group1.
    bars_through_first_chorus = 0
    first_chorus_end_bar = sum(
        number_of_bars
        for _section_name, number_of_bars in STRING_SECTIONS
    )
    for section_name, number_of_bars in STRING_SECTIONS:
        bars_through_first_chorus += number_of_bars
        if section_name == "group2":
            first_chorus_end_bar = bars_through_first_chorus
            break

    first_chorus_end = first_chorus_end_bar * bar_duration
    second_voice_notes = []

    for note_index, (start, end, pitch, velocity) in enumerate(melody_notes):
        if start < first_chorus_end or start >= music_end:
            continue

        note_bar_index = int(start / bar_duration)
        chord = chord_by_bar.get(note_bar_index)

        if chord is None:
            continue

        lower_pitch = lower_chord_tone(pitch, chord)

        if lower_pitch is None:
            voice_pair = chord_voice_pair(pitch, chord)

            if voice_pair is None:
                continue

            pitch, lower_pitch = voice_pair
            melody_notes[note_index] = (
                start,
                end,
                pitch,
                velocity,
            )

        if lower_pitch is not None:
            second_voice_notes.append(
                (start, end, lower_pitch, velocity)
            )

    melody_notes.extend(second_voice_notes)

    # Mantém a pista identificável no MIDI e preserva a duração
    # completa da forma, mesmo que os padrões melódicos estejam vazios.
    melody_notes.append(
        (
            music_end,
            music_end + EMPTY_TRACK_ANCHOR_DURATION,
            EMPTY_TRACK_ANCHOR_PITCH,
            EMPTY_TRACK_ANCHOR_VELOCITY,
        )
    )

    if EXTEND_NOTES:
        for track in tracks:
            track["notes"] = extend_notes_to_next_onset(
                track["notes"]
            )

        # Estende as notas musicais antes da âncora técnica, evitando
        # que a última nota seja prolongada até o fim artificial do MIDI.
        melody_notes = extend_notes_to_next_onset(
            melody_notes[:-1]
        ) + melody_notes[-1:]

    # O MIDI associa note-offs por canal e pitch. Sobreposições do mesmo
    # pitch podem encerrar uma nota antes do fim esperado durante a reprodução.
    musical_melody_notes = resolve_same_pitch_overlaps(melody_notes[:-1])
    melody_notes = musical_melody_notes + melody_notes[-1:]

    tracks.append({
        "name": "Melody",
        "program": MELODY_PROGRAM,
        "is_drum": False,
        "velocity": MELODY_TRACK_VELOCITY,
        "notes": melody_notes,
        "control_changes": [],
    })

    return tracks


# ============================================================
# GERAÇÃO DO MIDI
# ============================================================

def generate_midi(
    individual,
    output_path="generated.mid",
    bpm=None
):
    """
    Gera um arquivo MIDI a partir de um Individual.
    """

    tempo = float(
        BPM if bpm is None else bpm
    )

    seconds_per_step = (
        60.0 / tempo
    ) / STEPS_PER_BEAT

    midi = pretty_midi.PrettyMIDI(
        initial_tempo=tempo
    )

    bar_duration = (
        60.0 / tempo
    ) * BEATS_PER_BAR

    # ========================================================
    # TRILHAS
    # ========================================================

    tracks = build_tracks(
        individual,
        seconds_per_step
    )

    global_end = max(
        (
            note[1]
            for track in tracks
            for note in track["notes"]
        ),
        default=0.0
    )

    if global_end <= 0.0:

        global_end = (
            FINAL_EMPTY_BARS
            * bar_duration
        )

    for track in tracks:

        instrument = pretty_midi.Instrument(
            program=track["program"],
            is_drum=track["is_drum"],
            name=track["name"]
        )

        # ----------------------------------------------------
        # Notas
        # ----------------------------------------------------

        for note_data in track["notes"]:

            start, end, pitch = note_data[:3]
            velocity = (
                note_data[3]
                if len(note_data) > 3
                else track["velocity"]
            )

            instrument.notes.append(
                pretty_midi.Note(
                    velocity=velocity,
                    pitch=pitch,
                    start=start,
                    end=end
                )
            )

        # ----------------------------------------------------
        # Control changes
        # ----------------------------------------------------

        for number, value, time in track.get(
            "control_changes",
            []
        ):

            instrument.control_changes.append(
                pretty_midi.ControlChange(
                    number=number,
                    value=value,
                    time=time
                )
            )

        # ----------------------------------------------------
        # Compasso final silencioso
        # ----------------------------------------------------

        silent_start = global_end

        silent_end = (
            silent_start
            + FINAL_EMPTY_BARS
            * bar_duration
        )

        instrument.notes.append(
            pretty_midi.Note(
                velocity=0,
                pitch=36 if track["is_drum"] else 60,
                start=silent_start,
                end=silent_end
            )
        )

        # ----------------------------------------------------
        # Âncora para trilhas vazias
        # ----------------------------------------------------

        if not track["notes"]:

            instrument.notes.append(
                pretty_midi.Note(
                    velocity=EMPTY_TRACK_ANCHOR_VELOCITY,
                    pitch=EMPTY_TRACK_ANCHOR_PITCH,
                    start=global_end,
                    end=(
                        global_end
                        + EMPTY_TRACK_ANCHOR_DURATION
                    )
                )
            )

        midi.instruments.append(
            instrument
        )

    # ========================================================
    # SALVAR
    # ========================================================

    midi.write(
        output_path
    )


# ============================================================
# TESTE
# ============================================================

if __name__ == "__main__":

    from individual import Individual

    individual = Individual()

    # --------------------------------------------------------
    # Exemplo de padrão de bateria
    # --------------------------------------------------------

    individual.bat1[0].notes = [0, 2]
    individual.bat1[1].notes = [2]
    individual.bat1[2].notes = [1, 2]
    individual.bat1[3].notes = [2]
    individual.bat1[4].notes = [0, 2]
    individual.bat1[5].notes = [2]
    individual.bat1[6].notes = [1, 2]
    individual.bat1[7].notes = [2]

    generate_midi(
        individual,
        output_path="generated.mid"
    )

    print(
        "MIDI gerado: generated.mid"
    )
