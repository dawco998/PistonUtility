import sys, io, math
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# ============================================================
# SOI Z DOCELOWYM EOI - Mazda 1.6 MZ-CD (DV6TED4) / EDC16C3
# Uwzglednia: Duration map, Rail map, Injector delay, NM Limiter,
#             oryginalny SOI, dane z logu WOT
# ============================================================

comp_ratio = 18.0

# --- ORYGINALNY SOI (z generate_final_maps.py) ---
# Osie: RPM vs IQ (mg/cyc)
ori_soi_rpms = [600,750,1000,1250,1500,1750,2000,2250,2500,2750,3000,3250,3500,3750,4000,4500]
ori_soi_iqs = [0.0,1.7,3.0,5.1,6.8,8.5,9.5,11.0,12.9,14.6,18.0,21.4,24.8,31.4,38.0,50.0]
ori_soi = [
    [-0.23,-0.21,0.07,-0.49,-0.09,0,0,0,1.01,1.99,1.99,1.99,1.01,1.01,0,0],
    [-0.23,-0.21,0.07,-0.80,-0.21,0,0,0,1.01,1.99,1.99,1.99,1.01,1.01,0,0],
    [0.91,0.77,-0.33,-1.80,-1.20,-0.61,-0.09,0,1.01,1.99,1.99,1.99,0.49,0,0,0],
    [1.52,1.50,-1.80,-2.41,-1.62,-0.70,0.09,1.01,1.57,1.99,1.99,2.32,2.48,2.51,2.51,2.51],
    [1.52,1.50,-1.71,-2.02,-1.03,0.07,0.68,1.41,1.71,1.90,1.99,2.39,2.48,2.79,3.28,3.28],
    [1.17,1.12,-0.96,-1.62,-0.61,0.59,1.29,2.11,2.70,2.79,2.91,3.30,3.61,3.40,3.49,3.49],
    [0.80,0.75,0.23,-1.10,-0.09,1.10,2.11,3.21,3.98,4.38,4.71,4.90,5.11,4.71,5.60,5.60],
    [1.29,0.89,1.22,0.42,1.10,2.11,3.09,4.10,5.11,5.51,6.00,6.70,7.20,7.41,7.71,7.71],
    [2.30,2.39,2.55,2.39,3.00,3.89,4.71,5.93,6.94,7.41,7.99,9.00,9.61,10.10,10.10,10.10],
    [3.14,3.45,3.70,3.89,4.71,5.39,6.30,7.52,8.32,9.02,9.49,10.52,11.02,11.30,10.20,10.20],
    [6.07,6.66,6.96,7.05,7.36,7.80,8.53,9.23,9.54,10.05,10.59,11.04,11.44,11.79,12.61,12.61],
    [7.03,7.52,8.09,8.27,8.70,9.54,10.20,10.76,11.11,11.81,12.37,12.91,13.57,14.27,16.20,16.20],
    [7.31,7.87,8.77,9.05,9.66,10.55,11.46,11.88,12.37,13.05,13.64,14.34,15.30,16.50,18.00,18.00],
    [6.75,7.52,8.58,9.21,10.01,10.95,11.79,12.33,12.96,13.69,14.27,15.02,16.43,18.70,20.09,20.09],
    [6.19,7.15,8.41,9.35,10.36,11.34,12.09,12.75,13.57,14.32,14.91,15.70,17.53,20.88,22.19,22.19],
    [6.70,7.73,9.21,9.68,11.13,12.07,13.03,13.85,14.79,15.73,16.43,17.20,19.92,25.27,26.51,26.51],
]

# --- NM LIMITER (z mapy ECU) ---
nm_limiter = {1000:143.3,1250:200.4,1500:275,1750:300,2000:325,2250:345,
              2500:350,2750:345,3000:329,3250:319,3500:309,3750:298,4000:285,4250:280}

