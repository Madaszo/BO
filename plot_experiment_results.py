import matplotlib.pyplot as plt
import json
import re
import pandas as pd
import pathlib
from math import log2


# all
#changing_variables_ga = ["population_size", "crossover_rate", "mutation_rate"]
#changing_variables_bee = ["colony_size", "limit", "neighborhood_flips"]
#config_file = "configs\\population_experiment.json"
#results_folder = "results\\population"
#fname_regex = re.compile(r"^population_(\d+).csv$")

# population_budget
#changing_variables_ga = ["population_size", "graph"]
#changing_variables_bee = ["colony_size", "graph"]
#config_file = "configs\\population_budget_experiment.json"
#results_folder = "results\\population_budget"
#fname_regex = re.compile(r"^population_budget_(\d+).csv$")

# mutation
#changing_variables_ga = ["mutation_rate"]
#changing_variables_bee = ["neighborhood_flips"]
#config_file = "configs\\mutation_experiments.json"
#results_folder = "results\\mutation"
#fname_regex = re.compile(r"^mutation_(\d+).csv$")

# budget
#changing_variables_ga = ["graph"]
#changing_variables_bee = ["graph"]
#config_file = "configs\\budget_experiments.json"
#results_folder = "results\\experiments"
#fname_regex = re.compile(r"^budget_(\d+).csv$")

#population_mutation_large
#changing_variables_ga = ["population_size", "crossover_rate"]
#changing_variables_bee = ["colony_size", "neighborhood_flips"]
#config_file = "configs\\population_mutation_large_experiment.json"
#results_folder = "results\\population_mutation_large"
#fname_regex = re.compile(r"^population_mutation_large_(\d+).csv$")

#elite_count
#changing_variables_ga = ["elite_count"]
#changing_variables_bee = []
#config_file = "configs\\elite_count_experiment.json"
#results_folder = "results\\elite_count"
#fname_regex = re.compile(r"^elite_count_(\d+).csv$")

# population_solo
#changing_variables_ga = ["population_size"]
#changing_variables_bee = ["colony_size"]
#config_file = "configs\\population_solo_experiment.json"
#results_folder = "results\\population_solo"
#fname_regex = re.compile(r"^population_solo_(\d+).csv$")

# generations
changing_variables_ga = ["generations"]
changing_variables_bee = []
config_file = "configs\\generations_experiment.json"
results_folder = "results\\generations"
fname_regex = re.compile(r"^generations_(\d+).csv$")


budget_regex = re.compile(r"road_buget_(\d+).json")

ga_data = []
bee_data = []

config = json.load(open(config_file))

resd = pathlib.Path(results_folder)

ga_budget = False
if "graph" in changing_variables_ga:
    changing_variables_ga.remove("graph")
    ga_budget = True

bee_budget = False
if "graph" in changing_variables_bee:
    changing_variables_bee.remove("graph")
    bee_budget = True

for file in resd.iterdir():
    if file.is_file():
        match = fname_regex.match(file.name)
        if match is not None:
            n = int(match.group(1))
            settings = config[n]
            csv = pd.read_csv(file.resolve(), sep=",")
            ga_i = 0
            bee_i = 0
            ga_data_point = {"best_objective":0}
            bee_data_point = {"best_objective":0}
            for row in csv.itertuples():
                if row.solver == "GA":
                    for v in changing_variables_ga:
                        ga_data_point[v] = settings["ga_config"][v]
                    if row.feasible == 0:
                        continue
                    if ga_budget:
                        ga_data_point["budget"] = int(budget_regex.search(settings["graph"]).group(1))
                    ga_i+=1
                    ga_data_point["best_objective"] += row.best_objective
                else:
                    for v in changing_variables_bee:
                        bee_data_point[v] = settings["bee_config"][v]
                    if row.feasible == 0:
                        continue
                    if bee_budget:
                        bee_data_point["budget"] = int(budget_regex.search(settings["graph"]).group(1))
                    bee_i+=1
                    bee_data_point["best_objective"] += row.best_objective
            if ga_i == 0:
                ga_i+=1
            if bee_i == 0:
                bee_i+=1
            ga_data_point["best_objective"] = ga_data_point["best_objective"]/ga_i
            bee_data_point["best_objective"] = bee_data_point["best_objective"]/bee_i
            ga_data.append(ga_data_point)
            bee_data.append(bee_data_point)

