#!/bin/bash

export POPULATION_SIZE=10
export GENERATIONS=10000
export GLOBAL_CROSSOVER_RATE=0.5
export GLOBAL_MUTATION_RATE=0.5
export ELITISM=false
python3 ./ga/evolve_algorithm.py

export POPULATION_SIZE=10
export GENERATIONS=10000
export GLOBAL_CROSSOVER_RATE=0.5
export GLOBAL_MUTATION_RATE=0.5
export ELITISM=true
python3 ./ga/evolve_algorithm.py

export POPULATION_SIZE=10
export GENERATIONS=10000
export GLOBAL_CROSSOVER_RATE=0.8
export GLOBAL_MUTATION_RATE=0.1
export ELITISM=false
python3 ./ga/evolve_algorithm.py

export POPULATION_SIZE=10
export GENERATIONS=10000
export GLOBAL_CROSSOVER_RATE=0.8
export GLOBAL_MUTATION_RATE=0.1
export ELITISM=true
python3 ./ga/evolve_algorithm.py

export POPULATION_SIZE=20
export GENERATIONS=20000
export GLOBAL_CROSSOVER_RATE=0.8
export GLOBAL_MUTATION_RATE=0.1
export ELITISM=true
python3 ./ga/evolve_algorithm.py
