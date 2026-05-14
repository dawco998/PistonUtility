import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Sprawdzam skale osi NM_TO_IQ
# Kolumny (NM axis): 0, 100, 200, 350, 500, 750, 1000, 1250, 1500, 1750, 2000, 2250, 2500, 2750, 3000, 3500
# Wiersze (RPM axis): 250, 500, 750, 1000, ...

# Przy RPM=2000, NM=2500 (kolumna), IQ = 41.64
# Przy RPM=2000, NM=3000 (kolumna), IQ = 55.0
# Przy RPM=2000, NM=3500 (kolumna), IQ = 64.8

# 55 mg na 3000... czego? Jesli NM axis = NM/10, to 3000 = 300 Nm
# Wtedy: 300 Nm -> 55 mg. To idealnie pasuje!
# 350 Nm -> 64.8 mg. Tez idealnie!
# 250 Nm -> 41.64 mg. Tez OK!

# WNIOSEK: Os NM w mapie NM_TO_IQ jest w NM * 10!

# Sprawdzmy Rail Pressure: os mg/str: 0, 170, 340, 680, 850, 1020, 1190, 1360, 1550, 1840, 2280, 3000, 3300, 3500, 3700, 4000
# Jesli IQ (mg/suw) = 55, to na osi Rail szukamy 55... ale os zaczyna sie od 0,170,340...
# Zatem os Rail to IQ * pewien mnoznik
# 55 mg/suw. Gestosc ON = 0.835 g/cm3. 55mg / 0.835 = 65.87 mm3/suw
# Ale os zaczyna od 170... Moze os jest w 0.01 mm3? 65.87 * 100 = 6587? Za duzo.
# Albo IQ w mapie Rail jest w 0.01 mg? 55*100=5500? Nie.
# Moze os Rail to po prostu "IQ" ale w tej samej skali co wartosci IQ (mg/suw)?
# Wtedy przy IQ=55, interpolujemy miedzy 0 i 170... ale to daje Rail ~ 420 bar. Za malo.
# 
# Hmm, a moze os Rail jest w ug/suw (mikrogramow)? 55 mg = 55000 ug. Za duzo.
# A moze Duration IQ axis tez jest w * 10? 
# Duration IQ axis: 0,70,120,150,180,220,270,320,400,600,1000,1400,1800,2200,2500,2800,3100,3400,3600,3800,4000,4400,5000,7000
# Jesli / 10: 0, 7, 12, 15, 18, 22, 27, 32, 40, 60, 100...
# Przy 55 mg -> szukamy 550 na osi. To by padlo miedzy 400 i 600. Duration ~ 300-360 us. 
# Hmm, moze os jest w 0.1 mg? Wiec 55 mg = 550 na osi. To pasuje!

# Podsumowanie skal:
# NM_TO_IQ: Os NM = NM * 10. Wartosci IQ = mg/suw (bezposrednio).
# Rail Pressure: Os IQ = 0.1 mg/suw (wiec 55 mg = 550 na osi). Wartosci = bar.
# Duration: Os IQ = 0.1 mg/suw. Os Rail = bar (bez mnoznika, 1700 = 1700 bar).

# Weryfikacja Rail:
# RPM=2000, IQ=55 mg (= 550 na osi Rail). 
# Os: ...340, 680... 550 jest miedzy 340 a 680.
# t = (550-340)/(680-340) = 210/340 = 0.617
# Wartosci: 493 + 0.617*(592-493) = 493 + 61 = 554 bar. Brzmi rozsadnie!
# Ale przy 1700 RPM i 310 Nm chcemy wiecej niz 554 bar...
# Sprawdzmy 2000 RPM, IQ=55, kolumna 550: 
# Rail = 554 bar. Hmm, to ciagle malo, docelowo chcemy 900-1100 bar...
# 
# Moze jednostki Rail to jednak 0.1 mg/suw ale z inna skala?
# Albo os Rail to mg/suw * 10? Wiec 55 mg = 550.
# Hmm to samo co 0.1 mg.

# Sprawdzmy inaczej. Log mowi: FRP = 128820 kPa = 1288 bar przy RPM 1930.
# Z logu: torque = 292 Nm. NM_TO_IQ: RPM=2000, NM=2920 (na osi *10) -> IQ ~ 53.8 mg.
# Na osi Rail: 53.8 mg -> 538 (jezeli os * 10). 
# RPM 2000 row: os ...340(493), 680(592)... 
# t = (538-340)/(680-340) = 0.582
# Rail = 493 + 0.582*(592-493) = 493+57.6 = 551 bar
# Ale log mowi 1288 bar! Wiec IQ musi byc wyzsze na osi.

