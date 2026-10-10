import random

from constants import *


class Gene:
    MAX_NOTES = GENE_MAX_NOTES

    def __init__(self, notes=None):
        if notes is None:
            count = random.randint(0, self.MAX_NOTES)
            self.notes = random.sample(
                range(Genotype.NUM_DRUMS),
                count
            )
        else:
            self.notes = list(notes)

        if len(self.notes) > self.MAX_NOTES:
            raise ValueError(
                f"Um Gene pode conter no máximo "
                f"{self.MAX_NOTES} elementos."
            )

        if len(self.notes) != len(set(self.notes)):
            raise ValueError(
                "Um Gene não pode conter elementos de bateria duplicados."
            )

        for note in self.notes:
            if not isinstance(note, int):
                raise TypeError(
                    "Cada elemento de bateria deve ser um inteiro."
                )

            if not 0 <= note < Genotype.NUM_DRUMS:
                raise ValueError(
                    f"Elemento de bateria inválido: {note}. "
                    f"O intervalo permitido é "
                    f"0-{Genotype.NUM_DRUMS - 1}."
                )

    def __repr__(self):
        return f"Gene({self.notes})"


class MChord:
    CHORD_INTERVALS = MCHORD_INTERVALS
    INVERSIONS = MCHORD_INVERSIONS
    MIN_NOTES = MCHORD_MIN_NOTES
    MAX_NOTES = MCHORD_MAX_NOTES
    MIN_MIDI_NOTE = MCHORD_MIN_MIDI_NOTE
    MAX_MIDI_NOTE = MCHORD_MAX_MIDI_NOTE
    ROOT_MIN_MIDI_NOTE = MCHORD_ROOT_MIN_MIDI_NOTE
    ROOT_MAX_MIDI_NOTE = MCHORD_ROOT_MAX_MIDI_NOTE

    @classmethod
    def normalize_note(cls, note):
        while note < cls.ROOT_MIN_MIDI_NOTE:
            note += 12

        while note > cls.ROOT_MAX_MIDI_NOTE:
            note -= 12

        return note

    @classmethod
    def _fit_window(cls, notes):
        notes = list(notes)

        while max(notes) > cls.ROOT_MAX_MIDI_NOTE:
            shifted = [note - 12 for note in notes]

            if min(shifted) < cls.MIN_MIDI_NOTE:
                break

            notes = shifted

        while min(notes) < cls.MIN_MIDI_NOTE:
            notes = [note + 12 for note in notes]

        while max(notes) > cls.MAX_MIDI_NOTE:
            shifted = [note - 12 for note in notes]

            if min(shifted) < cls.MIN_MIDI_NOTE:
                raise ValueError(
                    "A voicing do MChord não cabe na janela permitida."
                )

            notes = shifted

        return notes

    def __init__(self, root, chord_type="major", inversion=0):
        if not isinstance(root, int):
            raise TypeError(
                "A tônica do acorde deve ser um inteiro MIDI."
            )

        if chord_type not in self.CHORD_INTERVALS:
            raise ValueError(
                f"Tipo de acorde inválido: {chord_type}. "
                f"Tipos permitidos: {tuple(self.CHORD_INTERVALS)}."
            )

        if inversion not in self.INVERSIONS:
            raise ValueError(
                f"Inversão inválida: {inversion}. "
                f"Inversões permitidas: {self.INVERSIONS}."
            )

        intervals = self.CHORD_INTERVALS[chord_type]

        if not self.MIN_NOTES <= len(intervals) <= self.MAX_NOTES:
            raise ValueError(
                "A estrutura harmônica deve possuir entre "
                f"{self.MIN_NOTES} e {self.MAX_NOTES} notas."
            )

        root = self.normalize_note(root)

        base = [
            root + interval
            for interval in intervals
        ]

        size = len(base)
        voicing = []

        for index in range(size):
            source = (inversion + index) % size
            octave = 12 if inversion + index >= size else 0

            voicing.append(
                base[source] + octave
            )

        voicing = self._fit_window(voicing)
        notes = tuple(voicing)

        if len(notes) != len(set(notes)):
            raise ValueError(
                "Um MChord não pode conter notas duplicadas."
            )

        self.root = root
        self.chord_type = chord_type
        self.inversion = inversion
        self.notes = notes

    def __repr__(self):
        return (
            f"MChord(root={self.root}, "
            f"chord_type='{self.chord_type}', "
            f"inversion={self.inversion}, "
            f"notes={self.notes})"
        )


