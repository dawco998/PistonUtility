import sys, io, math
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# ============================================================
# ANALIZA SOI DLA PROJEKTU GTD1244VZ + INTERCOOLER
# Mazda 1.6 MZ-CD (DV6TED4) / EDC16C3
# ============================================================
# GTD1244VZ vs stock GT1544V:
#   - Wieksza sprezarka (~48mm inducer vs ~37mm)
#   - Wieksza turbina (~44mm vs ~37mm)
#   - Wyzszy max boost: 1.6-1.8 bar vs 1.0-1.2 bar stock
#   - Pozniejszy spool (~1800 RPM vs ~1500 RPM)
#   - Lepszy przeplyw powyzej 2500 RPM
# Intercooler:
#   - Obniza IAT z ~60-80C (bez IC) do ~35-45C
#   - Gęstsze powietrze = wiecej tlenu = mozna wiecej paliwa

bore = 75.0; stroke = 88.3; con_rod = 145.0; comp_ratio = 18.0
displacement_cc = 1560; n_cyl = 4; Vd_cyl_m3 = (displacement_cc / n_cyl) * 1e-6

# --- MAPY Z ECU ---
nm_limiter = {1000:143.3,1250:200.4,1500:275,1750:300,2000:325,2250:345,
              2500:350,2750:345,3000:329,3250:319,3500:309,3750:298,4000:285}

nm_axis = [0,100,200,350,500,750,1000,1250,1500,1750,2000,2250,2500,2750,3000,3500]
iq_rows = {
    1500: [0,1.7,2.99,5.8,7.36,11.33,16,21.08,25.68,30.49,35.69,41.23,46.65,51.8,55.8,65.5],
    1750: [0,1.96,3.9,5.74,8.13,11.43,16,19.69,23.97,29.16,34.31,38.97,43.68,49,54.74,64.5],
    2000: [0,2.02,3.24,5.5,7.8,12.1,15.74,20,24.3,28.94,33.59,37.24,41.64,48.48,55,64.8],
    2250: [0,2.06,3.9,6.26,8.95,12.5,15.63,19.84,24.79,29.49,33.03,37.87,42.58,48.5,55.8,66],
    2500: [0,2.1,4.9,7.42,10.09,13.36,17.84,22.06,26.4,30.45,34.08,37.98,42.48,48.97,56.82,67.4],
    2750: [0,2.15,3.5,5.49,8.73,13.51,15.93,20.14,24.41,28.78,33.2,37.83,42.53,50,58.15,69],
    3000: [0,2.2,4.55,7.16,10.42,13.57,17.45,21.45,26.63,30.69,34.27,38.46,43.36,51.15,59.35,70.7],
    3250: [0,2.23,4.36,6.73,9.42,12.94,17.74,21.81,26.52,31.02,34.67,39.21,44.07,52.58,60.62,72.45],
    3500: [0,2.26,4.17,6.3,8.41,12.3,18.03,22.17,26.41,31.34,35.06,39.95,44.77,54,61.89,74.2],
}

rail_by_rpm = {1500:1050, 1750:1225, 2000:1337, 2250:1420,
               2500:1477, 2750:1550, 3000:1600, 3250:1660, 3500:1700}

