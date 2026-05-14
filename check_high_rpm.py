import csv

file_po = r'c:\Users\Dawi\Documents\MazdaEDC16C3\bieg 4 po modyfikacji.csv'

def parse_log(filepath):
    data = []
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter=';')
        
        for row in reader:
            try:
                rpm_str = row['RPM(1/min)'].strip().replace(',', '.')
                vbcv_str = row['VBCV(%)'].strip().replace(',', '.')
                map_str = row['MAP.OBDII(kPa)'].strip().replace(',', '.')
                torque_str = row['TORQUE(Nm)'].strip().replace(',', '.')
                
                if not rpm_str or not vbcv_str or not map_str or rpm_str == '-' or torque_str == '-':
                    continue
                
                rpm = float(rpm_str)
                vbcv = float(vbcv_str)
                map_val = float(map_str)
                torque = float(torque_str)
                
                if torque > 100 and 2000 <= rpm <= 4500:
                    data.append({
                        'rpm': rpm,
                        'vbcv': vbcv,
                        'map': map_val
                    })
            except (ValueError, KeyError):
                continue
    return data

data_po = sorted(parse_log(file_po), key=lambda x: x['rpm'])

print("RPM      | MAP (bar) | VBCV (%)")
last_rpm = 1900
for d in data_po:
    if d['rpm'] >= last_rpm + 100:
        map_bar = d['map'] / 100.0
        print(f"{d['rpm']:<8.0f} | {map_bar:<9.2f} | {d['vbcv']:.2f}")
        last_rpm = d['rpm']
