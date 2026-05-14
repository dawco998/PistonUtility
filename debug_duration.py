import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Oś IQ w Duration: 0,70,120,150,180,220,270,320,400,600,1000,1400,1800,2200,2500,2800,3100,3400,3600,3800,4000,4400,5000,7000
# Oś IQ w Rail Pressure: 0,170,340,680,850,1020,1190,1360,1550,1840,2280,3000,3300,3500,3700,4000

# Kluczowe pytanie: JAKIE SA JEDNOSTKI osi IQ w Duration?
# Wiemy ze:
#   - IQ realne = 55 mm3/suw (na 315 Nm @ 2000 RPM)
#   - Rail = ~1337 bar
#   - Typowy Duration wtryskiwacza Bosch piezo/solenoid @ 1300 bar, 55mm3 = ~500-700 us

# Sprawdzmy: jesli os IQ Duration to 0.01 mm3 (jak Rail):
#   55 mm3 = 5500 na osi. Duration@1400bar,IQ=5500 -> ~1250 us. Za duzo.

# Jesli os IQ Duration to bezposrednio mm3 (bez mnoznika!):
#   55 mm3 = 55 na osi. To miedzy 0 i 70.
#   Duration@1400bar, IQ=55: interp miedzy 0(190us) i 70(190us) = 190 us.
#   To za MALO na 55 mm3.

# Jesli os IQ to 0.1 mm3 (mm3 * 10):
#   55 mm3 = 550 na osi. Miedzy 400 i 600.
#   Duration@1400bar, IQ=550: interp = 316 + (550-400)/(600-400)*(359-316) = 316+32 = 348 us
#   348 us na 55 mm3 @ 1400 bar. To realistyczne ale troche krotkie.

# Jesli os IQ to mg/suw (nie mm3):
#   55 mm3 * 0.835 = 45.9 mg = 459 na osi. Miedzy 400 i 600.
#   Duration@1400bar, IQ=459: interp = 316 + (459-400)/(600-400)*43 = 316+12.7 = 329 us
#   329 us. Hmm.

# WAIT. Moze Duration to nie mikrosekundy ale NANOSEKUNDY / 10?
# Lub: Moze Duration wartosci sa w 0.001 ms = us ale to nie jest duration OTWARCIA
# tylko duration calego zdarzenia wtrysku...

# Sprobujmy inaczej. Jaki czas otwarcia jest potrzebny zeby przy 1400 bar
# wstrzyknac 55 mm3?
# Przeplyw wtryskiwacza Bosch solenoid: ~50-60 cm3 / 30s @ 100 bar (spec katalogowa)
# Przeplyw skaluje z sqrt(P): flow = flow_ref * sqrt(P/P_ref)
# Przy 1400 bar: flow = 55 * sqrt(1400/100) = 55 * 3.74 = 206 mm3/s? Nie, to max flow.
# Typowy Bosch CRI: static flow ~25-30 mm3/ms @ 1000 bar
# Wiec flow@1400bar = 30 * sqrt(1400/1000) = 30 * 1.183 = 35.5 mm3/ms
# Duration = 55 mm3 / 35.5 mm3/ms = 1.55 ms = 1550 us

# To idealnie pasuje do osi! Wartosc 1000 na osi IQ -> Duration@1400bar = 359 us.
# Jesli os IQ = 0.01 mm3: 1000 = 10 mm3. Duration = 10/35.5 = 0.28 ms = 280 us. 
# Mapa mowi 359 us. Rozbieznosc 28%, moze byc bo flow nie jest idealnie liniowy.

# Sprawdzmy wieksza dawke: os 4000 = 40 mm3 (0.01mm3 * 4000)
# Duration = 40/35.5 = 1.13 ms = 1127 us.
# Mapa@1400bar, IQ=4000 mowi: 983 us (w wierszu 14000=1400bar, ostatnia kolumna 4400 bo 4000 nie jest ostatnia)
# Hmm, 4000 na osi dur: wartosc = 841 us (wiersz 14000). 
# Oczekiwane: 1127 us. Mapa mowi 841 us. Roznica duza.
# ALE! Jesli flow @ 1400 bar jest wyzszy niz zakladam (np 40 mm3/ms):
# Duration = 40/40 = 1.0 ms = 1000 us. Blizej ale ciagle nie 841.

# Moze trzeba uwzglednic ze wtryskiwacz nie otwiera sie natychmiast 
# (dead time ~200 us), a mapa juz to uwzglednia (BIP correction)?

