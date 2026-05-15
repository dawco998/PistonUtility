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
  pedal: 0,  // pedal percentage 0-100
  playing: true, speed: 0.1, globalAngle: 0, // 0-720 continuous
  lastTime: 0, useEcuMaps: false,
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
// Calibrated to real DV6 TED4 ECU Duration map data:
//   refFlow fitted across 1050-1700 bar range (error <0.3%)
//   Flow scales with (rail/ref)^0.627 (better fit than sqrt)
//   Deadtime matches ECU injector delay function
const INJ = {
  refFlow: 29.58,      // mg/ms at refPressure (calibrated to ECU Duration map)
  refPressure: 1000,   // bar reference
  flowExponent: 0.627, // power law exponent (hydraulic fit to real data)
  minPulse_us: 150,    // minimum effective pulse width
};

function calcInjection() {
  if (STATE.useEcuMaps && typeof ECU !== 'undefined') {
    // ── ECU MAP MODE: use Pedal% + RPM → full chain ──
    const lookup = ECU.lookupPartial(STATE.rpm, STATE.pedal);
    // Override STATE with map values
    STATE.fuel = lookup.iq * 0.835; // mm3 → mg
    STATE.fuel_mm3 = lookup.iq;
    STATE.rail = lookup.rail;
    STATE.soiBTDC = lookup.soi;
    STATE.boost = lookup.boost;
    STATE.ecuData = lookup; // store for panel
    // Duration from ECU map (already in µs)
    const injDelay = lookup.injDelay;
    STATE.injDuration_us = lookup.dur_us + injDelay;
    STATE.injDuration_deg = STATE.injDuration_us * STATE.rpm * 360 / (60e6);
    STATE.soi_ATDC = -STATE.soiBTDC;
    STATE.eoi_ATDC = STATE.soi_ATDC + STATE.injDuration_deg;
    STATE.massFlow_mg_ms = lookup.dur_us > 0 ? lookup.iq / (lookup.dur_us / 1000) : 0;
    STATE.deadtime_us_actual = injDelay;
    STATE.flowTime_us = lookup.dur_us;
    // Update sliders to reflect map values
    updateSlidersFromECU();
  } else {
  // ── MANUAL MODE: calibrated injector model ──
  // Flow rate scales with (pressure)^0.627 — fitted to real ECU Duration map
  const flowRate = INJ.refFlow * Math.pow(STATE.rail / INJ.refPressure, INJ.flowExponent); // mg/ms
  // Deadtime matches ECU injector delay function
  const deadtime = Math.max(180, Math.min(400 - 0.12 * STATE.rail, 400));
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
  } // end manual mode
}

function updateSlidersFromECU() {
  const s = (id, val) => { const e = document.getElementById(id); if(e) e.value = val; };
  const t = (id, val) => { const e = document.getElementById(id); if(e) e.textContent = val; };
  s('ctrl-fuel', STATE.fuel); t('val-fuel', `${STATE.fuel.toFixed(1)} mg / ${(STATE.fuel/0.835).toFixed(1)} mm³`);
  s('ctrl-soi', STATE.soiBTDC); t('val-soi', `${STATE.soiBTDC.toFixed(1)}° BTDC`);
  s('ctrl-rail', Math.min(STATE.rail, 1600)); t('val-rail', `${Math.round(STATE.rail)} bar`);
  s('ctrl-boost', STATE.boost); t('val-boost', `${STATE.boost.toFixed(2)} bar`);
}

function updateEcuPanel() {
  const panel = document.getElementById('ecu-map-panel');
  if (!panel) return;
  panel.style.display = STATE.useEcuMaps ? 'block' : 'none';
  if (!STATE.useEcuMaps || !STATE.ecuData) return;
  const w = STATE.ecuData;
  const s = (id, val) => { const e = document.getElementById(id); if(e) e.textContent = val; };
  s('ecu-pedal', `${Math.round(STATE.pedal)}%`);
  s('ecu-nm', `${w.nmMax.toFixed(0)} Nm`);
  s('ecu-iq', `${w.iq.toFixed(1)} mm³`);
  s('ecu-iqmg', `${(w.iq*0.835).toFixed(1)} mg`);
  s('ecu-rail-map', `${Math.round(w.rail)} bar`);
  s('ecu-dur', `${Math.round(w.dur_us)} µs (${(w.dur_us*STATE.rpm*6/1e6).toFixed(1)}°)`);
  s('ecu-injdel', `${Math.round(w.injDelay)} µs`);
  s('ecu-soi-map', `${w.soi.toFixed(1)}° BTDC`);
  s('ecu-eoi', `${w.eoi.toFixed(1)}° ATDC`);
  s('ecu-boost', `${w.boost.toFixed(2)} bar`);
}

// ═══════════════════════════════════════════════════════════════
// 0-D Single-Zone Thermodynamic Cycle Solver — DV6 TED4
// ═══════════════════════════════════════════════════════════════
const THERMO = {
  dTh: 0.5, nPts: 1441, pTrace: null, tTrace: null, valid: false,
  IVC_ca: 580, EVO_ca: 140,
  wiebe_a: 6.908, wiebe_m: 2.0,
  C1: 2.28, C2: 3.24e-3, Twall: 450,
  LHV: 42.5e6, eta_comb: 0.98, Rgas: 287,
};
THERMO.pTrace = new Float64Array(THERMO.nPts);
THERMO.tTrace = new Float64Array(THERMO.nPts);

function cylVol_m3(ca) { return cylinderVolume(((ca%720)+720)%720%360)/1e6; }
function dVdTh(ca) { return (cylVol_m3(ca+0.1)-cylVol_m3(ca-0.1))/0.2; }
function cylArea(ca) {
  const D=ENG.bore/1000, Ah=Math.PI/4*D*D, Vc=ENG.Vc/1e6;
  return 2*Ah + Math.PI*D*Math.max(0,(cylVol_m3(ca)-Vc)/Ah);
}

function calcIgnDelay(p_bar,T_K) {
  return Math.max(0.3, Math.min(0.36*Math.pow(Math.max(p_bar,1),-1.02)*Math.exp(2100/Math.max(T_K,300)), 3));
}

