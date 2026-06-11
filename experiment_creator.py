import json
import random

experiment_name = "population_solo"

fp = open(f"configs/{experiment_name}_experiment.json", "x")

runs = []

n = 0

for i in range(50, 10001, 50):
    iteration = {
        "graph": "graphs/parsing_results.json",
        "repetitions": 5,
        "iterations": 100,
        "out": f"{experiment_name}/{experiment_name}_{n}.csv",
        "ga_config": {
        "population_size": i,
        "generations": 50,
        "crossover_rate": 0.5,
        "mutation_rate": 0.9,
        "seed": random.randint(0, 1000)
        },
        "bee_config": {
        "colony_size": i,
        "iterations": 50,
        "limit": 100,
        "neighborhood_flips": 20,
        "seed": random.randint(0, 1000)
        }
    }
    runs.append(iteration)
    n+=1
        

json.dump(runs, fp, indent=1)
fp.close()