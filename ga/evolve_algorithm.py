import random
import shutil
import subprocess
import sys
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor

import matplotlib.pyplot as plt

from constants import *
from individual import Individual
from genotype import Genotype
from fitness import calculate_fitness
from generate_midi_long import generate_midi
from generate_wavefile import midi_to_wav
from generate_videofile import generate_video
from diversify_midi import diversify_midi
from crossover import clone_individual, crossover
from mutation import (
    generate_drum_step,
    mutate,
    randomize_chord_inversions,
)


random.seed(RANDOM_SEED)


# ============================================================
# PARÂMETROS DO ALGORITMO
# ============================================================

# Número de processos usados para avaliar a população.
#
# Para a fitness atual, WORKERS=1 normalmente é mais eficiente,
# pois a avaliação é barata e o custo de serialização dos
# indivíduos pode superar o ganho da paralelização.
# Fração aproximada de indivíduos novos inseridos em cada geração.
#
# Esses imigrantes mantêm diversidade genética quando a população converge
# para um platô de fitness.
# Elitismo:
# mantém o melhor indivíduo da geração anterior.


# ============================================================
# INICIALIZAÇÃO
# ============================================================

def initialize_individual():
    """
    Cria um indivíduo inicial.

    O indivíduo possui:

        Bat1 = 1 compasso
        8 Genes
        cada Gene = 1 colcheia
        2 BassPatterns
        2 ArpPatterns
        2 MelodyPatterns, cada um com 8 compassos (2 grupos de 4)
        8 MChords

    A população inicial não é totalmente aleatória.
    São utilizadas probabilidades musicais para aumentar a
    quantidade de grooves plausíveis desde o início.
    """

    individual = Individual()

    for step in range(
        Genotype.STEPS_PER_BAR
    ):

        individual.bat1[step] = (
            generate_drum_step(step)
        )

        individual.bat2[step] = (
            generate_drum_step(
                step,
                profile="chorus"
            )
        )

        individual.bati[step] = generate_drum_step(
            step,
            profile="intro"
        )
        individual.batf[step] = generate_drum_step(
            step,
            profile="final"
        )

    # Inversões iniciais: semeia diversidade de voicing sem
    # alterar a harmonia (raízes e tipos continuam os defaults).
    randomize_chord_inversions(individual)

    return individual


# ============================================================
# AVALIAÇÃO
# ============================================================

def evaluate(
    individual,
    index=None
):
    """
    Calcula o fitness de um indivíduo.

    O parâmetro index existe apenas por compatibilidade
    com versões anteriores.
    """

    return calculate_fitness(
        individual
    )


def evaluate_population(
    population,
    executor=None
):
    """
    Avalia toda a população.
    """

    if executor is None:

        return [
            evaluate(individual)
            for individual in population
        ]

    return list(
        executor.map(
            evaluate,
            population
        )
    )


def moving_average(values, window):
    """Calcula média móvel trailing, usando até `window` valores recentes."""

    averages = []
    for index in range(len(values)):
        window_start = max(0, index - window + 1)
        window_values = values[window_start:index + 1]
        averages.append(sum(window_values) / len(window_values))

    return averages


# ============================================================
# SELEÇÃO
# ============================================================

def selection(
    population,
    fitnesses
):
    """
    Seleção por torneio.

    Três indivíduos são escolhidos aleatoriamente.
    O indivíduo com maior fitness vence o torneio.
    """

    tournament_size = min(
        3,
        len(population)
    )

    candidates = random.sample(
        range(len(population)),
        tournament_size
    )

    winner = max(
        candidates,
        key=lambda i: fitnesses[i]
    )

    return population[winner]


def play_midi(path):
    """Toca um arquivo MIDI usando o FluidSynth do container."""

    if not PLAY_FINAL_MIDI:
        return

    command = [
        MIDI_PLAYER,
        "-ni",
        "-a",
        FLUIDSYNTH_AUDIO_DRIVER,
        "-o",
        f"audio.alsa.device={FLUIDSYNTH_AUDIO_DEVICE}",
        DEFAULT_SOUNDFONT_PATH,
        path,
    ]

    print(
        f"Reproduzindo {path} com {MIDI_PLAYER}..."
    )

    try:
        subprocess.run(command, check=True)
    except FileNotFoundError:
        print(
            f"Player MIDI não encontrado: {MIDI_PLAYER}"
        )
    except subprocess.CalledProcessError as error:
        print(
            f"Não foi possível reproduzir o MIDI "
            f"(código {error.returncode})."
        )


# ============================================================
# ALGORITMO GENÉTICO
# ============================================================