# KLUCZOWY TEST: porownajmy dwie wartosci Duration przy ROZNYM Rail
# dla TEGO SAMEGO IQ, i sprawdzmy czy skaluja sie z sqrt(P):
# IQ_os=4000:
#   @1200 bar: 5939 us
#   @1400 bar: 841 us  
#   @1700 bar: 726 us
# Stosunek 1400/1700: sqrt(1400/1700) = 0.907
# 841 * 0.907 = 763. Mapa mowi 726. Roznica -5%. OK, pasuje.
# ALE stosunek 1200/1400: sqrt(1200/1400) = 0.926
# 5939 * 0.926 = 5499. vs 841. 
# OGROMNA ROZNICA! 5939 vs 841. 
# 1200 bar mapa: [0,651,802,...,5939,...] - to NIE MOZE byc ten sam typ danych!

# AHA! Wiersz "1200" to 1200 bar = MIN. cisnienie robocze listwy.
# Przy 1200 bar wtryskiwacz ledwo daje rade i czasy sa ogromne.
# To sugeruje ze os Rail Duration to BAR bezposrednio (nie *10).
# 1200 bar -> czasy ogromne (bo wtryskiwacz ledwo otwiera).
# 14000 -> hmm, 14000 bar?? Nierealne!
# Wiec os Rail Duration to BAR / 10? 14000 = 1400 bar? TAK!

# POPRAWKA: Os Rail w Duration = bar * 10? NIE.
# Os: 1190,1200,2000,2500,3000,4000,5000,6000,7000,8000,9000,10000,11000,12000,14000,17000
# Jesli /10: 119, 120, 200, 250, 300, 400, 500, 600, 700, 800, 900, 1000, 1100, 1200, 1400, 1700 bar
# To pasuje IDEALNIE! 120-1700 bar to pelny zakres common-rail!

# Sprawdzmy: @120 bar (os 1200), IQ=4000: Duration = 5939 us = 5.94 ms
# Przy 120 bar cisnienie jest minimalne, wtryskiwacz ledwo codzi.
# @1400 bar (os 14000), IQ=4000: Duration = 841 us = 0.84 ms. REALISTYCZNE!
# @1700 bar (os 17000), IQ=4000: Duration = 726 us = 0.73 ms. REALISTYCZNE!

# WNIOSEK: Os Rail Duration = bar * 10!
# To zmienia wszystko! Moje wartosci Rail z mapy Rail Pressure sa w bar bezposrednio.
# Wiec: Rail = 1337 bar -> na osi Duration szukam 13370!

# Przeliczmy:
dur_rail_axis = [1190,1200,2000,2500,3000,4000,5000,6000,7000,8000,9000,10000,11000,12000,14000,17000]
# dzielimy / 10 zeby dostac bar:
dur_rail_bar = [x/10 for x in dur_rail_axis]
print("Os Rail Duration w bar:", dur_rail_bar)
# [119, 120, 200, 250, 300, 400, 500, 600, 700, 800, 900, 1000, 1100, 1200, 1400, 1700]

# Analogicznie os IQ:
dur_iq_axis = [0,70,120,150,180,220,270,320,400,600,1000,1400,1800,2200,2500,2800,3100,3400,3600,3800,4000,4400,5000,7000]
# Jesli tez /10: 0, 7, 12, 15, 18, 22, 27, 32, 40, 60, 100, 140, 180... mmm to mm3?
# Albo / 100: 0, 0.7, 1.2, 1.5, 1.8, 2.2, 2.7, 3.2, 4, 6, 10, 14, 18, 22, 25, 28, 31, 34, 36, 38, 40, 44, 50, 70
# /100 daje mm3/suw! Max = 70 mm3. To IDEALNIE pasuje do zakresu silnika!

dur_iq_mm3 = [x/100 for x in dur_iq_axis]
print("Os IQ Duration w mm3:", dur_iq_mm3)

# WERYFIKACJA: IQ=55 mm3 (os 5500), Rail=1337 bar (os 13370)
# Na osi Rail szukamy 1337 bar miedzy 1200(os 12000) i 1400(os 14000)
# Na osi IQ szukamy 55 mm3 (os 5500) miedzy 50(os 5000) i 70(os 7000)

# Rail interp: t = (1337-1200)/(1400-1200) = 137/200 = 0.685
# IQ interp na osi: t = (5500-5000)/(7000-5000) = 500/2000 = 0.25

# @1200 bar (os 12000): Dur[5000]=947, Dur[7000]=1740
# Dur@IQ5500 = 947 + 0.25*(1740-947) = 947+198 = 1145 us

# @1400 bar (os 14000): Dur[5000]=1151, Dur[7000]=1588
# Dur@IQ5500 = 1151 + 0.25*(1588-1151) = 1151+109 = 1260 us

