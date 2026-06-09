const API_BASE = "";

const state = {
  style: "kol",
  language: "zh",
  loading: false,
};

function $(id) { return document.getElementById(id); }

function setStyle(s) {
  state.style = s;
  document.querySelectorAll(".btn-style").forEach(b => b.classList.toggle("active", b.dataset.style === s));
}

function setLanguage(l) {
  state.language = l;
  document.querySelectorAll(".btn-lang").forEach(b => b.classList.toggle("active", b.dataset.lang === l));
}

function getCheckedTypes() {
  return ["wechat", "twitter"].filter(t => document.getElementById(`type-${t}`).checked);
}

function showSkeleton(cardId) {
  const el = document.getElementById(`${cardId}-content`);
  el.innerHTML = `
    <div class="skeleton wide"></div>
    <div class="skeleton medium"></div>
    <div class="skeleton wide"></div>
    <div class="skeleton short"></div>
    <div class="skeleton wide" style="margin-top:10px"></div>
    <div class="skeleton medium"></div>
  `;
  document.getElementById(`${cardId}-count`).textContent = "";
}

function setCardContent(cardId, text) {
  const el = document.getElementById(`${cardId}-content`);
  el.textContent = text;
  const count = cardId === "wechat"
    ? `${text.length} 字`
    : `${text.split(/\n\n+/).filter(t => t.trim()).length} 条`;
  document.getElementById(`${cardId}-count`).textContent = count;
}

function setPlaceholder(cardId, msg) {
  const el = document.getElementById(`${cardId}-content`);
  el.innerHTML = `<span class="placeholder-text">${msg}</span>`;
  document.getElementById(`${cardId}-count`).textContent = "";
}

function splitContent(raw) {
  const wechatMarkers = ["【公众号长文】", "【WeChat Article】", "# 公众号", "公众号长文", "WeChat"];
  const twitterMarkers = ["【X Thread】", "# X Thread", "X Thread", "Twitter Thread", "Thread"];

  let wechat = "", twitter = "";

  // Try to find clear markers
  const lines = raw.split("\n");
  let currentSection = null;
  const sections = { wechat: [], twitter: [] };

  for (const line of lines) {
    const isWechat = wechatMarkers.some(m => line.includes(m));
    const isTwitter = twitterMarkers.some(m => line.includes(m));

    if (isWechat) { currentSection = "wechat"; continue; }
    if (isTwitter) { currentSection = "twitter"; continue; }

    if (currentSection) sections[currentSection].push(line);
  }

  wechat = sections.wechat.join("\n").trim();
  twitter = sections.twitter.join("\n").trim();

  // Fallback: if no markers found but both requested, split at midpoint
  if (!wechat && !twitter) {
    const mid = raw.indexOf("\n\n1/");
    if (mid > 0) {
      wechat = raw.slice(0, mid).trim();
      twitter = raw.slice(mid).trim();
    } else {
      wechat = raw;
    }
  }

  return { wechat: wechat || raw, twitter };
}

async function generate() {
  const rawMaterial = $("raw-material").value.trim();
  if (!rawMaterial) {
    $("error-msg").textContent = "请先粘贴原始素材";
    $("error-msg").style.display = "block";
    return;
  }

  const contentTypes = getCheckedTypes();
  if (contentTypes.length === 0) {
    $("error-msg").textContent = "请至少选择一种输出格式";
    $("error-msg").style.display = "block";
    return;
  }

  $("error-msg").style.display = "none";

  if (contentTypes.includes("wechat")) showSkeleton("wechat");
  else setPlaceholder("wechat", "未选择公众号格式");

  if (contentTypes.includes("twitter")) showSkeleton("twitter");
  else setPlaceholder("twitter", "未选择 X Thread 格式");

  $("generate-btn").disabled = true;
  $("generate-btn").textContent = "生成中...";

  try {
    const res = await fetch(`${API_BASE}/api/generate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        raw_material: rawMaterial,
        content_types: contentTypes,
        style: state.style,
        language: state.language,
      }),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `HTTP ${res.status}`);
    }

    const data = await res.json();
    const { wechat, twitter } = splitContent(data.content);

    if (contentTypes.includes("wechat")) {
      setCardContent("wechat", wechat);
    }
    if (contentTypes.includes("twitter")) {
      setCardContent("twitter", twitter || data.content);
    }
  } catch (e) {
    $("error-msg").textContent = `生成失败：${e.message}`;
    $("error-msg").style.display = "block";
    if (contentTypes.includes("wechat")) setPlaceholder("wechat", "生成失败，请重试");
    if (contentTypes.includes("twitter")) setPlaceholder("twitter", "生成失败，请重试");
  } finally {
    $("generate-btn").disabled = false;
    $("generate-btn").textContent = "生成内容";
  }
}

function copyCard(cardId) {
  const el = document.getElementById(`${cardId}-content`);
  const text = el.textContent;
  if (!text || el.querySelector(".placeholder-text")) return;

  navigator.clipboard.writeText(text).then(() => {
    const btn = document.getElementById(`copy-${cardId}`);
    btn.textContent = "已复制";
    btn.classList.add("copied");
    setTimeout(() => { btn.textContent = "复制"; btn.classList.remove("copied"); }, 1500);
  });
}

document.addEventListener("DOMContentLoaded", () => {
  // Wire style buttons
  document.querySelectorAll(".btn-style").forEach(b => {
    b.addEventListener("click", () => setStyle(b.dataset.style));
  });

  // Wire language buttons
  document.querySelectorAll(".btn-lang").forEach(b => {
    b.addEventListener("click", () => setLanguage(b.dataset.lang));
  });

  // Wire copy buttons
  document.getElementById("copy-wechat").addEventListener("click", () => copyCard("wechat"));
  document.getElementById("copy-twitter").addEventListener("click", () => copyCard("twitter"));

  // Wire generate
  $("generate-btn").addEventListener("click", generate);

  // Ctrl/Cmd+Enter to generate
  $("raw-material").addEventListener("keydown", e => {
    if ((e.ctrlKey || e.metaKey) && e.key === "Enter") generate();
  });
});
