import os
import secrets

RANDOM_SEED = secrets.randbits(64)

PRINT_INTERVAL_PERCENT = 10
WORKERS = 1

# ============================================================
# HIPERPARÂMETROS GLOBAIS
# ============================================================

POPULATION_SIZE = int(os.getenv("POPULATION_SIZE", "10"))
GENERATIONS = int(os.getenv("GENERATIONS", "10000"))
GLOBAL_CROSSOVER_RATE = float(os.getenv("GLOBAL_CROSSOVER_RATE", "0.8"))
GLOBAL_MUTATION_RATE = float(os.getenv("GLOBAL_MUTATION_RATE", "0.1"))
ELITISM = os.getenv("ELITISM", "true").strip().lower() in {"1", "true", "yes", "on"}

# ============================================================
# HIPERPARAMETROS RELATIVOS
# ============================================================

# Os padrões de bateria definem o groove; a base muda menos que o
# refrão, enquanto intro e final permitem um pouco mais de variação.
# Essas taxas são aplicadas por step da bateria.
MCHORD_MUTATION_RATE = 0.30 * GLOBAL_MUTATION_RATE
BAT1_MUTATION_RATE = 0.20 * GLOBAL_MUTATION_RATE
BAT2_MUTATION_RATE = 0.28 * GLOBAL_MUTATION_RATE
BATI_MUTATION_RATE = 0.25 * GLOBAL_MUTATION_RATE
BATF_MUTATION_RATE = 0.30 * GLOBAL_MUTATION_RATE

# Baixo e arpejos sustentam o pulso; melodia recebe mais exploração,
# especialmente no refrão. Essas taxas são aplicadas por padrão.
BASS_PATT1_MUTATION_RATE = 0.40 * GLOBAL_MUTATION_RATE
BASS_PATT2_MUTATION_RATE = 0.45 * GLOBAL_MUTATION_RATE
ARP_PATT1_MUTATION_RATE = 0.35 * GLOBAL_MUTATION_RATE
ARP_PATT2_MUTATION_RATE = 0.40 * GLOBAL_MUTATION_RATE
MEL_PATT1_MUTATION_RATE = 0.50 * GLOBAL_MUTATION_RATE
MEL_PATT2_MUTATION_RATE = 0.60 * GLOBAL_MUTATION_RATE

# Recombinação preserva o groove base e favorece mudanças no refrão,
# na melodia e nos acompanhamentos que podem variar entre seções.
MCHORD_CROSSOVER_RATE = 0.40 * GLOBAL_CROSSOVER_RATE
BAT1_CROSSOVER_RATE = 0.35 * GLOBAL_CROSSOVER_RATE
BAT2_CROSSOVER_RATE = 0.50 * GLOBAL_CROSSOVER_RATE
BATI_CROSSOVER_RATE = 0.40 * GLOBAL_CROSSOVER_RATE
BATF_CROSSOVER_RATE = 0.45 * GLOBAL_CROSSOVER_RATE
BASS_PATT1_CROSSOVER_RATE = 0.45 * GLOBAL_CROSSOVER_RATE
BASS_PATT2_CROSSOVER_RATE = 0.50 * GLOBAL_CROSSOVER_RATE
ARP_PATT1_CROSSOVER_RATE = 0.40 * GLOBAL_CROSSOVER_RATE
ARP_PATT2_CROSSOVER_RATE = 0.50 * GLOBAL_CROSSOVER_RATE
MEL_PATT1_CROSSOVER_RATE = 0.50 * GLOBAL_CROSSOVER_RATE
MEL_PATT2_CROSSOVER_RATE = 0.60 * GLOBAL_CROSSOVER_RATE

# ============================================================
# OUTROS PARÂMETROS VARIÁVEIS
# ============================================================

MCHORD_ROOT_MIN = 48
MCHORD_ROOT_MAX = 84
RANDOM_IMMIGRANT_RATE = 0.05

DIVERSIFY_FINAL_MIDI = True
DIVERSIFY_MIDI_NOTES = False
DIVERSIFY_MIDI_INSTRUMENTS = False