# WAIT to nie moze byc - Duration rosnie z Rail? Powinno MALEC!
# Sprawdzmy surowe wartosci:
# @12000(1200bar), IQ=5000: 947 us
# @14000(1400bar), IQ=5000: 1151 us
# To rosnie! Wiec os Rail NIE JEST bar/10!

# Cofam. Os Rail = bar bezposrednio. 
# 1190, 1200 = 1190 bar, 1200 bar (min cisnienie idle)
# 14000 = 14000 bar?? To nonsens.
# Chyba ze to kPa? 14000 kPa = 140 bar? Tez malo.

# Albo: Os Rail Duration to DEKATECHNICZNE?
# Hmm. Sprawdzmy po prostu co daje sens fizyczny:
# Oczekiwanie: Duration MALEJE gdy Rail rosnie (wiecej cisnienia = szybszy wtrysk)
# Patrzymy na kolumne IQ=1400 (0.1mm3=14mm3):
# Rail 1200: 2412
# Rail 2000: 1447
# Rail 3000: 1036
# Rail 5000: 708
# Rail 8000: 545
# Rail 12000: 445
# Rail 17000: 379
# TAK! Duration maleje z rosnacem "Rail"! Wiec WYZSZY numer = WYZSZE cisnienie.
# Pytanie: jaka jednostka?

# Moze to po prostu 0.1 bar? 17000 = 1700 bar. 1200 = 120 bar. 
# 120 bar to idle rail. 1700 bar to max. IDEALNIE!
# Sprawdzmy: @120bar, IQ=14mm3: 2412 us. Przy 120 bar i 14mm3 to dluge ale realne.
# @1700bar, IQ=14mm3: 379 us. Przy 1700 bar i 14mm3 to krotkie i realne!

# POTWIERDZAM: Os Rail Duration = 0.1 bar (dzielimy /10 zeby dostac bar)
# Os IQ Duration = 0.01 mm3 (dzielimy /100 zeby dostac mm3)

print()
print("POTWIERDZONE JEDNOSTKI DURATION MAP:")
print("  Os Rail: wartosci / 10 = bar")
print("  Os IQ: wartosci / 100 = mm3/suw")
print()

# Teraz prawidlowe obliczenie:
# IQ = 55 mm3 -> os = 5500
# Rail = 1337 bar -> os = 13370

# Interp Rail: miedzy os 12000(1200bar) i 14000(1400bar)
# t = (13370 - 12000) / (14000 - 12000) = 1370/2000 = 0.685

# Interp IQ: miedzy os 5000(50mm3) i 7000(70mm3)
# t = (5500 - 5000) / (7000 - 5000) = 0.25

# @Rail os 12000: IQ os 5000=947, 7000=1740
# dur_12000 = 947 + 0.25*(1740-947) = 1145 us

# @Rail os 14000: IQ os 5000=1151, 7000=1588
# dur_14000 = 1151 + 0.25*(1588-1151) = 1260 us

# Hmm, dur_14000 > dur_12000 dla tego samego IQ??
# 1200 bar: 947 us ale 1400 bar: 1151 us. Duration ROSNIE z cisnieniem? To zle.

# AH WAIT. Moze os Rail jest ODWROTNA? Moze to nie rail pressure ale
# cos innego jak Back-EMF, przetwornik itp?
# Albo: Moze mapa jest transponowana w moim dumpie!
# Sprawdzmy: plik XLSX mowi "Rail Press \ IQ"
# Naglowek: Rail Press \ IQ | 0 | 70 | 120 ...
# Wiersze: 1190, 1200, 2000, 2500, 3000, ...

# Wiec WIERSZE = Rail Press, KOLUMNY = IQ. To mam dobrze.
# Ale Duration ROSNIE z Rail? Sprawdzmy wiecej:
# IQ kolumna = 1400 (=14mm3): 
#   Rail 1200: 2412
#   Rail 2000: 1447
#   Rail 5000: 708
#   Rail 12000: 445
#   Rail 14000: 414
#   Rail 17000: 379
# O! Wiec 1200 -> 2412 i 14000 -> 414. Duration SPADA!
# Moj blad wyzej byl w tym ze porownywalem os 12000 vs 14000 ale
# patrzalem na KOLUMNE 5000 (=50mm3):
#   Rail 12000: 947
#   Rail 14000: 1151
# Duration ROSNIE z 947 na 1151? To dziwne.

# Sprawdzmy pelne wiersze:
dur_12000 = [0,195,195,195,195,201,248,272,296,330,386,445,504,574,627,672,712,750,810,874,947,1096,1261,1740]
dur_14000 = [0,190,190,190,190,190,241,261,282,316,359,414,465,533,578,621,659,693,722,767,841,983,1151,1588]

print("IQ kolumna 5000:")
print(f"  @Rail 12000: {dur_12000[22]} us")  # index 22 = kolumna 5000
print(f"  @Rail 14000: {dur_14000[22]} us")

