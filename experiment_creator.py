import json

experiment_name = "population_budget"

fp = open(f"configs/{experiment_name}_experiment.json", "x")

runs = []

n = 0

for i in range(100,1001, 100):
    for j in range(17000, 20001, 500):
        iteration = {
            "graph": f"graphs/road_buget_{j}.json",
            "repetitions": 1,
            "iterations": 100,
            "out": f"results/{experiment_name}/{experiment_name}_{n}.csv",
            "ga_config": {
            "population_size": i,
            "generations": 50,
            "crossover_rate": 0.85,
            "mutation_rate": 0.05,
            "seed": 100
            },
            "bee_config": {
            "colony_size": i,
            "iterations": 50,
            "limit": 40,
            "neighborhood_flips": 3,
            "seed": 200
            }
        }
        runs.append(iteration)

json.dump(runs, fp, indent=1)
fp.close()