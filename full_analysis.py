import csv, sys, io, math
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# === DANE Z MAP (wklejone recznie z xlsx dump) ===

# NM LIMITER: rpm -> max NM
nm_limiter = {
    1000:143.3, 1250:200.4, 1500:275, 1750:300, 2000:325, 2250:345, 2500:350,
    2750:345, 3000:329, 3250:319, 3500:309, 3750:298, 4000:285, 4250:280
}

# NM TO IQ: rpm -> lista (NM_breakpoint, IQ_value)
nm_to_iq_rpm_axis = [250,500,750,1000,1250,1500,1750,2000,2250,2500,2750,3000,3500,4000,4500,5000]
nm_to_iq_nm_axis = [0,100,200,350,500,750,1000,1250,1500,1750,2000,2250,2500,2750,3000,3500]

nm_to_iq_data = {
    250:  [0,2,4.12,7.53,10.95,16.91,22.86,28.82,34.78,40.73,46.69,52.64,58.6,64.56,70.24,81.9],
    500:  [0,1.86,3.98,6.89,10.29,15.7,21.6,27.42,33.21,39.11,44.97,51.13,57.48,62.89,68.13,79.5],
    750:  [0,4.43,5.74,8.26,10.7,14.85,20.11,25.46,31.32,36.92,42.44,48.49,54.56,60.2,64.57,75.4],
    1000: [0,2.55,4.63,7.61,10.15,14.36,18.37,23.97,29.34,34.78,40.33,46.12,52.01,55.7,61.8,71.8],
    1250: [0,2.37,3.91,6.51,9.4,13.27,17.62,23.69,28.23,33.09,38.46,43.89,49.57,53.81,58.8,68.3],
    1500: [0,1.7,2.99,5.8,7.36,11.33,16,21.08,25.68,30.49,35.69,41.23,46.65,51.8,55.8,65.5],
    1750: [0,1.96,3.9,5.74,8.13,11.43,16,19.69,23.97,29.16,34.31,38.97,43.68,49,54.74,64.5],
    2000: [0,2.02,3.24,5.5,7.8,12.1,15.74,20,24.3,28.94,33.59,37.24,41.64,48.48,55,64.8],
    2250: [0,2.06,3.9,6.26,8.95,12.5,15.63,19.84,24.79,29.49,33.03,37.87,42.58,48.5,55.8,66],
    2500: [0,2.1,4.9,7.42,10.09,13.36,17.84,22.06,26.4,30.45,34.08,37.98,42.48,48.97,56.82,67.4],
    2750: [0,2.15,3.5,5.49,8.73,13.51,15.93,20.14,24.41,28.78,33.2,37.83,42.53,50,58.15,69],
    3000: [0,2.2,4.55,7.16,10.42,13.57,17.45,21.45,26.63,30.69,34.27,38.46,43.36,51.15,59.35,70.7],
    3500: [0,2.26,4.17,6.3,8.41,12.3,18.03,22.17,26.41,31.34,35.06,39.95,44.77,54,61.89,74.2],
    4000: [0,2.3,4.89,7.38,10.13,14.18,17.43,22.32,27.07,31.82,36.5,41.36,46.3,55.72,63.69,76.3],
    4500: [0,2.33,4.34,7.42,9.32,13.65,18.86,25.38,28.9,32.92,37.82,42.81,48.01,56.46,64.57,77.4],
    5000: [0,2.35,4.37,7.38,9.88,14.72,17.8,22.64,28.03,33.19,38.12,43.01,48.61,56.36,64.68,77.59],
}

# DURATION: rail_press -> lista (IQ_breakpoint, duration_us)
dur_rail_axis = [1190,1200,2000,2500,3000,4000,5000,6000,7000,8000,9000,10000,11000,12000,14000,17000]
dur_iq_axis = [0,70,120,150,180,220,270,320,400,600,1000,1400,1800,2200,2500,2800,3100,3400,3600,3800,4000,4400,5000,7000]

dur_data = {
    17000: [0,172,172,172,172,172,226,241,260,290,331,379,417,476,520,560,598,632,652,672,726,846,1024,1413],
    14000: [0,190,190,190,190,190,241,261,282,316,359,414,465,533,578,621,659,693,722,767,841,983,1151,1588],
    12000: [0,195,195,195,195,201,248,272,296,330,386,445,504,574,627,672,712,750,810,874,947,1096,1261,1740],
    11000: [0,200,200,200,200,220,257,281,305,339,399,463,532,604,654,711,750,789,844,945,1030,1147,1326,1829],
    10000: [0,205,205,205,205,229,262,287,313,347,416,490,564,639,688,735,783,854,941,1023,1095,1208,1418,1956],
    9000:  [0,210,210,210,212,240,276,300,324,361,444,522,604,677,726,770,833,928,1022,1098,1164,1282,1510,2083],
    8000:  [0,215,215,215,222,256,287,311,335,372,463,545,631,710,761,810,881,1017,1103,1176,1237,1385,1640,2263],
}