class BassNote:
    def __init__(self, position, duration):
        if not isinstance(position, int):
            raise TypeError(
                "A posição da nota deve ser um inteiro."
            )

        if not isinstance(duration, int):
            raise TypeError(
                "A duração da nota deve ser um inteiro."
            )

        if position < 0 or position >= BASS_BAR_UNITS:
            raise ValueError(
                f"A posição deve estar entre 0 e "
                f"{BASS_BAR_UNITS - 1}."
            )

        if duration not in BASS_DURATION_UNITS:
            raise ValueError(
                "A duração deve ser 1/16, 1/8, 1/4 ou 1/2 do compasso."
            )

        self.position = position
        self.duration = duration

    def __repr__(self):
        return (
            f"BassNote(position={self.position}, "
            f"duration={self.duration})"
        )


class BassPattern:
    NOTE_COUNTS = BASS_NOTE_COUNTS
    BAR_UNITS = BASS_BAR_UNITS
    DURATION_UNITS = BASS_DURATION_UNITS

    def __init__(self, notes=None):
        self.notes = (
            list(notes)
            if notes is not None
            else self._generate_notes()
        )

        self._validate()

    @classmethod
    def _generate_durations(cls, count):
        valid_sequences = []

        def collect(prefix, remaining):
            if len(prefix) == count:
                if remaining == 0:
                    valid_sequences.append(tuple(prefix))

                return

            slots_left = count - len(prefix) - 1

            for duration in cls.DURATION_UNITS:
                next_remaining = remaining - duration

                if next_remaining < slots_left:
                    continue

                if next_remaining > slots_left * max(cls.DURATION_UNITS):
                    continue

                collect(
                    prefix + [duration],
                    next_remaining
                )

        collect([], cls.BAR_UNITS)

        if not valid_sequences:
            raise ValueError(
                "Não foi possível criar um ritmo de baixo válido."
            )

        return list(random.choice(valid_sequences))

    @classmethod
    def _generate_notes(cls):
        count = random.choices(
            cls.NOTE_COUNTS,
            weights=BASS_NOTE_COUNT_WEIGHTS,
            k=1
        )[0]

        durations = cls._generate_durations(count)
        notes = []

        for index, duration in enumerate(durations):
            position = (
                0
                if index == 0
                else durations[index - 1]
            )

            notes.append(
                BassNote(position, duration)
            )

        return notes

    def _validate(self):
        if len(self.notes) not in self.NOTE_COUNTS:
            raise ValueError(
                f"BassPattern deve possuir {self.NOTE_COUNTS} notas."
            )

        if not all(
            isinstance(note, BassNote)
            for note in self.notes
        ):
            raise TypeError(
                "BassPattern deve conter somente BassNote."
            )

        total_duration = 0

        for index, note in enumerate(self.notes):
            expected_position = (
                0
                if index == 0
                else self.notes[index - 1].duration
            )

            if note.position != expected_position:
                raise ValueError(
                    "As posições relativas do BassPattern "
                    "devem ser sequenciais."
                )

            total_duration += note.duration

        if total_duration != self.BAR_UNITS:
            raise ValueError(
                "As durações do BassPattern devem preencher "
                "exatamente um compasso."
            )

    def __repr__(self):
        return f"BassPattern(notes={self.notes})"

    @property
    def start_positions(self):
        positions = []
        current = 0

        for note in self.notes:
            positions.append(current)
            current += note.duration

        return tuple(positions)


class ArpPattern:
    NOTE_COUNTS = ARP_NOTE_COUNTS
    STEP_UNITS = ARP_STEP_UNITS
    BAR_UNITS = 32

    def __init__(self, note_count=None, step=None, note_order=None):
        if note_count is None:
            note_count = random.choices(
                self.NOTE_COUNTS,
                weights=ARP_NOTE_COUNT_WEIGHTS,
                k=1
            )[0]

        if step is None:
            valid_steps = [
                value
                for value in self.STEP_UNITS
                if self.BAR_UNITS % value == 0
                and self.BAR_UNITS // value in self.NOTE_COUNTS
            ]

            if valid_steps:
                compatible = [
                    value
                    for value in valid_steps
                    if self.BAR_UNITS // value == note_count
                ]

                if compatible:
                    step = random.choice(compatible)
                else:
                    step = self.BAR_UNITS // note_count
            else:
                step = self.BAR_UNITS // note_count

        self.note_count = note_count
        self.step = step
        self.note_order = (
            tuple(random.sample(range(3), 3))
            if note_order is None
            else tuple(note_order)
        )

        self._validate()

    def _validate(self):
        if self.note_count not in self.NOTE_COUNTS:
            raise ValueError(
                f"ArpPattern deve possuir {self.NOTE_COUNTS} notas."
            )

        if self.step not in self.STEP_UNITS:
            raise ValueError(
                f"Step inválido. Valores permitidos: {self.STEP_UNITS}."
            )

        if self.note_count * self.step != self.BAR_UNITS:
            raise ValueError(
                "A quantidade de notas e o step devem "
                "preencher exatamente um compasso."
            )

        if len(self.note_order) != 3 or set(self.note_order) != {0, 1, 2}:
            raise ValueError(
                "note_order deve ser uma permutação dos índices (0, 1, 2)."
            )

    @property
    def start_positions(self):
        return tuple(
            index * self.step
            for index in range(self.note_count)
        )

    def __repr__(self):
        return (
            f"ArpPattern("
            f"note_count={self.note_count}, "
            f"step={self.step}, "
            f"note_order={self.note_order})"
        )