function solveThermoCycle() {
  const dTh=THERMO.dTh, N=THERMO.nPts;
  const D=ENG.bore/1000, S=ENG.stroke/1000, Sp=2*S*STATE.rpm/60;
  const Vc_m3=ENG.Vc/1e6, Vd_m3=ENG.Vd/1e6;
  const pI_Pa=(1+STATE.boost)*101325, pI_bar=pI_Pa/1e5;
  const tFresh_K=STATE.tIntake+273.15;
  
  // Poprawka na VE (Volumetric Efficiency - Sprawność objętościowa)
  // Fizycznie żaden silnik nie napełnia się w 100% ciśnieniem z kolektora.
  // Straty przepływu sprawiają, że ciśnienie w cylindrze na IVC to ~85% ciśnienia Boost.
  const VE = 0.85;
  const pI_IVC_Pa = pI_Pa * VE;
  const pI_IVC_bar = pI_IVC_Pa / 1e5;
  
  // EGR / Frakcja gazów resztkowych (Residual Gas Model)
  const P_exh = Math.max(pI_bar * 1.1, 1.1); // Ciśnienie wydechu
  const xr = (1 / ENG.CR) * Math.pow(P_exh / Math.max(pI_IVC_bar, 1.0), 1 / 1.35);
  const tExh_K = STATE.tMax > 0 ? STATE.tMax * 0.75 : 800;
  const tI_K = (1 - xr) * tFresh_K + xr * tExh_K;

  const mfuel=STATE.fuel/1e6, Qt=mfuel*THERMO.LHV*THERMO.eta_comb;
  const Vivc=cylVol_m3(THERMO.IVC_ca);

  // Udoskonalony Model Opóźnienia Zapłonu: Całka Livengood-Wu
  let lw_integral = 0;
  let soc_found = false;
  let current_ca = ((720 + STATE.soi_ATDC) % 720);
  let socDelay_ca = 0.5;

  for (let s = 0; s < 200; s++) { 
    const V = cylVol_m3(current_ca);
    const P = pI_IVC_bar * Math.pow(Vivc / Math.max(V, ENG.Vc/1e6*0.99), 1.35);
    const T = tI_K * Math.pow(Vivc / Math.max(V, ENG.Vc/1e6*0.99), 0.35);
    
    const tau_ms = calcIgnDelay(P, T);
    const tau_deg = tau_ms * STATE.rpm * 6 / 1000;
    
    lw_integral += dTh / tau_deg;
    socDelay_ca += dTh;
    
    if (lw_integral >= 1.0) {
      break;
    }
    current_ca = (current_ca + dTh) % 720;
  }
  
  STATE.socDelay_ms = socDelay_ca / (STATE.rpm * 6 / 1000);
  STATE.soc_ATDC = STATE.soi_ATDC + socDelay_ca;
  const soc_ca = ((720 + STATE.soc_ATDC) % 720);

  const burnDur=Math.max((STATE.injDuration_deg||20)+15,25);
  
  // Model podwójnej funkcji Wiebego (Double-Wiebe)
  // Brak wtrysku pilotującego! Oznacza to, że całe paliwo wstrzyknięte podczas opóźnienia zapłonu
  // spala się gwałtownnie w fazie kinetycznej. Beta musi być znacząca.
  const beta = Math.min(0.35, STATE.socDelay_ms * 0.15); 
  
  // Faza kinetyczna (Premixed)
  const wa_p = 6.908, wm_p = 3.0;
  const dur_p = burnDur * 0.25; 
  
  // Faza dyfuzyjna (Diffusion)
  const wa_d = 6.908, wm_d = 2.0;
  const dur_d = burnDur;

  function dQch(ca){
    if(Qt<=0)return 0;
    const ba=((ca-soc_ca+720)%720);
    if(ba>=burnDur||ba<0)return 0;
    if(soc_ca>60&&soc_ca<680)return 0;
    
    // dQ dla fazy kinetycznej
    let dq_p = 0;
    if (ba < dur_p) {
        const x_p = ba / dur_p;
        dq_p = beta * Qt * wa_p * (wm_p + 1) / dur_p * Math.pow(x_p, wm_p) * Math.exp(-wa_p * Math.pow(x_p, wm_p + 1));
    }
    
    // dQ dla fazy dyfuzyjnej
    const x_d = ba / dur_d;
    const dq_d = (1 - beta) * Qt * wa_d * (wm_d + 1) / dur_d * Math.pow(x_d, wm_d) * Math.exp(-wa_d * Math.pow(x_d, wm_d + 1));
    
    return dq_p + dq_d;
  }
  
  function xBurned(ca){
    if(Qt<=0)return 0;
    const ba=((ca-soc_ca+720)%720);
    if(ba<0)return 0;
    if(ba>=burnDur)return 1.0;
    if(soc_ca>60&&soc_ca<680)return 0;
    
    let x_p = 0;
    if (ba < dur_p) {
        x_p = 1 - Math.exp(-wa_p * Math.pow(ba / dur_p, wm_p + 1));
    } else {
        x_p = 1.0;
    }
    
    const x_d = 1 - Math.exp(-wa_d * Math.pow(ba / dur_d, wm_d + 1));
    
    return beta * x_p + (1 - beta) * x_d;
  }
  function pMot(ca){ return pI_IVC_Pa*Math.pow(Vivc/Math.max(cylVol_m3(ca),Vc_m3*0.99), 1.35); }
  
  // Model Strat Ciepła: Hohenberg
  function dQht(ca,p,T){
    const V_L = cylVol_m3(ca) * 1000; // objętość w litrach
    const P_bar = p / 1e5;
    // Współczynnik wnikania ciepła Hohenberga
    const hc = 130 * Math.pow(V_L, -0.06) * Math.pow(P_bar, 0.8) * Math.pow(Math.max(T, 300), -0.4) * Math.pow(Sp + 1.4, 0.8);
    // Skalibrowane Twall z modelu (np. 450K)
    return hc * cylArea(ca) * (T - THERMO.Twall) / (6 * STATE.rpm);
  }

  // Fill exhaust+intake
  for(let i=0;i<N;i++){
    const ca=i*dTh;
    if(ca>=THERMO.EVO_ca&&ca<THERMO.IVC_ca){
      THERMO.pTrace[i]=ca<360?pI_bar*1.02:pI_bar*0.98;
      THERMO.tTrace[i]=ca<360?800:tI_K;
    }
  }

  // Integrate IVC→EVO
  const span=Math.round((720-THERMO.IVC_ca+THERMO.EVO_ca)/dTh);
  let p=pI_IVC_Pa, T=tI_K;
  let mCh=pI_IVC_Pa*Vivc/(THERMO.Rgas*tI_K);
  const ivcI=Math.round(THERMO.IVC_ca/dTh);
  THERMO.pTrace[ivcI]=p/1e5; THERMO.tTrace[ivcI]=T;

  for(let s=1;s<=span;s++){
    const ca=(THERMO.IVC_ca+s*dTh)%720;
    const idx=Math.round(ca/dTh)%(N-1);
    const V=cylVol_m3(ca), dV=dVdTh(ca);
    // Zmienne wlasciwosci gazu (aproksymacja ciepla wlasciwego i gamma w zaleznosci od Temp)
    const cv = 718 + 0.13 * T + 0.00002 * T * T;
    const g = 1 + THERMO.Rgas / cv;
    
    const qc=dQch(ca), qh=dQht(ca,p,T);
    
    // Model Upustów Przedmuchowych (Blow-by)
    let dm_blowby = 0;
    if (p > 101325) {
        // Uproszczony wyciek przez szczeliny pierścieni: dm = C * A * p / sqrt(RT)
        dm_blowby = 1.2e-6 * p * Math.sqrt(1 / (THERMO.Rgas * T)) * (dTh / (6 * STATE.rpm));
        mCh = Math.max(mCh - dm_blowby, mCh * 0.7); // Redukcja masy ładunku (zabezpieczenie min 70%)
    }
    
    p+=((g-1)/V*(qc-qh) - g*p*dV/V - p*dm_blowby/mCh)*dTh;
    p=Math.max(p,50000);
    T=p*V/(mCh*THERMO.Rgas); T=Math.max(T,300);
    THERMO.pTrace[idx]=p/1e5; THERMO.tTrace[idx]=T;
  }

  // Extract results
  let pMax=0,pMI=0,dpMax=0,dpMI=0,ca50a=0,ca50f=false;
  for(let i=1;i<N;i++){
    if(THERMO.pTrace[i]>pMax){pMax=THERMO.pTrace[i];pMI=i;}
    const dp=(THERMO.pTrace[i]-THERMO.pTrace[i-1])/dTh;
    if(dp>dpMax){dpMax=dp;dpMI=i;}
  }
  if(Qt>0)for(let i=0;i<N&&!ca50f;i++){if(xBurned(i*dTh)>=0.5){ca50a=i*dTh;ca50f=true;}}

  let work=0;
  for(let i=0;i<N-1;i++){
    work+=(THERMO.pTrace[i]+THERMO.pTrace[i+1])/2*1e5*(cylVol_m3((i+1)*dTh)-cylVol_m3(i*dTh));
  }
  const toA=i=>{const c=i*dTh;return c<=360?c:c-720;};

  STATE.pMax=pMax; STATE.pMaxAngle=toA(pMI);
  STATE.dpMax=dpMax; STATE.dpMaxAngle=toA(dpMI);
  STATE.tMax=THERMO.tTrace[pMI]||0;
  STATE.ca50=ca50f?(ca50a<=360?ca50a:ca50a-720):STATE.soc_ATDC+burnDur*0.55;
  STATE.imep=work/Vd_m3/1e5;
  const fmep=0.97+0.15*(STATE.rpm/1000)+0.05*Math.pow(STATE.rpm/1000,2);
  STATE.fmep=fmep;
  const bmep=STATE.imep-fmep;
  const VtL=ENG.Vd*4/1000;
  STATE.torque=bmep*1e5*(VtL/1000)/(4*Math.PI);
  STATE.power=STATE.torque*STATE.rpm*2*Math.PI/60/1000;
  const qJ=STATE.fuel/1000*42500;
  STATE.etaTherm=qJ>0?(STATE.imep*1e5*Vd_m3)/qJ:0;
  const airM=(1+STATE.boost)*1.01325*1e5*(VtL/1000)*0.85/(287*(STATE.tIntake+273.15))*1000;
  STATE.lambda=airM/(STATE.fuel*4*14.5);
  const fG=STATE.fuel*4/1000, cH=STATE.rpm/2*60;
  STATE.bsfc=STATE.power>0.01?fG*cH/STATE.power:0;
  STATE.pMaxLimit=160; STATE.pMaxAbsLimit=180; STATE.dpLimit=8; STATE.dpDanger=12;
  THERMO.valid=true;
}