dur_iq_axis = [0,70,120,150,180,220,270,320,400,600,1000,1400,1800,2200,2500,2800,3100,3400,3600,3800,4000,4400,5000,7000]
dur_table = {
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
    return y_arr[-1]

def get_iq(rpm, torque_nm):
    nm_val = torque_nm * 10
    rpms = sorted(iq_rows.keys())
    if rpm <= rpms[0]: return interp(nm_axis, iq_rows[rpms[0]], nm_val)
    if rpm >= rpms[-1]: return interp(nm_axis, iq_rows[rpms[-1]], nm_val)
    for i in range(len(rpms)-1):
        if rpms[i] <= rpm <= rpms[i+1]:
            v1 = interp(nm_axis, iq_rows[rpms[i]], nm_val)
            v2 = interp(nm_axis, iq_rows[rpms[i+1]], nm_val)
            t = (rpm - rpms[i]) / (rpms[i+1] - rpms[i])
            return v1 + t * (v2 - v1)

def get_duration(rail_bar, iq_mm3):
    iq_axis_val = iq_mm3 * 100
    rail_axis_val = rail_bar * 10
    rails = sorted(dur_table.keys())
    if rail_axis_val <= rails[0]: return interp(dur_iq_axis, dur_table[rails[0]], iq_axis_val)
    if rail_axis_val >= rails[-1]: return interp(dur_iq_axis, dur_table[rails[-1]], iq_axis_val)
    for i in range(len(rails)-1):
        if rails[i] <= rail_axis_val <= rails[i+1]:
            d1 = interp(dur_iq_axis, dur_table[rails[i]], iq_axis_val)
            d2 = interp(dur_iq_axis, dur_table[rails[i+1]], iq_axis_val)
            t = (rail_axis_val - rails[i]) / (rails[i+1] - rails[i])
            return d1 + t * (d2 - d1)

def calc_ignition_delay(rpm, rail_bar, T_intake_K, P_intake_bar):
    gamma = 1.35
    T_comp = T_intake_K * (comp_ratio ** (gamma - 1))
    P_comp = P_intake_bar * (comp_ratio ** gamma)
    base_id = 0.8
    rail_factor = math.exp(-0.0008 * (rail_bar - 800))
    temp_factor = (800 / T_comp) ** 1.2
    tau_ms = max(0.25, min(base_id * rail_factor * temp_factor, 1.5))
    tau_deg = tau_ms * rpm * 360.0 / 60000.0
    return tau_ms, tau_deg, T_comp, P_comp

def calc_soi(rpm, rail_bar, T_intake_K, P_intake_bar, target_pcp_atdc=12):
    tau_ms, tau_deg, T_comp, P_comp = calc_ignition_delay(rpm, rail_bar, T_intake_K, P_intake_bar)
    burn_dur = 22 + 0.005 * rpm
    burn_to_peak = burn_dur * 0.35
    soi_btdc = tau_deg + burn_to_peak - target_pcp_atdc
    return soi_btdc, tau_ms, tau_deg, burn_dur, T_comp, P_comp

# ============================================================
# PROFIL BOOST GTD1244VZ
# ============================================================
# GTD1244VZ spool profil - realny boost vs RPM
# Pozniejszy spool niz GT1544V ale wyzszy max boost
gtd1244_boost_bar = {
    1250: 0.4, 1500: 0.8, 1750: 1.2, 2000: 1.5, 2250: 1.6,
    2500: 1.65, 2750: 1.65, 3000: 1.6, 3250: 1.55, 3500: 1.5,
    3750: 1.4, 4000: 1.3
}
# MAP kPa = (1 + boost_bar) * 101.325

# IAT po intercoolerze
iat_with_ic = 40   # C - z dobrym FMIC
iat_no_ic = 70     # C - bez IC (referencyjna)

print("=" * 120)
print("ANALIZA SOI DLA PROJEKTU GTD1244VZ + INTERCOOLER - Mazda 1.6 MZ-CD")
print("=" * 120)

# ============================================================
# 1. POROWNANIE: STOCK BOOST vs GTD1244VZ BOOST
# ============================================================
print("\n" + "=" * 120)
print("1. PROFIL BOOST: GTD1244VZ vs aktualny setup")
print("=" * 120)

stock_boost = {1500:1.0, 1750:1.2, 2000:1.3, 2250:1.35, 2500:1.4, 2750:1.35, 3000:1.3, 3250:1.2, 3500:1.1}

print(f"\n{'RPM':<6} | {'Stock boost':<12} | {'GTD1244 boost':<14} | {'Roznica':<10} | {'MAP GTD kPa':<12} | {'Airflow zysk'}")
print("-" * 80)
for rpm in [1500,1750,2000,2250,2500,2750,3000,3250,3500]:
    sb = stock_boost.get(rpm, 1.0)
    gb_rpms = sorted(gtd1244_boost_bar.keys())
    gb = interp(gb_rpms, [gtd1244_boost_bar[r] for r in gb_rpms], rpm)
    map_gtd = (1 + gb) * 101.325
    airflow_gain = ((1+gb)/(1+sb) - 1) * 100
    print(f"{rpm:<6} | {sb:<12.2f} | {gb:<14.2f} | {gb-sb:<+10.2f} | {map_gtd:<12.0f} | {airflow_gain:<+.1f}%")

# ============================================================
# 2. SOI Z GTD1244VZ + IC vs AKTUALNY SOI
# ============================================================
print("\n" + "=" * 120)
print("2. SOI: AKTUALNY vs GTD1244VZ + IC (PCP target @ 10 deg ATDC - agresywny balans)")
print("=" * 120)

# Obecny SOI (z eoi_calculation.py)
current_soi = {1500:5.2, 1750:5.7, 2000:6.4, 2250:7.2, 2500:8.0, 2750:8.6, 3000:9.4, 3250:10.1, 3500:10.8}

print(f"\n{'RPM':<6} | {'Boost bar':<10} | {'MAP kPa':<8} | {'IAT C':<6} | {'T_comp K':<9} | {'ID ms':<6} | {'ID deg':<7} | {'SOI stary':<10} | {'SOI GTD':<10} | {'Zmiana'}")
print("-" * 110)

new_soi = {}
for rpm in [1500,1750,2000,2250,2500,2750,3000,3250,3500]:
    gb_rpms = sorted(gtd1244_boost_bar.keys())
    boost = interp(gb_rpms, [gtd1244_boost_bar[r] for r in gb_rpms], rpm)
    map_kpa = (1 + boost) * 101.325
    T_intake_K = 273.15 + iat_with_ic
    P_intake_bar = map_kpa / 100.0

    rail = rail_by_rpm.get(rpm, 1400)
    # PCP target: 10 deg ATDC - agresywny balans dla turbo projektu
    soi, tau_ms, tau_deg, burn_dur, T_comp, P_comp = calc_soi(rpm, rail, T_intake_K, P_intake_bar, target_pcp_atdc=10)
    old_soi = current_soi.get(rpm, 6.0)
    new_soi[rpm] = round(soi, 1)

    print(f"{rpm:<6} | {boost:<10.2f} | {map_kpa:<8.0f} | {iat_with_ic:<6} | {T_comp:<9.0f} | {tau_ms:<6.2f} | {tau_deg:<7.1f} | {old_soi:<10.1f} | {soi:<10.1f} | {soi-old_soi:<+.1f}")

# ============================================================
# 3. DAWKA PALIWA, LAMBDA, DURATION, EOI
# ============================================================
print("\n" + "=" * 120)
print("3. DAWKA PALIWA / LAMBDA / DURATION / EOI - GTD1244VZ + IC")
print("=" * 120)

print(f"\n{'RPM':<5}|{'Nm':<5}|{'IQ mm3':<7}|{'IQ mg':<7}|{'Rail':<6}|{'Boost':<6}|{'Air mg':<7}|{'AFR':<6}|{'Lam':<5}|{'Dur us':<7}|{'Dur deg':<8}|{'SOI':<5}|{'EOI':<10}|{'Status'}")
print("-" * 115)

for rpm in [1500,1750,2000,2250,2500,2750,3000,3250,3500]:
    nm_rpms = sorted(nm_limiter.keys())
    nm_max = interp(nm_rpms, [nm_limiter[r] for r in nm_rpms], rpm)
    target_nm = min(315, nm_max)

    iq_mm3 = get_iq(rpm, target_nm)
    iq_mg = iq_mm3 * 0.835
    rail = rail_by_rpm.get(rpm, 1400)

    gb_rpms = sorted(gtd1244_boost_bar.keys())
    boost = interp(gb_rpms, [gtd1244_boost_bar[r] for r in gb_rpms], rpm)
    map_kpa = (1 + boost) * 101.325

    # VE: GTD1244VZ ma lepszy VE na gorze niz stock
    if rpm < 1750: ve = 0.82
    elif rpm < 2500: ve = 0.87
    elif rpm < 3000: ve = 0.85
    else: ve = 0.82

    rho = 1.15  # kg/m3 po IC przy ~40C
    air_mg = rho * (map_kpa / 101.325) * Vd_cyl_m3 * ve * 1e6

    afr = air_mg / iq_mg if iq_mg > 0 else 99
    lam = afr / 14.5

    dur_us = get_duration(rail, iq_mm3)
    dur_ms = dur_us / 1000.0
    dur_deg = dur_us * rpm * 6.0 / 1e6

    soi = new_soi.get(rpm, 6.0)
    eoi_val = soi - dur_deg
    eoi_str = f"{abs(eoi_val):.1f} {'BTDC' if eoi_val > 0 else 'ATDC'}"

    eoi_atdc = -eoi_val
    if lam < 1.05: status = "BOGATO!"
    elif lam < 1.15: status = "GRANICA"
    elif eoi_atdc > 30: status = "EOI POZNE!"
    elif eoi_atdc > 25: status = "EOI UWAGA"
    else: status = "OK"

    print(f"{rpm:<5}|{target_nm:<5.0f}|{iq_mm3:<7.1f}|{iq_mg:<7.1f}|{rail:<6}|{boost:<6.2f}|{air_mg:<7.0f}|{afr:<6.1f}|{lam:<5.2f}|{dur_us:<7.0f}|{dur_deg:<8.1f}|{soi:<5.1f}|{eoi_str:<10}|{status}")

# ============================================================
# 4. WPLYW IC NA IGNITION DELAY
# ============================================================
print("\n" + "=" * 120)
print("4. WPLYW INTERCOOLERA NA IGNITION DELAY")
print("=" * 120)

print(f"\n{'RPM':<6} | {'Boost':<6} | {'IAT bez IC':<11} | {'ID bez IC':<10} | {'IAT z IC':<9} | {'ID z IC':<8} | {'Roznica ID':<11} | {'Zysk SOI'}")
print("-" * 90)

for rpm in [1500,1750,2000,2250,2500,2750,3000,3250,3500]:
    gb_rpms = sorted(gtd1244_boost_bar.keys())
    boost = interp(gb_rpms, [gtd1244_boost_bar[r] for r in gb_rpms], rpm)
    map_kpa = (1 + boost) * 101.325
    P_bar = map_kpa / 100.0
    rail = rail_by_rpm.get(rpm, 1400)

    T_no_ic = 273.15 + iat_no_ic
    T_ic = 273.15 + iat_with_ic

    tau_no_ic, deg_no_ic, _, _ = calc_ignition_delay(rpm, rail, T_no_ic, P_bar)
    tau_ic, deg_ic, _, _ = calc_ignition_delay(rpm, rail, T_ic, P_bar)

    print(f"{rpm:<6} | {boost:<6.2f} | {iat_no_ic:<11}C | {tau_no_ic:<10.3f}ms | {iat_with_ic:<9}C | {tau_ic:<8.3f}ms | {tau_ic-tau_no_ic:<+11.3f}ms | {deg_ic-deg_no_ic:<+.2f} deg")

# ============================================================
# 5. REKOMENDOWANA MAPA SOI - GTD1244VZ + IC
# ============================================================
print("\n" + "=" * 120)
print("5. REKOMENDOWANA MAPA SOI DLA GTD1244VZ + IC")
print("=" * 120)
print()
print("PCP target: 10 deg ATDC (agresywny balans - max moc przy rozsadnym PCP)")
print("IAT: 40C (po FMIC)")
print()
print("RPM:   " + "  |  ".join([str(r) for r in sorted(new_soi.keys())]))
print("SOI:   " + "  |  ".join([f"{new_soi[r]:.1f}" for r in sorted(new_soi.keys())]))

# ============================================================
# 6. ZMIANY DO WPROWADZENIA
# ============================================================
print("\n" + "=" * 120)
print("6. LISTA ZMIAN DO PROJEKTU GTD1244VZ + IC")
print("=" * 120)
print("""
A. MAPA SOI (Start of Injection):
   Przesunac SOI o ~1-2 deg wczesniej (wiecej BTDC) niz obecny BALANS.
   Uzasadnienie: GTD1244VZ daje wyzszy boost -> wyzsza T_comp -> krotszy
   ignition delay -> mozna agresywniej ustawic SOI dla wiekszej mocy.
   IC obniza IAT o ~30C co daje gestsza ladunke i nieco dluzszy ID,
   ale sumarycznie wyzsze cisnienie kompresji (wiekszy boost) dominuje.

B. NM LIMITER:
   Obecny: max 350 Nm @ 2500 RPM
   Przy GTD1244VZ mozna osiagnac 350+ Nm, ale ogranicza nas:
   - Lambda (min 1.15 dla bezpiecznego spalania bez dymu)
   - PCP (max ~160 bar dla DV6TED4, stock con-rods)
   - Temperatura spalin EGT (max 750C)
   REKOMENDACJA: Zostaw 315 Nm jako bezpieczny cel. NM Limiter OK.

C. RAIL PRESSURE:
   Obecna mapa saturuje na IQ=40mm3 (os 4000).
   Przy 315 Nm, IQ = 55-65 mm3 -> PRZEKRACZA mape Rail!
   KONIECZNE: Rozszerzyc os Rail do min 7000 (70 mm3/suw).
   Dodac kolumny: 4500, 5000, 5500, 6000, 6500, 7000
   Rail w nowych kolumnach: ekstrapolacja liniowa z ostatnich 2 punktow.

D. BOOST MAPA (VNT/N75):
   GTD1244VZ profil:
   RPM:   1500 | 1750 | 2000 | 2250 | 2500 | 2750 | 3000 | 3250 | 3500
   BOOST: 0.80 | 1.20 | 1.50 | 1.60 | 1.65 | 1.65 | 1.60 | 1.55 | 1.50
   Ustawic boost request w mapie doladowania.
   UWAGA: PID boost trzeba przetuningowac - GTD1244VZ ma inercje wiekszego
   kola sprrezarki, wiec P/I/D musza byc wolniejsze niz stock GT1544V.

E. PILOT INJECTION:
   Przy wyzszym Rail (1400-1700 bar) i IC:
   - Pilot: 1.5-2.5 mg, 18-22 deg przed SOI glownym
   - IC obniza temperature kolektora -> moze byc glosniej bez pilota
   - NIE usuwac pilota!

F. EGR:
   Przy WOT z GTD1244VZ: EGR musi byc 100% zamkniety.
   Kazde otwarcie EGR przy pelnym gazie = strata mocy + dym.
""")

# ============================================================
# 7. BEZPIECZENSTWO: PCP i EGT
# ============================================================
print("=" * 120)
print("7. SZACUNKOWE PCP i EGT")
print("=" * 120)

print(f"\n{'RPM':<6} | {'Nm':<5} | {'IQ mm3':<7} | {'Boost':<6} | {'P_comp':<8} | {'PCP est':<8} | {'EGT est':<8} | {'Status'}")
print("-" * 75)

for rpm in [1500,1750,2000,2250,2500,2750,3000,3250,3500]:
    nm_rpms = sorted(nm_limiter.keys())
    nm_max = interp(nm_rpms, [nm_limiter[r] for r in nm_rpms], rpm)
    target_nm = min(315, nm_max)
    iq_mm3 = get_iq(rpm, target_nm)

    gb_rpms = sorted(gtd1244_boost_bar.keys())
    boost = interp(gb_rpms, [gtd1244_boost_bar[r] for r in gb_rpms], rpm)
    map_kpa = (1 + boost) * 101.325
    P_intake_bar = map_kpa / 100.0

    gamma = 1.35
    T_intake_K = 273.15 + iat_with_ic
    P_comp = P_intake_bar * (comp_ratio ** gamma)

    # PCP ~ P_comp * (1 + fuel_energy_factor)
    # Szacunkowo: PCP ~ P_comp * 1.3 dla diesel przy WOT
    pcp_est = P_comp * 1.25
    # EGT szacunkowo z IQ i lambda
    egt_est = 400 + iq_mm3 * 5  # bardzo grube przyblizenie

    pcp_ok = "OK" if pcp_est < 160 else "WYSOKI!"
    egt_ok = "OK" if egt_est < 750 else "WYSOKI!"
    status = f"PCP:{pcp_ok} EGT:{egt_ok}"

    print(f"{rpm:<6} | {target_nm:<5.0f} | {iq_mm3:<7.1f} | {boost:<6.2f} | {P_comp:<8.0f} | {pcp_est:<8.0f} | {egt_est:<8.0f} | {status}")

print("\n" + "=" * 120)
print("KONIEC ANALIZY GTD1244VZ + IC")
print("=" * 120)
