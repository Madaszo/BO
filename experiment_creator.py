import json

experiment_name = "population"

fp = open(f"configs/{experiment_name}_experiment.json", "x")

runs = []

n = 0

for i in range(100,1001, 100):
    for j in [0, 5, 20, 50, 85, 95]:
        for k in [0, 5, 20, 50, 85, 95]:
            iteration = {
                "graph": "graphs/parsing_results.json",
                "repetitions": 1,
                "iterations": 100,
                "out": f"{experiment_name}/{experiment_name}_{n}.csv",
                "ga_config": {
                "population_size": i,
                "generations": 50,
                "crossover_rate": j/100,
                "mutation_rate": k/100,
                "seed": 100
                },
                "bee_config": {
                "colony_size": i,
                "iterations": 100,
                "limit": k,
                "neighborhood_flips": j//5,
                "seed": 200
                }
            }
            runs.append(iteration)
            n+=1

json.dump(runs, fp, indent=1)
fp.close()