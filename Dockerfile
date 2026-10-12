# ==============================================================================
# TP1 - Generative AI for Music
# Algoritmo Genético para geração de músicas MIDI
#
# Imagem base: Python 3.11 slim (compatível com todas as bibliotecas abaixo)
# ==============================================================================
FROM python:3.11-slim

LABEL description="Ambiente para geração de música MIDI (AG + bibliotecas simbólicas)" \
      maintainer="TP1 - Generative AI for Music"

# Evita prompts interativos do apt e melhora o comportamento do Python no container
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# ------------------------------------------------------------------------------
# Dependências de sistema
# ------------------------------------------------------------------------------
#  fluidsynth          -> sintetizador de software (CLI)
#  libfluidsynth-dev   -> headers + biblioteca compartilhada usada pelo pyfluidsynth
#  fluid-soundfont-gm  -> SoundFont General MIDI (FluidR3_GM.sf2) p/ renderizar áudio
#  libsndfile1         -> leitura/escrita de áudio (soundfile / pretty_midi)
#  build-essential, git-> utilitários de build e controle de versão
# ------------------------------------------------------------------------------
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        fluidsynth \
        libfluidsynth-dev \
        fluid-soundfont-gm \
        libsndfile1 \
        build-essential \
        ffmpeg \
        git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Diretório de trabalho (o diretório do projeto é montado aqui pelo start_container.sh)
WORKDIR /app

# ------------------------------------------------------------------------------
# Bibliotecas Python sugeridas no enunciado
# ------------------------------------------------------------------------------
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir \
        music21 \
        pretty_midi \
        muspy \
        miditok \
        pyfluidsynth \
        matplotlib

# Caminho do SoundFont padrão do sistema (facilita uso em scripts/notebooks)
ENV SOUNDFONT=/usr/share/sounds/sf2/FluidR3_GM.sf2

# Shell interativo por padrão
CMD ["/bin/bash"]
