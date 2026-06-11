#set text(lang: "PL")
#set heading(numbering: "1.")
#set math.equation(numbering: "(1)", supplement: none)
#set page(
  header: align(left+horizon, [Badania operacyjne - Problem remontu dróg])
)
#align(center,text(17pt)[*Badania operacyjne - Problem remontu dróg*])

#v(1em)
#outline(indent: 1em)
#v(1em)

= Wstęp
Pewne miasto ma problem, wszystkie jego drogi znajdują się w fatalnym stanie i muszą zostać wymienione. Miasto jednak dysponuje ograniczoną ilością załóg remontowych. Jednocześnie chce żeby remonty były zakończone jak najszybciej i powodowały jak najmniej problemów dla mieszkańców. Celem projektu jest stworzenie aplikacji wykorzystującej algorytm genetyczny i algorytm pszczeli, do rozwiązania tego problemu.
= Model
== Wejścia
Wejściem do problemu jest graf reprezentujący siatkę drogową miasta:
$ G = (E, V) $
- Każda krawędź $e$ (droga) posiada wagę $t_s$, która oznacza podstawowy czas potrzebny na remont. Do każdej drogi można przydzielić dowolną liczbę ekip remontowych $n$. Wtedy czas remontu będzie wynosił:
$ t(e) = ceil(2^(-n+1) * t_(s e)) $
- Każda krawędź posiada także wagę $d$ opisującą trudność drogi. Waga ta nie modyfikuje bezpośrednio czasu pracy, lecz służy wyłącznie do ustalania priorytetu dróg przy deterministycznym układaniu harmonogramu. Drogi są sortowane malejąco według iloczynu $d_e * t_(s e)$.
#image("graf.png", width: 50%)
Kolejnym wejściem jest liczba ekip remontowych $r$. Każda ekipa remontowa posiada koszt $k_i$ który musimy ponieść jeśli korzystamy z jej usług. Ten koszt jest ponoszony każdego dnia gdy korzystamy z danej ekipy. Mamy określony budżet $b$ którego nie możemy przekroczyć.
== Przedstawienie problemu
Problem rozwiązujemy macierzą $X$, która przedstawia przypisanie ekip do dróg. Kolejność dróg jest wyznaczana deterministycznie przez posortowanie ich malejąco według iloczynu $d_e$ i $t_(s e)$. Na podstawie tej kolejności obliczany jest wektor $s$, który zawiera czas rozpoczęcia prac nad każdą drogą. Jest on używany do obliczenia funkcji kosztu oraz sprawdzania ograniczeń.
== Funkcja kosztu
//$ Z(x_11, x_21, ... , x_(r 1), ..., x_(r |E|)) = sum_(e=0)^(|E|) d_e  dot ceil(2^(-(sum_(i=0)^r x_(i e))  + 1) * t_(s e)) -> "MIN" $
$ Z(s, X) = max({s_e + t(e)| e in E}) -> "MIN" $
== Ograniczenia
$ 0<= x_(i e) <= 1, x_(i e) in NN $
$ sum_(i=0)^r x_(i e) >= 1 $
Ograniczenia podane we wzorze 4 i 5 nakazują że każda droga musi mieć przynajmniej jedną przypisaną ekipę.