# --- LOG WOT (tylko jako ref dla boost/rail) ---
log_wot = {
    1500: {'map_kpa':210,'rail':1023}, 1750: {'map_kpa':230,'rail':1186},
    2000: {'map_kpa':241,'rail':1328}, 2250: {'map_kpa':238,'rail':1398},
    2500: {'map_kpa':244,'rail':1477}, 2750: {'map_kpa':245,'rail':1540},
    3000: {'map_kpa':245,'rail':1602}, 3250: {'map_kpa':251,'rail':1678},
    3500: {'map_kpa':249,'rail':1689},
}

# --- MAPY ECU ---
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
rail_iq_axis = [0,170,340,680,850,1020,1190,1360,1550,1840,2280,3000,3300,3500,3700,4000]
rail_data = {
    1500: [350,395,438,540,631,683,735,806,808,786,783,806,844,884,924,1050],
    1750: [377,427,473,580,651,711,760,848,867,858,874,870,912,986,1042,1225],
    2000: [402,450,493,592,647,723,770,856,881,916,958,944,988,1064,1120,1337],
    2250: [415,450,480,565,627,721,775,864,904,957,1019,1020,1071,1146,1199,1420],
    2500: [418,441,468,539,613,686,761,867,921,992,1076,1111,1166,1235,1281,1477],
    2750: [418,432,459,517,582,634,726,851,931,1021,1116,1160,1241,1312,1357,1550],
    3000: [395,407,417,471,524,540,605,788,925,1013,1104,1169,1251,1347,1419,1600],
    3250: [395,405,415,453,466,478,543,723,869,985,1044,1141,1226,1347,1444,1660],
    3500: [396,406,416,433,444,454,515,688,841,986,1044,1130,1221,1336,1451,1700],
}
dur_iq_axis = [0,70,120,150,180,220,270,320,400,600,1000,1400,1800,2200,2500,2800,3100,3400,3600,3800,4000,4400,5000,7000]
dur_table = {
    1190:[0]*24, 1200:[0,651,802,879,939,1018,1107,1192,1313,1588,2036,2412,2782,3250,3673,4126,4579,5033,5335,5637,5939,6543,8000,8000],
    2000:[0,390,481,527,563,611,664,715,788,953,1222,1447,1658,1942,2204,2476,2748,3020,3201,3382,3563,3926,4470,6168],
    2500:[0,297,383,414,444,501,538,574,632,767,999,1191,1380,1567,1777,2013,2246,2479,2634,2790,2945,3256,3722,5136],
    3000:[0,270,334,367,391,421,462,508,553,659,857,1036,1201,1362,1499,1717,1921,2120,2252,2384,2516,2781,3177,4384],
    4000:[0,260,270,305,334,357,379,403,453,542,683,828,959,1086,1202,1355,1515,1687,1802,1919,2036,2269,2620,3615],
    5000:[0,245,245,260,289,318,346,365,389,467,588,708,821,925,1003,1129,1284,1424,1519,1624,1729,1939,2255,3111],
    6000:[0,225,225,225,255,290,320,339,362,415,523,621,724,816,878,954,1115,1247,1327,1409,1513,1698,1977,2728],
    7000:[0,220,220,220,231,270,300,322,345,385,486,575,667,751,806,863,972,1120,1200,1265,1342,1519,1755,2421],
    8000:[0,215,215,215,222,256,287,311,335,372,463,545,631,710,761,810,881,1017,1103,1176,1237,1385,1640,2263],
    9000:[0,210,210,210,212,240,276,300,324,361,444,522,604,677,726,770,833,928,1022,1098,1164,1282,1510,2083],
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
    return y_arr[-1]

def interp2d_rpm(data, rpms_sorted, rpm, x_axis, x_val):
    if rpm <= rpms_sorted[0]: return interp(x_axis, data[rpms_sorted[0]], x_val)
    if rpm >= rpms_sorted[-1]: return interp(x_axis, data[rpms_sorted[-1]], x_val)
    for i in range(len(rpms_sorted)-1):
        if rpms_sorted[i] <= rpm <= rpms_sorted[i+1]:
            v1 = interp(x_axis, data[rpms_sorted[i]], x_val)
            v2 = interp(x_axis, data[rpms_sorted[i+1]], x_val)
            t = (rpm - rpms_sorted[i]) / (rpms_sorted[i+1] - rpms_sorted[i])
            return v1 + t * (v2 - v1)

def get_iq(rpm, nm): return interp2d_rpm(iq_rows, sorted(iq_rows), rpm, nm_axis, nm*10)
def get_rail(rpm, iq_mm3): return interp2d_rpm(rail_data, sorted(rail_data), rpm, rail_iq_axis, min(iq_mm3*100,4000))

def get_duration(rail_bar, iq_mm3):
    rails = sorted(dur_table.keys())
    # Os Rail Duration = bar * 10
    rv = rail_bar * 10
    if rv <= rails[0]: return interp(dur_iq_axis, dur_table[rails[0]], iq_mm3*100)
    if rv >= rails[-1]: return interp(dur_iq_axis, dur_table[rails[-1]], iq_mm3*100)
    for i in range(len(rails)-1):
        if rails[i] <= rv <= rails[i+1]:
            d1 = interp(dur_iq_axis, dur_table[rails[i]], iq_mm3*100)
            d2 = interp(dur_iq_axis, dur_table[rails[i+1]], iq_mm3*100)
            t = (rv - rails[i]) / (rails[i+1] - rails[i])
            return d1 + t * (d2 - d1)

def inj_delay_us(rail_bar):
    return max(180, min(400 - 0.12*rail_bar, 400))

def ign_delay(rpm, rail_bar, map_kpa, iat_C=40):
    T_K = 273.15 + iat_C
    T_comp = T_K * (comp_ratio ** 0.35)
    tau_ms = max(0.25, min(0.8 * math.exp(-0.0008*(rail_bar-800)) * (800/T_comp)**1.2, 1.5))
    return tau_ms, tau_ms * rpm * 6.0 / 1000.0

def get_ori_soi_at_wot(rpm, iq_mm3):
    """Odczytaj oryginalny SOI dla danego RPM i IQ (mm3 ~ mg w tej mapie)"""
    iq_mg = iq_mm3 * 0.835  # mapa SOI jest vs mg/cyc
    r_idx = ori_soi_rpms
    if rpm <= r_idx[0]: row_vals = ori_soi[0]
    elif rpm >= r_idx[-1]: row_vals = ori_soi[-1]
    else:
        for i in range(len(r_idx)-1):
            if r_idx[i] <= rpm <= r_idx[i+1]:
                v1 = interp(ori_soi_iqs, ori_soi[i], iq_mg)
                v2 = interp(ori_soi_iqs, ori_soi[i+1], iq_mg)
                t = (rpm - r_idx[i]) / (r_idx[i+1] - r_idx[i])
                return v1 + t * (v2 - v1)
    return interp(ori_soi_iqs, row_vals, iq_mg)

# ============================================================
print("=" * 130)
print("SOI OBLICZONY OD EOI - z NM Limiter i oryginalnym SOI")
print("Mazda 1.6 MZ-CD / EDC16C3 / WOT")
print("=" * 130)

# --- SEKCJA 1: Co daje oryginalny SOI w kontekscie EOI? ---
print("\n" + "─"*130)
print("  1. ORYGINALNY SOI -> jaki EOI z tego wychodzi?")
print("─"*130)
print(f"{'RPM':<6}|{'NmLim':<6}|{'IQ mm3':<7}|{'Rail map':<9}|{'Rail log':<9}|{'Ori SOI':<8}|{'Dur us':<7}|{'InjDel':<7}|{'Tot deg':<8}|{'EOI ori':<10}|{'Ocena'}")
print("-"*105)

for rpm in [1500,1750,2000,2250,2500,2750,3000,3250,3500]:
    nm_rpms = sorted(nm_limiter.keys())
    nm_max = interp(nm_rpms, [nm_limiter[r] for r in nm_rpms], rpm)
    iq = get_iq(rpm, nm_max)
    rail_map = get_rail(rpm, iq)
    rail_log = log_wot.get(rpm, {}).get('rail', rail_map)
    rail = rail_log  # uzyj realnego rail z logu
    
    ori_soi_val = get_ori_soi_at_wot(rpm, iq)
    dur_us = get_duration(rail, iq)
    inj_del = inj_delay_us(rail)
    total_deg = (dur_us + inj_del) * rpm * 6.0 / 1e6
    
    eoi_pos = -ori_soi_val + total_deg  # ATDC
    ocena = "OK" if 5 <= eoi_pos <= 25 else ("WCZESNE" if eoi_pos < 5 else "POZNE!")
    eoi_str = f"{eoi_pos:.1f} ATDC"
    
    print(f"{rpm:<6}|{nm_max:<6.0f}|{iq:<7.1f}|{rail_map:<9.0f}|{rail_log:<9}|{ori_soi_val:<8.1f}|{dur_us:<7.0f}|{inj_del:<7.0f}|{total_deg:<8.1f}|{eoi_str:<10}|{ocena}")

# --- SEKCJA 2: SOI z PCP target ---
print("\n" + "─"*130)
print("  2. SOI z PCP target (10 ATDC) -> EOI wynikowy")
print("─"*130)

for pcp_tgt, label in [(10,"AGRESYWNY BALANS"),(12,"BEZPIECZNY")]:
    print(f"\n  PCP target: {pcp_tgt} ATDC - {label}")
    print(f"  {'RPM':<6}|{'NmLim':<6}|{'IQ':<6}|{'Rail':<6}|{'ID deg':<7}|{'SOI':<7}|{'Dur+Del':<8}|{'EOI':<10}|{'vs Ori SOI':<11}|{'Ocena'}")
    print("  "+"-"*90)
    
    for rpm in [1500,1750,2000,2250,2500,2750,3000,3250,3500]:
        nm_rpms = sorted(nm_limiter.keys())
        nm_max = interp(nm_rpms, [nm_limiter[r] for r in nm_rpms], rpm)
        iq = get_iq(rpm, nm_max)
        rail = log_wot.get(rpm,{}).get('rail', get_rail(rpm,iq))
        map_kpa = log_wot.get(rpm,{}).get('map_kpa', 240)
        
        id_ms, id_deg = ign_delay(rpm, rail, map_kpa)
        burn_dur = 22 + 0.005*rpm
        soi = id_deg + burn_dur*0.35 - pcp_tgt
        
        dur_us = get_duration(rail, iq)
        total_deg = (dur_us + inj_delay_us(rail)) * rpm * 6.0 / 1e6
        eoi = -soi + total_deg
        
        ori = get_ori_soi_at_wot(rpm, iq)
        diff = soi - ori
        ocena = "OK" if 5 <= eoi <= 25 else ("WCZESNE" if eoi<5 else "POZNE!")
        
        print(f"  {rpm:<6}|{nm_max:<6.0f}|{iq:<6.1f}|{rail:<6}|{id_deg:<7.1f}|{soi:<7.1f}|{total_deg:<8.1f}|{eoi:<10.1f}|{diff:<+11.1f}|{ocena}")

# --- SEKCJA 3: Iteracyjne - EOI target z PCP clamp ---
print("\n" + "="*130)
print("  3. FINALNA MAPA: EOI target z ograniczeniem PCP >= 8 ATDC")
print("="*130)

eoi_targets = {1500:12, 1750:11, 2000:10, 2250:9, 2500:8, 2750:7, 3000:6, 3250:5.5, 3500:5}
MIN_PCP = 8.0

print(f"\n{'RPM':<6}|{'NmLim':<6}|{'IQ':<6}|{'Rail':<6}|{'ID':<5}|{'Burn35':<7}|{'Dur+Del':<8}|{'EOI cel':<8}|{'SOI eoi':<8}|{'PCP':<6}|{'SOI fin':<8}|{'EOI fin':<9}|{'Ori SOI':<8}|{'Zmiana'}")
print("-"*120)

final = {}
for rpm in [1500,1750,2000,2250,2500,2750,3000,3250,3500]:
    nm_rpms = sorted(nm_limiter.keys())
    nm_max = interp(nm_rpms, [nm_limiter[r] for r in nm_rpms], rpm)
    iq = get_iq(rpm, nm_max)
    rail = log_wot.get(rpm,{}).get('rail', get_rail(rpm,iq))
    map_kpa = log_wot.get(rpm,{}).get('map_kpa', 240)
    
    id_ms, id_deg = ign_delay(rpm, rail, map_kpa)
    burn35 = (22 + 0.005*rpm) * 0.35
    
    dur_us = get_duration(rail, iq)
    tot_deg = (dur_us + inj_delay_us(rail)) * rpm * 6.0 / 1e6
    
    eoi_cel = eoi_targets[rpm]
    soi_eoi = tot_deg - eoi_cel
    pcp_eoi = -soi_eoi + id_deg + burn35
    
    soi_max = id_deg + burn35 - MIN_PCP
    
    if pcp_eoi >= MIN_PCP:
        soi_fin = soi_eoi; eoi_fin = eoi_cel
    else:
        soi_fin = soi_max; eoi_fin = -soi_fin + tot_deg
    
    ori = get_ori_soi_at_wot(rpm, iq)
    diff = soi_fin - ori
    
    final[rpm] = {'soi': round(soi_fin,1), 'eoi': round(eoi_fin,1), 'ori': round(ori,1), 'nm': nm_max, 'iq': iq}
    
    print(f"{rpm:<6}|{nm_max:<6.0f}|{iq:<6.1f}|{rail:<6}|{id_deg:<5.1f}|{burn35:<7.1f}|{tot_deg:<8.1f}|{eoi_cel:<8.1f}|{soi_eoi:<8.1f}|{pcp_eoi:<6.1f}|{soi_fin:<8.1f}|{eoi_fin:<9.1f}|{ori:<8.1f}|{diff:<+.1f}")

# --- PODSUMOWANIE ---
print("\n" + "="*130)
print("FINALNA MAPA SOI (deg BTDC)")
print("="*130)
print()
print("RPM:      " + "  |  ".join([str(r) for r in sorted(final)]))
print("NM Limit: " + "  |  ".join([f"{final[r]['nm']:5.0f}" for r in sorted(final)]))
print("IQ mm3:   " + "  |  ".join([f"{final[r]['iq']:5.1f}" for r in sorted(final)]))
print("Ori SOI:  " + "  |  ".join([f"{final[r]['ori']:5.1f}" for r in sorted(final)]))
print("NOWY SOI: " + "  |  ".join([f"{final[r]['soi']:5.1f}" for r in sorted(final)]))
print("EOI:      " + "  |  ".join([f"{final[r]['eoi']:5.1f}" for r in sorted(final)]))

print("""
WNIOSKI:
  - Oryginalny SOI to 1.5-18 deg BTDC (rosnie z RPM i IQ)
  - Przy pelnym NM Limiter (275-350 Nm), dawki to 46-67 mm3
  - Duration przy tych dawkach to 900-1350 us = 14-25 deg CA
  - EOI ~12 ATDC @ 1500 jest osiagalny (SOI ~2 BTDC)
  - EOI ~0 ATDC @ 3500 jest NIEMOZLIWY (wymagalby SOI 23 BTDC = PCP BTDC!)
  - Realny minimalny EOI @ 3500 to ~10 ATDC (z PCP >= 8 ATDC)
  
OPCJE na nizszy EOI:
  1. Podniesc Rail Pressure powyzej wartosci z logu -> krotszy Duration
  2. Zmniejszyc NM Limiter na gorze -> mniejsza dawka -> krotszy Duration
  3. Piezo wtryskiwacze -> krotszy delay (~100us vs ~200us)
""")
