/* FUEL LAB — HyperFrames builders (one file, all kinds).
   scripts/gfx4.py injects window.GFX = {kind, dur, data} and copies fonts/, img/, grain.png, gsap.min.js next to it.
   Rules: one paused GSAP timeline, registered at the END of the async build; entrances = fromTo (immediateRender),
   exits = fromTo with immediateRender:false; no clocks, no unseeded random, no callbacks for visual state. */
(function () {
  "use strict";
  const G = window.GFX || {}; const D = G.data || {}; const DUR = +G.dur || 3; const FR = 1 / 30;
  const P = 2000; // stage perspective
  const C = { ink: "#0D0D0D", paper: "#EFEBE3", paper2: "#E2DDD2", accent: "#FF5A1F", hi: "#FFD84D", green: "#1F6B45",
              grid: "#2E8A5C", white: "#FFFFFF" };
  const app = document.getElementById("app");
  const tl = gsap.timeline({ paused: true });
  const SMALL = new Set(["a", "an", "the", "of", "to", "in", "on", "for", "and", "or", "is", "it", "its", "at", "by", "be",
                         "as", "so", "but", "with", "like", "your", "you", "my", "i", "we", "that", "this", "are", "was", "from", "vs"]);

  // ------------------------------------------------------------------ helpers
  function el(tag, cls, parent, text) {
    const e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text;
    if (parent) parent.appendChild(e); return e;
  }
  function css(e, o) { Object.assign(e.style, o); return e; }
  function px(v) { return Math.round(v) + "px"; }
  function norm(w) { return String(w).toLowerCase().replace(/[^a-z0-9%]/g, ""); }
  function accSet(a) { return new Set(String(a || "").split(/\s+/).map(norm).filter(Boolean)); }
  function pad2(n) { return String(n).padStart(2, "0"); }
  function rng(seed) { let a = seed >>> 0; return function () { a |= 0; a = (a + 0x6D2B79F5) | 0; let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }; }
  const meas = el("div", "", document.body); css(meas, { position: "absolute", left: "-9999px", top: "0", visibility: "hidden", whiteSpace: "pre" });
  function textW(text, cls, size, extra) {
    const s = el("span", cls, meas, text); css(s, Object.assign({ fontSize: size + "px", whiteSpace: "pre", display: "inline-block" }, extra || {}));
    const w = s.getBoundingClientRect().width; meas.removeChild(s); return w;
  }
  function boxW(e) { return e.getBoundingClientRect().width; }

  // tokens -> balanced lines at a fitted size
  function tokenize(text, opts) {
    opts = opts || {}; const acc = accSet(opts.accent);
    return String(text).replace(/->/g, "→").trim().split(/\s+/).filter(Boolean).map((t) => {
      const small = opts.smallSerif && SMALL.has(norm(t));
      const tk = { t: opts.upper === false ? t : (small ? t.toLowerCase() : t.toUpperCase()), cls: small ? "is" : (opts.cls || "ab"),
                   scale: small ? (opts.smallScale || 0.62) : 1, acc: acc.has(norm(t)), small };
      tk.w100 = textW(tk.t, tk.cls, 100 * tk.scale); tk.sp100 = textW(" ", opts.cls || "ab", 100) * (opts.spaceMul || 1);
      return tk;
    });
  }
  function lineW(line, s) { return line.reduce((a, tk, i) => a + tk.w100 * s / 100 + (i ? tk.sp100 * s / 100 : 0), 0); }
  function partitions(n, k) { // all ways to cut n tokens into k non-empty consecutive lines
    const out = []; (function rec(start, left, acc) { if (left === 1) { out.push(acc.concat([[start, n]])); return; }
      for (let e = start + 1; e <= n - left + 1; e++) rec(e, left - 1, acc.concat([[start, e]])); })(0, k, []); return out; }
  function layoutLines(tokens, maxW, maxLines, sMax, sMin, forced) {
    const n = tokens.length;
    if (forced) { // forced groups (array of token counts per line)
      let s = sMax; const lines = []; let i = 0; for (const c of forced) { lines.push(tokens.slice(i, i + c)); i += c; }
      while (s > sMin && Math.max(...lines.map((l) => lineW(l, s))) > maxW) s -= 2; return { size: s, lines };
    }
    for (let s = sMax; s >= sMin; s -= 2) {
      for (let k = 1; k <= Math.min(maxLines, n); k++) {
        let best = null, bestW = 1e9;
        for (const p of partitions(n, k)) {
          const lines = p.map(([a, b]) => tokens.slice(a, b)); const ws = lines.map((l) => lineW(l, s)); const mw = Math.max(...ws);
          const opStart = lines.slice(1).filter((l) => /^(=|\+|→|->|≠|\/|&|×|·)$/.test(l[0].t) || l[0].glue).length;
          if (mw <= maxW) { const score = mw + 0.15 * (Math.max(...ws) - Math.min(...ws)) + (lines[lines.length - 1].length === 1 && n > 3 ? 40 : 0) + opStart * 400;
            if (score < bestW) { bestW = score; best = lines; } }
        }
        if (best) return { size: s, lines: best };
      }
    }
    return { size: sMin, lines: [tokens] };
  }
  // render lines: each line = mask > line-in > word spans. returns {block, lines:[lineIn], words:[span]}
  function renderLines(parent, lay, opts) {
    opts = opts || {}; const block = el("div", "", parent); const lineEls = [], words = [];
    css(block, { position: "absolute", textAlign: opts.align || "left" });
    lay.lines.forEach((line) => {
      const m = el("div", "mask", block); const li = el("div", "line-in", m);
      css(li, { lineHeight: opts.lh || 0.9 });
      if (opts.align === "center") css(m, { textAlign: "center" });
      line.forEach((tk, i) => {
        const w = el("span", "w " + tk.cls, li, tk.t);
        css(w, { fontSize: px(lay.size * tk.scale), color: tk.acc ? (opts.accColor || C.accent) : (tk.small ? (opts.smallColor || opts.color) : opts.color),
                 marginLeft: i ? px(tk.sp100 * lay.size / 100) : "0px" });
        if (tk.small) css(w, { textTransform: "none", letterSpacing: "-0.01em" });
        if (tk.acc && opts.accSerif) css(w, { fontFamily: "IS", textTransform: "none", fontSize: px(lay.size * 1.12), letterSpacing: "-0.01em" });
        words.push(w);
      });
      lineEls.push(li);
    });
    return { block, lines: lineEls, words };
  }
  function layer(cam, z) { const l = el("div", "layer", cam); gsap.set(l, { z: z, scale: (P - z) / P }); return l; }
  function rig() { const stage = el("div", "stage", app); const cam = el("div", "cam", stage); return { stage, cam }; }
  function background(parent, v) {
    const b = el("div", "bg bg-" + v, parent); const g = el("div", "gridlines g-" + v, b);
    css(g, { backgroundPosition: "0px 0px" }); return b;
  }
  function grain(parent, op, dur) {
    if (!G.browser_grain) return null; // film grain is added at encode time (ffmpeg noise) - noisy PNGs are slow to capture
    const g = el("div", "grain", parent); g.style.opacity = op; const steps = Math.max(1, Math.floor((dur || DUR) * 15));
    tl.fromTo(g, { backgroundPosition: "0px 0px" }, { backgroundPosition: `${steps * 97}px ${steps * 61}px`, ease: `steps(${steps})`, duration: dur || DUR }, 0);
    return g;
  }
  function svg(parent, w, h, inner, style) {
    const d = el("div", "abs", parent); d.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}" viewBox="0 0 ${w} ${h}">${inner}</svg>`;
    css(d, Object.assign({ width: px(w), height: px(h) }, style || {})); return d;
  }
  function regMark(parent, x, y, color, op, size) {
    size = size || 34; const h = size / 2;
    return svg(parent, size, size, `<g fill="none" stroke="${color}" stroke-width="1.5"><circle cx="${h}" cy="${h}" r="${size * 0.24}"/>` +
      `<line x1="0" y1="${h}" x2="${size}" y2="${h}"/><line x1="${h}" y1="0" x2="${h}" y2="${size}"/></g>`,
      { left: px(x - h), top: px(y - h), opacity: op });
  }
  function regMarks(parent, color, op) { return [[48, 48], [1872, 48], [48, 1032], [1872, 1032]].map(([x, y]) => regMark(parent, x, y, color, op)); }
  function edgeTicks(parent, color, op) {
    let s = "";
    for (let y = 120; y <= 960; y += 60) { const L = y % 240 === 0 ? 16 : 8; s += `<line x1="0" y1="${y}" x2="${L}" y2="${y}"/><line x1="${1920 - L}" y1="${y}" x2="1920" y2="${y}"/>`; }
    for (let x = 120; x <= 1800; x += 60) { const L = x % 240 === 0 ? 14 : 7; s += `<line x1="${x}" y1="0" x2="${x}" y2="${L}"/>`; }
    return svg(parent, 1920, 1080, `<g stroke="${color}" stroke-width="1.5">${s}</g>`, { left: "0px", top: "0px", opacity: op });
  }
  function typeIn(container, text, at, per) {
    container.textContent = ""; const spans = [...String(text)].map((ch) => el("span", "", container, ch));
    tl.fromTo(spans, { opacity: 0 }, { opacity: 1, duration: 0.001, stagger: per || 0.012, ease: "none" }, at); return spans;
  }
  function typeOut(spans, at, per) { tl.fromTo(spans, { opacity: 1 }, { opacity: 0, duration: 0.001, stagger: { each: per || 0.004, from: "end" }, ease: "none", immediateRender: false }, at); }
  function polaroid(parent, src, x, y, w, h, rot, cap) {
    const p = el("div", "polaroid", parent); css(p, { left: px(x), top: px(y), width: px(w), height: px(h) });
    const ph = el("div", "ph", p); if (src) ph.style.backgroundImage = `url(${src})`; else ph.style.background = C.paper2;
    if (cap) el("div", "cap", p, cap); gsap.set(p, { rotation: rot || 0 }); return p;
  }
  function chip(parent, text, bg, fg, size, padY, padX, cls) {
    const c = el("div", "chip " + (cls || "sm"), parent, text);
    css(c, { background: bg, color: fg, fontSize: px(size || 20), padding: `${padY == null ? 7 : padY}px ${padX == null ? 14 : padX}px`, lineHeight: 1 });
    return c;
  }
  function theme(v) {
    if (v === "green") return { fg: C.white, meta: C.paper, dim: "rgba(239,235,227,.86)", acc: C.hi, outline: "rgba(239,235,227,.24)",
      tickOn: C.hi, tickOff: "rgba(239,235,227,.26)", chipBg: C.hi, chipFg: C.ink, rule: "rgba(239,235,227,.55)", reg: C.paper, grain: 0.55 };
    if (v === "paper") return { fg: C.ink, meta: C.ink, dim: "rgba(13,13,13,.78)", acc: C.accent, outline: "rgba(13,13,13,.16)",
      tickOn: C.accent, tickOff: "rgba(13,13,13,.18)", chipBg: C.accent, chipFg: C.ink, rule: "rgba(13,13,13,.45)", reg: C.ink, grain: 0.75 };
    return { fg: C.white, meta: C.paper, dim: "rgba(239,235,227,.82)", acc: C.accent, outline: "rgba(255,255,255,.13)",
      tickOn: C.accent, tickOff: "rgba(255,255,255,.22)", chipBg: C.accent, chipFg: C.ink, rule: "rgba(239,235,227,.45)", reg: C.paper, grain: 0.7 };
  }
  function img(p) { return p ? "img/" + p.split(/[\\/]/).pop() : null; }

  // ------------------------------------------------------------------ CHAPTER CARD (opaque, 3.0 s)
  function buildChapter() {
    document.body.classList.add("opaque");
    const v = D.bg || (D.n % 2 ? "green" : "paper"); const T = theme(v);
    const { cam } = rig();
    const Lbg = layer(cam, -900), Lnum = layer(cam, -460), Lph = layer(cam, -170), Ltx = layer(cam, 0);
    background(Lbg, v); el("div", "vignette" + (v === "paper" ? " soft" : ""), app);
    const hud = el("div", "hud", app);
    const photo = img(D.photo); const maxW = photo ? 1150 : 1560;

    // giant outlined index number (deep layer, slow parallax)
    const num = el("div", "outline-num abs", Lnum, pad2(D.n));
    css(num, { fontSize: "960px", right: "-30px", top: "70px", WebkitTextStroke: `3px ${T.outline}` });

    // photo stack (mid layer)
    let cards = [];
    if (photo) {
      const ghost = polaroid(Lph, null, 1262, 300, 520, 440, -6); css(ghost, { background: v === "paper" ? "#DCD6CA" : "#E9E5DC" });
      const card = polaroid(Lph, photo, 1290, 280, 520, 440, 4.5, D.photo_label || D.topic || ("FIG. " + pad2(D.n)));
      cards = [ghost, card];
    }
    // title + kicker
    const toks = tokenize(D.title || "CHAPTER TITLE", { accent: D.accent_word });
    const lay = layoutLines(toks, maxW, 3, 196, 92);
    const R = renderLines(Ltx, lay, { color: T.fg, accColor: T.acc });
    const titleH = lay.lines.length * lay.size * 0.9;
    let kick = null, kickH = 0, bar = null;
    if (D.kicker) {
      kick = el("div", "is abs", Ltx, D.kicker); css(kick, { fontSize: "66px", lineHeight: 1.04, color: T.dim, maxWidth: px(Math.min(maxW, 1150)), left: "96px" });
      kickH = kick.getBoundingClientRect().height + 54;
    }
    const top = Math.round(540 - (titleH + kickH) / 2 - 10);
    css(R.block, { left: "96px", top: px(top) });
    if (kick) {
      bar = el("div", "abs", Ltx); css(bar, { left: "100px", top: px(top + titleH + 22), width: "64px", height: "6px", background: T.acc, transformOrigin: "0 50%" });
      css(kick, { top: px(top + titleH + 44) });
    }
    // HUD rows
    const lab = el("div", "sm abs", hud); css(lab, { left: "96px", top: "50px", fontSize: "22px", color: T.meta, whiteSpace: "pre" });
    const labSpans = typeIn(lab, `CHAPTER ${pad2(D.n)} / ${pad2(D.total || 13)}`, 0.03, 0.014);
    const right = el("div", "abs", hud); css(right, { right: "96px", top: "44px", display: "flex", alignItems: "center", gap: "18px" });
    let topicChip = null; if (D.topic) topicChip = chip(right, D.topic, T.chipBg, T.chipFg, 18, 8, 13);
    const tc = el("div", "smr", right, D.tc ? "TC " + D.tc : "FUEL LAB · EP." + (D.ep || "01")); css(tc, { fontSize: "18px", color: T.meta, opacity: 0.85 });
    const rw = boxW(right); const lw = boxW(lab) || 330;
    const rule = el("div", "rule", hud); css(rule, { left: px(96 + Math.max(lw, 300) + 28), top: "62px", width: px(1824 - rw - 28 - (96 + Math.max(lw, 300) + 28)), background: T.rule });
    const foot = el("div", "smr abs", hud, D.footer || "FUEL LAB — NIZAM × CARRIE MULLIN INNES"); css(foot, { left: "96px", top: "1006px", fontSize: "16px", color: T.meta, opacity: 0.62 });
    const ticks = el("div", "abs", hud); css(ticks, { right: "96px", top: "1009px", display: "flex", gap: "6px", alignItems: "flex-end" });
    const total = D.total || 13; const tickEls = [];
    for (let i = 1; i <= total; i++) { const t = el("div", "", ticks); css(t, { width: "34px", height: i === D.n ? "14px" : "6px", background: i <= D.n ? T.tickOn : T.tickOff, transformOrigin: "50% 100%" }); tickEls.push(t); }
    const regs = regMarks(hud, T.reg, 0.5); const edges = edgeTicks(hud, T.reg, 0.32);
    grain(app, T.grain);

    // ---- motion
    tl.set(cam, { rotationY: 0, rotationX: 0, z: 0, x: 0 }, 0); // STILL: no camera move (Nizam 2026-11-09)
    tl.fromTo(rule, { scaleX: 0 }, { scaleX: 1, duration: 0.45, ease: "expo.out" }, 0.02);
    tl.fromTo([...regs, edges], { opacity: 0 }, { opacity: (i) => (i < 4 ? 0.5 : 0.32), duration: 0.2, stagger: 0.02 }, 0.02);
    tl.fromTo(num, { x: 280, opacity: 0, filter: "blur(22px)" }, { x: 0, opacity: 1, filter: "blur(0px)", duration: 0.55, ease: "expo.out" }, 0.03);
    tl.fromTo(R.lines, { yPercent: 108 }, { yPercent: 0, duration: 0.5, ease: "expo.out", stagger: 0.07 }, 0.1);
    if (cards.length) {
      tl.fromTo(cards[0], { y: -90, rotation: -14, opacity: 0 }, { y: 0, rotation: -6, opacity: 1, duration: 0.5, ease: "back.out(1.3)" }, 0.2);
      tl.fromTo(cards[1], { y: -140, rotation: 15, scale: 1.12, opacity: 0 }, { y: 0, rotation: 4.5, scale: 1, opacity: 1, duration: 0.55, ease: "back.out(1.25)" }, 0.27);
    }
    if (bar) tl.fromTo(bar, { scaleX: 0 }, { scaleX: 1, duration: 0.35, ease: "expo.out" }, 0.3);
    if (kick) tl.fromTo(kick, { opacity: 0, x: -24, filter: "blur(10px)" }, { opacity: 1, x: 0, filter: "blur(0px)", duration: 0.45, ease: "power3.out" }, 0.34);
    if (topicChip) tl.fromTo(topicChip, { clipPath: "inset(0% 100% 0% 0%)" }, { clipPath: "inset(0% 0% 0% 0%)", duration: 0.3, ease: "expo.out" }, 0.28);
    tl.fromTo(tc, { opacity: 0 }, { opacity: 0.85, duration: 0.2 }, 0.36);
    tl.fromTo(foot, { opacity: 0, y: 8 }, { opacity: 0.62, y: 0, duration: 0.3, ease: "power2.out" }, 0.4);
    tl.fromTo(tickEls, { scaleY: 0 }, { scaleY: 1, duration: 0.18, ease: "back.out(2)", stagger: 0.018 }, 0.38);
    // exit: last 6-7 frames are already clearing, everything gone 1 frame before the end
    const X = DUR - 0.23;
    tl.fromTo(R.lines, { yPercent: 0 }, { yPercent: -110, duration: 0.14, ease: "power3.in", stagger: 0.015, immediateRender: false }, X);
    if (kick) tl.fromTo(kick, { opacity: 1 }, { opacity: 0, y: -16, duration: 0.12, ease: "power2.in", immediateRender: false }, X);
    if (bar) tl.fromTo(bar, { scaleX: 1 }, { scaleX: 0, duration: 0.1, ease: "power2.in", immediateRender: false }, X);
    if (cards.length) tl.fromTo(cards, { opacity: 1 }, { opacity: 0, y: "-=90", rotation: "+=6", duration: 0.15, ease: "power2.in", stagger: 0.02, immediateRender: false }, X);
    tl.fromTo(num, { opacity: 1 }, { opacity: 0, x: -140, duration: 0.17, ease: "power2.in", immediateRender: false }, X);
    tl.fromTo([lab, right, foot, ticks], { opacity: 1 }, { opacity: 0, duration: 0.12, immediateRender: false }, X + 0.03);
    tl.fromTo(rule, { scaleX: 1 }, { scaleX: 0, transformOrigin: "100% 50%", duration: 0.15, ease: "power3.in", immediateRender: false }, X);
  }

  // ------------------------------------------------------------------ CHAPTER TAG (alpha, 4.0 s) top-left
  function buildTag() {
    const g = el("div", "abs", app); css(g, { left: "96px", top: "64px", display: "flex", alignItems: "stretch", height: "54px" });
    const c = el("div", "chip sm", g, pad2(D.n)); css(c, { width: "62px", background: C.accent, color: C.ink, fontSize: "24px", letterSpacing: "0.04em" });
    const bar = el("div", "", g); css(bar, { background: "rgba(13,13,13,.88)", display: "flex", alignItems: "center", padding: "0 22px 0 18px", gap: "14px" });
    const dash = el("div", "", bar); css(dash, { width: "18px", height: "3px", background: C.accent });
    const tx = el("div", "ith", bar); css(tx, { fontSize: "25px", color: C.paper, letterSpacing: "0.05em", textTransform: "uppercase", whiteSpace: "pre", lineHeight: 1 });
    const text = String(D.title || "").toUpperCase(); const per = Math.min(0.02, 0.55 / Math.max(1, text.length));
    const sp = typeIn(tx, text, 0.2, per);
    tl.fromTo(c, { scale: 0, rotation: -90 }, { scale: 1, rotation: 0, duration: 0.3, ease: "back.out(1.8)" }, 0.0);
    tl.fromTo(bar, { clipPath: "inset(0% 100% 0% 0%)" }, { clipPath: "inset(0% 0% 0% 0%)", duration: 0.4, ease: "expo.out" }, 0.1);
    tl.fromTo(dash, { scaleX: 0 }, { scaleX: 1, transformOrigin: "0 50%", duration: 0.25, ease: "expo.out" }, 0.18);
    const X = DUR - 0.42;
    typeOut(sp, X, 0.12 / Math.max(1, text.length));
    tl.fromTo(bar, { clipPath: "inset(0% 0% 0% 0%)" }, { clipPath: "inset(0% 100% 0% 0%)", duration: 0.24, ease: "power3.in", immediateRender: false }, X + 0.08);
    tl.fromTo(c, { scale: 1 }, { scale: 0, rotation: 90, duration: 0.18, ease: "back.in(1.6)", immediateRender: false }, X + 0.22);
  }

  // ------------------------------------------------------------------ LOWER THIRD (alpha, 4.5 s) bottom-left, above caption zone
  function buildLT() {
    const g = el("div", "abs", app); css(g, { left: "96px", bottom: px(1080 - 832), display: "flex", flexDirection: "column", alignItems: "flex-start" });
    const row = el("div", "", g); css(row, { display: "flex", gap: "8px", marginBottom: "10px", alignItems: "center" });
    const c1 = chip(row, D.label || "GUEST", C.accent, C.ink, 19, 7, 12);
    const c2 = chip(row, D.idx || "01", "rgba(13,13,13,.88)", C.paper, 19, 7, 10, "smr");
    const nameS = el("div", "", g); css(nameS, { position: "relative", background: C.paper, padding: "20px 30px 12px 34px" });
    const edge = el("div", "abs", nameS); css(edge, { left: "0px", top: "0px", width: "8px", height: "100%", background: C.accent, transformOrigin: "50% 0%" });
    const nm = el("div", "mask", nameS); const nmi = el("div", "line-in ab", nm, String(D.name || "NAME").toUpperCase());
    css(nmi, { fontSize: px(D.name_size || 62), color: C.ink, lineHeight: 0.92 });
    const roleS = el("div", "", g); css(roleS, { background: "rgba(13,13,13,.92)", padding: "13px 30px 14px 34px" });
    const role = el("div", "itm", roleS); css(role, { fontSize: "29px", color: C.paper, whiteSpace: "pre", lineHeight: 1.05 });
    const parts = String(D.role || "").split(/\s+/); const rws = [];
    parts.forEach((p, i) => { const s = el("span", "", role, (i ? " " : "") + p); if (p === "·") s.style.color = C.accent; rws.push(s); });
    const reg = regMark(nameS, 0, 0, C.ink, 0.55, 22); css(reg, { left: "auto", right: "8px", top: "6px" });
    tl.fromTo([c1, c2], { scale: 0.4, opacity: 0 }, { scale: 1, opacity: 1, duration: 0.28, ease: "back.out(2)", stagger: 0.05 }, 0.0);
    tl.fromTo(nameS, { clipPath: "inset(0% 100% 0% 0%)" }, { clipPath: "inset(0% 0% 0% 0%)", duration: 0.42, ease: "expo.out" }, 0.08);
    tl.fromTo(edge, { scaleY: 0 }, { scaleY: 1, duration: 0.3, ease: "expo.out" }, 0.12);
    tl.fromTo(nmi, { yPercent: 105 }, { yPercent: 0, duration: 0.45, ease: "expo.out" }, 0.17);
    tl.fromTo(reg, { opacity: 0, rotation: -90 }, { opacity: 0.55, rotation: 0, duration: 0.35, ease: "expo.out" }, 0.3);
    tl.fromTo(roleS, { clipPath: "inset(0% 100% 0% 0%)" }, { clipPath: "inset(0% 0% 0% 0%)", duration: 0.42, ease: "expo.out" }, 0.28);
    tl.fromTo(rws, { opacity: 0, filter: "blur(6px)" }, { opacity: 1, filter: "blur(0px)", duration: 0.16, stagger: 0.045 }, 0.38);
    const X = DUR - 0.5;
    tl.fromTo(rws, { opacity: 1 }, { opacity: 0, duration: 0.08, stagger: { each: 0.01, from: "end" }, immediateRender: false }, X);
    tl.fromTo(nmi, { yPercent: 0 }, { yPercent: 105, duration: 0.2, ease: "power3.in", immediateRender: false }, X + 0.04);
    tl.fromTo(roleS, { clipPath: "inset(0% 0% 0% 0%)" }, { clipPath: "inset(0% 0% 0% 100%)", duration: 0.25, ease: "power3.in", immediateRender: false }, X + 0.1);
    tl.fromTo(nameS, { clipPath: "inset(0% 0% 0% 0%)" }, { clipPath: "inset(0% 0% 0% 100%)", duration: 0.25, ease: "power3.in", immediateRender: false }, X + 0.16);
    tl.fromTo([c1, c2], { scale: 1, opacity: 1 }, { scale: 0.4, opacity: 0, duration: 0.14, ease: "power2.in", stagger: 0.03, immediateRender: false }, X + 0.3);
  }

  // ------------------------------------------------------------------ HEADLINE (alpha) H3 label / H1 slab / H2 serif
  function buildHeadline() {
    const pos = D.pos || "tl"; const sty = D.style || "paper";
    const slabBg = sty === "ink" ? "rgba(13,13,13,.92)" : sty === "accent" ? C.accent : C.paper;
    const slabFg = sty === "ink" ? C.white : C.ink; const accC = sty === "accent" ? C.white : C.accent;
    const center = pos === "center";
    const g = el("div", "abs", app); css(g, { display: "flex", flexDirection: "column", alignItems: center ? "center" : "flex-start" });
    if (pos === "tl") css(g, { left: "96px", top: "96px" });
    else if (pos === "left") css(g, { left: "96px", top: "0px" });
    else if (pos === "bl") css(g, { left: "96px", bottom: px(1080 - 820) });
    else css(g, { left: "0px", width: "1920px", top: "0px" });
    let h3 = null; if (D.h3) { h3 = chip(g, D.h3, C.accent, C.ink, 22, 8, 14); css(h3, { marginBottom: "12px" }); }
    const toks = tokenize(D.h1 || "HEADLINE", { accent: D.accent_word });
    const lay = layoutLines(toks, D.max_w || 1100, 2, D.size || 104, 64);
    const slabs = [], ins = [];
    lay.lines.forEach((line) => {
      const s = el("div", "", g); css(s, { background: slabBg, padding: `${Math.round(lay.size * 0.14)}px ${Math.round(lay.size * 0.24)}px ${Math.round(lay.size * 0.06)}px` });
      const m = el("div", "mask", s); const li = el("div", "line-in", m); css(li, { lineHeight: 0.98 });
      line.forEach((tk, i) => { const w = el("span", "w " + tk.cls, li, tk.t); css(w, { fontSize: px(lay.size), color: tk.acc ? accC : slabFg, marginLeft: i ? px(tk.sp100 * lay.size / 100) : "0px" }); });
      slabs.push(s); ins.push(li);
    });
    let h2 = null, h2s = null;
    if (D.h2) { h2s = el("div", "", g); css(h2s, { background: "rgba(13,13,13,.78)", padding: "6px 20px 10px", marginTop: "10px" });
      h2 = el("div", "is", h2s, D.h2); css(h2, { fontSize: px(D.h2_size || 52), color: C.white, lineHeight: 1.05, whiteSpace: "pre" }); }
    if (pos === "left" || center) { const h = g.getBoundingClientRect().height; css(g, { top: px(Math.round((center ? 470 : 470) - h / 2)) }); }
    let t = 0;
    if (h3) { tl.fromTo(h3, { clipPath: "inset(0% 100% 0% 0%)" }, { clipPath: "inset(0% 0% 0% 0%)", duration: 0.25, ease: "expo.out" }, 0); t = 0.08; }
    const o = center ? "50% 50%" : "0% 50%";
    tl.fromTo(slabs, { clipPath: center ? "inset(0% 50% 0% 50%)" : "inset(0% 100% 0% 0%)" }, { clipPath: "inset(0% 0% 0% 0%)", duration: 0.4, ease: "expo.out", stagger: 0.07 }, t);
    tl.fromTo(ins, { yPercent: 110 }, { yPercent: 0, duration: 0.45, ease: "expo.out", stagger: 0.07 }, t + 0.08);
    if (h2s) { tl.fromTo(h2s, { clipPath: "inset(0% 100% 0% 0%)" }, { clipPath: "inset(0% 0% 0% 0%)", duration: 0.35, ease: "expo.out" }, t + 0.28);
      tl.fromTo(h2, { opacity: 0, filter: "blur(8px)" }, { opacity: 1, filter: "blur(0px)", duration: 0.3 }, t + 0.34); }
    const X = DUR - 0.45;
    tl.fromTo(ins, { yPercent: 0 }, { yPercent: -110, duration: 0.2, ease: "power3.in", stagger: 0.03, immediateRender: false }, X);
    if (h2) tl.fromTo(h2, { opacity: 1 }, { opacity: 0, duration: 0.12, immediateRender: false }, X);
    const all = [h3, ...slabs, h2s].filter(Boolean);
    tl.fromTo(all, { clipPath: "inset(0% 0% 0% 0%)" }, { clipPath: center ? "inset(0% 50% 0% 50%)" : "inset(0% 0% 0% 100%)", duration: 0.24, ease: "power3.in", stagger: 0.03, immediateRender: false }, X + 0.12);
  }

  // ------------------------------------------------------------------ HERO cards (opaque)
  function heroFrame(v) {
    document.body.classList.add("opaque"); const T = theme(v); const { cam } = rig();
    const Lbg = layer(cam, -700); background(Lbg, v); const Lmid = layer(cam, -260); const Ltx = layer(cam, 0);
    el("div", "vignette" + (v === "paper" ? " soft" : ""), app);
    const hud = el("div", "hud", app);
    const lab = el("div", "sm abs", hud); css(lab, { left: "96px", top: "52px", fontSize: "18px", color: T.meta, opacity: 0.8, whiteSpace: "pre" });
    const lsp = typeIn(lab, D.label_top || "FUEL LAB — " + (D.n ? "NOTE " + pad2(D.n) : "EP.01"), 0.02, 0.01);
    const regs = regMarks(hud, T.reg, 0.45); const edges = edgeTicks(hud, T.reg, 0.28);
    grain(app, T.grain);
    tl.set(cam, { z: 0, rotationY: 0, rotationX: 0 }, 0);
    tl.fromTo([...regs, edges], { opacity: 0 }, { opacity: (i) => (i < 4 ? 0.45 : 0.28), duration: 0.2 }, 0);
    const X = DUR - 0.17;
    tl.fromTo([lab, edges, ...regs], { opacity: (i) => (i === 0 ? 0.8 : i === 1 ? 0.28 : 0.45) }, { opacity: 0, duration: 0.1, immediateRender: false }, X);
    return { T, Ltx, Lmid, hud, X };
  }
  function exitGroup(targets, X) {
    tl.fromTo(targets, { opacity: 1 }, { opacity: 0, duration: 0.16, ease: "power2.in", immediateRender: false }, X);
  }
  function buildPunch() {
    const v = D.bg || "ink"; const { T, Ltx, Lmid, X } = heroFrame(v);
    const toks = tokenize(D.screen || "PUNCH LINE", { accent: D.accent_word });
    const lay = layoutLines(toks, 1560, 3, D.size || 168, 92);
    const R = renderLines(Ltx, lay, { color: T.fg, accColor: T.acc, align: "center", accSerif: D.accent_style === "serif" });
    const h = lay.lines.length * lay.size * 0.9; css(R.block, { left: "0px", width: "1920px", top: px(Math.round(530 - h / 2)) });
    R.lines.forEach((l) => css(l.parentNode, { textAlign: "center" }));
    // ghost echo of the accent word, huge + outlined, behind
    const accTok = toks.find((t) => t.acc);
    if (accTok) { const gh = el("div", "outline-num abs", Lmid, accTok.t); css(gh, { fontSize: "430px", left: "0px", width: "1920px", textAlign: "center", top: "300px", WebkitTextStroke: `2px ${T.outline}`, lineHeight: 0.8 });
      tl.fromTo(gh, { opacity: 0 }, { opacity: 1, duration: 0.4, ease: "power2.out" }, 0.1); }
    const ca = v === "paper" ? "none" : "-2px 0 rgba(255,40,70,.55), 2px 0 rgba(0,210,255,.45)";
    R.words.forEach((w, i) => {
      const at = 0.1 + i * (D.word_gap || 0.085);
      tl.fromTo(w, { opacity: 0, y: 24 }, { opacity: 1, y: 0, duration: 0.3, ease: "expo.out" }, at);
    });
    exitGroup(R.lines, X);
  }
  const UNITS = new Set(["KG", "G", "L", "ML", "MG", "IU", "MIN", "MINS", "HOUR", "HOURS", "HRS", "PM", "AM", "LITRE", "LITRES", "CUPS", "CUP", "K", "KCAL", "%"]);
  function buildNumber() {
    const v = D.bg || "green"; const { T, Ltx, X } = heroFrame(v);
    const numC = v === "paper" ? C.accent : C.hi;
    const filt = el("div", "abs", app); filt.innerHTML = '<svg width="0" height="0" style="position:absolute"><filter id="vb" x="-5%" y="-40%" width="110%" height="180%"><feGaussianBlur id="vbn" stdDeviation="0 0"/></filter></svg>';
    const raw = String(D.screen || "0").replace(/->/g, "→").trim().split(/\s+/);
    const toks = raw.map((t, i) => {
      const isNum = /\d/.test(t);
      const isUnit = !isNum && i > 0 && /\d/.test(raw[i - 1]) && UNITS.has(t.toUpperCase().replace(/[^A-Z%]/g, ""));
      const isOp = /^(=|→|\+|\/|≠|·|-|&)$/.test(t);
      const tk = { t: t.toUpperCase(), num: isNum, unit: isUnit, op: isOp, glue: isUnit, cls: isUnit ? "ith" : "ab",
                   scale: isNum ? 1 : isUnit ? 0.4 : isOp ? 0.5 : 0.52, acc: false, small: false };
      tk.w100 = textW(tk.t, tk.cls, 100 * tk.scale); tk.sp100 = textW(" ", "ab", 100) * (isUnit ? 0.45 : 0.62); return tk;
    });
    const nNum = toks.filter((t) => t.num).length;
    const lay = layoutLines(toks, 1640, 3, D.size || (nNum === 1 && toks.length <= 3 ? 400 : 280), 96);
    const LH = 0.98; const block = el("div", "", Ltx); css(block, { position: "absolute", left: "0px", width: "1920px", textAlign: "center" });
    const strips = [], plain = [], under = [];
    lay.lines.forEach((line) => {
      const li = el("div", "", block); css(li, { lineHeight: LH, whiteSpace: "nowrap" });
      line.forEach((tk, i) => {
        const fs = lay.size * tk.scale; const w = el("span", "w " + tk.cls, li, tk.t);
        css(w, { fontSize: px(fs), color: tk.num ? "transparent" : (tk.op ? numC : T.fg), marginLeft: i ? px(tk.sp100 * lay.size / 100) : "0px",
                 position: "relative", lineHeight: LH, verticalAlign: "baseline" });
        if (tk.unit) css(w, { letterSpacing: "0.02em" });
        if (!tk.num) { plain.push(w); return; }
        under.push(w);
        const ov = el("div", "abs", w); css(ov, { left: "0px", top: "0px", height: "100%", display: "flex", color: numC, filter: "url(#vb)" });
        [...tk.t].forEach((ch) => {
          const cw = textW(ch, "ab", fs); const col = el("div", "", ov); css(col, { width: px(cw), height: "100%", overflow: "hidden", position: "relative", clipPath: "inset(13% -10% 9% -10%)" });
          if (!/\d/.test(ch)) { const c = el("div", "", col, ch); css(c, { lineHeight: LH, textAlign: "center" }); return; }
          const d = +ch; const turns = Math.max(0, 2 - (strips.length % 3)); const strip = el("div", "", col); const cells = [];
          for (let r = 0; r <= turns; r++) for (let q = 0; q < 10; q++) { if (r === turns && q > d) break; cells.push(q); }
          cells.forEach((q) => { const c = el("div", "", strip, String(q)); css(c, { lineHeight: LH, textAlign: "center" }); });
          strips.push({ strip, n: cells.length - 1, col });
        });
      });
    });
    const bh = block.getBoundingClientRect().height; const btop = Math.round(520 - bh / 2); css(block, { top: px(btop) });
    strips.forEach((s) => { const h = s.col.getBoundingClientRect().height; s.h = h; [...s.strip.children].forEach((c) => css(c, { height: px(h), lineHeight: px(h) })); });
    // static chars inside number overlays: match the placeholder line box
    const kick = D.kicker ? el("div", "sm abs", Ltx, D.kicker) : null;
    if (kick) css(kick, { left: "0px", width: "1920px", textAlign: "center", top: px(btop - 54), fontSize: "22px", color: T.meta, opacity: 0.85 });
    const bars = under.slice(0, 1).map((w) => { const r = w.getBoundingClientRect(); const b = el("div", "abs", Ltx);
      css(b, { left: px(r.left), top: px(r.bottom - r.height * 0.04), width: px(r.width), height: "10px", background: numC, transformOrigin: "0 50%" }); return b; });
    const roll = D.roll || 0.85, rollEnd = 0.12 + roll;
    strips.forEach((s, i) => tl.fromTo(s.strip, { y: 0 }, { y: -s.n * s.h, duration: roll, ease: "power3.out" }, 0.12 + (i % 4) * 0.025));
    tl.fromTo("#vbn", { attr: { stdDeviation: "0 26" } }, { attr: { stdDeviation: "0 0" }, duration: roll * 0.9, ease: "power3.out" }, 0.12);
    tl.fromTo(under, { opacity: 0 }, { opacity: 1, duration: 0.05 }, 0.1);
    if (plain.length) tl.fromTo(plain, { opacity: 0, y: 26, filter: "blur(10px)" }, { opacity: 1, y: 0, filter: "blur(0px)", duration: 0.35, ease: "expo.out", stagger: 0.05 }, 0.3);
    tl.fromTo(bars, { scaleX: 0 }, { scaleX: 1, duration: 0.4, ease: "expo.out" }, rollEnd - 0.1);
    if (kick) tl.fromTo(kick, { opacity: 0 }, { opacity: 0.85, duration: 0.2 }, 0.05);
    exitGroup([block, ...bars, kick].filter(Boolean), X);
  }
  function R_center(R, top) { css(R.block, { left: "0px", width: "1920px", top: px(Math.round(top)) }); R.lines.forEach((l) => css(l.parentNode, { textAlign: "center" })); }
  function buildQuote() {
    const v = D.bg || "paper"; const { T, Ltx, Lmid, X } = heroFrame(v);
    const qm = el("div", "is abs", Lmid, "“"); css(qm, { fontSize: "520px", color: C.accent, left: "110px", top: "120px", lineHeight: 1 });
    const toks = tokenize(D.screen || "QUOTE", { accent: D.accent_word });
    const lay = layoutLines(toks, 1420, 3, D.size || 170, 80);
    const R = renderLines(Ltx, lay, { color: T.fg, accColor: C.accent, lh: 0.92 });
    const h = lay.lines.length * lay.size * 0.92; const top = Math.round(500 - h / 2); css(R.block, { left: "250px", top: px(top) });
    const rule = el("div", "abs", Ltx); css(rule, { left: "254px", top: px(top + h + 40), width: "80px", height: "5px", background: C.accent, transformOrigin: "0 50%" });
    const by = el("div", "sm abs", Ltx); css(by, { left: "254px", top: px(top + h + 64), fontSize: "22px", color: T.meta, opacity: 0.85, whiteSpace: "pre" });
    tl.fromTo(qm, { opacity: 0, y: 70, filter: "blur(18px)" }, { opacity: 1, y: 0, filter: "blur(0px)", duration: 0.6, ease: "expo.out" }, 0.0);
    const per = Math.min(0.08, 0.7 / R.words.length);
    tl.fromTo(R.words, { opacity: 0, y: 24, filter: "blur(12px)" }, { opacity: 1, y: 0, filter: "blur(0px)", duration: 0.35, ease: "expo.out", stagger: per }, 0.1);
    const endW = 0.1 + per * R.words.length;
    tl.fromTo(rule, { scaleX: 0 }, { scaleX: 1, duration: 0.35, ease: "expo.out" }, endW);
    typeIn(by, "— " + (D.by || "CARRIE MULLIN INNES · SPORTS DIETITIAN"), endW + 0.05, 0.008);
    exitGroup([R.block, qm, by, rule], X);
  }
  function buildMyth() {
    const v = D.bg || "ink"; const { T, Ltx, X } = heroFrame(v);
    const s = String(D.screen || "");
    const two = !!(D.myth && D.fact); const question = !two && /\?/.test(s);
    const g = el("div", "abs", Ltx); css(g, { left: "150px", top: "0px" });
    const row = el("div", "", g); css(row, { display: "flex", gap: "14px", alignItems: "center", marginBottom: "26px" });
    const mc = chip(row, "MYTH CHECK", "transparent", T.fg, 24, 8, 16); css(mc, { border: `2px solid ${T.fg}`, position: "relative" });
    const strike = el("div", "abs", mc); css(strike, { left: "-6px", right: "-6px", top: "44%", height: "5px", background: C.accent, transformOrigin: "0 50%" });
    const fc = question ? null : chip(row, "FACT", C.hi, C.ink, 24, 10, 18);
    let MR = null;
    if (two) { const mt = tokenize(D.myth, {}); MR = renderLines(g, layoutLines(mt, 1560, 2, D.size || 100, 60), { color: T.fg });
      css(MR.block, { position: "relative", marginBottom: "36px", opacity: 0.4 }); }
    const toks = tokenize(two ? D.fact : s, { accent: D.accent_word });
    const lay = layoutLines(toks, 1600, 3, D.size || 150, 80);
    const R = renderLines(g, lay, { color: T.fg, accColor: C.hi }); css(R.block, { position: "relative" });
    const gh = g.getBoundingClientRect().height; css(g, { top: px(Math.round(530 - gh / 2)) });
    tl.fromTo(mc, { clipPath: "inset(0% 100% 0% 0%)" }, { clipPath: "inset(0% 0% 0% 0%)", duration: 0.28, ease: "expo.out" }, 0.04);
    if (MR) tl.fromTo(MR.lines, { yPercent: 108 }, { yPercent: 0, duration: 0.4, ease: "expo.out", stagger: 0.05 }, 0.1);
    const S = D.strike_at || (question ? 0.3 : 0.42);
    if (!question) {
      tl.fromTo(strike, { scaleX: 0 }, { scaleX: 1, duration: 0.18, ease: "power3.inOut" }, S);
      tl.fromTo(mc, { opacity: 1 }, { opacity: 0.45, duration: 0.2, immediateRender: false }, S + 0.12);
      tl.fromTo(fc, { scale: 0, rotation: -10 }, { scale: 1, rotation: 0, duration: 0.32, ease: "back.out(2.2)" }, S + 0.16);
    } else { css(strike, { display: "none" }); }
    tl.fromTo(R.lines, { yPercent: 108 }, { yPercent: 0, duration: 0.48, ease: "expo.out", stagger: 0.07 }, S + 0.2);
    const qs = R.words.filter((w) => /\?$/.test(w.textContent) && w.style.color !== C.hi);
    if (question && qs.length) tl.fromTo(qs, { color: T.fg }, { color: C.hi, duration: 0.15, stagger: 0.25 }, S + 0.6);
    exitGroup([g], X);
  }

  // ------------------------------------------------------------------ TITLE STING (opaque, ~4.5 s)
  function buildTitle() {
    document.body.classList.add("opaque"); const T = theme("ink"); const { cam } = rig();
    const Lbg = layer(cam, -1000), Lnum = layer(cam, -640), Lph = layer(cam, -240), Ltx = layer(cam, 0);
    const bg = background(Lbg, "ink"); el("div", "vignette", app); const hud = el("div", "hud", app);
    const big = el("div", "outline-num abs", Lnum, "01"); css(big, { fontSize: "1020px", right: "-60px", top: "40px", WebkitTextStroke: "3px rgba(255,90,31,.30)" });
    const photos = (D.photos || []).map(img).slice(0, 3);
    const pos = [[1330, 210, -7], [1395, 300, 5], [1300, 400, -2.5]]; const cards = [];
    photos.forEach((p, i) => { const [x, y, r] = pos[i]; cards.push(polaroid(Lph, p, x, y, 470, 380, r, (D.photo_caps || [])[i] || "")); });
    const toks = tokenize(D.title || "FUELLING LIKE AN ENDURANCE ATHLETE", { smallSerif: true, smallScale: 0.6 });
    // one big word per line, small words ride with the previous big word
    const groups = []; toks.forEach((tk) => { if (tk.small && groups.length) groups[groups.length - 1]++; else groups.push(1); });
    const forced = groups.length <= 4 ? groups : null;
    const lay = layoutLines(toks, photos.length ? 1180 : 1600, 4, 210, 110, forced);
    const R = renderLines(Ltx, lay, { color: C.white, smallColor: C.accent, lh: 0.88 });
    const th = lay.lines.length * lay.size * 0.88; const top = Math.round(500 - th / 2 - 30);
    css(R.block, { left: "96px", top: px(top) });
    const rule = el("div", "abs", Ltx); const tw = Math.max(...R.lines.map((l) => boxW(l)));
    css(rule, { left: "100px", top: px(top + th + 34), width: px(tw), height: "6px", background: C.accent, transformOrigin: "0 50%" });
    const names = el("div", "ith abs", Ltx); css(names, { left: "96px", top: px(top + th + 68), fontSize: "50px", color: C.white, whiteSpace: "pre", letterSpacing: "0.005em" });
    const nw = []; String(D.names || "Nizam × Carrie Mullin Innes").split(/\s+/).forEach((w, i) => { const s = el("span", "", names, (i ? " " : "") + w); if (w === "×") s.style.color = C.accent; nw.push(s); });
    const role = el("div", "sm abs", Ltx); css(role, { left: "98px", top: px(top + th + 136), fontSize: "21px", color: C.paper, opacity: 0.75, whiteSpace: "pre" });
    // HUD
    const tlab = el("div", "sm abs", hud); css(tlab, { left: "96px", top: "52px", fontSize: "19px", color: C.paper, opacity: 0.85, whiteSpace: "pre" });
    const trab = el("div", "smr abs", hud); css(trab, { right: "96px", top: "52px", fontSize: "18px", color: C.paper, opacity: 0.7, whiteSpace: "pre", textAlign: "right" });
    const foot = el("div", "smr abs", hud); css(foot, { left: "96px", top: "1006px", fontSize: "16px", color: C.paper, opacity: 0.55, whiteSpace: "pre" });
    const regs = regMarks(hud, C.paper, 0.45); const edges = edgeTicks(hud, C.paper, 0.26);
    const scan = el("div", "abs", hud); css(scan, { left: "0px", top: "539px", width: "1920px", height: "3px", background: C.accent, transformOrigin: "0 50%" });
    grain(app, 0.75);
    // ---- motion
    tl.fromTo(bg, { opacity: 0 }, { opacity: 1, duration: 0.35, ease: "power1.out" }, 0);
    tl.fromTo(scan, { scaleX: 0 }, { scaleX: 1, duration: 0.24, ease: "expo.out" }, 0.0);
    tl.fromTo(scan, { scaleY: 1, opacity: 1 }, { scaleY: 0, opacity: 0, duration: 0.14, ease: "power2.in", immediateRender: false }, 0.24);
    typeIn(tlab, D.top_left || "FUEL LAB — EPISODE 01", 0.06, 0.012);
    typeIn(trab, D.top_right || "SPORTS NUTRITION · 64 MIN", 0.12, 0.01);
    typeIn(foot, D.footer || "NIZAM × CARRIE MULLIN INNES — A CONVERSATION ABOUT FOOD, SWEAT & PERFORMANCE", 0.4, 0.006);
    tl.fromTo([...regs, edges], { opacity: 0 }, { opacity: (i) => (i < 4 ? 0.45 : 0.26), duration: 0.25, stagger: 0.03 }, 0.05);
    tl.set(cam, { rotationY: 0, rotationX: 0, z: 0, x: 0 }, 0);
    tl.fromTo(big, { x: 360, opacity: 0, filter: "blur(30px)" }, { x: 0, opacity: 1, filter: "blur(0px)", duration: 0.9, ease: "expo.out" }, 0.15);
    // slams: one beat per line
    const beats = [0.28, 0.72, 1.06, 1.36];
    R.lines.forEach((li, i) => {
      const at = beats[i] != null ? beats[i] : 1.36 + (i - 3) * 0.28;
      const ws = [...li.children];
      const bigW = ws.filter((w) => !w.classList.contains("is")); const smallW = ws.filter((w) => w.classList.contains("is"));
      if (i % 2 === 0) tl.fromTo(li, { yPercent: 110 }, { yPercent: 0, duration: 0.42, ease: "expo.out" }, at);
      else { tl.fromTo(li, { yPercent: 110 }, { yPercent: 0, duration: 0.42, ease: "expo.out" }, at);
        tl.fromTo(bigW, { letterSpacing: "0.14em" }, { letterSpacing: "-0.02em", duration: 0.55, ease: "expo.out" }, at); }
      if (smallW.length) tl.fromTo(smallW, { opacity: 0, x: -16, filter: "blur(12px)" }, { opacity: 1, x: 0, filter: "blur(0px)", duration: 0.4, ease: "power3.out" }, at + 0.22);
      if (cards[i]) tl.fromTo(cards[i], { y: -160, rotation: (i % 2 ? 18 : -18), scale: 1.15, opacity: 0 }, { y: 0, rotation: pos[i][2], scale: 1, opacity: 1, duration: 0.55, ease: "back.out(1.25)" }, at + 0.04);
    });
    // tiny camera kick on the first slam
    const after = (beats[Math.min(R.lines.length, beats.length) - 1] || 1.36) + 0.4;
    tl.fromTo(rule, { scaleX: 0 }, { scaleX: 1, duration: 0.55, ease: "expo.out" }, after);
    tl.fromTo(nw, { opacity: 0, y: 20, filter: "blur(10px)" }, { opacity: 1, y: 0, filter: "blur(0px)", duration: 0.4, ease: "expo.out", stagger: 0.06 }, after + 0.1);
    typeIn(role, D.role || "HIGH-PERFORMANCE SPORTS DIETITIAN · IOC DIP. SPORTS NUTRITION", after + 0.35, 0.01);
    // exit: push-through
    const X = DUR - 0.5;
    tl.fromTo(R.lines, { opacity: 1 }, { opacity: 0, duration: 0.3, ease: "power2.in", stagger: 0.04, immediateRender: false }, X);
    tl.fromTo([names, role, rule], { opacity: 1 }, { opacity: 0, y: 30, duration: 0.22, ease: "power2.in", immediateRender: false }, X);
    cards.forEach((c, i) => tl.fromTo(c, { opacity: 1 }, { opacity: 0, x: 380 + i * 60, rotation: "+=" + (12 + i * 4), duration: 0.32, ease: "power3.in", immediateRender: false }, X + 0.02 * i));
    tl.fromTo(big, { opacity: 1 }, { opacity: 0, duration: 0.35, ease: "power2.in", immediateRender: false }, X);
    tl.fromTo([tlab, trab, foot, edges, ...regs], { opacity: (i) => [0.85, 0.7, 0.55, 0.26, 0.45, 0.45, 0.45, 0.45][i] }, { opacity: 0, duration: 0.2, immediateRender: false }, X + 0.15);
  }

  // ------------------------------------------------------------------ OUTRO (opaque, 6 s, calm)
  function buildOutro() {
    document.body.classList.add("opaque"); const T = theme("paper"); const { cam } = rig();
    const Lbg = layer(cam, -800), Lph = layer(cam, -220), Ltx = layer(cam, 0);
    background(Lbg, "paper"); el("div", "vignette soft", app); const hud = el("div", "hud", app);
    const photo = img(D.photo); let card = null;
    if (photo) card = polaroid(Lph, photo, 1330, 170, 470, 380, 4, D.photo_label || "FIG. END");
    const thx = el("div", "is abs", Ltx, D.thanks1 || "Thanks for"); css(thx, { left: "96px", top: "190px", fontSize: "150px", color: C.ink, lineHeight: 1 });
    const wm = el("div", "mask abs", Ltx); css(wm, { left: "96px", top: "330px" });
    const wi = el("div", "line-in ab", wm); css(wi, { fontSize: "196px", color: C.ink, lineHeight: 0.9 });
    wi.innerHTML = (D.thanks2 || "WATCHING").toUpperCase() + '<span style="color:#FF5A1F">.</span>';
    const rule = el("div", "abs", Ltx); css(rule, { left: "100px", top: "560px", width: "1724px", height: "3px", background: C.ink, transformOrigin: "0 50%" });
    function col(x, role, name, sub, w) {
      const c = el("div", "abs", Ltx); css(c, { left: px(x), top: "606px", width: px(w) });
      const ch = chip(c, role, C.ink, C.paper, 18, 7, 12); css(ch, { marginBottom: "18px" });
      const n = el("div", "ab", c, name.toUpperCase()); css(n, { fontSize: "58px", color: C.ink, lineHeight: 0.95 });
      const s = el("div", "itm", c, sub); css(s, { fontSize: "30px", color: "rgba(13,13,13,.78)", marginTop: "14px", lineHeight: 1.18 });
      return c;
    }
    const host = D.host || { name: "Nizam", role: "Training to become an endurance athlete" };
    const guest = D.guest || { name: "Carrie Mullin Innes", role: "High-Performance Sports Dietitian · IOC Dip. Sports Nutrition" };
    const c1 = col(96, "HOST", host.name, host.role, 600); const c2 = col(820, "GUEST", guest.name, guest.role, 1000);
    const tlab = el("div", "sm abs", hud); css(tlab, { left: "96px", top: "52px", fontSize: "19px", color: C.ink, opacity: 0.8, whiteSpace: "pre" });
    const trab = el("div", "smr abs", hud); css(trab, { right: "96px", top: "52px", fontSize: "18px", color: C.ink, opacity: 0.65, whiteSpace: "pre" });
    const foot = el("div", "sm abs", hud); css(foot, { left: "96px", top: "1004px", fontSize: "18px", color: C.ink, opacity: 0.72, whiteSpace: "pre" });
    const fr = el("div", "smr abs", hud, "EP.01"); css(fr, { right: "96px", top: "1004px", fontSize: "18px", color: C.ink, opacity: 0.6 });
    const regs = regMarks(hud, C.ink, 0.4); const edges = edgeTicks(hud, C.ink, 0.22);
    grain(app, 0.75);
    const fade = el("div", "abs", app); css(fade, { inset: "0px", background: C.ink });
    tl.set(cam, { z: 0, rotationY: 0, rotationX: 0 }, 0);
    tl.fromTo(fade, { opacity: 1 }, { opacity: 0, duration: 0.5, ease: "power1.out" }, 0);
    tl.fromTo([...regs, edges], { opacity: 0 }, { opacity: (i) => (i < 4 ? 0.4 : 0.22), duration: 0.5 }, 0.2);
    typeIn(tlab, D.top_left || "END OF EPISODE 01", 0.3, 0.02);
    typeIn(trab, D.top_right || "FUEL LAB", 0.4, 0.02);
    tl.fromTo(thx, { opacity: 0, y: 30, filter: "blur(14px)" }, { opacity: 1, y: 0, filter: "blur(0px)", duration: 1.0, ease: "power3.out" }, 0.35);
    tl.fromTo(wi, { yPercent: 105 }, { yPercent: 0, duration: 0.9, ease: "expo.out" }, 0.7);
    tl.fromTo(rule, { scaleX: 0 }, { scaleX: 1, duration: 1.1, ease: "expo.inOut" }, 1.0);
    tl.fromTo([c1, c2], { opacity: 0, y: 26 }, { opacity: 1, y: 0, duration: 0.8, ease: "power3.out", stagger: 0.18 }, 1.35);
    typeIn(foot, D.title || "FUELLING LIKE AN ENDURANCE ATHLETE", 1.8, 0.012);
    tl.fromTo(fr, { opacity: 0 }, { opacity: 0.6, duration: 0.4 }, 2.0);
    if (card) { tl.fromTo(card, { y: -60, rotation: 10, opacity: 0 }, { y: 0, rotation: 4, opacity: 1, duration: 1.0, ease: "power3.out" }, 0.9);
      }
    tl.fromTo(fade, { opacity: 0 }, { opacity: 1, duration: 0.9, ease: "power1.in", immediateRender: false }, DUR - 0.9);
  }

  // ------------------------------------------------------------------ TRANSITIONS (alpha, full frame, cover 0.20-0.30 s of 0.5 s)
  function buildTransition() {
    const v = D.variant || "ink"; const a = D.cover_at || 0.2, b = D.cover_end || 0.3; const e = DUR;
    if (v === "ink") {
      const p = el("div", "abs", app); css(p, { left: "0px", top: "0px", width: "2000px", height: "1080px", background: C.ink });
      const edgeL = el("div", "abs", p); css(edgeL, { left: "0px", top: "0px", width: "34px", height: "1080px", background: C.accent });
      const edgeR = el("div", "abs", p); css(edgeR, { right: "0px", top: "0px", width: "34px", height: "1080px", background: C.accent });
      const lab = el("div", "sm abs", p, "FUEL LAB"); css(lab, { left: "40px", width: "1920px", textAlign: "center", top: "526px", fontSize: "22px", color: C.paper, opacity: 0.0 });
      tl.fromTo(p, { x: -2040 }, { x: -40, duration: a, ease: "power3.in" }, 0);
      tl.fromTo(p, { x: -40 }, { x: 1960, duration: e - b, ease: "power3.out", immediateRender: false }, b);
      tl.fromTo(lab, { opacity: 0 }, { opacity: 0.8, duration: 0.001 }, a - 0.03);
      tl.fromTo(lab, { opacity: 0.8 }, { opacity: 0, duration: 0.001, immediateRender: false }, b + 0.03);
    } else if (v === "bars") {
      const n = 6, hh = 1080 / n;
      for (let i = 0; i < n; i++) {
        const bar = el("div", "abs", app); const dir = i % 2 ? 1 : -1;
        css(bar, { left: "0px", top: px(i * hh - 1), width: "1920px", height: px(hh + 2), background: i % 2 ? C.ink : C.accent });
        tl.fromTo(bar, { x: dir * 1960 }, { x: 0, duration: a - i * 0.012, ease: "power3.in" }, i * 0.012);
        tl.fromTo(bar, { x: 0 }, { x: -dir * 1960, duration: e - b - (n - 1 - i) * 0.012, ease: "power3.out", immediateRender: false }, b + i * 0.012);
      }
    } else if (v === "green") {
      const p = el("div", "abs", app); css(p, { left: "0px", top: "0px", width: "1920px", height: "1180px" });
      const bgp = el("div", "abs", p); css(bgp, { left: "0px", top: "50px", width: "1920px", height: "1080px", background: C.green });
      const g = el("div", "gridlines g-green", bgp);
      const t1 = el("div", "abs", p); css(t1, { left: "0px", top: "40px", width: "1920px", height: "12px", background: C.hi });
      const t2 = el("div", "abs", p); css(t2, { left: "0px", top: "1128px", width: "1920px", height: "12px", background: C.hi });
      tl.fromTo(p, { y: 1100 }, { y: -50, duration: a, ease: "power3.in" }, 0);
      tl.fromTo(p, { y: -50 }, { y: -1200, duration: e - b, ease: "power3.out", immediateRender: false }, b);
    } else { // blocks: 8 columns drop
      const n = 8, w = 1920 / n;
      for (let i = 0; i < n; i++) {
        const c = el("div", "abs", app); css(c, { left: px(i * w - 1), top: "0px", width: px(w + 2), height: "1080px", background: i % 3 === 1 ? C.accent : C.ink });
        tl.fromTo(c, { y: -1100 }, { y: 0, duration: a - i * 0.01, ease: "power3.in" }, i * 0.01);
        tl.fromTo(c, { y: 0 }, { y: 1100, duration: e - b - (n - 1 - i) * 0.01, ease: "power3.out", immediateRender: false }, b + i * 0.01);
      }
    }
  }

  // ------------------------------------------------------------------ PLATES (single frame png)
  function buildPlate() {
    document.body.classList.add("opaque"); const v = D.variant || "paper";
    const b = el("div", "abs", app); css(b, { inset: "0px" });
    const bg = el("div", "abs bg-" + v, b); css(bg, { inset: "0px" });
    el("div", "gridlines g-" + v, bg);
    el("div", "vignette" + (v === "paper" ? " soft" : ""), b);
    const col = v === "paper" ? C.ink : C.paper;
    regMarks(app, col, v === "paper" ? 0.32 : 0.4); edgeTicks(app, col, v === "paper" ? 0.2 : 0.26);
    const l = el("div", "smr abs", app, D.top_left || "FUEL LAB — EP.01"); css(l, { left: "80px", top: "34px", fontSize: "15px", color: col, opacity: 0.5 });
    const r = el("div", "smr abs", app, D.top_right || "NIZAM × CARRIE MULLIN INNES"); css(r, { right: "80px", top: "34px", fontSize: "15px", color: col, opacity: 0.5 });
    tl.set(b, { opacity: 1 }, 0);
  }

  const B = { chapter: buildChapter, tag: buildTag, lt: buildLT, headline: buildHeadline, title: buildTitle, outro: buildOutro,
              transition: buildTransition, plate: buildPlate,
              hero: () => ({ number: buildNumber, quote: buildQuote, myth: buildMyth }[D.style] || buildPunch)() };
  const fonts = ["400 100px AB", "400 100px ITH", "400 100px ITM", "400 100px IS", "400 100px SM", "700 100px SM"];
  Promise.all(fonts.map((f) => document.fonts.load(f))).then(() => document.fonts.ready).then(() => {
    (B[G.kind] || buildPunch)();
    window.__timelines["main"] = tl;
    if (window.__hfForceTimelineRebind) window.__hfForceTimelineRebind();
  });
})();
