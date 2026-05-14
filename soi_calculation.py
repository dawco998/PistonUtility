import sys, io, math
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# ============================================================
# OBLICZENIA SOI DLA MAZDA 1.6 MZ-CD (DV6TED4) / EDC16C3
# ============================================================
# Parametry silnika
bore = 75.0          # mm
stroke = 88.3        # mm
con_rod = 145.0      # mm (szacowany)
comp_ratio = 18.0    # stopien sprezania
displacement = 1560  # cm3 (total)
n_cyl = 4

# Parametry paliwa (ON)
cetane = 51          # typowy ON w Europie
LHV = 42700          # kJ/kg (wartosc opalowa)
stoich_afr = 14.5    # stechiometryczne AFR

# Docelowe cisnienie Rail z mapy (bar) - uzywamy wartosci z logu/mapy
rail_by_rpm = {
    1500: 1050, 1750: 1225, 2000: 1337, 2250: 1420,
    2500: 1477, 2750: 1550, 3000: 1600, 3250: 1660, 3500: 1700
}

# Docelowe cisnienie doladowania MAP (kPa abs)
map_kpa = 250  # 1.5 bar boost = 250 kPa abs

# ============================================================
# 1. OBLICZENIE OPOZNIENIA ZAPLONU (Ignition Delay)
# ============================================================
# Model Hardenberg & Hase (SAE 790493) - standard przemyslowy:
# tau_id [ms] = C1 * exp(EA / (R * T_comp)) * (P_comp)^(-n)
#
# Uproszczony model Assanis:
# tau_id [deg CA] = (0.36 + 0.22 * Sp) * exp(EA * (1/(R*T_comp) - 1/17190) * (21.2 / (P_comp - 12.4))^0.63)
#
# Praktyczny model dla common-rail diesel:
# tau_id [ms] ~ 0.3 + 1.5 * exp(-0.002 * P_rail) * (800/T_intake)^1.5

def calc_ignition_delay_ms(rpm, rail_bar, map_kpa, iat_C=40):
    """
    Opoznienie zaplonu w ms.
    Zalezne od: cisnienia rail (atomizacja), temperatury w cylindrze (kompresja powietrza z turbo).
    """
    # Temperatura po sprezeniu (adiabtyczne)
    T_intake_K = 273.15 + iat_C  # po intercoolerze
    gamma = 1.35  # wykladnik adiabaty dla powietrza
    T_comp = T_intake_K * (comp_ratio ** (gamma - 1))  # ~850-900K
    
    # Cisnienie po sprezeniu
    P_intake_bar = map_kpa / 100.0
    P_comp = P_intake_bar * (comp_ratio ** gamma)  # ~70-80 bar
    
    # Ignition delay (model empiryczny dla CR diesel, skalibrowany do typowych 0.3-0.8ms)
    # Wyzsze cisnienie rail = lepsza atomizacja = krotsze ID
    # Wyzsza temperatura = krotsze ID
    base_id = 0.8  # ms bazowe
    rail_factor = math.exp(-0.0008 * (rail_bar - 800))  # normalizacja do 800 bar
    temp_factor = (800 / T_comp) ** 1.2
    
    tau_ms = base_id * rail_factor * temp_factor
    tau_ms = max(0.25, min(tau_ms, 1.5))  # clamp do fizycznych granic
    
    # Przeliczenie na stopnie obrotu walu korbowego
    tau_deg = tau_ms * (rpm * 360.0) / (60.0 * 1000.0)  # ms -> deg CA
    
    return tau_ms, tau_deg, T_comp, P_comp

# ============================================================
# 2. OBLICZENIE OPTYMALNEGO SOI
# ============================================================
# Cel: szczytowe cisnienie (PCP) powinno wystapic w optymalnym miejscu
#
# MAX MOC:     PCP @ 8-10 deg ATDC  (agresywne, wysokie NOx, glosne)
# MAX EKONOMIA: PCP @ 15-18 deg ATDC (lagodne, niskie NOx, ciche)
# BALANS:       PCP @ 12-14 deg ATDC (kompromis moc/ekonomia)
#
# SOI = -(tau_id_deg + burn_delay - target_PCP_location)
# burn_delay = czas od zaplonu do szczytu cisnienia (ok. 30-40% czasu spalania)
# Czas spalania (10-90%) ~ 25-40 deg CA w zaleznosci od RPM i dawki

def calc_optimal_soi(rpm, rail_bar, map_kpa, target_pcp_atdc=12, iat_C=40):
    """
    Oblicza optymalny SOI w stopniach BTDC.
    target_pcp_atdc: docelowa pozycja PCP (stopnie po GMP)
    """
    tau_ms, tau_deg, T_comp, P_comp = calc_ignition_delay_ms(rpm, rail_bar, map_kpa, iat_C)
    
    # Czas spalania 10-90% (rozciaga sie z RPM bo jest mniej czasu na mieszanie)
    # Typowo: 25 deg @ 1500 RPM do 40 deg @ 4000 RPM
    burn_duration_deg = 22 + 0.005 * rpm  # deg CA (10-90%)
    
    # Czas od momentu zaplonu do szczytu cisnienia (ok. 35% calkowitego spalania)
    burn_to_peak = burn_duration_deg * 0.35
    
    # SOI: musimy zaczac wtrysk na tyle wczesnie, zeby:
    # SOI + ignition_delay + burn_to_peak = target_PCP_location
    # SOI = target_PCP_location - ignition_delay - burn_to_peak
    # (ujemne = BTDC)
    soi_btdc = tau_deg + burn_to_peak - target_pcp_atdc
    
    return soi_btdc, tau_ms, tau_deg, burn_duration_deg, burn_to_peak