def genetic_algorithm():

    outputs_root = Path("./outputs")
    outputs_root.mkdir(parents=True, exist_ok=True)

    existing_run_numbers = [
        int(directory.name[3:])
        for directory in outputs_root.iterdir()
        if directory.is_dir()
        and directory.name.startswith("out")
        and directory.name[3:].isdigit()
    ]
    next_run_number = max(existing_run_numbers, default=0) + 1
    run_output_dir = outputs_root / f"out{next_run_number}"
    while run_output_dir.exists():
        next_run_number += 1
        run_output_dir = outputs_root / f"out{next_run_number}"
    run_output_dir.mkdir()

    config_path = run_output_dir / "config.txt"
    config_path.write_text(
        "\n".join((
            f"POPULATION_SIZE = {POPULATION_SIZE}",
            f"GENERATIONS = {GENERATIONS}",
            f"GLOBAL_CROSSOVER_RATE = {GLOBAL_CROSSOVER_RATE}",
            f"GLOBAL_MUTATION_RATE = {GLOBAL_MUTATION_RATE}",
            f"ELITISM = {ELITISM}",
        )) + "\n",
        encoding="utf-8",
    )

    output_mid_path = str(run_output_dir / Path(OUTPUT_MID_FNAM).name)
    output_mid_plus_path = str(
        run_output_dir / Path(OUTPUT_MID_FNAM_PLUS).name
    )
    output_png_path = str(run_output_dir / Path(OUTPUT_PNG_FNAM).name)
    output_wav_path = str(run_output_dir / Path(OUTPUT_WAV_FNAM).name)
    output_mp4_path = str(run_output_dir / Path(OUTPUT_MP4_FNAM).name)

    # --------------------------------------------------------
    # População inicial
    # --------------------------------------------------------

    population = [
        initialize_individual()
        for _ in range(
            POPULATION_SIZE
        )
    ]

    # --------------------------------------------------------
    # Melhor indivíduo global
    # --------------------------------------------------------

    best_individual = None
    best_fitness = -1.0

    # --------------------------------------------------------
    # Executor
    # --------------------------------------------------------

    executor = None

    if WORKERS > 1:

        executor = ProcessPoolExecutor(
            max_workers=WORKERS
        )

    print_interval = max(1, GENERATIONS // PRINT_INTERVAL_PERCENT)
    generation_history = []
    minimum_fitness_history = []
    mean_fitness_history = []
    generation_best_history = []
    best_fitness_history = []

    # ========================================================
    # GERAÇÕES
    # ========================================================

    try:

        for generation in range(
            GENERATIONS
        ):

            # ------------------------------------------------
            # Avaliação
            # ------------------------------------------------

            fitnesses = (
                evaluate_population(
                    population,
                    executor
                )
            )

            # ------------------------------------------------
            # Melhor da geração
            # ------------------------------------------------

            generation_best = max(
                fitnesses
            )

            best_index = (
                fitnesses.index(
                    generation_best
                )
            )

            minimum_fitness = min(fitnesses)
            mean_fitness = sum(fitnesses) / len(fitnesses)

            # ------------------------------------------------
            # Melhor global
            # ------------------------------------------------

            if (
                generation_best
                > best_fitness
            ):

                best_fitness = (
                    generation_best
                )

                # Importante:
                # copiar o indivíduo evita que futuras
                # mutações alterem o melhor global.
                best_individual = clone_individual(
                    population[best_index]
                )

            # ------------------------------------------------
            # Log
            # ------------------------------------------------

            generation_id = (
                generation + 1
            )

            generation_history.append(generation_id)
            minimum_fitness_history.append(minimum_fitness)
            mean_fitness_history.append(mean_fitness)
            generation_best_history.append(generation_best)
            best_fitness_history.append(best_fitness)

            if (
                generation_id
                % print_interval
                == 0
            ):

                print(
                    f"Generation "
                    f"{generation_id}/"
                    f"{GENERATIONS} "
                    f"- Worst: {minimum_fitness:.6f} "
                    f"- Mean: {mean_fitness:.6f} "
                    f"- Best: {generation_best:.6f} "
                    f"- Global: {best_fitness:.6f}"
                )

                # ------------------------------------------------
                # Salvar melhor MIDI
                # ------------------------------------------------
                if(False):
                    generate_midi(
                        best_individual,
                        "current_best.mid"
                    )

            # ------------------------------------------------
            # Nova população
            # ------------------------------------------------

            new_population = []

            # ------------------------------------------------
            # Elitismo
            # ------------------------------------------------

            if ELITISM:

                elite = (
                    population[
                        best_index
                    ]
                )

                new_population.append(
                    clone_individual(elite)
                )

            # ------------------------------------------------
            # Reprodução
            # ------------------------------------------------

            while len(
                new_population
            ) < POPULATION_SIZE:

                if random.random() < RANDOM_IMMIGRANT_RATE:

                    new_population.append(
                        initialize_individual()
                    )

                    continue

                parent1 = selection(
                    population,
                    fitnesses
                )

                parent2 = selection(
                    population,
                    fitnesses
                )

                child = crossover(
                    parent1,
                    parent2
                )

                child = mutate(
                    child
                )

                new_population.append(
                    child
                )

            # ------------------------------------------------
            # Substituição
            # ------------------------------------------------

            population = (
                new_population
            )

    finally:

        # ----------------------------------------------------
        # Finalização do executor
        # ----------------------------------------------------

        if executor is not None:

            executor.shutdown()

    # ========================================================
    # GRÁFICO DA EVOLUÇÃO DA FITNESS
    # ========================================================

    figure, axis = plt.subplots(figsize=(10, 6))
    axis.plot(
        generation_history,
        minimum_fitness_history,
        color="red",
        alpha=0.2,
        label="_nolegend_",
    )
    axis.plot(
        generation_history,
        moving_average(minimum_fitness_history, print_interval),
        color="red",
        linewidth=2.5,
        label="Worst",
    )
    axis.plot(
        generation_history,
        mean_fitness_history,
        color="gray",
        alpha=0.2,
        label="_nolegend_",
    )
    axis.plot(
        generation_history,
        moving_average(mean_fitness_history, print_interval),
        color="gray",
        linewidth=2.5,
        label="Mean",
    )
    axis.plot(
        generation_history,
        generation_best_history,
        color="green",
        label="Best",
    )
    axis.plot(
            generation_history,
            best_fitness_history,
            linewidth=4.0,
            alpha=0.25,
            color="blue",
            label="Global",
     )

    axis.scatter(
        generation_history[-1],
        best_fitness,
        color="blue",
        s=36,
        zorder=5,
    )
    axis.annotate(
        f"Global Best = {best_fitness:.6f}",
        xy=(generation_history[-1], best_fitness),
        xytext=(-8, 0),
        textcoords="offset points",
        ha="right",
        va="center",
        color="blue",
        fontsize=15,
        bbox={
            "facecolor": "white",
            "alpha": 0.75,
            "edgecolor": "none",
            "pad": 2,
        },
    )


    axis.set_title("Fitness evolution", fontsize=18)
    axis.set_xlabel("Generation", fontsize=15)
    axis.set_ylabel("Fitness", fontsize=15)
    axis.tick_params(axis="both", labelsize=15)
    axis.set_xticks(
        range(print_interval, GENERATIONS + 1, print_interval)
    )

    plotted_fitnesses = (
        minimum_fitness_history
        + mean_fitness_history
        + generation_best_history
        + best_fitness_history
    )
    minimum_plot_fitness = min(plotted_fitnesses)
    maximum_plot_fitness = max(plotted_fitnesses)
    if minimum_plot_fitness < maximum_plot_fitness:
        y_top_padding = (
            maximum_plot_fitness - minimum_plot_fitness
        ) * 0.05
    else:
        y_top_padding = max(abs(maximum_plot_fitness) * 0.05, 0.01)

    axis.set_ylim(
        minimum_plot_fitness,
        maximum_plot_fitness + y_top_padding,
    )

    axis.grid(True, alpha=0.3)
    axis.legend(loc="lower right", fontsize=15)
    figure.tight_layout()

    fitness_plot_path = run_output_dir / "fitness_evolution.png"
    figure.savefig(fitness_plot_path, dpi=150)
    plt.close(figure)
    print(f"Fitness graph saved in: {fitness_plot_path}")

    # ========================================================
    # RESULTADO FINAL
    # ========================================================

    generate_midi(
        best_individual,
        output_mid_path
    )

    if(DIVERSIFY_FINAL_MIDI):
        diversify_midi(
            output_mid_path,
            output_mid_plus_path,
            DIVERSIFY_MIDI_NOTES,
            DIVERSIFY_MIDI_INSTRUMENTS
        )
    else:
        shutil.copy(
            output_mid_path,
            output_mid_plus_path
        )

    midi_to_wav(
        output_mid_plus_path,
        output_wav_path
    )

    print()
    print(
        f"Melhor fitness: "
        f"{best_fitness:.4f}"
    )

    print(
        "MIDI salvo em: ",
        output_mid_path
    )

    pianoroll_script = (
        Path(__file__).resolve().parent
        / "generate_pianoroll.py"
    )

    subprocess.run(
        [
            sys.executable,
            str(pianoroll_script),
            output_mid_plus_path,
            output_png_path,
        ],
        check=True,
    )

    print(
        "Pianoroll salvo em: ",
        output_png_path
    )

    generate_video(
        output_wav_path,
        output_png_path,
        output_mp4_path
    )

    if(False):
        play_midi(
            output_mid_path
        )

# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    genetic_algorithm()
