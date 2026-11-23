import json
import streamlit as st
import streamlit.components.v1 as components
from game_logic import is_in_storm, resolve_br_round

DIR_PAD = [
    [("↖️", -1, -1), ("⬆️", -1, 0), ("↗️", -1, 1)],
    [("⬅️", 0, -1), ("🛡️", 0, 0), ("➡️", 0, 1)],
    [("↙️", 1, -1), ("⬇️", 1, 0), ("↘️", 1, 1)],
]

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


def _render_3d_canvas(room, my_pid, warning_active):
    state = room["state"]
    ring = state["storm_ring"]
    alive = [p for p in room["players"] if state["hp"].get(p, 0) > 0]

    players_payload = []
    for p in alive:
        r, c = state["pos"][p]
        badge = room["badges"][p]
        players_payload.append({
            "id": p,
            "name": room["names"][p],
            "r": r,
            "c": c,
            "hp": state["hp"][p],
            "color": BADGE_HEX.get(badge, "#38bdf8"),
            "isMe": p == my_pid,
            "ready": state["moves"].get(p) is not None,
        })

    items_payload = [
        {"r": r, "c": c, "kind": kind}
        for (r, c), kind in state["items"].items()
    ]

    my_move = state["moves"].get(my_pid) if room["winner"] is None else None

    scene_data = json.dumps({
        "ring": ring,
        "warning": warning_active,
        "players": players_payload,
        "items": items_payload,
        "myMove": list(my_move) if my_move else None,
    })

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8" />
      <style>
        html, body {{
          margin: 0;
          padding: 0;
          overflow: hidden;
          background: #090d16;
          font-family: system-ui, -apple-system, sans-serif;
          user-select: none;
        }}
        #canvas-wrap {{
          position: relative;
          width: 100vw;
          height: 460px;
          cursor: grab;
        }}
        #canvas-wrap:active {{
          cursor: grabbing;
        }}
        #hud-hint {{
          position: absolute;
          bottom: 10px;
          left: 12px;
          background: rgba(15, 23, 42, 0.8);
          color: #cbd5e1;
          padding: 5px 10px;
          border-radius: 8px;
          font-size: 12px;
          border: 1px solid rgba(148, 163, 184, 0.25);
          pointer-events: none;
        }}
        .label {{
          position: absolute;
          transform: translate(-50%, -100%);
          background: rgba(15, 23, 42, 0.88);
          color: #f8fafc;
          padding: 2px 7px;
          border-radius: 6px;
          font-size: 11px;
          font-weight: 700;
          white-space: nowrap;
          pointer-events: none;
          border: 1px solid rgba(255,255,255,0.2);
          text-align: center;
          line-height: 1.25;
        }}
      </style>
      <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    </head>
    <body>
      <div id="canvas-wrap">
        <div id="labels"></div>
        <div id="hud-hint">🖱️ Drag to rotate 3D camera · Scroll to zoom</div>
      </div>

      <script>
        const DATA = {scene_data};
        const wrap = document.getElementById("canvas-wrap");
        const labelsDiv = document.getElementById("labels");

        const scene = new THREE.Scene();
        scene.background = new THREE.Color(0x090d16);
        scene.fog = new THREE.FogExp2(0x090d16, 0.032);

        const camera = new THREE.PerspectiveCamera(45, wrap.clientWidth / wrap.clientHeight, 0.1, 100);
        const renderer = new THREE.WebGLRenderer({{ antialias: true }});
        renderer.setSize(wrap.clientWidth, wrap.clientHeight);
        renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
        renderer.shadowMap.enabled = true;
        wrap.appendChild(renderer.domElement);

        const hemi = new THREE.HemisphereLight(0xdbeafe, 0x1e293b, 0.95);
        scene.add(hemi);

        const dirLight = new THREE.DirectionalLight(0xffffff, 0.9);
        dirLight.position.set(8, 15, 10);
        dirLight.castShadow = true;
        scene.add(dirLight);

        const baseGeo = new THREE.BoxGeometry(8.6, 0.6, 8.6);
        const baseMat = new THREE.MeshStandardMaterial({{ color: 0x0f172a, roughness: 0.7 }});
        const baseMesh = new THREE.Mesh(baseGeo, baseMat);
        baseMesh.position.y = -0.45;
        scene.add(baseMesh);

        const toWorld = (r, c) => ({{ x: c - 3.5, z: r - 3.5 }});
        const inStorm = (r, c, ring) => r < ring || r >= 8 - ring || c < ring || c >= 8 - ring;

        const tileGeo = new THREE.BoxGeometry(0.92, 0.28, 0.92);
        const stormGeo = new THREE.BoxGeometry(0.96, 1.45, 0.96);
        const stormMat = new THREE.MeshStandardMaterial({{
          color: 0x9333ea,
          emissive: 0x581c87,
          emissiveIntensity: 0.6,
          transparent: true,
          opacity: 0.52,
          roughness: 0.2
        }});

        for (let r = 0; r < 8; r++) {{
          for (let c = 0; c < 8; c++) {{
            const {{ x, z }} = toWorld(r, c);
            const storm = inStorm(r, c, DATA.ring);
            const warn = DATA.warning && !storm && inStorm(r, c, DATA.ring + 1);

            let color = (r + c) % 2 === 0 ? 0x1e293b : 0x263449;
            let emissive = 0x000000;
            if (storm) {{
              color = 0x3b0764;
              emissive = 0x4c1d95;
            }} else if (warn) {{
              color = 0xd97706;
              emissive = 0x92400e;
            }}

            const mat = new THREE.MeshStandardMaterial({{
              color,
              emissive,
              emissiveIntensity: warn ? 0.55 : 0.25,
              roughness: 0.55
            }});
            const tile = new THREE.Mesh(tileGeo, mat);
            tile.position.set(x, 0, z);
            tile.receiveShadow = true;
            scene.add(tile);

            if (storm) {{
              const wall = new THREE.Mesh(stormGeo, stormMat);
              wall.position.set(x, 0.72, z);
              scene.add(wall);
            }}
          }}
        }}

        const itemMeshes = [];
        DATA.items.forEach(it => {{
          const {{ x, z }} = toWorld(it.r, it.c);
          let geo, color, emissive;
          if (it.kind === "💖") {{
            geo = new THREE.OctahedronGeometry(0.28, 0);
            color = 0xf43f5e;
            emissive = 0xbe123c;
          }} else if (it.kind === "⚡") {{
            geo = new THREE.ConeGeometry(0.25, 0.55, 5);
            color = 0xfacc15;
            emissive = 0xca8a04;
          }} else {{
            geo = new THREE.TorusGeometry(0.24, 0.08, 10, 20);
            color = 0x22d3ee;
            emissive = 0x0891b2;
          }}
          const mat = new THREE.MeshStandardMaterial({{
            color,
            emissive,
            emissiveIntensity: 0.65,
            roughness: 0.25
          }});
          const mesh = new THREE.Mesh(geo, mat);
          mesh.position.set(x, 0.55, z);
          scene.add(mesh);
          itemMeshes.push(mesh);
        }});

        const playerMeshes = [];
        DATA.players.forEach(p => {{
          const {{ x, z }} = toWorld(p.r, p.c);
          const group = new THREE.Group();
          group.position.set(x, 0.14, z);

          const bodyMat = new THREE.MeshStandardMaterial({{
            color: p.color,
            roughness: 0.3,
            metalness: 0.15
          }});

          const torso = new THREE.Mesh(new THREE.CylinderGeometry(0.22, 0.3, 0.58, 18), bodyMat);
          torso.position.y = 0.29;
          torso.castShadow = true;
          group.add(torso);

          const head = new THREE.Mesh(new THREE.SphereGeometry(0.21, 18, 18), bodyMat);
          head.position.y = 0.72;
          head.castShadow = true;
          group.add(head);

          if (p.isMe) {{
            const ringGeo = new THREE.RingGeometry(0.34, 0.44, 28);
            const ringMat = new THREE.MeshBasicMaterial({{ color: 0x4ade80, side: THREE.DoubleSide }});
            const ringMesh = new THREE.Mesh(ringGeo, ringMat);
            ringMesh.rotation.x = -Math.PI / 2;
            ringMesh.position.y = 0.02;
            group.add(ringMesh);
          }}

          scene.add(group);

          const el = document.createElement("div");
          el.className = "label";
          if (p.isMe) el.style.borderColor = "#4ade80";
          const hearts = "❤️".repeat(p.hp);
          const check = p.ready ? " ✅" : "";
          el.innerHTML = `${{p.isMe ? "★ " : ""}}${{p.name}}${{check}}<br>${{hearts}}`;
          labelsDiv.appendChild(el);

          playerMeshes.push({{ group, el }});
        }});

        let beacon = null;
        if (DATA.myMove) {{
          const {{ x, z }} = toWorld(DATA.myMove[0], DATA.myMove[1]);
          const bGeo = new THREE.CylinderGeometry(0.34, 0.34, 0.08, 24);
          const bMat = new THREE.MeshBasicMaterial({{ color: 0x4ade80, transparent: true, opacity: 0.75 }});
          beacon = new THREE.Mesh(bGeo, bMat);
          beacon.position.set(x, 0.18, z);
          scene.add(beacon);
        }}

        let camState = {{ yaw: 0.65, pitch: 0.78, dist: 12.2 }};
        try {{
          if (window.parent && window.parent._brCam3D) {{
            camState = window.parent._brCam3D;
          }}
        }} catch (e) {{}}

        const saveCam = () => {{
          try {{
            if (window.parent) window.parent._brCam3D = camState;
          }} catch (e) {{}}
        }};

        let dragging = false;
        let lastX = 0, lastY = 0;

        wrap.addEventListener("pointerdown", e => {{
          dragging = true;
          lastX = e.clientX;
          lastY = e.clientY;
        }});
        window.addEventListener("pointerup", () => {{ dragging = false; }});
        window.addEventListener("pointermove", e => {{
          if (!dragging) return;
          const dx = e.clientX - lastX;
          const dy = e.clientY - lastY;
          lastX = e.clientX;
          lastY = e.clientY;
          camState.yaw -= dx * 0.008;
          camState.pitch = Math.max(0.32, Math.min(1.35, camState.pitch + dy * 0.006));
          saveCam();
        }});
        wrap.addEventListener("wheel", e => {{
          e.preventDefault();
          camState.dist = Math.max(7.5, Math.min(18, camState.dist + e.deltaY * 0.008));
          saveCam();
        }}, {{ passive: false }});

        function updateCamera() {{
          camera.position.x = Math.sin(camState.yaw) * Math.cos(camState.pitch) * camState.dist;
          camera.position.y = Math.sin(camState.pitch) * camState.dist;
          camera.position.z = Math.cos(camState.yaw) * Math.cos(camState.pitch) * camState.dist;
          camera.lookAt(0, 0.3, 0);
        }}

        const projVec = new THREE.Vector3();
        let t = 0;
        function animate() {{
          requestAnimationFrame(animate);
          t += 0.03;

          itemMeshes.forEach((m, idx) => {{
            m.rotation.y += 0.03;
            m.position.y = 0.52 + Math.sin(t + idx) * 0.08;
          }});

          if (beacon) {{
            beacon.scale.setScalar(0.92 + Math.sin(t * 2) * 0.1);
          }}

          updateCamera();
          renderer.render(scene, camera);

          playerMeshes.forEach(({{ group, el }}) => {{
            projVec.set(group.position.x, group.position.y + 1.12, group.position.z);
            projVec.project(camera);
            const sx = (projVec.x * 0.5 + 0.5) * wrap.clientWidth;
            const sy = (-projVec.y * 0.5 + 0.5) * wrap.clientHeight;
            el.style.left = `${{sx}}px`;
            el.style.top = `${{sy}}px`;
          }});
        }}
        animate();
      </script>
    </body>
    </html>
    """
    components.html(html, height=465)


def render_br(room, my_pid):
    st.markdown("""
    <style>
    div[data-testid="stButton"] button {
        height: 48px !important;
        min-height: 48px !important;
        padding: 0 !important;
        font-size: 1.15rem !important;
        border-radius: 10px !important;
    }
    </style>
    """, unsafe_allow_html=True)

    players = room["players"]
    names = room["names"]
    badges = room["badges"]
    state = room["state"]

    hp = state["hp"]
    pos = state["pos"]
    moves = state["moves"]
    items = state["items"]
    ring = state["storm_ring"]
    rnd = state["round"]

    alive = [p for p in players if hp.get(p, 0) > 0]
    am_alive = my_pid in alive
    my_pos = pos.get(my_pid)
    my_locked_move = moves.get(my_pid)
    warning_active = (rnd % 2 == 0) and (ring < 3)

    left, right = st.columns([1.65, 1])

    with left:
        shrink_msg = (
            "⚠️ **Storm shrinks AFTER this round! Get off glowing orange tiles!**"
            if warning_active
            else f"🌪️ Round **{rnd}** · Storm shrinks after Round **{rnd + 1}**"
        )
        st.markdown(shrink_msg)
        _render_3d_canvas(room, my_pid, warning_active)
        st.caption("3D Items: 💖 Medkit (+1 HP) · ⚡ Shockwave (blasts neighbors) · 🌀 Random Warp")

    with right:
        if room["winner"] is None:
            if not am_alive:
                st.error("💀 You were eliminated! Spectating remaining players...")
            elif my_locked_move is None:
                st.success("🟢 **Choose Your Step:**")
                for row_dirs in DIR_PAD:
                    d_cols = st.columns(3)
                    for idx, (arrow, dr, dc) in enumerate(row_dirs):
                        nr, nc = my_pos[0] + dr, my_pos[1] + dc
                        valid = (0 <= nr < 8) and (0 <= nc < 8) and not is_in_storm(nr, nc, ring)
                        dest = (nr, nc)

                        tag = arrow
                        if valid:
                            if dest in items:
                                tag = f"{arrow}{items[dest]}"
                            elif warning_active and is_in_storm(nr, nc, ring + 1):
                                tag = f"{arrow}⚠️"

                        if d_cols[idx].button(
                            tag,
                            key=f"br3d_{dr}_{dc}",
                            disabled=not valid,
                            use_container_width=True,
                        ):
                            moves[my_pid] = dest
                            if all(moves.get(p) is not None for p in alive):
                                resolve_br_round(room)
                            st.rerun()
                st.caption("`🛡️` = Guard in place · `⚠️` = Storm next round")
            else:
                st.info("⏳ Move locked in! Waiting for the remaining players...")

        st.markdown("#### 💓 Survivors")
        for p in players:
            hearts = hp.get(p, 0)
            if hearts > 0:
                status = "✅ Ready" if moves.get(p) is not None else "⏳ Picking"
                hp_str = "❤️" * hearts + "🖤" * (3 - hearts)
                st.markdown(f"{badges[p]} **{names[p]}** — {hp_str} · *{status}*")
            else:
                st.markdown(f"💀 ~~{badges[p]} {names[p]}~~ — *Eliminated*")

        st.divider()
        st.markdown("#### 📜 Battle Feed")
        for line in state.get("log", []):
            st.markdown(f"- {line}")