# Moze os NM w NM_TO_IQ NIE jest *10 ale bezposrednio NM?
# Wtedy RPM=2000, NM=292: interpolacja miedzy 200(3.24) i 350(5.5)
# t=(292-200)/(350-200) = 0.613, IQ = 3.24+0.613*(5.5-3.24) = 3.24+1.38 = 4.63 mg
# 4.63 mg? To absurdalnie malo.

# Wrocmy do NM*10 i sprawdzmy czy os Rail to cos innego.
# IQ = 53.8 mg/suw. Moze os Rail to mm3/suw?
# 53.8 mg / 0.835 (gestosc) = 64.4 mm3
# Os Rail: ...340... 680... Nadal za malo.
# Moze os to mm3/suw * 10? 64.4 * 10 = 644. Miedzy 340 i 680.
# Rail RPM=2000: 493 + (644-340)/(680-340) * (592-493) = 493 + 0.894*99 = 581 bar.
# Ciagle za malo vs 1288 bar z logu.

# AHA! Moze os Rail to mm3/MIN lub mg/MIN (calkowita dawka na minute)?
# Przy 2000 RPM, 4-cylindrowy, 4-suw: 1000 wtryskow/min
# 53.8 mg/suw * 1000 = 53800 mg/min. Za duzo.
# mm3/min: 64.4 * 1000 = 64400. Za duzo.

# Moze os Rail: 0, 170, 340, 680, 850, 1020, 1190, 1360, 1550, 1840, 2280, 3000, 3300, 3500, 3700, 4000
# to po prostu IQ ale w roznych jednostkach...
# Przy 1288 bar z logu i RPM=2000, szukamy na osi Rail:
# RPM=2000 row: 402, 450, 493, 592, 647, 723, 770, 856, 881, 916, 958, 944, 988, 1064, 1120, 1337
# 1288 bar jest miedzy 1120(3700) i 1337(4000).
# t=(1288-1120)/(1337-1120) = 168/217 = 0.774
# IQ na osi = 3700 + 0.774*(4000-3700) = 3700+232 = 3932
# Wiec IQ na osi Rail = ~3932 kiedy mamy 53.8 mg/suw
# 3932 / 53.8 = 73.1. Mnoznik ~ 73?!
# Hmm, to nie wyglada na ladna liczbe...

# Sprawdzmy stock: 109 KM, ~230 Nm peak. 
# RPM=2000, NM=2300 -> IQ miedzy 2000(33.59) i 2250(37.24)
# t = (2300-2000)/(2250-2000) = 1.2 -> ekstrapolacja: 33.59+1.2*(37.24-33.59)=33.59+4.38 = 37.97 mg
# Stock Rail przy 2000 RPM i 37.97 mg:
# 37.97 mg -> mm3 = 37.97/0.835 = 45.5 mm3
# Moze os jest w 0.01 mm3? 45.5*100 = 4550? Za duzo.
# Hmm. Moze IQ map NM_TO_IQ jest w mm3/suw a nie mg/suw?
# 37.97 mm3 * 0.835 = 31.7 mg. Troche malo na 230 Nm...

# Dobra, czysty test. W ECU Bosch EDC16C3, IQ jest standardowo w mm3/suw (hub).
# Nm to IQ map: os NM jest w 0.1 Nm lub Nm/10.
# Wartosci IQ sa w mm3/suw.
# Os Rail pressure: jest tez w mm3/suw * 100? 

# Zakladam: NM_TO_IQ: os NM = Nm * 10. IQ = mm3/suw.
# Rail: os = mm3/suw * 100? Nie...

# Os Rail: 0, 170, 340, 680, 850, 1020, 1190, 1360, 1550, 1840, 2280, 3000...
# IQ typowe: 30-60 mm3/suw
# 55 mm3 * ? = 1840? -> mnoznik ~33. Nie ladne.
# 55 mm3 * 10 = 550. Miedzy 340 i 680.

# Inny pomysl: os Rail to mg/suw * 10?
# IQ = 55 mm3 * 0.835 = 45.9 mg. * 10 = 459. Miedzy 340 i 680.
# RPM=2000: 493 + (459-340)/(680-340)*99 = 493+34.6 = 528 bar. Nadal za malo.