# RAIL PRESSURE: rpm -> lista (mg/str_breakpoint, rail_bar)
rail_rpm_axis = [600,750,850,1000,1250,1500,1750,2000,2250,2500,2750,3000,3250,3500,4000,4500]
rail_mgstr_axis = [0,170,340,680,850,1020,1190,1360,1550,1840,2280,3000,3300,3500,3700,4000]

rail_data = {
    1500: [350,395,438,540,631,683,735,806,808,786,783,806,844,884,924,1050],
    1750: [377,427,473,580,651,711,760,848,867,858,874,870,912,986,1042,1225],
    2000: [402,450,493,592,647,723,770,856,881,916,958,944,988,1064,1120,1337],
    2250: [415,450,480,565,627,721,775,864,904,957,1019,1020,1071,1146,1199,1420],
    2500: [418,441,468,539,613,686,761,867,921,992,1076,1111,1166,1235,1281,1477],
    2750: [418,432,459,517,582,634,726,851,931,1021,1116,1160,1241,1312,1357,1550],
    3000: [395,407,417,471,524,540,605,788,925,1013,1104,1169,1251,1347,1419,1600],
    3250: [395,405,415,453,466,478,543,723,869,985,1044,1141,1226,1347,1444,1660],
}

def interp1d(x_arr, y_arr, x):
    if x <= x_arr[0]: return y_arr[0]
    if x >= x_arr[-1]: return y_arr[-1]
    for i in range(len(x_arr)-1):
        if x_arr[i] <= x <= x_arr[i+1]:
            t = (x - x_arr[i]) / (x_arr[i+1] - x_arr[i])
            return y_arr[i] + t * (y_arr[i+1] - y_arr[i])
    return y_arr[-1]

def lookup_nm_to_iq(rpm, nm):
    rpms = sorted(nm_to_iq_data.keys())
    if rpm <= rpms[0]:
        return interp1d(nm_to_iq_nm_axis, nm_to_iq_data[rpms[0]], nm)
    if rpm >= rpms[-1]:
        return interp1d(nm_to_iq_nm_axis, nm_to_iq_data[rpms[-1]], nm)
    for i in range(len(rpms)-1):
        if rpms[i] <= rpm <= rpms[i+1]:
            iq1 = interp1d(nm_to_iq_nm_axis, nm_to_iq_data[rpms[i]], nm)
            iq2 = interp1d(nm_to_iq_nm_axis, nm_to_iq_data[rpms[i+1]], nm)
            t = (rpm - rpms[i]) / (rpms[i+1] - rpms[i])
            return iq1 + t * (iq2 - iq1)

def lookup_rail(rpm, iq_mg):
    rpms = sorted(rail_data.keys())
    # IQ w mapie NM_TO_IQ jest w mg/suw ale os Rail Pressure jest w mg/str (x100?)
    # Sprawdzmy - os Rail to: 0,170,340,680... to wyglada jak mg/str * 100
    # Ale IQ z NM_TO_IQ to np 55 mg/suw. Os rail to 0..4000. 
    # Wiec os rail to prawdopodobnie IQ*100 (microliters?)
    # Lub: IQ jest w mm3/suw a nie mg/suw. Gestosc oleju ~ 0.84 g/cm3
    # Wiec 55 mg = 55/0.84 = 65.5 mm3. Ale os siega 4000...
    # Zakladam ze os Rail to IQ * pewien mnoznik. 
    # Przy 2000rpm i 325Nm, IQ ~ 55mg. Jesli os jest w 0.01mm3: 55/0.84*100 = 6547
    # To nie pasuje. Moze os jest po prostu w mg/str (mg na skok - to samo co mg/suw)
    # i wartosci 0-4000 to zakres. 55mg = 55 na osi? Ale os zaczyna sie od 0,170,340...
    # To raczej wiele za duzo. 
    # Sprawdzmy inaczej: IQ ~ 55 mg/suw. Os: 0,170,340,680,850,1020,1190,1360,1550,1840,2280,3000,3300,3500,3700,4000
    # Moze to jest IQ w 0.01 mg? Czyli 55 mg = 5500? Nie, za duzo.
    # Moze to calkowity mg/min? Przy 2000rpm (1000 wtryskow/min) i 55mg/suw = 55000 mg/min. Za duzo.
    # Najbardziej prawdopodobne: os Rail to IQ w 10*mg/suw lub mm3/hub
    # 55mg / 0.84 g/cm3 = 65.5 mm3. * 10 = 655. Na osi mamy 680. BINGO!
    # Os Rail to IQ w 0.1 mm3/suw (lub rownowaznie: mm3*10)
    # Konwersja: mg -> mm3: mg / 0.84. Potem * 10 zeby trafic na os.
    iq_mm3_10 = (iq_mg / 0.84) * 10  # konwersja mg -> os mapy rail
    
    if rpm not in rail_data:
        closest = min(rpms, key=lambda r: abs(r - rpm))
        return interp1d(rail_mgstr_axis, rail_data[closest], iq_mm3_10)
    return interp1d(rail_mgstr_axis, rail_data[rpm], iq_mm3_10)

