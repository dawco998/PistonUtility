import csv

file_po = r'c:\Users\Dawi\Documents\MazdaEDC16C3\bieg 4 po modyfikacji.csv'
file_przed = r'c:\Users\Dawi\Documents\MazdaEDC16C3\bieg 4 przed modyfikacja.csv'

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
                
                if not rpm_str or not vbcv_str or not map_str or rpm_str == '-' or torque_str == '-': continue
                
                rpm = float(rpm_str)
                torque = float(torque_str)
                if torque > 100 and 2000 <= rpm <= 3500:
                    data.append({'rpm': rpm, 'vbcv': float(vbcv_str), 'map': float(map_str)/100.0})
            except (ValueError, KeyError):
                continue
    return sorted(data, key=lambda x: x['rpm'])

def get_closest(data, rpm_target):
    # Find the row with the closest RPM
    return min(data, key=lambda x: abs(x['rpm'] - rpm_target))

d_po = parse_log(file_po)
d_przed = parse_log(file_przed)

print(f"{'RPM':<6} | {'MAP Przed':<10} | {'MAP Po':<10} | {'VBCV Przed':<12} | {'VBCV Po':<12}")
for rpm in range(2000, 3500, 150):
    p1 = get_closest(d_przed, rpm)
    p2 = get_closest(d_po, rpm)
    print(f"{rpm:<6} | {p1['map']:<10.2f} | {p2['map']:<10.2f} | {p1['vbcv']:<12.2f} | {p2['vbcv']:<12.2f}")
