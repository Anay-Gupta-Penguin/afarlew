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
        "mode": arena_mode,  # "1v1" or "br"
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
<style>
  * {{ box-sizing: border-box; user-select: none; }}
  html, body {{
    margin: 0; padding: 0; overflow: hidden;
    background: #070b14; font-family: system-ui, -apple-system, sans-serif; color: #f8fafc;
  }}
  #game-container {{
    position: relative; width: 100vw; height: 660px; overflow: hidden;
  }}
  #crosshair {{
    position: absolute; top: 50%; left: 50%;
    width: 22px; height: 22px; transform: translate(-50%, -50%);
    pointer-events: none; z-index: 10;
  }}
  #crosshair::before, #crosshair::after {{
    content: ""; position: absolute; background: rgba(255,255,255,0.92);
    box-shadow: 0 0 3px #000;
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

  #top-hud {{
    position: absolute; top: 12px; left: 14px; right: 14px;
    display: flex; justify-content: space-between; align-items: flex-start;
    pointer-events: none; z-index: 12; gap: 10px;
  }}
  .hud-box {{
    background: rgba(15, 23, 42, 0.84);
    border: 1px solid rgba(148, 163, 184, 0.28);
    border-radius: 10px; padding: 8px 13px; font-size: 13px;
    backdrop-filter: blur(4px);
  }}
  #minimap {{
    border-radius: 50%; border: 2px solid #38bdf8;
    background: #0f172a; margin-top: 6px;
  }}
  #kill-feed {{
    text-align: right; max-width: 290px; font-size: 12px; color: #e2e8f0;
  }}
  #prompt-banner {{
    position: absolute; top: 58%; left: 50%; transform: translateX(-50%);
    background: rgba(15, 23, 42, 0.9); border: 1px solid #facc15;
    padding: 6px 14px; border-radius: 8px; font-size: 13px; font-weight: 700;
    color: #fef08a; display: none; z-index: 13; pointer-events: none;
  }}

  #bottom-hud {{
    position: absolute; bottom: 12px; left: 50%; transform: translateX(-50%);
    display: flex; flex-direction: column; align-items: center; gap: 7px;
    pointer-events: none; z-index: 12; width: 95%; max-width: 780px;
  }}
  .mats-row {{
    display: flex; gap: 12px; font-size: 12px; font-weight: 800;
    background: rgba(15, 23, 42, 0.85); padding: 4px 14px; border-radius: 8px;
    border: 1px solid rgba(255,255,255,0.15);
  }}
  .bars {{
    display: flex; gap: 10px; width: 100%; max-width: 400px;
  }}
  .bar-wrap {{
    flex: 1; background: rgba(15, 23, 42, 0.9); border-radius: 8px;
    padding: 4px 8px; border: 1px solid rgba(255,255,255,0.18);
  }}
  .bar-label {{ font-size: 11px; font-weight: 700; display: flex; justify-content: space-between; }}
  .bar-track {{ height: 8px; background: #1e293b; border-radius: 4px; margin-top: 3px; overflow: hidden; }}
  #hp-fill {{ height: 100%; width: 100%; background: #22c55e; transition: width 0.1s; }}
  #sh-fill {{ height: 100%; width: 100%; background: #38bdf8; transition: width 0.1s; }}

  .hotbar {{
    display: flex; gap: 5px; pointer-events: auto; flex-wrap: wrap; justify-content: center;
  }}
  .slot {{
    background: rgba(15, 23, 42, 0.9);
    border: 2px solid rgba(148, 163, 184, 0.35);
    border-radius: 8px; padding: 5px 9px; text-align: center;
    min-width: 68px; cursor: pointer; font-size: 12px; font-weight: 700;
  }}
  .slot.active {{
    border-color: #facc15; background: rgba(250, 204, 21, 0.22); transform: translateY(-3px);
  }}
  .slot span {{ display: block; font-size: 10px; color: #94a3b8; font-weight: 600; }}

  /* 3x3 Build Edit Modal */
  #edit-modal {{
    position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);
    background: rgba(15, 23, 42, 0.94); border: 2px solid #38bdf8;
    border-radius: 14px; padding: 14px; z-index: 18; display: none; text-align: center;
  }}
  #edit-grid {{
    display: grid; grid-template-columns: repeat(3, 54px); gap: 6px; margin: 10px 0;
  }}
  .edit-tile {{
    width: 54px; height: 54px; border-radius: 6px; cursor: pointer;
    background: #2563eb; border: 2px solid #93c5fd;
  }}
  .edit-tile.cut {{
    background: rgba(15, 23, 42, 0.5); border: 2px dashed #475569;
  }}

  #overlay {{
    position: absolute; inset: 0; background: rgba(7, 11, 20, 0.82);
    display: flex; flex-direction: column; align-items: center; justify-content: center;
    z-index: 25; text-align: center; padding: 20px;
  }}
  #overlay h1 {{ margin: 0 0 8px 0; font-size: 32px; }}
  #overlay p {{ margin: 4px 0; color: #cbd5e1; max-width: 560px; font-size: 14px; line-height: 1.45; }}
  .btn-row {{ display: flex; gap: 10px; margin-top: 16px; flex-wrap: wrap; justify-content: center; }}
  button.action-btn {{
    background: #2563eb; color: white; border: none; border-radius: 10px;
    padding: 11px 20px; font-size: 14px; font-weight: 700; cursor: pointer;
  }}
  button.action-btn:hover {{ background: #1d4ed8; }}
  button.bot-btn {{ background: #059669; }}
  button.bot-btn:hover {{ background: #047857; }}
  button.reset-btn {{ background: #d97706; }}
  button.reset-btn:hover {{ background: #b45309; }}

  .nametag {{
    position: absolute; transform: translate(-50%, -100%);
    background: rgba(15, 23, 42, 0.88); padding: 2px 7px; border-radius: 6px;
    font-size: 11px; font-weight: 700; pointer-events: none; white-space: nowrap;
    border: 1px solid rgba(255,255,255,0.22); z-index: 8;
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
      <div id="mode-header"><b>🏗️ 1v1.LOL BUILD FIGHT</b> · Wins: <span id="wins-txt">0</span></div>
      <div style="font-size:12px;margin-top:2px;" id="sub-header">👥 Alive: <span id="alive-txt">1</span> · <span id="net-status">Connecting P2P...</span></div>
      <canvas id="minimap" width="96" height="96" style="display:none;"></canvas>
    </div>
    <div class="hud-box" id="kill-feed">
      <div><b>WASD</b> Move · <b>Space</b> Jump/Glide · <b>Hold Click</b> Shoot / Turbo-Build</div>
      <div><b>1-4</b> Weapons/Shield · <b>Q</b> Wall · <b>E</b> Ramp · <b>C</b> Floor · <b>V</b> Cone · <b>G</b> Edit</div>
      <div id="extra-keys"><b>R</b> Rotate · <b>B</b> Spawn Bot · <b>X</b> Reset Arena · <b>M</b> Mute</div>
    </div>
  </div>

  <div id="edit-modal">
    <div style="font-weight:800;font-size:14px;color:#38bdf8;">✏️ BUILD EDIT (Click squares to open window/door)</div>
    <div id="edit-grid"></div>
    <button class="action-btn" id="confirm-edit-btn" style="padding:6px 16px;font-size:13px;">✅ Confirm [G]</button>
  </div>

  <div id="bottom-hud">
    <div class="mats-row">
      <span>🪵 Wood: <span id="mat-wood">999</span></span>
      <span>🧱 Brick: <span id="mat-brick">999</span></span>
      <span>⚙️ Metal: <span id="mat-metal">999</span></span>
      <span>🧪 Shields: <span id="mat-pots">2</span></span>
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
      <div class="slot active" data-mode="ar">🔫 Gold AR<span>[1]</span></div>
      <div class="slot" data-mode="pump">💥 Pump<span>[2]</span></div>
      <div class="slot" data-mode="smg">⚡ Rapid SMG<span>[3]</span></div>
      <div class="slot" data-mode="pick">⛏️ Pickaxe<span>[4]</span></div>
      <div class="slot" data-mode="pot">🧪 Shield Pot<span>[5]</span></div>
      <div class="slot" data-mode="wall">🧱 Wall<span>[Q]</span></div>
      <div class="slot" data-mode="ramp">📐 Ramp<span>[E]</span></div>
      <div class="slot" data-mode="floor">🟫 Floor<span>[C]</span></div>
      <div class="slot" data-mode="cone">🔺 Cone<span>[V]</span></div>
    </div>
  </div>

  <div id="overlay">
    <h1 id="ov-title">🏗️ 1v1.LOL BUILD FIGHT</h1>
    <p id="ov-sub">Crank 90s with Turbo-Build (<b>Q/E/C/V</b>), edit windows with <b>G</b>, and blast your opponent!</p>
    <div class="btn-row">
      <button class="action-btn" id="play-btn">🎮 Play Now</button>
      <button class="action-btn bot-btn" id="bot-btn">🤖 Play vs. 1v1 Bot</button>
      <button class="action-btn reset-btn" id="reset-btn">🔄 Reset Builds [X]</button>
    </div>
  </div>
</div>

<script>
const CFG = {config};
const IS_BR = (CFG.mode === "br");
const container = document.getElementById("game-container");
const overlay = document.getElementById("overlay");
const labelsDiv = document.getElementById("labels");
const promptBanner = document.getElementById("prompt-banner");

if (IS_BR) {{
  document.getElementById("ov-title").textContent = "🪂 FORTNITE BATTLE ROYALE";
  document.getElementById("ov-sub").textContent = "Glide onto the island, open Golden Chests [F], harvest trees/rocks with your Pickaxe, and outlast the shrinking Storm!";
  document.getElementById("mode-header").innerHTML = `<b>🌪️ STORM:</b> <span id="storm-txt">75m</span> · <b>🏆 Elims:</b> <span id="wins-txt">0</span>`;
  document.getElementById("minimap").style.display = "block";
  document.getElementById("reset-btn").style.display = "none";
  document.getElementById("bot-btn").textContent = "🤖 Spawn Island Bots";
}}

// --- PROCEDURAL WEB AUDIO SFX ---
let muted = false;
const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
function playSfx(type) {{
  if (muted) return;
  if (audioCtx.state === "suspended") audioCtx.resume();
  const now = audioCtx.currentTime;
  const osc = audioCtx.createOscillator();
  const gain = audioCtx.createGain();
  osc.connect(gain);
  gain.connect(audioCtx.destination);

  if (type === "ar" || type === "smg") {{
    osc.type = "sawtooth";
    osc.frequency.setValueAtTime(type === "ar" ? 320 : 420, now);
    osc.frequency.exponentialRampToValueAtTime(75, now + 0.08);
    gain.gain.setValueAtTime(0.14, now);
    gain.gain.exponentialRampToValueAtTime(0.001, now + 0.08);
    osc.start(now); osc.stop(now + 0.08);
  }} else if (type === "pump") {{
    osc.type = "square";
    osc.frequency.setValueAtTime(160, now);
    osc.frequency.exponentialRampToValueAtTime(38, now + 0.22);
    gain.gain.setValueAtTime(0.24, now);
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

// --- THREE.JS SCENE SETUP ---
const scene = new THREE.Scene();
scene.background = new THREE.Color(IS_BR ? 0x38bdf8 : 0x0b1324);
scene.fog = new THREE.FogExp2(IS_BR ? 0x7dd3fc : 0x0b1324, IS_BR ? 0.0045 : 0.006);

const camera = new THREE.PerspectiveCamera(74, container.clientWidth / container.clientHeight, 0.1, 320);
const renderer = new THREE.WebGLRenderer({{ antialias: true }});
renderer.setSize(container.clientWidth, container.clientHeight);
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.shadowMap.enabled = true;
container.insertBefore(renderer.domElement, container.firstChild);

scene.add(new THREE.HemisphereLight(0xffffff, IS_BR ? 0x3f6212 : 0x1e293b, 1.0));
const sun = new THREE.DirectionalLight(0xfffbeb, 0.95);
sun.position.set(45, 75, 35);
sun.castShadow = true;
scene.add(sun);

const MAP_HALF = IS_BR ? 80 : 48;
const ground = new THREE.Mesh(
  new THREE.PlaneGeometry(MAP_HALF * 2, MAP_HALF * 2),
  new THREE.MeshStandardMaterial({{ color: IS_BR ? 0x2e7d32 : 0x132238, roughness: 0.85 }})
);
ground.rotation.x = -Math.PI / 2;
ground.receiveShadow = true;
scene.add(ground);

if (!IS_BR) {{
  const gridHelper = new THREE.GridHelper(96, 24, 0x38bdf8, 0x1e3a5f);
  gridHelper.position.y = 0.02;
  scene.add(gridHelper);
}}

// Storm Cylinder (BR mode)
let stormRadius = IS_BR ? 78 : 999;
const stormMesh = new THREE.Mesh(
  new THREE.CylinderGeometry(1, 1, 55, 48, 1, true),
  new THREE.MeshBasicMaterial({{ color: 0xa855f7, transparent: true, opacity: 0.28, side: THREE.DoubleSide }})
);
stormMesh.position.y = 27;
stormMesh.scale.set(stormRadius, 1, stormRadius);
stormMesh.visible = IS_BR;
scene.add(stormMesh);

// --- BR ISLAND PROPS (Trees, Rocks, Towers, Loot Chests) ---
const harvestNodes = []; // {{ mesh, x, z, hp, matType }}
const chests = [];       // {{ id, mesh, lid, x, z, opened }}

if (IS_BR) {{
  // Tilted-style brick/wood structures
  const towerSpots = [[-22, -22], [24, -18], [-18, 26], [22, 24], [0, 0]];
  towerSpots.forEach(([tx, tz], idx) => {{
    const h = idx === 4 ? 10 : 6.5;
    const bldg = new THREE.Mesh(
      new THREE.BoxGeometry(8, h, 8),
      new THREE.MeshStandardMaterial({{ color: idx % 2 === 0 ? 0x7c2d12 : 0x475569, roughness: 0.8 }})
    );
    bldg.position.set(tx, h / 2, tz);
    bldg.castShadow = true; bldg.receiveShadow = true;
    scene.add(bldg);
    harvestNodes.push({{ mesh: bldg, x: tx, z: tz, radius: 4.5, hp: 300, matType: "brick", isBuilding: true, height: h }});
  }});

  // Trees & Boulders for farming mats
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
      const trunk = new THREE.Mesh(
        new THREE.CylinderGeometry(0.35, 0.5, 3.2, 8),
        new THREE.MeshStandardMaterial({{ color: 0x78350f }})
      );
      trunk.position.y = 1.6;
      const leaves = new THREE.Mesh(
        new THREE.ConeGeometry(2.1, 4.2, 8),
        new THREE.MeshStandardMaterial({{ color: 0x15803d }})
      );
      leaves.position.y = 4.2;
      tree.add(trunk, leaves);
      tree.position.set(px, 0, pz);
      scene.add(tree);
      harvestNodes.push({{ mesh: tree, x: px, z: pz, radius: 1.2, hp: 90, matType: "wood" }});
    }}
  }}

  // Glowing Golden Loot Chests
  const chestSpots = [
    [-22, -16], [24, -12], [-18, 32], [22, 30], [0, 6],
    [-42, 0], [42, 0], [0, -42], [0, 42], [-35, -35], [35, 35], [-35, 35], [35, -35]
  ];
  chestSpots.forEach(([cx, cz], idx) => {{
    const g = new THREE.Group();
    const box = new THREE.Mesh(
      new THREE.BoxGeometry(1.3, 0.85, 0.9),
      new THREE.MeshStandardMaterial({{ color: 0xfacc15, emissive: 0xca8a04, emissiveIntensity: 0.55, metalness: 0.4 }})
    );
    box.position.y = 0.42;
    g.add(box);
    g.position.set(cx, 0, cz);
    scene.add(g);
    chests.push({{ id: idx, mesh: g, x: cx, z: cz, opened: false }});
  }});
}}

// --- BUILDING & 3x3 EDIT SYSTEM ---
const CELL = 4.0;
const WALL_H = 3.2;
const builds = new Map(); // key -> {{ key, type, gx, gy, gz, rot, mat, hp, mask, group }}

const MAT_COLORS = {{ wood: 0xd97706, brick: 0xb91c1c, metal: 0x64748b }};

function buildWorldPos(type, gx, gy, gz, rot) {{
  const cx = gx * CELL;
  const cz = gz * CELL;
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
  const color = isPreview ? 0x38bdf8 : (MAT_COLORS[matName] || 0xd97706);
  const mat = new THREE.MeshStandardMaterial({{
    color,
    emissive: isPreview ? 0x0284c7 : 0x000000,
    emissiveIntensity: isPreview ? 0.5 : 0,
    transparent: isPreview,
    opacity: isPreview ? 0.45 : 1.0,
    roughness: 0.65
  }});

  if (type === "wall") {{
    // 3x3 sub-panes so editing windows & doors creates real physical openings!
    const pw = CELL / 3;
    const ph = WALL_H / 3;
    for (let r = 0; r < 3; r++) {{
      for (let c = 0; c < 3; c++) {{
        if (!mask[r * 3 + c]) continue;
        const pane = new THREE.Mesh(new THREE.BoxGeometry(pw * 0.98, ph * 0.98, 0.24), mat);
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
        const tile = new THREE.Mesh(new THREE.BoxGeometry(pw * 0.98, 0.22, pw * 0.98), mat);
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
  if (builds.has(key)) {{
    scene.remove(builds.get(key).group);
  }}
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
  if (b.hp <= 0) {{
    scene.remove(b.group);
    builds.delete(key);
  }}
  if (broadcast) netSend({{ t: "dmg_build", key, dmg }});
}}

// Classic 1v1.LOL Starting Build-Fight Ramps!
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

// --- PLAYER STATE ---
const SPAWNS_1V1 = [[0, -6, 0], [0, 6, Math.PI], [-6, 0, -Math.PI/2], [6, 0, Math.PI/2]];
const SPAWNS_BR  = [[-30, -30, 0], [30, 30, Math.PI], [-30, 30, 0], [30, -30, Math.PI], [0, -38, 0], [0, 38, Math.PI], [-38, 0, 0], [38, 0, Math.PI]];
const sp = (IS_BR ? SPAWNS_BR : SPAWNS_1V1)[CFG.slotIdx % 4];

const me = {{
  id: CFG.myPid,
  name: CFG.myName,
  color: CFG.myColor,
  x: sp[0], y: IS_BR ? 38 : 0, z: sp[1],
  vy: 0, yaw: sp[2], pitch: 0.12,
  hp: 100, shield: IS_BR ? 0 : 100, alive: true,
  gliding: IS_BR,
  mode: "ar", buildRot: 0,
  mats: {{ wood: IS_BR ? 60 : 999, brick: IS_BR ? 30 : 999, metal: IS_BR ? 0 : 999 }},
  pots: IS_BR ? 1 : 2,
  wins: 0,
  lastShot: 0
}};

function createAvatar(colorHex) {{
  const g = new THREE.Group();
  const mat = new THREE.MeshStandardMaterial({{ color: colorHex, roughness: 0.35 }});
  const body = new THREE.Mesh(new THREE.BoxGeometry(0.75, 1.0, 0.45), mat);
  body.position.y = 1.05; body.castShadow = true; g.add(body);
  const head = new THREE.Mesh(new THREE.BoxGeometry(0.52, 0.52, 0.52), mat);
  head.position.y = 1.85; head.castShadow = true; g.add(head);
  const gun = new THREE.Mesh(new THREE.BoxGeometry(0.16, 0.18, 0.78), new THREE.MeshStandardMaterial({{ color: 0x0f172a }}));
  gun.position.set(0.45, 1.25, -0.35); g.add(gun);
  const glider = new THREE.Mesh(new THREE.BoxGeometry(2.6, 0.12, 1.1), new THREE.MeshStandardMaterial({{ color: 0x38bdf8 }}));
  glider.position.set(0, 2.5, 0); glider.visible = false; g.add(glider);
  g.userData.glider = glider;
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
    r = {{ ...p, mesh, labelEl }};
    remotes.set(p.id, r);
  }}
  Object.assign(r, p);
  r.mesh.visible = r.alive;
  r.mesh.userData.glider.visible = !!r.gliding;
  r.labelEl.style.display = r.alive ? "block" : "none";
  r.mesh.position.set(r.x, r.y, r.z);
  r.mesh.rotation.y = r.yaw;
  r.labelEl.innerHTML = `${{r.name}} · ❤️${{Math.ceil(r.hp)}} 🛡️${{Math.ceil(r.shield)}}`;
}}

// --- 1v1 / ISLAND BOT ---
let botEnabled = false;
let botState = null;

function toggleBot() {{
  botEnabled = !botEnabled;
  if (botEnabled) {{
    botState = {{
      id: "BOT_1", name: "🤖 Sweat Bot", color: "#10b981",
      x: 0, y: 0, z: 6, vy: 0, yaw: Math.PI, hp: 100, shield: 100, alive: true,
      dirTimer: 0, moveAngle: Math.PI, shootTimer: 0, buildTimer: 0
    }};
    upsertRemote(botState);
    logFeed("🤖 1v1 Bot spawned!");
  }} else if (botState) {{
    botState.alive = false;
    upsertRemote(botState);
    remotes.delete("BOT_1");
    scene.remove(botState.mesh);
    botState.labelEl.remove();
    botState = null;
  }}
}}

// --- TRACERS & HITMARKER ---
const tracers = [];
function spawnTracer(from, to, color = 0xfacc15) {{
  const geo = new THREE.BufferGeometry().setFromPoints([from, to]);
  const line = new THREE.Line(geo, new THREE.LineBasicMaterial({{ color }}));
  scene.add(line);
  tracers.push({{ line, life: 0.12 }});
}}
function flashHitmarker() {{
  playSfx("hit");
  const hm = document.getElementById("hitmarker");
  hm.style.opacity = "1";
  setTimeout(() => {{ hm.style.opacity = "0"; }}, 110);
}}

// --- INPUT & IFRAME-SAFE AIMING ---
const keys = {{}};
let mouseDown = false;
let isPlaying = false;
let pointerLocked = false;
let adsZoom = false;
let editingBuild = null;
let editMaskDraft = [];

function startPlaying() {{
  overlay.style.display = "none";
  isPlaying = true;
  if (renderer.domElement.requestPointerLock) {{
    try {{ renderer.domElement.requestPointerLock(); }} catch (e) {{}}
  }}
}}

document.getElementById("play-btn").addEventListener("click", startPlaying);
document.getElementById("bot-btn").addEventListener("click", () => {{ if (!botEnabled) toggleBot(); startPlaying(); }});
document.getElementById("reset-btn").addEventListener("click", () => {{ reset1v1Round(true); startPlaying(); }});

document.addEventListener("pointerlockchange", () => {{
  pointerLocked = (document.pointerLockElement === renderer.domElement);
}});

// Fallback mouse look when Streamlit's iframe blocks requestPointerLock
let lastMouseX = null, lastMouseY = null;
window.addEventListener("mousemove", e => {{
  if (!isPlaying || editingBuild) return;
  const sens = adsZoom ? 0.0014 : 0.0024;
  if (pointerLocked) {{
    me.yaw -= e.movementX * sens;
    me.pitch = Math.max(-0.85, Math.min(1.05, me.pitch + e.movementY * sens));
  }} else if (lastMouseX !== null) {{
    me.yaw -= (e.clientX - lastMouseX) * sens * 1.3;
    me.pitch = Math.max(-0.85, Math.min(1.05, me.pitch + (e.clientY - lastMouseY) * sens * 1.1));
  }}
  lastMouseX = e.clientX;
  lastMouseY = e.clientY;
}});

window.addEventListener("mousedown", e => {{
  if (!isPlaying || !me.alive || editingBuild) return;
  if (e.target.closest(".slot") || e.target.closest("button")) return;
  if (e.button === 2) adsZoom = true;
  if (e.button === 0) {{
    mouseDown = true;
    triggerPrimaryAction();
  }}
}});
window.addEventListener("mouseup", e => {{
  if (e.button === 2) adsZoom = false;
  if (e.button === 0) mouseDown = false;
}});
window.addEventListener("contextmenu", e => e.preventDefault());

window.addEventListener("keydown", e => {{
  keys[e.code] = true;
  if (e.code === "Escape" && isPlaying && !pointerLocked) {{
    isPlaying = false;
    overlay.style.display = "flex";
  }}
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
    // Confirm edit
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
document.getElementById("confirm-edit-btn").addEventListener("click", toggleEditMode);

// --- SHOOTING, SHIELD POTIONS & TURBO BUILDING ---
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
    if (!matUsed) {{ logFeed("⚠️ Out of materials! Harvest trees/rocks with [4]"); return; }}
    addOrUpdateBuild({{ ...p, mat: matUsed }}, true);
    return;
  }}

  if (me.mode === "pot") {{
    if (me.pots > 0 && me.shield < 100) {{
      me.pots--;
      me.shield = Math.min(100, me.shield + 50);
      playSfx("shield");
      logFeed("🧪 Drank Shield Potion (+50 Shield)");
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
    // Harvest nearby tree/rock
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
      ch.opened = true;
      ch.mesh.visible = false;
      playSfx("chest");
      me.mats.wood += 60; me.mats.brick += 40; me.mats.metal += 20;
      me.pots += 1;
      logFeed("✨ Opened Golden Chest! (+120 Mats, +1 Shield Pot)");
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
    me.shield -= absorbed;
    dmg -= absorbed;
  }}
  me.hp = Math.max(0, me.hp - dmg);
  if (me.hp <= 0) {{
    me.alive = false;
    myAvatar.visible = false;
    logFeed(`💀 Eliminated by ${{attackerName}}!`);
    netSend({{ t: "elim", victim: me.name, killer: attackerName, killerId: attackerName }});
    if (!IS_BR) {{
      setTimeout(() => reset1v1Round(true), 2200);
    }} else {{
      isPlaying = false;
      document.getElementById("ov-title").textContent = "💀 ELIMINATED";
      document.getElementById("ov-sub").textContent = `Taken out by ${{attackerName}}. Click below to re-deploy!`;
      document.getElementById("play-btn").textContent = "🪂 Re-Deploy";
      document.getElementById("play-btn").onclick = () => {{
        const rsp = SPAWNS_BR[Math.floor(Math.random() * SPAWNS_BR.length)];
        me.x = rsp[0]; me.y = 38; me.z = rsp[1]; me.gliding = true;
        me.hp = 100; me.shield = 0; me.alive = true; myAvatar.visible = true;
        startPlaying();
      }};
      overlay.style.display = "flex";
    }}
  }}
}}

function applyDamageToBot(dmg) {{
  if (!botState || !botState.alive) return;
  if (botState.shield > 0) {{
    const abs = Math.min(botState.shield, dmg);
    botState.shield -= abs;
    dmg -= abs;
  }}
  botState.hp = Math.max(0, botState.hp - dmg);
  if (botState.hp <= 0) {{
    me.wins++;
    logFeed(`🏆 ${{me.name}} eliminated Sweat Bot!`);
    if (!IS_BR) setTimeout(() => reset1v1Round(false), 1800);
    else {{
      botState.x = 20; botState.y = 0; botState.z = -20;
      botState.hp = 100; botState.shield = 100;
    }}
  }}
}}

function logFeed(msg) {{
  const kf = document.getElementById("kill-feed");
  const line = document.createElement("div");
  line.style.color = "#facc15";
  line.textContent = msg;
  kf.appendChild(line);
  if (kf.children.length > 6) kf.removeChild(kf.children[3]);
}}

// --- PHYSICS & BUILD COLLISIONS ---
function stepPhysics(dt) {{
  if (!me.alive) return;

  // Arrow key camera turn support
  if (keys["ArrowLeft"]) me.yaw += 2.2 * dt;
  if (keys["ArrowRight"]) me.yaw -= 2.2 * dt;

  // Turbo-Build & Auto-Fire while holding Left Click
  if (isPlaying && mouseDown && !editingBuild) {{
    if (["ar", "smg", "wall", "ramp", "floor", "cone"].includes(me.mode)) {{
      triggerPrimaryAction();
    }}
  }}

  const speed = me.gliding ? 14.5 : (keys["ShiftLeft"] ? 11.5 : 8.5);
  let fwdMove = (keys["KeyW"] ? 1 : 0) - (keys["KeyS"] ? 1 : 0);
  let sideMove = (keys["KeyD"] ? 1 : 0) - (keys["KeyA"] ? 1 : 0);

  if (fwdMove !== 0 || sideMove !== 0) {{
    const len = Math.hypot(fwdMove, sideMove);
    fwdMove /= len; sideMove /= len;
    const sin = Math.sin(me.yaw), cos = Math.cos(me.yaw);
    me.x += (-sin * fwdMove + cos * sideMove) * speed * dt;
    me.z += (-cos * fwdMove - sin * sideMove) * speed * dt;
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

  let supportY = 0;
  // Building rooftops in BR
  if (IS_BR) {{
    for (const node of harvestNodes) {{
      if (node.isBuilding && Math.abs(me.x - node.x) < 4.1 && Math.abs(me.z - node.z) < 4.1) {{
        if (me.y >= node.height - 0.6 && node.height > supportY) supportY = node.height;
      }}
    }}
  }}

  // Player builds (Floors, Ramps, Cones)
  builds.forEach(b => {{
    const cx = b.gx * CELL, cz = b.gz * CELL;
    const dx = me.x - cx, dz = me.z - cz;
    if (Math.abs(dx) <= CELL * 0.52 && Math.abs(dz) <= CELL * 0.52) {{
      if (b.type === "floor") {{
        // Check if player is standing over a solid sub-tile
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
    if (keys["Space"] && isPlaying) me.vy = 10.0;
  }}

  // Wall collision (allows walking through edited doorway openings!)
  builds.forEach(b => {{
    if (b.type !== "wall") return;
    const wp = buildWorldPos("wall", b.gx, b.gy, b.gz, b.rot);
    if (me.y + 1.8 < wp.y - WALL_H * 0.5 || me.y > wp.y + WALL_H * 0.5 - 0.2) return;
    const halfX = (b.rot % 2 === 0) ? CELL * 0.5 : 0.45;
    const halfZ = (b.rot % 2 === 0) ? 0.45 : CELL * 0.5;
    const dx = me.x - wp.x, dz = me.z - wp.z;
    if (Math.abs(dx) < halfX && Math.abs(dz) < halfZ) {{
      // Check if bottom-middle door is cut open
      const localX = (b.rot % 2 === 0) ? dx : dz;
      const colIdx = Math.min(2, Math.max(0, Math.floor((localX + CELL * 0.5) / (CELL / 3))));
      if (!b.mask[6 + colIdx] && !b.mask[3 + colIdx]) return; // Walk right through edited door!

      if (halfX - Math.abs(dx) < halfZ - Math.abs(dz)) {{
        me.x += dx >= 0 ? (halfX - Math.abs(dx)) : -(halfX - Math.abs(dx));
      }} else {{
        me.z += dz >= 0 ? (halfZ - Math.abs(dz)) : -(halfZ - Math.abs(dz));
      }}
    }}
  }});

  myAvatar.position.set(me.x, me.y, me.z);
  myAvatar.rotation.y = me.yaw;
}}

// --- 1v1 BOT AI (Cranks Ramps, Places Walls & Shoots) ---
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

  // Bot builds defensive walls/ramps
  botState.buildTimer -= dt;
  if (botState.buildTimer <= 0) {{
    botState.buildTimer = 2.4;
    const gx = Math.round(botState.x / CELL);
    const gz = Math.round(botState.z / CELL);
    const rot = ((Math.round(-botState.yaw / (Math.PI / 2)) % 4) + 4) % 4;
    addOrUpdateBuild({{ type: Math.random() < 0.6 ? "wall" : "ramp", gx, gy: 0, gz, rot, mat: "wood" }}, false);
  }}

  botState.shootTimer -= dt;
  if (botState.shootTimer <= 0 && me.alive) {{
    botState.shootTimer = 1.25;
    const from = new THREE.Vector3(botState.x, botState.y + 1.4, botState.z);
    const to = new THREE.Vector3(me.x, me.y + 1.2, me.z);
    spawnTracer(from, to, 0x10b981);
    if (Math.random() < 0.42) takeDamage(16, "🤖 Sweat Bot");
  }}
  upsertRemote(botState);
}}

// --- WEBRTC MULTIPLAYER ---
const conns = new Map();
const hostId = `shsfn-${{CFG.mode}}-${{CFG.roomCode}}-0`;
const myPeerId = `shsfn-${{CFG.mode}}-${{CFG.roomCode}}-${{CFG.slotIdx}}`;
const peer = new Peer(myPeerId);

function wireConn(conn) {{
  conn.on("open", () => {{
    conns.set(conn.peer, conn);
    document.getElementById("net-status").textContent = `🟢 P2P Live (${{conns.size + 1}} players)`;
    if (CFG.isHost) {{
      builds.forEach(b => conn.send({{ t: "build", b: {{ type: b.type, gx: b.gx, gy: b.gy, gz: b.gz, rot: b.rot, mat: b.mat, mask: b.mask, hp: b.hp }} }}));
    }}
  }});
  conn.on("data", data => {{
    if (CFG.isHost) conns.forEach((c, pid) => {{ if (pid !== conn.peer && c.open) c.send(data); }});
    if (data.t === "state") upsertRemote(data.p);
    else if (data.t === "build") addOrUpdateBuild(data.b, false);
    else if (data.t === "dmg_build") damageBuild(data.key, data.dmg, false);
    else if (data.t === "tracer") spawnTracer(new THREE.Vector3(...data.from), new THREE.Vector3(...data.to));
    else if (data.t === "hit" && data.targetId === me.id) takeDamage(data.dmg, data.fromName);
    else if (data.t === "reset_1v1") reset1v1Round(false);
    else if (data.t === "chest") {{
      const ch = chests.find(c => c.id === data.id);
      if (ch) {{ ch.opened = true; ch.mesh.visible = false; }}
    }}
    else if (data.t === "elim") {{
      if (data.killer === me.name) me.wins++;
      logFeed(`💀 ${{data.victim}} was eliminated by ${{data.killer}}!`);
    }}
  }});
}}
function netSend(payload) {{ conns.forEach(c => {{ if (c.open) c.send(payload); }}); }}

peer.on("open", () => {{
  document.getElementById("net-status").textContent = CFG.isHost ? "🟢 Hosting Lobby" : "🟡 Joining Host...";
  if (!CFG.isHost) wireConn(peer.connect(hostId, {{ reliable: false }}));
}});
peer.on("connection", conn => wireConn(conn));

setInterval(() => {{
  netSend({{
    t: "state",
    p: {{ id: me.id, name: me.name, color: me.color, x: me.x, y: me.y, z: me.z, yaw: me.yaw, hp: me.hp, shield: me.shield, alive: me.alive, gliding: me.gliding }}
  }});
}}, 33);

// --- MINIMAP (BR MODE) ---
const mmCanvas = document.getElementById("minimap");
const mmCtx = mmCanvas.getContext("2d");
function drawMinimap() {{
  if (!IS_BR) return;
  mmCtx.clearRect(0, 0, 96, 96);
  mmCtx.fillStyle = "#14532d";
  mmCtx.fillRect(0, 0, 96, 96);
  // Storm ring
  mmCtx.strokeStyle = "#c084fc";
  mmCtx.lineWidth = 2.5;
  mmCtx.beginPath();
  mmCtx.arc(48, 48, (stormRadius / MAP_HALF) * 46, 0, Math.PI * 2);
  mmCtx.stroke();
  // Me
  mmCtx.fillStyle = "#facc15";
  mmCtx.beginPath();
  mmCtx.arc(48 + (me.x / MAP_HALF) * 46, 48 + (me.z / MAP_HALF) * 46, 3.5, 0, Math.PI * 2);
  mmCtx.fill();
  // Enemies
  mmCtx.fillStyle = "#ef4444";
  remotes.forEach(r => {{
    if (!r.alive) return;
    mmCtx.beginPath();
    mmCtx.arc(48 + (r.x / MAP_HALF) * 46, 48 + (r.z / MAP_HALF) * 46, 3, 0, Math.PI * 2);
    mmCtx.fill();
  }});
}}

// --- MAIN RENDER LOOP ---
let previewGroup = null, previewSig = "";
let lastTime = performance.now(), stormTick = 0;
const projVec = new THREE.Vector3();

function animate(now) {{
  requestAnimationFrame(animate);
  const dt = Math.min(0.05, (now - lastTime) / 1000);
  lastTime = now;

  stepPhysics(dt);
  stepBot(dt);

  // Chest proximity prompt in BR
  if (IS_BR && me.alive) {{
    const nearChest = chests.some(ch => !ch.opened && Math.hypot(me.x - ch.x, me.z - ch.z) < 3.4);
    promptBanner.style.display = nearChest ? "block" : "none";
    if (nearChest) promptBanner.textContent = "Press [F] to Open Golden Chest";
  }}

  // Build Hologram Preview
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

  // Storm Shrink in BR
  if (IS_BR) {{
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

  let aliveCount = me.alive ? 1 : 0;
  remotes.forEach(r => {{
    if (!r.alive) return;
    aliveCount++;
    projVec.set(r.x, r.y + 2.35, r.z);
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
  document.getElementById("alive-txt").textContent = aliveCount;
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