# ============================================================
# ELEMENTOS DE BATERIA
# ============================================================

# Indices usados pelo Gene:
#
#   0 = Kick
#   1 = Snare
#   2 = Closed Hi-Hat
#   3 = Open Hi-Hat
#   4 = Crash
#
# Pitches General MIDI:
#
#   Kick          = 36
#   Snare         = 38
#   Closed Hi-Hat = 42
#   Open Hi-Hat   = 46
#   Crash         = 49

KICK = 0
SNARE = 1
CLOSED_HIHAT = 2
OPEN_HIHAT = 3
CRASH = 4

DRUMS = [
    KICK,
    SNARE,
    CLOSED_HIHAT,
    OPEN_HIHAT,
    CRASH,
]

DRUM_PITCHES = {
    KICK: 36,
    SNARE: 38,
    CLOSED_HIHAT: 42,
    OPEN_HIHAT: 46,
    CRASH: 51,
}

DRUM_NAMES = {
    KICK: "Kick",
    SNARE: "Snare",
    CLOSED_HIHAT: "Closed_HiHat",
    OPEN_HIHAT: "Open_HiHat",
    CRASH: "Crash",
}

DRUM_NAMES_FITNESS = {
    KICK: "Kick",
    SNARE: "Snare",
    CLOSED_HIHAT: "Closed Hi-Hat",
    OPEN_HIHAT: "Open Hi-Hat",
    CRASH: "Crash",
}

# ============================================================
# GERACAO DOS PADROES DE BATERIA
# ============================================================

KICK_WEIGHT = 30
SNARE_WEIGHT = 25
CLOSED_HIHAT_WEIGHT = 35
OPEN_HIHAT_WEIGHT = 5
CRASH_WEIGHT = 4
BAT1_EMPTY_STEP_PROBABILITY = 0.15
BAT2_EMPTY_STEP_PROBABILITY = 0.05
BAT1_SECOND_NOTE_PROBABILITY = 0.45
BAT2_SECOND_NOTE_PROBABILITY = 0.65
BAT1_THIRD_NOTE_PROBABILITY = 0.15
BAT2_THIRD_NOTE_PROBABILITY = 0.35
BATI_EMPTY_STEP_PROBABILITY = 0.35
BATF_EMPTY_STEP_PROBABILITY = 0.25
BATI_SECOND_NOTE_PROBABILITY = 0.25
BATF_SECOND_NOTE_PROBABILITY = 0.50
BATI_THIRD_NOTE_PROBABILITY = 0.05
BATF_THIRD_NOTE_PROBABILITY = 0.20

# ============================================================
# TEMPO E COMPASSO
# ============================================================

BPM = 120
BEATS_PER_BAR = 4
STEPS_PER_BEAT = 2
STEPS_PER_BAR = BEATS_PER_BAR * STEPS_PER_BEAT
SECONDS_PER_BEAT = 60.0 / BPM
SECONDS_PER_STEP = SECONDS_PER_BEAT / STEPS_PER_BEAT

# ============================================================
# FORMA DA MUSICA CURTA (legado) E CONSTANTES DE COMPATIBILIDADE
# ============================================================

NUM_BAT1 = 32
BATI_BARS = 1
BAT1_BARS_FIRST = 8
BAT2_BARS_FIRST = 4
BAT1_BARS_SECOND = 8
BAT2_BARS_SECOND = 4
BATF_BARS = 1
NUM_MUSIC_BARS = (
    BATI_BARS
    + BAT1_BARS_FIRST
    + BAT2_BARS_FIRST
    + BAT1_BARS_SECOND
    + BAT2_BARS_SECOND
    + BATF_BARS
)
NUM_MCHORDS = 8
MCHORDS_PER_GROUP = 4
GROUP_REPETITIONS = 2
EMPTY_BARS_START = 1
GROUP1_REPETITIONS_FIRST = 2
GROUP2_REPETITIONS_FIRST = 1
GROUP1_REPETITIONS_SECOND = 2
GROUP2_REPETITIONS_SECOND = 1
EMPTY_BARS_END = 1
FINAL_EMPTY_BARS = 1

