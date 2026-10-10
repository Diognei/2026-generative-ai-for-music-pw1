#!/usr/bin/env bash
# ==============================================================================
# start_container.sh
# Constrói (se necessário) e inicia o container Docker de forma INTERATIVA,
# montando o diretório atual em /app:
#     docker run -it -v ./:/app/ ...
#
# Uso:
#   ./start_container.sh            # usa a imagem existente (build automático se não houver)
#   ./start_container.sh --build    # força o rebuild da imagem antes de subir
#   ./start_container.sh <cmd>      # roda <cmd> dentro do container (ex: python script.py)
# ==============================================================================
set -euo pipefail

# ---- Configurações -----------------------------------------------------------
IMAGE_NAME="${IMAGE_NAME:-tp1-genai-music}"
CONTAINER_NAME="${CONTAINER_NAME:-tp1-genai-music-container-2}"

# Diretório do script = diretório do projeto (será montado em /app)
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ---- 1. Build da imagem ------------------------------------------------------
# Faz o build se: (a) o usuário passar --build, ou (b) a imagem ainda não existir.
if [[ "${1:-}" == "--build" ]]; then
    shift
    echo ">> Construindo a imagem '${IMAGE_NAME}'..."
    docker build -t "${IMAGE_NAME}" "${PROJECT_DIR}"
elif ! docker image inspect "${IMAGE_NAME}" >/dev/null 2>&1; then
    echo ">> Imagem '${IMAGE_NAME}' não encontrada. Construindo..."
    docker build -t "${IMAGE_NAME}" "${PROJECT_DIR}"
fi

# ---- 2. Remove um container antigo com o mesmo nome (se existir) -------------
docker rm -f "${CONTAINER_NAME}" >/dev/null 2>&1 || true

# ---- 3. Sobe o container interativo ------------------------------------------
echo ">> Iniciando o container '${CONTAINER_NAME}' (interativo)"
echo "   Diretório: ${PROJECT_DIR}  ->  /app"

# Usa -it quando há um terminal interativo; cai para -i em contextos sem TTY
# (ex.: execução via pipe/CI), evitando o erro "the input device is not a TTY".
DOCKER_TTY="-it"
[[ -t 0 ]] || DOCKER_TTY="-i"

# Permite que o FluidSynth use o áudio ALSA do host quando disponível.
AUDIO_DEVICE_ARGS=()
AUDIO_GROUP_ARGS=()
if [[ -d /dev/snd ]]; then
    AUDIO_DEVICE_ARGS+=(--device /dev/snd)

    AUDIO_GROUP_ID="$(getent group audio | cut -d: -f3 || true)"
    if [[ -n "${AUDIO_GROUP_ID}" ]]; then
        AUDIO_GROUP_ARGS+=(--group-add "${AUDIO_GROUP_ID}")
    fi
else
    echo ">> Aviso: /dev/snd não existe no host; reprodução de áudio ficará indisponível."
fi

# Dica: para que os arquivos criados dentro do container pertençam ao seu usuário
# no host, descomente a linha abaixo (e comente/remova o '--user' que não existir):
#     -u "$(id -u):$(id -g)" \
docker run ${DOCKER_TTY} --rm \
    --name "${CONTAINER_NAME}" \
    -v "${PROJECT_DIR}":/app \
    -w /app \
    "${AUDIO_DEVICE_ARGS[@]}" \
    "${AUDIO_GROUP_ARGS[@]}" \
    ${DOCKER_EXTRA_ARGS:-} \
    "${IMAGE_NAME}" \
    "${@:-bash}"
