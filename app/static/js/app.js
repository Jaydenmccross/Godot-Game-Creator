/**
 * Godot Game Creator — Frontend Application
 */

const API = "/api";
const SESSION_ID =
  "session_" + Math.random().toString(36).substring(2, 10);

const chatMessages = document.getElementById("chatMessages");
const chatInput = document.getElementById("chatInput");
const sendBtn = document.getElementById("sendBtn");
const typingIndicator = document.getElementById("typingIndicator");
const progressBar = document.getElementById("progressBar");
const specPanel = document.getElementById("specPanel");
const downloadArea = document.getElementById("downloadArea");
const downloadBtn = document.getElementById("downloadBtn");
const validationLog = document.getElementById("validationLog");
const togglePanelBtn = document.getElementById("togglePanel");
const newChatBtn = document.getElementById("newChat");
const sidePanel = document.getElementById("sidePanel");

let isWaiting = false;
let downloadUrl = null;

/* ---- Markdown-lite renderer ---- */
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
      if (!inList) {
        result.push("<ul>");
        inList = true;
      }
      result.push(`<li>${trimmed.substring(2)}</li>`);
    } else {
      if (inList) {
        result.push("</ul>");
        inList = false;
      }
      if (trimmed === "") {
        result.push("<br>");
      } else {
        result.push(`<p>${trimmed}</p>`);
      }
    }
  }
  if (inList) result.push("</ul>");
  return result.join("");
}

/* ---- Message rendering ---- */
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

/* ---- Spec panel update ---- */
function updateSpecPanel(spec) {
  if (!spec) {
    specPanel.innerHTML =
      '<div class="spec-card"><p style="color:var(--text-muted);font-size:13px;">Start a conversation to see your game spec here.</p></div>';
    return;
  }

  const genreLabels = {
    platformer: "2D Platformer",
    topdown: "Top-Down Adventure",
    shooter: "Space Shooter",
    puzzle: "Puzzle Game",
    visual_novel: "Visual Novel",
    racing: "Racing Game",
  };

  specPanel.innerHTML = `
    <div class="spec-card">
      <h3>Game Blueprint</h3>
      <div class="spec-row"><span class="label">Name</span><span class="value">${spec.name}</span></div>
      <div class="spec-row"><span class="label">Genre</span><span class="value">${genreLabels[spec.genre] || spec.genre}</span></div>
      <div class="spec-row"><span class="label">Theme</span><span class="value">${spec.theme || "—"}</span></div>
      <div class="spec-row"><span class="label">Player</span><span class="value">${spec.player_name}</span></div>
    </div>
    <div class="spec-card">
      <h3>Features</h3>
      <div class="spec-row"><span class="label">Enemies</span><span class="value">${spec.has_enemies ? "Yes" : "No"}</span></div>
      <div class="spec-row"><span class="label">Collectibles</span><span class="value">${spec.has_collectibles ? "Yes" : "No"}</span></div>
      <div class="spec-row"><span class="label">Power-ups</span><span class="value">${spec.has_powerups ? "Yes" : "No"}</span></div>
      <div class="spec-row"><span class="label">Dialogue</span><span class="value">${spec.has_dialogue ? "Yes" : "No"}</span></div>
      <div class="spec-row"><span class="label">Difficulty</span><span class="value">${spec.difficulty}</span></div>
    </div>
  `;
}

/* ---- API call ---- */
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

/* ---- Event listeners ---- */
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

newChatBtn.addEventListener("click", () => {
  chatMessages.innerHTML = "";
  downloadArea.classList.remove("visible");
  validationLog.classList.remove("visible");
  downloadUrl = null;
  updateSpecPanel(null);
  sendMessage("start over");
});

/* ---- Quick actions ---- */
document.querySelectorAll(".quick-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    sendMessage(btn.dataset.msg);
  });
});

/* ---- Init ---- */
addMessage(
  "assistant",
  "Welcome to **Godot Game Creator** — your AI-powered game studio!\n\n" +
    "Tell me about the game you want to build. You can:\n" +
    "- Pick a genre (e.g. *\"I want a platformer\"*)\n" +
    "- Describe your idea (e.g. *\"A space shooter where you fight aliens\"*)\n" +
    "- Or just chat and I'll guide you step by step\n\n" +
    "**Available genres:** Platformer · Top-Down Adventure · " +
    "Space Shooter · Puzzle · Visual Novel · Racing"
);
