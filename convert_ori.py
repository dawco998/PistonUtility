import os
import re
import json

ori_dir = r"C:\Users\Dawi\Documents\MazdaEDC16C3\Logi_i_Analiza_N75\MAPY MOD"
js_file = r"C:\Users\Dawi\Documents\MazdaEDC16C3\Logi_i_Analiza_N75\piston_sim\ecu-maps.js"

def parse_txt_map(filepath, has_x_header=True):
    with open(filepath, 'r') as f:
        lines = [line.strip() for line in f.readlines() if line.strip()]
        
    y_keys = []
    data = {}
    x_axis = []
    
    start_idx = 0
    for i, line in enumerate(lines):
        if '\t' in line and any(char.isdigit() for char in line):
            # To jest linia z nagłówkiem X lub z pierwszymi danymi
            parts = line.split('\t')
            if 'rpm' in parts[0].lower() or 'mg' in parts[0].lower() or 'nm' in parts[0].lower() or 'bar' in parts[0].lower() or parts[0] == '':
                # Header X
                if 'rpm' not in parts[0].lower() and 'r/min' not in parts[0].lower():
                     x_axis = [float(x.replace(',', '.')) for x in parts[1:]]
                     start_idx = i + 1
                     if 'rpm' in lines[start_idx].split('\t')[0].lower() or 'r/min' in lines[start_idx].split('\t')[0].lower():
                         start_idx += 1
                     break
            elif 'r/min' in parts[0].lower() or 'rpm' in parts[0].lower() and not has_x_header:
                start_idx = i
                break
            
    for i in range(start_idx, len(lines)):
        line = lines[i]
        if not line: continue
        parts = line.split('\t')
        if len(parts) < 2: continue
        
        y_val_str = parts[0].replace('r/min', '').replace('rpm', '').strip()
        if not y_val_str: continue
        try:
            y_val = float(y_val_str.replace(',', '.'))
            row_data = [float(x.replace(',', '.')) for x in parts[1:]]
            y_keys.append(y_val)
            data[y_val] = row_data
        except ValueError:
            continue
            
    return x_axis, y_keys, data

# Parse TQ LIMITER
with open(os.path.join(ori_dir, "TQ LIMITER.txt"), 'r') as f:
    lines = f.readlines()
tq_rpm = []
tq_nm = []
for line in lines:
    parts = line.strip().split()
    if len(parts) >= 2:
        try:
            if parts[0] in ['r/min', 'rpm']: parts = parts[1:]
            rpm = float(parts[0])
            nm = float(parts[1])
            tq_rpm.append(rpm)
            tq_nm.append(nm)
        except:
            pass

# Parse NM TO IQ
nm_x, nm_y, nm_data = parse_txt_map(os.path.join(ori_dir, "NM TO IQ conversion map.txt"))
# Parse Rail
rail_x, rail_y, rail_data = parse_txt_map(os.path.join(ori_dir, "RailPressure.txt"))
# Parse Duration
dur_x, dur_y, dur_data = parse_txt_map(os.path.join(ori_dir, "Duration.txt"))
# Parse SOI
soi_x, soi_y, soi_data = parse_txt_map(os.path.join(ori_dir, "SOI.txt"))


# Now read ecu-maps.js and replace the blocks
with open(js_file, 'r', encoding='utf-8') as f:
    js_content = f.read()

def replace_block(content, marker_start, marker_end, replacement):
    pattern = re.compile(marker_start + r'.*?' + marker_end, re.DOTALL)
    if not pattern.search(content):
        print(f"Błąd: Nie znaleziono bloku {marker_start}")
        return content
    return pattern.sub(marker_start + '\n' + replacement + '\n' + marker_end, content)

tq_repl = f"ECU.nmLimiter = {{\n  rpm: {json.dumps([int(x) for x in tq_rpm])},\n  nm:  {json.dumps([round(x,1) for x in tq_nm])}\n}};"
js_content = replace_block(js_content, r"// ── NM Limiter ──", r"// ── NM_TO_IQ", tq_repl + "\n\n")

nm_iq_repl = f"ECU.nmToIq = {{\n  nmAxis: {json.dumps([round(x,1) for x in nm_x])},\n  rpmKeys: {json.dumps([int(x) for x in nm_y])},\n  data: {{\n"
for k in nm_y: nm_iq_repl += f"    {int(k)}: {json.dumps(nm_data[k])},\n"
nm_iq_repl += "  }\n};"
js_content = replace_block(js_content, r"// ── NM_TO_IQ \(RPM × NM\*10 → mm3/stroke\) ──", r"// ── Rail Pressure", nm_iq_repl + "\n\n")

rail_repl = f"ECU.rail = {{\n  iqAxis: {json.dumps([round(x*10,1) for x in rail_x])},\n  rpmKeys: {json.dumps([int(x) for x in rail_y])},\n  data: {{\n"
for k in rail_y: rail_repl += f"    {int(k)}: {json.dumps([int(x) for x in rail_data[k]])},\n"
rail_repl += "  }\n};"
js_content = replace_block(js_content, r"// ── Rail Pressure \(RPM × IQ\*100 → bar\) ──", r"// ── Duration", rail_repl + "\n\n")

dur_repl = f"ECU.duration = {{\n  iqAxis: {json.dumps([round(x*100,1) for x in dur_x])},\n  railKeys: {json.dumps([int(x*10) for x in dur_y])},\n  data: {{\n"
for k in dur_y: dur_repl += f"    {int(k*10)}: {json.dumps([int(x) for x in dur_data[k]])},\n"
dur_repl += "  }\n};"
js_content = replace_block(js_content, r"// ── Duration \(Rail\*10 × IQ\*100 → µs\) ──", r"// ── Original SOI Map", dur_repl + "\n\n")

soi_repl = f"ECU.soi = {{\n  iqAxis: {json.dumps([round(x,1) for x in soi_x])},\n  rpmKeys: {json.dumps([int(x) for x in soi_y])},\n  data: {{\n"
for k in soi_y: soi_repl += f"    {int(k)}: {json.dumps([round(x,2) for x in soi_data[k]])},\n"
soi_repl += "  }\n};"
js_content = replace_block(js_content, r"// ── Original SOI Map \(RPM × IQ_mg → deg BTDC\) ──", r"// ── Log WOT data", soi_repl + "\n\n")

with open(js_file, 'w', encoding='utf-8') as f:
    f.write(js_content)
    
print("Ukończono aktualizację ecu-maps.js mapami fabrycznymi!")