class MelodyNote:
    """Nota melódica com posição e duração em unidades da grade."""

    def __init__(self, pitch, velocity, position, duration):
        for name, value in (
            ("pitch", pitch),
            ("velocity", velocity),
            ("position", position),
            ("duration", duration),
        ):
            if not isinstance(value, int):
                raise TypeError(f"{name} deve ser um inteiro.")

        if not 0 <= pitch <= 127:
            raise ValueError("pitch deve estar entre 0 e 127.")

        if not 1 <= velocity <= 127:
            raise ValueError("velocity deve estar entre 1 e 127.")

        if position < 0:
            raise ValueError("position não pode ser negativa.")

        if duration <= 0:
            raise ValueError("duration deve ser maior que zero.")

        self.pitch = pitch
        self.velocity = velocity
        self.position = position
        self.duration = duration

    def __repr__(self):
        return (
            f"MelodyNote(pitch={self.pitch}, "
            f"velocity={self.velocity}, "
            f"position={self.position}, "
            f"duration={self.duration})"
        )


class MelodyPattern:
    """Sequência melódica com extensão fixa de oito compassos."""

    BAR_UNITS = MELODY_BAR_UNITS
    NUM_BARS = MELODY_PATTERN_BARS
    TOTAL_UNITS = NUM_BARS * BAR_UNITS
    DEFAULT_NOTE_COUNT = 32

    def __init__(self, notes=None):
        self.notes = (
            self._generate_notes()
            if notes is None
            else list(notes)
        )
        self._validate()

    @classmethod
    def _generate_notes(cls):
        positions = sorted(
            random.sample(
                range(cls.TOTAL_UNITS),
                cls.DEFAULT_NOTE_COUNT,
            )
        )
        notes = []

        for position in positions:
            notes.append(
                MelodyNote(
                    pitch=random.randint(48, 84),
                    velocity=random.randint(50, 110),
                    position=position,
                    duration=random.randint(
                        1,
                        min(8, cls.TOTAL_UNITS - position),
                    ),
                )
            )

        return notes

    def _validate(self):
        if not all(isinstance(note, MelodyNote) for note in self.notes):
            raise TypeError("MelodyPattern deve conter somente MelodyNote.")

        previous_position = -1

        for note in self.notes:
            if note.position < previous_position:
                raise ValueError(
                    "As notas do MelodyPattern devem estar em ordem temporal."
                )

            if note.position + note.duration > self.TOTAL_UNITS:
                raise ValueError(
                    "A nota deve terminar dentro dos oito compassos do padrão."
                )

            previous_position = note.position

    @property
    def note_count(self):
        return len(self.notes)

    def __repr__(self):
        return f"MelodyPattern(notes={self.notes})"


