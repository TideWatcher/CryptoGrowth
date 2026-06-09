const API_BASE = "";

const MAX_STYLES = 3;

const state = {
  styles: ["kol"],
  language: "zh",
  wechatLength: "1000-1500",
  twitterLength: "5",
};

function $(id) { return document.getElementById(id); }

function toggleStyle(s) {
  const idx = state.styles.indexOf(s);
  if (idx !== -1) {
    if (state.styles.length > 1) state.styles.splice(idx, 1);
  } else if (state.styles.length < MAX_STYLES) {
    state.styles.push(s);
  }
  document.querySelectorAll(".btn-style").forEach(b => b.classList.toggle("active", state.styles.includes(b.dataset.style)));
}

function setLanguage(l) {
  state.language = l;
  document.querySelectorAll(".btn-lang").forEach(b => b.classList.toggle("active", b.dataset.lang === l));
}

function getCheckedTypes() {
  return ["wechat", "twitter"].filter(t => document.getElementById(`type-${t}`).checked);
}

function updateSubOptions() {
  $("wechat-length-options").classList.toggle("disabled", !$("type-wechat").checked);
  $("twitter-length-options").classList.toggle("disabled", !$("type-twitter").checked);
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
  const actions = document.getElementById(`${cardId}-actions`);
  if (actions) actions.style.display = "none";
}

function setCardContent(cardId, text) {
  const el = document.getElementById(`${cardId}-content`);
  el.textContent = text;
  const count = cardId === "wechat"
    ? `${text.length} 字`
    : `${text.split(/\n\n+/).filter(t => t.trim()).length} 条`;
  document.getElementById(`${cardId}-count`).textContent = count;
  const actions = document.getElementById(`${cardId}-actions`);
  if (actions) actions.style.display = "flex";
}

function setPlaceholder(cardId, msg) {
  const el = document.getElementById(`${cardId}-content`);
  el.innerHTML = `<span class="placeholder-text">${msg}</span>`;
  document.getElementById(`${cardId}-count`).textContent = "";
  const actions = document.getElementById(`${cardId}-actions`);
  if (actions) actions.style.display = "none";
}

function isSeparator(line) {
  return /^[-*_]{3,}$/.test(line.trim());
}

function stripSeparators(text) {
  return text
    .split("\n")
    .filter(line => !isSeparator(line))
    .join("\n")
    .trim();
}

function splitContent(raw) {
  const wechatMarkers = ["【公众号长文】", "【WeChat Article】", "公众号长文", "WeChat"];
  const twitterMarkers = ["【X Thread】", "X Thread", "Twitter Thread"];

  const lines = raw.split("\n");
  let currentSection = null;
  const sections = { wechat: [], twitter: [] };

  for (const line of lines) {
    if (wechatMarkers.some(m => line.includes(m))) { currentSection = "wechat"; continue; }
    if (twitterMarkers.some(m => line.includes(m))) { currentSection = "twitter"; continue; }
    if (currentSection) sections[currentSection].push(line);
  }

  let wechat = stripSeparators(sections.wechat.join("\n").trim());
  let twitter = stripSeparators(sections.twitter.join("\n").trim());

  if (!wechat && !twitter) {
    const mid = raw.indexOf("\n\n1/");
    if (mid > 0) {
      wechat = stripSeparators(raw.slice(0, mid).trim());
      twitter = stripSeparators(raw.slice(mid).trim());
    } else {
      wechat = stripSeparators(raw);
    }
  }

  return { wechat: wechat || stripSeparators(raw), twitter };
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
      credentials: "include",
      body: JSON.stringify({
        raw_material: rawMaterial,
        content_types: contentTypes,
        styles: state.styles,
        language: state.language,
        wechat_length: state.wechatLength,
        twitter_length: state.twitterLength,
      }),
    });

    if (res.status === 401) {
      showAuthModal();
      setPlaceholder("wechat", "请登录后使用");
      setPlaceholder("twitter", "请登录后使用");
      return;
    }

    if (res.status === 402) {
      showPaywall();
      setPlaceholder("wechat", "免费次数已用完，请订阅");
      setPlaceholder("twitter", "免费次数已用完，请订阅");
      return;
    }

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `HTTP ${res.status}`);
    }

    const data = await res.json();

    // Update usage display
    if (typeof data.free_uses_remaining === "number") {
      updateUsage(data.free_uses_remaining, data.is_subscribed);
    }

    const { wechat, twitter } = splitContent(data.content);

    if (contentTypes.includes("wechat")) setCardContent("wechat", wechat);
    if (contentTypes.includes("twitter")) {
      setCardContent("twitter", twitter || data.content);
      const copyFirstBtn = $("copy-twitter-first");
      const hint = document.querySelector("#twitter-actions .action-hint");
      const isSingle = state.twitterLength === "single";
      copyFirstBtn.style.display = isSingle ? "none" : "";
      hint.textContent = isSingle ? "复制全文后前往 X 发布" : "复制第 1 条后前往 X 发布 Thread";
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
    setTimeout(() => { btn.textContent = "复制全文"; btn.classList.remove("copied"); }, 1500);
  });
}

document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".btn-style").forEach(b => {
    b.addEventListener("click", () => toggleStyle(b.dataset.style));
  });
  document.querySelectorAll(".btn-lang").forEach(b => {
    b.addEventListener("click", () => setLanguage(b.dataset.lang));
  });
  document.getElementById("type-wechat").addEventListener("change", updateSubOptions);
  document.getElementById("type-twitter").addEventListener("change", updateSubOptions);
  updateSubOptions();
  document.querySelectorAll('input[name="wechat-length"]').forEach(r => {
    r.addEventListener("change", () => { if (r.checked) state.wechatLength = r.value; });
  });
  document.querySelectorAll('input[name="twitter-length"]').forEach(r => {
    r.addEventListener("change", () => { if (r.checked) state.twitterLength = r.value; });
  });
  document.getElementById("copy-wechat").addEventListener("click", () => copyCard("wechat"));
  document.getElementById("copy-twitter").addEventListener("click", () => copyCard("twitter"));

  document.getElementById("copy-twitter-first").addEventListener("click", () => {
    const el = document.getElementById("twitter-content");
    const text = el.textContent;
    if (!text || el.querySelector(".placeholder-text")) return;
    const paragraphs = text.split(/\n\n+/).filter(t => t.trim() && !isSeparator(t));
    const startIdx = paragraphs.findIndex(p => /^\d+\//.test(p.trim()));
    let first;
    if (startIdx === -1) {
      first = paragraphs[0] || text;
    } else {
      let endIdx = paragraphs.findIndex((p, i) => i > startIdx && /^\d+\//.test(p.trim()));
      if (endIdx === -1) endIdx = paragraphs.length;
      first = paragraphs.slice(startIdx, endIdx).join("\n\n");
    }
    navigator.clipboard.writeText(first.trim()).then(() => {
      const btn = document.getElementById("copy-twitter-first");
      btn.textContent = "已复制";
      btn.classList.add("copied");
      setTimeout(() => { btn.textContent = "📋 复制第 1 条"; btn.classList.remove("copied"); }, 1500);
    });
  });

  $("generate-btn").addEventListener("click", generate);
  $("raw-material").addEventListener("keydown", e => {
    if ((e.ctrlKey || e.metaKey) && e.key === "Enter") generate();
  });
});
