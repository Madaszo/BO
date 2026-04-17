#set text(lang: "PL")
#set page(
  numbering: "1"
)
#set math.equation(numbering: "(1)", supplement: none)

= Badania operacyjne - Problem remontu dróg
== Prezentacja problemu
Pewne miasto ma problem, wszystkie jego drogi znajdują się w fatalnym stanie i muszą zostać wymienione. Miasto jednak dysponuje ograniczoną ilością załóg remontowych. Jednocześnie chce żeby remonty były zakończone jak najszybciej i powodowały jak najmniej problemów dla mieszkańców.
== Wejścia
Wejściem do problemu jest graf reprezentujący siatkę drogową miasta:
$ G = (E, V) $
- Każda krawędź $e$ (droga) posiada wagę $t_s$ która oznacza podstawowy czas potrzebny na remont. Do każdej drogi można przydzielić dowolną liczbę ekip remontowych $n$. Wtedy czas remontu będzie wynosił:
$ t = ceil(2^(-n+1) * t_s) $
- Każda krawędź posiada wagę $d$ która oznacza obciążenie tej drogi.
#image("graf.png", width: 50%)
Kolejnym wejściem jest liczba ekip remontowych $r$. Każda ekipa remontowa posiada koszt $k_i$ który musimy ponieść jeśli korzystamy z jej usług. Mamy określony budżet $b$ którego nie możemy przekroczyć.
== Funkcja kosztu
$ Z(x_11, x_21, ... , x_(r 1), ..., x_(r |E|)) = sum_(e=0)^(|E|) d_e  dot ceil(2^(-(sum_(i=0)^r x_(i e))  + 1) * t_(s e)) -> "MIN" $
#pagebreak()
== Ograniczenia
$ 0<= x_(i e) <= 1, x_(i e) in NN $
$ sum_(i=0)^r x_(i e) >= 1 $
Zmienne $s$ określają początek pracy nad drogą $e$
$ s_(e) >= 0 $
$ s_(e) * (x_(i e) - 1) >= 0 $
$ s_(e') >= s_(e) + ceil(2^(-(sum_(i=0)^r x_(i e))  + 1) * t_(s e)) * x_(i e)  $
$ b <= sum_(i=0)^k "sign"(sum_(e=0)^(|E|)x_(e i))*k_i  $