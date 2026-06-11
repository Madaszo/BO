# Algorytm Genetyczny

## 1. Cel i zastosowanie

GA rozwiązuje problem harmonogramowania remontów dróg: przypisuje ekipy remontowe do odcinków drogowych tak, by zminimalizować czas zakończenia wszystkich prac (makespan) bez przekraczania budżetu. Ze względu na wykładniczą przestrzeń rozwiązań (każda ekipa może być przypisana do każdego podzbioru odcinków), dokładne metody kombinatoryczne są praktycznie nieużywalne już dla kilkunastu ekip i kilkudziesięciu odcinków — GA jest jedną z dwóch metaheurystyk porównywanych w projekcie, obok algorytmu pszczelego (`src/bee.py`).

---

## 2. Reprezentacja rozwiązania

Rozwiązanie to binarna macierz `crews × edges`:

```
solution[i][j] = 1  →  ekipa i jest przypisana do odcinka j
solution[i][j] = 0  →  brak przypisania
```

Przykład dla 3 ekip i 4 odcinków:

```
          droga_0  droga_1  droga_2  droga_3
ekipa_0  [  1,      0,       1,       0   ]
ekipa_1  [  0,      1,       1,       0   ]
ekipa_2  [  1,      0,       0,       1   ]
```

Każdy odcinek musi mieć przypisaną co najmniej jedną ekipę — jest to twarde ograniczenie egzekwowane przez mechanizm naprawy (sekcja 8).

---

## 3. Inicjalizacja populacji

Każde z `population_size` rozwiązań startowych jest generowane losowo: każdy bit jest ustawiany na 1 z prawdopodobieństwem 0,35. Przeciętne rozwiązanie startowe ma więc ok. jednej trzeciej ekip przypisanych do danego odcinka. Po wygenerowaniu każde rozwiązanie jest naprawiane (sekcja 8).

Wartość 0,35 jest hardcoded w `_random_solution()` i wynika z kompromisu między zbyt rzadkim wypełnieniem (wiele naruszeń ograniczenia przypisań) a zbyt gęstym (wysokie koszty ekip).

---

## 4. Funkcja celu i ocena rozwiązania

**Cel:** minimalizacja makespanu

```
Z(s, X) = max({ s_e + t(e) | e ∈ E })
```

gdzie `s_e` to czas rozpoczęcia remontu odcinka `e`, a `t(e)` to czas jego trwania.

**Czas trwania remontu** zależy od liczby przypisanych ekip `k`:

```
t(e) = ceil( 2^(-k+1) · base_time[e] )
```

Każda dodatkowa ekipa skraca czas o połowę: jedna ekipa to pełny `base_time`, dwie ekipy to 50%, trzy ekipy to 25% itd. Jeśli do odcinka przypisane są dwie lub więcej ekip, wszystkie pracują równocześnie — zaczynają, gdy ostatnia z nich skończy poprzednie zadanie.

**Kolejność remontów** wyznaczana jest malejąco według `load[e] · base_time[e]` — odcinki o najwyższym obciążeniu i najdłuższym czasie bazowym remontowane są pierwsze.

**Koszt ekip** liczony jest za przepracowane dni:

```
koszt = Σ_i  Σ_e  solution[i][e] · t(e) · crew_cost[i]
```

### Kary

Fitness jest sumą wartości obiektywnej i kar:

| Naruszenie | Kara |
|---|---|
| Odcinek bez żadnej ekipy | `10 000` za odcinek |
| Przekroczenie budżetu | `1 000 × budget_excess` |
| Nakładanie się pracy ekipy | `1 000 000 000` za każdą nakładkę |

Kara za nakładki jest celowo astronomiczna — traktuje harmonogramy z kolizjami jako praktycznie niedopuszczalne, bez usuwania ich formalnie z populacji.

---

## 5. Selekcja

Selekcja turniejowa: do każdego turnieju losowanych jest `tournament_size` osobników z bieżącej populacji — wygrywa ten z najniższym fitness. Domyślnie turniej obejmuje 3 osobniki.

Selekcja turniejowa jest odporna na dominację pojedynczych super-osobników i ogranicza ryzyko przedwczesnej zbieżności populacji.

---

## 6. Krzyżowanie

Krzyżowanie jednopunktowe na spłaszczonej reprezentacji macierzy. Macierz `crews × edges` jest spłaszczana do wektora bitów; losowany jest punkt cięcia, po czym powstają dwa potomki przez wymianę sufixów:

