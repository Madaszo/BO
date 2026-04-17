# Visualization Handoff

Ten dokument jest kontraktem danych dla zespolu wizualizacji.
Opisuje, jakie pliki generuje program, jaka jest ich struktura i jak je mapowac na wykresy.

## 1) Jak wygenerowac dane

Uruchom:

```bash
python run_experiments.py --graph input_graph.json --repetitions 10 --iterations 120 --out single_graph_results.csv
```

Po uruchomieniu powstaja 3 pliki w katalogu results:

- single_graph_results.csv
- single_graph_results_matrices.json
- single_graph_results_history.json

## 2) Cel kazdego pliku

### 2.1 single_graph_results.csv

Plik do szybkich tabel i statystyk agregowanych.
Kazdy wiersz to jeden solver (GA lub Bee) dla jednego powtorzenia.

Kolumny:

- rep
- solver
- best_fitness
- best_objective
- feasible
- time_s

### 2.2 single_graph_results_matrices.json

Plik do wizualizacji rozwiazan i harmonogramu.

Zawiera:

- instance: definicja instancji (drogi, koszty ekip, budzet)
- best_overall: najlepszy run dla GA i najlepszy run dla Bee
- runs: wszystkie powtorzenia z pelnymi danymi rozwiazania

Kluczowe sciezki:

- instance.edge_ids
- instance.base_times
- instance.loads
- instance.crew_costs
- best_overall.ga.matrix
- best_overall.bee.matrix
- best_overall.ga.schedule
- best_overall.bee.schedule
- runs[].ga
- runs[].bee

### 2.3 single_graph_results_history.json

Plik do wykresow zbieznosci (convergence curves).

Zawiera:

- runs[].ga.history_best_fitness
- runs[].bee.history_best_fitness
- runs[].ga.history_length
- runs[].bee.history_length

Interpretacja:

- GA: wartosci sa zapisane per pokolenie.
- Bee: wartosci sa zapisane per iteracje kolonii.

## 3) Jak czytac macierz rozwiazania

Macierz ma wymiary crews x edges:

- wiersz = indeks ekipy
- kolumna = indeks drogi
- wartosc 1 = ekipa przypisana do drogi
- wartosc 0 = brak przypisania

Mapowanie kolumn na drogi:

- kolumna j odpowiada instance.edge_ids[j]

## 4) Harmonogram i konflikty ekip

W schedule znajdziesz:

- edge_starts: czas startu kazdej drogi
- edge_ends: czas konca kazdej drogi
- edge_durations: czas trwania kazdej drogi
- crew_intervals: lista przedzialow [start, end, edge_index] dla kazdej ekipy
- overlaps: wykryte konflikty tej samej ekipy

W tym projekcie konflikt pracy tej samej ekipy jest mocno karany (hard penalty).
Praktycznie dobre rozwiazania powinny miec:

- overlaps_count = 0
- schedule.overlaps puste

