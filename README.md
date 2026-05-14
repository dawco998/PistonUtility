# PistonUtility
Program for ECU tuners for complex calculations.


tasks:
1. Synchronizacja Symulatora z MAPY ORI bez logow, oraz MAPY MOD ktore sa spojne z logami forscan. Mozlwosc przelaczania map w symulatorze dla analizy.
2. Dodanie automatycznego convertera dawek do nm na suwaku dawki korzystajac z NM to IQ map (widocznosc jaka wartosc nm z mapy nm to iq wskazuje dana dawka)
3. Pokazywanie AirfuelRatio, Warning po przekroczeniu lambda 1.14
4. Sprawdzenie modelu calej fizyki, funkcja Wiebego, Zmienne właściwości gazu z uwzgledniejem skladu mieszanki, wlasciwosci i dynamika wtryskiwacza  i w razie bledow poprawa.

       Cecha	Specyfikacja
Typ wtryskiwacza	Elektromagnetyczny (solenoidowy) Common Rail
Numer katalogowy Bosch	0 445 110 259 (często zapisywany jako 0445110259)
Numer części zamiennej	0 986 435 126, BX-CRI2
Seria Bosch	CRI2.1
Maks. ciśnienie pracy	1600 barów
Napięcie sterujące	80 V (standard dla CRI2)
Rezystancja cewki	0.8 Ω (wartość kluczowa dla diagnostyki)
Typ dyszy	DLLA149P1515 (numer seryjny Bosch: 0433171936)
Konstrukcja dyszy	6- lub 7-otworowa, symetryczna
Średnica otworów	0.12 – 0.16 mm (dokładny rozmiar zależy od kalibracji przepływu)
informacje nie klarowne wywnioskuj sam korzystajac z przebiegu map i mocy fabrycznej ~109hp
