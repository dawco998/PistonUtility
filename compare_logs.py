import csv

file_przed = r'c:\Users\Dawi\Documents\MazdaEDC16C3\bieg 4 przed modyfikacja.csv'
file_po = r'c:\Users\Dawi\Documents\MazdaEDC16C3\bieg 4 po modyfikacji.csv'

def parse_log(filepath):
    data = []
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter=';')
        
        for row in reader:
            try:
                # Oczyszczanie wartości (np. usuwanie znaków spacji)
                rpm_str = row['RPM(1/min)'].strip().replace(',', '.')
                vbcv_str = row['VBCV(%)'].strip().replace(',', '.')
                map_str = row['MAP.OBDII(kPa)'].strip().replace(',', '.')
                maf_str = row['MAF.OBDII(g/s)'].strip().replace(',', '.')
                torque_str = row['TORQUE(Nm)'].strip().replace(',', '.')
                
                # Pomiń wiersze bez danych
                if not rpm_str or not vbcv_str or not map_str or rpm_str == '-' or vbcv_str == '-' or map_str == '-':
                    continue
                
                rpm = float(rpm_str)
                vbcv = float(vbcv_str)
                map_val = float(map_str)
                maf = float(maf_str) if maf_str != '-' else 0.0
                torque = float(torque_str) if torque_str != '-' else 0.0
                
                # Tylko pełne obciążenie ("but") i obroty od 1000
                if torque > 100 and rpm >= 1000:
                    data.append({
                        'rpm': rpm,
                        'vbcv': vbcv,
                        'map': map_val,
                        'maf': maf,
                        'torque': torque
                    })
            except (ValueError, KeyError) as e:
                continue
    return data

data_przed = parse_log(file_przed)
data_po = parse_log(file_po)

def calc_stats_in_range(data, r_min, r_max):
    filtered = [d for d in data if r_min <= d['rpm'] <= r_max]
    if not filtered:
        return {'vbcv': 0, 'map': 0, 'maf': 0, 'count': 0}
    
    n = len(filtered)
    return {
        'vbcv': sum(d['vbcv'] for d in filtered) / n,
        'map': sum(d['map'] for d in filtered) / n,
        'maf': sum(d['maf'] for d in filtered) / n,
        'count': n
    }

stats_przed = calc_stats_in_range(data_przed, 1750, 2000)
stats_po = calc_stats_in_range(data_po, 1750, 2000)

print("\n--- Analiza przedziału 1750 - 2000 RPM ---")
print(f"Ilość próbek przed: {stats_przed['count']}, po: {stats_po['count']}")
if stats_przed['count'] > 0 and stats_po['count'] > 0:
    print("\nŚrednie wysterowanie N75 (VBCV %):")
    print(f"  Przed: {stats_przed['vbcv']:.2f} %")
    print(f"  Po:    {stats_po['vbcv']:.2f} %")
    print(f"  Różnica: {stats_po['vbcv'] - stats_przed['vbcv']:.2f} %")

    print("\nŚrednie ciśnienie doładowania MAP (kPa):")
    print(f"  Przed: {stats_przed['map']:.2f} kPa")
    print(f"  Po:    {stats_po['map']:.2f} kPa")
    print(f"  Różnica: {stats_po['map'] - stats_przed['map']:.2f} kPa")

    print("\nŚredni przepływ MAF (g/s):")
    print(f"  Przed: {stats_przed['maf']:.2f} g/s")
    print(f"  Po:    {stats_po['maf']:.2f} g/s")
    print(f"  Różnica: {stats_po['maf'] - stats_przed['maf']:.2f} g/s")

# Dodatkowo podgląd w binach co 50 rpm (np. 1750, 1800, 1850 itd.)
print("\n--- Szczegóły co 50 RPM (1700 - 2050) ---")
print(f"{'RPM':<10} | {'VBCV Przed':<12} | {'VBCV Po':<12} | {'MAP Przed':<12} | {'MAP Po':<12}")
print("-" * 65)

for rpm_bin in range(1700, 2100, 50):
    bin_min = rpm_bin
    bin_max = rpm_bin + 50
    st_przed = calc_stats_in_range(data_przed, bin_min, bin_max)
    st_po = calc_stats_in_range(data_po, bin_min, bin_max)
    
    if st_przed['count'] > 0 and st_po['count'] > 0:
        print(f"{bin_min}-{bin_max:<4} | {st_przed['vbcv']:>10.2f} % | {st_po['vbcv']:>10.2f} % | {st_przed['map']:>7.0f} kPa | {st_po['map']:>7.0f} kPa")