# OK moze os Rail to CALKIEM co innego. Moze to nie IQ tylko cos innego.
# Naglowek: "rpm \ mg/str"
# mg/str = mg per stroke!
# Wiec os to mg/suw, i wartosci to 0, 170, 340, 680... mg/suw?!
# To oznaczaloby ze wtryskuja 680 mg paliwa na suw? Niemozliwe.

# CHYBA ZE... os to mg/stroke ale * 0.01 (czyli setne mg)
# 0, 1.7, 3.4, 6.8, 8.5, 10.2, 11.9, 13.6, 15.5, 18.4, 22.8, 30, 33, 35, 37, 40
# To sa TYPOWE dawki w mm3/suw!!! 
# OS RAIL = mm3/suw * 100! (lub mg/suw / 10 zalezy jak patrzec)

# Wiec os Rail nalezy dzielic przez 100 zeby dostac mm3/suw!
# 0, 1.7, 3.4, 6.8, 8.5, 10.2, 11.9, 13.6, 15.5, 18.4, 22.8, 30, 33, 35, 37, 40 mm3/suw

# NM_TO_IQ daje IQ w mm3/suw
# Przy RPM=2000, NM=2920 (292 Nm *10): IQ ~ 53.8 mm3/suw
# Os Rail / 100: max = 40 mm3/suw. ALE 53.8 > 40!
# Wiec mapa Rail POTRZEBUJE rozszerzenia!

# Sprawdzmy: przy IQ=40 mm3 (max osi), RPM=2000:
# Rail = 1337 bar (ostatnia wartosc w wierszu 2000).
# Log mowi 1288 bar przy torque 292. IQ ~ 53.8 mm3.
# Wiec IQ przekracza mape Rail! To jest PROBLEM.

# Hmm ale czekaj, uzytkownik mowil ze rozszerzal mapy...
# Moze os jest w 0.01 mm3 (1/100 mm3)?
# 0, 1.70, 3.40, 6.80, 8.50, 10.20, 11.90, 13.60, 15.50, 18.40, 22.80, 30.00, 33.00, 35.00, 37.00, 40.00
# Dla stock 109KM (max ~23 Nm*10 IQ ~ 25 mm3) to by pasowalo.
# Ale on rozszerzyl do 40 mm3, co przy gęstości 0.835 = ~33.4 mg, generuje ~230Nm stock.
# Hmm ale on chce 315 Nm, wiec IQ musi byc wyzsze.

# WAIT. Moze skala NM w mapie NM_TO_IQ NIE jest *10!
# Sprawdzmy surowo: RPM=2000, kolumna NM=3500, IQ=64.8
# Jesli NM os jest bezposrednio w Nm: 3500 Nm? Absurd dla 1.6L.
# Jesli NM * 10: 350 Nm. Mozliwe (po tuningu).
# Jesli NM * 0.1: 350 Nm. To to samo.

# OK, os NM to Nm/10 * 100 = Nm * 10? Nie, to 0,100,200,350...
# Jesli os to Nm * 10: 0, 10, 20, 35, 50, 75, 100, 125, 150, 175, 200, 225, 250, 275, 300, 350 Nm
# Przy 300 Nm IQ = 55.0 mm3. Przy 350 Nm IQ = 64.8 mm3. TO IDEALNIE PASUJE!

# Weryfikacja: Stock Mazda 1.6 MZ-CD (109KM) max torque ~230 Nm @ 1750 RPM
# 230 Nm = os 2300. RPM=1750: IQ miedzy kolumnami 2250(38.97) i 2500(43.68)
# t = (2300-2250)/(2500-2250) = 0.2
# IQ = 38.97 + 0.2*(43.68-38.97) = 38.97+0.94 = 39.9 mm3/suw
# 39.9 mm3 * 0.835 = 33.3 mg. Na stock diesel 1.6L 230Nm to jest realistyczne!

# A Rail? Os Rail / 100 = mm3/suw. 39.9 mm3 = os 3990 (~4000). RPM=1750: Rail=1225 bar.
# Stock Mazda przy WOT 1750 RPM: ~1200 bar. PERFEKCYJNIE PASUJE!

# Wiec podsumowanie KLUCZOWE:
# NM_TO_IQ: os NM = Nm * 10. Wartosci = mm3/suw.
# Rail: os IQ = mm3/suw * 100 (0.01 mm3/suw). Wartosci = bar.
# Duration: os IQ = mm3/suw * 100. Os Rail = bar (bezposrednio).

