/* ═══════════════════════════════════════════════════════════════
   DV6 TED4 Piston Simulator — Core Physics & State
   ═══════════════════════════════════════════════════════════════ */
'use strict';

const ENG = {
  bore: 75, stroke: 88.3, conRod: 145.5, CR: 18, nCyl: 4,
  firingOrder: [1,3,4,2],
  // Phase offsets in 720° cycle for each cylinder index (0-based)
  // Firing 1-3-4-2: cyl1=0°, cyl3=180°, cyl4=360°, cyl2=540°
  phaseOffset: [0, 540, 180, 360],
  R: 88.3/2,  // crank radius mm
  gamma: 1.35, gammaExp: 1.30,
  fuelDensity: 0.832, // kg/L
  baseFlowAt100: 7.9,  // mg/ms at 100 bar
};
ENG.Vd = Math.PI/4 * Math.pow(ENG.bore/10,2) * (ENG.stroke/10); // cm³/cyl
ENG.Vc = ENG.Vd / (ENG.CR - 1);
ENG.Vmax = ENG.Vd + ENG.Vc;

const STATE = {
  rpm: 2000, fuel: 25, soiBTDC: 8, boost: 1.0, rail: 1000, tIntake: 40,
  playing: true, speed: 0.1, globalAngle: 0, // 0-720 continuous
  lastTime: 0,
  // Computed per frame
  cylStates: [{},{},{},{}],
  injDuration_us: 0, injDuration_deg: 0, eoi_ATDC: 0,
  soi_ATDC: 0, socDelay_ms: 0,
  pMax: 0, tMax: 0,
};

const PRESETS = {
  idle:   {rpm:750,  fuel:5,   soiBTDC:4,  boost:0,   rail:350,  tIntake:30},
  cruise: {rpm:1800, fuel:15,  soiBTDC:6,  boost:0.5, rail:700,  tIntake:35},
  maxTq:  {rpm:2000, fuel:25,  soiBTDC:8,  boost:1.0, rail:1000, tIntake:40},
  maxPw:  {rpm:4000, fuel:30,  soiBTDC:10, boost:1.2, rail:1350, tIntake:50},
  stage1: {rpm:2000, fuel:35,  soiBTDC:9,  boost:1.4, rail:1400, tIntake:45},
};

const COLORS = {
  cylWall: '#1a1e30', cylWallStroke: '#2a3050',
  piston: '#556080', pistonTop: '#6878a0', pistonRing: '#8898c0',
  conRod: '#445070', conRodStroke: '#5a6a90',
  crankMain: '#334060', crankPin: '#4facfe', crankCounter: '#252a40',
  injSpray: 'rgba(0,242,254,0.6)', combustion: 'rgba(255,120,20,',
  soiMarker: '#00e676', eoiMarker: '#ff9800',
  intake: '#4facfe33', compression: '#b388ff33', power: '#ff980033', exhaust: '#ff444433',
  bg: '#060810',
};

// ── Kinematics ──
function pistonPinY(crankAngleDeg) {
  const th = crankAngleDeg * Math.PI / 180;
  const R = ENG.R, L = ENG.conRod;
  return R * Math.cos(th) + Math.sqrt(L*L - R*R * Math.sin(th)*Math.sin(th));
}

function pistonDisplacement(crankAngleDeg) {
  // displacement from TDC (0 at TDC, stroke at BDC)
  const atTDC = pistonPinY(0);
  return atTDC - pistonPinY(crankAngleDeg);
}

function cylinderVolume(crankAngleDeg) {
  // cm³
  const s = pistonDisplacement(crankAngleDeg); // mm from TDC
  const areaCC = Math.PI/4 * Math.pow(ENG.bore/10,2); // cm²
  return ENG.Vc + areaCC * (s/10); // cm³
}

function crankPinPos(crankAngleDeg) {
  const th = crankAngleDeg * Math.PI / 180;
  return { x: ENG.R * Math.sin(th), y: -ENG.R * Math.cos(th) }; // y neg = up
}