# ============================================================
# INSTRUMENTOS MIDI, VELOCITIES E REPRODUCAO
# ============================================================

MELODY_PROGRAM = 0

STRING_PROGRAM = 49
BASS_PROGRAM = 36
ARPEGGIO_PROGRAM = 24
DRUM_TRACK_VELOCITY = 100
STRING_TRACK_VELOCITY = 100
STRING2_TRACK_VELOCITY = 60
BASS_TRACK_VELOCITY = 100
BASS2_TRACK_VELOCITY = 40
ARPEGGIO_TRACK_VELOCITY = 100
ARPEGGIO2_TRACK_VELOCITY = 100
MELODY_TRACK_VELOCITY = 115

STRING2_PROGRAM = 50
BASS2_PROGRAM = 51
ARPEGGIO2_PROGRAM = 27

AUTOTUNE_MELODY = True
TUNE_PROBABILITY = 1
AUTOCOMP_MELODY = True
COMP_PROBABILITY = 1
EXTEND_NOTES = True
EXTEND_PROBABILITY = 0.95
MIN_MELODY_VEL = 90
MAX_MELODY_VEL = 110
MIN_MELODY_PIT = "A3"
MAX_MELODY_PIT = "F5"

EMPTY_TRACK_ANCHOR_PITCH = 127
EMPTY_TRACK_ANCHOR_VELOCITY = 1
EMPTY_TRACK_ANCHOR_DURATION = 0.05

SUSTAIN_PEDAL_CC = 64
SUSTAIN_PEDAL_ON = 127
SUSTAIN_PEDAL_OFF = 0

PLAY_FINAL_MIDI = True
MIDI_PLAYER = "fluidsynth"
DEFAULT_SOUNDFONT_PATH = "./assets/PC51d.sf2"
FLUIDSYNTH_AUDIO_DRIVER = os.environ.get(
    "FLUIDSYNTH_AUDIO_DRIVER",
    "alsa"
)

# ============================================================
# INSTRUMENTOS MIDI, VELOCITIES E REPRODUCAO (cont.)
# ============================================================

FLUIDSYNTH_AUDIO_DRIVER = os.environ.get(
    "FLUIDSYNTH_AUDIO_DRIVER",
    "alsa"
)
FLUIDSYNTH_AUDIO_DEVICE = os.environ.get(
    "FLUIDSYNTH_AUDIO_DEVICE",
    "plughw:0,0"
)


# ============================================================
# FITNESS
# ============================================================

MAX_REFS = 10

FITNESS_WEIGHTS = {
    "strong_beats": 0.12,
    "backbeat": 0.18,
    "kick": 0.15,
    "hihat": 0.12,
    "syncopation": 0.08,
    "density": 0.10,
    "variation": 0.08,
    "structure": 0.07,
    "combination": 0.10,
}

MSIM_WEIGHTS = {
    "kick": 0.18,
    "snare": 0.18,
    "hihat": 0.16,
    "open_hihat": 0.08,
    "crash": 0.08,
    "density": 0.12,
    "variation": 0.08,
    "polyrhythm": 0.06,
    "combination": 0.06,
}

RHYTHM_WEIGHT = 0.53
HARMONY_WEIGHT = 0.27
BASS_PATTERN_WEIGHT = 0.10
BASS_PATT1_WEIGHT = 0.05
BASS_PATT2_WEIGHT = 0.05
ARP_PATTERN_WEIGHT = 0.10
ARP_PATT1_WEIGHT = 0.05
ARP_PATT2_WEIGHT = 0.05
BAT1_RHYTHM_WEIGHT = 0.65
BAT2_RHYTHM_WEIGHT = 0.25
BATI_RHYTHM_WEIGHT = 0.05
BATF_RHYTHM_WEIGHT = 0.05

HARMONIC_WEIGHTS = {
    "chord_validity": 0.20,
    "tonal_coherence": 0.30,
    "root_motion": 0.25,
    "voice_leading": 0.25,
}