# ============================================================
# 3. GENEROWANIE TABELI SOI
# ============================================================

print("="*110)
print("OBLICZENIA OPTYMALNEGO SOI (Start of Injection) - Mazda 1.6 MZ-CD")
print("="*110)
print()
print("Parametry: CR=18:1, Boost=1.5bar, IAT=40C (po intercoolerze), Cetane~51")
print()

# Trzy scenariusze
scenarios = [
    ("MAX MOC",     8,  "Agresywne, glosne, max PCP, wysokie NOx"),
    ("BALANS",     12,  "Kompromis moc/ekonomia - REKOMENDOWANY"),
    ("EKONOMIA",   16,  "Lagodne, ciche, niskie EGT, niskie NOx"),
]

for name, target_pcp, desc in scenarios:
    print(f"\n{'─'*110}")
    print(f"  SCENARIUSZ: {name} (PCP target @ {target_pcp} deg ATDC) - {desc}")
    print(f"{'─'*110}")
    print(f"{'RPM':<6} | {'Rail bar':<9} | {'ID ms':<7} | {'ID deg':<7} | {'Burn deg':<9} | {'SOI BTDC':<9} | {'T_comp K':<9} | {'P_comp bar'}")
    print("-"*90)
    
    for rpm in sorted(rail_by_rpm.keys()):
        rail = rail_by_rpm[rpm]
        soi, tau_ms, tau_deg, burn_dur, burn_peak = calc_optimal_soi(rpm, rail, map_kpa, target_pcp)
        _, _, T_comp, P_comp = calc_ignition_delay_ms(rpm, rail, map_kpa)
        
        print(f"{rpm:<6} | {rail:<9} | {tau_ms:<7.2f} | {tau_deg:<7.1f} | {burn_dur:<9.1f} | {soi:<9.1f} | {T_comp:<9.0f} | {P_comp:<.0f}")

# ============================================================
# 4. TABELA KONCOWA - REKOMENDOWANY SOI
# ============================================================
print()
print("="*110)
print("REKOMENDOWANA MAPA SOI (deg BTDC) - scenariusz BALANS")
print("="*110)
print()
print("Do wklejenia do mapy SOI w ECU (os X = RPM, wartosci = stopnie BTDC):")
print()

row_rpm = []
row_soi = []
for rpm in sorted(rail_by_rpm.keys()):
    rail = rail_by_rpm[rpm]
    soi, _, _, _, _ = calc_optimal_soi(rpm, rail, map_kpa, target_pcp_atdc=12)
    row_rpm.append(str(rpm))
    row_soi.append(f"{soi:.1f}")

print("RPM:  " + "  |  ".join(row_rpm))
print("SOI:  " + "  |  ".join(row_soi))

# ============================================================
# 5. PID - REKOMENDACJE
# ============================================================
print()
print("="*110)
print("REKOMENDACJE PID")
print("="*110)
print()

print("""
1. PID DOLADOWANIA (Boost / N75 / VNT):
   ─────────────────────────────────────
   Problem z Twojego logu: oscylacja cisnienia (1.42 -> 1.29 -> wzrost).
   To klasyczny objaw ZA DUZEGO czlonu P (Proportional) lub ZA MALEGO czlonu D (Derivative).
   
   Rekomendacja:
   - Czlon P (Proportional): Zmniejsz o 10-15% jesli masz oscylacje. 
     Za duze P = sterownik reaguje zbyt gwaltownie na blad (overboost -> underboost -> overboost).
   - Czlon I (Integral): Zostaw bez zmian lub delikatnie zwieksz (+5-10%).
     I odpowiada za "dobijanie" do wartosci docelowej. Wieksze I = wolniejsze ale dokladniejsze.
   - Czlon D (Derivative): Zwieksz o 10-20% jesli masz oscylacje.
     D "hamuje" zbyt szybkie zmiany. Wieksze D = tlumi oscylacje.
   
   UWAGA: W EDC16C3 PID turbo czesto ma odwrocona logike (wyzsze VBCV = bardziej zamkniete 
   lopatki = wiecej boostu). Upewnij sie, ze modyfikujesz we wlasciwym kierunku!

2. PID CISNIENIA RAIL:
   ────────────────────
   Z logu: Rail trzyma sie bardzo dobrze (blad <2% vs mapa). Nie ruszaj PID Rail!
   Pompa CP1H swietnie nadaza. Jedyna sytuacja do zmiany to gdyby pojawily sie 
   oscylacje cisnienia rail (szarpanie pod gazem).

3. EGR PID:
   ─────────
   Jesli masz EGR wylaczony (usuniety / zablokowany) - nie dotyczy.
   Jesli EGR dziala: upewnij sie ze przy WOT (pelne obciazenie) EGR jest calkowicie zamkniety.
   Jakikolwiek EGR przy pelnym gazie = mniej tlenu = wiecej dymu = nizszy moment.

4. PILOT INJECTION (wtrysk pilotowy):
   ──────────────────────────────────
   Jesli masz mape Pilot Injection:
   - Pilot pomaga zmniejszyc opoznienie zaplonu (ID) i halas.
   - Typowo: 1-3 mg paliwa, 15-25 deg przed SOI glownym.
   - Przy wyzszym cisnieniu Rail (1700 bar) pilot moze byc mniejszy (lepsza atomizacja).
   - Nie usuwaj pilota calkowicie - silnik bedzie glosny jak traktor.
""")
