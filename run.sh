#!/bin/bash
export POPULATION_SIZE=20
export GENERATIONS=20000
export GLOBAL_CROSSOVER_RATE=0.8
export GLOBAL_MUTATION_RATE=0.1
export ELITISM=true
python3 ./ga/evolve_algorithm.py