BASS_NOTE_COUNTS = (2, 4, 8)
BASS_NOTE_COUNT_WEIGHTS = (0.20, 0.60, 0.20)
BASS_BAR_UNITS = 16
BASS_DURATION_UNITS = (1, 2, 4, 8)

ARP_NOTE_COUNTS = (1, 2, 4, 8, 16, 32)
ARP_NOTE_COUNT_WEIGHTS = (0.05, 0.10, 0.30, 0.30, 0.20, 0.05)
ARP_STEP_UNITS = (1, 2, 4, 8, 16, 32)

# Cada padrão melódico cobre 8 compassos (dois grupos de 4),
# com 32 unidades temporais por compasso.
MELODY_BAR_UNITS = 32
MELODY_PATTERN_BARS = 8


# ============================================================
# REPRESENTACAO GENETICA
# ============================================================

GENE_MAX_NOTES = 3

MCHORD_INTERVALS = {
    "major": (0, 4, 7),
    "minor": (0, 3, 7),
    "diminished": (0, 3, 6),
}
MCHORD_MIN_NOTES = 3
MCHORD_MAX_NOTES = 5
# Inversões permitidas:
#     0 = posição fundamental (a tônica é o baixo)
#     1 = primeira inversão   (a terça é o baixo)
#     2 = segunda inversão    (a quinta é o baixo)
MCHORD_INVERSIONS = (0, 1, 2)
# Janela de voicing dos MChords. As inversões podem ultrapassar
# C4, então o teto fica em A4 (69).
MCHORD_MIN_MIDI_NOTE = 48
MCHORD_MAX_MIDI_NOTE = 69
# Tônica canonizada em C3-C4; não muda com a inversão.
MCHORD_ROOT_MIN_MIDI_NOTE = 48
MCHORD_ROOT_MAX_MIDI_NOTE = 60

GENOTYPE_BPM = BPM
GENOTYPE_BEATS_PER_BAR = BEATS_PER_BAR
GENOTYPE_STEPS_PER_BEAT = STEPS_PER_BEAT
GENOTYPE_STEPS_PER_BAR = STEPS_PER_BAR
GENOTYPE_MAX_POLYPHONY = 5
GENOTYPE_DRUMS = [
    "Kick",
    "Snare",
    "Closed_HiHat",
    "Open_HiHat",
    "Crash",
]
GENOTYPE_NUM_DRUMS = len(GENOTYPE_DRUMS)

# ============================================================
# CONFIGURAÇÃO
# ============================================================

# Programas das trilhas reservadas (vazias).
# O pretty_midi mescla na leitura os instrumentos que compartilham o
# mesmo (program, is_drum): String1/String2, Bass1/Bass2 e Guitar1/
# Guitar2 sumiriam em pares se usassem o mesmo program. Programas
# distintos garantem que as 7 pistas sobrevivam ao round-trip do MIDI.
# Escolhas próximas ao timbre original:
#   50 = String Ensemble 2 (vs. 49 String Ensemble 1)
#   33 = Electric Bass (finger) (vs. 36 Fretless Bass)
#   25 = Acoustic Guitar (nylon) (vs. 24 Acoustic Guitar (steel))
STRING2_PROGRAM = 50
BASS2_PROGRAM = 33
ARPEGGIO2_PROGRAM = 25
STRING2_OCTAVE_SHIFT = 12

# Nota âncora das trilhas vazias (String2/Bass2/Guitar2).
# O pretty_midi só recria um instrumento na leitura do MIDI se ele
# contiver pelo menos um note_on com velocity > 0; sem isso a trilha
# reservada sumiria do arquivo. A âncora usa um pitch fora da faixa
# audível dos instrumentos (G8 = 127) com velocity 1 e duração mínima,
# posicionada no fim da música: inaudível e invisível no pianoroll.
# Duração de 50 ms: garante start_tick != end_tick na quantização
# MIDI (âncoras de 1 ms colapsavam para o mesmo tick e eram
# descartadas na leitura, fazendo a trilha sumir de novo).
EMPTY_TRACK_ANCHOR_PITCH = 127
EMPTY_TRACK_ANCHOR_VELOCITY = 1
EMPTY_TRACK_ANCHOR_DURATION = 0.05

