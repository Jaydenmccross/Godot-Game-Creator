/**
 * Godot Game Creator — Frontend Application
 * v2: Preview canvas, undo, contextual suggestions, help system
 */

const API = "/api";
const SESSION_ID = "session_" + Math.random().toString(36).substring(2, 10);

/* ── DOM refs ──────────────────────────────────────── */
const chatMessages    = document.getElementById("chatMessages");
const chatInput       = document.getElementById("chatInput");
const sendBtn         = document.getElementById("sendBtn");
const typingIndicator = document.getElementById("typingIndicator");
const progressBar     = document.getElementById("progressBar");
const specPanel       = document.getElementById("specPanel");
const downloadArea    = document.getElementById("downloadArea");
const downloadBtn     = document.getElementById("downloadBtn");
const validationLog   = document.getElementById("validationLog");
const togglePanelBtn  = document.getElementById("togglePanel");
const newChatBtn      = document.getElementById("newChat");
const sidePanel       = document.getElementById("sidePanel");
const undoBtn         = document.getElementById("undoBtn");
const helpBtn         = document.getElementById("helpBtn");
const helpOverlay     = document.getElementById("helpOverlay");
const helpClose       = document.getElementById("helpClose");
const helpBody        = document.getElementById("helpBody");
const suggestionsBar  = document.getElementById("suggestionsBar");
const quickActions    = document.getElementById("quickActions");
const paletteSection  = document.getElementById("paletteSection");
const paletteRow      = document.getElementById("paletteRow");
const previewCanvas   = document.getElementById("previewCanvas");

let isWaiting   = false;
let downloadUrl = null;
let currentSpec = null;

/* ── Preview init ──────────────────────────────────── */
Preview.init(previewCanvas);
Preview.startLoop(() => currentSpec);

/* ── Markdown-lite renderer ────────────────────────── */
function renderMarkdown(text) {
  let html = text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
  html = html.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
  html = html.replace(/\*(.+?)\*/g, "<em>$1</em>");
  html = html.replace(/`(.+?)`/g, "<code>$1</code>");

  const lines = html.split("\n");
  const result = [];
  let inList = false;
  for (const line of lines) {
    const trimmed = line.trim();
    if (trimmed.startsWith("- ") || trimmed.startsWith("• ")) {
      if (!inList) { result.push("<ul>"); inList = true; }
      result.push(`<li>${trimmed.substring(2)}</li>`);
    } else {
      if (inList) { result.push("</ul>"); inList = false; }
      if (trimmed === "") result.push("<br>");
      else result.push(`<p>${trimmed}</p>`);
    }
  }
  if (inList) result.push("</ul>");
  return result.join("");
}