function calcPressureCycle(cycleAngle) {
  const ca=((cycleAngle%720)+720)%720;
  if(!THERMO.valid){
    const pI=(1+STATE.boost)*1.01325;
    if(ca>=360)return pI*(ca<540?0.95:1.02);
    return pI*Math.pow(cylinderVolume(180)/Math.max(cylinderVolume(ca%360),ENG.Vc*0.95), 1.35);
  }
  return THERMO.pTrace[Math.min(Math.round(ca/THERMO.dTh),THERMO.nPts-1)]||1;
}

function calcPressureAtAngle(atdc) { return calcPressureCycle(((atdc%720)+720)%720); }
function calcTempAtAngle(atdc) {
  if(!THERMO.valid){
    const tK=STATE.tIntake+273.15,Vb=cylinderVolume(180),a=Math.abs(atdc);
    return tK*Math.pow(Vb/Math.max(cylinderVolume(a<180?a:360-a),ENG.Vc*0.99), 1.35 - 1);
  }
  const ca=((atdc%720)+720)%720;
  return THERMO.tTrace[Math.min(Math.round(ca/THERMO.dTh),THERMO.nPts-1)]||300;
}

// ═══ calcMetrics: orchestrator ═══
function calcMetrics() {
  calcInjection();
  solveThermoCycle();
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


/* ═══ DV6 TED4 Drawing & UI ═══ */
'use strict';

const canvas = document.getElementById('engine-canvas');
const ctx = canvas.getContext('2d');
const pvCanvas = document.getElementById('pv-canvas');
const pvCtx = pvCanvas.getContext('2d');
const prCanvas = document.getElementById('pressure-canvas');
const prCtx = prCanvas.getContext('2d');

function resizeAll() {
  [canvas, pvCanvas, prCanvas].forEach(c => {
    c.width = c.parentElement.clientWidth * devicePixelRatio;
    c.height = c.parentElement.clientHeight * devicePixelRatio;
  });
}
window.addEventListener('resize', resizeAll);
resizeAll();

// ── Draw one cylinder ──
function drawCylinder(idx, cx, topY, scale, W) {
  const cycleAngle = ((STATE.globalAngle - ENG.phaseOffset[idx]) % 720 + 720) % 720;
  const crankAngle = cycleAngle % 360;
  const strokeName = getStrokeName(cycleAngle);
  const boreW = ENG.bore * scale;
  const halfBore = boreW / 2;
  const pistonH = 20 * scale;
  const R = ENG.R * scale, L = ENG.conRod * scale;
  const strokePx = ENG.stroke * scale;

  // Crank center is below cylinder: head + stroke + small gap
  const headY = topY;                     // top of cylinder bore (head)
  const crankCY = headY + strokePx + L + 10 * scale;

  // Crank pin position (th=0 → crank pin UP = TDC)
  const th = crankAngle * Math.PI / 180;
  const crankPinX = cx + R * Math.sin(th);
  const crankPinY = crankCY - R * Math.cos(th);

  // Piston pin Y — constrained vertically along cylinder axis
  const lateralOffset = R * Math.sin(th);
  const conRodVertical = Math.sqrt(L * L - lateralOffset * lateralOffset);
  const pistonPinYabs = crankPinY - conRodVertical;
  const pistonTopY = pistonPinYabs - pistonH * 0.35;

  // Cylinder walls: from head to just past BDC piston bottom
  const cylTop = headY - 2;
  const cylBot = crankCY - (L - R) + pistonH + 5 * scale; // past BDC

  ctx.save();
  const wallGrad = ctx.createLinearGradient(cx - halfBore, 0, cx + halfBore, 0);
  wallGrad.addColorStop(0, '#2a3050');
  wallGrad.addColorStop(0.08, '#1a1e30');
  wallGrad.addColorStop(0.92, '#1a1e30');
  wallGrad.addColorStop(1, '#2a3050');
  ctx.fillStyle = wallGrad;
  ctx.fillRect(cx - halfBore - 5, cylTop, halfBore * 2 + 10, cylBot - cylTop);

  // Cylinder bore (inner fill — stroke color background)
  ctx.fillStyle = getStrokeColor(strokeName);
  ctx.fillRect(cx - halfBore, cylTop, halfBore * 2, cylBot - cylTop);

  // Cylinder head plate
  ctx.fillStyle = '#2a3050';
  ctx.fillRect(cx - halfBore - 7, cylTop - 8, halfBore * 2 + 14, 10);
  ctx.fillStyle = '#3a4570';
  ctx.fillRect(cx - halfBore - 7, cylTop - 8, halfBore * 2 + 14, 3);

  // Injector nozzle
  ctx.fillStyle = '#556080';
  ctx.fillRect(cx - 3, cylTop - 16, 6, 10);
  ctx.fillStyle = '#6878a0';
  ctx.fillRect(cx - 5, cylTop - 18, 10, 4);

  // Injection spray
  if (isInjecting(cycleAngle)) {
    const sprayLen = Math.min(pistonTopY - cylTop - 5, 55 * scale);
    if (sprayLen > 5) {
      for (let i = 0; i < 8; i++) {
        const angle = (i - 3.5) * 0.13;
        const grad = ctx.createLinearGradient(cx, cylTop, cx, cylTop + sprayLen);
        grad.addColorStop(0, 'rgba(0,242,254,0.9)');
        grad.addColorStop(1, 'rgba(0,242,254,0)');
        ctx.strokeStyle = grad;
        ctx.lineWidth = 1.5;
        ctx.beginPath();
        ctx.moveTo(cx, cylTop + 2);
        ctx.lineTo(cx + Math.sin(angle) * sprayLen, cylTop + 2 + sprayLen);
        ctx.stroke();
      }
      const glow = ctx.createRadialGradient(cx, cylTop + 12, 0, cx, cylTop + 12, sprayLen * 0.6);
      glow.addColorStop(0, 'rgba(0,242,254,0.18)');
      glow.addColorStop(1, 'rgba(0,242,254,0)');
      ctx.fillStyle = glow;
      ctx.fillRect(cx - halfBore, cylTop, halfBore * 2, sprayLen);
    }
  }

  // Combustion glow
  if (isBurning(cycleAngle)) {
    const ca = cycleAngle % 720;
    const intensity = Math.max(0, 1 - ca / 55);
    if (intensity > 0) {
      const glowR = halfBore * 0.9;
      const glow = ctx.createRadialGradient(cx, cylTop + 12, 0, cx, cylTop + 12, glowR);
      glow.addColorStop(0, `rgba(255,150,30,${intensity * 0.5})`);
      glow.addColorStop(0.6, `rgba(255,60,10,${intensity * 0.2})`);
      glow.addColorStop(1, 'rgba(255,60,10,0)');
      ctx.fillStyle = glow;
      ctx.fillRect(cx - halfBore, cylTop, halfBore * 2, Math.max(0, pistonTopY - cylTop));
    }
  }

  // Piston body
  const pGrad = ctx.createLinearGradient(0, pistonTopY, 0, pistonTopY + pistonH);
  pGrad.addColorStop(0, '#7888b0');
  pGrad.addColorStop(0.3, '#5a6a90');
  pGrad.addColorStop(1, '#445070');
  ctx.fillStyle = pGrad;
  ctx.fillRect(cx - halfBore + 2, pistonTopY, halfBore * 2 - 4, pistonH);

  // Piston rings (3 compression rings)
  for (let r = 0; r < 3; r++) {
    ctx.fillStyle = r === 0 ? '#9aa8d0' : '#8090b0';
    ctx.fillRect(cx - halfBore + 1, pistonTopY + 2 + r * 4, halfBore * 2 - 2, 1.5);
  }

  // Piston pin
  ctx.fillStyle = '#8898c0';
  ctx.beginPath();
  ctx.arc(cx, pistonPinYabs, 3, 0, Math.PI * 2);
  ctx.fill();

  // Connecting rod (draw below cylinder wall using clip)
  ctx.strokeStyle = '#5a6a90';
  ctx.lineWidth = 6 * scale;
  ctx.lineCap = 'round';
  ctx.beginPath();
  ctx.moveTo(cx, pistonPinYabs);
  ctx.lineTo(crankPinX, crankPinY);
  ctx.stroke();
  ctx.strokeStyle = '#6a7aa0';
  ctx.lineWidth = 3.5 * scale;
  ctx.beginPath();
  ctx.moveTo(cx, pistonPinYabs);
  ctx.lineTo(crankPinX, crankPinY);
  ctx.stroke();

  // Crank main journal
  ctx.fillStyle = '#334060';
  ctx.beginPath();
  ctx.arc(cx, crankCY, 9 * scale, 0, Math.PI * 2);
  ctx.fill();
  ctx.strokeStyle = '#445070';
  ctx.lineWidth = 1.5;
  ctx.stroke();

  // Counterweight
  const cwX = cx - R * 0.7 * Math.sin(th);
  const cwY = crankCY + R * 0.7 * Math.cos(th);
  ctx.fillStyle = '#1e2235';
  ctx.beginPath();
  ctx.arc(cwX, cwY, 11 * scale, 0, Math.PI * 2);
  ctx.fill();
  ctx.strokeStyle = '#2a3050';
  ctx.lineWidth = 1;
  ctx.stroke();

  // Crank pin dot (blue accent)
  ctx.fillStyle = '#4facfe';
  ctx.beginPath();
  ctx.arc(crankPinX, crankPinY, 4 * scale, 0, Math.PI * 2);
  ctx.fill();
  ctx.shadowColor = '#4facfe';
  ctx.shadowBlur = 6;
  ctx.fill();
  ctx.shadowBlur = 0;

  ctx.restore();

  // ── Crank angle dial ──
  const dialR = 22 * scale;
  const dialCX = cx;
  const dialCY = crankCY + R + dialR + 15 * scale;
  // Dial bg
  ctx.fillStyle = '#10131f';
  ctx.beginPath();
  ctx.arc(dialCX, dialCY, dialR + 2, 0, Math.PI * 2);
  ctx.fill();
  ctx.strokeStyle = '#2a3050';
  ctx.lineWidth = 1;
  ctx.stroke();

  // SOI arc (green)
  const soiStart = (-STATE.soiBTDC - 90) * Math.PI / 180;
  const eoiEnd = (STATE.eoi_ATDC - 90) * Math.PI / 180;
  ctx.beginPath();
  ctx.arc(dialCX, dialCY, dialR - 2, soiStart, eoiEnd);
  ctx.strokeStyle = '#00e676';
  ctx.lineWidth = 3;
  ctx.stroke();

  // EOI marker
  ctx.beginPath();
  ctx.arc(dialCX + (dialR-2)*Math.cos(eoiEnd), dialCY + (dialR-2)*Math.sin(eoiEnd), 3, 0, Math.PI*2);
  ctx.fillStyle = '#ff9800';
  ctx.fill();

  // SOI marker
  ctx.beginPath();
  ctx.arc(dialCX + (dialR-2)*Math.cos(soiStart), dialCY + (dialR-2)*Math.sin(soiStart), 3, 0, Math.PI*2);
  ctx.fillStyle = '#00e676';
  ctx.fill();

  // Current position needle
  const needleAngle = (cycleAngle / 2 - 90) * Math.PI / 180;
  ctx.strokeStyle = '#ff4444';
  ctx.lineWidth = 1.5;
  ctx.beginPath();
  ctx.moveTo(dialCX, dialCY);
  ctx.lineTo(dialCX + dialR * 0.8 * Math.cos(needleAngle), dialCY + dialR * 0.8 * Math.sin(needleAngle));
  ctx.stroke();

  // TDC mark
  ctx.fillStyle = '#fff';
  ctx.fillRect(dialCX - 0.5, dialCY - dialR - 1, 1, 4);

  // Labels
  ctx.fillStyle = '#e8eaf6';
  ctx.font = `bold ${12 * scale}px Inter`;
  ctx.textAlign = 'center';
  ctx.fillText(`CYL ${idx + 1}`, cx, topY - 24 * scale);
  ctx.font = `${9 * scale}px JetBrains Mono`;
  ctx.fillStyle = strokeName === 'POWER' ? '#ff9800' : strokeName === 'COMPRESSION' ? '#b388ff' :
                  strokeName === 'INTAKE' ? '#4facfe' : '#ff4444';
  ctx.fillText(strokeName, cx, topY - 12 * scale);

  // Crank angle text on dial
  ctx.fillStyle = '#8892b0';
  ctx.font = `${8 * scale}px JetBrains Mono`;
  ctx.fillText(`${Math.round(cycleAngle)}°`, dialCX, dialCY + 3);

  return { cycleAngle, crankAngle, strokeName };
}

// ── Main draw ──
function drawEngine() {
  const W = canvas.width, H = canvas.height;
  ctx.clearRect(0, 0, W, H);

  const margin = W * 0.03;
  const colW = (W - margin * 2) / 4;
  const scale = Math.min(colW / (ENG.bore * 1.8), H / 400);
  const topY = H * 0.15;

  for (let i = 0; i < 4; i++) {
    const cx = margin + colW * i + colW / 2;
    const info = drawCylinder(i, cx, topY, scale, colW);
    STATE.cylStates[i] = info;
  }

  // Title
  ctx.fillStyle = '#5a6380';
  ctx.font = `${10 * Math.min(scale, 1.5)}px JetBrains Mono`;
  ctx.textAlign = 'center';
  ctx.fillText(`Firing Order: 1-3-4-2  |  CR ${ENG.CR}:1  |  ${ENG.bore}×${ENG.stroke}mm`, W/2, H - 10);
}

// ── P-V Diagram ──
function drawPV() {
  const W = pvCanvas.width, H = pvCanvas.height;
  pvCtx.clearRect(0, 0, W, H);
  const pad = {l:50, r:15, t:20, b:30};
  const pw = W - pad.l - pad.r, ph = H - pad.t - pad.b;

  // Axes
  pvCtx.strokeStyle = '#2a3050';
  pvCtx.lineWidth = 1;
  pvCtx.beginPath();
  pvCtx.moveTo(pad.l, pad.t);
  pvCtx.lineTo(pad.l, pad.t + ph);
  pvCtx.lineTo(pad.l + pw, pad.t + ph);
  pvCtx.stroke();

  pvCtx.fillStyle = '#5a6380';
  pvCtx.font = '9px JetBrains Mono';
  pvCtx.textAlign = 'center';
  pvCtx.fillText('Volume (cm³)', pad.l + pw/2, H - 4);
  pvCtx.save();
  pvCtx.translate(12, pad.t + ph/2);
  pvCtx.rotate(-Math.PI/2);
  pvCtx.fillText('Pressure (bar)', 0, 0);
  pvCtx.restore();

  const vMin = ENG.Vc * 0.9, vMax = ENG.Vmax * 1.1;
  const pMin = 0, pMax = Math.max(STATE.pMax * 1.2, 80);
  const xScale = pw / (vMax - vMin), yScale = ph / (pMax - pMin);
  const toX = v => pad.l + (v - vMin) * xScale;
  const toY = p => pad.t + ph - (p - pMin) * yScale;

  // Grid
  pvCtx.strokeStyle = '#1a1e30';
  pvCtx.lineWidth = 0.5;
  for (let p = 20; p < pMax; p += 20) {
    pvCtx.beginPath(); pvCtx.moveTo(pad.l, toY(p)); pvCtx.lineTo(pad.l+pw, toY(p)); pvCtx.stroke();
    pvCtx.fillStyle = '#5a6380'; pvCtx.textAlign = 'right'; pvCtx.fillText(p, pad.l - 5, toY(p) + 3);
  }

  // PV curve
  pvCtx.beginPath();
  pvCtx.strokeStyle = '#4facfe';
  pvCtx.lineWidth = 1.5;
  for (let ca = 0; ca <= 720; ca += 2) {
    const v = cylinderVolume(ca % 360);
    const p = calcPressureCycle(ca);
    const x = toX(v), y = toY(p);
    ca === 0 ? pvCtx.moveTo(x, y) : pvCtx.lineTo(x, y);
  }
  pvCtx.stroke();

  // Current point for cyl 1
  const ca1 = ((STATE.globalAngle - ENG.phaseOffset[0]) % 720 + 720) % 720;
  const v1 = cylinderVolume(ca1 % 360);
  const p1 = calcPressureCycle(ca1);
  pvCtx.fillStyle = '#ff4444';
  pvCtx.beginPath();
  pvCtx.arc(toX(v1), toY(p1), 4, 0, Math.PI * 2);
  pvCtx.fill();

  pvCtx.fillStyle = '#8892b0';
  pvCtx.textAlign = 'left';
  pvCtx.font = 'bold 10px Inter';
  pvCtx.fillText('P-V Diagram (Cyl 1)', pad.l + 5, pad.t + 12);
}

// ── Pressure-CA Diagram ──
function drawPressureCA() {
  const W = prCanvas.width, H = prCanvas.height;
  prCtx.clearRect(0, 0, W, H);
  const pad = {l:50, r:15, t:20, b:30};
  const pw = W - pad.l - pad.r, ph = H - pad.t - pad.b;

  prCtx.strokeStyle = '#2a3050';
  prCtx.lineWidth = 1;
  prCtx.beginPath();
  prCtx.moveTo(pad.l, pad.t);
  prCtx.lineTo(pad.l, pad.t + ph);
  prCtx.lineTo(pad.l + pw, pad.t + ph);
  prCtx.stroke();

  prCtx.fillStyle = '#5a6380';
  prCtx.font = '9px JetBrains Mono';
  prCtx.textAlign = 'center';
  prCtx.fillText('Crank Angle (°)', pad.l + pw/2, H - 4);

  const caMin = -180, caMax = 180;
  const pMin = 0, pMax = Math.max(STATE.pMax * 1.2, 80);
  const xScale = pw / (caMax - caMin), yScale = ph / (pMax - pMin);
  const toX = a => pad.l + (a - caMin) * xScale;
  const toY = p => pad.t + ph - (p - pMin) * yScale;

  // TDC line
  prCtx.strokeStyle = '#ff444444';
  prCtx.setLineDash([3,3]);
  prCtx.beginPath(); prCtx.moveTo(toX(0), pad.t); prCtx.lineTo(toX(0), pad.t+ph); prCtx.stroke();
  prCtx.setLineDash([]);

  // SOI/EOI markers
  prCtx.strokeStyle = '#00e676';
  prCtx.lineWidth = 2;
  prCtx.beginPath(); prCtx.moveTo(toX(STATE.soi_ATDC), pad.t); prCtx.lineTo(toX(STATE.soi_ATDC), pad.t+ph); prCtx.stroke();
  prCtx.strokeStyle = '#ff9800';
  prCtx.beginPath(); prCtx.moveTo(toX(STATE.eoi_ATDC), pad.t); prCtx.lineTo(toX(STATE.eoi_ATDC), pad.t+ph); prCtx.stroke();

  // SOI/EOI labels
  prCtx.font = '8px JetBrains Mono';
  prCtx.fillStyle = '#00e676';
  prCtx.textAlign = 'right';
  prCtx.fillText('SOI', toX(STATE.soi_ATDC) - 3, pad.t + 12);
  prCtx.fillStyle = '#ff9800';
  prCtx.textAlign = 'left';
  prCtx.fillText('EOI', toX(STATE.eoi_ATDC) + 3, pad.t + 12);

  // Pressure curve (compression-expansion)
  prCtx.beginPath();
  prCtx.strokeStyle = '#4facfe';
  prCtx.lineWidth = 1.5;
  for (let a = -180; a <= 180; a += 1) {
    const ca720 = a < 0 ? 720 + a : a;
    const p = calcPressureCycle(ca720);
    const x = toX(a), y = toY(p);
    a === -180 ? prCtx.moveTo(x, y) : prCtx.lineTo(x, y);
  }
  prCtx.stroke();

  // Current position marker for cyl 1
  const ca1 = ((STATE.globalAngle - ENG.phaseOffset[0]) % 720 + 720) % 720;
  const caATDC = ca1 <= 360 ? ca1 : ca1 - 720;
  if (caATDC >= -180 && caATDC <= 180) {
    const p1 = calcPressureCycle(ca1);
    prCtx.fillStyle = '#ff4444';
    prCtx.beginPath();
    prCtx.arc(toX(caATDC), toY(p1), 4, 0, Math.PI * 2);
    prCtx.fill();
  }

  // Axis labels
  for (let a = -180; a <= 180; a += 60) {
    prCtx.fillStyle = '#5a6380';
    prCtx.font = '8px JetBrains Mono';
    prCtx.textAlign = 'center';
    prCtx.fillText(`${a}°`, toX(a), pad.t + ph + 12);
  }
  for (let p = 20; p < pMax; p += 20) {
    prCtx.fillStyle = '#5a6380';
    prCtx.textAlign = 'right';
    prCtx.fillText(p, pad.l - 5, toY(p) + 3);
  }

  prCtx.fillStyle = '#8892b0';
  prCtx.textAlign = 'left';
  prCtx.font = 'bold 10px Inter';
  prCtx.fillText('P-θ Diagram (Cyl 1)', pad.l + 5, pad.t + 12);
}

// ── Update Metrics Panel ──
function updateMetrics() {
  const set = (id, v) => { const e = document.getElementById(id); if(e) e.textContent = v; };
  const setHTML = (id, v) => { const e = document.getElementById(id); if(e) e.innerHTML = v; };
  const setColor = (id, c) => { const e = document.getElementById(id); if(e) e.style.color = c; };
  set('m-soi', `${STATE.soi_ATDC.toFixed(1)}°`);
  set('m-eoi', `${STATE.eoi_ATDC.toFixed(1)}°`);
  set('m-soc', `${(STATE.soc_ATDC||0).toFixed(1)}°`);
  set('m-igndelay', `${(STATE.socDelay_ms||0).toFixed(2)}`);
  set('m-duration', `${Math.round(STATE.injDuration_us)} / ${STATE.injDuration_deg.toFixed(1)}°`);

  // ── Pmax with angle and color-coded warning ──
  const pmaxAngleStr = STATE.pMaxAngle >= 0 ? `${STATE.pMaxAngle.toFixed(0)}° ATDC` : `${Math.abs(STATE.pMaxAngle).toFixed(0)}° BTDC`;
  set('m-pmax', `${STATE.pMax.toFixed(0)}`);
  set('m-pmax-angle', pmaxAngleStr);
  // Color: green < 160, yellow 160-180, red > 180
  const pmaxColor = STATE.pMax < STATE.pMaxLimit ? '#00e676' :
                    STATE.pMax < STATE.pMaxAbsLimit ? '#ff9800' : '#ff4444';
  setColor('m-pmax', pmaxColor);

  // ── dp/dθ with color-coded warning ──
  const dpAngleStr = STATE.dpMaxAngle >= 0 ? `${STATE.dpMaxAngle.toFixed(0)}° ATDC` : `${Math.abs(STATE.dpMaxAngle).toFixed(0)}° BTDC`;
  set('m-dp', `${STATE.dpMax.toFixed(1)}`);
  set('m-dp-angle', dpAngleStr);
  const dpColor = STATE.dpMax < STATE.dpLimit ? '#00e676' :
                  STATE.dpMax < STATE.dpDanger ? '#ff9800' : '#ff4444';
  setColor('m-dp', dpColor);

  // ── CA50 and thermal efficiency ──
  set('m-ca50', `${(STATE.ca50||0).toFixed(1)}°`);
  set('m-eta', `${((STATE.etaTherm||0)*100).toFixed(1)}%`);

  set('m-tmax', `${Math.round(STATE.tMax)}`);

  const ca1 = ((STATE.globalAngle - ENG.phaseOffset[0]) % 720 + 720) % 720;
  const pLive = calcPressureCycle(ca1);
  const vLive = cylinderVolume(ca1 % 360);
  set('m-pcyl', `${pLive.toFixed(1)}`);
  set('m-vol', `${vLive.toFixed(1)}`);
  set('m-torque', `${(STATE.torque||0).toFixed(0)}`);
  set('m-power', `${(STATE.power||0).toFixed(1)}`);
  set('m-lambda', `${(STATE.lambda||0).toFixed(2)}`);
  set('m-bsfc', `${(STATE.bsfc||0).toFixed(0)}`);
  set('rpm-value-display', STATE.rpm);

  // ── Pmax status panel ──
  const pmaxStatusEl = document.getElementById('pmax-status');
  if (pmaxStatusEl) {
    const cls = STATE.pMax < STATE.pMaxLimit ? 'ok' :
                STATE.pMax < STATE.pMaxAbsLimit ? 'warn' : 'danger';
    pmaxStatusEl.className = 'eoi-status ' + cls;
    const pmaxText = document.getElementById('pmax-status-text');
    const pmaxRec = document.getElementById('pmax-recommendation');
    if (pmaxText) pmaxText.textContent = `${STATE.pMax.toFixed(0)} bar @ ${pmaxAngleStr}`;
    if (pmaxRec) {
      pmaxRec.textContent = STATE.pMax < STATE.pMaxLimit ?
        `Pmax < ${STATE.pMaxLimit} bar — bezpieczne` :
        STATE.pMax < STATE.pMaxAbsLimit ?
        `Pmax ${STATE.pMaxLimit}-${STATE.pMaxAbsLimit} bar — wzmocniona uszczelka wymagana` :
        `Pmax > ${STATE.pMaxAbsLimit} bar — RYZYKO USZKODZENIA! Cofnij SOI lub zmniejsz dawkę`;
    }
  }

  // ── dp/dθ status panel ──
  const dpStatusEl = document.getElementById('dp-status');
  if (dpStatusEl) {
    const cls = STATE.dpMax < STATE.dpLimit ? 'ok' :
                STATE.dpMax < STATE.dpDanger ? 'warn' : 'danger';
    dpStatusEl.className = 'eoi-status ' + cls;
    const dpText = document.getElementById('dp-status-text');
    const dpRec = document.getElementById('dp-recommendation');
    if (dpText) dpText.textContent = `${STATE.dpMax.toFixed(1)} bar/°CA`;
    if (dpRec) {
      dpRec.textContent = STATE.dpMax < STATE.dpLimit ?
        `dp/dθ < ${STATE.dpLimit} — spalanie kontrolowane` :
        STATE.dpMax < STATE.dpDanger ?
        `dp/dθ ${STATE.dpLimit}-${STATE.dpDanger} — podwyższone stukanie` :
        `dp/dθ > ${STATE.dpDanger} — DIESEL KNOCK! Obciążenie łożysk krytyczne`;
    }
  }

  // EOI status
  const eoiEl = document.getElementById('eoi-status');
  const eoiText = document.getElementById('eoi-status-text');
  const eoiRec = document.getElementById('eoi-recommendation');
  if (eoiEl && eoiText) {
    const eoi = STATE.eoi_ATDC;
    eoiEl.className = 'eoi-status ' + (eoi <= 8 ? 'ok' : eoi <= 15 ? 'warn' : 'danger');
    eoiText.textContent = `${eoi.toFixed(1)}° ATDC`;
    if (eoiRec) {
      eoiRec.textContent = eoi <= 8 ? 'EOI before 8° ATDC — optimal' :
        eoi <= 15 ? 'EOI 8-15° — acceptable, monitor PCP' : 'EOI > 15° ATDC — retard SOI or reduce fuel';
    }
  }
}

// ── Cylinder Status Bar ──
function updateCylStatus() {
  for (let i = 0; i < 4; i++) {
    const idx = i + 1;
    const cycleAngle = ((STATE.globalAngle - ENG.phaseOffset[i]) % 720 + 720) % 720;
    // Convert to BTDC/ATDC relative to firing TDC (0°)
    let atdc;
    if (cycleAngle <= 360) {
      atdc = cycleAngle; // 0-360: power & exhaust, positive = ATDC
    } else {
      atdc = cycleAngle - 720; // 360-720: intake & compression, negative = BTDC
    }
    
    const angleEl = document.getElementById(`cyl-angle-${idx}`);
    const injEl = document.getElementById(`cyl-inj-${idx}`);
    if (!angleEl || !injEl) continue;
    
    // Angle display
    if (atdc >= 0) {
      angleEl.textContent = `${atdc.toFixed(0)}° ATDC`;
      angleEl.style.color = atdc < 180 ? '#ff9800' : '#ff4444';
    } else {
      angleEl.textContent = `${Math.abs(atdc).toFixed(0)}° BTDC`;
      angleEl.style.color = Math.abs(atdc) < 180 ? '#b388ff' : '#4facfe';
    }
    
    // Injection status for this cylinder
    const injecting = isInjecting(cycleAngle);
    const burning = isBurning(cycleAngle);
    const soiCA = ((720 + STATE.soi_ATDC) % 720);
    const eoiCA = ((720 + STATE.eoi_ATDC) % 720);
    const distToSOI = ((soiCA - cycleAngle) + 720) % 720;
    const distToEOI = ((eoiCA - cycleAngle) + 720) % 720;
    
    if (injecting) {
      injEl.innerHTML = `<span style="color:#00f2fe;font-weight:600">◆ WTRYSK</span> <span style="color:#ff9800">EOI za ${distToEOI.toFixed(0)}°</span>`;
    } else if (burning) {
      injEl.innerHTML = `<span style="color:#ff6e40;font-weight:600">🔥 SPALANIE</span>`;
    } else if (distToSOI < 60 && distToSOI > 0) {
      injEl.innerHTML = `<span style="color:#00e676">SOI za ${distToSOI.toFixed(0)}°</span>`;
    } else {
      injEl.innerHTML = `<span style="color:#3a4570">—</span>`;
    }
  }
}

// ── UI Bindings ──
let _wasPlayingBeforeDrag = false;
function bindControls() {
  const sliders = {
    'ctrl-rpm':     {key:'rpm',     fmt:v=>`${v} RPM`,        target:'val-rpm'},
    'ctrl-fuel':    {key:'fuel',    fmt:v=>`${parseFloat(v).toFixed(1)} mg / ${(parseFloat(v)/0.835).toFixed(1)} mm³`, target:'val-fuel'},
    'ctrl-soi':     {key:'soiBTDC', fmt:v=>`${parseFloat(v).toFixed(1)}° BTDC`, target:'val-soi'},
    'ctrl-boost':   {key:'boost',   fmt:v=>`${parseFloat(v).toFixed(2)} bar`, target:'val-boost'},
    'ctrl-rail':    {key:'rail',    fmt:v=>`${v} bar`,        target:'val-rail'},
    'ctrl-tintake': {key:'tIntake', fmt:v=>`${v} °C`,         target:'val-tintake'},
  };
  Object.entries(sliders).forEach(([id, cfg]) => {
    const el = document.getElementById(id);
    if (!el) return;
    // Pause animation while dragging slider
    const startDrag = () => {
      _wasPlayingBeforeDrag = STATE.playing;
      STATE.playing = false;
    };
    const endDrag = () => {
      if (_wasPlayingBeforeDrag) STATE.playing = true;
    };
    el.addEventListener('mousedown', startDrag);
    el.addEventListener('touchstart', startDrag, {passive:true});
    el.addEventListener('mouseup', endDrag);
    el.addEventListener('touchend', endDrag);
    // Also listen on document for mouseup in case user drags outside slider
    el.addEventListener('mousedown', () => {
      const docUp = () => { endDrag(); document.removeEventListener('mouseup', docUp); };
      document.addEventListener('mouseup', docUp);
    });

    el.addEventListener('input', () => {
      STATE[cfg.key] = parseFloat(el.value);
      document.getElementById(cfg.target).textContent = cfg.fmt(el.value);
      calcMetrics();
      updateMetrics();
      drawEngine();
      drawPV();
      drawPressureCA();
      if (STATE.useEcuMaps) updateEcuPanel();
    });
  });

  // Presets
  document.querySelectorAll('.preset-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const p = PRESETS[btn.dataset.preset];
      if (!p) return;
      document.querySelectorAll('.preset-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      Object.entries(p).forEach(([k, v]) => { STATE[k] = v; });
      Object.entries(sliders).forEach(([id, cfg]) => {
        const el = document.getElementById(id);
        if (el) { el.value = STATE[cfg.key]; document.getElementById(cfg.target).textContent = cfg.fmt(STATE[cfg.key]); }
      });
      calcMetrics();
      updateMetrics();
    });
  });

  // Play/Pause
  const playBtn = document.getElementById('btn-play');
  
  playBtn.addEventListener('click', () => {
    STATE.playing = !STATE.playing;
    playBtn.textContent = STATE.playing ? '⏸ Pause' : '▶ Play';
    playBtn.classList.toggle('paused', !STATE.playing);
  });

  // Crank angle scrubber — auto-pause on drag, resume on release
  const crankSlider = document.getElementById('ctrl-crank');
  const crankLabel = document.getElementById('val-crank');
  let _wasPlayingBeforeCrank = false;
  if (crankSlider) {
    const startCrankDrag = () => {
      _wasPlayingBeforeCrank = STATE.playing;
      STATE.playing = false;
      playBtn.textContent = '▶ Play';
      playBtn.classList.add('paused');
    };
    const endCrankDrag = () => {
      if (_wasPlayingBeforeCrank) {
        STATE.playing = true;
        playBtn.textContent = '⏸ Pause';
        playBtn.classList.remove('paused');
      }
    };
    crankSlider.addEventListener('mousedown', startCrankDrag);
    crankSlider.addEventListener('touchstart', startCrankDrag, {passive:true});
    crankSlider.addEventListener('mousedown', () => {
      const docUp = () => { endCrankDrag(); document.removeEventListener('mouseup', docUp); };
      document.addEventListener('mouseup', docUp);
    });
    crankSlider.addEventListener('input', () => {
      STATE.globalAngle = parseFloat(crankSlider.value);
      if (crankLabel) crankLabel.textContent = `${Math.round(STATE.globalAngle)}°`;
      calcMetrics();
      drawEngine(); drawPV(); drawPressureCA();
      updateMetrics(); updateCylStatus();
      if (STATE.useEcuMaps) updateEcuPanel();
    });
  }

  // Pedal slider
  const pedalSlider = document.getElementById('ctrl-pedal');
  const pedalLabel = document.getElementById('val-pedal');
  if (pedalSlider) {
    pedalSlider.addEventListener('input', () => {
      STATE.pedal = parseFloat(pedalSlider.value);
      if (pedalLabel) pedalLabel.textContent = `${Math.round(STATE.pedal)} %`;
      if (STATE.useEcuMaps) {
        calcMetrics(); updateMetrics(); updateEcuPanel();
        drawEngine(); drawPV(); drawPressureCA();
      }
    });
  }

  // Speed
  document.querySelectorAll('.speed-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.speed-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      STATE.speed = parseFloat(btn.dataset.speed);
    });
  });
}

