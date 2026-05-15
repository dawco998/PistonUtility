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
  set('m-soi', `${STATE.soi_ATDC.toFixed(1)}°`);
  set('m-eoi', `${STATE.eoi_ATDC.toFixed(1)}°`);
  set('m-soc', `${(STATE.soc_ATDC||0).toFixed(1)}°`);
  set('m-igndelay', `${(STATE.socDelay_ms||0).toFixed(2)}`);
  set('m-duration', `${Math.round(STATE.injDuration_us)} / ${STATE.injDuration_deg.toFixed(1)}°`);
  set('m-pmax', `${STATE.pMax.toFixed(0)}`);
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

// ── UI Bindings ──
let _wasPlayingBeforeDrag = false;
function bindControls() {
  const sliders = {
    'ctrl-rpm':     {key:'rpm',     fmt:v=>`${v} RPM`,        target:'val-rpm'},
    'ctrl-fuel':    {key:'fuel',    fmt:v=>`${parseFloat(v).toFixed(1)} mg`, target:'val-fuel'},
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
      // Force immediate redraw so pistons update in real-time while paused
      drawEngine();
      drawPV();
      drawPressureCA();
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
    // degrees per second = RPM * 360 / 60 = RPM * 6
    // But we track 720° cycle, so degsPerSec applies directly
    const degsPerSec = STATE.rpm * 6 * STATE.speed;
    STATE.globalAngle = (STATE.globalAngle + degsPerSec * dt) % 720;
  }

  drawEngine();

  if (frameCount % 3 === 0) {
    drawPV();
    drawPressureCA();
    updateMetrics();
  }
  frameCount++;
  requestAnimationFrame(animate);
}

// ── Init ──
function init() {
  bindControls();
  calcMetrics();
  updateMetrics();
  STATE.playing = true;
  document.getElementById('btn-play').textContent = '⏸ Pause';
  requestAnimationFrame(animate);
}

init();
