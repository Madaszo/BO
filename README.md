# BO - Problem Remontu Drog (GA i Bee)

Projekt porownuje dwa podejscia metaheurystyczne dla problemu przydzialu ekip remontowych do drog:

- Algorytm genetyczny (GA)
- Algorytm pszczeli (Bee Colony)

Celem jest minimalizacja wazonego czasu remontow przy ograniczeniu budzetowym.

Uwaga: koszt ekipy liczony jest dziennie (koszt_ekipy * liczba dni pracy ekipy),
a nie jednorazowo przy pierwszym uzyciu.

W modelu dziala harmonogramowanie pracy ekip i twarda kara za nakladanie sie czasu tej samej ekipy (jedna ekipa nie moze byc jednoczesnie w dwoch miejscach).

Zalecany jeden punkt wejscia do calego workflow to [run_pipeline.py](run_pipeline.py), a szczegolowa dokumentacja techniczna jest w [docs/TECHNICAL_DOCUMENTATION.md](docs/TECHNICAL_DOCUMENTATION.md).

## Co jest w repo

- [src/model.py](src/model.py): definicja instancji problemu, ocena, harmonogram i kary
- [src/ga.py](src/ga.py): solver GA
- [src/bee.py](src/bee.py): solver Bee Colony
- [run_experiments.py](run_experiments.py): uruchamianie eksperymentu dla jednego zadanego grafu
- [run_pipeline.py](run_pipeline.py): jeden skrypt uruchamiajacy import danych, eksperymenty i wizualizacje
- [input_graph.json](input_graph.json): przykladowe dane wejsciowe
- [results/.gitkeep](results/.gitkeep): katalog wynikow lokalnych (pliki wynikowe sa ignorowane przez git)
- [docs/VISUALIZATION_HANDOFF.md](docs/VISUALIZATION_HANDOFF.md): przekazanie danych dla zespolu wizualizacji
- [docs/TECHNICAL_DOCUMENTATION.md](docs/TECHNICAL_DOCUMENTATION.md): pelna dokumentacja techniczna repozytorium

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

Standardowe uruchomienie dla jednego scenariusza:

```bash
python run_experiments.py --graph input_graph.json --repetitions 10 --iterations 120 --out single_graph_results.csv
```

Nowe możliwości konfiguracyjne:

- `--ga-config <path>` — opcjonalny plik JSON z parametrami GA (np. `configs/ga_config_example.json`).
- `--bee-config <path>` — opcjonalny plik JSON z parametrami Bee (np. `configs/bee_config_example.json`).
- `--runs-config <path>` — opcjonalny plik JSON zawierający tablicę definicji uruchomień; każdy wpis może nadpisać `graph`, `repetitions`, `iterations`, `out`, `ga_config` i `bee_config`.

Przykładowy `runs-config` znajduje się w `configs/runs_example.json` — jeżeli podasz `--runs-config`, wszystkie wpisy zostaną wykonane sekwencyjnie (najpierw pierwszy, potem drugi itd.). Parametry `repetitions` i `iterations` można przenieść do definicji każdego wpisu w `runs-config`.

Pliki konfiguracyjne `ga_config` i `bee_config` mogą być podane jako:
- ścieżka do pliku JSON, lub
- bezpośredni obiekt JSON (inline) w `runs-config`.

Format przykładowych plików konfiguracyjnych:

- `configs/ga_config_example.json` możliwe pola: `population_size`, `generations`, `crossover_rate`, `mutation_rate`, `tournament_size`, `elite_count`, `seed`.
- `configs/bee_config_example.json` możliwe pola: `colony_size`, `iterations`, `limit`, `neighborhood_flips`, `seed`.

Program wygeneruje (dla każdego uruchomienia):

- `results/<out>`: CSV z metrykami uruchomień
- `results/<out>_matrices.json`: macierze przypisań, harmonogramy i overlaps
- `results/<out>_history.json`: historia najlepszego fitnessu z każdej iteracji/pokolenia

## Format Danych Wejsciowych (`--graph`)

Wymagane pola JSON:

- `edges`: lista drog, kazda droga ma `base_time` i `load`
- `crew_costs`: koszty ekip
- `budget`: budzet calkowity w modelu kosztu dziennego ekip

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
- `results/*_history.json`

Zawiera m.in.:

- `instance`: dane instancji
- `best_overall.ga.matrix` i `best_overall.bee.matrix`
- `best_overall.*.schedule` (start, end, interwaly ekip)
- `best_overall.*.overlaps_count` i `schedule.overlaps`
- `runs`: wszystkie powtorzenia

Plik `*_history.json` zawiera:

- `runs[].ga.history_best_fitness`: najlepszy fitness GA dla kazdego pokolenia
- `runs[].bee.history_best_fitness`: najlepszy fitness Bee dla kazdej iteracji
- `runs[].*.history_length`: dlugosc historii dla walidacji

Szczegoly mapowania sa w [docs/VISUALIZATION_HANDOFF.md](docs/VISUALIZATION_HANDOFF.md).

## Import danych OSM (real data importing)

W repo znajduje się prosty skrypt do parsowania danych z Overpass/OSM:

- `overpass_turbo_query.txt` — przykładowe zapytanie Overpass (użyj na https://overpass-turbo.eu/)
- `real_data_import.py` — skrypt parsujący `road_data.json` (dane Overpass) -> `parsing_results.json` używane jako `--graph` dla `run_experiments.py`.

Uwaga: w repo trafił duży plik `road_data.json` (surowe OSM). Lepiej przechowywać pobrane OSM poza VCS i trzymać jedynie wynikowy `parsing_results.json` albo przechowywać dane na dysku współdzielonym.

Przykładowe użycie:
```powershell
# Pobierz/umieść road_data.json w katalogu projektu, następnie:
python real_data_import.py
# wygeneruje parsing_results.json
```

## Wizualizacja wyników

Do tworzenia diagramów z wyników służy `visualize.py`. Skrypt szuka plików `*_matrices.json` w katalogu `results/` i generuje obrazy PNG obok nich.

Uruchomienie:
```powershell
python visualize.py
```

Plik wyjściowy np. `results/real_graph_results_run1_graf.png` zawiera:
- graf dróg i przypisanych ekip
- kolejność pracy ekip (liczby przy strzałkach)
- makespan i informację o wykonalności

Wymagane pakiety: `matplotlib`, `numpy` (powinny być na liście w `requirements.txt`).

## Dla Wspolpracy w Zespole

1. Clone repo i uruchom setup srodowiska z tej instrukcji.
2. Tworz branch do zmian, np. `feature/visualization` lub `feature/ga-tuning`.
3. Przed PR odpal testowe uruchomienie skryptu i dolacz opis zmian.
4. Nie commituj lokalnego `.venv` ani plikow z `results/`.

## Szybki Smoke Test

```bash
python run_experiments.py --graph input_graph.json --repetitions 1 --iterations 8 --out smoke.csv
```
