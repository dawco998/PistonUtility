const fs = require('fs');

global.document = { getElementById: function(id) { return { value: 0, textContent: '', style: {}, getContext: function() { return {}; }, parentElement: { clientWidth: 800, clientHeight: 600 }, addEventListener: function() {}, classList: { toggle: function(){}, add: function(){}, remove: function(){} } }; }, querySelectorAll: function() { return []; } };
global.window = { addEventListener: function() {}, devicePixelRatio: 1 };
global.requestAnimationFrame = function() {}; global.devicePixelRatio = 1; global.COLORS = { power:'', exhaust:'', intake:'', compression:'' }; global.PRESETS = {};

const ecuCode = fs.readFileSync('ecu-maps.js', 'utf8');
const engineCode = fs.readFileSync('engine.js', 'utf8').replace('init();', '');

const evalCode = `
  const rpm = 2000;
  STATE.rpm = rpm;
  STATE.useEcuMaps = true;
  STATE.pedal = 100;
  
  // Wymuś załadowanie map
  calcMetrics();
  
  console.log("Wyniki symulacji 0-D DLA FABRYCZNEJ MAPY (WOT):");
  console.log("- NM Limiter: " + STATE.ecuData.nmMax.toFixed(1) + " Nm");
  console.log("- Dawka: " + STATE.fuel.toFixed(1) + " mg (" + (STATE.fuel / 0.835).toFixed(1) + " mm3)");
  console.log("- RPM: " + STATE.rpm);
  console.log("- Boost: " + STATE.boost.toFixed(2) + " bar");
  console.log("- Rail: " + STATE.rail.toFixed(0) + " bar");
  console.log("------------------------");
  console.log("-> Fabryczne SOI: " + STATE.soiBTDC.toFixed(1) + " °BTDC");
  console.log("-> Moment Obrotowy: " + STATE.torque.toFixed(1) + " Nm");
  console.log("-> Pmax: " + STATE.pMax.toFixed(1) + " bar");
  console.log("-> Pmax Angle: " + STATE.pMaxAngle.toFixed(1) + " °");
  console.log("-> EOI: " + STATE.eoi_ATDC.toFixed(1) + " °ATDC");
  console.log("-> dp/dθ: " + STATE.dpMax.toFixed(1) + " bar/°CA");
`;

eval(ecuCode + "\n" + engineCode + "\n" + evalCode);
