import json
import streamlit as st
import streamlit.components.v1 as components

BADGE_HEX = {
    "🔴": "#ef4444",
    "🟡": "#eab308",
    "🟢": "#22c55e",
    "🔵": "#3b82f6",
    "🟣": "#a855f7",
    "🟠": "#f97316",
    "🟤": "#a16207",
    "⚪": "#e2e8f0",
}


def render_br(room, my_pid, arena_mode="1v1"):
    code = room["code"]
    players = room["players"]
    slot_idx = players.index(my_pid) if my_pid in players else 0
    is_host = (my_pid == room["host"])

    config = json.dumps({
        "mode": arena_mode,
        "roomCode": code,
        "myPid": my_pid,
        "myName": room["names"].get(my_pid, "Player"),
        "myColor": BADGE_HEX.get(room["badges"].get(my_pid, "🔴"), "#ef4444"),
        "slotIdx": slot_idx,
        "isHost": is_host,
    })

    html = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no" />
<style>
  * {{ box-sizing: border-box; user-select: none; -webkit-user-select: none; }}
  html, body {{
    margin: 0; padding: 0; overflow: hidden;
    background: #070b14; font-family: system-ui, -apple-system, sans-serif; color: #f8fafc;
    touch-action: none;
  }}
  #game-container {{
    position: relative; width: 100vw; height: 660px; overflow: hidden;
  }}
  #game-container:fullscreen {{
    width: 100vw; height: 100vh;
  }}

  /* Crosshair & Hitmarker */
  #crosshair {{
    position: absolute; top: 50%; left: 50%;
    width: 22px; height: 22px; transform: translate(-50%, -50%);
    pointer-events: none; z-index: 10;
  }}
  #crosshair::before, #crosshair::after {{
    content: ""; position: absolute; background: rgba(255,255,255,0.95);
    box-shadow: 0 0 4px #000;
  }}
  #crosshair::before {{ top: 10px; left: 0; width: 22px; height: 2px; }}
  #crosshair::after {{ left: 10px; top: 0; width: 2px; height: 22px; }}
  #hitmarker {{
    position: absolute; top: 50%; left: 50%;
    width: 26px; height: 26px; transform: translate(-50%, -50%) rotate(45deg);
    pointer-events: none; z-index: 11; opacity: 0; transition: opacity 0.08s;
  }}
  #hitmarker::before, #hitmarker::after {{
    content: ""; position: absolute; background: #facc15;
  }}
  #hitmarker::before {{ top: 12px; left: 0; width: 26px; height: 2px; }}
  #hitmarker::after {{ left: 12px; top: 0; width: 2px; height: 26px; }}

  /* Top HUD & Toolbar */
  #top-hud {{
    position: absolute; top: 10px; left: 12px; right: 12px;
    display: flex; justify-content: space-between; align-items: flex-start;
    pointer-events: none; z-index: 14; gap: 8px;
  }}
  .hud-box {{
    background: rgba(15, 23, 42, 0.85);
    border: 1px solid rgba(148, 163, 184, 0.3);
    border-radius: 10px; padding: 8px 12px; font-size: 12px;
    backdrop-filter: blur(5px);
  }}
  .top-btns {{
    display: flex; gap: 6px; margin-top: 6px; pointer-events: auto; flex-wrap: wrap;
  }}
  .mini-btn {{
    background: #1e293b; color: #f8fafc; border: 1px solid #475569;
    border-radius: 6px; padding: 4px 9px; font-size: 11px; font-weight: 700; cursor: pointer;
  }}
  .mini-btn:hover {{ background: #334155; }}
  .mini-btn.active {{ background: #2563eb; border-color: #60a5fa; }}

  #minimap {{
    border-radius: 50%; border: 2px solid #38bdf8;
    background: #0f172a; margin-top: 6px;
  }}
  #kill-feed {{
    text-align: right; max-width: 280px; font-size: 11px; color: #e2e8f0;
  }}
  #prompt-banner {{
    position: absolute; top: 58%; left: 50%; transform: translateX(-50%);
    background: rgba(15, 23, 42, 0.92); border: 1px solid #facc15;
    padding: 6px 14px; border-radius: 8px; font-size: 13px; font-weight: 700;
    color: #fef08a; display: none; z-index: 13; pointer-events: none;
  }}

  /* Bottom HUD */
  #bottom-hud {{
    position: absolute; bottom: 10px; left: 50%; transform: translateX(-50%);
    display: flex; flex-direction: column; align-items: center; gap: 6px;
    pointer-events: none; z-index: 14; width: 96%; max-width: 780px;
  }}
  .mats-row {{
    display: flex; gap: 10px; font-size: 11px; font-weight: 800;
    background: rgba(15, 23, 42, 0.88); padding: 4px 12px; border-radius: 8px;
    border: 1px solid rgba(255,255,255,0.16);
  }}
  .bars {{
    display: flex; gap: 8px; width: 100%; max-width: 380px;
  }}
  .bar-wrap {{
    flex: 1; background: rgba(15, 23, 42, 0.9); border-radius: 8px;
    padding: 4px 8px; border: 1px solid rgba(255,255,255,0.18);
  }}
  .bar-label {{ font-size: 11px; font-weight: 700; display: flex; justify-content: space-between; }}
  .bar-track {{ height: 7px; background: #1e293b; border-radius: 4px; margin-top: 2px; overflow: hidden; }}
  #hp-fill {{ height: 100%; width: 100%; background: #22c55e; transition: width 0.1s; }}
  #sh-fill {{ height: 100%; width: 100%; background: #38bdf8; transition: width 0.1s; }}

  .hotbar {{
    display: flex; gap: 4px; pointer-events: auto; flex-wrap: wrap; justify-content: center;
  }}
  .slot {{
    background: rgba(15, 23, 42, 0.92);
    border: 2px solid rgba(148, 163, 184, 0.35);
    border-radius: 8px; padding: 4px 8px; text-align: center;
    min-width: 60px; cursor: pointer; font-size: 11px; font-weight: 700;
  }}
  .slot.active {{
    border-color: #facc15; background: rgba(250, 204, 21, 0.22); transform: translateY(-2px);
  }}
  .slot span {{ display: block; font-size: 9px; color: #94a3b8; font-weight: 600; }}

  /* Pre-Game Spawn Island Lobby Banner */
  #lobby-panel {{
    position: absolute; inset: 0; background: rgba(7, 11, 20, 0.84);
    display: flex; flex-direction: column; align-items: center; justify-content: center;
    z-index: 25; text-align: center; padding: 18px;
  }}
  #lobby-panel h1 {{ margin: 0 0 6px 0; font-size: 28px; }}
  #lobby-panel p {{ margin: 4px 0; color: #cbd5e1; max-width: 540px; font-size: 13px; }}
  #roster-box {{
    background: rgba(15, 23, 42, 0.92); border: 1px solid #38bdf8;
    border-radius: 12px; padding: 10px 18px; margin: 12px 0; min-width: 280px;
  }}
  .roster-item {{ font-size: 14px; font-weight: 700; margin: 4px 0; }}
  .btn-row {{ display: flex; gap: 10px; margin-top: 10px; flex-wrap: wrap; justify-content: center; }}
  button.action-btn {{
    background: #2563eb; color: white; border: none; border-radius: 10px;
    padding: 11px 18px; font-size: 14px; font-weight: 700; cursor: pointer;
  }}
  button.action-btn:hover {{ background: #1d4ed8; }}
  button.bot-btn {{ background: #059669; }}
  button.start-btn {{ background: #ea580c; }}

  /* 3x3 Build Edit Modal */
  #edit-modal {{
    position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);
    background: rgba(15, 23, 42, 0.95); border: 2px solid #38bdf8;
    border-radius: 14px; padding: 14px; z-index: 20; display: none; text-align: center;
  }}
  #edit-grid {{
    display: grid; grid-template-columns: repeat(3, 52px); gap: 6px; margin: 10px 0;
  }}
  .edit-tile {{
    width: 52px; height: 52px; border-radius: 6px; cursor: pointer;
    background: #2563eb; border: 2px solid #93c5fd;
  }}
  .edit-tile.cut {{
    background: rgba(15, 23, 42, 0.5); border: 2px dashed #475569;
  }}

  /* Touch Controls */
  #touch-layer {{
    position: absolute; inset: 0; pointer-events: none; z-index: 15; display: none;
  }}
  #joy-zone {{
    position: absolute; bottom: 115px; left: 20px; width: 124px; height: 124px;
    border-radius: 50%; background: rgba(15, 23, 42, 0.55);
    border: 2px solid rgba(148, 163, 184, 0.45); pointer-events: auto;
  }}
  #joy-knob {{
    position: absolute; top: 42px; left: 42px; width: 40px; height: 40px;
    border-radius: 50%; background: rgba(56, 189, 248, 0.85);
    border: 2px solid #fff; pointer-events: none;
  }}
  #look-zone {{
    position: absolute; top: 70px; right: 0; width: 52%; height: 62%;
    pointer-events: auto;
  }}
  #touch-btns {{
    position: absolute; bottom: 115px; right: 18px;
    display: grid; grid-template-columns: repeat(2, 62px); gap: 8px;
    pointer-events: auto;
  }}
  .t-btn {{
    height: 54px; border-radius: 12px; background: rgba(15, 23, 42, 0.78);
    border: 2px solid rgba(255,255,255,0.35); color: #fff;
    font-weight: 800; font-size: 12px; display: flex; align-items: center; justify-content: center;
  }}
  .t-btn:active {{ background: #2563eb; transform: scale(0.95); }}
  .t-fire {{ background: rgba(220, 38, 38, 0.82); border-color: #fca5a5; }}

  .nametag {{
    position: absolute; transform: translate(-50%, -100%);
    background: rgba(15, 23, 42, 0.88); padding: 2px 7px; border-radius: 6px;
    font-size: 11px; font-weight: 700; pointer-events: none; white-space: nowrap;
    border: 1px solid rgba(255,255,255,0.25); z-index: 8;
  }}
</style>
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<script src="https://unpkg.com/peerjs@1.5.4/dist/peerjs.min.js"></script>
</head>
<body>
<div id="game-container">
  <div id="crosshair"></div>
  <div id="hitmarker"></div>
  <div id="labels"></div>
  <div id="prompt-banner"></div>

  <div id="top-hud">
    <div class="hud-box">
      <div id="mode-header"><b>🏗️ 1v1.LOL</b> · Wins: <span id="wins-txt">0</span> · <span id="phase-txt">SPAWN LOBBY</span></div>
      <div style="font-size:11px;margin-top:2px;" id="net-status">🟡 Connecting Lobby...</div>
      <div class="top-btns">
        <button class="mini-btn" id="fs-btn">⛶ Fullscreen</button>
        <button class="mini-btn" id="lock-btn">🖱️ Lock Mouse</button>
        <button class="mini-btn" id="touch-toggle-btn">📱 Touch UI</button>
        <button class="mini-btn" id="lobby-open-btn">👥 Lobby</button>
      </div>
      <canvas id="minimap" width="90" height="90" style="display:none;"></canvas>
    </div>
    <div class="hud-box" id="kill-feed">
      <div><b>WASD</b> Move · <b>Space</b> Jump · <b>Hold Click</b> Shoot/Build</div>
      <div><b>1-5</b> Loadout · <b>Q</b> Wall · <b>E</b> Ramp · <b>C</b> Floor · <b>V</b> Cone · <b>G</b> Edit</div>
      <div><b>R</b> Rotate · <b>B</b> Bot · <b>X</b> Reset · <b>M</b> Mute</div>
    </div>
  </div>

  <div id="edit-modal">
    <div style="font-weight:800;font-size:14px;color:#38bdf8;">✏️ BUILD EDIT (Click squares to open window/door)</div>
    <div id="edit-grid"></div>
    <button class="action-btn" id="confirm-edit-btn" style="padding:6px 16px;font-size:13px;">✅ Confirm [G]</button>
  </div>

  <!-- Mobile / Tablet Touch Controls -->
  <div id="touch-layer">
    <div id="joy-zone"><div id="joy-knob"></div></div>
    <div id="look-zone"></div>
    <div id="touch-btns">
      <div class="t-btn t-fire" id="t-fire">🔥 FIRE</div>
      <div class="t-btn" id="t-jump">⬆️ JUMP</div>
      <div class="t-btn" id="t-ads">🎯 ADS</div>
      <div class="t-btn" id="t-edit">✏️ EDIT</div>
    </div>
  </div>

  <div id="bottom-hud">
    <div class="mats-row">
      <span>🪵 Wood: <span id="mat-wood">999</span></span>
      <span>🧱 Brick: <span id="mat-brick">999</span></span>
      <span>⚙️ Metal: <span id="mat-metal">999</span></span>
      <span>🧪 Pots: <span id="mat-pots">2</span></span>
    </div>
    <div class="bars">
      <div class="bar-wrap">
        <div class="bar-label"><span>❤️ HP</span><span id="hp-num">100</span></div>
        <div class="bar-track"><div id="hp-fill"></div></div>
      </div>
      <div class="bar-wrap">
        <div class="bar-label"><span>🛡️ SHIELD</span><span id="sh-num">100</span></div>
        <div class="bar-track"><div id="sh-fill"></div></div>
      </div>
    </div>
    <div class="hotbar" id="hotbar">
      <div class="slot active" data-mode="ar">🔫 AR<span>[1]</span></div>
      <div class="slot" data-mode="pump">💥 Pump<span>[2]</span></div>
      <div class="slot" data-mode="smg">⚡ SMG<span>[3]</span></div>
      <div class="slot" data-mode="pick">⛏️ Pick<span>[4]</span></div>
      <div class="slot" data-mode="pot">🧪 Pot<span>[5]</span></div>
      <div class="slot" data-mode="wall">🧱 Wall<span>[Q]</span></div>
      <div class="slot" data-mode="ramp">📐 Ramp<span>[E]</span></div>
      <div class="slot" data-mode="floor">🟫 Floor<span>[C]</span></div>
      <div class="slot" data-mode="cone">🔺 Cone<span>[V]</span></div>
    </div>
  </div>

  <!-- Pre-Match Lobby Overlay -->
  <div id="lobby-panel">
    <h1 id="ov-title">🏗️ 1v1.LOL SPAWN LOBBY</h1>
    <p id="ov-sub">Room Code: <b>{code}</b> — Wait for your friend to appear below, or warm up in the arena right now!</p>
    <div id="roster-box">
      <div style="font-size:11px;color:#94a3b8;margin-bottom:4px;">CONNECTED PLAYERS IN MATCH</div>
      <div id="roster-list"></div>
    </div>
    <div style="font-size:12px;color:#cbd5e1;margin-bottom:6px;">
      Mouse Sensitivity: <input type="range" id="sens-slider" min="0.5" max="2.5" step="0.1" value="1.0" style="vertical-align:middle;" />
    </div>
    <div class="btn-row">
      <button class="action-btn" id="warmup-btn">🏃 Warm Up / Resume</button>
      <button class="action-btn start-btn" id="start-match-btn">🚀 Start Official Match</button>
      <button class="action-btn bot-btn" id="bot-btn">🤖 Toggle Bot</button>
    </div>
  </div>
</div>

<script>
const CFG = {config};
const IS_BR = (CFG.mode === "br");
const container = document.getElementById("game-container");
const lobbyPanel = document.getElementById("lobby-panel");
const labelsDiv = document.getElementById("labels");
const promptBanner = document.getElementById("prompt-banner");

if (IS_BR) {{
  document.getElementById("ov-title").textContent = "🪂 BATTLE ROYALE SPAWN ISLAND";
  document.getElementById("ov-sub").textContent = "Room Code: " + CFG.roomCode + " — Once your friend joins the list below, click Start Official Match to deploy from the sky!";
  document.getElementById("mode-header").innerHTML = `<b>🌪️ STORM:</b> <span id="storm-txt">78m</span> · <b>🏆 Elims:</b> <span id="wins-txt">0</span>`;
  document.getElementById("minimap").style.display = "block";
}}

// --- PROCEDURAL CANVAS TEXTURE GENERATOR ---
function makeCanvasTex(drawFn, repeatX = 1, repeatY = 1) {{
  const c = document.createElement("canvas");
  c.width = 256; c.height = 256;
  const ctx = c.getContext("2d");
  drawFn(ctx, 256, 256);
  const tex = new THREE.CanvasTexture(c);
  tex.wrapS = THREE.RepeatWrapping;
  tex.wrapT = THREE.RepeatWrapping;
  tex.repeat.set(repeatX, repeatY);
  tex.anisotropy = 4;
  return tex;
}}

const TEX_WOOD = makeCanvasTex((ctx, w, h) => {{
  ctx.fillStyle = "#b45309";
  ctx.fillRect(0, 0, w, h);
  for (let i = 0; i < 8; i++) {{
    const y = i * 32;
    ctx.fillStyle = i % 2 === 0 ? "#c2610c" : "#9a3412";
    ctx.fillRect(0, y + 2, w, 28);
    ctx.fillStyle = "#451a03";
    ctx.fillRect(0, y, w, 2);
    // Wood grain streaks
    ctx.fillStyle = "rgba(69, 26, 3, 0.28)";
    for (let g = 0; g < 6; g++) ctx.fillRect((g * 43 + i * 19) % w, y + 8 + g * 3, 38, 2);
    // Nails
    ctx.fillStyle = "#1e293b";
    ctx.fillRect(10, y + 14, 4, 4);
    ctx.fillRect(w - 14, y + 14, 4, 4);
  }}
}});

const TEX_BRICK = makeCanvasTex((ctx, w, h) => {{
  ctx.fillStyle = "#cbd5e1"; // mortar
  ctx.fillRect(0, 0, w, h);
  const rows = 8, cols = 4;
  const rh = h / rows, cw = w / cols;
  for (let r = 0; r < rows; r++) {{
    const offset = (r % 2) * (cw / 2);
    for (let c = -1; c <= cols; c++) {{
      ctx.fillStyle = (r + c) % 2 === 0 ? "#b91c1c" : "#991b1b";
      ctx.fillRect(c * cw + offset + 2, r * rh + 2, cw - 4, rh - 4);
    }}
  }}
}});

const TEX_METAL = makeCanvasTex((ctx, w, h) => {{
  ctx.fillStyle = "#475569";
  ctx.fillRect(0, 0, w, h);
  ctx.strokeStyle = "#94a3b8";
  ctx.lineWidth = 3;
  ctx.strokeRect(6, 6, w - 12, h - 12);
  ctx.fillStyle = "#64748b";
  for (let y = 16; y < h; y += 32) {{
    for (let x = 16; x < w; x += 32) {{
      ctx.save();
      ctx.translate(x, y);
      ctx.rotate(Math.PI / 4);
      ctx.fillRect(-6, -2, 12, 4);
      ctx.restore();
    }}
  }}
}});

const TEX_GRASS = makeCanvasTex((ctx, w, h) => {{
  ctx.fillStyle = IS_BR ? "#2e7d32" : "#16243d";
  ctx.fillRect(0, 0, w, h);
  for (let i = 0; i < 650; i++) {{
    const x = (i * 73) % w;
    const y = (i * 137) % h;
    ctx.fillStyle = IS_BR
      ? (i % 2 === 0 ? "#388e3c" : "#1b5e20")
      : (i % 2 === 0 ? "#1e3a5f" : "#0f172a");
    ctx.fillRect(x, y, 3, 6);
  }}
  if (!IS_BR) {{
    ctx.strokeStyle = "rgba(56, 189, 248, 0.35)";
    ctx.lineWidth = 3;
    ctx.strokeRect(0, 0, w, h);
  }}
}}, IS_BR ? 28 : 24, IS_BR ? 28 : 24);

// --- WEB AUDIO SFX ---
let muted = false;
const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
function playSfx(type) {{
  if (muted) return;
  if (audioCtx.state === "suspended") audioCtx.resume();
  const now = audioCtx.currentTime;
  const osc = audioCtx.createOscillator();
  const gain = audioCtx.createGain();
  osc.connect(gain); gain.connect(audioCtx.destination);
  if (type === "ar" || type === "smg") {{
    osc.type = "sawtooth";
    osc.frequency.setValueAtTime(type === "ar" ? 310 : 420, now);
    osc.frequency.exponentialRampToValueAtTime(75, now + 0.08);
    gain.gain.setValueAtTime(0.13, now);
    gain.gain.exponentialRampToValueAtTime(0.001, now + 0.08);
    osc.start(now); osc.stop(now + 0.08);
  }} else if (type === "pump") {{
    osc.type = "square";
    osc.frequency.setValueAtTime(155, now);
    osc.frequency.exponentialRampToValueAtTime(36, now + 0.22);
    gain.gain.setValueAtTime(0.22, now);
    gain.gain.exponentialRampToValueAtTime(0.001, now + 0.22);
    osc.start(now); osc.stop(now + 0.22);
  }} else if (type === "build") {{
    osc.type = "triangle";
    osc.frequency.setValueAtTime(220, now);
    osc.frequency.exponentialRampToValueAtTime(480, now + 0.06);
    gain.gain.setValueAtTime(0.14, now);
    gain.gain.exponentialRampToValueAtTime(0.001, now + 0.06);
    osc.start(now); osc.stop(now + 0.06);
  }} else if (type === "hit") {{
    osc.type = "sine";
    osc.frequency.setValueAtTime(880, now);
    osc.frequency.exponentialRampToValueAtTime(1320, now + 0.06);
    gain.gain.setValueAtTime(0.16, now);
    gain.gain.exponentialRampToValueAtTime(0.001, now + 0.06);
    osc.start(now); osc.stop(now + 0.06);
  }} else if (type === "chest" || type === "shield") {{
    osc.type = "sine";
    osc.frequency.setValueAtTime(440, now);
    osc.frequency.exponentialRampToValueAtTime(880, now + 0.25);
    gain.gain.setValueAtTime(0.16, now);
    gain.gain.exponentialRampToValueAtTime(0.001, now + 0.25);
    osc.start(now); osc.stop(now + 0.25);
  }}
}}

// --- THREE.JS SCENE & SKYBOX ---
const scene = new THREE.Scene();
scene.background = new THREE.Color(IS_BR ? 0x38bdf8 : 0x091122);
scene.fog = new THREE.FogExp2(IS_BR ? 0x7dd3fc : 0x091122, IS_BR ? 0.0042 : 0.0055);

const camera = new THREE.PerspectiveCamera(74, container.clientWidth / container.clientHeight, 0.1, 360);
const renderer = new THREE.WebGLRenderer({{ antialias: true }});
renderer.setSize(container.clientWidth, container.clientHeight);
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.shadowMap.enabled = true;
container.insertBefore(renderer.domElement, container.firstChild);

scene.add(new THREE.HemisphereLight(0xffffff, IS_BR ? 0x365314 : 0x1e293b, 1.05));
const sun = new THREE.DirectionalLight(0xfffbeb, 1.0);
sun.position.set(45, 80, 35);
sun.castShadow = true;
scene.add(sun);

const MAP_HALF = IS_BR ? 80 : 48;
const ground = new THREE.Mesh(
  new THREE.PlaneGeometry(MAP_HALF * 2, MAP_HALF * 2),
  new THREE.MeshStandardMaterial({{ map: TEX_GRASS, roughness: 0.85 }})
);
ground.rotation.x = -Math.PI / 2;
ground.receiveShadow = true;
scene.add(ground);

// Scenic Perimeter Mountains + Clouds
for (let i = 0; i < 20; i++) {{
  const a = (i / 20) * Math.PI * 2;
  const dist = MAP_HALF + 28 + (i % 3) * 14;
  const h = 24 + (i % 4) * 12;
  const mtn = new THREE.Mesh(
    new THREE.ConeGeometry(26, h, 6),
    new THREE.MeshStandardMaterial({{ color: IS_BR ? 0x475569 : 0x1e293b, roughness: 0.95 }})
  );
  mtn.position.set(Math.cos(a) * dist, h / 2 - 2, Math.sin(a) * dist);
  scene.add(mtn);

  const cloud = new THREE.Mesh(
    new THREE.BoxGeometry(14, 3, 8),
    new THREE.MeshBasicMaterial({{ color: IS_BR ? 0xffffff : 0x38bdf8, transparent: true, opacity: IS_BR ? 0.75 : 0.18 }})
  );
  cloud.position.set(Math.cos(a + 0.2) * (dist - 20), 46 + (i % 3) * 6, Math.sin(a + 0.2) * (dist - 20));
  scene.add(cloud);
}}

// Storm Cylinder
let stormRadius = IS_BR ? 78 : 999;
const stormMesh = new THREE.Mesh(
  new THREE.CylinderGeometry(1, 1, 60, 48, 1, true),
  new THREE.MeshBasicMaterial({{ color: 0xa855f7, transparent: true, opacity: 0.28, side: THREE.DoubleSide }})
);
stormMesh.position.y = 30;
stormMesh.scale.set(stormRadius, 1, stormRadius);
stormMesh.visible = false;
scene.add(stormMesh);

// --- BR ISLAND PROPS ---
const harvestNodes = [];
const chests = [];
if (IS_BR) {{
  const towerSpots = [[-22, -22], [24, -18], [-18, 26], [22, 24], [0, 0]];
  towerSpots.forEach(([tx, tz], idx) => {{
    const h = idx === 4 ? 10 : 6.5;
    const bldg = new THREE.Mesh(
      new THREE.BoxGeometry(8, h, 8),
      new THREE.MeshStandardMaterial({{ map: idx % 2 === 0 ? TEX_BRICK : TEX_METAL, roughness: 0.75 }})
    );
    bldg.position.set(tx, h / 2, tz);
    bldg.castShadow = true; bldg.receiveShadow = true;
    scene.add(bldg);
    harvestNodes.push({{ mesh: bldg, x: tx, z: tz, radius: 4.5, hp: 350, matType: "brick", isBuilding: true, height: h }});
  }});

  for (let i = 0; i < 34; i++) {{
    const angle = (i / 34) * Math.PI * 2 + (i % 3) * 0.2;
    const dist = 12 + (i * 19) % 58;
    const px = Math.cos(angle) * dist;
    const pz = Math.sin(angle) * dist;
    if (i % 3 === 0) {{
      const rock = new THREE.Mesh(
        new THREE.DodecahedronGeometry(1.5, 0),
        new THREE.MeshStandardMaterial({{ color: 0x64748b, roughness: 0.9 }})
      );
      rock.position.set(px, 1.1, pz); rock.castShadow = true;
      scene.add(rock);
      harvestNodes.push({{ mesh: rock, x: px, z: pz, radius: 1.6, hp: 90, matType: "brick" }});
    }} else {{
      const tree = new THREE.Group();
      const trunk = new THREE.Mesh(new THREE.CylinderGeometry(0.35, 0.5, 3.2, 8), new THREE.MeshStandardMaterial({{ map: TEX_WOOD }}));
      trunk.position.y = 1.6;
      const leaves = new THREE.Mesh(new THREE.ConeGeometry(2.1, 4.2, 8), new THREE.MeshStandardMaterial({{ color: 0x15803d }}));
      leaves.position.y = 4.2;
      tree.add(trunk, leaves);
      tree.position.set(px, 0, pz);
      scene.add(tree);
      harvestNodes.push({{ mesh: tree, x: px, z: pz, radius: 1.2, hp: 90, matType: "wood" }});
    }}
  }}

  const chestSpots = [
    [-22, -16], [24, -12], [-18, 32], [22, 30], [0, 6],
    [-42, 0], [42, 0], [0, -42], [0, 42], [-35, -35], [35, 35], [-35, 35], [35, -35]
  ];
  chestSpots.forEach(([cx, cz], idx) => {{
    const g = new THREE.Group();
    const box = new THREE.Mesh(
      new THREE.BoxGeometry(1.3, 0.85, 0.9),
      new THREE.MeshStandardMaterial({{ color: 0xfacc15, emissive: 0xca8a04, emissiveIntensity: 0.6, metalness: 0.45 }})
    );
    box.position.y = 0.42;
    g.add(box);
    g.position.set(cx, 0, cz);
    scene.add(g);
    chests.push({{ id: idx, mesh: g, x: cx, z: cz, opened: false }});
  }});
}}

// --- BUILDING & 3x3 EDIT SYSTEM WITH TEXTURES ---
const CELL = 4.0;
const WALL_H = 3.2;
const builds = new Map();
const MAT_TEX = {{ wood: TEX_WOOD, brick: TEX_BRICK, metal: TEX_METAL }};

function buildWorldPos(type, gx, gy, gz, rot) {{
  const cx = gx * CELL, cz = gz * CELL;
  if (type === "floor" || type === "cone") return new THREE.Vector3(cx, gy * WALL_H + 0.1, cz);
  if (type === "ramp") return new THREE.Vector3(cx, gy * WALL_H + WALL_H * 0.5, cz);
  const off = CELL * 0.5;
  if (rot === 0) return new THREE.Vector3(cx, gy * WALL_H + WALL_H * 0.5, cz - off);
  if (rot === 1) return new THREE.Vector3(cx + off, gy * WALL_H + WALL_H * 0.5, cz);
  if (rot === 2) return new THREE.Vector3(cx, gy * WALL_H + WALL_H * 0.5, cz + off);
  return new THREE.Vector3(cx - off, gy * WALL_H + WALL_H * 0.5, cz);
}}

function makeBuildGroup(type, rot, matName = "wood", mask = [1,1,1,1,1,1,1,1,1], isPreview = false) {{
  const group = new THREE.Group();
  const mat = isPreview
    ? new THREE.MeshStandardMaterial({{ color: 0x38bdf8, emissive: 0x0284c7, emissiveIntensity: 0.55, transparent: true, opacity: 0.45 }})
    : new THREE.MeshStandardMaterial({{ map: MAT_TEX[matName] || TEX_WOOD, roughness: 0.7 }});

  if (type === "wall") {{
    const pw = CELL / 3, ph = WALL_H / 3;
    for (let r = 0; r < 3; r++) {{
      for (let c = 0; c < 3; c++) {{
        if (!mask[r * 3 + c]) continue;
        const pane = new THREE.Mesh(new THREE.BoxGeometry(pw * 0.99, ph * 0.99, 0.24), mat);
        pane.position.set((c - 1) * pw, (1 - r) * ph, 0);
        pane.castShadow = !isPreview; pane.receiveShadow = !isPreview;
        group.add(pane);
      }}
    }}
    group.rotation.y = rot * (Math.PI / 2);
  }} else if (type === "floor") {{
    const pw = CELL / 3;
    for (let r = 0; r < 3; r++) {{
      for (let c = 0; c < 3; c++) {{
        if (!mask[r * 3 + c]) continue;
        const tile = new THREE.Mesh(new THREE.BoxGeometry(pw * 0.99, 0.22, pw * 0.99), mat);
        tile.position.set((c - 1) * pw, 0, (r - 1) * pw);
        tile.castShadow = !isPreview; tile.receiveShadow = !isPreview;
        group.add(tile);
      }}
    }}
  }} else if (type === "ramp") {{
    const mesh = new THREE.Mesh(new THREE.BoxGeometry(CELL, 0.22, 5.1225), mat);
    mesh.castShadow = !isPreview; mesh.receiveShadow = !isPreview;
    group.add(mesh);
    group.rotation.order = "YXZ";
    group.rotation.y = rot * (Math.PI / 2);
    group.rotation.x = -Math.atan2(WALL_H, CELL);
  }} else if (type === "cone") {{
    const cone = new THREE.Mesh(new THREE.ConeGeometry(CELL * 0.7, WALL_H * 0.85, 4), mat);
    cone.position.y = WALL_H * 0.42;
    cone.rotation.y = Math.PI / 4;
    cone.castShadow = !isPreview; cone.receiveShadow = !isPreview;
    group.add(cone);
  }}
  return group;
}}

function addOrUpdateBuild(b, broadcast = false) {{
  const rotNorm = (b.type === "floor" || b.type === "cone") ? 0 : b.rot;
  const key = `${{b.type}}_${{b.gx}}_${{b.gy}}_${{b.gz}}_${{rotNorm}}`;
  if (builds.has(key) && !b.forceReplace) return;
  if (builds.has(key)) scene.remove(builds.get(key).group);
  const mask = b.mask || [1,1,1,1,1,1,1,1,1];
  const group = makeBuildGroup(b.type, rotNorm, b.mat || "wood", mask, false);
  group.position.copy(buildWorldPos(b.type, b.gx, b.gy, b.gz, rotNorm));
  group.children.forEach(ch => {{ ch.userData.buildKey = key; }});
  scene.add(group);
  const record = {{ ...b, rot: rotNorm, key, mask, hp: b.hp || 150, group }};
  builds.set(key, record);
  if (broadcast) {{
    playSfx("build");
    netSend({{ t: "build", b: {{ type: b.type, gx: b.gx, gy: b.gy, gz: b.gz, rot: rotNorm, mat: b.mat || "wood", mask, hp: record.hp, forceReplace: !!b.forceReplace }} }});
  }}
}}

function damageBuild(key, dmg, broadcast = true) {{
  const b = builds.get(key);
  if (!b) return;
  b.hp -= dmg;
  if (b.hp <= 0) {{ scene.remove(b.group); builds.delete(key); }}
  if (broadcast) netSend({{ t: "dmg_build", key, dmg }});
}}

function build1v1StarterArena() {{
  builds.forEach(b => scene.remove(b.group));
  builds.clear();
  if (!IS_BR) {{
    addOrUpdateBuild({{ type: "floor", gx: 0, gy: 0, gz: 0, rot: 0, mat: "metal", hp: 9999 }}, false);
    addOrUpdateBuild({{ type: "ramp", gx: 0, gy: 0, gz: -1, rot: 2, mat: "wood", hp: 400 }}, false);
    addOrUpdateBuild({{ type: "ramp", gx: 0, gy: 0, gz: 1, rot: 0, mat: "wood", hp: 400 }}, false);
  }}
}}
build1v1StarterArena();

// --- ANIMATED 3D CHARACTERS ---
let matchStarted = false;
const SPAWNS_1V1 = [[0, -6, 0], [0, 6, Math.PI], [-6, 0, -Math.PI/2], [6, 0, Math.PI/2]];
const SPAWNS_BR  = [[-30, -30, 0], [30, 30, Math.PI], [-30, 30, 0], [30, -30, Math.PI], [0, -38, 0], [0, 38, Math.PI], [-38, 0, 0], [38, 0, Math.PI]];
const initSp = (IS_BR ? SPAWNS_BR : SPAWNS_1V1)[CFG.slotIdx % 4];

const me = {{
  id: CFG.myPid,
  name: CFG.myName,
  color: CFG.myColor,
  x: initSp[0], y: 0, z: initSp[1],
  vy: 0, yaw: initSp[2], pitch: 0.12,
  hp: 100, shield: IS_BR ? 0 : 100, alive: true,
  gliding: false,
  mode: "ar", buildRot: 0,
  mats: {{ wood: IS_BR ? 60 : 999, brick: IS_BR ? 30 : 999, metal: IS_BR ? 0 : 999 }},
  pots: IS_BR ? 1 : 2,
  wins: 0,
  lastShot: 0,
  walkPhase: 0
}};

function createAvatar(colorHex) {{
  const g = new THREE.Group();
  const suitMat = new THREE.MeshStandardMaterial({{ color: colorHex, roughness: 0.35 }});
  const darkMat = new THREE.MeshStandardMaterial({{ color: 0x0f172a, roughness: 0.5 }});
  const visorMat = new THREE.MeshStandardMaterial({{ color: 0x38bdf8, emissive: 0x0284c7, emissiveIntensity: 0.6 }});

  // Legs
  const legL = new THREE.Mesh(new THREE.BoxGeometry(0.26, 0.72, 0.28), darkMat);
  legL.position.set(-0.2, 0.36, 0); legL.castShadow = true; g.add(legL);
  const legR = new THREE.Mesh(new THREE.BoxGeometry(0.26, 0.72, 0.28), darkMat);
  legR.position.set(0.2, 0.36, 0); legR.castShadow = true; g.add(legR);

  // Torso + Backpack
  const body = new THREE.Mesh(new THREE.BoxGeometry(0.76, 0.88, 0.44), suitMat);
  body.position.y = 1.15; body.castShadow = true; g.add(body);
  const pack = new THREE.Mesh(new THREE.BoxGeometry(0.5, 0.62, 0.24), darkMat);
  pack.position.set(0, 1.18, 0.32); g.add(pack);

  // Head + Visor
  const head = new THREE.Mesh(new THREE.BoxGeometry(0.52, 0.52, 0.52), suitMat);
  head.position.y = 1.88; head.castShadow = true; g.add(head);
  const visor = new THREE.Mesh(new THREE.BoxGeometry(0.46, 0.16, 0.08), visorMat);
  visor.position.set(0, 1.9, -0.25); g.add(visor);

  // Weapon
  const gun = new THREE.Mesh(new THREE.BoxGeometry(0.16, 0.18, 0.82), darkMat);
  gun.position.set(0.46, 1.25, -0.35); g.add(gun);

  // Glider
  const glider = new THREE.Mesh(new THREE.BoxGeometry(2.8, 0.12, 1.15), new THREE.MeshStandardMaterial({{ color: 0xfacc15 }}));
  glider.position.set(0, 2.55, 0); glider.visible = false; g.add(glider);

  g.userData = {{ legL, legR, glider }};
  return g;
}}

const myAvatar = createAvatar(me.color);
scene.add(myAvatar);

const remotes = new Map();
function upsertRemote(p) {{
  if (p.id === me.id) return;
  let r = remotes.get(p.id);
  if (!r) {{
    const mesh = createAvatar(p.color || "#38bdf8");
    scene.add(mesh);
    const labelEl = document.createElement("div");
    labelEl.className = "nametag";
    labelsDiv.appendChild(labelEl);
    r = {{ ...p, mesh, labelEl, walkPhase: 0 }};
    remotes.set(p.id, r);
    updateRosterUI();
  }}
  const movedDist = Math.hypot((p.x - r.x) || 0, (p.z - r.z) || 0);
  if (movedDist > 0.02) r.walkPhase += 0.35;
  Object.assign(r, p);
  r.mesh.visible = r.alive;
  r.mesh.userData.glider.visible = !!r.gliding;
  r.mesh.userData.legL.rotation.x = Math.sin(r.walkPhase) * 0.55;
  r.mesh.userData.legR.rotation.x = -Math.sin(r.walkPhase) * 0.55;
  r.labelEl.style.display = r.alive ? "block" : "none";
  r.mesh.position.set(r.x, r.y, r.z);
  r.mesh.rotation.y = r.yaw;
  r.labelEl.innerHTML = `${{r.name}} · ❤️${{Math.ceil(r.hp)}} 🛡️${{Math.ceil(r.shield)}}`;
}}

function updateRosterUI() {{
  const box = document.getElementById("roster-list");
  let html = `<div class="roster-item" style="color:#4ade80;">★ ${{me.name}} (You)</div>`;
  remotes.forEach(r => {{
    html += `<div class="roster-item">🟢 ${{r.name}}</div>`;
  }});
  box.innerHTML = html;
}}
updateRosterUI();

// --- BOT ---
let botEnabled = false, botState = null;
function toggleBot() {{
  botEnabled = !botEnabled;
  if (botEnabled) {{
    botState = {{
      id: "BOT_1", name: "🤖 Sweat Bot", color: "#10b981",
      x: 0, y: 0, z: 6, vy: 0, yaw: Math.PI, hp: 100, shield: 100, alive: true,
      dirTimer: 0, moveAngle: Math.PI, shootTimer: 0, buildTimer: 0
    }};
    upsertRemote(botState);
  }} else if (botState) {{
    remotes.delete("BOT_1");
    scene.remove(botState.mesh);
    botState.labelEl.remove();
    botState = null;
    updateRosterUI();
  }}
}}

// --- TRACERS & HITMARKER ---
const tracers = [];
function spawnTracer(from, to, color = 0xfacc15) {{
  const line = new THREE.Line(
    new THREE.BufferGeometry().setFromPoints([from, to]),
    new THREE.LineBasicMaterial({{ color }})
  );
  scene.add(line);
  tracers.push({{ line, life: 0.12 }});
}}
function flashHitmarker() {{
  playSfx("hit");
  const hm = document.getElementById("hitmarker");
  hm.style.opacity = "1";
  setTimeout(() => {{ hm.style.opacity = "0"; }}, 110);
}}

// --- FULLSCREEN, POINTER LOCK & TOUCH CONTROLS ---
let mouseSens = 1.0;
document.getElementById("sens-slider").addEventListener("input", e => {{
  mouseSens = parseFloat(e.target.value);
}});

document.getElementById("fs-btn").addEventListener("click", () => {{
  if (!document.fullscreenElement) {{
    if (container.requestFullscreen) container.requestFullscreen();
    else if (container.webkitRequestFullscreen) container.webkitRequestFullscreen();
  }} else {{
    if (document.exitFullscreen) document.exitFullscreen();
  }}
}});

function requestMouseCapture() {{
  if (renderer.domElement.requestPointerLock) {{
    try {{ renderer.domElement.requestPointerLock(); }} catch (e) {{}}
  }}
}}
document.getElementById("lock-btn").addEventListener("click", requestMouseCapture);
renderer.domElement.addEventListener("click", () => {{
  if (isPlaying && !editingBuild && !pointerLocked) requestMouseCapture();
}});

let touchUIActive = ('ontouchstart' in window) || (navigator.maxTouchPoints > 0);
const touchLayer = document.getElementById("touch-layer");
const touchToggleBtn = document.getElementById("touch-toggle-btn");
function syncTouchUI() {{
  touchLayer.style.display = touchUIActive ? "block" : "none";
  touchToggleBtn.classList.toggle("active", touchUIActive);
}}
syncTouchUI();
touchToggleBtn.addEventListener("click", () => {{ touchUIActive = !touchUIActive; syncTouchUI(); }});

// Virtual Left Joystick
let joyX = 0, joyY = 0;
const joyZone = document.getElementById("joy-zone");
const joyKnob = document.getElementById("joy-knob");
joyZone.addEventListener("touchmove", e => {{
  e.preventDefault();
  const rect = joyZone.getBoundingClientRect();
  const t = e.touches[0];
  const dx = t.clientX - (rect.left + rect.width / 2);
  const dy = t.clientY - (rect.top + rect.height / 2);
  const maxR = 42;
  const dist = Math.min(maxR, Math.hypot(dx, dy));
  const ang = Math.atan2(dy, dx);
  const kx = Math.cos(ang) * dist;
  const ky = Math.sin(ang) * dist;
  joyKnob.style.transform = `translate(${{kx}}px, ${{ky}}px)`;
  joyX = kx / maxR;
  joyY = -ky / maxR;
}}, {{ passive: false }});
joyZone.addEventListener("touchend", () => {{
  joyX = 0; joyY = 0;
  joyKnob.style.transform = "translate(0px, 0px)";
}});

// Right-Side Touch Drag Camera Look
let lookTouchId = null, lastTouchX = 0, lastTouchY = 0;
const lookZone = document.getElementById("look-zone");
lookZone.addEventListener("touchstart", e => {{
  const t = e.changedTouches[0];
  lookTouchId = t.identifier;
  lastTouchX = t.clientX; lastTouchY = t.clientY;
}}, {{ passive: true }});
lookZone.addEventListener("touchmove", e => {{
  e.preventDefault();
  for (const t of e.changedTouches) {{
    if (t.identifier === lookTouchId) {{
      me.yaw -= (t.clientX - lastTouchX) * 0.0065 * mouseSens;
      me.pitch = Math.max(-0.85, Math.min(1.05, me.pitch + (t.clientY - lastTouchY) * 0.0055 * mouseSens));
      lastTouchX = t.clientX; lastTouchY = t.clientY;
    }}
  }}
}}, {{ passive: false }});

// Touch Action Buttons
let touchFireHeld = false, touchJumpHeld = false;
document.getElementById("t-fire").addEventListener("touchstart", e => {{ e.preventDefault(); touchFireHeld = true; triggerPrimaryAction(); }});
document.getElementById("t-fire").addEventListener("touchend", () => {{ touchFireHeld = false; }});
document.getElementById("t-jump").addEventListener("touchstart", e => {{ e.preventDefault(); touchJumpHeld = true; }});
document.getElementById("t-jump").addEventListener("touchend", () => {{ touchJumpHeld = false; }});
document.getElementById("t-ads").addEventListener("touchstart", e => {{ e.preventDefault(); adsZoom = !adsZoom; }});
document.getElementById("t-edit").addEventListener("touchstart", e => {{ e.preventDefault(); toggleEditMode(); }});

// --- INPUT & LOBBY FLOW ---
const keys = {{}};
let mouseDown = false, isPlaying = false, pointerLocked = false, adsZoom = false;
let editingBuild = null, editMaskDraft = [];

function closeLobbyOverlay() {{
  lobbyPanel.style.display = "none";
  isPlaying = true;
  if (!touchUIActive) requestMouseCapture();
}}

document.getElementById("warmup-btn").addEventListener("click", closeLobbyOverlay);
document.getElementById("lobby-open-btn").addEventListener("click", () => {{
  isPlaying = false;
  if (document.pointerLockElement) document.exitPointerLock();
  updateRosterUI();
  lobbyPanel.style.display = "flex";
}});
document.getElementById("bot-btn").addEventListener("click", () => {{
  if (!botEnabled) toggleBot();
  closeLobbyOverlay();
}});
document.getElementById("start-match-btn").addEventListener("click", () => {{
  startOfficialMatch(true);
  closeLobbyOverlay();
}});

function startOfficialMatch(broadcast = false) {{
  matchStarted = true;
  document.getElementById("phase-txt").textContent = "LIVE MATCH";
  if (IS_BR) {{
    stormRadius = 78;
    stormMesh.visible = true;
    const rsp = SPAWNS_BR[CFG.slotIdx % SPAWNS_BR.length];
    me.x = rsp[0]; me.y = 42; me.z = rsp[1]; me.yaw = rsp[2]; me.gliding = true;
    me.hp = 100; me.shield = 0; me.alive = true; myAvatar.visible = true;
  }} else {{
    reset1v1Round(false);
  }}
  if (broadcast) netSend({{ t: "start_match" }});
}}

document.addEventListener("pointerlockchange", () => {{
  pointerLocked = (document.pointerLockElement === renderer.domElement);
  document.getElementById("lock-btn").classList.toggle("active", pointerLocked);
  document.getElementById("lock-btn").textContent = pointerLocked ? "🔒 Mouse Locked" : "🖱️ Lock Mouse";
}});

let lastMouseX = null, lastMouseY = null;
window.addEventListener("mousemove", e => {{
  if (!isPlaying || editingBuild || touchUIActive) return;
  const sens = (adsZoom ? 0.0014 : 0.0023) * mouseSens;
  if (pointerLocked) {{
    me.yaw -= e.movementX * sens;
    me.pitch = Math.max(-0.85, Math.min(1.05, me.pitch + e.movementY * sens));
  }} else if (lastMouseX !== null) {{
    me.yaw -= (e.clientX - lastMouseX) * sens * 1.25;
    me.pitch = Math.max(-0.85, Math.min(1.05, me.pitch + (e.clientY - lastMouseY) * sens * 1.1));
  }}
  lastMouseX = e.clientX; lastMouseY = e.clientY;
}});

window.addEventListener("mousedown", e => {{
  if (!isPlaying || !me.alive || editingBuild) return;
  if (e.target.closest(".slot") || e.target.closest("button") || e.target.closest("#touch-layer")) return;
  if (e.button === 2) adsZoom = true;
  if (e.button === 0) {{ mouseDown = true; triggerPrimaryAction(); }}
}});
window.addEventListener("mouseup", e => {{
  if (e.button === 2) adsZoom = false;
  if (e.button === 0) mouseDown = false;
}});
window.addEventListener("contextmenu", e => e.preventDefault());

window.addEventListener("keydown", e => {{
  keys[e.code] = true;
  if (e.code === "Digit1") setMode("ar");
  if (e.code === "Digit2") setMode("pump");
  if (e.code === "Digit3") setMode("smg");
  if (e.code === "Digit4") setMode("pick");
  if (e.code === "Digit5") setMode("pot");
  if (e.code === "KeyQ") setMode("wall");
  if (e.code === "KeyE") setMode("ramp");
  if (e.code === "KeyC") setMode("floor");
  if (e.code === "KeyV") setMode("cone");
  if (e.code === "KeyR") me.buildRot = (me.buildRot + 1) % 4;
  if (e.code === "KeyB") toggleBot();
  if (e.code === "KeyX" && !IS_BR) reset1v1Round(true);
  if (e.code === "KeyM") muted = !muted;
  if (e.code === "KeyF" && IS_BR) tryOpenNearbyChest();
  if (e.code === "KeyG") toggleEditMode();
}});
window.addEventListener("keyup", e => {{ keys[e.code] = false; }});

document.querySelectorAll(".slot").forEach(el => {{
  el.addEventListener("click", () => setMode(el.dataset.mode));
}});
function setMode(m) {{
  me.mode = m;
  document.querySelectorAll(".slot").forEach(el => el.classList.toggle("active", el.dataset.mode === m));
}}

// --- 3x3 BUILD EDITING [G] ---
function toggleEditMode() {{
  if (editingBuild) {{
    addOrUpdateBuild({{ ...editingBuild, mask: editMaskDraft, forceReplace: true }}, true);
    editingBuild = null;
    document.getElementById("edit-modal").style.display = "none";
    return;
  }}
  const ray = new THREE.Raycaster();
  ray.setFromCamera(new THREE.Vector2(0, 0), camera);
  const meshes = [];
  builds.forEach(b => {{ if (b.type === "wall" || b.type === "floor") meshes.push(...b.group.children); }});
  const hits = ray.intersectObjects(meshes, false);
  if (hits.length === 0 || hits[0].distance > 7.5) return;

  const b = builds.get(hits[0].object.userData.buildKey);
  if (!b) return;
  editingBuild = b;
  editMaskDraft = [...b.mask];
  if (document.pointerLockElement) document.exitPointerLock();

  const grid = document.getElementById("edit-grid");
  grid.innerHTML = "";
  editMaskDraft.forEach((val, idx) => {{
    const div = document.createElement("div");
    div.className = "edit-tile" + (val ? "" : " cut");
    div.onclick = () => {{
      editMaskDraft[idx] = editMaskDraft[idx] ? 0 : 1;
      div.classList.toggle("cut", !editMaskDraft[idx]);
    }};
    grid.appendChild(div);
  }});
  document.getElementById("edit-modal").style.display = "block";
}}
document.getElementById("confirm-edit-btn").addEventListener("click", () => {{
  toggleEditMode();
  if (!touchUIActive) requestMouseCapture();
}});

// --- SHOOTING & BUILDING ---
function getPlacementCoords() {{
  const fwd = new THREE.Vector3(-Math.sin(me.yaw), 0, -Math.cos(me.yaw));
  const targetPt = new THREE.Vector3(me.x, me.y + 1.0, me.z).addScaledVector(fwd, 3.3);
  const gx = Math.round(targetPt.x / CELL);
  const gz = Math.round(targetPt.z / CELL);
  const gy = Math.max(0, Math.floor((me.y + 0.5) / WALL_H));
  const cardinal = ((Math.round(-me.yaw / (Math.PI / 2)) % 4) + 4) % 4;
  const rot = me.mode === "ramp" ? (cardinal + me.buildRot) % 4 : cardinal;
  return {{ type: me.mode, gx, gy, gz, rot }};
}}

function consumeMat() {{
  if (!IS_BR) return "wood";
  if (me.mats.wood >= 10) {{ me.mats.wood -= 10; return "wood"; }}
  if (me.mats.brick >= 10) {{ me.mats.brick -= 10; return "brick"; }}
  if (me.mats.metal >= 10) {{ me.mats.metal -= 10; return "metal"; }}
  return null;
}}

function triggerPrimaryAction() {{
  const now = performance.now();
  if (["wall", "ramp", "floor", "cone"].includes(me.mode)) {{
    const p = getPlacementCoords();
    const key = `${{p.type}}_${{p.gx}}_${{p.gy}}_${{p.gz}}_${{(p.type === "floor" || p.type === "cone") ? 0 : p.rot}}`;
    if (builds.has(key)) return;
    const matUsed = consumeMat();
    if (!matUsed) return;
    addOrUpdateBuild({{ ...p, mat: matUsed }}, true);
    return;
  }}

  if (me.mode === "pot") {{
    if (me.pots > 0 && me.shield < 100) {{
      me.pots--;
      me.shield = Math.min(100, me.shield + 50);
      playSfx("shield");
    }}
    return;
  }}

  const cooldowns = {{ ar: 145, pump: 780, smg: 85, pick: 360 }};
  if (now - me.lastShot < cooldowns[me.mode]) return;
  me.lastShot = now;
  playSfx(me.mode === "pick" ? "build" : me.mode);

  const maxRange = me.mode === "pick" ? 4.4 : 95;
  const dmgs = {{ ar: 30, pump: 110, smg: 19, pick: 65 }};
  const dmg = dmgs[me.mode];

  const ray = new THREE.Raycaster();
  ray.setFromCamera(new THREE.Vector2(0, 0), camera);
  const muzzle = new THREE.Vector3(me.x, me.y + 1.45, me.z);
  let endPt = ray.ray.origin.clone().addScaledVector(ray.ray.direction, maxRange);

  const buildMeshes = [];
  builds.forEach(b => buildMeshes.push(...b.group.children));
  const bHits = ray.intersectObjects(buildMeshes, false);
  let closestDist = maxRange;
  let hitBuildKey = null;

  if (bHits.length > 0 && bHits[0].distance < closestDist) {{
    closestDist = bHits[0].distance;
    endPt = bHits[0].point;
    hitBuildKey = bHits[0].object.userData.buildKey;
  }}

  let hitTarget = null;
  remotes.forEach(r => {{
    if (!r.alive) return;
    const pHits = ray.intersectObjects(r.mesh.children, false);
    if (pHits.length > 0 && pHits[0].distance < closestDist) {{
      closestDist = pHits[0].distance;
      endPt = pHits[0].point;
      hitTarget = r;
      hitBuildKey = null;
    }}
  }});

  if (me.mode !== "pick") {{
    spawnTracer(muzzle, endPt, me.mode === "pump" ? 0xf97316 : 0xfacc15);
    netSend({{ t: "tracer", from: muzzle.toArray(), to: endPt.toArray() }});
  }}

  if (hitTarget) {{
    flashHitmarker();
    if (hitTarget.id === "BOT_1" && botState) applyDamageToBot(dmg);
    else netSend({{ t: "hit", targetId: hitTarget.id, dmg, fromName: me.name }});
  }} else if (hitBuildKey) {{
    damageBuild(hitBuildKey, dmg, true);
  }} else if (me.mode === "pick" && IS_BR) {{
    for (const node of harvestNodes) {{
      if (Math.hypot(me.x - node.x, me.z - node.z) <= node.radius + 3.2 && node.hp > 0) {{
        node.hp -= 30;
        me.mats[node.matType] += 25;
        flashHitmarker();
        if (node.hp <= 0 && !node.isBuilding) scene.remove(node.mesh);
        break;
      }}
    }}
  }}
}}

function tryOpenNearbyChest() {{
  for (const ch of chests) {{
    if (!ch.opened && Math.hypot(me.x - ch.x, me.z - ch.z) < 3.4) {{
      ch.opened = true; ch.mesh.visible = false;
      playSfx("chest");
      me.mats.wood += 60; me.mats.brick += 40; me.mats.metal += 20; me.pots += 1;
      netSend({{ t: "chest", id: ch.id }});
      break;
    }}
  }}
}}

function reset1v1Round(broadcast = false) {{
  build1v1StarterArena();
  const s = SPAWNS_1V1[CFG.slotIdx % 4];
  me.x = s[0]; me.y = 0; me.z = s[1]; me.vy = 0; me.yaw = s[2];
  me.hp = 100; me.shield = 100; me.alive = true; me.pots = 2;
  myAvatar.visible = true;
  if (botState) {{
    botState.x = 0; botState.y = 0; botState.z = 6;
    botState.hp = 100; botState.shield = 100; botState.alive = true;
  }}
  if (broadcast) netSend({{ t: "reset_1v1" }});
}}

function takeDamage(dmg, attackerName) {{
  if (!me.alive) return;
  if (me.shield > 0) {{
    const absorbed = Math.min(me.shield, dmg);
    me.shield -= absorbed; dmg -= absorbed;
  }}
  me.hp = Math.max(0, me.hp - dmg);
  if (me.hp <= 0) {{
    me.alive = false;
    myAvatar.visible = false;
    netSend({{ t: "elim", victim: me.name, killer: attackerName }});
    if (!IS_BR) {{
      setTimeout(() => reset1v1Round(true), 2000);
    }} else {{
      isPlaying = false;
      document.getElementById("ov-title").textContent = "💀 ELIMINATED";
      document.getElementById("ov-sub").textContent = `Taken out by ${{attackerName}}. Click Warm Up to re-deploy!`;
      lobbyPanel.style.display = "flex";
      me.hp = 100; me.shield = 0; me.alive = true; myAvatar.visible = true;
      const rsp = SPAWNS_BR[Math.floor(Math.random() * SPAWNS_BR.length)];
      me.x = rsp[0]; me.y = 40; me.z = rsp[1]; me.gliding = true;
    }}
  }}
}}

function applyDamageToBot(dmg) {{
  if (!botState || !botState.alive) return;
  if (botState.shield > 0) {{
    const abs = Math.min(botState.shield, dmg);
    botState.shield -= abs; dmg -= abs;
  }}
  botState.hp = Math.max(0, botState.hp - dmg);
  if (botState.hp <= 0) {{
    me.wins++;
    if (!IS_BR) setTimeout(() => reset1v1Round(false), 1800);
    else {{ botState.x = 20; botState.y = 0; botState.z = -20; botState.hp = 100; botState.shield = 100; }}
  }}
}}

// --- PHYSICS & WALK ANIMATION ---
function stepPhysics(dt) {{
  if (!me.alive) return;
  if (keys["ArrowLeft"]) me.yaw += 2.2 * dt;
  if (keys["ArrowRight"]) me.yaw -= 2.2 * dt;

  if (isPlaying && (mouseDown || touchFireHeld) && !editingBuild) {{
    if (["ar", "smg", "wall", "ramp", "floor", "cone"].includes(me.mode)) triggerPrimaryAction();
  }}

  const speed = me.gliding ? 14.5 : (keys["ShiftLeft"] ? 11.5 : 8.5);
  let fwdMove = (keys["KeyW"] ? 1 : 0) - (keys["KeyS"] ? 1 : 0) + joyY;
  let sideMove = (keys["KeyD"] ? 1 : 0) - (keys["KeyA"] ? 1 : 0) + joyX;

  if (Math.hypot(fwdMove, sideMove) > 0.08) {{
    const len = Math.max(1, Math.hypot(fwdMove, sideMove));
    fwdMove /= len; sideMove /= len;
    const sin = Math.sin(me.yaw), cos = Math.cos(me.yaw);
    me.x += (-sin * fwdMove + cos * sideMove) * speed * dt;
    me.z += (-cos * fwdMove - sin * sideMove) * speed * dt;
    me.walkPhase += 11 * dt;
  }} else {{
    me.walkPhase = 0;
  }}

  me.x = Math.max(-MAP_HALF + 2, Math.min(MAP_HALF - 2, me.x));
  me.z = Math.max(-MAP_HALF + 2, Math.min(MAP_HALF - 2, me.z));

  if (me.gliding) {{
    me.y -= 5.2 * dt;
    if (me.y <= 0) {{ me.y = 0; me.gliding = false; }}
  }} else {{
    me.vy -= 24 * dt;
    me.y += me.vy * dt;
  }}

  myAvatar.userData.glider.visible = me.gliding;
  myAvatar.userData.legL.rotation.x = Math.sin(me.walkPhase) * 0.6;
  myAvatar.userData.legR.rotation.x = -Math.sin(me.walkPhase) * 0.6;

  let supportY = 0;
  if (IS_BR) {{
    for (const node of harvestNodes) {{
      if (node.isBuilding && Math.abs(me.x - node.x) < 4.1 && Math.abs(me.z - node.z) < 4.1) {{
        if (me.y >= node.height - 0.6 && node.height > supportY) supportY = node.height;
      }}
    }}
  }}

  builds.forEach(b => {{
    const cx = b.gx * CELL, cz = b.gz * CELL;
    const dx = me.x - cx, dz = me.z - cz;
    if (Math.abs(dx) <= CELL * 0.52 && Math.abs(dz) <= CELL * 0.52) {{
      if (b.type === "floor") {{
        const sc = Math.min(2, Math.max(0, Math.floor((dx + CELL * 0.5) / (CELL / 3))));
        const sr = Math.min(2, Math.max(0, Math.floor((dz + CELL * 0.5) / (CELL / 3))));
        if (b.mask[sr * 3 + sc]) {{
          const fy = b.gy * WALL_H + 0.21;
          if (me.y >= fy - 0.65 && fy > supportY) supportY = fy;
        }}
      }} else if (b.type === "ramp") {{
        let t = 0.5;
        if (b.rot === 0) t = 0.5 - dz / CELL;
        else if (b.rot === 2) t = 0.5 + dz / CELL;
        else if (b.rot === 1) t = 0.5 + dx / CELL;
        else t = 0.5 - dx / CELL;
        t = Math.max(0, Math.min(1, t));
        const ry = b.gy * WALL_H + t * WALL_H + 0.12;
        if (me.y >= ry - 0.85 && ry > supportY) supportY = ry;
      }} else if (b.type === "cone") {{
        const cy = b.gy * WALL_H + WALL_H * 0.55;
        if (me.y >= cy - 0.8 && cy > supportY) supportY = cy;
      }}
    }}
  }});

  if (!me.gliding && me.y <= supportY) {{
    me.y = supportY;
    me.vy = 0;
    if ((keys["Space"] || touchJumpHeld) && isPlaying) me.vy = 10.0;
  }}

  builds.forEach(b => {{
    if (b.type !== "wall") return;
    const wp = buildWorldPos("wall", b.gx, b.gy, b.gz, b.rot);
    if (me.y + 1.8 < wp.y - WALL_H * 0.5 || me.y > wp.y + WALL_H * 0.5 - 0.2) return;
    const halfX = (b.rot % 2 === 0) ? CELL * 0.5 : 0.45;
    const halfZ = (b.rot % 2 === 0) ? 0.45 : CELL * 0.5;
    const dx = me.x - wp.x, dz = me.z - wp.z;
    if (Math.abs(dx) < halfX && Math.abs(dz) < halfZ) {{
      const localX = (b.rot % 2 === 0) ? dx : dz;
      const colIdx = Math.min(2, Math.max(0, Math.floor((localX + CELL * 0.5) / (CELL / 3))));
      if (!b.mask[6 + colIdx] && !b.mask[3 + colIdx]) return;
      if (halfX - Math.abs(dx) < halfZ - Math.abs(dz)) me.x += dx >= 0 ? (halfX - Math.abs(dx)) : -(halfX - Math.abs(dx));
      else me.z += dz >= 0 ? (halfZ - Math.abs(dz)) : -(halfZ - Math.abs(dz));
    }}
  }});

  myAvatar.position.set(me.x, me.y, me.z);
  myAvatar.rotation.y = me.yaw;
}}

function stepBot(dt) {{
  if (!botEnabled || !botState || !botState.alive) return;
  botState.dirTimer -= dt;
  if (botState.dirTimer <= 0) {{
    botState.dirTimer = 1.1 + Math.random() * 1.1;
    botState.moveAngle = Math.atan2(me.x - botState.x, me.z - botState.z) + (Math.random() - 0.5) * 1.4;
    if (Math.random() < 0.5 && botState.y <= 0.1) botState.vy = 9.5;
  }}
  botState.x += Math.sin(botState.moveAngle) * 5.6 * dt;
  botState.z += Math.cos(botState.moveAngle) * 5.6 * dt;
  botState.x = Math.max(-35, Math.min(35, botState.x));
  botState.z = Math.max(-35, Math.min(35, botState.z));
  botState.vy -= 24 * dt;
  botState.y = Math.max(0, botState.y + botState.vy * dt);
  botState.yaw = Math.atan2(-(me.x - botState.x), -(me.z - botState.z));

  botState.buildTimer -= dt;
  if (botState.buildTimer <= 0) {{
    botState.buildTimer = 2.4;
    const gx = Math.round(botState.x / CELL), gz = Math.round(botState.z / CELL);
    const rot = ((Math.round(-botState.yaw / (Math.PI / 2)) % 4) + 4) % 4;
    addOrUpdateBuild({{ type: Math.random() < 0.6 ? "wall" : "ramp", gx, gy: 0, gz, rot, mat: "wood" }}, false);
  }}
  botState.shootTimer -= dt;
  if (botState.shootTimer <= 0 && me.alive) {{
    botState.shootTimer = 1.25;
    spawnTracer(new THREE.Vector3(botState.x, botState.y + 1.4, botState.z), new THREE.Vector3(me.x, me.y + 1.2, me.z), 0x10b981);
    if (Math.random() < 0.42) takeDamage(16, "🤖 Sweat Bot");
  }}
  upsertRemote(botState);
}}

// --- RESILIENT WEBRTC P2P MULTIPLAYER WITH STUN & AUTO-RECONNECT ---
const ICE_CFG = {{
  iceServers: [
    {{ urls: "stun:stun.l.google.com:19302" }},
    {{ urls: "stun:stun1.l.google.com:19302" }}
  ]
}};
const hostPeerId = `shs-arcade-${{CFG.mode}}-${{CFG.roomCode}}-HOST`;
const peer = CFG.isHost
  ? new Peer(hostPeerId, {{ config: ICE_CFG }})
  : new Peer(undefined, {{ config: ICE_CFG }});

const conns = new Map();
let hostConn = null;

function handleNetData(data, senderConn) {{
  if (CFG.isHost) {{
    conns.forEach((c, pid) => {{ if (pid !== senderConn.peer && c.open) c.send(data); }});
  }}
  if (data.t === "state") upsertRemote(data.p);
  else if (data.t === "build") addOrUpdateBuild(data.b, false);
  else if (data.t === "dmg_build") damageBuild(data.key, data.dmg, false);
  else if (data.t === "tracer") spawnTracer(new THREE.Vector3(...data.from), new THREE.Vector3(...data.to));
  else if (data.t === "hit" && data.targetId === me.id) takeDamage(data.dmg, data.fromName);
  else if (data.t === "reset_1v1") reset1v1Round(false);
  else if (data.t === "start_match") {{ startOfficialMatch(false); closeLobbyOverlay(); }}
  else if (data.t === "chest") {{
    const ch = chests.find(c => c.id === data.id);
    if (ch) {{ ch.opened = true; ch.mesh.visible = false; }}
  }}
  else if (data.t === "elim" && data.killer === me.name) me.wins++;
}}

function wireConn(conn) {{
  conn.on("open", () => {{
    conns.set(conn.peer, conn);
    document.getElementById("net-status").textContent = `🟢 Connected (${{conns.size + 1}} in room)`;
    updateRosterUI();
    if (CFG.isHost) {{
      builds.forEach(b => conn.send({{ t: "build", b: {{ type: b.type, gx: b.gx, gy: b.gy, gz: b.gz, rot: b.rot, mat: b.mat, mask: b.mask, hp: b.hp }} }}));
    }}
  }});
  conn.on("data", data => handleNetData(data, conn));
  conn.on("close", () => {{
    conns.delete(conn.peer);
    document.getElementById("net-status").textContent = `🟡 Reconnecting... (${{conns.size + 1}} in room)`;
  }});
}}

function netSend(payload) {{
  conns.forEach(c => {{ if (c.open) c.send(payload); }});
}}

peer.on("open", () => {{
  document.getElementById("net-status").textContent = CFG.isHost
    ? "🟢 Hosting Lobby (waiting for friend)"
    : "🟡 Searching for Host...";
  if (!CFG.isHost) {{
    hostConn = peer.connect(hostPeerId, {{ reliable: true }});
    wireConn(hostConn);
  }}
}});
peer.on("connection", conn => wireConn(conn));

// Auto-retry connecting to Host every 2s until connected
if (!CFG.isHost) {{
  setInterval(() => {{
    if (peer.open && (!hostConn || !hostConn.open)) {{
      hostConn = peer.connect(hostPeerId, {{ reliable: true }});
      wireConn(hostConn);
    }}
  }}, 2000);
}}

setInterval(() => {{
  netSend({{
    t: "state",
    p: {{ id: me.id, name: me.name, color: me.color, x: me.x, y: me.y, z: me.z, yaw: me.yaw, hp: me.hp, shield: me.shield, alive: me.alive, gliding: me.gliding }}
  }});
}}, 33);

// --- MINIMAP & MAIN LOOP ---
const mmCanvas = document.getElementById("minimap");
const mmCtx = mmCanvas.getContext("2d");
function drawMinimap() {{
  if (!IS_BR) return;
  mmCtx.clearRect(0, 0, 90, 90);
  mmCtx.fillStyle = "#14532d";
  mmCtx.fillRect(0, 0, 90, 90);
  mmCtx.strokeStyle = "#c084fc";
  mmCtx.lineWidth = 2.5;
  mmCtx.beginPath();
  mmCtx.arc(45, 45, (stormRadius / MAP_HALF) * 43, 0, Math.PI * 2);
  mmCtx.stroke();
  mmCtx.fillStyle = "#facc15";
  mmCtx.beginPath();
  mmCtx.arc(45 + (me.x / MAP_HALF) * 43, 45 + (me.z / MAP_HALF) * 43, 3.5, 0, Math.PI * 2);
  mmCtx.fill();
  mmCtx.fillStyle = "#ef4444";
  remotes.forEach(r => {{
    if (!r.alive) return;
    mmCtx.beginPath();
    mmCtx.arc(45 + (r.x / MAP_HALF) * 43, 45 + (r.z / MAP_HALF) * 43, 3, 0, Math.PI * 2);
    mmCtx.fill();
  }});
}}

let previewGroup = null, previewSig = "";
let lastTime = performance.now(), stormTick = 0;
const projVec = new THREE.Vector3();

function animate(now) {{
  requestAnimationFrame(animate);
  const dt = Math.min(0.05, (now - lastTime) / 1000);
  lastTime = now;

  stepPhysics(dt);
  stepBot(dt);

  if (IS_BR && me.alive) {{
    const nearChest = chests.some(ch => !ch.opened && Math.hypot(me.x - ch.x, me.z - ch.z) < 3.4);
    promptBanner.style.display = nearChest ? "block" : "none";
    if (nearChest) promptBanner.textContent = "Press [F] to Open Golden Chest";
  }}

  if (["wall", "ramp", "floor", "cone"].includes(me.mode) && me.alive && !editingBuild) {{
    const p = getPlacementCoords();
    const sig = `${{p.type}}_${{p.rot}}`;
    if (!previewGroup || previewSig !== sig) {{
      if (previewGroup) scene.remove(previewGroup);
      previewGroup = makeBuildGroup(p.type, p.rot, "wood", [1,1,1,1,1,1,1,1,1], true);
      previewSig = sig;
      scene.add(previewGroup);
    }}
    previewGroup.visible = true;
    previewGroup.position.copy(buildWorldPos(p.type, p.gx, p.gy, p.gz, p.rot));
  }} else if (previewGroup) {{
    previewGroup.visible = false;
  }}

  if (IS_BR && matchStarted) {{
    if (stormRadius > 10) {{
      stormRadius -= 0.45 * dt;
      stormMesh.scale.set(stormRadius, 1, stormRadius);
    }}
    stormTick += dt;
    if (stormTick >= 1.0) {{
      stormTick = 0;
      if (me.alive && Math.hypot(me.x, me.z) > stormRadius) takeDamage(5, "🌪️ The Storm");
    }}
  }}

  for (let i = tracers.length - 1; i >= 0; i--) {{
    tracers[i].life -= dt;
    if (tracers[i].life <= 0) {{ scene.remove(tracers[i].line); tracers.splice(i, 1); }}
  }}

  camera.fov = adsZoom ? 48 : 74;
  camera.updateProjectionMatrix();
  const camDist = me.gliding ? 7.0 : (adsZoom ? 2.5 : 4.6);
  const shoulder = 0.78;
  camera.position.set(
    me.x + Math.cos(me.yaw) * shoulder + Math.sin(me.yaw) * camDist,
    me.y + 2.25 + Math.sin(me.pitch) * 2.2,
    me.z - Math.sin(me.yaw) * shoulder + Math.cos(me.yaw) * camDist
  );
  camera.lookAt(
    me.x + Math.cos(me.yaw) * shoulder - Math.sin(me.yaw) * 6,
    me.y + 1.65 - Math.sin(me.pitch) * 4,
    me.z - Math.sin(me.yaw) * shoulder - Math.cos(me.yaw) * 6
  );

  remotes.forEach(r => {{
    if (!r.alive) return;
    projVec.set(r.x, r.y + 2.4, r.z);
    projVec.project(camera);
    const inFront = projVec.z < 1;
    r.labelEl.style.display = inFront ? "block" : "none";
    if (inFront) {{
      r.labelEl.style.left = `${{(projVec.x * 0.5 + 0.5) * container.clientWidth}}px`;
      r.labelEl.style.top = `${{(-projVec.y * 0.5 + 0.5) * container.clientHeight}}px`;
    }}
  }});

  document.getElementById("hp-num").textContent = Math.ceil(me.hp);
  document.getElementById("hp-fill").style.width = `${{me.hp}}%`;
  document.getElementById("sh-num").textContent = Math.ceil(me.shield);
  document.getElementById("sh-fill").style.width = `${{me.shield}}%`;
  document.getElementById("mat-wood").textContent = me.mats.wood;
  document.getElementById("mat-brick").textContent = me.mats.brick;
  document.getElementById("mat-metal").textContent = me.mats.metal;
  document.getElementById("mat-pots").textContent = me.pots;
  document.getElementById("wins-txt").textContent = me.wins;
  if (IS_BR) document.getElementById("storm-txt").textContent = `${{Math.ceil(stormRadius)}}m`;

  drawMinimap();
  renderer.render(scene, camera);
}}
requestAnimationFrame(animate);
</script>
</body>
</html>
"""
    components.html(html, height=665)