Zmienne $s$ określają początek pracy nad drogą $e$
$ s_(e) >= 0 $
$ s_(e) * (x_(i e) - 1) >= 0 $
$ s_(e') >= s_(e) + ceil(2^(-(sum_(i=0)^r x_(i e))  + 1) * t_(s e)) * x_(i e)  $
Ograniczenia z wzorów 6, 7, i 8  nakazują że jedna ekipa nie może pracować nad więcej niż jedną drogą jednocześnie.

$ b >= sum_(i=0)^k k_i (sum_(e=0)^(|E|)x_(e i)*t(e)) $

Ograniczenie ze wzoru 9 nakazuje że nie możemy przekroczyć budżetu płacąc każdej ekipie jej koszt za każdy dzień pracy.
== Wejście do algorytmu
Dane których używamy to części mapy z OpenStreetMap. Z danych mapowych izolujemy dane o drogach. Następnie na podstawie tych danych tworzymy graf. Też z tych danych otrzymujemy wagi dla naszych krawędzi w grafie. Waga $t_s$ jest długością drogi liczoną jako odległość Haversine-a żeby bać pod uwagę kulistość planety. Waga $d$ jest otrzymywana z klasyfikacji drogi w danych, np autostrada ma największą wagę a lokalna droga najmniejszą.
= Rozwiązanie problemu
== Algorytm Genetyczny
Pierwszym algorytmem rozwiązującym ten problem jest algorytm genetyczny. Jego celem jest iteracyjne przeszukiwanie przestrzeni rozwiązań w kierunku minimalizacji funkcji przystosowania. W kontekście rozpatrywanego problemu funkcją tą jest $Z(s, X)$.

*Reprezentacja osobnika:* Pojedynczy osobnik (chromosom) koduje pełne rozwiązanie problemu i składa się wyłącznie z macierzy przypisań $X in {0,1}^(r times |E|)$, określającej które ekipy pracują przy których drogach. Kolejność dróg nie jest częścią chromosomu, ponieważ jest zawsze wyznaczana deterministycznie podczas budowy harmonogramu.

*Populacja początkowa:* Algorytm rozpoczyna działanie od wygenerowania populacji $P$ losowych osobników o ustalonej wielkości. Każdy osobnik jest tworzony tak, aby spełniał ograniczenie przypisania co najmniej jednej ekipy do każdej drogi.

*Funkcja przystosowania:* Jakość osobnika oceniana jest na podstawie wartości $Z(s, X)$. Dodatkowo uwzględniane są kary za naruszenie ograniczenia budżetowego oraz za nakładanie się prac tej samej ekipy w tym samym czasie. Im niższa wartość funkcji przystosowania, tym lepsze rozwiązanie.

*Selekcja:* Do reprodukcji osobniki wybierane są metodą turniejową — z populacji losowana jest grupa o rozmiarze $t$ (parametr `tournament_size`), a najlepszy osobnik z tej grupy zostaje rodzicem. Procedura powtarzana jest dwukrotnie w celu wyłonienia pary rodziców.

*Krzyżowanie (crossover):* Para rodziców z prawdopodobieństwem `crossover_rate` poddawana jest operacji krzyżowania. Najpierw macierz przypisań $X$ jest spłaszczana do jednowymiarowego wektora, następnie wykonywane jest klasyczne krzyżowanie jednopunktowe, a na końcu potomek jest konwertowany z powrotem do macierzy 2D. Dzięki temu krzyżowanie działa na całej reprezentacji rozwiązania, ale bez dodawania osobnego genu dla kolejności dróg.

*Mutacja:* Potomek z prawdopodobieństwem `mutation_rate` podlega mutacji — losowej modyfikacji fragmentu chromosomu. Mutacja polega na odwracaniu wybranych bitów macierzy przypisań, czyli zmianie wartości $0$ na $1$ lub $1$ na $0$. Po mutacji rozwiązanie jest naprawiane tak, aby nadal spełniało podstawowe ograniczenia.

*Elitaryzm:* Pewna liczba najlepszych osobników (`elite_count`) jest bezpośrednio przenoszona do następnego pokolenia bez modyfikacji, co gwarantuje niemalejącą jakość najlepszego znalezionego rozwiązania.

*Przebieg algorytmu:* Pętla ewolucyjna powtarza się przez zadaną liczbę pokoleń (`generations`):
+ Ocena przystosowania wszystkich osobników w populacji.
+ Przeniesienie elity do nowej populacji.
+ Dopóki nowa populacja nie osiągnie zadanego rozmiaru:
  + Selekcja turniejowa dwóch rodziców.
  + Krzyżowanie rodziców z prawdopodobieństwem `crossover_rate`.
  + Mutacja potomka z prawdopodobieństwem `mutation_rate`.
  + Naprawa potomka i dodanie go do nowej populacji.
+ Zastąpienie starej populacji nową.

Po zakończeniu ostatniego pokolenia zwracany jest najlepszy znaleziony osobnik, czyli rozwiązanie o najniższej wartości $Z(s, X)$.

```text
Algorytm Genetyczny(instance, cfg):
  P <- losowa populacja macierzy X
  dla każdego osobnika w P:
    napraw osobnika

  dla g od 1 do generations:
    oceń fitness wszystkich osobników w P
    zachowaj elite_count najlepszych osobników w nowej_populacji

    dopóki nowa_populacja ma mniej niż population_size osobników:
      p1 <- selekcja turniejowa z P
      p2 <- selekcja turniejowa z P

      jeśli los() < crossover_rate:
        a <- flatten(p1)
        b <- flatten(p2)
        punkt <- losowy punkt jednopunktowego krzyżowania
        c1 <- unflatten(a[:punkt] + b[punkt:])
        c2 <- unflatten(b[:punkt] + a[punkt:])
      inaczej:
        c1 <- kopia p1
        c2 <- kopia p2

      jeśli los() < mutation_rate:
        odwróć losowe bity w c1
      jeśli los() < mutation_rate:
        odwróć losowe bity w c2

      napraw c1
      napraw c2
      dodaj c1 do nowej_populacji
      jeśli nowa_populacja nie jest pełna:
        dodaj c2 do nowej_populacji

    P <- nowa_populacja

  zwróć najlepszy osobnik z P
```

== Algorytm Pszczeli
Drugim z algorytmów zastosowanych do rozwiązania problemu jest algorytm pszczelego roju, zwany również pszczelim. Jego działanie opiera się na iteracyjnym przeszukiwaniu przestrzeni rozwiązań poprzez naśladowanie zachowań roju pszczół poszukujących pożywienia. W kontekście rozpatrywanego problemu każde źródło pożywienia odpowiada jednemu rozwiązaniu opisanemu wyłącznie przez macierz przypisań $X$, a jego jakość oceniana jest za pomocą funkcji celu $Z(s, X)$.

*Reprezentacja rozwiązania:* Pojedyncze źródło pożywienia koduje pełne rozwiązanie problemu i składa się wyłącznie z macierzy przypisań $X \in {0,1}^{r times|E|}$, określającej które ekipy pracują przy których drogach. Kolejność dróg nie jest częścią rozwiązania, ponieważ jest zawsze wyznaczana deterministycznie podczas harmonogramowania.

*Populacja początkowa:* Algorytm rozpoczyna działanie od wygenerowania zbioru losowych źródeł pożywienia o ustalonej liczbie. Każde rozwiązanie jest tworzone tak, aby spełniało ograniczenie przypisania co najmniej jednej ekipy do każdej drogi.

*Funkcja jakości:* Jakość źródła pożywienia oceniana jest na podstawie wartości $Z(s, X)$. Dodatkowo uwzględniane są kary za naruszenie ograniczenia budżetowego oraz za nakładanie się prac tej samej ekipy w tym samym czasie. Im niższa wartość funkcji celu, tym lepsze rozwiązanie.

*Pszczoły zatrudnione:* Każde źródło pożywienia jest przypisane do jednej pszczoły zatrudnionej. W każdej iteracji pszczoła generuje nowe rozwiązanie w sąsiedztwie aktualnego źródła przez odwracanie losowych bitów w macierzy przypisań. Liczba odwróconych bitów jest kontrolowana przez parametr `neighborhood_flips`. Jeżeli nowe rozwiązanie jest lepsze od dotychczasowego, zastępuje ono poprzednie źródło pożywienia.

*Pszczoły obserwatorki:* Po zakończeniu fazy pszczół zatrudnionych pszczoły obserwatorki wybierają źródła pożywienia z prawdopodobieństwem zależnym od ich jakości. Ponieważ problem jest minimalizowany, wybór jest realizowany selekcją ruletkową opartą na odwrotności funkcji kosztu: lepsze rozwiązania mają większą szansę na wybór. Następnie dla wybranych źródeł generowane są nowe rozwiązania sąsiednie, które mogą zastąpić rozwiązania aktualne, jeśli okażą się korzystniejsze.

*Pszczoły zwiadowcy:* Jeżeli dane źródło pożywienia nie uległo poprawie przez określoną liczbę iteracji (limit), zostaje ono porzucone. Wówczas odpowiadająca mu pszczoła staje się zwiadowcą i generuje nowe losowe rozwiązanie, które zastępuje porzucone źródło. Mechanizm ten zwiększa eksplorację przestrzeni rozwiązań i ogranicza ryzyko utknięcia w optimum lokalnym.

*Generowanie sąsiedztwa:* Modyfikacja rozwiązania polega na odwracaniu wartości losowych bitów w macierzy przypisań, czyli zmianie $0$ na $1$ lub $1$ na $0$. Liczba takich zmian wynika z parametru `neighborhood_flips`, dlatego sąsiedztwo jest kontrolowaną, lokalną perturbacją aktualnego rozwiązania.

*Przebieg algorytmu:* Pętla optymalizacyjna powtarza się przez zadaną liczbę iteracji:
+ ocena jakości wszystkich źródeł pożywienia
+ faza pszczół zatrudnionych — lokalne ulepszanie rozwiązań
+ faza pszczół obserwatorek — selekcja ruletkowa i dalsza eksploracja obiecujących źródeł
+ faza pszczół zwiadowców — zastępowanie rozwiązań, które przez dłuższy czas nie ulegają poprawie
+ aktualizacja najlepszego znalezionego rozwiązania

Po zakończeniu ostatniej iteracji zwracane jest najlepsze znalezione źródło pożywienia, czyli rozwiązanie o najniższej wartości $Z(s, X)$.

```text
Algorytm Pszczeli(instance, cfg):
  food_count <- liczba źródeł pożywienia
  foods <- losowe macierze X
  trials <- tablica zer o długości food_count

  oceń wszystkie foods
  zapamiętaj najlepsze rozwiązanie

  dla iteracji od 1 do iterations:
    # Pszczoły zatrudnione
    dla i od 1 do food_count:
      candidate <- sąsiedztwo foods[i] przez odwrócenie neighborhood_flips losowych bitów
      jeśli candidate jest lepsze od foods[i]:
        foods[i] <- candidate
        trials[i] <- 0
      inaczej:
        trials[i] <- trials[i] + 1

    # Pszczoły obserwatorki
    dla powtórzenia od 1 do food_count:
      i <- selekcja ruletkowa oparta na 1 / (1 + fitness[i])
      candidate <- sąsiedztwo foods[i] przez odwrócenie neighborhood_flips losowych bitów
      jeśli candidate jest lepsze od foods[i]:
        foods[i] <- candidate
        trials[i] <- 0
      inaczej:
        trials[i] <- trials[i] + 1

    # Pszczoły zwiadowcy
    dla i od 1 do food_count:
      jeśli trials[i] > limit:
        foods[i] <- nowe losowe rozwiązanie
        trials[i] <- 0

    zaktualizuj najlepsze rozwiązanie

  zwróć najlepsze rozwiązanie
```

= Interfejs
== Pliki i odpowiedzialności

| Plik | Odpowiedzialność |
|---|---|
| `src/model.py` | definicje instancji problemu, harmonogramu, oceny rozwiązań i kar |
| `src/ga.py` | implementacja algorytmu genetycznego |
| `src/bee.py` | implementacja algorytmu pszczelego |
| `run_experiments.py` | uruchamianie eksperymentów dla jednego grafu lub wielu konfiguracji |
| `run_pipeline.py` | jedno polecenie uruchamiające import, eksperymenty i wizualizację |
| `visualize.py` | budowa rysunków z plików `*_matrices.json` |
| `real_data_import.py` | historyczny skrypt importu danych OSM; logika importu została odwzorowana w `run_pipeline.py` |

== Wejścia i wyjścia

=== Wejścia

- `input_graph.json` - przykładowy graf do szybkich testów,
- `road_data.json` - surowy eksport OSM / Overpass,
- pliki konfiguracyjne w `configs/`.

=== Wyjścia

- `parsing_results.json` - graf przygotowany do solverów,
- `results/<out>.csv` - metryki końcowe,
- `results/<out>_matrices.json` - najlepsze rozwiązania, harmonogramy i overlap,
- `results/<out>_history.json` - przebieg fitnessu w kolejnych iteracjach/pokoleniach,
- `results/<out>_graf.png` - wizualizacja wygenerowana przez `visualize.py`.

== Konfiguracja eksperymentów

=== Pojedynczy scenariusz

`run_experiments.py` obsługuje klasyczne uruchomienie jednego grafu:

```powershell
python run_experiments.py --graph input_graph.json --repetitions 10 --iterations 120 --out single_graph_results.csv
```

=== Pliki konfiguracyjne algorytmów

Parametry GA można przechowywać w JSON, np. `configs/ga_config_example.json`.

Dostępne pola:

- `population_size`
- `generations`
- `crossover_rate`
- `mutation_rate`
- `tournament_size`
- `elite_count`
- `seed`

Parametry Bee można przechowywać w JSON, np. `configs/bee_config_example.json`.

Dostępne pola:

- `colony_size`
- `iterations`
- `limit`
- `neighborhood_flips`
- `seed`

=== Wiele konfiguracji w jednym pliku

`configs/runs_example.json` pokazuje format `runs-config`.
Każdy wpis może nadpisać:

- `graph`
- `repetitions`
- `iterations`
- `out`
- `ga_config`
- `bee_config`

Jeżeli w jednym pliku są dwie konfiguracje, uruchomienia są wykonywane sekwencyjnie: najpierw pierwszy wpis, potem drugi.

== Pipeline

Najprostszy wariant:

```powershell
python run_pipeline.py --road-data road_data.json --runs-config configs/runs_example.json
```

Domyślnie pipeline:

- zbuduje `parsing_results.json`,
- uruchomi eksperymenty,
- wygeneruje wizualizacje z `results/`.

Jeżeli chcesz pominąć któryś etap, możesz użyć:

- `--skip-import`
- `--skip-experiments`
- `--skip-visualize`

== Logika modelu

Wynik optymalizowany przez solver to makespan:

$$
Z(s, X) = \max\{s_e + t(e) \mid e \in E\}
$$

Model uwzględnia:

- koszt ekip liczony dziennie,
- ograniczenie budżetowe,
- twardą karę za nakładanie się prac tej samej ekipy,
- harmonogramowanie zadań według wagi `load * base_time`.

== Wizualizacja

`visualize.py` czyta wszystkie pliki `*_matrices.json` z katalogu `results/` i generuje obraz PNG dla każdego zestawu wyników.

Uruchomienie:

```powershell
python visualize.py
```
= Eksperymenty
Na obu algorytmach przeprowadziliśmy 10 eksperymentów mających sprawdzić działanie różnych zmiennych na wynik końcowy.

Na wszystkich wykresach punkty są średnią z 5 powtórzeń algorytmu dla różnych ziaren dla generatora liczb losowych.
== Algorytm Genetyczny

#figure(
  image("population_experiment_results.png", width: 80%),
  caption: [Wpływ wielu parametrów na wyniki]
) <gen_1>
Jak można zauważyć na @gen_1 najważniejszym parametrem jest częstotliwość mutacji. Jest też niezależne to od rozmiaru populacji. Natomiast parametr określający prawdopodobieństwo dziedziczenia wydaje się być nieznaczący, lecz najlepszy wynik dna niskich częstotliwości mutacji został osiągnięty dla $0,5$.

