// Auth state
window.currentUser = null;

async function checkAuth() {
  const res = await fetch("/auth/me", { credentials: "include" });
  const data = await res.json();
  if (data.logged_in) {
    window.currentUser = data.user;
    showApp();
  } else {
    showAuthModal();
  }
}

function showApp() {
  document.getElementById("auth-overlay").classList.add("hidden");
  updateHeader();
  // Check payment success/fail in URL
  const params = new URLSearchParams(location.search);
  if (params.get("payment") === "success") {
    showToast("🎉 订阅成功！感谢支持");
    history.replaceState({}, "", "/");
    checkAuth(); // refresh user state
  } else if (params.get("payment") === "cancelled" || params.get("payment") === "failed") {
    history.replaceState({}, "", "/");
  }
}

function showAuthModal(tab) {
  document.getElementById("auth-overlay").classList.remove("hidden");
  if (tab === "register") showRegister();
  else showLogin();
}

function showLogin() {
  document.getElementById("login-form").style.display = "block";
  document.getElementById("register-form").style.display = "none";
  document.getElementById("login-error").textContent = "";
}

function showRegister() {
  document.getElementById("login-form").style.display = "none";
  document.getElementById("register-form").style.display = "block";
  document.getElementById("register-error").textContent = "";
}

function updateHeader() {
  const u = window.currentUser;
  if (!u) return;
  document.getElementById("header-user").style.display = "flex";
  document.getElementById("user-name").textContent = u.name || u.email;

  const badge = document.getElementById("usage-badge");
  if (u.is_subscribed) {
    badge.textContent = "已订阅 ∞";
    badge.className = "usage-badge subscribed";
  } else {
    badge.textContent = `剩余 ${u.free_uses_remaining} 次免费`;
    badge.className = u.free_uses_remaining <= 1 ? "usage-badge warning" : "usage-badge";
  }
}

function updateUsage(freeRemaining, isSubscribed) {
  if (window.currentUser) {
    window.currentUser.free_uses_remaining = freeRemaining;
    window.currentUser.is_subscribed = isSubscribed;
    updateHeader();
  }
}

// Google login — show only if configured
async function initGoogleButton() {
  try {
    const res = await fetch("/auth/me", { credentials: "include" });
    // Check if Google OAuth is configured by probing
    const probe = await fetch("/auth/google", { method: "HEAD", redirect: "manual" });
    if (probe.status !== 501) {
      document.querySelectorAll(".btn-google").forEach(b => b.style.display = "flex");
      document.querySelectorAll("[id^='google-divider']").forEach(d => d.style.display = "flex");
    }
  } catch {}
}

function showToast(msg) {
  const t = document.createElement("div");
  t.style.cssText = `
    position:fixed;bottom:24px;left:50%;transform:translateX(-50%);
    background:#161b22;border:1px solid #30363d;color:#e6edf3;
    padding:10px 20px;border-radius:8px;font-size:14px;z-index:200;
    box-shadow:0 4px 16px rgba(0,0,0,0.4);
  `;
  t.textContent = msg;
  document.body.appendChild(t);
  setTimeout(() => t.remove(), 3000);
}

// ── Event wiring ──────────────────────────────────────────────

document.getElementById("to-register").addEventListener("click", showRegister);
document.getElementById("to-login").addEventListener("click", showLogin);

document.getElementById("btn-login").addEventListener("click", async () => {
  const email = document.getElementById("login-email").value.trim();
  const password = document.getElementById("login-password").value;
  const errEl = document.getElementById("login-error");
  errEl.textContent = "";
  if (!email || !password) { errEl.textContent = "请填写邮箱和密码"; return; }

  const btn = document.getElementById("btn-login");
  btn.disabled = true; btn.textContent = "登录中...";
  try {
    const res = await fetch("/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({ email, password }),
    });
    const data = await res.json();
    if (!res.ok) { errEl.textContent = data.detail || "登录失败"; return; }
    window.currentUser = data.user;
    showApp();
  } catch { errEl.textContent = "网络错误，请重试"; }
  finally { btn.disabled = false; btn.textContent = "登录"; }
});

document.getElementById("btn-register").addEventListener("click", async () => {
  const name = document.getElementById("reg-name").value.trim();
  const email = document.getElementById("reg-email").value.trim();
  const password = document.getElementById("reg-password").value;
  const errEl = document.getElementById("register-error");
  errEl.textContent = "";
  if (!email || !password) { errEl.textContent = "请填写邮箱和密码"; return; }
  if (password.length < 6) { errEl.textContent = "密码至少 6 位"; return; }

  const btn = document.getElementById("btn-register");
  btn.disabled = true; btn.textContent = "注册中...";
  try {
    const res = await fetch("/auth/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({ email, password, name }),
    });
    const data = await res.json();
    if (!res.ok) { errEl.textContent = data.detail || "注册失败"; return; }
    window.currentUser = data.user;
    showApp();
  } catch { errEl.textContent = "网络错误，请重试"; }
  finally { btn.disabled = false; btn.textContent = "注册并开始使用"; }
});

document.getElementById("btn-logout").addEventListener("click", async () => {
  await fetch("/auth/logout", { method: "POST", credentials: "include" });
  window.currentUser = null;
  document.getElementById("header-user").style.display = "none";
  showAuthModal();
});

document.querySelectorAll(".btn-google").forEach(b => {
  b.addEventListener("click", () => { window.location.href = "/auth/google"; });
});

// Enter key on login form
document.getElementById("login-password").addEventListener("keydown", e => {
  if (e.key === "Enter") document.getElementById("btn-login").click();
});
document.getElementById("reg-password").addEventListener("keydown", e => {
  if (e.key === "Enter") document.getElementById("btn-register").click();
});

// Init
initGoogleButton();
checkAuth();
