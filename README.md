# BO - Problem Remontu Drog (GA i Bee)

Projekt porownuje dwa podejscia metaheurystyczne dla problemu przydzialu ekip remontowych do drog:

- Algorytm genetyczny (GA)
- Algorytm pszczeli (Bee Colony)

Celem jest minimalizacja wazonego czasu remontow przy ograniczeniu budzetowym.

W modelu dziala harmonogramowanie pracy ekip i twarda kara za nakladanie sie czasu tej samej ekipy (jedna ekipa nie moze byc jednoczesnie w dwoch miejscach).

## Co jest w repo

- [src/model.py](src/model.py): definicja instancji problemu, ocena, harmonogram i kary
- [src/ga.py](src/ga.py): solver GA
- [src/bee.py](src/bee.py): solver Bee Colony
- [run_experiments.py](run_experiments.py): uruchamianie eksperymentu dla jednego zadanego grafu
- [input_graph.json](input_graph.json): przykladowe dane wejsciowe
- [results/.gitkeep](results/.gitkeep): katalog wynikow lokalnych (pliki wynikowe sa ignorowane przez git)
- [docs/VISUALIZATION_HANDOFF.md](docs/VISUALIZATION_HANDOFF.md): przekazanie danych dla zespolu wizualizacji

## Wymagania

- Python 3.11+ (testowane na 3.14)
- pip

## Setup Srodowiska

### Windows (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### Linux/macOS (bash/zsh)

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Uruchomienie

```bash
python run_experiments.py --graph input_graph.json --repetitions 10 --iterations 120 --out single_graph_results.csv
```

Program wygeneruje:

- `results/single_graph_results.csv`: metryki uruchomien
- `results/single_graph_results_matrices.json`: macierze przypisan, harmonogramy i overlaps

## Format Danych Wejsciowych (`--graph`)

Wymagane pola JSON:

- `edges`: lista drog, kazda droga ma `base_time` i `load`
- `crew_costs`: koszty ekip
- `budget`: budzet calkowity

Przyklad:

```json
{
  "edges": [
    {"id": "e1", "base_time": 14, "load": 7},
    {"id": "e2", "base_time": 11, "load": 9}
  ],
  "crew_costs": [6, 8, 7],
  "budget": 20
}
```

## Co Oznacza `load`

`load` to waga obciazenia drogi. Im wyzsze `load`, tym bardziej kosztowne jest dlugie zamkniecie tej drogi w funkcji celu.

## Dane Dla Wizualizacji

Najwazniejszy plik do dashboardu:

- `results/*_matrices.json`

Zawiera m.in.:

- `instance`: dane instancji
- `best_overall.ga.matrix` i `best_overall.bee.matrix`
- `best_overall.*.schedule` (start, end, interwaly ekip)
- `best_overall.*.overlaps_count` i `schedule.overlaps`
- `runs`: wszystkie powtorzenia

Szczegoly mapowania sa w [docs/VISUALIZATION_HANDOFF.md](docs/VISUALIZATION_HANDOFF.md).

## Dla Wspolpracy w Zespole

1. Clone repo i uruchom setup srodowiska z tej instrukcji.
2. Tworz branch do zmian, np. `feature/visualization` lub `feature/ga-tuning`.
3. Przed PR odpal testowe uruchomienie skryptu i dolacz opis zmian.
4. Nie commituj lokalnego `.venv` ani plikow z `results/`.

## Szybki Smoke Test

```bash
python run_experiments.py --graph input_graph.json --repetitions 1 --iterations 8 --out smoke.csv
```
