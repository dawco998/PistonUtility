import sys, io, math
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Dane z ECU
nm_limiter = {1000:143.3,1250:200.4,1500:275,1750:300,2000:325,2250:345,
              2500:350,2750:345,3000:329,3250:319,3500:309,3750:298,4000:285}

# Prawidlowe ORI SOI z pliku dla WOT (IQ 38 i 50)
ori_soi = {
    1000: 0.00,
    1250: 2.51,
    1500: 3.28,
    1750: 3.49,
    2000: 5.60,
    2250: 7.71,
    2500: 10.10,
    2750: 10.20,
    3000: 12.61,
    3250: 16.20,
    3500: 18.00,
    3750: 20.09,
    4000: 22.19,
    4500: 26.51
}

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
    3750: [0,2.26,4.17,6.3,8.41,12.3,18.03,22.17,26.41,31.34,35.06,39.95,44.77,54,61.89,74.2], # duplicated 3500
    4000: [0,2.3,4.89,7.38,10.13,14.18,17.43,22.32,27.07,31.82,36.5,41.36,46.3,55.72,63.69,76.3],
    4500: [0,2.33,4.34,7.42,9.32,13.65,18.86,25.38,28.9,32.92,37.82,42.81,48.01,56.46,64.57,77.4]
}

rail_by_rpm = {1000:600, 1250:800, 1500:1050, 1750:1225, 2000:1337, 2250:1420,
               2500:1477, 2750:1550, 3000:1600, 3250:1660, 3500:1700, 3750:1700, 4000:1700, 4500:1700}

dur_iq_axis = [0,70,120,150,180,220,270,320,400,600,1000,1400,1800,2200,2500,2800,3100,3400,3600,3800,4000,4400,5000,7000]
dur_table = {
    6000:[0,225,225,225,255,290,320,339,362,415,523,621,724,816,878,954,1115,1247,1327,1409,1513,1698,1977,2728],
    8000:[0,215,215,215,222,256,287,311,335,372,463,545,631,710,761,810,881,1017,1103,1176,1237,1385,1640,2263],
    10000:[0,205,205,205,205,229,262,287,313,347,416,490,564,639,688,735,783,854,941,1023,1095,1208,1418,1956],
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

print("ANALIZA EOI DLA CALYM ZAKRESIE OBROTOW (WOT)")
print(f"{'RPM':<5} | {'Nm':<4} | {'IQ mm3':<6} | {'Rail':<5} | {'ORI SOI':<7} | {'Dur deg':<7} | {'EOI (ORI)':<10} | {'Prop SOI':<8} | {'EOI (Prop)'}")
print("-" * 85)

proposed_soi = {
    1000: 0.0,
    1250: 3.5,
    1500: 4.5,
    1750: 5.5,
    2000: 6.5,
    2250: 6.5,
    2500: 7.0,
    2750: 7.5,
    3000: 9.0,
    3250: 10.0,
    3500: 11.0,
    3750: 12.0,
    4000: 13.0,
    4500: 15.0
}

for rpm in sorted(ori_soi.keys()):
    nm_rpms = sorted(nm_limiter.keys())
    nm_max = interp(nm_rpms, [nm_limiter[r] for r in nm_rpms], rpm)
    target_nm = min(315, nm_max)
    
    iq_mm3 = get_iq(rpm, target_nm)
    rail = rail_by_rpm.get(rpm, 1400)
    dur_us = get_duration(rail, iq_mm3)
    dur_deg = dur_us * rpm * 6.0 / 1e6
    
    soi_o = ori_soi[rpm]
    eoi_o = soi_o - dur_deg
    eoi_o_str = f"{abs(eoi_o):.1f} {'BTDC' if eoi_o > 0 else 'ATDC'}"
    
    soi_p = proposed_soi[rpm]
    eoi_p = soi_p - dur_deg
    eoi_p_str = f"{abs(eoi_p):.1f} {'BTDC' if eoi_p > 0 else 'ATDC'}"
    
    print(f"{rpm:<5} | {target_nm:<4.0f} | {iq_mm3:<6.1f} | {rail:<5} | {soi_o:<7.2f} | {dur_deg:<7.1f} | {eoi_o_str:<10} | {soi_p:<8.1f} | {eoi_p_str}")