#figure(
  image("crossover_pop_ga.png", width: 70%),
  caption: [Zmiany w prawdopodobieństwie dziedziczenia i populacji]
) <gen_2>

W eksperymencie przedstawionym na @gen_2 głębiej sprawdziliśmy wpływ prawdopodobieństwa dziedziczenia oraz populacji na wynik ponieważ poprzedni eksperyment mało informacji na temat tych parametrów pokazał. Tutaj możemy już stwierdzić że prawdopodobieństwa dziedziczenia ma wpływ na nasz wynik oraz że jego optymalne wartości znajdują się w okolicy $0,8$. 

#figure(
  image("elite_count_ga.png", width: 60%),
  caption: [Zmiana w liczbie elit]
) <gen_3>

Następnym parametrem który był sprawdzany to liczba najlepszych rozwiązań przenoszonych bez krzyżowania do następnej generacji. Ten eksperyment był przeprowadzany na populacji 100 rozwiązań więc wartość na wykresie odpowiada procentowi w danych. Na @gen_3 widać że wyniki osiągnięte dla wartości poniżej $40$ buły dość stabilne jednak najlepsza osiągnięta wartość się pogarszała. Najlepsze wyniki ogólnie zostały osiągnięte dla wartości równej $10$.

#figure(
  image("tournament_size_ga.png", width: 60%),
  caption: [Zmiana w wielkości turnieju]
) <gen_4>

