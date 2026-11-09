/* FUEL LAB explainer-graphics engine (HyperFrames: one paused GSAP timeline, seek-safe, deterministic).
   window.SPEC = {id, mode:"full"|"panel", dur, kind, bg:"paper"|"ink"|"green", idx, tag, data:{...}}
   Motion grammar: fast in (6-12 frames, expo/back-out, 2-3 frame staggers) / calm hold with a slow push / fast out. */
(function () {
  "use strict";
  const S = window.SPEC;
  const FULL = S.mode === "full";
  const W = FULL ? 1920 : 840, H = FULL ? 1080 : 780;
  const DUR = S.dur;
  const D = S.data || {};
  const NS = "http://www.w3.org/2000/svg";
  const THEMES = {
    paper: { bg: "#EFEBE3", fg: "#0D0D0D", mut: "#6f695f", line: "rgba(13,13,13,.075)", a: "#FF5A1F", a2: "#FFD84D", card: "#E5E0D5", ext: "#A8380F", hl: "#FFD84D", hlfg: "#0D0D0D", soft: "rgba(13,13,13,.10)", grain: .10, blend: "multiply", pos: "#1F6B45", neg: "#FF5A1F" },
    ink: { bg: "#0D0D0D", fg: "#EFEBE3", mut: "#9a958b", line: "rgba(239,235,227,.06)", a: "#FF5A1F", a2: "#FFD84D", card: "#1A1A1A", ext: "#6E2408", hl: "#FF5A1F", hlfg: "#0D0D0D", soft: "rgba(239,235,227,.10)", grain: .16, blend: "screen", pos: "#FFD84D", neg: "#FF5A1F" },
    green: { bg: "#1F6B45", fg: "#F4F1EA", mut: "#b9dcc8", line: "#2E8A5C", a: "#FFD84D", a2: "#FF5A1F", card: "#185A39", ext: "#8F6F12", hl: "#FFD84D", hlfg: "#0D0D0D", soft: "rgba(255,255,255,.12)", grain: .12, blend: "overlay", pos: "#FFD84D", neg: "#FF5A1F" },
  };
  const TH = THEMES[S.bg] || THEMES.paper;
  const CB = FULL ? { x: 96, y: 150, w: 1728, h: 690 } : { x: 44, y: 100, w: 752, h: 640 };
  const fs = (a, b) => (FULL ? a : b) + "px";
  const F = (a, b) => (FULL ? a : b);

  // ------------------------------------------------------------------ deterministic random
  let seed = 0; for (const c of S.id) seed = (seed * 31 + c.charCodeAt(0)) >>> 0;
  function rnd() { seed |= 0; seed = (seed + 0x6D2B79F5) | 0; let t = Math.imul(seed ^ (seed >>> 15), 1 | seed); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }

  // ------------------------------------------------------------------ DOM helpers
  function el(tag, cls, parent, style, html) {
    const e = document.createElement(tag);
    if (cls) e.className = cls;
    if (style) Object.assign(e.style, style);
    if (html !== undefined) e.innerHTML = html;
    if (parent) parent.appendChild(e);
    return e;
  }
  function sv(tag, attrs, parent) {
    const e = document.createElementNS(NS, tag);
    for (const k in attrs || {}) e.setAttribute(k, attrs[k]);
    if (parent) parent.appendChild(e);
    return e;
  }
  const abs = (x, y, w, h) => { const o = { position: "absolute", left: x + "px", top: y + "px" }; if (w !== undefined && w !== null) o.width = w + "px"; if (h !== undefined && h !== null) o.height = h + "px"; return o; };
  // mini markup: *serif italic*  [marker highlight]  {accent colour}  ^accent2^
  function rich(s) {
    return String(s || "")
      .replace(/\*([^*]+)\*/g, '<span class="ser">$1</span>')
      .replace(/\[([^\]]+)\]/g, '<span class="mark">$1</span>')
      .replace(/\{([^}]+)\}/g, '<span class="acc">$1</span>')
      .replace(/\^([^^]+)\^/g, '<span class="a2">$1</span>');
  }
  function fit(node, maxW, maxH, minPx) {
    let f = parseFloat(getComputedStyle(node).fontSize), g = 0;
    const over = () => (maxW && Math.max(node.scrollWidth, node.offsetWidth) > maxW + 1) || (maxH && Math.max(node.scrollHeight, node.offsetHeight) > maxH + 1);
    while (over() && f > (minPx || 12) && g++ < 90) { f *= 0.955; node.style.fontSize = f + "px"; }
    return f;
  }

  // ------------------------------------------------------------------ icons (48 grid, stroke = currentColor)
  const ICONS = {
    alarm: '<circle cx="24" cy="27" r="15"/><path d="M24 19v8l5 4"/><path d="M8 12l6-5M40 12l-6-5"/>',
    shake: '<path d="M13 16h22l-3 27H16z"/><path d="M11 16h26"/><path d="M25 16l4-10h7"/><path d="M15 27h18"/>',
    bowl: '<path d="M5 22h38a19 19 0 0 1-38 0z"/><path d="M17 41h14"/><path d="M15 16c2-3 4-3 6 0M27 14c2-3 4-3 6 0"/>',
    plate: '<circle cx="24" cy="25" r="17"/><circle cx="24" cy="25" r="10"/>',
    apple: '<path d="M24 15c-4-3-14-3-14 9 0 10 7 19 14 17 7 2 14-7 14-17 0-12-10-12-14-9z"/><path d="M24 15c0-4 2-7 5-8"/>',
    banana: '<path d="M7 13c4 19 22 27 35 18-11 2-23-4-29-20z"/><path d="M7 13l-1-5"/>',
    orange: '<circle cx="24" cy="27" r="15"/><path d="M24 12c0-3 2-6 6-7 0 4-2 7-6 7z"/><path d="M15 26a9 9 0 0 1 8-8"/>',
    drop: '<path d="M24 5C24 5 11 20 11 29a13 13 0 0 0 26 0C37 20 24 5 24 5z"/><path d="M18 30a6 6 0 0 0 5 6"/>',
    bottle: '<path d="M19 4h10v6l4 5v27a3 3 0 0 1-3 3H18a3 3 0 0 1-3-3V15l4-5z"/><path d="M15 22h18M15 34h18"/>',
    scale: '<rect x="6" y="9" width="36" height="33" rx="5"/><path d="M15 21a9 9 0 0 1 18 0"/><path d="M24 21l4-5"/>',
    run: '<circle cx="31" cy="8" r="4"/><path d="M28 15l-6 12 7 5-2 10"/><path d="M22 27l-6 7H9"/><path d="M27 17l7 5 5-3"/><path d="M27 17l-9 2-4 6"/>',
    bike: '<circle cx="11" cy="32" r="8"/><circle cx="37" cy="32" r="8"/><path d="M11 32l8-14h12l6 14M19 18l6 14H11M25 32l6-14M16 13h6M31 18l-2-6h5"/>',
    dumbbell: '<path d="M6 19v10M11 14v20M37 14v20M42 19v10M11 24h26"/>',
    moon: '<path d="M30 6a18 18 0 1 0 12 26A15 15 0 0 1 30 6z"/>',
    sun: '<circle cx="24" cy="24" r="8"/><path d="M24 4v6M24 38v6M4 24h6M38 24h6M10 10l4 4M34 34l4 4M10 38l4-4M34 14l4-4"/>',
    egg: '<path d="M24 5c-8 0-14 13-14 22a14 14 0 0 0 28 0C38 18 32 5 24 5z"/>',
    sandwich: '<path d="M5 29L24 9l19 20z"/><path d="M5 29v7h38v-7"/><path d="M10 25h28"/>',
    can: '<ellipse cx="24" cy="14" rx="16" ry="5"/><path d="M8 14v20c0 3 7 5 16 5s16-2 16-5V14"/><path d="M8 24c0 3 7 5 16 5s16-2 16-5"/>',
    carrot: '<path d="M34 14c-3-3-7-2-9 0L8 37c-1 2 1 4 3 3l23-17c2-2 3-6 0-9z"/><path d="M34 14l6-6M36 18l7-1M30 12l1-7"/><path d="M20 22l3 3M15 28l3 3"/>',
    leaf: '<path d="M9 39C9 19 21 9 40 8c0 19-11 31-31 31z"/><path d="M9 39L29 19"/>',
    calendar: '<rect x="6" y="9" width="36" height="33" rx="3"/><path d="M6 18h36M15 5v8M33 5v8"/><path d="M14 26h4M22 26h4M30 26h4M14 33h4M22 33h4"/>',
    salt: '<path d="M16 19h16l3 23H13z"/><path d="M17 19c0-8 3-12 7-12s7 4 7 12"/><path d="M21 12h.1M27 12h.1M24 10h.1"/>',
    gel: '<path d="M14 5h20l-2 7v26l-8 6-8-6V12z"/><path d="M18 21h12M18 28h12"/>',
    bolt: '<path d="M27 4L10 27h12l-3 17 19-24H26z"/>',
    flame: '<path d="M24 4c3 9 13 13 13 25a13 13 0 0 1-26 0c0-7 4-10 6-15 2 5 4 6 7 6-2-6-2-11 0-16z"/>',
    battery: '<rect x="5" y="15" width="34" height="18" rx="3"/><path d="M43 21v6"/><path d="M11 21v6M17 21v6"/>',
    check: '<path d="M8 25l10 10 22-22"/>',
    cross: '<path d="M12 12l24 24M36 12L12 36"/>',
    fridge: '<rect x="11" y="4" width="26" height="40" rx="3"/><path d="M11 18h26M16 9v5M16 23v8"/>',
    pan: '<circle cx="20" cy="26" r="13"/><path d="M33 26h12"/><path d="M15 24a5 5 0 0 1 5-5"/>',
    office: '<rect x="10" y="6" width="28" height="38"/><path d="M17 14h4M27 14h4M17 22h4M27 22h4M17 30h4M27 30h4M21 44v-7h6v7"/>',
    home: '<path d="M6 22L24 7l18 15"/><path d="M11 18v24h26V18"/><path d="M20 42V30h8v12"/>',
    flask: '<path d="M19 5h10M21 5v13L9 39a3 3 0 0 0 3 4h24a3 3 0 0 0 3-4L27 18V5"/><path d="M14 30h20"/>',
    doc: '<path d="M11 4h18l9 9v31H11z"/><path d="M29 4v9h9"/><path d="M17 22h15M17 29h15M17 36h10"/>',
    pill: '<rect x="5" y="17" width="38" height="14" rx="7" transform="rotate(-40 24 24)"/><path d="M24 17v14" transform="rotate(-40 24 24)"/>',
    shield: '<path d="M24 4l16 6v12c0 11-7 18-16 22C15 40 8 33 8 22V10z"/><path d="M17 24l5 5 9-10"/>',
    heart: '<path d="M24 41S6 30 6 17a9 9 0 0 1 18-3 9 9 0 0 1 18 3c0 13-18 24-18 24z"/>',
    person: '<circle cx="24" cy="10" r="5"/><path d="M14 44V26a10 10 0 0 1 20 0v18"/>',
    clock: '<circle cx="24" cy="24" r="18"/><path d="M24 13v11l7 4"/>',
    spark: '<path d="M24 5v9M24 34v9M5 24h9M34 24h9M11 11l6 6M31 31l6 6M11 37l6-6M31 17l6-6"/>',
    swim: '<path d="M4 36c4 3 8 3 12 0s8-3 12 0 8 3 12 0 4-2 6-1"/><circle cx="33" cy="14" r="4"/><path d="M8 28l10-8 8 6 6-4"/>',
    bar: '<rect x="5" y="16" width="38" height="16" rx="2"/><path d="M11 16v16M37 16v16"/><path d="M17 24h14"/>',
    jar: '<path d="M14 13h20v27a4 4 0 0 1-4 4H18a4 4 0 0 1-4-4z"/><path d="M12 6h24v7H12z"/><path d="M14 27h20"/>',
    toaster: '<rect x="6" y="20" width="36" height="22" rx="5"/><path d="M14 20V10h8v10M26 20V8h8v12"/><path d="M42 28h4"/>',
    arm: '<path d="M8 38c3-14 9-25 16-28 4-1 7 3 3 6l-5 4c5 3 13 2 17 8 3 4 1 10-5 10-9 1-17 1-26 0z"/>',
    chicken: '<path d="M31 6a11 11 0 0 1 11 11c0 8-8 13-15 13l-8 8a4 4 0 1 1-6 3 4 4 0 1 1 3-6l8-8c0-8 2-21 7-21z"/>',
    tomato: '<circle cx="24" cy="27" r="15"/><path d="M17 13l7 4 7-4M24 17V8"/>',
    coffee: '<path d="M8 17h26v13a10 10 0 0 1-10 10h-6A10 10 0 0 1 8 30z"/><path d="M34 21h3a5 5 0 0 1 0 10h-3"/><path d="M15 5v6M21 5v6M27 5v6"/>',
    yogurt: '<path d="M10 15h28l-4 28H14z"/><path d="M8 15h32"/><path d="M13 25h22"/>',
    rice: '<path d="M5 24h38a19 19 0 0 1-38 0z"/><path d="M11 24c2-7 7-10 13-10s11 3 13 10"/><path d="M19 19h.1M25 17h.1M30 20h.1"/>',
    wrap: '<path d="M10 38L34 8c3-2 7 2 5 5L15 42c-2 2-6 0-5-4z"/><path d="M18 28l10 8M23 21l10 8"/>',
    snow: '<path d="M24 4v40M7 14l34 20M7 34l34-20"/><path d="M19 7l5 4 5-4M19 41l5-4 5 4"/>',
    brain: '<path d="M24 10a7 7 0 0 0-12 3 7 7 0 0 0-4 12 7 7 0 0 0 6 11 7 7 0 0 0 10 2zM24 10a7 7 0 0 1 12 3 7 7 0 0 1 4 12 7 7 0 0 1-6 11 7 7 0 0 1-10 2z"/><path d="M24 10v28"/>',
    bed: '<path d="M4 38V12M4 30h40v8M44 30v-6a6 6 0 0 0-6-6H20v12"/><circle cx="12" cy="23" r="4"/>',
    fork: '<path d="M14 5v12a5 5 0 0 0 10 0V5M19 5v38"/><path d="M34 43V5c-5 3-7 9-7 16h7"/>',
    laptop: '<rect x="9" y="10" width="30" height="21" rx="2"/><path d="M4 38h40l-4-7H8z"/>',
    pin: '<path d="M24 44S10 29 10 19a14 14 0 0 1 28 0c0 10-14 25-14 25z"/><circle cx="24" cy="19" r="5"/>',
    tshirt: '<path d="M17 6l-11 6 4 9 5-2v23h18V19l5 2 4-9-11-6a7 7 0 0 1-14 0z"/>',
    nut: '<path d="M24 6c8 0 13 6 13 14 0 10-7 22-13 22S11 30 11 20c0-8 5-14 13-14z"/><path d="M17 16c3-3 11-3 14 0"/>',
  };
  function icon(name, size, parent, style, sw) {
    const s = sv("svg", { viewBox: "0 0 48 48", width: size, height: size, fill: "none", stroke: "currentColor", "stroke-width": sw || 3, "stroke-linecap": "round", "stroke-linejoin": "round" }, parent);
    s.innerHTML = ICONS[name] || ICONS.spark;
    if (style) Object.assign(s.style, style);
    s.querySelectorAll("path,circle,rect,ellipse,line,polyline").forEach(p => { p.setAttribute("pathLength", "1"); p.style.strokeDasharray = "1"; p.style.strokeDashoffset = "0"; });
    return s;
  }

  // ------------------------------------------------------------------ root + layers
  const root = document.getElementById("root");
  root.style.setProperty("--bg", TH.bg); root.style.setProperty("--fg", TH.fg); root.style.setProperty("--mut", TH.mut);
  root.style.setProperty("--a", TH.a); root.style.setProperty("--a2", TH.a2); root.style.setProperty("--card", TH.card);
  root.style.setProperty("--hl", TH.hl); root.style.setProperty("--hlfg", TH.hlfg); root.style.setProperty("--grain-op", TH.grain); root.style.setProperty("--grain-blend", TH.blend);
  document.body.style.background = TH.bg;
  const bg = el("div", "", root); bg.id = "bg";
  const gridl = el("div", "", bg); gridl.id = "gridl";
  const G = S.bg === "green" ? 96 : 48;
  const gw = S.bg === "green" ? 2 : 1;
  gridl.style.backgroundImage = `linear-gradient(${TH.line} ${gw}px, transparent ${gw}px), linear-gradient(90deg, ${TH.line} ${gw}px, transparent ${gw}px)`;
  gridl.style.backgroundSize = `${G}px ${G}px`;
  gridl.style.backgroundPosition = `${(FULL ? 96 : 44) + 120}px ${(FULL ? 54 : 30) + 120}px`;
  const stage = el("div", "", root); stage.id = "stage";
  stage.style.perspective = (FULL ? 2200 : 1500) + "px";
  const world = el("div", "", stage); world.id = "world";
  const grain = el("div", "", root); grain.id = "grain";

  const tl = gsap.timeline({ paused: true });
  const EX = [];          // groups that exit together
  const T0 = 0.12;        // first entrance
  const TE = DUR - 0.36;  // exit start

  // ------------------------------------------------------------------ motion helpers
  const E_IN = "expo.out", E_BACK = "back.out(1.7)";
  function fin(e, t, o) { o = o || {}; tl.fromTo(e, { opacity: 0, y: o.y !== undefined ? o.y : F(40, 26), x: o.x || 0 }, { opacity: 1, y: 0, x: 0, duration: o.d || 0.42, ease: o.ease || E_IN }, t); }
  function wipe(e, t, o) { o = o || {}; const from = { r: "inset(0% 100% 0% 0%)", l: "inset(0% 0% 0% 100%)", u: "inset(100% 0% 0% 0%)", d: "inset(0% 0% 100% 0%)" }[o.dir || "r"]; tl.fromTo(e, { clipPath: from, webkitClipPath: from }, { clipPath: "inset(0% 0% 0% 0%)", webkitClipPath: "inset(0% 0% 0% 0%)", duration: o.d || 0.4, ease: o.ease || "expo.inOut" }, t); }
  function pop(e, t, o) { o = o || {}; tl.fromTo(e, { opacity: 0, scale: o.s || 0.4 }, { opacity: 1, scale: 1, duration: o.d || 0.45, ease: o.ease || "back.out(2.2)" }, t); }
  function drop(e, t, rot, o) { o = o || {}; tl.fromTo(e, { opacity: 0, y: o.y || -F(110, 70), rotation: (rot || 0) * 3.5, scale: 1.08 }, { opacity: 1, y: 0, rotation: rot || 0, scale: 1, duration: o.d || 0.55, ease: "back.out(1.3)" }, t); }
  function draw(svgOrEl, t, d, stagger) {
    const parts = svgOrEl.matches && svgOrEl.matches("path,circle,rect,ellipse,line,polyline") ? [svgOrEl] : Array.from(svgOrEl.querySelectorAll("path,circle,rect,ellipse,line,polyline"));
    parts.forEach(p => { p.setAttribute("pathLength", "1"); p.style.strokeDasharray = "1"; });
    tl.fromTo(parts, { strokeDashoffset: 1 }, { strokeDashoffset: 0, duration: d || 0.6, ease: "power2.inOut", stagger: stagger === undefined ? 0.05 : stagger }, t);
  }
  function type(e, t, cps) {
    const txt = e.textContent; e.textContent = "";
    const spans = [...txt].map(ch => el("span", "", e, null, ch === " " ? "&nbsp;" : ch));
    tl.fromTo(spans, { opacity: 0 }, { opacity: 1, duration: 0.01, stagger: 1 / (cps || 55), ease: "none" }, t);
  }
  function markIn(scope, t) { const m = scope.querySelectorAll(".mark"); if (m.length) tl.fromTo(m, { backgroundSize: "0% 86%" }, { backgroundSize: "100% 86%", duration: 0.45, ease: "power3.inOut", stagger: 0.12 }, t); }
  function ex(e) { EX.push(e); return e; }
  function blurFilter() {
    const id = "mb" + Math.floor(rnd() * 1e9);
    const s = sv("svg", { width: 0, height: 0, style: "position:absolute" }, root);
    const f = sv("filter", { id, x: "-20%", y: "-60%", width: "140%", height: "220%" }, s);
    const g = sv("feGaussianBlur", { in: "SourceGraphic", stdDeviation: "0 0" }, f);
    return { id, node: g };
  }
  function contentW(row) { let w = 0; [...row.children].forEach(c => { w = Math.max(w, c.offsetLeft + c.offsetWidth); }); return w; }
  function extrude(n, col, step) { const out = []; for (let i = 1; i <= n; i++) out.push(`${i * step}px ${i * step}px 0 ${col}`); return out.join(","); }

  // rolling digits (slot-machine) with vertical motion blur riding the same ease
  function roller(parent, str, o) {
    o = o || {};
    let fsz = o.size; const lh = 1.0;
    const wrap = el("span", "disp nowrap", parent, { display: "inline-flex", alignItems: "flex-start", fontSize: fsz + "px", lineHeight: lh, color: o.color || "var(--a)" });
    if (o.ext !== false) wrap.style.textShadow = extrude(o.extN || F(12, 7), o.extC || TH.ext, o.extS || F(1.6, 1.3));
    const bf = blurFilter(); wrap.style.filter = `url(#${bf.id})`;
    const cells = [];
    let k = 0;
    for (const ch of String(str)) {
      if (/[0-9]/.test(ch)) {
        const d = +ch;
        const cell = el("span", "", wrap, { display: "inline-block", height: fsz * lh + "px", position: "relative", clipPath: "inset(-3% -60% -6% -30%)", overflow: "visible" });
        const meas = el("span", "", cell, { visibility: "hidden" }, ch);
        const strip = el("span", "", cell, { position: "absolute", left: "50%", top: "0", display: "flex", flexDirection: "column", alignItems: "center", transform: "translateX(-50%)" });
        const cyc = 1 + ((k + o.seed || 0) % 2);
        const start = Math.floor(rnd() * 10);
        const seq = []; for (let i = 0; i < cyc * 10; i++) seq.push((start + i) % 10);
        while (seq[seq.length - 1] !== d) seq.push((seq[seq.length - 1] + 1) % 10);
        seq.forEach(v => el("span", "", strip, { display: "block", height: fsz * lh + "px", lineHeight: lh }, String(v)));
        cells.push({ strip, n: seq.length - 1, cell, meas });
        k++;
      } else {
        const sp = el("span", "", wrap, { display: "inline-block", whiteSpace: "pre" }, ch === " " ? "&nbsp;" : ch);
        cells.push({ stat: sp });
      }
    }
    wrap._scale = function (k) {
      fsz *= k; wrap.style.fontSize = fsz + "px";
      cells.forEach(c => { if (c.cell) { c.cell.style.height = fsz * lh + "px"; c.strip.querySelectorAll("span").forEach(s => s.style.height = fsz * lh + "px"); } });
    };
    wrap._size = () => fsz;
    wrap._anim = function (t, dur) {
      dur = dur || 1.1;
      let i = 0;
      cells.forEach(c => {
        if (c.stat) { tl.fromTo(c.stat, { opacity: 0, y: fsz * 0.25 }, { opacity: 1, y: 0, duration: 0.3, ease: E_IN }, t + 0.1 + i * 0.04); }
        else { tl.fromTo(c.strip, { y: 0 }, { y: -c.n * fsz * lh, duration: dur + i * 0.06, ease: "expo.out" }, t + i * 0.05); }
        i++;
      });
      const pr = { v: F(26, 16) };
      const wr = () => bf.node.setAttribute("stdDeviation", `0 ${pr.v.toFixed(2)}`);
      wr();
      tl.fromTo(pr, { v: F(26, 16) }, { v: 0, duration: dur * 0.9, ease: "expo.out", onUpdate: wr }, t);
      tl.fromTo(wrap, { opacity: 0 }, { opacity: 1, duration: 0.12 }, t);
    };
    return wrap;
  }
  function countText(e, from, to, dec, t, d, fmt) {
    const p = { v: from };
    const wr = () => { e.textContent = (fmt || (v => v.toFixed(dec)))(p.v); };
    wr();
    tl.fromTo(p, { v: from }, { v: to, duration: d, ease: "power2.inOut", onUpdate: wr }, t);
  }

  // ------------------------------------------------------------------ chrome: header + marks
  function header() {
    const g = ex(el("div", "abs", world, Object.assign(abs(CB.x, F(58, 32), CB.w, F(44, 34)), { display: "flex", alignItems: "center", gap: F(18, 12) + "px" })));
    const idx = el("div", "mono", g, { fontSize: fs(21, 15), border: `3px solid ${TH.fg}`, padding: F(5, 3) + "px " + F(10, 7) + "px " + F(3, 2) + "px", lineHeight: 1, letterSpacing: ".06em" }, S.idx || "00");
    const tag = el("div", "mono", g, { fontSize: fs(21, 15), color: TH.a, whiteSpace: "nowrap", lineHeight: 1 }, S.tag || "");
    const rule = el("div", "", g, { flex: "1", height: "3px", background: TH.fg, transformOrigin: "0 50%" });
    const br = el("div", "mono", g, { fontSize: fs(16, 12), color: TH.mut, whiteSpace: "nowrap", lineHeight: 1 }, S.brand || "FUEL LAB");
    const ch = sv("svg", { width: F(28, 22), height: F(28, 22), viewBox: "0 0 28 28", fill: "none", stroke: TH.fg, "stroke-width": 2 }, g);
    ch.innerHTML = '<circle cx="14" cy="14" r="7"/><path d="M14 0v28M0 14h28"/>';
    pop(idx, 0.04, { d: 0.35 });
    type(tag, 0.1, 60);
    tl.fromTo(rule, { scaleX: 0 }, { scaleX: 1, duration: 0.5, ease: "expo.inOut" }, 0.08);
    tl.fromTo([br, ch], { opacity: 0 }, { opacity: 1, duration: 0.3, stagger: 0.05 }, 0.3);
    tl.fromTo(ch, { rotation: -90 }, { rotation: 0, duration: 0.6, ease: E_IN }, 0.3);
    // registration marks at the bottom corners of the content box (above the caption zone)
    const yb = CB.y + CB.h - F(6, 0);
    [CB.x, CB.x + CB.w].forEach((x, i) => {
      const m = sv("svg", { width: 22, height: 22, viewBox: "0 0 22 22", fill: "none", stroke: TH.mut, "stroke-width": 2 }, world);
      Object.assign(m.style, abs(x - 11, yb - 11));
      m.innerHTML = '<path d="M11 0v22M0 11h22"/>';
      ex(m); tl.fromTo(m, { opacity: 0, scale: 0 }, { opacity: 0.7, scale: 1, duration: 0.35, ease: E_BACK }, 0.25 + i * 0.05);
    });
  }
  function title(txt, o) {
    o = o || {};
    const t = el("div", "disp", world, Object.assign(abs(o.x || CB.x, o.y || CB.y, o.w || CB.w), { fontSize: fs(o.f || 70, o.fp || 46), color: o.color || TH.fg }), rich(txt));
    fit(t, o.w || CB.w, o.h || F(150, 110), 20);
    ex(t); wipe(t, o.t || T0 + 0.05, { d: 0.45 });
    markIn(t, (o.t || T0) + 0.5);
    return t;
  }
  function subline(txt, x, y, w, o) {
    o = o || {};
    const s = el("div", "uim", world, Object.assign(abs(x, y, w), { fontSize: fs(Math.max(34, o.f || 36), Math.max(24, o.fp || 26)), color: o.color || TH.mut, lineHeight: 1.18 }), rich(txt));
    if (o.h) fit(s, w, o.h, 14);
    ex(s); fin(s, o.t || 0.5, { y: 18 });
    markIn(s, (o.t || 0.5) + 0.3);
    return s;
  }
  function chipRow(list, x, y, w, t, o) {
    o = o || {};
    const r = el("div", "", world, Object.assign(abs(x, y, w), { display: "flex", flexWrap: "wrap", gap: F(14, 10) + "px" }));
    list.forEach((c, i) => {
      const p = el("div", "mono pill", r, { fontSize: fs(o.f || 22, 15), color: o.color || TH.fg, background: o.bg || "transparent" }, rich(c));
      pop(p, t + i * 0.07, { s: 0.6, d: 0.35 });
    });
    ex(r); return r;
  }
  function sourceLine(txt, t) {
    const s = el("div", "monor", world, Object.assign(abs(CB.x, CB.y + CB.h - F(26, 22), CB.w), { fontSize: fs(19, 14), color: TH.mut, lineHeight: 1.2, letterSpacing: ".04em" }), txt);
    fit(s, CB.w, F(40, 40), 10);
    ex(s); fin(s, t || 0.9, { y: 10 });
    return s;
  }
  function badgeIcon(name, size, parent, style, t, col) {
    const b = el("div", "", parent, Object.assign({ width: size + "px", height: size + "px", borderRadius: "50%", border: `3px solid ${col || TH.fg}`, display: "flex", alignItems: "center", justifyContent: "center", color: col || TH.fg }, style || {}));
    const ic = icon(name, size * 0.58, b);
    if (t !== undefined) { pop(b, t, { s: 0.5 }); draw(ic, t + 0.08, 0.55); }
    return b;
  }

  // ================================================================== renderers
  const R = {};

  // ---------------------------------------------------------------- counter
  R.counter = function () {
    const v = D.variant || "big";
    if (v === "eq") return counterEq();
    if (v === "scale") return counterScale();
    const side = D.icon || D.photo;
    const colW = FULL ? (D.photo ? 1120 : CB.w) : CB.w;
    const lowW = FULL && side ? CB.w - (D.photo ? 600 : 360) : colW;
    let y = CB.y;
    if (D.kicker) {
      const k = el("div", "disp", world, Object.assign(abs(CB.x, y, colW - (FULL ? 0 : (side ? 170 : 0))), { fontSize: fs(56, 38) }), rich(D.kicker));
      fit(k, colW - (FULL ? 0 : (side ? 170 : 0)), F(120, 90), 18); ex(k); wipe(k, T0 + 0.04);
      markIn(k, 0.6);
      y += k.offsetHeight + F(26, 18);
    }
    const row = el("div", "", world, Object.assign(abs(CB.x - F(6, 4), y), { display: "flex", alignItems: "flex-end", gap: F(26, 16) + "px", flexWrap: "nowrap", whiteSpace: "nowrap" }));
    const big = roller(row, D.num, { size: D.size ? F(D.size, D.sizeP || D.size * 0.6) : F(420, 250), seed: 1, extN: F(16, 9), extS: F(1.7, 1.4) });
    let unit = null;
    if (D.unit) {
      unit = el("div", "disp", row, { fontSize: fs(D.unitSize || 150, D.unitSizeP || 84), color: TH.fg, paddingBottom: F(30, 16) + "px", whiteSpace: "nowrap" }, rich(D.unit));
    }
    // shrink to fit the column
    let g = 0;
    while (contentW(row) > colW && g++ < 40) {
      big._scale(0.95);
      if (unit) unit.style.fontSize = parseFloat(getComputedStyle(unit).fontSize) * 0.95 + "px";
    }
    ex(row);
    big._anim(T0 + 0.2, 1.15);
    if (unit) { wipe(unit, T0 + 0.55, { d: 0.4 }); }
    // 3D: the number block tilts in and settles (extruded type reads as an object)
    row.style.transformOrigin = "0% 80%";
    tl.fromTo(row, { rotationY: 26, rotationX: 10, z: -160 }, { rotationY: 6, rotationX: 3, z: 0, duration: 1.3, ease: "expo.out" }, T0 + 0.15);
    y += row.offsetHeight + F(34, 14);
    if (D.line2) {
      const l2 = el("div", "disp", world, Object.assign(abs(CB.x, y, lowW), { fontSize: fs(72, 44), color: TH.fg }), rich(D.line2));
      fit(l2, lowW, F(80, 100), 18); ex(l2); wipe(l2, T0 + 0.75); markIn(l2, 1.2);
      y += l2.offsetHeight + F(24, 16);
    }
    if (D.sub) { const s = subline(D.sub, CB.x, y, lowW - 20, { f: 38, fp: 28, t: 0.95, h: F(Math.max(50, CB.y + CB.h - y - 10), 120) }); y += s.offsetHeight + F(22, 14); }
    if (D.chips) chipRow(D.chips, CB.x, y, lowW, 1.2);
    if (side) {
      if (D.photo) {
        const pw = F(560, 250), ph = F(620, 280);
        const p = el("div", "photo", world, abs(FULL ? CB.x + CB.w - pw - 20 : CB.x + CB.w - pw, FULL ? CB.y + 40 : CB.y + CB.h - ph - 40, pw, ph));
        el("img", "", p).src = "img/" + D.photo + ".jpg";
        if (D.photoCap) el("div", "cap", p, null, D.photoCap);
        ex(p); drop(p, T0 + 0.45, D.tilt || 3);
      } else {
        const sz = F(300, 150);
        const b = badgeIcon(D.icon, sz, world, abs(FULL ? CB.x + CB.w - sz - 10 : CB.x + CB.w - sz, FULL ? CB.y + CB.h - sz - 4 : CB.y - 6), T0 + 0.35, TH.fg);
        b.style.borderWidth = F(4, 3) + "px";
        b.style.background = TH.card;
        ex(b);

      }
    }
  };
  function counterEq() {
    if (D.kicker) title(D.kicker, { f: 60, fp: 40, h: F(120, 90) });
    const y0 = CB.y + F(170, 130);
    const row = el("div", "", world, Object.assign(abs(CB.x, y0, CB.w), { display: "flex", flexWrap: FULL ? "nowrap" : "wrap", alignItems: "flex-start", justifyContent: "flex-start", gap: F(30, 18) + "px " + F(30, 18) + "px", rowGap: F(20, 20) + "px" }));
    const terms = [];
    D.terms.forEach((tm, i) => {
      if (tm.op) {
        const o = el("div", "disp", row, { fontSize: fs(170, 110), color: TH.mut, lineHeight: 1, paddingTop: F(10, 6) + "px" }, tm.op);
        terms.push({ op: o, i });
      } else {
        const box = el("div", "", row, { display: "flex", flexDirection: "row", flexWrap: "wrap", alignItems: "flex-end", columnGap: F(14, 10) + "px", maxWidth: F(900, 740) + "px" });
        const r = roller(box, tm.v, { size: F(tm.res ? 220 : 190, tm.res ? 140 : 120), color: tm.res ? TH.a : TH.fg, ext: !!tm.res, seed: i });
        const u = el("div", "disp", box, { fontSize: fs(64, 40), color: tm.res ? TH.a : TH.fg, paddingBottom: F(22, 14) + "px" }, tm.u || "");
        const l = el("div", "mono", box, { fontSize: fs(22, 15), color: TH.mut, marginTop: F(10, 6) + "px", flexBasis: "100%" }, tm.l || "");
        terms.push({ r, u, l, i, res: tm.res });
      }
    });
    let gq = 0;
    if (FULL) { row.style.width = "max-content"; while (contentW(row) > CB.w && gq++ < 30) { terms.forEach(tm => { if (tm.r) tm.r._scale(0.95); else tm.op.style.fontSize = parseFloat(getComputedStyle(tm.op).fontSize) * 0.95 + "px"; }); } }
    ex(row);
    let t = T0 + 0.3;
    terms.forEach(tm => {
      if (tm.op) { pop(tm.op, t, { s: 0.3 }); t += 0.12; }
      else { tm.r._anim(t, tm.res ? 1.0 : 0.7); fin(tm.u, t + 0.25, { y: 16 }); fin(tm.l, t + 0.35, { y: 10 }); t += tm.res ? 0.2 : 0.32; }
    });
    if (D.sub) subline(D.sub, CB.x, CB.y + CB.h - F(110, 100), CB.w, { t: t + 0.6, f: 38, fp: 26 });
  }
  function counterScale() {
    // digital scale (front-on, slight 3D tilt) with an LCD readout that counts down, then the equation
    const sw = F(640, 420), sh = F(560, 360);
    const sx = FULL ? CB.x + 20 : CB.x + (CB.w - sw) / 2, sy = FULL ? CB.y + 40 : CB.y + 10;
    const box = el("div", "", world, Object.assign(abs(sx, sy, sw, sh), { transformStyle: "preserve-3d" }));
    const plat = el("div", "", box, Object.assign(abs(0, 0, sw, sh), { background: TH.card, border: `4px solid ${TH.fg}`, borderRadius: F(46, 30) + "px", boxShadow: `0 ${F(26, 16)}px 0 ${TH.fg}` }));
    const lcd = el("div", "", plat, Object.assign(abs(sw * 0.14, sh * 0.16, sw * 0.72, sh * 0.34), { background: "#0D0D0D", borderRadius: "10px", display: "flex", alignItems: "center", justifyContent: "flex-end", paddingRight: F(30, 18) + "px", boxSizing: "border-box" }));
    const num = el("div", "mono", lcd, { fontSize: fs(130, 84), color: "#FFD84D", letterSpacing: "0", lineHeight: 1 }, "74.0");
    el("div", "mono", lcd, { fontSize: fs(34, 22), color: "#FFD84D", marginLeft: "12px", paddingTop: F(50, 30) + "px" }, "KG");
    const lab = el("div", "mono", plat, Object.assign(abs(0, sh * 0.6, sw), { textAlign: "center", fontSize: fs(26, 17), color: TH.mut }), "BEFORE");
    const feet = [0.16, 0.84].map(f => el("div", "", box, Object.assign(abs(sw * f - F(40, 26), sh + F(22, 14), F(80, 52), F(18, 12)), { background: TH.fg, borderRadius: "4px" })));
    ex(box);
    tl.fromTo(box, { opacity: 0, y: F(80, 50), rotationX: 38 }, { opacity: 1, y: 0, rotationX: 14, duration: 0.6, ease: E_IN }, T0 + 0.05);
    const p = { v: 74.0 };
    const wr = () => { num.textContent = p.v.toFixed(1); };
    wr();
    tl.to(p, { v: 73.0, duration: 1.1, ease: "power2.inOut", onUpdate: wr }, 1.0);
    tl.set(lab, { textContent: "AFTER" }, 1.0);
    tl.fromTo(lcd, { boxShadow: "0 0 0 0 rgba(255,90,31,0)" }, { boxShadow: `0 0 0 ${F(8, 6)}px #FF5A1F`, duration: 0.2, yoyo: true, repeat: 1 }, 2.1);
    // equation on the right (full) / below (panel)
    const ex0 = FULL ? CB.x + sw + 140 : CB.x;
    const ey0 = FULL ? CB.y + 40 : sy + sh + F(60, 50);
    const eqw = FULL ? CB.w - sw - 140 : CB.w;
    const l1 = el("div", "disp", world, Object.assign(abs(ex0, ey0, eqw), { fontSize: fs(210, 96), color: TH.a, textShadow: extrude(F(10, 6), TH.ext, F(1.6, 1.3)), lineHeight: 0.95 }), D.l1 || "−1 KG");
    const l2 = el("div", "disp", world, Object.assign(abs(ex0, ey0 + F(220, 100), eqw), { fontSize: fs(210, 96), color: TH.fg, lineHeight: 0.95 }), D.l2 || "= 1 L");
    const l3 = el("div", "uim", world, Object.assign(abs(ex0, ey0 + F(450, 204), eqw), { fontSize: fs(40, 28), color: TH.mut, lineHeight: 1.2 }), rich(D.sub || ""));
    fit(l1, eqw, 0, 30); fit(l2, eqw, 0, 30); fit(l3, eqw, F(170, 90), 14);
    [l1, l2, l3].forEach(ex);
    if (FULL) { wipe(l1, 2.15, { d: 0.35 }); wipe(l2, 2.35, { d: 0.35 }); fin(l3, 2.6, { y: 16 }); markIn(l3, 2.9); }
    else { wipe(l1, 2.15, { d: 0.35 }); wipe(l2, 2.35, { d: 0.35 }); fin(l3, 2.6, { y: 16 }); markIn(l3, 2.9); }
  }

  // ---------------------------------------------------------------- timeline (day line, with an optional highlighted gap)
  R.timeline = function () {
    if (D.variant === "race") return timelineRace();
    if (D.title) title(D.title, { f: 62, fp: 42, h: F(120, 100) });
    const ev = D.events;
    const n = ev.length;
    if (FULL) {
      const ax = CB.y + (D.gap ? 320 : 380);
      let lw0 = 330; for (let q = 0; q < 4; q++) lw0 = Math.min(330, (CB.w - lw0) / (n - 1) - 18);
      const x0 = CB.x + lw0 / 2, x1 = CB.x + CB.w - lw0 / 2;
      const xs = ev.map((e, i) => x0 + (x1 - x0) * (D.even === false ? (e.h - ev[0].h) / (ev[n - 1].h - ev[0].h) : i / (n - 1)));
      const axis = el("div", "", world, Object.assign(abs(x0 - 40, ax - 3, x1 - x0 + 80, 6), { background: TH.fg, transformOrigin: "0 50%" }));
      ex(axis); tl.fromTo(axis, { scaleX: 0 }, { scaleX: 1, duration: 0.9, ease: "expo.inOut" }, T0 + 0.2);
      const spacing = (x1 - x0) / (n - 1);
      const lw = Math.min(330, spacing - 18);
      if (D.gap) {
        const ga = xs[D.gap.a], gb = xs[D.gap.b];
        const band = el("div", "", world, Object.assign(abs(ga, ax - 9, gb - ga, 18), { background: TH.a, transformOrigin: "0 50%" }));
        const hatch = el("div", "", world, Object.assign(abs(ga, ax + 30, gb - ga, 100), { backgroundImage: `repeating-linear-gradient(-45deg, ${TH.a} 0 3px, transparent 3px 16px)`, opacity: 0.55, transformOrigin: "0 50%" }));
        const br = sv("svg", { width: gb - ga, height: 60 }, world); Object.assign(br.style, abs(ga, ax + 142));
        sv("path", { d: `M2 0 V26 H${gb - ga - 2} V0 M${(gb - ga) / 2} 26 V52`, stroke: TH.a, "stroke-width": 5, fill: "none" }, br);
        const gl = el("div", "disp", world, Object.assign(abs(ga - 200, ax + 204, gb - ga + 400), { fontSize: fs(108, 60), color: TH.a, textAlign: "center", textShadow: extrude(8, TH.ext, 1.5) }), rich(D.gap.label));
        fit(gl, gb - ga + 400, 0, 30);
        [band, hatch, br, gl].forEach(ex);
        const tg = 1.25 + n * 0.08;
        tl.fromTo(band, { scaleX: 0 }, { scaleX: 1, duration: 0.7, ease: "expo.inOut" }, tg);
        tl.fromTo(hatch, { scaleX: 0, opacity: 0 }, { scaleX: 1, opacity: 0.55, duration: 0.7, ease: "expo.inOut" }, tg + 0.05);
        draw(br, tg + 0.35, 0.5);
        pop(gl, tg + 0.55, { s: 0.5 });
        if (D.gap.note) { const gn = el("div", "uim", world, Object.assign(abs(ga - 200, ax + 204 + F(112, 70), gb - ga + 400), { fontSize: fs(32, 24), color: TH.mut, textAlign: "center" }), rich(D.gap.note)); ex(gn); fin(gn, tg + 0.8, { y: 12 }); }
      }
      ev.forEach((e, i) => {
        const t = T0 + 0.35 + i * 0.09;
        const hot = D.gap && (i === D.gap.a || i === D.gap.b);
        const node = el("div", "", world, Object.assign(abs(xs[i] - 17, ax - 17, 34, 34), { borderRadius: "50%", background: hot ? TH.a : TH.bg, border: `5px solid ${hot ? TH.a : TH.fg}`, boxSizing: "border-box" }));
        ex(node); pop(node, t);
        const lab = el("div", "", world, Object.assign(abs(xs[i] - lw / 2, ax - F(190, 0), lw, 160), { display: "flex", flexDirection: "column", justifyContent: "flex-end", alignItems: "center", textAlign: "center" }));
        const tm = el("div", "mono", lab, { fontSize: fs(26, 18), color: hot ? TH.a : TH.mut, marginBottom: "8px" }, e.t || "");
        const tt = el("div", "disp", lab, { fontSize: fs(e.f || 40, 28), color: TH.fg, lineHeight: 0.98 }, rich(e.title));
        fit(tt, lw, 96, 16);
        ex(lab); fin(lab, t + 0.05, { y: 24 });
        if (e.icon) {
          const isz = D.gap ? 72 : 104; const ic = el("div", "", world, Object.assign(abs(xs[i] - isz / 2, ax + 36, isz, isz), { color: hot ? TH.a : TH.fg }));
          const s = icon(e.icon, isz, ic);
          ex(ic); tl.fromTo(ic, { opacity: 0 }, { opacity: 1, duration: 0.1 }, t + 0.1); draw(s, t + 0.1, 0.5);
        }
        if (e.note && !D.gap) {
          const nt = el("div", "uim", world, Object.assign(abs(xs[i] - lw / 2, ax + 170, lw), { fontSize: fs(32, 18), color: TH.mut, textAlign: "center", lineHeight: 1.15 }), rich(e.note));
          fit(nt, lw, 130, 12); ex(nt); fin(nt, t + 0.2, { y: 10 });
        }
      });
      if (D.sub) subline(D.sub, CB.x, CB.y + CB.h - 60, CB.w, { t: 2.0, f: 30 });
    } else {
      // panel: vertical line
      const top = CB.y + F(0, 120), bot = CB.y + CB.h - 30;
      const axx = CB.x + 190;
      const ys = ev.map((e, i) => top + (bot - top) * (i / (n - 1)));
      const axis = el("div", "", world, Object.assign(abs(axx - 3, top - 20, 6, bot - top + 40), { background: TH.fg, transformOrigin: "50% 0" }));
      ex(axis); tl.fromTo(axis, { scaleY: 0 }, { scaleY: 1, duration: 0.8, ease: "expo.inOut" }, T0 + 0.2);
      if (D.gap) {
        const ga = ys[D.gap.a], gb = ys[D.gap.b];
        const band = el("div", "", world, Object.assign(abs(axx - 9, ga, 18, gb - ga), { background: TH.a, transformOrigin: "50% 0" }));
        ex(band); tl.fromTo(band, { scaleY: 0 }, { scaleY: 1, duration: 0.6, ease: "expo.inOut" }, 1.3);
        const gl = el("div", "disp", world, Object.assign(abs(CB.x + 520, ga, CB.w - 520, gb - ga), { fontSize: fs(80, 62), color: TH.a, display: "flex", alignItems: "center", lineHeight: 0.9, textShadow: extrude(6, TH.ext, 1.3) }), rich(D.gap.label));
        fit(gl, CB.w - 520, gb - ga + 40, 20); ex(gl); pop(gl, 1.6, { s: 0.5 });
        const hatch = el("div", "", world, Object.assign(abs(axx + 26, ga, 300, gb - ga), { backgroundImage: `repeating-linear-gradient(-45deg, ${TH.a} 0 2px, transparent 2px 13px)`, opacity: 0.35 }));
        ex(hatch); wipe(hatch, 1.4, { dir: "d", d: 0.6 });
      }
      ev.forEach((e, i) => {
        const t = T0 + 0.35 + i * 0.09;
        const hot = D.gap && (i === D.gap.a || i === D.gap.b);
        const node = el("div", "", world, Object.assign(abs(axx - 14, ys[i] - 14, 28, 28), { borderRadius: "50%", background: hot ? TH.a : TH.bg, border: `5px solid ${hot ? TH.a : TH.fg}`, boxSizing: "border-box" }));
        ex(node); pop(node, t);
        const tm = el("div", "mono", world, Object.assign(abs(CB.x, ys[i] - 13, 160), { fontSize: "19px", color: hot ? TH.a : TH.mut, textAlign: "right" }), e.t || "");
        ex(tm); fin(tm, t, { x: -10, y: 0 });
        const tt = el("div", "disp", world, Object.assign(abs(axx + 34, ys[i] - 17, 290), { fontSize: "30px", color: TH.fg }), rich(e.title));
        fit(tt, 290, 40, 14); ex(tt); fin(tt, t + 0.05, { x: 14, y: 0 });
      });
    }
  };
  function timelineRace() {
    title(D.title, { f: 60, fp: 40, h: F(110, 90) });
    const ax = FULL ? CB.y + 450 : CB.y + 330;
    const x0 = CB.x + F(20, 10), x1 = CB.x + CB.w - F(20, 10);
    const X = m => x0 + (x1 - x0) * (m / D.max);
    const track = el("div", "", world, Object.assign(abs(x0, ax - F(14, 10), x1 - x0, F(28, 20)), { background: TH.fg, transformOrigin: "0 50%" }));
    ex(track); tl.fromTo(track, { scaleX: 0 }, { scaleX: 1, duration: 1.0, ease: "expo.inOut" }, T0 + 0.2);
    // progress runner fill
    const fill = el("div", "", world, Object.assign(abs(x0, ax - F(14, 10), x1 - x0, F(28, 20)), { background: TH.a, transformOrigin: "0 50%" }));
    ex(fill); tl.fromTo(fill, { scaleX: 0 }, { scaleX: 1, duration: 3.4, ease: "none" }, 0.9);
    (D.ticks || []).forEach((m, i) => {
      const tk = el("div", "mono", world, Object.assign(abs(X(m) - 50, ax + F(28, 20), 100), { fontSize: fs(20, 13), color: TH.mut, textAlign: "center" }), D.tickLabels[i]);
      ex(tk); fin(tk, 0.6 + i * 0.04, { y: 8 });
    });
    // cups (water) under the track
    (D.cups || []).forEach((m, i) => {
      const c = el("div", "", world, Object.assign(abs(X(m) - F(17, 10), ax + F(58, 46), F(34, 20), F(34, 20)), { color: TH.a2 }));
      icon("drop", F(34, 20), c); ex(c); pop(c, 0.9 + (m / D.max) * 3.4, { s: 0.3, d: 0.3 });
    });
    if (D.cupLabel) { const cl = el("div", "uim", world, Object.assign(abs(x0, ax + F(104, 72), x1 - x0), { fontSize: fs(30, 18), color: TH.mut }), rich(D.cupLabel)); ex(cl); fin(cl, 1.6, { y: 8 }); }
    // events above the track
    D.events.forEach((e, i) => {
      const at = 0.9 + (e.m / D.max) * 3.4;
      const hot = e.hot;
      const stem = el("div", "", world, Object.assign(abs(X(e.m) - 2, ax - F(14, 10) - (e.hgt || F(120, 90)), 4, e.hgt || F(120, 90)), { background: hot ? TH.a : TH.fg, transformOrigin: "50% 100%" }));
      ex(stem); tl.fromTo(stem, { scaleY: 0 }, { scaleY: 1, duration: 0.3, ease: E_IN }, at - 0.05);
      const fw = F(e.w || 300, e.wp || 210);
      const al = e.align || "c";
      const fx = al === "r" ? X(e.m) - fw + 2 : al === "l" ? X(e.m) - 2 : X(e.m) - fw / 2;
      const flag = el("div", "", world, Object.assign(abs(fx, ax - F(14, 10) - (e.hgt || F(120, 90)) - F(136, 96), fw, F(130, 92)), { display: "flex", flexDirection: "column", justifyContent: "flex-end", alignItems: al === "r" ? "flex-end" : al === "l" ? "flex-start" : "center", textAlign: al === "r" ? "right" : al === "l" ? "left" : "center" }));
      const tt = el("div", "disp", flag, { fontSize: fs(54, 30), color: hot ? TH.a : TH.fg, lineHeight: 0.95 }, rich(e.title));
      const tn = el("div", "uim", flag, { fontSize: fs(25, 16), color: TH.mut, marginTop: "6px", lineHeight: 1.15 }, rich(e.note || ""));
      fit(tt, fw, 0, 12);
      ex(flag); pop(flag, at, { s: 0.7, d: 0.35, ease: E_BACK });
      if (e.icon) { const ic = el("div", "", world, Object.assign(abs(X(e.m) - F(26, 18), ax - F(26, 18), F(52, 36), F(52, 36)), { background: hot ? TH.a : TH.bg, border: `4px solid ${hot ? TH.a : TH.fg}`, borderRadius: "50%", display: "flex", alignItems: "center", justifyContent: "center", color: hot ? TH.bg : TH.fg, boxSizing: "border-box" })); icon(e.icon, F(30, 20), ic); ex(ic); pop(ic, at - 0.05); }
    });
    if (D.chips) {
      const cy = FULL ? ax + 160 : ax + 150;
      const lab = el("div", "mono", world, Object.assign(abs(CB.x, cy, CB.w), { fontSize: fs(22, 15), color: TH.a }), D.chipsTitle || "");
      ex(lab); fin(lab, 3.5, { y: 8 });
      chipRow(D.chips, CB.x, cy + F(38, 32), CB.w, 3.65, { f: 25, color: TH.fg });
    }
  }

  // ---------------------------------------------------------------- steps (row of cards / loop / pyramid)
  R.steps = function () {
    if (D.variant === "loop") return stepsLoop();
    if (D.variant === "pyramid") return stepsPyramid();
    if (D.title) title(D.title, { f: 62, fp: 42, h: F(120, 96) });
    const st = D.steps, n = st.length;
    const top = CB.y + F(150, 116);
    if (FULL || n <= 2) {
      const gap = F(70, 26);
      const cw = (CB.w - gap * (n - 1)) / n, ch = CB.y + CB.h - top - F(10, 10);
      st.forEach((s, i) => {
        const x = CB.x + i * (cw + gap);
        const t = T0 + 0.3 + i * 0.22;
        const c = el("div", "card shadow", world, Object.assign(abs(x, top, cw, ch), { boxSizing: "border-box", padding: F(30, 18) + "px", display: "flex", flexDirection: "column", gap: F(14, 10) + "px", background: s.hot ? TH.a : TH.card, color: s.hot ? TH.bg : TH.fg, borderColor: s.hot ? TH.a : TH.fg }));
        const num = el("div", "mono", c, { fontSize: fs(24, 16), color: s.hot ? TH.bg : TH.a }, String(i + 1).padStart(2, "0") + " /");
        const icw = el("div", "", c, { height: F(120, 80) + "px", color: "inherit" });
        const ic = icon(s.icon || "spark", F(120, 80), icw, null, 2.6);
        const tt = el("div", "disp", c, { fontSize: fs(s.f || 46, 32), lineHeight: 0.95 }, rich(s.title));
        fit(tt, cw - F(60, 36), F(140, 100), 16);
        const bd = el("div", "uim", c, { fontSize: fs(29, 21), lineHeight: 1.2, color: s.hot ? TH.bg : TH.mut }, rich(s.body || ""));
        fit(bd, cw - F(60, 36), ch - F(330, 230), 13);
        ex(c); drop(c, t, (i % 2 ? 1.2 : -1.2));
        draw(ic, t + 0.25, 0.55);
        markIn(c, t + 0.6);
        if (i < n - 1) {
          const ar = sv("svg", { width: gap, height: 40, viewBox: `0 0 ${gap} 40` }, world); Object.assign(ar.style, abs(x + cw + 4, top + ch / 2 - 20));
          sv("path", { d: `M4 20 H${gap - 16} M${gap - 26} 8 L${gap - 12} 20 L${gap - 26} 32`, stroke: TH.fg, "stroke-width": 5, fill: "none", "stroke-linecap": "square" }, ar);
          ex(ar); draw(ar, t + 0.3, 0.3, 0.05);
        }
      });
    } else {
      // panel: rows
      const rh = (CB.y + CB.h - top) / n;
      st.forEach((s, i) => {
        const y = top + i * rh;
        const t = T0 + 0.3 + i * 0.18;
        const c = el("div", "card shadow", world, Object.assign(abs(CB.x, y, CB.w - 14, rh - 18), { boxSizing: "border-box", padding: "14px 20px", display: "flex", alignItems: "center", gap: "20px", background: s.hot ? TH.a : TH.card, color: s.hot ? TH.bg : TH.fg, borderColor: s.hot ? TH.a : TH.fg }));
        const num = el("div", "disp", c, { fontSize: "54px", color: s.hot ? TH.bg : TH.a, minWidth: "70px", lineHeight: 1 }, String(i + 1).padStart(2, "0"));
        const icw = el("div", "", c, { width: "70px", height: "70px", flex: "0 0 70px" });
        const ic = icon(s.icon || "spark", 70, icw, null, 2.8);
        const tx = el("div", "", c, { flex: "1", minWidth: 0 });
        const tt = el("div", "disp", tx, { fontSize: "34px", lineHeight: 0.95 }, rich(s.title));
        const bd = el("div", "uim", tx, { fontSize: "21px", lineHeight: 1.15, marginTop: "6px", color: s.hot ? TH.bg : TH.mut }, rich(s.body || ""));
        fit(tt, CB.w - 230, 70, 14); fit(bd, CB.w - 230, rh - 40 - tt.offsetHeight - 14, 12);
        ex(c); drop(c, t, i % 2 ? 0.8 : -0.8, { y: -50 });
        draw(ic, t + 0.2, 0.5);
        markIn(c, t + 0.5);
      });
    }
    if (D.sub && FULL) subline(D.sub, CB.x, CB.y + CB.h + 0, CB.w, { t: 2.2, f: 28 });
  };
  function stepsLoop() {
    if (D.title) title(D.title, { f: 58, fp: 40, h: F(120, 96), w: FULL ? 760 : CB.w });
    const st = D.steps, n = st.length;
    const cx = FULL ? CB.x + 1250 : CB.x + CB.w / 2, cy = FULL ? CB.y + 360 : CB.y + 360;
    const r = F(270, 205);
    const ring = sv("svg", { width: r * 2 + 80, height: r * 2 + 80, viewBox: `${-r - 40} ${-r - 40} ${r * 2 + 80} ${r * 2 + 80}` }, world);
    Object.assign(ring.style, abs(cx - r - 40, cy - r - 40));
    ex(ring);
    const nodes = [];
    for (let i = 0; i < n; i++) {
      const a0 = -Math.PI / 2 + (i / n) * Math.PI * 2 + 0.36, a1 = -Math.PI / 2 + ((i + 1) / n) * Math.PI * 2 - 0.36;
      const p0 = [r * Math.cos(a0), r * Math.sin(a0)], p1 = [r * Math.cos(a1), r * Math.sin(a1)];
      const pth = sv("path", { d: `M${p0[0]} ${p0[1]} A${r} ${r} 0 0 1 ${p1[0]} ${p1[1]}`, stroke: TH.a, "stroke-width": F(8, 6), fill: "none" }, ring);
      const ah = a1; const hx = p1[0], hy = p1[1];
      const tx = -Math.sin(ah), ty = Math.cos(ah); // tangent (clockwise)
      const nx = Math.cos(ah), ny = Math.sin(ah);
      const L = F(26, 20);
      const head = sv("path", { d: `M${hx - tx * L + nx * L * 0.7} ${hy - ty * L + ny * L * 0.7} L${hx} ${hy} L${hx - tx * L - nx * L * 0.7} ${hy - ty * L - ny * L * 0.7}`, stroke: TH.a, "stroke-width": F(8, 6), fill: "none", "stroke-linejoin": "miter" }, ring);
      nodes.push({ pth, head, i });
    }
    const bw = F(330, 250);
    st.forEach((s, i) => {
      const a = -Math.PI / 2 + (i / n) * Math.PI * 2;
      const x = cx + r * Math.cos(a), y = cy + r * Math.sin(a);
      const b = el("div", "card shadow", world, Object.assign(abs(x - bw / 2, y - F(62, 50), bw), { boxSizing: "border-box", padding: F(16, 12) + "px " + F(20, 14) + "px", textAlign: "center", background: s.hot ? TH.a : TH.card, color: s.hot ? TH.bg : TH.fg, borderColor: s.hot ? TH.a : TH.fg }));
      el("div", "disp", b, { fontSize: fs(s.f || 44, 30), lineHeight: 0.95 }, rich(s.title));
      if (s.body) el("div", "uim", b, { fontSize: fs(24, 17), marginTop: "6px", color: s.hot ? TH.bg : TH.mut, lineHeight: 1.1 }, rich(s.body));
      ex(b); pop(b, T0 + 0.4 + i * 0.45, { s: 0.6 });
    });
    nodes.forEach(nd => { draw(nd.pth, T0 + 0.6 + nd.i * 0.45, 0.4, 0); draw(nd.head, T0 + 0.95 + nd.i * 0.45, 0.15, 0); });
    tl.fromTo(ring, { rotation: -6 }, { rotation: 0, duration: 2, ease: E_IN }, T0 + 0.4);
    if (D.center) { const cc = el("div", "disp", world, Object.assign(abs(cx - r * 0.62, cy - F(50, 40), r * 1.24), { textAlign: "center", fontSize: fs(56, 40), color: TH.fg, lineHeight: 0.95 }), rich(D.center)); fit(cc, r * 1.24, r, 16); ex(cc); pop(cc, T0 + 0.4 + n * 0.45, { s: 0.5 }); }
    if (D.sub && FULL) subline(D.sub, CB.x, CB.y + F(220, 0), 700, { t: 1.0, f: 36, h: 400 });
  }
  function stepsPyramid() {
    if (D.title) title(D.title, { f: 58, fp: 40, h: F(120, 96), w: FULL ? 700 : CB.w });
    // isometric stacked slabs, widest at the bottom; labels on the right
    const st = D.steps, n = st.length;
    const baseW = F(620, 420), slabH = F(92, 74), shrink = F(120, 86), dep = F(70, 48);
    const cx = FULL ? CB.x + 1060 : CB.x + 250, by = CB.y + CB.h - F(60, 30);
    const svg = sv("svg", { width: W, height: H }, world); Object.assign(svg.style, abs(0, 0));
    ex(svg);
    st.forEach((s, i) => {
      const w = baseW - i * shrink;
      const y = by - i * (slabH + 6);
      const x = cx - w / 2;
      const g = sv("g", {}, svg);
      const fill = s.hot ? TH.a : (i % 2 ? TH.fg : TH.card);
      const txtc = s.hot ? TH.bg : (i % 2 ? TH.bg : TH.fg);
      sv("polygon", { points: `${x},${y - slabH} ${x + dep},${y - slabH - dep * 0.55} ${x + w + dep},${y - slabH - dep * 0.55} ${x + w},${y - slabH}`, fill: s.hot ? "#ff8a5c" : TH.soft, stroke: TH.fg, "stroke-width": 3 }, g);
      sv("polygon", { points: `${x + w},${y - slabH} ${x + w + dep},${y - slabH - dep * 0.55} ${x + w + dep},${y - dep * 0.55} ${x + w},${y}`, fill: s.hot ? TH.ext : TH.mut, stroke: TH.fg, "stroke-width": 3 }, g);
      sv("rect", { x, y: y - slabH, width: w, height: slabH, fill, stroke: TH.fg, "stroke-width": 3 }, g);
      const lab = el("div", "disp", world, Object.assign(abs(x, y - slabH, w, slabH), { display: "flex", alignItems: "center", justifyContent: "center", fontSize: fs(38, 28), color: txtc, textAlign: "center" }), rich(s.title));
      fit(lab, w - 20, slabH, 12);
      const t = T0 + 0.35 + i * 0.32;
      tl.fromTo([g, lab], { opacity: 0, y: -F(140, 100) }, { opacity: 1, y: 0, duration: 0.42, ease: "bounce.out" }, t);
      ex(lab);
      if (s.body) {
        const bx = FULL ? cx + baseW / 2 + dep + 40 : CB.x + 520;
        const bd = el("div", "uim", world, Object.assign(abs(bx, y - slabH + 6, FULL ? CB.x + CB.w - bx : CB.x + CB.w - bx), { fontSize: fs(28, 19), color: TH.mut, lineHeight: 1.15 }), rich(s.body));
        fit(bd, FULL ? CB.x + CB.w - bx : CB.x + CB.w - bx, slabH + 20, 11);
        ex(bd); fin(bd, t + 0.2, { x: 20, y: 0 });
      }
    });
    if (D.sub && FULL) subline(D.sub, CB.x, CB.y + 200, 640, { t: 1.4, f: 36, h: 360 });
  }

  // ---------------------------------------------------------------- do / don't
  R.dodont = function () {
    if (D.title) title(D.title, { f: 60, fp: 40, h: F(110, 90) });
    const top = CB.y + (D.title ? F(140, 104) : 0);
    const cols = [D.do, D.dont];
    const gap = F(40, 22);
    const cw = FULL ? (CB.w - gap) / 2 : CB.w;
    const chH = FULL ? CB.y + CB.h - top : (CB.y + CB.h - top - gap) / 2;
    cols.forEach((c, k) => {
      const x = FULL ? CB.x + k * (cw + gap) : CB.x;
      const y = FULL ? top : top + k * (chH + gap);
      const good = k === 0;
      const col = good ? TH.pos : TH.neg;
      const box = el("div", "", world, Object.assign(abs(x, y, cw, chH), { boxSizing: "border-box", border: `4px solid ${TH.fg}`, background: TH.card, padding: F(30, 18) + "px", display: "flex", flexDirection: "column", gap: F(18, 10) + "px", transformOrigin: good ? "100% 50%" : "0% 50%" }));
      const hd = el("div", "", box, { display: "flex", alignItems: "center", gap: F(18, 12) + "px" });
      const bdg = el("div", "", hd, { width: F(78, 52) + "px", height: F(78, 52) + "px", background: col, display: "flex", alignItems: "center", justifyContent: "center", color: good && S.bg !== "paper" ? "#0D0D0D" : (good ? "#EFEBE3" : "#0D0D0D"), flex: "0 0 auto" });
      const bi = icon(good ? "check" : "cross", F(52, 36), bdg, null, 5);
      el("div", "disp", hd, { fontSize: fs(64, 42), color: TH.fg }, c.h || (good ? "DO" : "DON'T"));
      const items = c.items.map((it, i) => {
        const r = el("div", "", box, { display: "flex", gap: F(16, 10) + "px", alignItems: "flex-start" });
        el("div", "", r, { width: F(14, 10) + "px", height: F(14, 10) + "px", background: col, marginTop: F(16, 10) + "px", flex: "0 0 auto" });
        const tx = el("div", "ui", r, { fontSize: fs(it.f || 40, 25), lineHeight: 1.12, color: TH.fg }, rich(it.t || it));
        if (it.d) el("div", "uim", tx, { fontSize: fs(28, 18), color: TH.mut, marginTop: "4px", lineHeight: 1.15 }, rich(it.d));
        return r;
      });
      // fit all items in the box
      let guard = 0;
      while (box.scrollHeight > chH + 2 && guard++ < 30) box.querySelectorAll(".ui").forEach(u => { u.style.fontSize = parseFloat(getComputedStyle(u).fontSize) * 0.94 + "px"; u.querySelectorAll(".uim").forEach(m => m.style.fontSize = parseFloat(getComputedStyle(m).fontSize) * 0.94 + "px"); });
      ex(box);
      const t = T0 + 0.2 + k * (FULL ? 0.18 : 0.3);
      tl.fromTo(box, { opacity: 0, rotationY: good ? 50 : -50, x: good ? -60 : 60 }, { opacity: 1, rotationY: 0, x: 0, duration: 0.6, ease: E_IN }, t);
      pop(bdg, t + 0.2); draw(bi, t + 0.3, 0.35, 0);
      items.forEach((r, i) => fin(r, t + 0.35 + i * 0.12, { x: -20, y: 0 }));
      markIn(box, t + 0.8);
    });
  };

  // ---------------------------------------------------------------- myth vs fact
  R.myth = function () {
    const top = CB.y + F(10, 6);
    const lw = FULL ? CB.w : CB.w;
    const mlab = el("div", "mono pill", world, Object.assign(abs(CB.x, top), { fontSize: fs(24, 17), color: TH.mut }), "✕&nbsp;&nbsp;" + (D.mythLabel || "MYTH"));
    ex(mlab); pop(mlab, T0 + 0.05, { s: 0.6 });
    const mt = el("div", "disp", world, Object.assign(abs(CB.x, top + F(64, 48), lw), { fontSize: fs(D.mf || 92, D.mfp || 48), color: TH.fg, lineHeight: 0.98 }), rich(D.myth));
    fit(mt, lw, F(200, 190), 18); ex(mt); wipe(mt, T0 + 0.15, { d: 0.5 });
    // strike-through lines drawn over each text line
    const lines = Math.max(1, Math.round(mt.offsetHeight / (parseFloat(getComputedStyle(mt).fontSize) * 0.98)));
    const lh = mt.offsetHeight / lines;
    const strikes = [];
    for (let i = 0; i < lines; i++) {
      const s = el("div", "", world, Object.assign(abs(CB.x - 10, top + F(64, 48) + lh * (i + 0.5) - F(6, 4), Math.min(lw, mt.scrollWidth) + 20, F(12, 8)), { background: TH.a, transformOrigin: "0 50%" }));
      strikes.push(s); ex(s);
    }
    const ts = 1.15;
    tl.fromTo(strikes, { scaleX: 0 }, { scaleX: 1, duration: 0.38, ease: "power3.inOut", stagger: 0.12 }, ts);
    tl.to(mt, { color: TH.mut, duration: 0.3 }, ts + 0.2);
    tl.to([mt, ...strikes], { rotation: -1.2, duration: 0.35, ease: E_BACK }, ts + 0.35);
    const fy = top + F(64, 48) + mt.offsetHeight + F(60, 40);
    const flab = el("div", "mono pill", world, Object.assign(abs(CB.x, fy), { fontSize: fs(24, 17), color: TH.bg, background: TH.a, borderColor: TH.a }), "✓&nbsp;&nbsp;" + (D.factLabel || "FACT"));
    ex(flab); pop(flab, ts + 0.55, { s: 0.6 });
    const ft = el("div", "disp", world, Object.assign(abs(CB.x, fy + F(64, 48), lw), { fontSize: fs(D.ff || 124, D.ffp || 54), color: TH.fg, lineHeight: 0.95 }), rich(D.fact));
    fit(ft, lw, CB.y + CB.h - (fy + F(64, 48)) - (D.sub ? F(80, 70) : 0), 16); ex(ft); wipe(ft, ts + 0.65, { d: 0.5 });
    markIn(ft, ts + 1.1);
    if (D.sub) subline(D.sub, CB.x, fy + F(64, 48) + ft.offsetHeight + F(22, 16), lw, { t: ts + 1.2, f: 34, fp: 23, h: F(110, 90) });
    tl.fromTo(world, { rotationX: 8, z: -60 }, { rotationX: 0, z: 0, duration: 1.2, ease: E_IN }, 0);
  };

  // ---------------------------------------------------------------- checklist
  R.list = function () {
    const hasT = !!D.title;
    if (hasT) title(D.title, { f: 62, fp: 42, h: F(120, 96), w: D.photo && FULL ? CB.w - 560 : CB.w });
    const top = CB.y + (hasT ? F(140, 110) : 0) + (D.sub ? 0 : 0);
    const items = D.items;
    const cols = D.cols || (FULL && items.length > 4 ? 2 : 1);
    const areaW = D.photo && FULL ? CB.w - 560 : CB.w;
    const gapX = F(50, 0);
    const cw = (areaW - gapX * (cols - 1)) / cols;
    const rows = Math.ceil(items.length / cols);
    const areaH = CB.y + CB.h - top - (D.sub ? F(70, 60) : 0);
    const rh = Math.min(areaH / rows, F(200, 130));
    items.forEach((it, i) => {
      const c = Math.floor(i / rows), r = i % rows;
      const x = CB.x + c * (cw + gapX), y = top + r * rh;
      const t = T0 + 0.35 + i * 0.13;
      const row = el("div", "", world, Object.assign(abs(x, y, cw, rh - F(16, 12)), { display: "flex", alignItems: "center", gap: F(22, 14) + "px", borderTop: `3px solid ${TH.fg}`, paddingTop: F(12, 8) + "px", boxSizing: "border-box" }));
      const bx = el("div", "", row, { width: F(56, 40) + "px", height: F(56, 40) + "px", border: `4px solid ${TH.fg}`, flex: "0 0 auto", display: "flex", alignItems: "center", justifyContent: "center", color: TH.a, boxSizing: "border-box" });
      const ck = icon("check", F(46, 34), bx, null, 6);
      const num = el("div", "mono", row, { fontSize: fs(20, 14), color: TH.mut, flex: "0 0 auto", width: F(44, 30) + "px" }, String(i + 1).padStart(2, "0"));
      const tx = el("div", "", row, { flex: "1", minWidth: 0 });
      const tt = el("div", "ui", tx, { fontSize: fs(it.f || 50, 32), lineHeight: 1.05, color: TH.fg }, rich(it.t));
      if (it.d) el("div", "uim", tx, { fontSize: fs(30, 20), color: TH.mut, lineHeight: 1.12, marginTop: "6px" }, rich(it.d));
      let g = 0; while (tx.scrollHeight > rh - F(30, 24) && g++ < 30) { tx.querySelectorAll("div").forEach(d => d.style.fontSize = parseFloat(getComputedStyle(d).fontSize) * 0.94 + "px"); }
      if (it.icon) { const iw = el("div", "", row, { width: F(84, 52) + "px", height: F(84, 52) + "px", flex: "0 0 auto", color: TH.fg }); const s = icon(it.icon, F(84, 52), iw, null, 2.6); draw(s, t + 0.2, 0.5); }
      ex(row);
      wipe(row, t, { d: 0.42 });
      draw(ck, t + 0.3, 0.25, 0);
      tl.fromTo(bx, { backgroundColor: "rgba(0,0,0,0)" }, { backgroundColor: TH.fg, duration: 0.12 }, t + 0.32);
      markIn(row, t + 0.5);
    });
    if (D.sub) subline(D.sub, CB.x, CB.y + CB.h - F(56, 48), areaW, { t: 1.6, f: 30, fp: 21 });
    if (D.photo && FULL) {
      const pw = 480, ph = 560;
      const p = el("div", "photo", world, abs(CB.x + CB.w - pw - 10, CB.y + 40, pw, ph));
      el("img", "", p).src = "img/" + D.photo + ".jpg";
      if (D.photoCap) el("div", "cap", p, null, D.photoCap);
      ex(p); drop(p, T0 + 0.3, D.tilt || 3);
    }
  };

  // ---------------------------------------------------------------- compare (two cards / swap / balance)
  R.compare = function () {
    if (D.variant === "balance") return compareBalance();
    if (D.title) title(D.title, { f: 60, fp: 40, h: F(110, 90) });
    const top = CB.y + (D.title ? F(140, 104) : 0);
    const gap = F(120, 26);
    const cw = FULL ? (CB.w - gap) / 2 : CB.w;
    const chH = FULL ? CB.y + CB.h - top : (CB.y + CB.h - top - gap) / 2;
    [D.a, D.b].forEach((c, k) => {
      const x = FULL ? CB.x + k * (cw + gap) : CB.x;
      const y = FULL ? top : top + k * (chH + gap);
      const win = D.win === (k ? "b" : "a");
      const box = el("div", "", world, Object.assign(abs(x, y, cw, chH), { boxSizing: "border-box", border: `4px solid ${win ? TH.a : TH.fg}`, background: win ? TH.card : "transparent", padding: F(30, 16) + "px", display: "flex", flexDirection: "column", gap: F(14, 8) + "px", boxShadow: win ? `${F(16, 10)}px ${F(16, 10)}px 0 ${TH.a}` : "none" }));
      const hd = el("div", "", box, { display: "flex", alignItems: "center", gap: F(20, 14) + "px" });
      let ic = null;
      if (c.icon) { const iw = el("div", "", hd, { width: F(96, 56) + "px", height: F(96, 56) + "px", flex: "0 0 auto", color: win ? TH.a : TH.fg }); ic = icon(c.icon, F(96, 56), iw, null, 2.6); }
      const nmw = el("div", "", hd, { flex: "1", minWidth: 0 });
      if (c.kicker) el("div", "mono", nmw, { fontSize: fs(20, 14), color: win ? TH.a : TH.mut, marginBottom: "6px" }, c.kicker);
      const nm = el("div", "disp", nmw, { fontSize: fs(c.f || 60, c.fp || 38), color: TH.fg }, rich(c.name));
      fit(nm, cw - F(200, 120), F(130, 80), 16);
      const rows = (c.rows || []).map((rw, i) => {
        const r = el("div", "", box, { display: "flex", alignItems: "flex-start", gap: F(14, 10) + "px" });
        const ok = rw.ok;
        const mk = el("div", "", r, { width: F(40, 28) + "px", height: F(40, 28) + "px", flex: "0 0 auto", background: ok === true ? TH.pos : ok === false ? TH.neg : TH.soft, color: ok === true && S.bg === "paper" ? "#EFEBE3" : "#0D0D0D", display: "flex", alignItems: "center", justifyContent: "center", marginTop: F(4, 2) + "px" });
        if (ok !== null && ok !== undefined) icon(ok ? "check" : "cross", F(30, 20), mk, null, 6);
        el("div", "ui", r, { fontSize: fs(rw.f || 36, 23), lineHeight: 1.12, color: TH.fg }, rich(rw.t));
        return r;
      });
      let g = 0; while (box.scrollHeight > chH + 2 && g++ < 30) box.querySelectorAll(".ui").forEach(u => u.style.fontSize = parseFloat(getComputedStyle(u).fontSize) * 0.94 + "px");
      ex(box);
      const t = T0 + 0.25 + k * 0.5;
      if (FULL) tl.fromTo(box, { opacity: 0, rotationY: k ? -40 : 40, x: k ? 80 : -80 }, { opacity: 1, rotationY: 0, x: 0, duration: 0.6, ease: E_IN }, t);
      else tl.fromTo(box, { opacity: 0, rotationX: k ? -40 : 40, y: k ? 50 : -50 }, { opacity: 1, rotationX: 0, y: 0, duration: 0.6, ease: E_IN }, t);
      if (ic) draw(ic, t + 0.2, 0.5);
      rows.forEach((r, i) => fin(r, t + 0.3 + i * 0.1, { x: -14, y: 0 }));
      markIn(box, t + 0.7);
      if (c.photo && FULL) {
        const pw = c.pw || 300, ph = c.ph || 330;
        const p = el("div", "photo", world, abs(x + cw - pw + 30, y + chH - ph + 40, pw, ph));
        el("img", "", p).src = "img/" + c.photo + ".jpg";
        if (c.photoCap) el("div", "cap", p, null, c.photoCap);
        ex(p); drop(p, t + 0.5, k ? 4 : -4);
      }
    });
    // middle badge
    const mid = D.mid || "VS";
    const bs = F(110, 64);
    const bx = FULL ? CB.x + cw + gap / 2 - bs / 2 : CB.x + CB.w / 2 - bs / 2;
    const by = FULL ? top + (CB.y + CB.h - top) / 2 - bs / 2 : top + chH + gap / 2 - bs / 2;
    const badge = el("div", "disp", world, Object.assign(abs(bx, by, bs, bs), { borderRadius: "50%", background: TH.fg, color: TH.bg, display: "flex", alignItems: "center", justifyContent: "center", fontSize: fs(mid.length > 2 ? 44 : 50, 28), zIndex: 5 }), mid === "->" ? (FULL ? "→" : "↓") : mid);
    ex(badge); pop(badge, T0 + 0.6, { s: 0.2 });
    tl.fromTo(badge, { rotation: -180 }, { rotation: 0, duration: 0.6, ease: E_IN }, T0 + 0.6);
    if (D.sub) subline(D.sub, CB.x, CB.y + CB.h + F(8, 0), CB.w, { t: 2.0, f: 28 });
  };
  function compareBalance() {
    // seesaw: beam tips toward the heavy side, then the light side gets loaded and it levels out
    if (D.title) title(D.title, { f: 60, fp: 40, h: F(110, 90) });
    const cx = CB.x + CB.w / 2, py = FULL ? CB.y + 470 : CB.y + 450;
    const bw = F(1300, 680);
    const piv = sv("svg", { width: F(160, 110), height: F(150, 100), viewBox: "0 0 160 150" }, world); Object.assign(piv.style, abs(cx - F(80, 55), py));
    sv("polygon", { points: "80,0 160,150 0,150", fill: TH.fg }, piv);
    ex(piv); pop(piv, T0 + 0.1, { s: 0.3 });
    const beam = el("div", "", world, Object.assign(abs(cx - bw / 2, py - F(14, 10), bw, F(20, 14)), { background: TH.fg, transformOrigin: "50% 50%" }));
    ex(beam); tl.fromTo(beam, { scaleX: 0 }, { scaleX: 1, duration: 0.5, ease: "expo.out" }, T0 + 0.2);
    const pans = [D.a, D.b].map((c, k) => {
      const pw = F(470, 300), ph = F(250, 190);
      const px = k ? cx + bw / 2 - pw : cx - bw / 2;
      const pan = el("div", "", world, Object.assign(abs(px, py - F(14, 10) - ph - F(10, 6), pw, ph), { display: "flex", flexDirection: "column", justifyContent: "flex-end", alignItems: "center", transformOrigin: "50% 100%" }));
      const stack = el("div", "", pan, { display: "flex", flexDirection: "column-reverse", alignItems: "center", gap: F(8, 6) + "px", marginBottom: F(10, 6) + "px" });
      const blocks = (c.blocks || []).map((b, i) => el("div", "disp", stack, { background: k ? TH.a2 : TH.a, color: "#0D0D0D", fontSize: fs(30, 20), padding: F(10, 7) + "px " + F(22, 12) + "px", border: `3px solid ${TH.fg}`, whiteSpace: "nowrap" }, b));
      const nm = el("div", "disp", pan, { fontSize: fs(c.f || 58, 34), color: TH.fg, order: -1, marginBottom: F(10, 6) + "px", textAlign: "center" }, rich(c.name));
      ex(pan);
      return { pan, blocks, nm, k };
    });
    // beam rotation: heavy left first, then level
    const ang = F(9, 11);
    const tilt = (deg, t, d) => {
      tl.to(beam, { rotation: -deg, duration: d, ease: "back.out(1.6)" }, t);
      const dy = Math.sin(deg * Math.PI / 180) * (bw / 2 - F(235, 150));
      tl.to(pans[0].pan, { y: dy, duration: d, ease: "back.out(1.6)" }, t);
      tl.to(pans[1].pan, { y: -dy, duration: d, ease: "back.out(1.6)" }, t);
    };
    fin(pans[0].nm, T0 + 0.35, { y: 16 }); fin(pans[1].nm, T0 + 0.45, { y: 16 });
    pans[0].blocks.forEach((b, i) => tl.fromTo(b, { opacity: 0, y: -F(200, 140) }, { opacity: 1, y: 0, duration: 0.4, ease: "bounce.out" }, T0 + 0.5 + i * 0.16));
    tilt(-ang, T0 + 0.55, 0.7);
    const tb = T0 + 0.5 + pans[0].blocks.length * 0.16 + 0.75;
    pans[1].blocks.forEach((b, i) => tl.fromTo(b, { opacity: 0, y: -F(200, 140) }, { opacity: 1, y: 0, duration: 0.4, ease: "bounce.out" }, tb + i * 0.16));
    if (pans[1].blocks.length) tilt(0, tb + 0.2, 0.9);
    if (D.sub) subline(D.sub, CB.x, py + F(190, 130), CB.w, { t: tb + 0.7, f: 36, fp: 24, h: F(120, 100) });
  }

  // ---------------------------------------------------------------- clock / dial
  R.clock = function () {
    const v = D.variant || "window";
    if (D.title) title(D.title, { f: 60, fp: 40, h: F(130, 96), w: FULL ? 820 : CB.w });
    const r = F(D.r || 325, D.rp || 215);
    const cx = FULL ? CB.x + CB.w - r - 70 : CB.x + CB.w / 2, cy = FULL ? CB.y + 350 : CB.y + 110 + r + 30;
    const svg = sv("svg", { width: r * 2 + 120, height: r * 2 + 120, viewBox: `${-r - 60} ${-r - 60} ${r * 2 + 120} ${r * 2 + 120}` }, world);
    Object.assign(svg.style, abs(cx - r - 60, cy - r - 60));
    ex(svg);
    const face = sv("circle", { cx: 0, cy: 0, r, fill: TH.card, stroke: TH.fg, "stroke-width": F(6, 5) }, svg);
    const maxV = D.max || 12; // units around the dial
    const A = vv => -Math.PI / 2 + (vv / maxV) * Math.PI * 2;
    const ticks = sv("g", {}, svg);
    for (let i = 0; i < (D.ticks || maxV); i++) {
      const a = -Math.PI / 2 + (i / (D.ticks || maxV)) * Math.PI * 2;
      const big = (D.majorEvery ? i % D.majorEvery === 0 : true);
      const r0 = r - (big ? F(34, 26) : F(18, 14)), r1 = r - F(10, 8);
      sv("line", { x1: r0 * Math.cos(a), y1: r0 * Math.sin(a), x2: r1 * Math.cos(a), y2: r1 * Math.sin(a), stroke: TH.fg, "stroke-width": big ? F(5, 4) : F(2.5, 2) }, ticks);
    }
    (D.nums || []).forEach(nm => {
      const a = A(nm.v), rr = r - F(70, 54);
      const lb = el("div", "mono", world, Object.assign(abs(cx + rr * Math.cos(a) - 50, cy + rr * Math.sin(a) - F(14, 11), 100), { textAlign: "center", fontSize: fs(24, 18), color: TH.mut }), nm.l);
      ex(lb); fin(lb, T0 + 0.4, { y: 6 });
    });
    tl.fromTo(svg, { scale: 0.6, opacity: 0, rotation: -30 }, { scale: 1, opacity: 1, rotation: 0, duration: 0.7, ease: E_IN }, T0 + 0.1);
    draw(ticks, T0 + 0.3, 0.3, 0.008);
    const arcs = D.arcs || [];
    arcs.forEach((ac, i) => {
      const rr = ac.r ? r * ac.r : r - F(110, 84);
      const a0 = A(ac.from), a1 = A(ac.to);
      const large = (ac.to - ac.from) / maxV > 0.5 ? 1 : 0;
      const p = sv("path", { d: `M${rr * Math.cos(a0)} ${rr * Math.sin(a0)} A${rr} ${rr} 0 ${large} 1 ${rr * Math.cos(a1)} ${rr * Math.sin(a1)}`, stroke: ac.col === "a2" ? TH.a2 : ac.col === "fg" ? TH.fg : TH.a, "stroke-width": ac.w ? F(ac.w, ac.w * 0.75) : F(46, 36), fill: "none", "stroke-linecap": "butt", opacity: ac.op || 1 }, svg);
      draw(p, ac.t || (T0 + 0.8 + i * 0.5), ac.d || 0.9, 0);
    });
    // hand sweeping to D.hand
    if (D.hand !== undefined) {
      const hand = sv("g", {}, svg);
      sv("line", { x1: 0, y1: F(30, 24), x2: 0, y2: -(r - F(40, 30)), stroke: TH.fg, "stroke-width": F(9, 7), "stroke-linecap": "round" }, hand);
      sv("circle", { cx: 0, cy: 0, r: F(18, 14), fill: TH.fg }, hand);
      sv("circle", { cx: 0, cy: 0, r: F(7, 5), fill: TH.a }, hand);
      tl.fromTo(hand, { rotation: (D.handFrom || 0) / maxV * 360, transformOrigin: "0px 0px", svgOrigin: "0 0" }, { rotation: D.hand / maxV * 360, svgOrigin: "0 0", duration: D.handDur || 1.6, ease: "power2.inOut" }, D.handAt || T0 + 0.9);
    }
    if (D.center) {
      const cc = el("div", "disp", world, Object.assign(abs(cx - r * 0.5, D.centerUp ? cy - r * 0.62 : cy + r * 0.18, r), { textAlign: "center", fontSize: fs(54, 40), color: TH.fg, lineHeight: 0.95 }), rich(D.center));
      fit(cc, r, r * 0.4, 16); ex(cc); pop(cc, D.centerAt || 2.0, { s: 0.5 });
    }
    (D.labels || []).forEach((lb, i) => {
      const a = A(lb.v), rr = r + F(40, 30);
      const lx = cx + rr * Math.cos(a), ly = cy + rr * Math.sin(a);
      const right = Math.cos(a) >= -0.05;
      const L = el("div", "", world, Object.assign(abs(right ? lx : lx - F(300, 200), ly - F(24, 18), F(300, 200)), { textAlign: right ? "left" : "right" }));
      el("div", "disp", L, { fontSize: fs(34, 24), color: lb.hot ? TH.a : TH.fg, lineHeight: 0.95 }, rich(lb.t));
      if (lb.d) el("div", "mono", L, { fontSize: fs(18, 13), color: TH.mut, marginTop: "4px" }, lb.d);
      ex(L); fin(L, lb.at || (T0 + 1.0 + i * 0.3), { y: 10 });
    });
    // legend / key lines on the left (full) or below (panel)
    if (D.keys) {
      const kx = CB.x, ky = FULL ? CB.y + F(200, 0) : cy + r + 50;
      D.keys.forEach((k, i) => {
        const row = el("div", "", world, Object.assign(abs(kx, ky + i * F(200, 0), FULL ? 760 : CB.w), { display: "flex", gap: F(22, 14) + "px", alignItems: "flex-start" }));
        el("div", "", row, { width: F(56, 30) + "px", height: F(56, 30) + "px", background: k.col === "a2" ? TH.a2 : k.col === "fg" ? TH.fg : TH.a, flex: "0 0 auto", marginTop: F(6, 4) + "px", border: `3px solid ${TH.fg}`, boxSizing: "border-box" });
        const tx = el("div", "", row, { flex: 1 });
        el("div", "disp", tx, { fontSize: fs(72, 30), color: TH.fg, lineHeight: 0.95 }, rich(k.t));
        if (k.d) el("div", "uim", tx, { fontSize: fs(36, 20), color: TH.mut, marginTop: "8px", lineHeight: 1.15 }, rich(k.d));
        ex(row); fin(row, k.at || (T0 + 0.9 + i * 0.5), { x: -20, y: 0 });
        markIn(row, (k.at || (T0 + 0.9 + i * 0.5)) + 0.4);
      });
    }
    if (D.sub) subline(D.sub, CB.x, FULL ? CB.y + CB.h - F(150, 0) : CB.y + CB.h - 60, FULL ? 820 : CB.w, { t: D.subAt || 2.3, f: 34, fp: 22, h: F(150, 80) });
  };

  // ---------------------------------------------------------------- chart variants
  R.chart = function () {
    const v = D.variant;
    if (D.title) title(D.title, { f: 60, fp: 40, h: F(130, 96), w: (v === "gauge" || v === "fill") && FULL ? 860 : CB.w });
    if (v === "months") return chartMonths();
    if (v === "gauge") return chartGauge();
    if (v === "range") return chartRange();
    if (v === "status") return chartStatus();
    if (v === "fill") return chartFill();
    if (v === "dots") return chartDots();
  };
  function chartMonths() {
    const M = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"];
    const on = D.on; // indexes
    const top = CB.y + F(160, 120);
    const cols = FULL ? 12 : 6;
    const gap = F(12, 10);
    const cw = (CB.w - gap * (cols - 1)) / cols, ch = F(210, 150);
    const order = D.order || [...Array(12).keys()];
    order.forEach((m, i) => {
      const c = i % cols, r = Math.floor(i / cols);
      const x = CB.x + c * (cw + gap), y = top + r * (ch + gap);
      const lit = on.includes(m);
      const cell = el("div", "", world, Object.assign(abs(x, y, cw, ch), { boxSizing: "border-box", border: `3px solid ${TH.fg}`, background: TH.card, display: "flex", flexDirection: "column", justifyContent: "space-between", padding: F(14, 10) + "px" }));
      const mn = el("div", "disp", cell, { fontSize: fs(34, 28), color: TH.fg }, M[m]);
      const dot = el("div", "", cell, { width: F(44, 32) + "px", height: F(44, 32) + "px", borderRadius: "50%", border: `3px solid ${TH.fg}`, alignSelf: "flex-end", boxSizing: "border-box", color: TH.fg, display: "flex", alignItems: "center", justifyContent: "center" });
      ex(cell);
      const t = T0 + 0.25 + i * 0.04;
      tl.fromTo(cell, { opacity: 0, rotationX: -90, transformOrigin: "50% 0%" }, { opacity: 1, rotationX: 0, duration: 0.45, ease: E_IN }, t);
      if (lit) {
        const tt = 1.1 + on.indexOf(m) * 0.08;
        tl.to(cell, { backgroundColor: TH.a, borderColor: TH.a, duration: 0.15 }, tt);
        tl.to(mn, { color: "#0D0D0D", duration: 0.15 }, tt);
        tl.to(dot, { backgroundColor: "#0D0D0D", borderColor: "#0D0D0D", duration: 0.15 }, tt);
      }
    });
    const rows = Math.ceil(12 / cols);
    const by = top + rows * (ch + gap) + F(40, 26);
    if (D.big) {
      const b = el("div", "", world, Object.assign(abs(CB.x, by, CB.w), { display: "flex", alignItems: "baseline", gap: F(26, 14) + "px", flexWrap: "wrap" }));
      const r = roller(b, D.big, { size: F(150, 96), seed: 2 });
      el("div", "disp", b, { fontSize: fs(70, 44), color: TH.fg }, rich(D.bigUnit || ""));
      ex(b); r._anim(1.6, 1.0);
      if (D.sub) subline(D.sub, CB.x, by + F(170, 110), CB.w, { t: 2.1, f: 34, fp: 23, h: F(80, 90) });
    }
  }
  function chartGauge() {
    const r = F(330, 250);
    const cx = FULL ? CB.x + CB.w - r - 40 : CB.x + CB.w / 2, cy = FULL ? CB.y + 520 : CB.y + 470;
    const svg = sv("svg", { width: r * 2 + 120, height: r + 140, viewBox: `${-r - 60} ${-r - 60} ${r * 2 + 120} ${r + 140}` }, world);
    Object.assign(svg.style, abs(cx - r - 60, cy - r - 60)); ex(svg);
    const seg = 5;
    for (let i = 0; i < seg; i++) {
      const a0 = Math.PI + (i / seg) * Math.PI + 0.025, a1 = Math.PI + ((i + 1) / seg) * Math.PI - 0.025;
      const rr = r - F(40, 30);
      const p = sv("path", { d: `M${rr * Math.cos(a0)} ${rr * Math.sin(a0)} A${rr} ${rr} 0 0 1 ${rr * Math.cos(a1)} ${rr * Math.sin(a1)}`, stroke: i >= 3 ? TH.a : (i === 2 ? TH.mut : TH.fg), "stroke-width": F(70, 54), fill: "none", opacity: i >= 3 ? 1 : 0.85 }, svg);
      draw(p, T0 + 0.3 + i * 0.08, 0.35, 0);
    }
    const lab = (t, a, al) => { const x = cx + (r + F(30, 20)) * Math.cos(a), y = cy + (r + F(30, 20)) * Math.sin(a); const L = el("div", "mono", world, Object.assign(abs(al === "r" ? x - 220 : x, y - 10, 220), { fontSize: fs(22, 16), color: TH.mut, textAlign: al === "r" ? "right" : "left" }), t); ex(L); fin(L, 0.8, { y: 8 }); };
    lab(D.lo || "EASY", Math.PI + 0.02, "r"); lab(D.hi || "MAX", -0.02, "l");
    const hand = sv("g", {}, svg);
    sv("line", { x1: 0, y1: 0, x2: -(r - F(70, 56)), y2: 0, stroke: TH.fg, "stroke-width": F(12, 9), "stroke-linecap": "round" }, hand);
    sv("circle", { cx: 0, cy: 0, r: F(26, 20), fill: TH.fg }, hand);
    const v0 = D.from !== undefined ? D.from : 0.85, v1 = D.to !== undefined ? D.to : 0.55;
    tl.fromTo(hand, { rotation: 0, svgOrigin: "0 0" }, { rotation: v0 * 180, svgOrigin: "0 0", duration: 0.9, ease: "back.out(1.4)" }, T0 + 0.6);
    tl.to(hand, { rotation: v1 * 180, svgOrigin: "0 0", duration: 0.9, ease: "back.out(1.2)" }, D.dropAt || 2.0);
    const ro = el("div", "disp", world, Object.assign(abs(cx - r, cy + F(40, 30), r * 2), { textAlign: "center", fontSize: fs(46, 32), color: TH.fg }), rich(D.readout || "PERCEIVED EFFORT"));
    fit(ro, r * 2, F(60, 50), 14); ex(ro); fin(ro, 0.9, { y: 14 });
    if (D.chip) { const c = el("div", "mono pill", world, Object.assign(abs(cx - r * 0.2 - F(60, 40), cy - r - F(40, 30)), { fontSize: fs(22, 16), color: TH.bg, background: TH.a, borderColor: TH.a }), D.chip); ex(c); pop(c, (D.dropAt || 2.0) - 0.1, { s: 0.5 }); }
    if (D.keys && FULL) {
      D.keys.forEach((k, i) => {
        const row = el("div", "", world, Object.assign(abs(CB.x, CB.y + 210 + i * 150, 780), {}));
        el("div", "disp", row, { fontSize: fs(46, 30), color: i === 0 ? TH.fg : TH.a, lineHeight: 0.95 }, rich(k.t));
        if (k.d) el("div", "uim", row, { fontSize: fs(30, 20), color: TH.mut, marginTop: "8px", lineHeight: 1.15 }, rich(k.d));
        ex(row); fin(row, k.at || (1.0 + i * 1.0), { x: -20, y: 0 }); markIn(row, (k.at || (1.0 + i * 1.0)) + 0.4);
      });
    } else if (D.keys) {
      const k = D.keys[D.keys.length - 1];
      const row = el("div", "", world, Object.assign(abs(CB.x, cy + F(110, 100), CB.w), { textAlign: "center" }));
      el("div", "uim", row, { fontSize: "24px", color: TH.mut, lineHeight: 1.15 }, rich(k.d || k.t));
      ex(row); fin(row, 2.4, { y: 10 });
    }
  }
  function chartRange() {
    const lo = D.min, hi = D.max;
    const top = CB.y + F(290, 250);
    const x0 = CB.x + F(30, 20), x1 = CB.x + CB.w - F(30, 20);
    const X = v => x0 + (x1 - x0) * (v - lo) / (hi - lo);
    const axis = el("div", "", world, Object.assign(abs(x0, top, x1 - x0, F(8, 6)), { background: TH.fg, transformOrigin: "0 50%" }));
    ex(axis); tl.fromTo(axis, { scaleX: 0 }, { scaleX: 1, duration: 0.7, ease: "expo.inOut" }, T0 + 0.2);
    for (let v = lo; v <= hi; v += (D.step || 1)) {
      const big = (v - lo) % (D.major || 5) === 0;
      const tk = el("div", "", world, Object.assign(abs(X(v) - 1.5, top + F(8, 6), 3, big ? F(30, 22) : F(16, 12)), { background: TH.fg }));
      ex(tk); fin(tk, T0 + 0.4 + (v - lo) * 0.015, { y: -6 });
      if (big) { const l = el("div", "mono", world, Object.assign(abs(X(v) - 40, top + F(44, 32), 80), { textAlign: "center", fontSize: fs(24, 16), color: TH.mut }), String(v)); ex(l); fin(l, T0 + 0.5, { y: 6 }); }
    }
    (D.bands || []).forEach((b, i) => {
      const band = el("div", "", world, Object.assign(abs(X(b.from), top - F(90, 70), X(b.to) - X(b.from), F(90, 70)), { background: b.col === "a2" ? TH.a2 : TH.a, opacity: 0.9, transformOrigin: "0 100%", border: `3px solid ${TH.fg}`, boxSizing: "border-box" }));
      const bl = el("div", "mono", world, Object.assign(abs(X(b.from), top - F(132, 104), X(b.to) - X(b.from)), { textAlign: "center", fontSize: fs(22, 15), color: TH.fg }), b.label || "");
      ex(band); ex(bl);
      tl.fromTo(band, { scaleY: 0 }, { scaleY: 1, duration: 0.5, ease: E_BACK }, 1.0 + i * 0.3);
      fin(bl, 1.2 + i * 0.3, { y: 10 });
    });
    (D.marks || []).forEach((m, i) => {
      const mk = el("div", "", world, Object.assign(abs(X(m.v) - F(30, 22), top + F(90, 70), F(60, 44)), { display: "flex", flexDirection: "column", alignItems: "center" }));
      const tri = sv("svg", { width: F(40, 30), height: F(30, 22), viewBox: "0 0 40 30" }, mk); sv("polygon", { points: "20,0 40,30 0,30", fill: TH.a }, tri);
      const lb = el("div", "", world, Object.assign(abs(X(m.v) - 220, top + F(130, 100), 440), { textAlign: "center" }));
      const r = roller(lb, m.num, { size: F(120, 80), seed: 3 });
      el("div", "mono", lb, { fontSize: fs(22, 15), color: TH.mut, marginTop: "8px" }, m.label);
      ex(mk); ex(lb);
      tl.fromTo(mk, { opacity: 0, x: -(X(m.v) - x0) }, { opacity: 1, x: 0, duration: 1.0, ease: "expo.out" }, 1.6 + i * 0.3);
      r._anim(1.6 + i * 0.3, 1.0);
    });
    if (D.sub) subline(D.sub, CB.x, CB.y + CB.h - F(70, 80), CB.w, { t: 2.4, f: 32, fp: 22, h: F(80, 90) });
  }
  function chartStatus() {
    const top = CB.y + F(150, 116);
    const n = D.rows.length;
    const rh = Math.min(F(150, 130), (CB.y + CB.h - top - (D.sub ? F(70, 60) : 0)) / n);
    D.rows.forEach((rw, i) => {
      const y = top + i * rh, t = T0 + 0.35 + i * 0.25;
      const row = el("div", "", world, Object.assign(abs(CB.x, y, CB.w, rh - F(18, 12)), { display: "flex", alignItems: "center", gap: F(26, 14) + "px", borderTop: `3px solid ${TH.fg}`, boxSizing: "border-box", paddingTop: F(10, 8) + "px" }));
      const nm = el("div", "disp", row, { fontSize: fs(54, 34), width: F(420, 230) + "px", flex: "0 0 auto", color: TH.fg }, rich(rw.name));
      fit(nm, F(420, 230), rh, 14);
      const barw = FULL ? 520 : 200;
      const bar = el("div", "", row, { width: barw + "px", height: F(36, 26) + "px", border: `3px solid ${TH.fg}`, flex: "0 0 auto", position: "relative", boxSizing: "border-box" });
      const fl = el("div", "", bar, { position: "absolute", left: 0, top: 0, bottom: 0, width: (rw.v * 100) + "%", background: rw.ok ? TH.pos : TH.neg, transformOrigin: "0 50%" });
      const tx = el("div", "", row, { flex: 1, minWidth: 0 });
      el("div", "ui", tx, { fontSize: fs(32, 20), color: rw.ok ? TH.fg : TH.a, lineHeight: 1.05 }, rich(rw.t));
      if (rw.d) el("div", "uim", tx, { fontSize: fs(24, 16), color: TH.mut, lineHeight: 1.1, marginTop: "4px" }, rich(rw.d));
      ex(row); wipe(row, t, { d: 0.4 });
      tl.fromTo(fl, { scaleX: 0 }, { scaleX: 1, duration: 0.8, ease: "expo.out" }, t + 0.25);
    });
    if (D.sub) subline(D.sub, CB.x, CB.y + CB.h - F(60, 52), CB.w, { t: 2.2, f: 30, fp: 21 });
  }
  function chartFill() {
    // isometric-ish bottle that fills to a value with a marked target band
    const bwid = F(300, 220), bh = F(560, 430);
    const bx = FULL ? CB.x + 860 : CB.x + 80, by = FULL ? CB.y + 70 : CB.y + 150;
    const maxL = D.max || 3;
    const body = el("div", "", world, Object.assign(abs(bx, by + F(70, 50), bwid, bh - F(70, 50)), { border: `5px solid ${TH.fg}`, borderRadius: F(40, 30) + "px " + F(40, 30) + "px " + F(30, 22) + "px " + F(30, 22) + "px", overflow: "hidden", boxSizing: "border-box", background: TH.card }));
    const neck = el("div", "", world, Object.assign(abs(bx + bwid * 0.3, by, bwid * 0.4, F(78, 56)), { border: `5px solid ${TH.fg}`, borderBottom: "none", boxSizing: "border-box", background: TH.card }));
    const cap = el("div", "", world, Object.assign(abs(bx + bwid * 0.26, by - F(30, 22), bwid * 0.48, F(34, 26)), { background: TH.fg }));
    const liquidH = (bh - F(70, 50)) - 10;
    const liq = el("div", "", body, { position: "absolute", left: 0, right: 0, bottom: 0, height: (D.value / maxL * liquidH) + "px", background: TH.a, transformOrigin: "50% 100%" });
    const wave = el("div", "", liq, { position: "absolute", left: "-10%", right: "-10%", top: "-14px", height: "28px", background: `radial-gradient(circle at 12px 0, transparent 13px, ${TH.a} 14px) 0 0/28px 28px repeat-x` });
    [body, neck, cap].forEach(ex);
    tl.fromTo([body, neck, cap], { opacity: 0, y: F(60, 40) }, { opacity: 1, y: 0, duration: 0.5, ease: E_IN, stagger: 0.05 }, T0 + 0.1);
    tl.fromTo(liq, { scaleY: 0 }, { scaleY: 1, duration: 1.6, ease: "power2.inOut" }, 0.7);
    tl.fromTo(wave, { x: 0 }, { x: 56, duration: DUR, ease: "none" }, 0);
    // scale ticks + labels on the left of the bottle
    for (let l = 0; l <= maxL; l += 0.5) {
      const y = by + F(70, 50) + 5 + liquidH * (1 - l / maxL);
      const big = l % 1 === 0;
      const tk = el("div", "", world, Object.assign(abs(bx - (big ? F(40, 30) : F(22, 16)), y - 1.5, big ? F(40, 30) : F(22, 16), 3), { background: TH.fg })); ex(tk); fin(tk, 0.5 + l * 0.08, { x: -8, y: 0 });
      if (big) { const lb = el("div", "mono", world, Object.assign(abs(bx - F(150, 110), y - F(14, 10), F(100, 74)), { textAlign: "right", fontSize: fs(24, 17), color: TH.mut }), l + " L"); ex(lb); fin(lb, 0.55 + l * 0.08, { x: -8, y: 0 }); }
    }
    (D.bands || []).forEach((b, i) => {
      const yTop = by + F(70, 50) + 5 + liquidH * (1 - b.to / maxL), yBot = by + F(70, 50) + 5 + liquidH * (1 - b.from / maxL);
      const brk = sv("svg", { width: F(50, 36), height: Math.max(8, yBot - yTop) }, world); Object.assign(brk.style, abs(bx + bwid + F(16, 12), yTop));
      sv("path", { d: `M0 2 H${F(26, 18)} V${yBot - yTop - 2} H0`, stroke: b.col === "fg" ? TH.fg : TH.a, "stroke-width": 5, fill: "none" }, brk);
      const lb = el("div", "", world, Object.assign(abs(bx + bwid + F(70, 52), (yTop + yBot) / 2 - F(36, 26) + F(b.dy || 0, (b.dy || 0) * 0.8), FULL ? CB.x + CB.w - (bx + bwid + 70) : CB.x + CB.w - (bx + bwid + 52)), {}));
      el("div", "disp", lb, { fontSize: fs(42, 28), color: b.col === "fg" ? TH.fg : TH.a, lineHeight: 0.95 }, rich(b.t));
      if (b.d) el("div", "mono", lb, { fontSize: fs(18, 13), color: TH.mut, marginTop: "6px", lineHeight: 1.2 }, b.d);
      ex(brk); ex(lb); draw(brk, b.at || (1.8 + i * 0.5), 0.4, 0); fin(lb, (b.at || (1.8 + i * 0.5)) + 0.15, { x: 16, y: 0 });
    });
    if (D.big) {
      const bb = el("div", "", world, Object.assign(abs(CB.x, CB.y + F(190, 0), 700), { display: FULL ? "flex" : "none", alignItems: "flex-end", gap: "20px" }));
      if (FULL) { const r = roller(bb, D.big, { size: 260, seed: 4 }); el("div", "disp", bb, { fontSize: "110px", paddingBottom: "16px" }, D.bigUnit || ""); r._anim(0.8, 1.3); ex(bb); }
    }
    if (D.sub) subline(D.sub, CB.x, FULL ? CB.y + 500 : CB.y + CB.h - 40, FULL ? 760 : CB.w, { t: 2.2, f: 34, fp: 22, h: FULL ? 180 : 60 });
  }
  function chartDots() {
    // a field of small figures; a subset lights up (illustrative, not a statistic)
    const cols = F(14, 8), rows = F(3, 4);
    const top = CB.y + F(170, 130);
    const cw = F(70, 62), chh = F(96, 84);
    const total = cols * rows;
    const lit = new Set(D.lit || []);
    for (let i = 0; i < total; i++) {
      const c = i % cols, r = Math.floor(i / cols);
      const w = el("div", "", world, Object.assign(abs(CB.x + c * (cw + F(52, 26)) * (FULL ? 0.86 : 1), top + r * (chh + 20), cw, chh), { color: TH.mut }));
      icon("person", cw, w, null, 3);
      ex(w); pop(w, T0 + 0.2 + i * 0.012, { s: 0.3, d: 0.3 });
      if (lit.has(i)) tl.to(w, { color: TH.a, duration: 0.15 }, 1.3 + (i % 7) * 0.04);
    }
    if (D.keys) {
      const ky = top + rows * (chh + 20) + F(30, 20);
      D.keys.forEach((k, i) => {
        const row = el("div", "", world, Object.assign(abs(FULL ? CB.x + i * 860 : CB.x, FULL ? ky : ky + i * 80, FULL ? 820 : CB.w), { display: "flex", gap: "16px", alignItems: "flex-start" }));
        el("div", "", row, { width: F(34, 26) + "px", height: F(34, 26) + "px", background: i === 0 ? TH.a : TH.mut, flex: "0 0 auto", marginTop: "6px" });
        const tx = el("div", "", row, {});
        el("div", "disp", tx, { fontSize: fs(40, 28), color: TH.fg }, rich(k.t));
        if (k.d) el("div", "uim", tx, { fontSize: fs(26, 18), color: TH.mut, marginTop: "4px" }, rich(k.d));
        ex(row); fin(row, 1.6 + i * 0.3, { x: -16, y: 0 });
      });
    }
  }

  // ---------------------------------------------------------------- isometric bars
  R.bars = function () {
    if (D.title) title(D.title, { f: 60, fp: 40, h: F(120, 96) });
    const bars = D.bars, n = bars.length;
    const baseY = CB.y + CB.h - F(100, 90);
    const topY = CB.y + F(D.title && D.title.length > 34 ? 280 : 210, 220);
    const areaX = CB.x + F(20, 0), areaW = (D.side && FULL ? CB.w - 640 : CB.w) - F(20, 0);
    const slot = areaW / n;
    const bw = Math.min(F(230, 120), slot * 0.56), dep = bw * 0.42;
    const maxV = D.max || Math.max(...bars.map(b => b.v));
    const svg = sv("svg", { width: W, height: H }, world); Object.assign(svg.style, abs(0, 0)); ex(svg);
    // floor line
    const fl = sv("line", { x1: areaX - 10, y1: baseY, x2: areaX + areaW + 10, y2: baseY, stroke: TH.fg, "stroke-width": 4 }, svg);
    draw(fl, T0 + 0.15, 0.5, 0);
    bars.forEach((b, i) => {
      const x = areaX + slot * i + (slot - bw - dep) / 2;
      const hFull = (baseY - topY) * (b.v / maxV);
      const col = b.hl ? TH.a : (b.ghost ? "transparent" : TH.fg);
      const g = sv("g", {}, svg);
      const front = sv("rect", { x, y: baseY, width: bw, height: 0, fill: col, stroke: TH.fg, "stroke-width": 3, "stroke-dasharray": b.ghost ? "10 8" : "none" }, g);
      const side = sv("polygon", { points: "", fill: b.hl ? TH.ext : (b.ghost ? "transparent" : TH.mut), stroke: TH.fg, "stroke-width": 3, "stroke-dasharray": b.ghost ? "10 8" : "none" }, g);
      const topf = sv("polygon", { points: "", fill: b.hl ? "#ff8a5c" : (b.ghost ? "transparent" : (S.bg === "paper" ? "#4a4741" : "#d9d4c9")), stroke: TH.fg, "stroke-width": 3, "stroke-dasharray": b.ghost ? "10 8" : "none" }, g);
      const p = { h: 0 };
      const upd = () => {
        const h = p.h, yT = baseY - h;
        front.setAttribute("y", yT); front.setAttribute("height", Math.max(0, h));
        side.setAttribute("points", `${x + bw},${yT} ${x + bw + dep},${yT - dep * 0.6} ${x + bw + dep},${baseY - dep * 0.6} ${x + bw},${baseY}`);
        topf.setAttribute("points", `${x},${yT} ${x + dep},${yT - dep * 0.6} ${x + bw + dep},${yT - dep * 0.6} ${x + bw},${yT}`);
      };
      upd();
      const t = T0 + 0.4 + i * 0.22;
      tl.fromTo(p, { h: 0 }, { h: hFull, duration: 0.9, ease: "expo.out", onUpdate: upd }, t);
      // value label rides the top
      const vl = el("div", "", world, Object.assign(abs(x - 60, baseY - hFull - dep * 0.6 - F(110, 74), bw + dep + 120), { textAlign: "center" }));
      if (b.disp) { const dd = el("div", "disp", vl, { fontSize: fs(b.vf || 76, 40), color: b.hl ? TH.a : TH.fg, lineHeight: 1 }, rich(b.disp)); fit(dd, bw + dep + 120, 0, 14); }
      if (b.note) el("div", "mono", vl, { fontSize: fs(18, 13), color: TH.mut, marginTop: "4px" }, b.note);
      ex(vl); tl.fromTo(vl, { opacity: 0, y: hFull }, { opacity: 1, y: 0, duration: 0.9, ease: "expo.out" }, t);
      const nl = el("div", "", world, Object.assign(abs(x - 40, baseY + F(16, 12), bw + dep + 80), { textAlign: "center" }));
      const nn = el("div", "disp", nl, { fontSize: fs(b.lf || 40, 24), color: TH.fg, lineHeight: 0.95 }, rich(b.label));
      fit(nn, bw + dep + 80, F(80, 60), 12);
      ex(nl); fin(nl, t + 0.1, { y: 10 });
    });
    if (D.side && FULL) {
      const sx = CB.x + CB.w - 580;
      const s = el("div", "", world, Object.assign(abs(sx, CB.y + 230, 580), {}));
      el("div", "disp", s, { fontSize: "64px", color: TH.fg, lineHeight: 0.98 }, rich(D.side.t));
      if (D.side.d) el("div", "uim", s, { fontSize: "36px", color: TH.mut, lineHeight: 1.2, marginTop: "22px" }, rich(D.side.d));
      fit(s, 580, 420, 14);
      ex(s); fin(s, D.side.at || 1.8, { x: 30, y: 0 }); markIn(s, (D.side.at || 1.8) + 0.4);
    }
    if (D.illus) { const il = el("div", "monor", world, Object.assign(abs(CB.x + F(30, 24), CB.y + CB.h - F(30, 26), CB.w - F(60, 48)), { fontSize: fs(19, 14), color: TH.mut }), D.illus); ex(il); fin(il, 1.5, { y: 6 }); }
  };

  // ---------------------------------------------------------------- body map (back view)
  R.bodymap = function () {
    if (D.title) title(D.title, { f: 60, fp: 40, h: F(130, 96), w: FULL ? 900 : CB.w });
    const sc = F(1.0, 0.82);
    const fw = 300 * sc, fh = 640 * sc;
    const fx = FULL ? CB.x + (D.fx || 1000) : CB.x + 20, fy = FULL ? CB.y + 30 : CB.y + 110;
    const svg = sv("svg", { width: fw, height: fh, viewBox: "0 0 300 640" }, world); Object.assign(svg.style, abs(fx, fy)); ex(svg);
    const st = { fill: TH.card, stroke: TH.fg, "stroke-width": 4, "stroke-linejoin": "round" };
    const body = sv("g", {}, svg);
    // simple geometric back-view figure
    sv("circle", Object.assign({ cx: 150, cy: 48, r: 36 }, st), body);
    sv("path", Object.assign({ d: "M138 82h24v22h-24z" }, st), body);
    sv("path", Object.assign({ d: "M86 108 Q150 92 214 108 L226 200 Q222 262 204 300 L96 300 Q78 262 74 200 Z" }, st), body);
    sv("path", Object.assign({ d: "M86 112 Q64 120 58 160 L44 280 Q42 300 56 302 Q66 302 70 284 L88 176 Z" }, st), body);
    sv("path", Object.assign({ d: "M214 112 Q236 120 242 160 L256 280 Q258 300 244 302 Q234 302 230 284 L212 176 Z" }, st), body);
    sv("path", Object.assign({ d: "M96 296 L204 296 Q214 330 206 352 L154 356 L146 356 L94 352 Q86 330 96 296 Z" }, st), body);
    sv("path", Object.assign({ d: "M96 350 L146 354 L140 470 Q138 486 122 486 Q104 486 104 470 Z" }, st), body);
    sv("path", Object.assign({ d: "M204 350 L154 354 L160 470 Q162 486 178 486 Q196 486 196 470 Z" }, st), body);
    sv("path", Object.assign({ d: "M104 482 L140 482 L134 596 L112 596 Z" }, st), body);
    sv("path", Object.assign({ d: "M196 482 L160 482 L166 596 L188 596 Z" }, st), body);
    sv("path", Object.assign({ d: "M106 594 L136 594 L140 620 L96 620 Z" }, st), body);
    sv("path", Object.assign({ d: "M194 594 L164 594 L160 620 L204 620 Z" }, st), body);
    sv("path", { d: "M150 110 V292", stroke: TH.fg, "stroke-width": 3, fill: "none", opacity: 0.5 }, body);
    draw(body, T0 + 0.15, 0.8, 0.03);
    tl.fromTo(body.querySelectorAll("path,circle"), { fillOpacity: 0 }, { fillOpacity: 1, duration: 0.4, stagger: 0.02 }, 0.7);
    const SPOTS = {
      calves: [[122, 528, 13, 36], [178, 528, 13, 36]],
      hamstrings: [[122, 410, 15, 50], [178, 410, 15, 50]],
      quads: [[122, 410, 15, 50], [178, 410, 15, 50]],
    };
    (D.spots || []).forEach((spt, k) => {
      const t = (spt.at || 1.1 + k * 0.7);
      const g = sv("g", {}, svg);
      SPOTS[spt.part].forEach(([x, y, rx, ry]) => {
        const e = sv("ellipse", { cx: x, cy: y, rx, ry, fill: TH.a, stroke: TH.fg, "stroke-width": 3 }, g);
        const ring = sv("ellipse", { cx: x, cy: y, rx: rx + 6, ry: ry + 6, fill: "none", stroke: TH.a, "stroke-width": 4 }, g);
        tl.fromTo(e, { scale: 0, svgOrigin: `${x} ${y}` }, { scale: 1, svgOrigin: `${x} ${y}`, duration: 0.4, ease: "back.out(2.5)" }, t);
        tl.fromTo(ring, { scale: 1, opacity: 1, svgOrigin: `${x} ${y}` }, { scale: 2.0, opacity: 0, svgOrigin: `${x} ${y}`, duration: 0.8, ease: "power2.out", repeat: 3, repeatDelay: 0.15 }, t + 0.2);
      });
      // callout: line from the right-hand spot to a label box
      const si = FULL && spt.side === "l" ? 0 : 1;
      const [sx0, sy0] = SPOTS[spt.part][si];
      const ax0 = fx + sx0 * sc + (si ? 16 : -16), ay0 = fy + sy0 * sc;
      const lx = FULL ? (spt.side === "l" ? CB.x : fx + fw + 90) : fx + fw + 30;
      const lw = FULL ? (spt.side === "l" ? 860 : CB.x + CB.w - lx) : CB.x + CB.w - lx;
      const ly = spt.ly !== undefined ? CB.y + F(spt.ly, spt.lyp !== undefined ? spt.lyp : spt.ly * 0.8) : ay0 - F(60, 50);
      const ln = sv("svg", { width: W, height: H }, world); Object.assign(ln.style, abs(0, 0));
      const ex1 = FULL && spt.side === "l" ? lx + lw : lx - 14;
      sv("path", { d: `M${ax0} ${ay0} L${(ax0 + ex1) / 2} ${ly + F(30, 22)} L${ex1} ${ly + F(30, 22)}`, stroke: TH.fg, "stroke-width": 3, fill: "none" }, ln);
      sv("circle", { cx: ax0, cy: ay0, r: 6, fill: TH.fg }, ln);
      const box = el("div", "", world, Object.assign(abs(lx, ly, lw), { textAlign: FULL && spt.side === "l" ? "right" : "left" }));
      box.style.fontSize = fs(84, 40); el("div", "disp", box, { fontSize: "1em", color: TH.a, lineHeight: 0.95 }, rich(spt.label));
      if (spt.note) el("div", "uim", box, { fontSize: "0.45em", color: TH.fg, marginTop: F(10, 6) + "px", lineHeight: 1.15 }, rich(spt.note));
      if (spt.mono) el("div", "mono", box, { fontSize: "0.27em", color: TH.mut, marginTop: F(10, 6) + "px", lineHeight: 1.3 }, spt.mono);
      fit(box, lw, F(300, 220), 12);
      ex(ln); ex(box);
      draw(ln.querySelector("path"), t + 0.2, 0.4, 0);
      fin(box, t + 0.45, { x: FULL && spt.side === "l" ? -20 : 20, y: 0 });
      markIn(box, t + 0.8);
    });
    if (D.sub) subline(D.sub, CB.x, FULL ? CB.y + CB.h - 120 : CB.y + CB.h - 70, FULL ? 860 : CB.w, { t: 2.6, f: 30, fp: 20, h: F(120, 80) });
  };

  // ---------------------------------------------------------------- isometric route map of a training day
  R.map = function () {
    if (D.title) title(D.title, { f: 60, fp: 40, h: F(120, 96) });
    const stops = D.stops, n = stops.length;
    // iso projection of a plane: (u,v) in [0,1] -> screen
    const ox = FULL ? CB.x + 180 : CB.x + 40, oy = FULL ? CB.y + 520 : CB.y + 470;
    const U = FULL ? [1400, -250] : [620, -180], V = FULL ? [190, 140] : [90, 130];
    const P = (u, v) => [ox + U[0] * u + V[0] * v, oy + U[1] * u + V[1] * v];
    const svg = sv("svg", { width: W, height: H }, world); Object.assign(svg.style, abs(0, 0)); ex(svg);
    // plane + grid
    const c = [P(-0.04, -0.6), P(1.04, -0.6), P(1.04, 1.0), P(-0.04, 1.0)];
    const plane = sv("polygon", { points: c.map(p => p.join(",")).join(" "), fill: TH.soft, stroke: "none" }, svg);
    const grid = sv("g", { stroke: TH.fg, "stroke-width": 1.2, opacity: 0.22 }, svg);
    for (let i = 0; i <= 12; i++) { const a = P(-0.04 + i * 1.08 / 12, -0.6), b = P(-0.04 + i * 1.08 / 12, 1.0); sv("line", { x1: a[0], y1: a[1], x2: b[0], y2: b[1] }, grid); }
    for (let j = 0; j <= 8; j++) { const a = P(-0.04, -0.6 + j * 1.6 / 8), b = P(1.04, -0.6 + j * 1.6 / 8); sv("line", { x1: a[0], y1: a[1], x2: b[0], y2: b[1] }, grid); }
    tl.fromTo([plane, grid], { opacity: 0 }, { opacity: (i) => i ? 0.22 : 1, duration: 0.5 }, T0 + 0.1);
    const pts = stops.map(s => P(s.u, s.v));
    // route path with 2 control-ish bends
    let d = `M${pts[0][0]} ${pts[0][1]}`;
    for (let i = 1; i < n; i++) { const a = pts[i - 1], b = pts[i]; const mx = (a[0] + b[0]) / 2, my = (a[1] + b[1]) / 2 + (i % 2 ? -F(50, 30) : F(40, 24)); d += ` Q${mx} ${my} ${b[0]} ${b[1]}`; }
    const route = sv("path", { d, stroke: TH.a, "stroke-width": F(12, 8), fill: "none", "stroke-linecap": "round", "stroke-dasharray": "1" }, svg);
    route.setAttribute("pathLength", "1");
    const segT = 0.55;
    const t0 = T0 + 0.5;
    tl.fromTo(route, { strokeDashoffset: 1 }, { strokeDashoffset: 0, duration: segT * (n - 1), ease: "none" }, t0 + 0.3);
    // moving dot
    const dot = sv("circle", { r: F(16, 11), fill: TH.fg, stroke: TH.bg, "stroke-width": 4 }, svg);
    const prog = { p: 0 };
    const L = route.getTotalLength ? null : null;
    const upd = () => { const len = route.getTotalLength(); const pt = route.getPointAtLength(len * prog.p); dot.setAttribute("cx", pt.x); dot.setAttribute("cy", pt.y); };
    upd();
    tl.fromTo(prog, { p: 0 }, { p: 1, duration: segT * (n - 1), ease: "none", onUpdate: upd }, t0 + 0.3);
    tl.fromTo(dot, { opacity: 0 }, { opacity: 1, duration: 0.1 }, t0 + 0.3);
    stops.forEach((s, i) => {
      const [x, y] = pts[i];
      const t = t0 + 0.3 + segT * i;
      const pinH = F(s.h || 120, s.hp || 90);
      const stem = el("div", "", world, Object.assign(abs(x - 2, y - pinH, 4, pinH), { background: TH.fg, transformOrigin: "50% 100%" }));
      const base = sv("ellipse", { cx: x, cy: y, rx: F(22, 16), ry: F(11, 8), fill: s.hot ? TH.a : TH.fg }, svg);
      const cw = F(s.w || 300, s.wp || 200);
      const al = s.al || "c";
      const card = el("div", "card shadow", world, Object.assign(abs(al === "l" ? x - F(20, 14) : al === "r" ? x - cw + F(20, 14) : x - cw / 2, y - pinH - F(s.ch || 118, s.chp || 92), cw), { boxSizing: "border-box", padding: F(14, 10) + "px " + F(18, 12) + "px", background: s.hot ? TH.a : TH.card, color: s.hot ? "#0D0D0D" : TH.fg, display: "flex", gap: F(14, 10) + "px", alignItems: "center", borderColor: s.hot ? TH.a : TH.fg }));
      if (s.icon) { const iw = el("div", "", card, { width: F(56, 40) + "px", height: F(56, 40) + "px", flex: "0 0 auto" }); icon(s.icon, F(56, 40), iw, null, 3); }
      const tx = el("div", "", card, { minWidth: 0 });
      const tt = el("div", "disp", tx, { fontSize: fs(34, 23), lineHeight: 0.95 }, rich(s.t));
      if (s.d) el("div", "mono", tx, { fontSize: fs(17, 12), marginTop: "5px", color: s.hot ? "#0D0D0D" : TH.mut, lineHeight: 1.2 }, s.d);
      [stem, card].forEach(ex);
      tl.fromTo(base, { scale: 0, svgOrigin: `${x} ${y}` }, { scale: 1, svgOrigin: `${x} ${y}`, duration: 0.3, ease: E_BACK }, t - 0.05);
      tl.fromTo(stem, { scaleY: 0 }, { scaleY: 1, duration: 0.28, ease: E_IN }, t);
      tl.fromTo(card, { opacity: 0, y: F(30, 20), rotationX: -70, transformOrigin: "50% 100%" }, { opacity: 1, y: 0, rotationX: 0, duration: 0.45, ease: E_BACK }, t + 0.12);
    });
    (D.legs || []).forEach((lg, i) => {
      const a = pts[i], b = pts[i + 1];
      const mx = (a[0] + b[0]) / 2, my = (a[1] + b[1]) / 2 + (i % 2 ? -F(25, 15) : F(20, 12)) + F(lg.dy || 46, lg.dyp || 34);
      const p = el("div", "mono pill", world, Object.assign(abs(mx - F(110, 80), my), { fontSize: fs(19, 13), color: TH.fg, background: TH.bg, whiteSpace: "nowrap" }), lg.t);
      ex(p); pop(p, t0 + 0.3 + segT * (i + 0.5), { s: 0.5, d: 0.3 });
    });
    tl.fromTo(world, { rotationX: 14, z: -80 }, { rotationX: 2, z: 0, duration: 1.6, ease: E_IN }, 0);
    if (D.sub) subline(D.sub, CB.x, CB.y + CB.h - F(50, 44), CB.w, { t: t0 + segT * n + 0.3, f: 30, fp: 20 });
  };

  // ---------------------------------------------------------------- research note (document card on the grid)
  R.research = function () {
    const cw = FULL ? 1580 : CB.w, chh = FULL ? 700 : CB.h + 20;
    const cx = FULL ? (W - cw) / 2 : CB.x, cy = FULL ? 146 : CB.y - 10;
    const card = el("div", "", world, Object.assign(abs(cx, cy, cw, chh), { background: "#EFEBE3", color: "#0D0D0D", boxSizing: "border-box", border: "4px solid #0D0D0D", boxShadow: `${F(22, 14)}px ${F(22, 14)}px 0 rgba(0,0,0,.35)`, transformOrigin: "50% 60%" }));
    ex(card);
    const pad = F(48, 26);
    // left accent strip + header
    el("div", "", card, Object.assign(abs(0, 0, F(18, 12), chh - 8), { background: "#FF5A1F" }));
    const hd = el("div", "", card, Object.assign(abs(pad + F(18, 12), pad - F(8, 6), cw - pad * 2 - F(18, 12)), { display: "flex", alignItems: "center", gap: F(16, 10) + "px" }));
    const ic = el("div", "", hd, { width: F(46, 34) + "px", height: F(46, 34) + "px", color: "#FF5A1F" }); const ics = icon(D.icon || "flask", F(46, 34), ic, null, 3.2);
    el("div", "mono", hd, { fontSize: fs(24, 17), color: "#0D0D0D", letterSpacing: ".14em" }, D.label || "THE SCIENCE");
    el("div", "", hd, { flex: 1, height: "3px", background: "#0D0D0D" });
    el("div", "mono", hd, { fontSize: fs(18, 13), color: "#6f695f" }, D.ref || "RESEARCH NOTE");
    const inner = el("div", "", card, Object.assign(abs(pad + F(18, 12), pad + F(70, 52), cw - pad * 2 - F(18, 12), chh - pad * 2 - F(70, 52) - F(70, 60)), { display: "flex", gap: F(22, 16) + "px", flexDirection: "column" }));
    let statBox = null, big = null;
    if (D.stat) {
      statBox = el("div", "", inner, { flex: "0 0 auto", display: "flex", flexDirection: FULL ? "row" : "column", alignItems: FULL ? "flex-end" : "flex-start", gap: F(40, 4) + "px" });
      const br = el("div", "", statBox, { display: "flex", alignItems: "flex-end", gap: F(14, 10) + "px" });
      big = roller(br, D.stat.num, { size: F(D.stat.size || 168, D.stat.sizeP || 150), color: "#FF5A1F", extC: "#A8380F", seed: 5 });
      if (D.stat.unit) el("div", "disp", br, { fontSize: fs(D.stat.unitSize || 80, 50), paddingBottom: F(16, 10) + "px", color: "#0D0D0D", whiteSpace: "nowrap" }, D.stat.unit);
      if (D.stat.cap) el("div", "mono", statBox, { fontSize: fs(24, 16), color: "#6f695f", marginBottom: F(26, 0) + "px", lineHeight: 1.3, maxWidth: F(420, 600) + "px" }, D.stat.cap);
      let g = 0; const maxW = FULL ? 980 : cw - pad * 2 - 20;
      br.style.width = "max-content";
      while (contentW(br) > maxW && g++ < 30) big._scale(0.95);
    }
    const txt = el("div", "", inner, { flex: 1, minWidth: 0, display: "flex", flexDirection: "column", gap: F(18, 10) + "px" });
    txt.style.setProperty("--hl", "#FFD84D"); txt.style.setProperty("--hlfg", "#0D0D0D"); txt.style.setProperty("--fg", "#0D0D0D");
    const claim = el("div", "disp", txt, { fontSize: fs(D.cf || 60, D.cfp || 50), lineHeight: 1.0, color: "#0D0D0D" }, rich(D.claim));
    const pts = (D.points || []).map(p => { const r = el("div", "", txt, { display: "flex", gap: F(14, 10) + "px", alignItems: "flex-start" }); el("div", "", r, { width: F(12, 9) + "px", height: F(12, 9) + "px", background: "#FF5A1F", marginTop: F(15, 10) + "px", flex: "0 0 auto" }); el("div", "uim", r, { fontSize: fs(34, 28), lineHeight: 1.18, color: "#2a2723" }, rich(p)); return r; });
    // fit text block
    const availH = parseFloat(inner.style.height) - (statBox ? statBox.offsetHeight + F(22, 16) : 0);
    let g = 0;
    while (txt.scrollHeight > availH + 2 && g++ < 40) { claim.style.fontSize = parseFloat(getComputedStyle(claim).fontSize) * 0.95 + "px"; txt.querySelectorAll(".uim").forEach(u => u.style.fontSize = parseFloat(getComputedStyle(u).fontSize) * 0.95 + "px"); }
    // source footer
    const ft = el("div", "", card, Object.assign(abs(pad + F(18, 12), chh - pad - F(30, 26), cw - pad * 2 - F(18, 12)), { borderTop: "3px solid #0D0D0D", paddingTop: F(14, 10) + "px" }));
    const src = el("div", "monor", ft, { fontSize: fs(20, 13), color: "#0D0D0D", letterSpacing: ".03em", lineHeight: 1.25 }, "SOURCE: " + D.source);
    fit(src, cw - pad * 2 - F(18, 12), F(56, 40), 10);
    // motion: card drops onto the grid in 3D, then a slow camera push
    tl.fromTo(card, { opacity: 0, rotationX: 38, rotationZ: -6, y: F(140, 90), z: -200 }, { opacity: 1, rotationX: 7, rotationZ: -1.2, y: 0, z: 0, duration: 0.7, ease: E_IN }, T0);
    draw(ics, T0 + 0.35, 0.5);
    if (big) big._anim(T0 + 0.45, 1.1);
    wipe(claim, T0 + 0.45, { d: 0.5 });
    markIn(claim, T0 + 1.1);
    pts.forEach((p, i) => fin(p, T0 + 0.9 + i * 0.18, { x: -16, y: 0 }));
    markIn(txt, T0 + 1.6);
    fin(ft, T0 + 1.2, { y: 10 });
  };

  // ---------------------------------------------------------------- plates (tilted pie plates with portion wedges)
  R.plate = function () {
    if (D.title) title(D.title, { f: 60, fp: 40, h: F(120, 96) });
    const plates = D.plates, n = plates.length;
    const colW = FULL ? (D.side ? CB.w - 600 : CB.w) / n : CB.w;
    plates.forEach((pl, k) => {
      const R0 = FULL ? (n > 1 ? 270 : 360) : (n > 1 ? 150 : 225);
      const cx = FULL ? CB.x + colW * k + colW / 2 : CB.x + (n > 1 ? (k ? CB.w * 0.73 : CB.w * 0.27) : CB.w / 2);
      const cy = FULL ? CB.y + 350 : CB.y + (n > 1 ? 290 : 280);
      const tilt = 0.56;
      const svg = sv("svg", { width: R0 * 2 + 80, height: R0 * 2 * tilt + 120 }, world); Object.assign(svg.style, abs(cx - R0 - 40, cy - R0 * tilt - 40));
      ex(svg);
      const g = sv("g", { transform: `translate(${R0 + 40} ${R0 * tilt + 40}) scale(1 ${tilt})` }, svg);
      sv("ellipse", { cx: 10, cy: 46, rx: R0 + 6, ry: R0 + 6, fill: "rgba(0,0,0,.25)" }, g);
      sv("circle", { cx: 0, cy: 22, r: R0, fill: TH.fg }, g);
      sv("circle", { cx: 0, cy: 0, r: R0, fill: S.bg === "ink" ? "#2a2a2a" : "#ffffff", stroke: TH.fg, "stroke-width": 5 }, g);
      sv("circle", { cx: 0, cy: 0, r: R0 * 0.8, fill: "none", stroke: TH.fg, "stroke-width": 2, opacity: 0.35 }, g);
      const rr = R0 * 0.38;
      let acc = 0;
      const COLS = { carbs: "#FFD84D", protein: "#FF5A1F", veg: "#1F6B45", fat: "#c9b28a", fruit: "#ff8a5c", dairy: "#ffffff" };
      pl.parts.forEach((pt, i) => {
        const frac = pt.f;
        const c = sv("circle", { cx: 0, cy: 0, r: rr, fill: "none", stroke: COLS[pt.type] || TH.a, "stroke-width": rr * 2, "stroke-dasharray": `${frac * 2 * Math.PI * rr} ${2 * Math.PI * rr}`, "stroke-dashoffset": 0, transform: `rotate(${-90 + acc * 360})` }, g);
        if (pt.dashed) { c.setAttribute("opacity", "0.55"); }
        const t = (pl.at || T0 + 0.5 + k * 1.2) + i * 0.3;
        const circ = 2 * Math.PI * rr;
        tl.fromTo(c, { attr: { "stroke-dasharray": `0 ${circ}` } }, { attr: { "stroke-dasharray": `${frac * circ} ${circ}` }, duration: 0.55, ease: "power3.out" }, t);
        // label
        const mid = (acc + frac / 2) * Math.PI * 2 - Math.PI / 2;
        const lx0 = cx + Math.cos(mid) * R0 * 0.55, ly0 = cy + Math.sin(mid) * R0 * 0.55 * tilt;
        const side = Math.cos(mid) >= 0 ? 1 : -1;
        const lx1 = cx + side * (R0 + F(40, 22)), ly1 = cy + Math.sin(mid) * (R0 * tilt + F(70, 50)) - F(20, 10);
        const ln = sv("svg", { width: W, height: H }, world); Object.assign(ln.style, abs(0, 0));
        sv("path", { d: `M${lx0} ${ly0} L${lx1} ${ly1} L${lx1 + side * F(30, 16)} ${ly1}`, stroke: TH.fg, "stroke-width": 3, fill: "none" }, ln);
        sv("circle", { cx: lx0, cy: ly0, r: 6, fill: TH.fg }, ln);
        const lw = F(pt.lw || 300, pt.lwp || 170);
        const lab = el("div", "", world, Object.assign(abs(side > 0 ? lx1 + F(38, 20) : lx1 - F(38, 20) - lw, ly1 - F(34, 22), lw), { textAlign: side > 0 ? "left" : "right" }));
        const nmx = el("div", "disp", lab, { fontSize: fs(54, 28), color: TH.fg, lineHeight: 0.95 }, rich(pt.label));
        if (pt.amt) el("div", "mono", lab, { fontSize: fs(26, 15), color: pt.type === "protein" ? TH.a : TH.mut, marginTop: "6px", lineHeight: 1.2 }, pt.amt);
        fit(lab, lw, F(140, 90), 11);
        ex(ln); ex(lab);
        draw(ln.querySelector("path"), t + 0.25, 0.3, 0);
        fin(lab, t + 0.35, { x: side * 14, y: 0 });
        acc += frac;
      });
      tl.fromTo(svg, { opacity: 0, y: F(80, 50), scale: 0.8 }, { opacity: 1, y: 0, scale: 1, duration: 0.6, ease: E_IN }, (pl.at || T0 + 0.2 + k * 1.2) - 0.25);

      const nm = el("div", "", world, Object.assign(abs(cx - F(300, 180), cy + R0 * tilt + F(70, 46), F(600, 360)), { textAlign: "center" }));
      el("div", "disp", nm, { fontSize: fs(44, 28), color: pl.hot ? TH.a : TH.fg }, rich(pl.name));
      if (pl.note) el("div", "uim", nm, { fontSize: fs(28, 18), color: TH.mut, marginTop: "6px", lineHeight: 1.15 }, rich(pl.note));
      fit(nm, F(600, 360), F(140, 90), 12);
      ex(nm); fin(nm, (pl.at || T0 + 0.2 + k * 1.2) + 0.2, { y: 14 });
    });
    if (n > 1) {
      const ar = el("div", "disp", world, Object.assign(abs(FULL ? CB.x + colW - 40 : CB.x + CB.w / 2 - 40, FULL ? CB.y + 300 : CB.y + 250, 80), { fontSize: fs(90, 60), color: TH.a, textAlign: "center" }), "→");
      ex(ar); pop(ar, T0 + 1.3, { s: 0.3 });
    }
    if (D.side && FULL) {
      const s = el("div", "", world, Object.assign(abs(CB.x + CB.w - 560, CB.y + 200, 560), {}));
      el("div", "disp", s, { fontSize: "48px", color: TH.fg, lineHeight: 0.98 }, rich(D.side.t));
      if (D.side.d) el("div", "uim", s, { fontSize: "30px", color: TH.mut, lineHeight: 1.2, marginTop: "16px" }, rich(D.side.d));
      fit(s, 560, 460, 14); ex(s); fin(s, D.side.at || 2.2, { x: 24, y: 0 }); markIn(s, (D.side.at || 2.2) + 0.4);
    }
    if (D.sub) subline(D.sub, CB.x, CB.y + CB.h - F(56, 50), CB.w, { t: D.subAt || 2.6, f: 30, fp: 20 });
  };

  // ================================================================== build
  function build() {
    header();
    (R[S.kind] || R.counter)();
    // ambient: slow push, grid parallax, grain flicker (seeded), fast out
    // STILL (Nizam 2026-11-09): no push / zoom / drift on graphics
    tl.set(grain, { backgroundPosition: `${Math.floor(rnd() * 512)}px ${Math.floor(rnd() * 512)}px` }, 0);
    tl.to(EX.slice().reverse(), { opacity: 0, y: -F(28, 18), duration: 0.2, ease: "power2.in", stagger: Math.min(0.018, 0.2 / Math.max(1, EX.length)) }, TE);
    tl.to({}, { duration: 0.001 }, DUR);
    window.__timelines["main"] = tl;
  }
  const fontsP = ['400 50px "Archivo Black"', '900 50px "Inter Tight"', '500 50px "Inter Tight"', 'italic 400 50px "Instrument Serif"', '700 50px "Space Mono"', '400 50px "Space Mono"'].map(f => document.fonts.load(f));
  Promise.all(fontsP).then(() => document.fonts.ready).then(build);
})();