print("WYNIK ANALIZY JEDNOSTEK:")
print("========================")
print()
print("NM_TO_IQ:")
print("  Os X (RPM): rpm (bezposrednio)")
print("  Os Y (NM):  Nm * 10 (tzn. 3000 = 300 Nm)")
print("  Wartosci:   mm3/suw (objętosciowa dawka paliwa)")
print()
print("Rail Pressure Map:")
print("  Os X (RPM): rpm (bezposrednio)")
print("  Os Y (mg/str): mm3/suw * 100 (tzn. 4000 = 40 mm3/suw)")
print("  Wartosci:   bar (cisnienie rail)")
print()
print("Duration Map:")
print("  Os X (Rail Press): bar (bezposrednio, 17000 = 1700 bar)")  
print("  WAIT - Rail axis: 1190,1200,2000,...,17000")
print("  Jesli bezposrednio bar: 1190 bar, 1200 bar... to nie ma sensu bo sa dwa wpisy bliskie")
print("  1190 to raczej tez * 0.1? 119 bar? Za malo.")
print("  Rail axis: bar/10? 1190=119bar? Za malo. Nie.")
print("  Rail axis = bar bezposrednio: 1190, 1200 -> hmm, 1190 to min (idle) a 1200 to pierwszy sensowny.")
print("  TAK - to bar bezposrednio. 1190 bar to minimum (wiersz samych zer).")
print()
print("  Os Y (IQ): mm3/suw * 100 (tzn. 3400 = 34 mm3/suw)")
print("  Wartosci: mikrosekundy (czas otwarcia wtryskiwacza)")
print()
print("NM Limiter:")
print("  Os: RPM")
print("  Wartosci: Nm (bezposrednio)")

print()
print("=== WERYFIKACJA Z LOGIEM ===")
print()

# Test: RPM=1930, Torque=292 Nm, FRP=128820 kPa = 1288 bar
# NM_TO_IQ: RPM=2000, NM=2920 -> interpolacja
# Kolumna 2750: IQ=48.48, Kolumna 3000: IQ=55.0
# t = (2920-2750)/(3000-2750) = 170/250 = 0.68
# IQ = 48.48 + 0.68*(55-48.48) = 48.48 + 4.43 = 52.91 mm3/suw
nm_axis = [0,100,200,350,500,750,1000,1250,1500,1750,2000,2250,2500,2750,3000,3500]
iq_2000 = [0,2.02,3.24,5.5,7.8,12.1,15.74,20,24.3,28.94,33.59,37.24,41.64,48.48,55,64.8]

def interp(x_arr, y_arr, x):
    if x <= x_arr[0]: return y_arr[0]
    if x >= x_arr[-1]: return y_arr[-1]
    for i in range(len(x_arr)-1):
        if x_arr[i] <= x <= x_arr[i+1]:
            t = (x - x_arr[i]) / (x_arr[i+1] - x_arr[i])
            return y_arr[i] + t * (y_arr[i+1] - y_arr[i])

iq_test = interp(nm_axis, iq_2000, 2920)
print(f"RPM=2000, Torque=292 Nm (os=2920):")
print(f"  IQ z mapy = {iq_test:.1f} mm3/suw ({iq_test*0.835:.1f} mg)")

# Rail: IQ=52.9 mm3 -> os = 5290. Ale max osi = 4000!
# Uzytkownik rozszerzyl do 4000 = 40 mm3. Wiec 52.9 mm3 PRZEKRACZA mape!
iq_os = iq_test * 100  # = 5291
print(f"  IQ na osi Rail = {iq_os:.0f} (max osi = 4000)")
if iq_os > 4000:
    print(f"  !!! DAWKA PRZEKRACZA MAPE RAIL o {(iq_os-4000)/100:.1f} mm3/suw !!!")
    print(f"  Sterownik ekstrapoluje lub saturuje na ostatniej wartosci (4000 -> {1337} bar)")
    
print()
print(f"  Rail z logu FRP = 1288 bar")
print(f"  Rail z mapy (max os) = 1337 bar (wartosc przy IQ=40mm3, RPM=2000)")
print()

# Duration: Rail=1288 bar, IQ=52.91 mm3 = os 5291 (ale max osi Duration IQ = 7000 = 70 mm3)
# Wiec Duration mapa ma wystarczajacy zakres!
dur_17000 = [0,172,172,172,172,172,226,241,260,290,331,379,417,476,520,560,598,632,652,672,726,846,1024,1413]
dur_iq_axis = [0,70,120,150,180,220,270,320,400,600,1000,1400,1800,2200,2500,2800,3100,3400,3600,3800,4000,4400,5000,7000]

