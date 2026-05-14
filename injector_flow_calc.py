import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# NM Limiter
nm_limiter = {1000:143.3,1250:200.4,1500:275,1750:300,2000:325,2250:345,2500:350,2750:345,3000:329,3250:319,3500:309}

# NM_TO_IQ
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

# Rail Pressure
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

# Duration
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

def get_rail(rpm, iq_mm3):
    iq_val = min(iq_mm3 * 100, 4000) # Saturacja
    rpms = sorted(rail_data.keys())
    if rpm <= rpms[0]: return interp(rail_iq_axis, rail_data[rpms[0]], iq_val)
    if rpm >= rpms[-1]: return interp(rail_iq_axis, rail_data[rpms[-1]], iq_val)
    for i in range(len(rpms)-1):
        if rpms[i] <= rpm <= rpms[i+1]:
            v1 = interp(rail_iq_axis, rail_data[rpms[i]], iq_val)
            v2 = interp(rail_iq_axis, rail_data[rpms[i+1]], iq_val)
            t = (rpm - rpms[i]) / (rpms[i+1] - rpms[i])
            return v1 + t * (v2 - v1)

def get_duration(rail_bar, iq_mm3):
    rail_axis_val = rail_bar * 10
    iq_axis_val = iq_mm3 * 100
    rails = sorted(dur_table.keys())
    if rail_axis_val <= rails[0]: return interp(dur_iq_axis, dur_table[rails[0]], iq_axis_val)
    if rail_axis_val >= rails[-1]: return interp(dur_iq_axis, dur_table[rails[-1]], iq_axis_val)
    for i in range(len(rails)-1):
        if rails[i] <= rail_axis_val <= rails[i+1]:
            d1 = interp(dur_iq_axis, dur_table[rails[i]], iq_axis_val)
            d2 = interp(dur_iq_axis, dur_table[rails[i+1]], iq_axis_val)
            t = (rail_axis_val - rails[i]) / (rails[i+1] - rails[i])
            return d1 + t * (d2 - d1)

print("="*120)
print(f"{'OBLICZENIA FAKTYCZNEJ DAWKI I WYDAJNOSCI WTRYSKIWACZA WEDLUG MAP (WOT)':^120}")
print("="*120)
print(f"{'RPM':<6} | {'Max Nm':<8} | {'Zadane IQ':<10} | {'Zadane IQ':<10} | {'Cisnienie':<10} | {'Czas Wtr.':<10} | {'Wydajnosc':<10} | {'Zapotrz. paliwa':<15}")
print(f"{'':<6} | {'(z limit)':<8} | {'(mm3/suw)':<10} | {'(mg/suw)':<10} | {'Rail (bar)':<10} | {'(us)':<10} | {'(mm3/ms)':<10} | {'(litry/h)':<15}")
print("-" * 120)

for rpm in [1500, 1750, 2000, 2250, 2500, 2750, 3000, 3250, 3500]:
    # 1. NM Limiter
    nm_rpms = sorted(nm_limiter.keys())
    max_nm = interp(nm_rpms, [nm_limiter[r] for r in nm_rpms], rpm)
    
    # 2. Zadane IQ z NM_TO_IQ
    iq_mm3 = get_iq(rpm, max_nm)
    iq_mg = iq_mm3 * 0.835 # Gestosc ON
    
    # 3. Cisnienie Rail
    rail_bar = get_rail(rpm, iq_mm3)
    
    # 4. Czas wtrysku (Duration)
    dur_us = get_duration(rail_bar, iq_mm3)
    
    # 5. Wydajnosc wtryskiwacza (przeplyw)
    # Skoro ECU przez dur_us osiaga iq_mm3, to wydajnosc:
    flow_rate = iq_mm3 / (dur_us / 1000.0) if dur_us > 0 else 0
    
    # 6. Zapotrzebowanie w l/h
    # (iq_mm3 [mm3/suw] * 2 suwy na obrot * rpm) / 1000000 = l/min
    # * 60 = l/h
    fuel_lh = (iq_mm3 * 2 * rpm * 60) / 1000000.0
    
    print(f"{rpm:<6} | {max_nm:<8.1f} | {iq_mm3:<10.1f} | {iq_mg:<10.1f} | {rail_bar:<10.0f} | {dur_us:<10.0f} | {flow_rate:<10.2f} | {fuel_lh:<15.2f}")

print("-" * 120)
print("\nOBJAŚNIENIA:")
print("1. Zadane IQ (mm3/suw) - Ilość paliwa jaką ECU chce wtrysnąć, wyliczona z mapy NM_TO_IQ dla limitu momentu.")
print("2. Zadane IQ (mg/suw)  - Masa paliwa (przyjęto gęstość ON = 0.835 kg/l).")
print("3. Czas Wtr. (us)      - Wyliczony czas otwarcia wtryskiwacza z mapy Duration dla zadanego IQ i ciśnienia Rail.")
print("4. Wydajnosc (mm3/ms)  - Faktyczny przepływ wtryskiwacza przy danym ciśnieniu. Widać jak przepływ rośnie wraz ze wzrostem ciśnienia (z ok 36 mm3/ms do 49 mm3/ms).")
print("5. Zapotrz. (litry/h)  - Teoretyczne spalanie chwilowe silnika przy maksymalnym obciążeniu (WOT).")
