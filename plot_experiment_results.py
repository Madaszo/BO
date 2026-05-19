import matplotlib.pyplot as plt
import json
import re
import pandas as pd
import pathlib

changing_variables_ga = ["population_size", "crossover_rate", "mutation_rate"]
changing_variables_bee = ["colony_size", "limit", "neighborhood_flips"]

config_file = "configs\\population_experiment.json"

results_folder = "results\\population"

fname_regex = re.compile(r"^population_(\d+).csv$")

ga_data = []
bee_data = []

config = json.load(open(config_file))

resd = pathlib.Path(results_folder)

for file in resd.iterdir():
    if file.is_file():
        match = fname_regex.match(file.name)
        if match is not None:
            n = int(match.group(1))
            settings = config[n]
            csv = pd.read_csv(file.resolve(), sep=",")
            for row in csv.itertuples():
                if row.solver == "GA":
                    tmp = {v:settings["ga_config"][v] for v in changing_variables_ga}
                    tmp["feasible"] = row.feasible
                    tmp["best_fitness"] = row.best_fitness
                    tmp["best_objective"] = row.best_objective
                    ga_data.append(tmp)
                else:
                    tmp = {v:settings["bee_config"][v] for v in changing_variables_bee}
                    tmp["feasible"] = row.feasible
                    tmp["best_fitness"] = row.best_fitness
                    tmp["best_objective"] = row.best_objective
                    bee_data.append(tmp)

dims = len(changing_variables_ga)

if dims == 1:
    pass
elif dims == 2:
    pass
elif dims == 3:
    x = [d[changing_variables_ga[0]] for d in ga_data]
    y = [d[changing_variables_ga[1]] for d in ga_data]
    z = [d[changing_variables_ga[2]] for d in ga_data]
    data = [d["best_objective"] for d in ga_data]
    fig = plt.figure(figsize=(9, 7))
    ax = fig.add_subplot(111, projection="3d")

    scatter = ax.scatter(
        x, y, z,
        c=data,
        cmap="viridis",
        alpha=0.8,
        edgecolors="none",
    )

    cbar = fig.colorbar(scatter, ax=ax, shrink=0.55, pad=0.1)
    cbar.set_label("Result", fontsize=11)
    
    ax.set_xlabel(changing_variables_ga[0])
    ax.set_ylabel(changing_variables_ga[1])
    ax.set_zlabel(changing_variables_ga[2])
    
    plt.tight_layout()
    plt.show()