def lookup_duration(rail_bar, iq_mg):
    # Os Duration IQ: 0,70,120,...,7000 - to wyglada na te same jednostki co Rail (0.1 mm3)
    iq_mm3_10 = (iq_mg / 0.84) * 10
    
    rails = sorted(dur_data.keys())
    # Zamiana bar na te same jednostki (mapa uzywa bar * 10? Nie, os to 1190..17000)
    # Os Duration Rail: 1190,1200,2000,...,17000 - to bar * 10!
    rail_10 = rail_bar * 10
    
    if rail_10 <= rails[0]: 
        return interp1d(dur_iq_axis, dur_data[rails[0]], iq_mm3_10)
    if rail_10 >= rails[-1]:
        return interp1d(dur_iq_axis, dur_data[rails[-1]], iq_mm3_10)
    for i in range(len(rails)-1):
        if rails[i] <= rail_10 <= rails[i+1]:
            d1 = interp1d(dur_iq_axis, dur_data[rails[i]], iq_mm3_10)
            d2 = interp1d(dur_iq_axis, dur_data[rails[i+1]], iq_mm3_10)
            t = (rail_10 - rails[i]) / (rails[i+1] - rails[i])
            return d1 + t * (d2 - d1)

# === WCZYTAJ LOG ===
def parse_log(filepath):
    data = []
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter=';')
        for row in reader:
            try:
                rpm = float(row['RPM(1/min)'].strip().replace(',','.'))
                vbcv = float(row['VBCV(%)'].strip().replace(',','.'))
                map_kpa = float(row['MAP.OBDII(kPa)'].strip().replace(',','.'))
                maf = float(row['MAF.OBDII(g/s)'].strip().replace(',','.'))
                torque = float(row['TORQUE(Nm)'].strip().replace(',','.'))
                frp_str = row['FRP.OBDII(kPa)'].strip().replace(',','.')
                frp = float(frp_str) if frp_str != '-' else 0
                if torque > 100 and rpm >= 1400:
                    data.append({'rpm':rpm,'vbcv':vbcv,'map':map_kpa,'maf':maf,'torque':torque,'frp':frp})
            except (ValueError, KeyError):
                continue
    return sorted(data, key=lambda x: x['rpm'])

log_po = parse_log(r'c:\Users\Dawi\Documents\MazdaEDC16C3\Logi_i_Analiza_N75\bieg 4 po modyfikacji.csv')

print("="*100)
print("ANALIZA KRZYZOWA: MAPY vs LOG 'PO MODYFIKACJI'")
print("="*100)

print(f"\n{'RPM':<6} | {'Torq LOG':<9} | {'NM Limit':<9} | {'IQ (mg)':<8} | {'Rail map':<9} | {'Rail LOG':<9} | {'MAP bar':<8} | {'MAF g/s':<8} | {'Air mg':<8} | {'Lambda':<7}")
print("-"*100)