dur_test = interp(dur_iq_axis, dur_17000, iq_os)
print(f"  Duration przy Rail=1700bar, IQ={iq_os:.0f}: {dur_test:.0f} us")

# Przy Rail=1400 bar:
dur_14000 = [0,190,190,190,190,190,241,261,282,316,359,414,465,533,578,621,659,693,722,767,841,983,1151,1588]
dur_1400_test = interp(dur_iq_axis, dur_14000, iq_os)
print(f"  Duration przy Rail=1400bar, IQ={iq_os:.0f}: {dur_1400_test:.0f} us")
print(f"  Roznica: {dur_1400_test - dur_test:.0f} us (1700 bar jest {(1-dur_test/dur_1400_test)*100:.1f}% krotszy)")

print()
print("=== OBLICZENIA DAWKI vs DOLADOWANIE vs LAMBDA ===")
print()
for rpm in [1750, 2000, 2250, 2500, 2750, 3000, 3250]:
    # Target boost: 1.5 bar = 250 kPa
    map_kpa = 250
    ve = 0.85 if rpm < 2500 else (0.80 if rpm < 3000 else 0.78)
    strokes_per_sec = rpm / 30.0  # 4cyl 4T: rpm*4/(2*60) = rpm/30
    
    # Masa powietrza: rho * MAP/101.325 * Vd_per_cyl * VE
    Vd_cyl = 0.39e-3  # m3 (390 cm3 = 1560/4)
    rho = 1.15  # kg/m3 (po intercoolerze ~40-50C)
    air_mg = rho * (map_kpa/101.325) * Vd_cyl * ve * 1e6  # mg
    
    # IQ z NM_TO_IQ przy docelowym momencie
    nm_limiter_v = {1000:143.3,1250:200.4,1500:275,1750:300,2000:325,2250:345,2500:350,2750:345,3000:329,3250:319}
    nm_rpms = sorted(nm_limiter_v.keys())
    nm_vals = [nm_limiter_v[r] for r in nm_rpms]
    nm_max = interp(nm_rpms, nm_vals, rpm)
    target_nm = min(315, nm_max)
    target_nm_axis = target_nm * 10
    
    # Interpolacja IQ z dwoch najblizszych wierszy RPM
    iq_rows = {
        1750: [0,1.96,3.9,5.74,8.13,11.43,16,19.69,23.97,29.16,34.31,38.97,43.68,49,54.74,64.5],
        2000: [0,2.02,3.24,5.5,7.8,12.1,15.74,20,24.3,28.94,33.59,37.24,41.64,48.48,55,64.8],
        2250: [0,2.06,3.9,6.26,8.95,12.5,15.63,19.84,24.79,29.49,33.03,37.87,42.58,48.5,55.8,66],
        2500: [0,2.1,4.9,7.42,10.09,13.36,17.84,22.06,26.4,30.45,34.08,37.98,42.48,48.97,56.82,67.4],
        2750: [0,2.15,3.5,5.49,8.73,13.51,15.93,20.14,24.41,28.78,33.2,37.83,42.53,50,58.15,69],
        3000: [0,2.2,4.55,7.16,10.42,13.57,17.45,21.45,26.63,30.69,34.27,38.46,43.36,51.15,59.35,70.7],
        3250: [0,2.23,4.36,6.73,9.42,12.94,17.74,21.81,26.52,31.02,34.67,39.21,44.07,52.58,60.62,72.45],
    }
    
    if rpm in iq_rows:
        iq_mm3 = interp(nm_axis, iq_rows[rpm], target_nm_axis)
    else:
        iq_mm3 = interp(nm_axis, iq_rows[min(iq_rows.keys(), key=lambda r: abs(r-rpm))], target_nm_axis)
    
    iq_mg = iq_mm3 * 0.835
    
    afr = air_mg / iq_mg if iq_mg > 0 else 99
    lam = afr / 14.5
    
    maf_gs = air_mg * strokes_per_sec / 1000
    
    print(f"RPM={rpm}: Target={target_nm:.0f}Nm | IQ={iq_mm3:.1f}mm3 ({iq_mg:.1f}mg) | Air={air_mg:.0f}mg/suw | MAF={maf_gs:.1f}g/s | AFR={afr:.1f} | Lambda={lam:.2f}")
