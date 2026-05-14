import csv, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

data = []
with open(r'c:\Users\Dawi\Documents\MazdaEDC16C3\Logi_i_Analiza_N75\bieg 4 po modyfikacji.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f, delimiter=';')
    for row in reader:
        try:
            rpm = float(row['RPM(1/min)'].strip().replace(',','.'))
            torque = float(row['TORQUE(Nm)'].strip().replace(',','.'))
            map_kpa = float(row['MAP.OBDII(kPa)'].strip().replace(',','.'))
            frp_str = row['FRP.OBDII(kPa)'].strip().replace(',','.')
            frp = float(frp_str) if frp_str != '-' else 0
            if torque > 100 and rpm >= 1400 and frp > 0:
                data.append({'rpm':rpm, 'torque':torque, 'map':map_kpa, 'frp_bar': frp/100.0})
        except (ValueError, KeyError):
            continue

data.sort(key=lambda x: x['rpm'])
last = 1300
for d in data:
    if d['rpm'] < last + 100:
        continue
    last = d['rpm']
    boost = d['map']/100.0 - 1.01325
    print(f"RPM={d['rpm']:.0f}  Torq={d['torque']:.0f}Nm  MAP={d['map']:.0f}kPa (boost={boost:.2f}bar)  Rail={d['frp_bar']:.0f}bar")