last_rpm = 1300
for d in log_po:
    if d['rpm'] < last_rpm + 150:
        continue
    last_rpm = d['rpm']
    
    rpm = d['rpm']
    torque_log = d['torque']
    map_bar = d['map'] / 100.0
    maf_gs = d['maf']
    frp_log_bar = d['frp'] / 100.0  # FRP jest w kPa
    
    # 1. NM Limiter - jaki max moment na tych obrotach?
    nm_rpms = sorted(nm_limiter.keys())
    nm_max = interp1d(nm_rpms, [nm_limiter[r] for r in nm_rpms], rpm)
    
    # 2. NM to IQ - ile mg paliwa na ten moment?
    iq = lookup_nm_to_iq(rpm, torque_log)
    
    # 3. Rail Pressure - jakie cisnienie rail na te obroty i dawke?
    rail_map = lookup_rail(rpm, iq)
    
    # 4. Masa powietrza na suw
    strokes_per_sec = (rpm * 4) / (2 * 60)  # 4 cyl, 4-suwowy
    air_mg_per_stroke = (maf_gs * 1000) / strokes_per_sec if strokes_per_sec > 0 else 0
    
    # 5. Lambda
    afr = air_mg_per_stroke / iq if iq > 0 else 99
    lam = afr / 14.5
    
    print(f"{rpm:<6.0f} | {torque_log:<9.0f} | {nm_max:<9.1f} | {iq:<8.1f} | {rail_map:<9.0f} | {frp_log_bar:<9.0f} | {map_bar:<8.2f} | {maf_gs:<8.1f} | {air_mg_per_stroke:<8.0f} | {lam:<7.2f}")

# === ANALIZA DURATION DLA 1700 BAR ===
print("\n" + "="*100)
print("ANALIZA DURATION MAP DLA 1700 BAR (rozszerzenie)")
print("="*100)
print("Sprawdzam czy wartosci Duration dla 17000 (1700 bar) sa fizycznie poprawne")
print("Porownanie z sasiednimi ciesnieniami (skalowanie sqrt):\n")

print(f"{'IQ (0.1mm3)':<12} | {'Dur@1400bar':<12} | {'Dur@1700bar':<12} | {'Oczekiw@1700':<13} | {'Blad %':<8}")
print("-"*65)

for i, iq in enumerate(dur_iq_axis):
    if iq < 270:
        continue
    d_1400 = dur_data[14000][i]
    d_1700 = dur_data[17000][i]
    
    # Przy wyzszym cisnieniu czas powinien byc krotszy proporcjonalnie do sqrt(P)
    # Flow ~ sqrt(deltaP). Wiec Duration ~ IQ / Flow ~ IQ / sqrt(P)
    # Ratio = sqrt(1400/1700)
    ratio = math.sqrt(1400.0 / 1700.0)
    expected_1700 = d_1400 * ratio
    
    error_pct = ((d_1700 - expected_1700) / expected_1700 * 100) if expected_1700 > 0 else 0
    
    print(f"{iq:<12} | {d_1400:<12} | {d_1700:<12} | {expected_1700:<13.0f} | {error_pct:<+8.1f}%")

# === SPRAWDZENIE CZY TARGET 315NM JEST OSIAGALNY ===
print("\n" + "="*100)
print("CZY 315 NM JEST OSIAGALNE? Analiza po RPM")
print("="*100)

print(f"\n{'RPM':<6} | {'NM Limit':<9} | {'IQ@315Nm':<9} | {'Rail@IQ':<8} | {'Air@1.5bar':<11} | {'Lambda':<7} | {'Status'}")
print("-"*80)

for rpm in [1750, 2000, 2250, 2500, 2750, 3000, 3250]:
    nm_rpms = sorted(nm_limiter.keys())
    nm_max = interp1d(nm_rpms, [nm_limiter[r] for r in nm_rpms], rpm)
    
    target_nm = min(315, nm_max)
    iq = lookup_nm_to_iq(rpm, target_nm)
    rail = lookup_rail(rpm, iq)
    
    # Szacowana masa powietrza przy 1.5 bar boost (250 kPa MAP)
    # Uzyj formuly: air_mass = VE * Vd * rho_air * (MAP/P_atm) / n_cyl_per_rev
    # Uproszczenie: przy 250 kPa MAP, ~1010 mg/suw (z naszych obliczen)
    # Skalujemy liniowo z RPM (VE spada lekko z RPM)
    ve = 0.85 if rpm < 2500 else (0.82 if rpm < 3000 else 0.78)
    Vd = 1.56  # litry
    rho = 1.225  # kg/m3 przy 20C
    map_abs = 250  # kPa target
    air_per_stroke = ve * (Vd/4) * rho * (map_abs/101.325) * 1000  # mg
    
    afr = air_per_stroke / iq if iq > 0 else 99
    lam = afr / 14.5
    
    status = "OK" if nm_max >= 315 else f"LIMIT {nm_max:.0f}Nm!"
    if lam < 1.05:
        status += " BOGATO!"
    
    print(f"{rpm:<6} | {nm_max:<9.1f} | {iq:<9.1f} | {rail:<8.0f} | {air_per_stroke:<11.0f} | {lam:<7.2f} | {status}")