Na @gen_4 możemy zaobserwować krzywe podobną do @gen_3. Znowu widzimy że najlepsze wyniki osiągają dość małe wartości zmiennej i znowu najlepszy zakres wyników znajduje się w przedziale od $0$ do $20$.

#figure(
  image("mutation_ga.png", width: 60%),
  caption: [Zmiana częstości mutacji]
) <gen_5>

Widzimy na rysunku @gen_5 dane potwierdzające tezę z @gen_1, czyli fakt że bardzo duża częstotliwość mutacji prowadzi do najlepszych wyników. Dzieje się to prawdopodobnie przez fakt że mutacja potrafi zmienić rozwiązanie o wiele bardziej niż krzyżowanie przez co eksplorujemy większą część przestrzeni rozwiązań.

#figure(
  image("pop_ga.png", width: 60%),
  caption: [Zmiana rozmiaru populacji]
) <gen_6>

@gen_6 pokazuje że zwiększenie rozmiaru populacji może ulepszyć rozwiązanie do pewnego momentu. Dla rozmiarów większych od 1500 nie widać już tak pewnej korelacji jak dla rozmiarów poniżej.

== Algorytm Pszczeli

#figure(
  image("bee_polulation_results.png", width: 80%),
  caption: [Wpływ wielu parametrów na wyniki.],
) <bee_1>
Jak widać na @bee_1 najlepsze wyniki zostały osiągnięte dla dużych populacji, wysokich zmian sąsiadów i dużym ograniczeniu iteracji algorytmu. Potwierdza to nasze poprzednie spostrzeżenia.
Jenak można na tym wykresie zauważyć że niskie ograniczenie rekompensuje trochę niskie zmiany sąsiadów. 