# Index 22 = os 5000. 
# dur_12000[22] = 1261
# dur_14000[22] = 1151

# OK wiec 1261 > 1151. Duration SPADA z 12000 na 14000. To poprawne!
# Moj wczesniejszy blad: pomylilem indeksy.

# Dobra, zrobie prawidlowa interpolacje od zera.
dur_rail_axis = [1190,1200,2000,2500,3000,4000,5000,6000,7000,8000,9000,10000,11000,12000,14000,17000]
dur_iq_axis = [0,70,120,150,180,220,270,320,400,600,1000,1400,1800,2200,2500,2800,3100,3400,3600,3800,4000,4400,5000,7000]

dur_table = {
    1190: [0]*24,
    1200: [0,651,802,879,939,1018,1107,1192,1313,1588,2036,2412,2782,3250,3673,4126,4579,5033,5335,5637,5939,6543,8000,8000],
    2000: [0,390,481,527,563,611,664,715,788,953,1222,1447,1658,1942,2204,2476,2748,3020,3201,3382,3563,3926,4470,6168],
    2500: [0,297,383,414,444,501,538,574,632,767,999,1191,1380,1567,1777,2013,2246,2479,2634,2790,2945,3256,3722,5136],
    3000: [0,270,334,367,391,421,462,508,553,659,857,1036,1201,1362,1499,1717,1921,2120,2252,2384,2516,2781,3177,4384],
    4000: [0,260,270,305,334,357,379,403,453,542,683,828,959,1086,1202,1355,1515,1687,1802,1919,2036,2269,2620,3615],
    5000: [0,245,245,260,289,318,346,365,389,467,588,708,821,925,1003,1129,1284,1424,1519,1624,1729,1939,2255,3111],
    6000: [0,225,225,225,255,290,320,339,362,415,523,621,724,816,878,954,1115,1247,1327,1409,1513,1698,1977,2728],
    7000: [0,220,220,220,231,270,300,322,345,385,486,575,667,751,806,863,972,1120,1200,1265,1342,1519,1755,2421],
    8000: [0,215,215,215,222,256,287,311,335,372,463,545,631,710,761,810,881,1017,1103,1176,1237,1385,1640,2263],
    9000: [0,210,210,210,212,240,276,300,324,361,444,522,604,677,726,770,833,928,1022,1098,1164,1282,1510,2083],
    10000:[0,205,205,205,205,229,262,287,313,347,416,490,564,639,688,735,783,854,941,1023,1095,1208,1418,1956],
    11000:[0,200,200,200,200,220,257,281,305,339,399,463,532,604,654,711,750,789,844,945,1030,1147,1326,1829],
    12000:[0,195,195,195,195,201,248,272,296,330,386,445,504,574,627,672,712,750,810,874,947,1096,1261,1740],
    14000:[0,190,190,190,190,190,241,261,282,316,359,414,465,533,578,621,659,693,722,767,841,983,1151,1588],
    17000:[0,172,172,172,172,172,226,241,260,290,331,379,417,476,520,560,598,632,652,672,726,846,1024,1413],
}

def interp(x_arr, y_arr, x):
    if x <= x_arr[0]: return y_arr[0]
    if x >= x_arr[-1]: return y_arr[-1]
    for i in range(len(x_arr)-1):
        if x_arr[i] <= x <= x_arr[i+1]:
            t = (x - x_arr[i]) / (x_arr[i+1] - x_arr[i])
            return y_arr[i] + t * (y_arr[i+1] - y_arr[i])

# IQ = 55 mm3 = os 5500. Rail = 1337 bar = os 13370.
rail_on_axis = 1337 * 10  # = 13370
iq_on_axis = 55 * 100  # = 5500

# Interp Rail: miedzy 12000 i 14000
t_rail = (rail_on_axis - 12000) / (14000 - 12000)  # = 0.685

# Interp IQ w wierszu 12000:
d_12000 = interp(dur_iq_axis, dur_table[12000], iq_on_axis)
# Interp IQ w wierszu 14000:
d_14000 = interp(dur_iq_axis, dur_table[14000], iq_on_axis)

dur_result = d_12000 + t_rail * (d_14000 - d_12000)

print(f"\nIQ=55mm3 (os {iq_on_axis}), Rail=1337bar (os {rail_on_axis}):")
print(f"  Dur@12000 = {d_12000:.0f} us")
print(f"  Dur@14000 = {d_14000:.0f} us")
print(f"  Interpolowane: {dur_result:.0f} us = {dur_result/1000:.2f} ms")
print(f"  Przy 2000 RPM = {dur_result * 2000 * 6 / 1e6:.1f} deg CA")