/* ── Message rendering ─────────────────────────────── */
function addMessage(role, text) {
  const div = document.createElement("div");
  div.className = `message ${role}`;

  const avatar = document.createElement("div");
  avatar.className = "message-avatar";
  avatar.textContent = role === "assistant" ? "G" : "U";

  const bubble = document.createElement("div");
  bubble.className = "message-bubble";
  bubble.innerHTML = renderMarkdown(text);

  div.appendChild(avatar);
  div.appendChild(bubble);
  chatMessages.appendChild(div);
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

/* ── Spec panel update ─────────────────────────────── */
function updateSpecPanel(spec) {
  if (!spec) {
    specPanel.innerHTML = '<div class="spec-card"><p style="color:var(--text-muted);font-size:13px;">Start describing your game to see the spec here.</p></div>';
    paletteSection.style.display = "none";
    return;
  }

  currentSpec = spec;

  const genreLabels = {
    platformer: "2D Platformer", topdown: "Top-Down Adventure",
    shooter: "Space Shooter", puzzle: "Puzzle Game",
    visual_novel: "Visual Novel", racing: "Racing Game",
  };

  let featRows = "";
  const feats = [
    ["Enemies", spec.has_enemies], ["Collectibles", spec.has_collectibles],
    ["Power-ups", spec.has_powerups], ["Dialogue", spec.has_dialogue],
    ["Particles", spec.has_particles], ["Parallax BG", spec.has_parallax_bg],
  ];
  for (const [label, val] of feats) {
    if (val) featRows += `<div class="spec-row"><span class="label">${label}</span><span class="value" style="color:var(--success)">Yes</span></div>`;
  }
  if (spec.particle_type && spec.particle_type !== "none") {
    featRows += `<div class="spec-row"><span class="label">Particle Type</span><span class="value">${spec.particle_type}</span></div>`;
  }
  if (spec.weather && spec.weather !== "none") {
    featRows += `<div class="spec-row"><span class="label">Weather</span><span class="value">${spec.weather}</span></div>`;
  }
  featRows += `<div class="spec-row"><span class="label">Difficulty</span><span class="value">${spec.difficulty}</span></div>`;

  specPanel.innerHTML = `
    <div class="spec-card">
      <h3>Game Blueprint</h3>
      <div class="spec-row"><span class="label">Name</span><span class="value">${spec.name}</span></div>
      <div class="spec-row"><span class="label">Genre</span><span class="value">${genreLabels[spec.genre] || spec.genre}</span></div>
      <div class="spec-row"><span class="label">Theme</span><span class="value">${spec.theme || "—"}</span></div>
      <div class="spec-row"><span class="label">Player</span><span class="value">${spec.player_name}</span></div>
    </div>
    <div class="spec-card">
      <h3>Features & Visuals</h3>
      ${featRows}
    </div>`;

  /* Palette */
  paletteSection.style.display = "block";
  paletteRow.innerHTML = [
    [spec.color_primary, "Player"],
    [spec.color_secondary, "Enemy"],
    [spec.color_accent, "Accent"],
    [spec.color_bg, "BG"],
    [spec.color_ground, "Ground"],
  ].map(([c, l]) => `<div class="palette-swatch" style="background:${c}" data-label="${l}" title="${l}: ${c}"></div>`).join("");
}

/* ── Suggestions rendering ─────────────────────────── */
function renderSuggestions(suggestions) {
  suggestionsBar.innerHTML = "";
  if (!suggestions || suggestions.length === 0) return;

  for (const s of suggestions) {
    const chip = document.createElement("button");
    chip.className = `suggestion-chip cat-${s.category}`;
    chip.textContent = s.text;
    chip.addEventListener("click", () => sendMessage(s.text));
    suggestionsBar.appendChild(chip);
  }
}

/* ── API call ──────────────────────────────────────── */
async function sendMessage(text) {
  if (isWaiting || !text.trim()) return;
  isWaiting = true;
  sendBtn.disabled = true;
  chatInput.value = "";
  chatInput.style.height = "50px";

  addMessage("user", text);
  typingIndicator.classList.add("active");
  progressBar.classList.add("active");

  try {
    const res = await fetch(`${API}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: SESSION_ID, message: text }),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    typingIndicator.classList.remove("active");
    progressBar.classList.remove("active");
    addMessage("assistant", data.message);

    if (data.spec) updateSpecPanel(data.spec);
    if (data.suggestions) renderSuggestions(data.suggestions);
    undoBtn.disabled = !data.can_undo;

    if (data.state !== "greeting" && data.state !== "genre_selection") {
      quickActions.style.display = "none";
    }

    if (data.game_ready && data.download_url) {
      downloadUrl = data.download_url;
      downloadArea.classList.add("visible");
      if (data.preview_log) {
        validationLog.textContent = data.preview_log;
        validationLog.classList.add("visible");
      }
    }
  } catch (err) {
    typingIndicator.classList.remove("active");
    progressBar.classList.remove("active");
    addMessage("assistant", "Something went wrong. Please try again.");
    console.error(err);
  }

  isWaiting = false;
  sendBtn.disabled = false;
  chatInput.focus();
}

/* ── Undo ──────────────────────────────────────────── */
async function doUndo() {
  if (isWaiting) return;
  isWaiting = true;
  try {
    const res = await fetch(`${API}/undo`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: SESSION_ID }),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    addMessage("assistant", data.message);
    if (data.spec) updateSpecPanel(data.spec);
    else updateSpecPanel(null);
    if (data.suggestions) renderSuggestions(data.suggestions);
    undoBtn.disabled = !data.can_undo;
  } catch (err) {
    addMessage("assistant", "Undo failed. Please try again.");
    console.error(err);
  }
  isWaiting = false;
}

/* ── Help ──────────────────────────────────────────── */
async function toggleHelp() {
  if (helpOverlay.classList.contains("active")) {
    helpOverlay.classList.remove("active");
    return;
  }
  try {
    const res = await fetch(`${API}/help/${SESSION_ID}`);
    const data = await res.json();
    if (data.help) {
      helpBody.innerHTML = renderMarkdown(data.help);
    }
  } catch (_e) { /* use static help */ }
  helpOverlay.classList.add("active");
}

/* ── Event listeners ───────────────────────────────── */
sendBtn.addEventListener("click", () => sendMessage(chatInput.value));

chatInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    sendMessage(chatInput.value);
  }
});

chatInput.addEventListener("input", () => {
  chatInput.style.height = "50px";
  chatInput.style.height = Math.min(chatInput.scrollHeight, 120) + "px";
});

downloadBtn.addEventListener("click", () => {
  if (downloadUrl) window.location.href = downloadUrl;
});

togglePanelBtn.addEventListener("click", () => {
  sidePanel.classList.toggle("hidden");
});

undoBtn.addEventListener("click", doUndo);
helpBtn.addEventListener("click", toggleHelp);
helpClose.addEventListener("click", () => helpOverlay.classList.remove("active"));
helpOverlay.addEventListener("click", (e) => {
  if (e.target === helpOverlay) helpOverlay.classList.remove("active");
});

newChatBtn.addEventListener("click", () => {
  chatMessages.innerHTML = "";
  downloadArea.classList.remove("visible");
  validationLog.classList.remove("visible");
  downloadUrl = null;
  currentSpec = null;
  quickActions.style.display = "";
  suggestionsBar.innerHTML = "";
  updateSpecPanel(null);
  undoBtn.disabled = true;
  sendMessage("start over");
});

document.querySelectorAll(".quick-btn").forEach((btn) => {
  btn.addEventListener("click", () => sendMessage(btn.dataset.msg));
});

/* ── Init ──────────────────────────────────────────── */
addMessage(
  "assistant",
  "Welcome to **Godot Game Creator** — your AI-powered game studio!\n\n" +
    "Tell me about the game you want to build. You can:\n" +
    "- Pick a genre (e.g. *\"I want a platformer\"*)\n" +
    "- Describe your idea in detail (e.g. *\"A cyberpunk shooter with " +
    "neon effects and rain particles\"*)\n" +
    "- Or just chat and I'll guide you step by step\n\n" +
    "**Pro tip:** The more visual details you describe — colors, " +
    "particle effects, backgrounds, terrain — the more polished " +
    "your game will look!\n\n" +
    "**Available genres:** Platformer · Top-Down Adventure · " +
    "Space Shooter · Puzzle · Visual Novel · Racing"
);