#figure(
  image("flips_size_bee.png", width: 70%),
  caption: [Wpływ zmian sąsiadów oraz populacji na wynik przeprowadzony na większym zakresie.]
) <bee_2>

Na podstawie eksperymentu z @bee_1 postanowiliśmy przeprowadzić kolejny eksperyment który sprawdzi jednocześnie wpływ populacji i zmian sąsiadów dla większego zbioru danych. 
Każdy punkt to średnia pięciu powtórzeń eksperymentu. Jak widać na @bee_2 najlepsze wartości zostały osiągnięcie przy liczbie zmian sąsiadów równej $10$ i $20$.  Wysokie wartości bardzo pogorszyły wynik.

#figure(
  image("neighborhood_flips_bee.png", width: 60%),
  caption: [Zmiany sąsiadów sprawdzone gęsto na małym przedziale.]
) <bee_3>

Znowu bazując na poprzednim eksperymencie sprawdziliśmy zakres
między $0$ a $20$ parametru zmian. Tym razem mimo że punkty na wykresie są średnią 5 wyników algorytmu nasze punkty nie trzymają się żadnego trendu na takiej skali. Na rysunku nie widać niektórych punktów ponieważ nie zostało w nich znalezione rozwiązanie spełniające ograniczenia.

#figure(
  image("pop_bee.png", width: 60%),
  caption: [Zmiana rozmiaru populacji pszczół]
) <bee_4>

