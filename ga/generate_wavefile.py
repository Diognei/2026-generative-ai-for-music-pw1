import os
import subprocess
from constants import *


def midi_to_wav(
    midi_path,
    wav_path=None,
    soundfont=DEFAULT_SOUNDFONT_PATH,
    sample_rate=44100,
):
    """
    Converte um arquivo MIDI para WAV usando FluidSynth.

    Parâmetros:
        midi_path:
            Caminho do arquivo .mid.

        wav_path:
            Caminho de saída .wav.
            Se None, usa o mesmo nome do MIDI.

        soundfont:
            SoundFont GM utilizado pelo FluidSynth.

        sample_rate:
            Taxa de amostragem do WAV.

    Retorna:
        Caminho do arquivo WAV gerado.
    """

    midi_path = os.path.abspath(midi_path)

    if wav_path is None:
        wav_path = os.path.splitext(midi_path)[0] + ".wav"

    wav_path = os.path.abspath(wav_path)

    if not os.path.isfile(midi_path):
        raise FileNotFoundError(
            f"Arquivo MIDI não encontrado: {midi_path}"
        )

    if not os.path.isfile(soundfont):
        raise FileNotFoundError(
            f"SoundFont não encontrado: {soundfont}"
        )

    command = [
        "fluidsynth",

        # Não abrir interface gráfica.
        "-ni",

        # SoundFont.
        "-F", wav_path,

        # Taxa de amostragem.
        "-r", str(sample_rate),

        # SoundFont.
        soundfont,

        # MIDI.
        midi_path,
    ]

    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(
            "Erro ao converter MIDI para WAV.\n\n"
            f"Comando: {' '.join(command)}\n\n"
            f"STDOUT:\n{result.stdout}\n\n"
            f"STDERR:\n{result.stderr}"
        )

    if not os.path.isfile(wav_path):
        raise RuntimeError(
            f"FluidSynth terminou sem gerar o arquivo: {wav_path}"
        )

    normalized_wav_path = wav_path + ".normalized.wav"
    normalize_command = [
        "ffmpeg",
        "-y",
        "-i", wav_path,
        "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
        "-ar", str(sample_rate),
        normalized_wav_path,
    ]

    normalization_result = subprocess.run(
        normalize_command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    if normalization_result.returncode != 0:
        if os.path.isfile(normalized_wav_path):
            os.remove(normalized_wav_path)
        raise RuntimeError(
            "Erro ao normalizar o áudio WAV.\n\n"
            f"Comando: {' '.join(normalize_command)}\n\n"
            f"STDOUT:\n{normalization_result.stdout}\n\n"
            f"STDERR:\n{normalization_result.stderr}"
        )

    if not os.path.isfile(normalized_wav_path):
        raise RuntimeError(
            "A normalização terminou sem gerar o arquivo: "
            f"{normalized_wav_path}"
        )

    os.replace(normalized_wav_path, wav_path)

    return wav_path
