"""Generate an HTML/JS animated ED floor plan for embedding in Streamlit."""


def generate_ed_animation_html(snapshots: list[dict], mode: str = "Traditional", width: int = 600, height: int = 420) -> str:
    """Generate an animated ED floor plan as self-contained HTML."""

    ctas_colors = {1: "#DC2626", 2: "#F97316", 3: "#EAB308", 4: "#22C55E", 5: "#3B82F6"}
    ctas_names = {1: "Resus", 2: "Emerg", 3: "Urgent", 4: "Less Urg", 5: "Non-Urg"}
    header_color = "#991B1B" if mode == "Traditional" else "#166534"
    header_bg = "#FEF2F2" if mode == "Traditional" else "#F0FDF4"
    border_color = "#DC2626" if mode == "Traditional" else "#16A34A"

    # Serialize snapshots to JS-safe JSON
    import json
    snaps_json = json.dumps(snapshots)

    return f"""
    <div style="border:2px solid {border_color}; border-radius:12px; overflow:hidden; font-family:system-ui,-apple-system,sans-serif;">
      <div style="background:{header_bg}; padding:8px 16px; border-bottom:1px solid #E2E8F0; display:flex; justify-content:space-between; align-items:center;">
        <strong style="color:{header_color}; font-size:0.95rem;">{mode}</strong>
        <span id="clock_{mode}" style="color:#64748B; font-size:0.85rem; font-family:monospace;">Hour 0</span>
      </div>
      <div style="position:relative; background:#F8FAFC;">
        <canvas id="canvas_{mode}" width="{width}" height="{height}" style="width:100%; display:block;"></canvas>
      </div>
      <div style="background:white; padding:6px 16px; border-top:1px solid #E2E8F0; display:flex; gap:16px; justify-content:center;">
        <span id="stat_waiting_{mode}" style="font-size:0.8rem; color:#64748B;">Waiting: 0</span>
        <span id="stat_served_{mode}" style="font-size:0.8rem; color:#64748B;">Served: 0</span>
      </div>
    </div>
    <script>
    (function() {{
      const snapshots = {snaps_json};
      const mode = "{mode}";
      const canvas = document.getElementById("canvas_" + mode);
      const ctx = canvas.getContext("2d");
      const W = {width}, H = {height};
      const ctasColors = {json.dumps(ctas_colors)};
      const ctasNames = {json.dumps(ctas_names)};

      let frame = 0;
      const speed = 150; // ms per frame

      function drawRoundedRect(x, y, w, h, r) {{
        ctx.beginPath();
        ctx.moveTo(x+r, y);
        ctx.lineTo(x+w-r, y);
        ctx.quadraticCurveTo(x+w, y, x+w, y+r);
        ctx.lineTo(x+w, y+h-r);
        ctx.quadraticCurveTo(x+w, y+h, x+w-r, y+h);
        ctx.lineTo(x+r, y+h);
        ctx.quadraticCurveTo(x, y+h, x, y+h-r);
        ctx.lineTo(x, y+r);
        ctx.quadraticCurveTo(x, y, x+r, y);
        ctx.closePath();
      }}

      function draw(snap) {{
        ctx.clearRect(0, 0, W, H);

        // Background
        ctx.fillStyle = "#F8FAFC";
        ctx.fillRect(0, 0, W, H);

        // --- Waiting Area (left) ---
        ctx.fillStyle = "#FFF7ED";
        drawRoundedRect(10, 10, 160, H-20, 8);
        ctx.fill();
        ctx.strokeStyle = "#FED7AA";
        ctx.lineWidth = 1;
        ctx.stroke();

        ctx.fillStyle = "#92400E";
        ctx.font = "bold 11px system-ui";
        ctx.textAlign = "center";
        ctx.fillText("WAITING ROOM", 90, 30);

        // Draw waiting patients as dots
        const waiting = snap.waiting_count || 0;
        const maxDots = Math.min(waiting, 60);
        for (let i = 0; i < maxDots; i++) {{
          const col = i % 6;
          const row = Math.floor(i / 6);
          const cx = 30 + col * 22;
          const cy = 48 + row * 22;
          // Random CTAS color for visual variety
          const colors = Object.values(ctasColors);
          ctx.fillStyle = colors[i % colors.length];
          ctx.beginPath();
          ctx.arc(cx, cy, 8, 0, Math.PI * 2);
          ctx.fill();
        }}
        if (waiting > 60) {{
          ctx.fillStyle = "#92400E";
          ctx.font = "10px system-ui";
          ctx.fillText("+" + (waiting - 60) + " more", 90, H-30);
        }}
        // Count
        ctx.fillStyle = "#92400E";
        ctx.font = "bold 14px system-ui";
        ctx.fillText(waiting + " patients", 90, H-10);

        // --- Arrow ---
        ctx.fillStyle = "#94A3B8";
        ctx.beginPath();
        ctx.moveTo(178, H/2-8);
        ctx.lineTo(198, H/2);
        ctx.lineTo(178, H/2+8);
        ctx.fill();

        // --- Treatment Rooms (center-right) ---
        const rooms = snap.rooms || [];
        const roomW = 160;
        const roomH = 65;
        const startX = 210;
        const startY = 15;
        const gap = 10;

        for (let i = 0; i < rooms.length; i++) {{
          const room = rooms[i];
          const rx = startX + (i % 2) * (roomW + gap);
          const ry = startY + Math.floor(i / 2) * (roomH + gap);

          // Room background
          if (room.occupied) {{
            const c = ctasColors[room.ctas] || "#94A3B8";
            ctx.fillStyle = c + "18"; // very light fill
            drawRoundedRect(rx, ry, roomW, roomH, 6);
            ctx.fill();
            ctx.strokeStyle = c;
            ctx.lineWidth = 2;
            ctx.stroke();

            // Patient dot
            ctx.fillStyle = c;
            ctx.beginPath();
            ctx.arc(rx + 20, ry + 25, 10, 0, Math.PI * 2);
            ctx.fill();

            // CTAS badge
            ctx.fillStyle = "white";
            ctx.font = "bold 9px system-ui";
            ctx.textAlign = "center";
            ctx.fillText(room.ctas, rx + 20, ry + 28);

            // Complaint text
            ctx.fillStyle = "#374151";
            ctx.font = "11px system-ui";
            ctx.textAlign = "left";
            const complaint = (room.complaint || "").substring(0, 18);
            ctx.fillText(complaint, rx + 36, ry + 22);

            // Time remaining
            ctx.fillStyle = "#64748B";
            ctx.font = "10px system-ui";
            ctx.fillText(Math.round(room.time_remaining) + " min left", rx + 36, ry + 38);

            // Progress bar
            const prog = room.progress || 0;
            ctx.fillStyle = "#E2E8F0";
            drawRoundedRect(rx + 8, ry + 50, roomW - 16, 6, 3);
            ctx.fill();
            ctx.fillStyle = c;
            drawRoundedRect(rx + 8, ry + 50, (roomW - 16) * prog, 6, 3);
            ctx.fill();
          }} else {{
            ctx.fillStyle = "#F1F5F9";
            drawRoundedRect(rx, ry, roomW, roomH, 6);
            ctx.fill();
            ctx.setLineDash([4, 4]);
            ctx.strokeStyle = "#CBD5E1";
            ctx.lineWidth = 1;
            ctx.stroke();
            ctx.setLineDash([]);

            ctx.fillStyle = "#94A3B8";
            ctx.font = "11px system-ui";
            ctx.textAlign = "center";
            ctx.fillText("Available", rx + roomW/2, ry + roomH/2 + 4);
          }}

          // Room label
          ctx.fillStyle = "#64748B";
          ctx.font = "bold 10px system-ui";
          ctx.textAlign = "left";
          ctx.fillText("Room " + (i + 1), rx + 8, ry - 2);
        }}

        // --- Discharge arrow ---
        const arrowX = startX + 2 * (roomW + gap) + 10;
        ctx.fillStyle = "#16A34A";
        ctx.beginPath();
        ctx.moveTo(arrowX, H/2 - 8);
        ctx.lineTo(arrowX + 20, H/2);
        ctx.lineTo(arrowX, H/2 + 8);
        ctx.fill();

        ctx.fillStyle = "#16A34A";
        ctx.font = "bold 10px system-ui";
        ctx.textAlign = "center";
        ctx.save();
        ctx.translate(arrowX + 35, H/2);
        ctx.rotate(-Math.PI/2);
        ctx.fillText("DISCHARGED", 0, 0);
        ctx.restore();

        // --- CTAS Legend ---
        ctx.font = "10px system-ui";
        ctx.textAlign = "left";
        let ly = H - 55;
        for (const [ctas, color] of Object.entries(ctasColors)) {{
          ctx.fillStyle = color;
          ctx.beginPath();
          ctx.arc(startX + 5, ly, 5, 0, Math.PI * 2);
          ctx.fill();
          ctx.fillStyle = "#374151";
          ctx.fillText("CTAS " + ctas, startX + 14, ly + 4);
          ly += 14;
        }}
      }}

      function animate() {{
        if (frame >= snapshots.length) frame = 0;
        const snap = snapshots[frame];
        draw(snap);

        // Update stats
        const hour = snap.hour || 0;
        document.getElementById("clock_" + mode).textContent = "Hour " + hour.toFixed(1);
        document.getElementById("stat_waiting_" + mode).textContent = "Waiting: " + (snap.waiting_count || 0);
        document.getElementById("stat_served_" + mode).textContent = "Served: " + (snap.total_discharged || 0);

        frame++;
        setTimeout(animate, speed);
      }}

      animate();
    }})();
    </script>
    """