@bee_4 pokazuje że większa populacja potrafi polepszyć rozwiązanie lecz zyski z tego wydają się być coraz mniejsze z czasem.
= Podsumowanie
== Wnioski
Uważamy że udało się stworzyć efektywne rozwiązanie naszego problemu. Użytkownicy mogą łatwo pobrać dane i uruchomić badania na nich. Oba algorytmy rozwiązują problem bardzo dobrze, jednak z nich lepiej działa algorytm pszczeli. Za pomocą eksperymentów znaleźliśmy optymalne wartości parametrów dla naszych algorytmu. Twierdzimy że nasza praca zakończyła się sukcesem.
== Problemy
Prawdopodobnie największym problemem w tej pracy był fakt że rozpoczęliśmy pracę z niepoprawną funkcją kosztu. Minimalizowała ona sumę czasów wykonania każdej drogi. Model wtedy nie posiadał również ograniczenia budżetem więc najbardziej optymalne rozwiązaniem dla tej funkcji kosztu było przypisanie wszystkich ekip remontowych do każdej drogi. Na szczęście zaimplementowaliśmy algorytmy rozwiązujące nasz problem więc ten błąd logiczny został szybko naprawiony. Naprawiliśmy to zmieniając funkcję kosztu tak żeby minimalizować czas zakończenia ostatniej drogi. Kolejnym problemem było stare ograniczenie budżetowe. Polegało ono na tym że płaci się koszt ekipy raz i można jej używać bez ograniczeń. Zmieniliśmy to na obecne ograniczenie ponieważ gdy zakupiło się ekipę nie było powodu aby jej nie używać czyli do prostszych dróg na końcu pracowały by wszystkie ekipy.
= Podział pracy
#table(
  columns: 2,
  [Franciszek Kuś],[Model problemu, Import danych, Eksperymenty],
  [Marcel Duda],[Aplikacja, Implementacja algorytmów, Dokumentacja interfejsu],
  [Iwo Zowada],[Wizualizacja rozwiązań, Dokumentacja algorytmu genetycznego],
  [Tomasz Smołka],[Dokumentacja algorytmu pszczelego]
)