# MIDI CC 64 = sustain (release) pedal.
# Valores >= 64 mantêm o pedal pressionado; < 64 soltam.
SUSTAIN_PEDAL_CC = 64
SUSTAIN_PEDAL_ON = 127
SUSTAIN_PEDAL_OFF = 0

# ============================================================
# PADROES DE BAIXO E ARPEJO (BASS/ARP PATTERNS)
# ============================================================

BASS_BAR_UNITS = 16
BASS_ALLOWED_DURATIONS = (1, 2, 4, 8)
ARP_BAR_UNITS = 32

# ============================================================
# ACORDES (MCHORDS)
# ============================================================

MCHORD_TYPES = ("major", "minor", "diminished")
MCHORD_INVERSIONS = (0, 1, 2)
MCHORD_MIN_MIDI_NOTE = 48
MCHORD_MAX_MIDI_NOTE = 69
MCHORD_ROOT_MIN_MIDI_NOTE = 48
MCHORD_ROOT_MAX_MIDI_NOTE = 60

# ============================================================
# FORMA DA MUSICA LONGA
# ============================================================
#
# A musica longa possui 62 compassos (124 segundos a 120 BPM).
#
# Cada secao define o conteudo e a quantidade de compassos:
#
#     ("bati"/"bat1"/"bat2"/"batf", compassos)  -> padrao de bateria
#     ("group1"/"group2", compassos)            -> acordes (4 por passe)
#     ("mel_patt1"/"mel_patt2", compassos)       -> padrao da melodia
#     (None, compassos)                         -> silencio
#
# Onde Grupo1 = [MChord1..MChord4] e Grupo2 = [MChord5..MChord8].
#
# As secoes foram escolhidas para que:
#
#     - Bat2 (refrao) sempre coincida com Grupo2;
#     - Strings entram no compasso 1;
#     - Bass entra no compasso 5;
#     - Guitar entra no compasso 9.

DRUM_SECTIONS = (
    ("bat1", 1),
    ("bati", 1),
    ("bat2", 1),
    ("bati", 1),
    ("bat1", 16),
    ("bat2", 8),
    ("bat1", 16),
    ("bat2", 16),
    ("bat1", 4),
    ("batf", 4),
)

STRING_SECTIONS = (
    ("group1", 4),
    ("group1", 16),
    ("group2", 8),
    ("group1", 16),
    ("group2", 16),
    ("group1", 4),
    ("group1", 4),
)

STRING2_SECTIONS = (
    (None, 28),
    ("group1", 16),
    ("group2", 16),
    ("group1", 4),
    (None, 4),
)

BASS_SECTIONS = (
    (None, 4),
    ("group1", 8),
    ("group1", 8),
    ("group2", 8),
    ("group1", 16),
    ("group2", 16),
    ("group1", 4),
    ("group1", 4)
)

ARPEGGIO_SECTIONS = (
    (None, 12),
    ("group1", 8),
    ("group2", 8),
    ("group1", 16),
    ("group2", 16),
    ("group1", 4),
    (None, 4),
)

MELODY_SECTIONS = (
    (None, 4),
    ("mel_patt1", 16),
    ("mel_patt2", 8),
    ("mel_patt1", 16),
    ("mel_patt2", 16),
    ("mel_patt1", 4),
    (None, 4),
)

OUTPUT_MID_FNAM = "./outputs/final_best.mid"
OUTPUT_MID_FNAM_PLUS = "./outputs/final_best_plus.mid"
OUTPUT_PNG_FNAM = "./outputs/final_best.png"
OUTPUT_WAV_FNAM = "./outputs/final_best.wav"
OUTPUT_MP4_FNAM = "./outputs/final_best.mp4"

DARK_PIANOROLL = False