// ── Injection Calc — Delphi DFI 1.3 injector model ──
// Calibrated to real DV6 TED4 injector data:
//   At 1000 bar: ~25 mg delivered in ~800 µs flow time
//   Deadtime ≈ 350 µs at 12V battery
//   Flow scales with sqrt(rail_pressure / ref_pressure)
const INJ = {
  refFlow: 25.0,       // mg/ms at refPressure (calibrated from real data)
  refPressure: 1000,   // bar reference
  deadtime_us: 350,    // µs base deadtime at 12V
  minPulse_us: 150,    // minimum effective pulse width
};

function calcInjection() {
  // Flow rate scales with sqrt(pressure) — hydraulic nozzle law
  const flowRate = INJ.refFlow * Math.sqrt(STATE.rail / INJ.refPressure); // mg/ms
  // Deadtime varies slightly with rail pressure
  const deadtime = INJ.deadtime_us * Math.pow(INJ.refPressure / Math.max(STATE.rail, 200), 0.08);
  // Flow time = fuel mass / flow rate
  const flowTime_us = (STATE.fuel / flowRate) * 1000; // µs
  // Total energize time = deadtime + flow time
  STATE.injDuration_us = deadtime + flowTime_us;
  STATE.injDuration_deg = STATE.injDuration_us * STATE.rpm * 360 / (60e6);
  STATE.soi_ATDC = -STATE.soiBTDC;
  STATE.eoi_ATDC = STATE.soi_ATDC + STATE.injDuration_deg;
  // Ignition delay (simplified Wolfer)
  const pComp = calcPressureAtAngle(-STATE.soiBTDC);
  const tComp = calcTempAtAngle(-STATE.soiBTDC);
  STATE.socDelay_ms = 0.36 * Math.pow(Math.max(pComp,1), -1.02) * Math.exp(2100/Math.max(tComp,300));
  STATE.socDelay_ms = Math.max(0.2, Math.min(STATE.socDelay_ms, 3));
  const socDelay_deg = STATE.socDelay_ms * STATE.rpm * 360 / 60000;
  STATE.soc_ATDC = STATE.soi_ATDC + socDelay_deg;
  // Store for display
  STATE.massFlow_mg_ms = flowRate;
  STATE.deadtime_us_actual = deadtime;
  STATE.flowTime_us = flowTime_us;
}

function calcPressureAtAngle(atdc) {
  // Simplified polytropic for motored pressure
  const pIntake = (1 + STATE.boost) * 1.01325; // bar absolute
  const V_bdc = cylinderVolume(180);
  const V = cylinderVolume(Math.abs(atdc) < 180 ? Math.abs(atdc) : 360 - Math.abs(atdc));
  return pIntake * Math.pow(V_bdc / Math.max(V, ENG.Vc*0.99), ENG.gamma);
}

function calcTempAtAngle(atdc) {
  const tIntakeK = STATE.tIntake + 273.15;
  const V_bdc = cylinderVolume(180);
  const a = Math.abs(atdc);
  const ca = a < 180 ? a : 360 - a;
  const V = cylinderVolume(ca);
  return tIntakeK * Math.pow(V_bdc / Math.max(V, ENG.Vc*0.99), ENG.gamma - 1);
}

function calcPressureCycle(cycleAngle) {
  // cycleAngle: 0-720, 0 = firing TDC
  const ca = cycleAngle % 720;
  const crankAngle = ca % 360;
  const pIntake = (1 + STATE.boost) * 1.01325;
  const V = cylinderVolume(crankAngle);
  const V_bdc = cylinderVolume(180);

  if (ca >= 360) {
    // Intake & exhaust strokes - roughly atmospheric
    return pIntake * (ca < 540 ? 0.95 : 1.02);
  }
  // 0-360: power & compression
  // Motored pressure
  let pMotored = pIntake * Math.pow(V_bdc / Math.max(V, ENG.Vc*0.95), ENG.gamma);

  // Combustion pressure rise (simple Wiebe overlay)
  if (STATE.fuel > 0) {
    const burnStart = (720 + STATE.soc_ATDC) % 720;
    const burnDur = STATE.injDuration_deg + 15; // burn lasts longer than injection
    const burnAngle = (ca - burnStart + 720) % 720;
    if (burnAngle >= 0 && burnAngle < burnDur && burnStart < 60) {
      const xb = 1 - Math.exp(-6.908 * Math.pow(burnAngle/burnDur, 2.5));
      const qRise = STATE.fuel * 42.5 * xb / (V * 100); // simplified
      pMotored += qRise * 8;
    }
  }
  return Math.min(pMotored, 250); // cap at 250 bar
}

