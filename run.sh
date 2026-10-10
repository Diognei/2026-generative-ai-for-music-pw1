#!/bin/bash
export POPULATION_SIZE=10
export GENERATIONS=10000
export GLOBAL_CROSSOVER_RATE=0.8
export GLOBAL_MUTATION_RATE=0.1
export ELITISM=true
python3 ./ga/evolve_algorithm.py
