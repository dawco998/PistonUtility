const fs = require('fs');

// Mock browser environment
global.document = {
  getElementById: function(id) {
    return {
      value: 0,
      textContent: '',
      style: {},
      getContext: function() { return {}; },
      parentElement: { clientWidth: 800, clientHeight: 600 },
      addEventListener: function() {},
      classList: { toggle: function(){}, add: function(){}, remove: function(){} }
    };
  },
  querySelectorAll: function() { return []; }
};
global.window = {
  addEventListener: function() {},
  devicePixelRatio: 1
};
global.requestAnimationFrame = function() {};
global.devicePixelRatio = 1;
global.COLORS = { power:'', exhaust:'', intake:'', compression:'' };
global.PRESETS = {};

// Load ECU maps and Engine logic
const ecuCode = fs.readFileSync('ecu-maps.js', 'utf8');
const engineCode = fs.readFileSync('engine.js', 'utf8');

// Strip the UI init call at the end of engine.js to prevent errors
const cleanEngineCode = engineCode.replace('init();', '');

// Optimizer configuration and loop string
const optimizerCode = `
const RPM_AXIS = [1500, 1750, 2000, 2250, 2500, 2750, 3000, 3250, 3500];
const IQ_AXIS = [10, 20, 30, 40, 50, 60, 70]; // mg

function getTargetBoost(rpm, iq) {
  if (iq < 20) return 0.2;
  if (iq < 30) return 0.6;
  if (rpm < 1500) return 1.0;
  if (rpm < 2000) return 1.4;
  return 1.6;
}

console.log("Rozpoczynam optymalizację mapy SOI...");
const bestSoiMap = [];

for (let rpm of RPM_AXIS) {
  const row = [];
  const pmaxLimit = (rpm >= 2500) ? 180 : 170;
  
  for (let iq of IQ_AXIS) {
    let bestSoi = -5;
    let minBsfc = 9999;
    
    STATE.rpm = rpm;
    STATE.fuel = iq;
    STATE.boost = getTargetBoost(rpm, iq);
    STATE.tIntake = 40 + STATE.boost * 10;
    STATE.rail = ECU.getRail(rpm, iq / 0.835);
    
    for (let soi = -5; soi <= 30; soi += 0.5) {
      STATE.soiBTDC = soi;
      STATE.useEcuMaps = false;
      calcMetrics();
      // Fallback mechanism scoring
      let pmaxOk = STATE.pMax <= pmaxLimit;
      let eoiOk = STATE.eoi_ATDC <= 15;
      let dpOk = STATE.dpMax <= 12;
      
      if (pmaxOk) {
        // Score = penalty for violations
        let score = 0;
        if (!eoiOk) score += (STATE.eoi_ATDC - 15) * 10; // penalty for late EOI
        if (!dpOk) score += (STATE.dpMax - 12) * 20;     // heavy penalty for knock
        
        // Add BSFC as secondary objective
        score += STATE.bsfc;
        
        if (score < minBsfc) { // abusing minBsfc variable as 'minScore'
          minBsfc = score;
          bestSoi = soi;
        }
      }
    }
    row.push(minBsfc === 9999 ? "ERR" : bestSoi.toFixed(1));
  }
  bestSoiMap.push(row);
}

console.log("=== ZOPTYMALIZOWANA MAPA SOI (°BTDC) ===");
console.log("RPM \\ IQ(mg)\\t" + IQ_AXIS.join("\\t"));
for (let i = 0; i < RPM_AXIS.length; i++) {
  console.log(RPM_AXIS[i] + "\\t\\t" + bestSoiMap[i].join("\\t"));
}

let csv = "RPM / IQ (mg);" + IQ_AXIS.join(";") + "\\n";
for (let i = 0; i < RPM_AXIS.length; i++) {
  csv += RPM_AXIS[i] + ";" + bestSoiMap[i].join(";") + "\\n";
}
require('fs').writeFileSync('Optimal_SOI_Map.csv', csv);
console.log("\\nMapa zapisana do pliku Optimal_SOI_Map.csv");
`;

eval(ecuCode + "\n" + cleanEngineCode + "\n" + optimizerCode);