function getStrokeName(cycleAngle) {
  const ca = ((cycleAngle % 720) + 720) % 720;
  if (ca < 180) return 'POWER';
  if (ca < 360) return 'EXHAUST';
  if (ca < 540) return 'INTAKE';
  return 'COMPRESSION';
}

function getStrokeColor(name) {
  return {POWER: COLORS.power, EXHAUST: COLORS.exhaust,
          INTAKE: COLORS.intake, COMPRESSION: COLORS.compression}[name] || '#fff1';
}

function isInjecting(cycleAngle) {
  const ca = ((cycleAngle % 720) + 720) % 720;
  const soiCA = ((720 + STATE.soi_ATDC) % 720);
  const eoiCA = ((720 + STATE.eoi_ATDC) % 720);
  if (soiCA <= eoiCA) return ca >= soiCA && ca <= eoiCA;
  return ca >= soiCA || ca <= eoiCA;
}

function isBurning(cycleAngle) {
  const ca = ((cycleAngle % 720) + 720) % 720;
  const socCA = ((720 + STATE.soc_ATDC) % 720);
  const endBurn = (socCA + STATE.injDuration_deg + 20) % 720;
  if (socCA <= endBurn) return ca >= socCA && ca <= endBurn;
  return ca >= socCA || ca <= endBurn;
}

function calcMetrics() {
  calcInjection();
  const pIntake = (1 + STATE.boost) * 1.01325;
  STATE.pMax = pIntake * Math.pow(ENG.CR, ENG.gamma);
  if (STATE.fuel > 0) {
    STATE.pMax += STATE.fuel * 42.5 / (ENG.Vc * 100) * 8;
  }
  STATE.pMax = Math.min(STATE.pMax, 220);
  STATE.tMax = (STATE.tIntake + 273.15) * Math.pow(ENG.CR, ENG.gamma - 1);
  if (STATE.fuel > 0) STATE.tMax += STATE.fuel * 15;

  // Performance estimates (Vd is cm³ per cyl, convert to litres)
  const VdL = ENG.Vd / 1000; // litres per cylinder
  const VtotalL = VdL * 4;   // total displacement litres
  // IMEP from fuel energy: Q_fuel * eta_therm / Vd
  // fuel per cycle per cylinder = STATE.fuel mg, LHV=42.5 kJ/g
  const qFuelJ = STATE.fuel / 1000 * 42500; // J per cylinder per cycle
  const imep = qFuelJ * 0.42 / (VdL / 1000); // Pa → divide by 1e5 for bar
  const imepBar = imep / 1e5;
  const bmepBar = imepBar * 0.82; // mechanical efficiency
  STATE.torque = bmepBar * 1e5 * (VtotalL / 1000) / (4 * Math.PI);
  STATE.power = STATE.torque * STATE.rpm * 2 * Math.PI / 60 / 1000;
  // Lambda
  const airMass = pIntake * 1e5 * (VtotalL / 1000) * 0.85 / (287 * (STATE.tIntake + 273.15)) * 1000; // mg
  STATE.lambda = airMass / (STATE.fuel * 4 * 14.5);
  // BSFC: fuel consumed per hour / power
  const fuelPerCycleTotal_g = STATE.fuel * 4 / 1000; // g per engine cycle
  const cyclesPerHour = STATE.rpm / 2 * 60; // 4-stroke: 1 cycle = 2 revs
  const fuelPerHour_g = fuelPerCycleTotal_g * cyclesPerHour;
  STATE.bsfc = STATE.power > 0.01 ? fuelPerHour_g / STATE.power : 0; // g/kWh
}