class Genotype:
    BPM = GENOTYPE_BPM

    BEATS_PER_BAR = GENOTYPE_BEATS_PER_BAR
    STEPS_PER_BEAT = GENOTYPE_STEPS_PER_BEAT

    STEPS_PER_BAR = GENOTYPE_STEPS_PER_BAR

    MAX_POLYPHONY = GENOTYPE_MAX_POLYPHONY

    DRUMS = GENOTYPE_DRUMS
    NUM_DRUMS = GENOTYPE_NUM_DRUMS

    def __init__(
        self,
        bat1=None,
        bat2=None,
        bati=None,
        batf=None,
        bass_patt1=None,
        bass_patt2=None,
        arp_patt1=None,
        arp_patt2=None,
        mel_patt1=None,
        mel_patt2=None,
        mchord1=None,
        mchord2=None,
        mchord3=None,
        mchord4=None,
        mchord5=None,
        mchord6=None,
        mchord7=None,
        mchord8=None,
    ):
        self.bat1 = (
            [Gene() for _ in range(self.STEPS_PER_BAR)]
            if bat1 is None
            else list(bat1)
        )

        self.bat2 = (
            [Gene() for _ in range(self.STEPS_PER_BAR)]
            if bat2 is None
            else list(bat2)
        )

        self.bati = (
            [Gene() for _ in range(self.STEPS_PER_BAR)]
            if bati is None
            else list(bati)
        )

        self.batf = (
            [Gene() for _ in range(self.STEPS_PER_BAR)]
            if batf is None
            else list(batf)
        )

        self.bass_patt1 = (
            BassPattern()
            if bass_patt1 is None
            else bass_patt1
        )

        self.bass_patt2 = (
            BassPattern()
            if bass_patt2 is None
            else bass_patt2
        )

        self.arp_patt1 = (
            ArpPattern()
            if arp_patt1 is None
            else arp_patt1
        )

        self.arp_patt2 = (
            ArpPattern()
            if arp_patt2 is None
            else arp_patt2
        )

        self.mel_patt1 = (
            MelodyPattern()
            if mel_patt1 is None
            else mel_patt1
        )

        self.mel_patt2 = (
            MelodyPattern()
            if mel_patt2 is None
            else mel_patt2
        )

        default_chords = tuple(
            self._random_mchord()
            for _ in range(NUM_MCHORDS)
        )

        provided_chords = (
            mchord1,
            mchord2,
            mchord3,
            mchord4,
            mchord5,
            mchord6,
            mchord7,
            mchord8,
        )

        for index, chord in enumerate(provided_chords):
            setattr(
                self,
                f"mchord{index + 1}",
                default_chords[index]
                if chord is None
                else chord
            )

        self._validate()

    @classmethod
    def _random_mchord(cls):
        root = random.randint(
            MChord.ROOT_MIN_MIDI_NOTE,
            MChord.ROOT_MAX_MIDI_NOTE
        )

        chord_type = random.choice(
            tuple(MChord.CHORD_INTERVALS.keys())
        )

        inversion = random.choice(
            tuple(MChord.INVERSIONS)
        )

        return MChord(
            root,
            chord_type,
            inversion
        )

    def _validate(self):
        if len(self.bat1) != self.STEPS_PER_BAR:
            raise ValueError(
                f"Bat1 deve possuir {self.STEPS_PER_BAR} genes."
            )

        if not all(
            isinstance(gene, Gene)
            for gene in self.bat1
        ):
            raise TypeError(
                "Todos os elementos de Bat1 devem ser objetos Gene."
            )

        if len(self.bat2) != self.STEPS_PER_BAR:
            raise ValueError(
                f"Bat2 deve possuir {self.STEPS_PER_BAR} genes."
            )

        if not all(
            isinstance(gene, Gene)
            for gene in self.bat2
        ):
            raise TypeError(
                "Todos os elementos de Bat2 devem ser objetos Gene."
            )

        for name, track in (
            ("BatI", self.bati),
            ("BatF", self.batf),
        ):
            if len(track) != self.STEPS_PER_BAR:
                raise ValueError(
                    f"{name} deve possuir {self.STEPS_PER_BAR} genes."
                )

            if not all(
                isinstance(gene, Gene)
                for gene in track
            ):
                raise TypeError(
                    f"Todos os elementos de {name} "
                    "devem ser objetos Gene."
                )

        for chord in self.mchords:
            if not isinstance(chord, MChord):
                raise TypeError(
                    "Todos os MChords devem ser objetos MChord."
                )

        for name, pattern in (
            ("bass_patt1", self.bass_patt1),
            ("bass_patt2", self.bass_patt2),
            ("arp_patt1", self.arp_patt1),
            ("arp_patt2", self.arp_patt2),
            ("mel_patt1", self.mel_patt1),
            ("mel_patt2", self.mel_patt2),
        ):
            if not isinstance(
                pattern,
                BassPattern
                if name.startswith("bass")
                else ArpPattern
                if name.startswith("arp")
                else MelodyPattern
            ):
                raise TypeError(
                    f"{name} deve ser um objeto "
                    f"{'BassPattern' if name.startswith('bass') else 'ArpPattern' if name.startswith('arp') else 'MelodyPattern'}."
                )

    @property
    def bass_pattern(self):
        return self.bass_patt1

    @bass_pattern.setter
    def bass_pattern(self, value):
        self.bass_patt1 = value

    @property
    def mchords(self):
        return tuple(
            getattr(self, f"mchord{index}")
            for index in range(1, NUM_MCHORDS + 1)
        )

    def __repr__(self):
        return (
            f"Genotype("
            f"bati={self.bati}, "
            f"bat1={self.bat1}, "
            f"bat2={self.bat2}, "
            f"batf={self.batf}, "
            f"bass_patt1={self.bass_patt1}, "
            f"bass_patt2={self.bass_patt2}, "
            f"arp_patt1={self.arp_patt1}, "
            f"arp_patt2={self.arp_patt2}, "
            f"mel_patt1={self.mel_patt1}, "
            f"mel_patt2={self.mel_patt2}, "
            f"mchords={self.mchords})"
        )