```
Rodzic A: [1, 0, 1, 1 | 0, 0, 1, 0]
Rodzic B: [0, 1, 0, 0 | 1, 1, 0, 1]
                      ^
                 punkt cięcia

Potomek 1: [1, 0, 1, 1, 1, 1, 0, 1]
Potomek 2: [0, 1, 0, 0, 0, 0, 1, 0]
```

Para rodziców krzyżuje się z prawdopodobieństwem `crossover_rate`; jeśli krzyżowanie nie zachodzi, potomkowie są kopiami rodziców. Obaj potomkowie są następnie naprawiani.

---

## 7. Mutacja

Bitflip: każdy bit macierzy jest odwracany niezależnie z prawdopodobieństwem `mutation_rate`. Przy domyślnej wartości 0,03 przeciętna mutacja zmienia ok. 3% pozycji macierzy. Po mutacji rozwiązanie jest naprawiane.

---

## 8. Mechanizm naprawy

Naprawa jest wywoływana po inicjalizacji, krzyżowaniu i mutacji — gwarantuje, że każde rozwiązanie trafiające do populacji spełnia ograniczenia twarde. Składa się z dwóch kroków wykonywanych w tej kolejności:

1. **Naprawa przypisań** (`_repair_assignment`): jeśli odcinek `j` nie ma żadnej ekipy, przypisywana jest do niego ekipa o indeksie `j % crews_count`.

2. **Naprawa budżetu** (`_repair_budget`): jeśli łączny koszt przekracza budżet, algorytm iteruje po ekipach od najdroższej do najtańszej. Dla każdej drogiej ekipy przegląda odcinki, na których jest przypisana i gdzie pracuje co najmniej jedna inna ekipa — wtedy zastępuje ją najtańszą dostępną ekipą i sprawdza, czy budżet jest już spełniony. Odcinki obsadzone przez jedną ekipę są pomijane.

Po naprawie budżetu naprawa przypisań jest wywoływana ponownie, ponieważ usunięcia mogły zostawić odcinki bez obsady.

---

## 9. Elityzm i budowanie następnej generacji

Pierwsze `elite_count` osobników z najniższym fitness przechodzi do następnej generacji bez modyfikacji. Reszta miejsc jest wypełniana potomkami z selekcji, krzyżowania i mutacji. Domyślnie `elite_count = 2`.

---

## 10. Warunek stopu

Algorytm wykonuje dokładnie `generations` iteracji — nie ma kryterium zbieżności ani wczesnego zatrzymania. Historia najlepszego fitness z każdej generacji jest zapisywana w `SolverResult.history` i dostępna do późniejszej wizualizacji.

---

## 11. Parametry konfiguracyjne

| Parametr | Typ | Domyślna wartość | Opis |
|---|---|---|---|
| `population_size` | `int` | `80` | Liczba osobników w populacji |
| `generations` | `int` | `180` | Liczba iteracji |
| `crossover_rate` | `float` | `0.85` | Prawdopodobieństwo krzyżowania pary rodziców |
| `mutation_rate` | `float` | `0.03` | Prawdopodobieństwo odwrócenia pojedynczego bitu |
| `tournament_size` | `int` | `3` | Liczba osobników losowanych do turnieju selekcji |
| `elite_count` | `int` | `2` | Liczba elitarnych osobników niepodlegających operatorom genetycznym |
| `seed` | `int` | `42` | Ziarno generatora pseudolosowego (powtarzalność eksperymentów) |

---

## 12. Przykładowa konfiguracja

```json
{
  "population_size": 100,
  "generations": 200,
  "crossover_rate": 0.9,
  "mutation_rate": 0.02,
  "tournament_size": 5,
  "elite_count": 4,
  "seed": 42
}
```

Plik konfiguracyjny jest przekazywany do `run_experiments.py`, który tworzy obiekt `GAConfig` i wywołuje `solve_ga(instance, cfg)`.

---

## 13. Powiązane moduły

| Plik | Rola |
|---|---|
| `src/ga.py` | Implementacja algorytmu |
| `src/model.py` | Model problemu, ewaluacja fitness, mechanizm naprawy, harmonogramowanie |
| `configs/ga_config_example.json` | Przykładowa konfiguracja |
| `run_experiments.py` | Uruchamianie eksperymentów z GA (i Bee) |
