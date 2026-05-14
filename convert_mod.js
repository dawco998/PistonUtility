const fs = require('fs');
const path = require('path');

const modDir = "C:\\Users\\Dawi\\Documents\\MazdaEDC16C3\\Logi_i_Analiza_N75\\MAPY MOD";
const jsFile = "C:\\Users\\Dawi\\Documents\\MazdaEDC16C3\\Logi_i_Analiza_N75\\piston_sim\\ecu-maps.js";

function parseTxt(filePath, hasXHeader) {
    if (!fs.existsSync(filePath)) return null;
    const lines = fs.readFileSync(filePath, 'utf8').replace(/\r/g, '').split('\n').filter(l => l.trim().length > 0);
    
    let x_axis = [];
    let y_keys = [];
    let data = {};
    
    let startIdx = 0;
    for (let i = 0; i < lines.length; i++) {
        const line = lines[i];
        if (line.includes('\t') && line.match(/\d/)) {
            const parts = line.split('\t');
            if (parts[0].toLowerCase().includes('rpm') || parts[0].toLowerCase().includes('mg') || parts[0].toLowerCase().includes('nm') || parts[0].toLowerCase().includes('bar') || parts[0] === '') {
                if (!parts[0].toLowerCase().includes('rpm') && !parts[0].toLowerCase().includes('r/min')) {
                    x_axis = parts.slice(1).map(x => parseFloat(x.replace(',', '.')));
                    startIdx = i + 1;
                    if (lines[startIdx] && (lines[startIdx].toLowerCase().includes('rpm') || lines[startIdx].toLowerCase().includes('r/min'))) {
                        startIdx++;
                    }
                    break;
                }
            } else if ((parts[0].toLowerCase().includes('rpm') || parts[0].toLowerCase().includes('r/min')) && !hasXHeader) {
                startIdx = i;
                break;
            }
        }
    }
    
    for (let i = startIdx; i < lines.length; i++) {
        const line = lines[i];
        const parts = line.split('\t');
        if (parts.length < 2) continue;
        const yValStr = parts[0].replace('r/min', '').replace('rpm', '').trim();
        if (!yValStr) continue;
        const yVal = parseFloat(yValStr.replace(',', '.'));
        if (isNaN(yVal)) continue;
        
        y_keys.push(yVal);
        data[yVal] = parts.slice(1).map(x => parseFloat(x.replace(',', '.')));
    }
    
    return { x: x_axis, y: y_keys, data };
}

// TQ LIMITER
const tqLines = fs.readFileSync(path.join(modDir, "TQ LIMITER.txt"), 'utf8').replace(/\r/g, '').split('\n');
const tqRpm = [];
const tqNm = [];
for (const line of tqLines) {
    const parts = line.trim().split(/\s+/);
    if (parts.length >= 2) {
        let p = parts;
        if (p[0] === 'r/min' || p[0] === 'rpm') p = p.slice(1);
        const rpm = parseFloat(p[0]);
        const nm = parseFloat(p[1]);
        if (!isNaN(rpm) && !isNaN(nm)) {
            tqRpm.push(rpm);
            tqNm.push(nm);
        }
    }
}

const nmMap = parseTxt(path.join(modDir, "NM TO IQ conversion map.txt"), true);
const railMap = parseTxt(path.join(modDir, "RailPressure.txt"), true);
const durMap = parseTxt(path.join(modDir, "Duration.txt"), true);
const soiMap = parseTxt(path.join(modDir, "SOI.txt"), true);

let content = fs.readFileSync(jsFile, 'utf8');

function replaceSection(name, objStr) {
    const regex = new RegExp(`ECU\\.${name} = \\{[\\s\\S]*?\\};`, 'm');
    content = content.replace(regex, `ECU.${name} = ${objStr};`);
}

// Replace Limiter
replaceSection('nmLimiter', `{\n  rpm: ${JSON.stringify(tqRpm)},\n  nm: ${JSON.stringify(tqNm)}\n}`);

// Replace NM_TO_IQ
let nmStr = `{\n  nmAxis: ${JSON.stringify(nmMap.x.map(x => Number(x.toFixed(1))))},\n  rpmKeys: ${JSON.stringify(nmMap.y)},\n  data: {\n`;
for (const y of nmMap.y) nmStr += `    ${y}: ${JSON.stringify(nmMap.data[y])},\n`;
nmStr += `  }\n}`;
replaceSection('nmToIq', nmStr);

// Replace Rail
let railStr = `{\n  iqAxis: ${JSON.stringify(railMap.x.map(x => Number((x*10).toFixed(1))))},\n  rpmKeys: ${JSON.stringify(railMap.y)},\n  data: {\n`;
for (const y of railMap.y) railStr += `    ${y}: ${JSON.stringify(railMap.data[y].map(Math.round))},\n`;
railStr += `  }\n}`;
replaceSection('rail', railStr);

// Replace Duration
let durStr = `{\n  iqAxis: ${JSON.stringify(durMap.x.map(x => Number((x*100).toFixed(1))))},\n  railKeys: ${JSON.stringify(durMap.y.map(y => y*10))},\n  data: {\n`;
for (const y of durMap.y) durStr += `    ${y*10}: ${JSON.stringify(durMap.data[y].map(Math.round))},\n`;
durStr += `  }\n}`;
replaceSection('duration', durStr);

// Replace SOI
let soiStr = `{\n  iqAxis: ${JSON.stringify(soiMap.x.map(x => Number(x.toFixed(1))))},\n  rpmKeys: ${JSON.stringify(soiMap.y)},\n  data: {\n`;
for (const y of soiMap.y) soiStr += `    ${y}: ${JSON.stringify(soiMap.data[y].map(v => Number(v.toFixed(2))))},\n`;
soiStr += `  }\n}`;
replaceSection('soi', soiStr);

fs.writeFileSync(jsFile, content, 'utf8');
console.log("SUCCESS!");