if ga_budget:
    changing_variables_ga.append("budget")

if bee_budget:
    changing_variables_bee.append("budget")

dims = len(changing_variables_ga)

if dims == 1:
    x = [d[changing_variables_ga[0]] for d in ga_data]
    y = [d["best_objective"] for d in ga_data]
    fig = plt.figure(figsize=(9, 7))
    ax = fig.add_subplot(111)
    scatter = ax.scatter(
        x, y,
        alpha=0.8,
        edgecolors="none",
    )
    ax.set_xlabel(changing_variables_ga[0])
    ax.set_ylabel("Result")

    plt.tight_layout()
    plt.show()

elif dims == 2:
    x = [d[changing_variables_ga[0]] for d in ga_data]
    y = [d[changing_variables_ga[1]] for d in ga_data]
    data = [d["best_objective"] for d in ga_data]
    fig = plt.figure(figsize=(9, 7))
    ax = fig.add_subplot(111)
    scatter = ax.scatter(
        x, y,
        c=data,
        cmap="jet",
        alpha=0.8,
        edgecolors="none",
    )

    #for i in range(len(x)):
    #    ax.annotate(str(data[i]), (x[i]-25, y[i]-85))

    cbar = fig.colorbar(scatter, ax=ax, shrink=0.55, pad=0.1)
    cbar.set_label("Result", fontsize=11)
    
    ax.set_xlabel(changing_variables_ga[0])
    ax.set_ylabel(changing_variables_ga[1])

    plt.tight_layout()
    plt.show()
elif dims == 3:
    x = [d[changing_variables_ga[0]] for d in ga_data]
    y = [d[changing_variables_ga[1]] for d in ga_data]
    z = [d[changing_variables_ga[2]] for d in ga_data]
    data = [log2(d["best_objective"]) for d in ga_data]
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
    cbar.set_label("Log results", fontsize=11)
    
    ax.set_xlabel(changing_variables_ga[0])
    ax.set_ylabel(changing_variables_ga[1])
    ax.set_zlabel(changing_variables_ga[2])
    
    plt.tight_layout()
    plt.show()


if dims == 1:
    x = [d[changing_variables_bee[0]] for d in bee_data]
    y = [d["best_objective"] for d in bee_data]
    fig = plt.figure(figsize=(9, 7))
    ax = fig.add_subplot(111)
    scatter = ax.scatter(
        x, y,
        alpha=0.8,
        edgecolors="none",
    )
    ax.set_xlabel(changing_variables_bee[0])
    ax.set_ylabel("Result")

    plt.tight_layout()
    plt.show()

elif dims == 2:
    x = [d[changing_variables_bee[0]] for d in bee_data]
    y = [d[changing_variables_bee[1]] for d in bee_data]
    data = [d["best_objective"] for d in bee_data]
    fig = plt.figure(figsize=(9, 7))
    ax = fig.add_subplot(111)
    scatter = ax.scatter(
        x, y,
        c=data,
        cmap="jet",
        alpha=0.8,
        edgecolors="none",
    )

    #for i in range(len(x)):
    #    ax.annotate(str(data[i]), (x[i]-25, y[i]-85))

    cbar = fig.colorbar(scatter, ax=ax, shrink=0.55, pad=0.1)
    cbar.set_label("Result", fontsize=11)
    
    ax.set_xlabel(changing_variables_bee[0])
    ax.set_ylabel(changing_variables_bee[1])

    plt.tight_layout()
    plt.show()
elif dims == 3:
    x = [d[changing_variables_bee[0]] for d in bee_data]
    y = [d[changing_variables_bee[1]] for d in bee_data]
    z = [d[changing_variables_bee[2]] for d in bee_data]
    data = [log2(d["best_objective"]) for d in bee_data]
    fig = plt.figure(figsize=(9, 7))
    ax = fig.add_subplot(111, projection="3d")

    scatter = ax.scatter(
        x, y, z,
        c=data,
        cmap="jet",
        alpha=0.8,
        edgecolors="none",
    )

    cbar = fig.colorbar(scatter, ax=ax, shrink=0.55, pad=0.1)
    cbar.set_label("Log scale result", fontsize=11)
    
    ax.set_xlabel(changing_variables_bee[0])
    ax.set_ylabel(changing_variables_bee[1])
    ax.set_zlabel(changing_variables_bee[2])
    
    plt.tight_layout()
    plt.show()