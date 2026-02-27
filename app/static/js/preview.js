/**
 * Godot Game Creator — Canvas Preview Renderer
 *
 * Procedurally draws a live visual preview of the game being designed:
 * player sprite, enemies, collectibles, terrain, background, particles, weather.
 */

const Preview = (() => {
  let canvas, ctx;
  let animFrame = null;
  let particles = [];
  let time = 0;

  function init(canvasEl) {
    canvas = canvasEl;
    ctx = canvas.getContext("2d");
    canvas.width = 320;
    canvas.height = 240;
    particles = _initParticles(40);
  }

  function render(spec) {
    if (!ctx || !spec) return;
    time += 0.016;
    const W = canvas.width, H = canvas.height;
    ctx.clearRect(0, 0, W, H);
    _drawBackground(spec, W, H);
    _drawTerrain(spec, W, H);
    if (spec.has_collectibles) _drawCollectibles(spec, W, H);
    if (spec.has_enemies) _drawEnemy(spec, W, H);
    _drawPlayer(spec, W, H);
    if (spec.has_particles || spec.particle_type !== "none") _drawParticles(spec, W, H);
    if (spec.weather && spec.weather !== "none") _drawWeather(spec, W, H);
    _drawHUDPreview(spec, W, H);
  }

  function startLoop(specGetter) {
    function loop() {
      render(specGetter());
      animFrame = requestAnimationFrame(loop);
    }
    if (animFrame) cancelAnimationFrame(animFrame);
    loop();
  }

  function stop() {
    if (animFrame) { cancelAnimationFrame(animFrame); animFrame = null; }
  }

  /* ── Background ─────────────────────────────── */
  function _drawBackground(spec, W, H) {
    const bg = spec.color_bg || "#1a1a2e";
    const grd = ctx.createLinearGradient(0, 0, 0, H);
    grd.addColorStop(0, _lighten(bg, 20));
    grd.addColorStop(1, bg);
    ctx.fillStyle = grd;
    ctx.fillRect(0, 0, W, H);

    if (spec.has_parallax_bg) {
      ctx.globalAlpha = 0.15;
      for (let i = 0; i < 3; i++) {
        const y = H * 0.3 + i * 30;
        const offset = Math.sin(time * 0.3 + i) * 20;
        ctx.fillStyle = spec.color_primary || "#4a90d9";
        ctx.beginPath();
        for (let x = -20; x < W + 20; x += 4) {
          const cy = y + Math.sin((x + offset) * 0.02 + i) * 15;
          x === -20 ? ctx.moveTo(x, cy) : ctx.lineTo(x, cy);
        }
        ctx.lineTo(W + 20, H); ctx.lineTo(-20, H); ctx.closePath(); ctx.fill();
      }
      ctx.globalAlpha = 1;
    }

    const theme = (spec.theme || "").toLowerCase();
    if (theme.includes("space") || theme.includes("sci")) {
      ctx.fillStyle = "#ffffff";
      for (let i = 0; i < 30; i++) {
        const sx = (i * 73 + time * 5 * (i % 3 + 1)) % W;
        const sy = (i * 47) % (H * 0.65);
        const sz = 0.5 + (i % 3) * 0.5;
        ctx.globalAlpha = 0.3 + Math.sin(time * 2 + i) * 0.3;
        ctx.fillRect(sx, sy, sz, sz);
      }
      ctx.globalAlpha = 1;
    }
  }

  /* ── Terrain / Ground ───────────────────────── */
  function _drawTerrain(spec, W, H) {
    const genre = spec.genre;
    const ground = spec.color_ground || "#2d5a27";

    if (genre === "platformer") {
      ctx.fillStyle = ground;
      ctx.fillRect(0, H - 32, W, 32);
      ctx.fillStyle = _darken(ground, 20);
      ctx.fillRect(0, H - 32, W, 3);
      // platforms
      ctx.fillStyle = "#6b5b4f";
      ctx.fillRect(40, H - 80, 70, 10);
      ctx.fillRect(140, H - 110, 60, 10);
      ctx.fillRect(230, H - 140, 55, 10);
    } else if (genre === "topdown") {
      ctx.fillStyle = ground;
      ctx.fillRect(20, 30, W - 40, H - 50);
      ctx.strokeStyle = _darken(ground, 30);
      ctx.lineWidth = 3;
      ctx.strokeRect(20, 30, W - 40, H - 50);
    } else if (genre === "shooter") {
      // starfield handled in background
    } else if (genre === "racing") {
      ctx.fillStyle = "#333340";
      ctx.fillRect(W * 0.2, 0, W * 0.6, H);
      ctx.strokeStyle = "rgba(255,255,255,0.15)";
      ctx.setLineDash([12, 12]);
      const off = (time * 80) % 24;
      ctx.beginPath();
      ctx.moveTo(W * 0.5, -off);
      ctx.lineTo(W * 0.5, H);
      ctx.stroke();
      ctx.setLineDash([]);
    } else if (genre === "puzzle") {
      // grid hint
      ctx.strokeStyle = "rgba(255,255,255,0.05)";
      for (let r = 0; r < 6; r++) for (let c = 0; c < 8; c++) {
        ctx.strokeRect(W * 0.15 + c * 28, H * 0.2 + r * 28, 26, 26);
      }
    } else if (genre === "visual_novel") {
      ctx.fillStyle = "rgba(0,0,0,0.5)";
      ctx.fillRect(10, H - 60, W - 20, 50);
      ctx.strokeStyle = "rgba(255,255,255,0.2)";
      ctx.strokeRect(10, H - 60, W - 20, 50);
    }
  }

  /* ── Player Sprite ──────────────────────────── */
  function _drawPlayer(spec, W, H) {
    const pc = spec.color_primary || "#4a90d9";
    const genre = spec.genre;

    ctx.fillStyle = pc;
    ctx.strokeStyle = _lighten(pc, 30);
    ctx.lineWidth = 1.5;

    if (genre === "platformer") {
      const px = 60, py = H - 56;
      const bob = Math.sin(time * 4) * 2;
      // body
      _roundRect(px - 8, py - 20 + bob, 16, 24, 3); ctx.fill(); ctx.stroke();
      // head
      ctx.beginPath(); ctx.arc(px, py - 26 + bob, 8, 0, Math.PI * 2); ctx.fill(); ctx.stroke();
      // eyes
      ctx.fillStyle = "#fff";
      ctx.fillRect(px + 2, py - 28 + bob, 3, 3);
      // legs
      ctx.fillStyle = _darken(pc, 20);
      ctx.fillRect(px - 6, py + 4 + bob, 5, 8);
      ctx.fillRect(px + 1, py + 4 + bob, 5, 8);
    } else if (genre === "topdown") {
      const px = W / 2, py = H / 2;
      const bob = Math.sin(time * 3) * 1;
      ctx.beginPath(); ctx.arc(px, py + bob, 10, 0, Math.PI * 2); ctx.fill(); ctx.stroke();
      ctx.fillStyle = "#fff";
      ctx.fillRect(px + 3, py - 3 + bob, 3, 3);
      ctx.fillStyle = _darken(pc, 30);
      ctx.beginPath(); ctx.arc(px, py + bob, 10, 0.1, Math.PI - 0.1); ctx.fill();
    } else if (genre === "shooter") {
      const px = W / 2, py = H * 0.78;
      ctx.beginPath();
      ctx.moveTo(px, py - 18);
      ctx.lineTo(px - 12, py + 10);
      ctx.lineTo(px + 12, py + 10);
      ctx.closePath();
      ctx.fill(); ctx.stroke();
      // engine glow
      ctx.fillStyle = spec.color_accent || "#f9ca24";
      ctx.globalAlpha = 0.5 + Math.sin(time * 10) * 0.3;
      ctx.beginPath(); ctx.arc(px, py + 12, 4, 0, Math.PI * 2); ctx.fill();
      ctx.globalAlpha = 1;
    } else if (genre === "racing") {
      const px = W / 2, py = H * 0.72;
      ctx.beginPath();
      ctx.moveTo(px - 8, py + 14);
      ctx.lineTo(px - 8, py - 10);
      ctx.lineTo(px - 5, py - 16);
      ctx.lineTo(px + 5, py - 16);
      ctx.lineTo(px + 8, py - 10);
      ctx.lineTo(px + 8, py + 14);
      ctx.closePath();
      ctx.fill(); ctx.stroke();
    } else if (genre === "visual_novel") {
      const px = W / 2, py = H * 0.45;
      // character silhouette
      _roundRect(px - 16, py - 20, 32, 60, 4); ctx.fill(); ctx.stroke();
      ctx.beginPath(); ctx.arc(px, py - 30, 14, 0, Math.PI * 2); ctx.fill(); ctx.stroke();
      ctx.fillStyle = "#fff";
      ctx.fillRect(px - 4, py - 33, 4, 4);
      ctx.fillRect(px + 2, py - 33, 4, 4);
    } else if (genre === "puzzle") {
      // cursor/selector
      ctx.strokeStyle = pc;
      ctx.lineWidth = 2;
      const blink = Math.sin(time * 3) > 0 ? 1 : 0.5;
      ctx.globalAlpha = blink;
      ctx.strokeRect(W * 0.15 + 3 * 28, H * 0.2 + 2 * 28, 26, 26);
      ctx.globalAlpha = 1;
    }
  }

  /* ── Enemies ────────────────────────────────── */
  function _drawEnemy(spec, W, H) {
    const ec = spec.color_secondary || "#d94a4a";
    ctx.fillStyle = ec;
    ctx.strokeStyle = _lighten(ec, 20);
    ctx.lineWidth = 1;
    const genre = spec.genre;

    if (genre === "platformer") {
      const ex = 200 + Math.sin(time * 1.5) * 20, ey = H - 50;
      ctx.beginPath(); ctx.arc(ex, ey, 9, 0, Math.PI * 2); ctx.fill(); ctx.stroke();
      ctx.fillStyle = "#fff";
      ctx.fillRect(ex - 5, ey - 3, 4, 4);
      ctx.fillRect(ex + 1, ey - 3, 4, 4);
      ctx.fillStyle = "#000";
      ctx.fillRect(ex - 4, ey - 2, 2, 2);
      ctx.fillRect(ex + 2, ey - 2, 2, 2);
    } else if (genre === "topdown") {
      const ex = W * 0.7 + Math.sin(time) * 15, ey = H * 0.35;
      ctx.beginPath(); ctx.arc(ex, ey, 8, 0, Math.PI * 2); ctx.fill(); ctx.stroke();
      ctx.fillStyle = "#fff";
      ctx.fillRect(ex + 2, ey - 2, 3, 3);
    } else if (genre === "shooter") {
      for (let i = 0; i < 3; i++) {
        const ex = 60 + i * 90, ey = 40 + Math.sin(time * 2 + i) * 15;
        ctx.fillStyle = ec;
        ctx.beginPath();
        ctx.moveTo(ex - 10, ey - 8);
        ctx.lineTo(ex, ey + 10);
        ctx.lineTo(ex + 10, ey - 8);
        ctx.closePath();
        ctx.fill(); ctx.stroke();
      }
    } else if (genre === "racing") {
      ctx.fillStyle = ec;
      const oy = ((time * 60) % (H + 40)) - 20;
      ctx.fillRect(W * 0.35 - 12, oy, 24, 24);
    }
  }

  /* ── Collectibles ───────────────────────────── */
  function _drawCollectibles(spec, W, H) {
    const ac = spec.color_accent || "#f9ca24";
    const genre = spec.genre;

    ctx.fillStyle = ac;
    ctx.strokeStyle = _darken(ac, 15);
    ctx.lineWidth = 1;

    const positions = genre === "platformer"
      ? [[80, H - 90], [160, H - 120], [250, H - 150]]
      : genre === "topdown"
        ? [[W * 0.35, H * 0.4], [W * 0.6, H * 0.6], [W * 0.3, H * 0.7]]
        : [];

    for (const [cx, cy] of positions) {
      const bob = Math.sin(time * 3 + cx) * 3;
      ctx.beginPath();
      ctx.arc(cx, cy + bob, 5, 0, Math.PI * 2);
      ctx.fill(); ctx.stroke();
      // sparkle
      ctx.globalAlpha = 0.4 + Math.sin(time * 5 + cx) * 0.3;
      ctx.fillStyle = "#fff";
      ctx.fillRect(cx - 1, cy + bob - 8, 2, 4);
      ctx.fillRect(cx - 4, cy + bob - 1, 4, 2);
      ctx.globalAlpha = 1;
      ctx.fillStyle = ac;
    }
  }

  /* ── Particles ──────────────────────────────── */
  function _initParticles(count) {
    const arr = [];
    for (let i = 0; i < count; i++) {
      arr.push({ x: Math.random(), y: Math.random(), s: 0.5 + Math.random() * 2, v: 0.2 + Math.random() * 0.8, phase: Math.random() * Math.PI * 2 });
    }
    return arr;
  }

  function _drawParticles(spec, W, H) {
    const pt = spec.particle_type || "sparkle";
    const colors = {
      fire: ["#ff6600", "#ff3300", "#ffaa00"],
      sparkle: ["#fff", "#ffe066", "#ffd700"],
      rain: ["#6ec6ff", "#4da6ff"],
      snow: ["#fff", "#e0e0ff", "#c0c0ff"],
      dust: ["#c4a35a", "#b8956a"],
      smoke: ["#888", "#aaa", "#666"],
      stars: ["#fff", "#ffe066", "#aaccff"],
      leaves: ["#4caf50", "#8bc34a", "#ff9800"],
      bubbles: ["#66ccff", "#99ddff", "#ffffff"],
      none: ["#fff", "#ffe066"],
    };
    const cols = colors[pt] || colors.sparkle;

    for (const p of particles) {
      const px = ((p.x * W + time * p.v * 30) % (W + 20)) - 10;
      let py;

      if (pt === "rain") {
        py = ((p.y * H + time * p.v * 120) % (H + 20)) - 10;
        ctx.strokeStyle = cols[0];
        ctx.globalAlpha = 0.4;
        ctx.beginPath(); ctx.moveTo(px, py); ctx.lineTo(px - 1, py + 6); ctx.stroke();
      } else if (pt === "snow") {
        py = ((p.y * H + time * p.v * 20) % (H + 20)) - 10;
        const sx = px + Math.sin(time + p.phase) * 8;
        ctx.fillStyle = cols[Math.floor(p.phase * 10) % cols.length];
        ctx.globalAlpha = 0.5 + Math.sin(time + p.phase) * 0.3;
        ctx.beginPath(); ctx.arc(sx, py, p.s, 0, Math.PI * 2); ctx.fill();
      } else if (pt === "fire") {
        py = H - 40 - p.y * 40 - Math.sin(time * 3 + p.phase) * 10;
        const fpx = W * 0.3 + p.x * W * 0.4;
        ctx.fillStyle = cols[Math.floor(p.phase * 10) % cols.length];
        ctx.globalAlpha = 0.3 + Math.sin(time * 4 + p.phase) * 0.3;
        ctx.beginPath(); ctx.arc(fpx, py, p.s * 1.5, 0, Math.PI * 2); ctx.fill();
      } else if (pt === "leaves") {
        py = ((p.y * H + time * p.v * 25) % (H + 20)) - 10;
        const lx = px + Math.sin(time * 0.7 + p.phase) * 15;
        ctx.fillStyle = cols[Math.floor(p.phase * 10) % cols.length];
        ctx.globalAlpha = 0.6;
        ctx.save(); ctx.translate(lx, py); ctx.rotate(time + p.phase);
        ctx.fillRect(-3, -1.5, 6, 3);
        ctx.restore();
      } else if (pt === "bubbles") {
        py = H - ((p.y * H + time * p.v * 30) % H);
        ctx.strokeStyle = cols[0];
        ctx.globalAlpha = 0.3 + Math.sin(time + p.phase) * 0.2;
        ctx.beginPath(); ctx.arc(px + Math.sin(time + p.phase) * 5, py, p.s * 2, 0, Math.PI * 2); ctx.stroke();
      } else {
        py = p.y * H;
        ctx.fillStyle = cols[Math.floor(p.phase * 10) % cols.length];
        ctx.globalAlpha = 0.3 + Math.sin(time * 3 + p.phase) * 0.4;
        ctx.beginPath(); ctx.arc(px, py, p.s, 0, Math.PI * 2); ctx.fill();
      }
    }
    ctx.globalAlpha = 1;
  }

  /* ── Weather overlay ────────────────────────── */
  function _drawWeather(spec, W, H) {
    const w = spec.weather;
    if (w === "rain") {
      ctx.strokeStyle = "rgba(100,180,255,0.25)";
      ctx.lineWidth = 1;
      for (let i = 0; i < 30; i++) {
        const rx = (i * 37 + time * 200) % W;
        const ry = (i * 53 + time * 400) % H;
        ctx.beginPath(); ctx.moveTo(rx, ry); ctx.lineTo(rx - 2, ry + 10); ctx.stroke();
      }
    } else if (w === "snow") {
      ctx.fillStyle = "rgba(255,255,255,0.4)";
      for (let i = 0; i < 25; i++) {
        const sx = (i * 41 + time * 15 + Math.sin(time + i) * 10) % W;
        const sy = (i * 67 + time * 30) % H;
        ctx.beginPath(); ctx.arc(sx, sy, 1 + (i % 2), 0, Math.PI * 2); ctx.fill();
      }
    } else if (w === "fog") {
      ctx.fillStyle = "rgba(180,180,200,0.12)";
      for (let i = 0; i < 4; i++) {
        const fy = H * 0.5 + i * 25 + Math.sin(time * 0.3 + i) * 10;
        ctx.beginPath();
        ctx.ellipse(W / 2 + Math.sin(time * 0.2 + i) * 30, fy, W * 0.6, 20, 0, 0, Math.PI * 2);
        ctx.fill();
      }
    }
  }

  /* ── HUD Preview ────────────────────────────── */
  function _drawHUDPreview(spec, W, H) {
    ctx.fillStyle = "rgba(255,255,255,0.7)";
    ctx.font = "bold 9px sans-serif";
    ctx.fillText("Score: 0", 6, 14);
    ctx.fillText("HP", 6, 26);
    ctx.fillStyle = "rgba(255,50,50,0.6)";
    ctx.fillRect(22, 19, 40, 6);
    ctx.fillStyle = "rgba(50,255,50,0.8)";
    ctx.fillRect(22, 19, 32, 6);
  }

  /* ── Helpers ────────────────────────────────── */
  function _roundRect(x, y, w, h, r) {
    ctx.beginPath();
    ctx.moveTo(x + r, y);
    ctx.lineTo(x + w - r, y); ctx.quadraticCurveTo(x + w, y, x + w, y + r);
    ctx.lineTo(x + w, y + h - r); ctx.quadraticCurveTo(x + w, y + h, x + w - r, y + h);
    ctx.lineTo(x + r, y + h); ctx.quadraticCurveTo(x, y + h, x, y + h - r);
    ctx.lineTo(x, y + r); ctx.quadraticCurveTo(x, y, x + r, y);
    ctx.closePath();
  }

  function _lighten(hex, pct) { return _adjustColor(hex, pct); }
  function _darken(hex, pct) { return _adjustColor(hex, -pct); }

  function _adjustColor(hex, pct) {
    hex = hex.replace("#", "");
    if (hex.length === 3) hex = hex[0]+hex[0]+hex[1]+hex[1]+hex[2]+hex[2];
    let r = parseInt(hex.substring(0, 2), 16);
    let g = parseInt(hex.substring(2, 4), 16);
    let b = parseInt(hex.substring(4, 6), 16);
    r = Math.min(255, Math.max(0, r + Math.round(r * pct / 100)));
    g = Math.min(255, Math.max(0, g + Math.round(g * pct / 100)));
    b = Math.min(255, Math.max(0, b + Math.round(b * pct / 100)));
    return `#${r.toString(16).padStart(2,"0")}${g.toString(16).padStart(2,"0")}${b.toString(16).padStart(2,"0")}`;
  }

  return { init, render, startLoop, stop };
})();