// ── Animation Loop ──
let frameCount = 0;
function animate(time) {
  if (!STATE.lastTime) STATE.lastTime = time;
  const dt = Math.min((time - STATE.lastTime) / 1000, 0.05);
  STATE.lastTime = time;

  if (STATE.playing) {
    const degsPerSec = STATE.rpm * 6 * STATE.speed;
    STATE.globalAngle = (STATE.globalAngle + degsPerSec * dt) % 720;
    // Sync crank scrubber
    const cs = document.getElementById('ctrl-crank');
    const cl = document.getElementById('val-crank');
    if (cs) { cs.value = Math.round(STATE.globalAngle); }
    if (cl) { cl.textContent = `${Math.round(STATE.globalAngle)}°`; }
  }

  drawEngine();

  if (frameCount % 3 === 0) {
    drawPV();
    drawPressureCA();
    updateMetrics();
    updateCylStatus();
    if (STATE.useEcuMaps) updateEcuPanel();
  }
  frameCount++;
  requestAnimationFrame(animate);
}

// ── Init ──
function init() {
  bindControls();
  // ECU Maps toggle
  const ecuToggle = document.getElementById('ctrl-ecu-maps');
  if (ecuToggle) {
    ecuToggle.addEventListener('change', () => {
      STATE.useEcuMaps = ecuToggle.checked;
      // Disable manual sliders when ECU mode is on (but keep RPM & pedal active)
      ['ctrl-fuel','ctrl-soi','ctrl-boost','ctrl-rail'].forEach(id => {
        const el = document.getElementById(id);
        if(el) { el.disabled = ecuToggle.checked; el.style.opacity = ecuToggle.checked ? '0.4' : '1'; }
      });
      // Enable pedal slider highlight in ECU mode
      const pedalSlider = document.getElementById('ctrl-pedal');
      if (pedalSlider) pedalSlider.style.opacity = ecuToggle.checked ? '1' : '0.6';
      calcMetrics();
      updateMetrics();
      updateEcuPanel();
    });
  }
  calcMetrics();
  updateMetrics();
  STATE.playing = true;
  document.getElementById('btn-play').textContent = '⏸ Pause';
  requestAnimationFrame(animate);
}

init();
