import csv

file_przed = r'c:\Users\Dawi\Documents\MazdaEDC16C3\bieg 4 przed modyfikacja.csv'
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
                
                if not rpm_str or not vbcv_str or not map_str or rpm_str == '-' or vbcv_str == '-' or map_str == '-':
                    continue
                
                rpm = float(rpm_str)
                vbcv = float(vbcv_str)
                map_val = float(map_str)
                
                # Zbierz próbki wokół interesującego przedziału
                if 1500 <= rpm <= 1800:
                    data.append({
                        'rpm': rpm,
                        'vbcv': vbcv,
                        'map': map_val
                    })
            except (ValueError, KeyError):
                continue
    return data

data_przed = sorted(parse_log(file_przed), key=lambda x: x['rpm'])
data_po = sorted(parse_log(file_po), key=lambda x: x['rpm'])

print("=== LOG PO MODYFIKACJI (1500 - 1800 RPM) ===")
print("RPM      | MAP (kPa) | MAP (bar) | VBCV (%)")
for d in data_po:
    map_bar = d['map'] / 100.0  # 100 kPa = 1 bar (absolutne)
    print(f"{d['rpm']:<8} | {d['map']:<9.0f} | {map_bar:<9.2f} | {d['vbcv']:.2f}")

print("\n=== LOG PRZED MODYFIKACJĄ (1500 - 1800 RPM) ===")
print("RPM      | MAP (kPa) | MAP (bar) | VBCV (%)")
for d in data_przed:
    map_bar = d['map'] / 100.0
    print(f"{d['rpm']:<8} | {d['map']:<9.0f} | {map_bar:<9.2f} | {d['vbcv']:.2f}")

