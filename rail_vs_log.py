import csv, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# NM_TO_IQ: os NM = Nm*10, wartosci = mm3/suw
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
}

# Rail Pressure: os IQ = mm3/suw * 100
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
    iq_axis_val = iq_mm3 * 100
    rpms = sorted(rail_data.keys())
    if rpm <= rpms[0]: return interp(rail_iq_axis, rail_data[rpms[0]], iq_axis_val)
    if rpm >= rpms[-1]: return interp(rail_iq_axis, rail_data[rpms[-1]], iq_axis_val)
    for i in range(len(rpms)-1):
        if rpms[i] <= rpm <= rpms[i+1]:
            v1 = interp(rail_iq_axis, rail_data[rpms[i]], iq_axis_val)
            v2 = interp(rail_iq_axis, rail_data[rpms[i+1]], iq_axis_val)
            t = (rpm - rpms[i]) / (rpms[i+1] - rpms[i])
            return v1 + t * (v2 - v1)

# Wczytaj log
def parse_log(filepath):
    data = []
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter=';')
        for row in reader:
            try:
                rpm = float(row['RPM(1/min)'].strip().replace(',','.'))
                torque = float(row['TORQUE(Nm)'].strip().replace(',','.'))
                frp_str = row['FRP.OBDII(kPa)'].strip().replace(',','.')
                frp = float(frp_str) if frp_str != '-' else 0
                if torque > 100 and rpm >= 1400 and frp > 0:
                    data.append({'rpm':rpm, 'torque':torque, 'frp_bar': frp/100.0})
            except (ValueError, KeyError):
                continue
    return sorted(data, key=lambda x: x['rpm'])

log = parse_log(r'c:\Users\Dawi\Documents\MazdaEDC16C3\Logi_i_Analiza_N75\bieg 4 po modyfikacji.csv')

print("POROWNANIE: Rail Pressure z MAPY vs Rail Pressure z LOGU")
print("="*95)
print(f"{'RPM':<6} | {'Torque':<7} | {'IQ mm3':<8} | {'IQ>40?':<7} | {'Rail MAPA':<10} | {'Rail LOG':<10} | {'Roznica':<10} | {'Trafione?'}")
print("-"*95)

last_rpm = 1300
for d in log:
    if d['rpm'] < last_rpm + 100:
        continue
    last_rpm = d['rpm']
    
    rpm = d['rpm']
    torque = d['torque']
    frp_log = d['frp_bar']
    
    iq = get_iq(rpm, torque)
    rail_map = get_rail(rpm, iq)
    
    przekr = "TAK" if iq > 40 else "nie"
    diff = frp_log - rail_map
    diff_pct = (diff / rail_map * 100) if rail_map > 0 else 0
    ok = "OK" if abs(diff_pct) < 5 else ("ZA DUZO" if diff > 0 else "ZA MALO")
    
    print(f"{rpm:<6.0f} | {torque:<7.0f} | {iq:<8.1f} | {przekr:<7} | {rail_map:<10.0f} | {frp_log:<10.0f} | {diff:>+7.0f} ({diff_pct:>+5.1f}%) | {ok}")

# Teraz pokaz co daje ostatnia kolumna (saturacja) vs log
print()
print("="*95)
print("SATURACJA: Czy ECU uzywa ostatniej kolumny (IQ=40mm3) dla wyzszych dawek?")
print("="*95)
print()

print(f"{'RPM':<6} | {'IQ mm3':<8} | {'Rail@40mm3':<11} | {'Rail LOG':<10} | {'Roznica':<12} | {'Wniosek'}")
print("-"*75)

last_rpm = 1300
for d in log:
    if d['rpm'] < last_rpm + 100:
        continue
    last_rpm = d['rpm']
    
    rpm = d['rpm']
    torque = d['torque']
    frp_log = d['frp_bar']
    
    iq = get_iq(rpm, torque)
    
    if iq <= 40:
        continue  # tylko dawki przekraczajace mape
    
    # Wartosc z ostatniej kolumny (saturacja na 40 mm3)
    rail_sat = get_rail(rpm, 40.0)
    
    diff = frp_log - rail_sat
    diff_pct = (diff / rail_sat * 100) if rail_sat > 0 else 0
    
    wniosek = "SATURUJE" if abs(diff_pct) < 5 else "INNA LOGIKA"
    
    print(f"{rpm:<6.0f} | {iq:<8.1f} | {rail_sat:<11.0f} | {frp_log:<10.0f} | {diff:>+7.0f} ({diff_pct:>+5.1f}%) | {wniosek}")
