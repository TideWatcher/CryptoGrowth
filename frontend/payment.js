// Payment modal logic

function showPaywall() {
  document.getElementById("paywall-overlay").classList.remove("hidden");
  loadUSDTAddress();
  loadPaymentsConfig();
}

async function loadPaymentsConfig() {
  try {
    const res = await fetch("/payments/config");
    const data = await res.json();

    const cardTab = document.querySelector('.payment-tab[data-tab="card"]');
    const airwallexTab = document.querySelector('.payment-tab[data-tab="airwallex"]');

    if (!data.stripe_enabled) cardTab.style.display = "none";
    if (!data.airwallex_enabled) airwallexTab.style.display = "none";

    // if the active tab is now hidden, switch to the first visible tab
    const activeTab = document.querySelector(".payment-tab.active");
    if (activeTab && activeTab.style.display === "none") {
      const firstVisible = [...document.querySelectorAll(".payment-tab")].find(t => t.style.display !== "none");
      if (firstVisible) firstVisible.click();
    }
  } catch { }
}

function hidePaywall() {
  document.getElementById("paywall-overlay").classList.add("hidden");
}

async function loadUSDTAddress() {
  try {
    const res = await fetch("/payments/usdt/address");
    const data = await res.json();
    const el = document.getElementById("usdt-address-display");
    if (data.address) {
      el.textContent = data.address;
    } else {
      el.textContent = "暂未配置 USDT 地址，请联系客服";
    }
  } catch { }
}

// Payment tabs
document.querySelectorAll(".payment-tab").forEach(tab => {
  tab.addEventListener("click", () => {
    document.querySelectorAll(".payment-tab").forEach(t => t.classList.remove("active"));
    document.querySelectorAll(".payment-panel").forEach(p => p.classList.remove("active"));
    tab.classList.add("active");
    document.getElementById(`panel-${tab.dataset.tab}`).classList.add("active");
  });
});

// Stripe checkout
document.getElementById("btn-stripe-pay").addEventListener("click", async () => {
  const btn = document.getElementById("btn-stripe-pay");
  btn.disabled = true; btn.textContent = "跳转中...";
  try {
    const res = await fetch("/payments/stripe/checkout", {
      method: "POST",
      credentials: "include",
    });
    if (res.status === 401) { showAuthModal(); return; }
    const data = await res.json();
    if (data.url) window.location.href = data.url;
    else btn.textContent = "出错了，请重试";
  } catch {
    btn.textContent = "出错了，请重试";
  } finally {
    btn.disabled = false;
  }
});

// Airwallex checkout
document.getElementById("btn-airwallex-pay").addEventListener("click", async () => {
  const btn = document.getElementById("btn-airwallex-pay");
  btn.disabled = true; btn.textContent = "跳转中...";
  try {
    const res = await fetch("/payments/airwallex/checkout", {
      method: "POST",
      credentials: "include",
    });
    if (res.status === 401) { showAuthModal(); return; }
    const data = await res.json();
    if (data.url) window.location.href = data.url;
    else btn.textContent = "出错了，请重试";
  } catch {
    btn.textContent = "出错了，请重试";
  } finally {
    btn.disabled = false;
  }
});

// Copy USDT address
document.getElementById("copy-usdt-addr").addEventListener("click", () => {
  const addr = document.getElementById("usdt-address-display").textContent;
  navigator.clipboard.writeText(addr).then(() => {
    const btn = document.getElementById("copy-usdt-addr");
    btn.textContent = "已复制";
    setTimeout(() => { btn.textContent = "复制地址"; }, 1500);
  });
});

// USDT submit
document.getElementById("btn-usdt-submit").addEventListener("click", async () => {
  const txHash = document.getElementById("usdt-tx-hash").value.trim();
  const errEl = document.getElementById("usdt-error");
  errEl.textContent = "";
  if (!txHash) { errEl.textContent = "请粘贴交易哈希"; return; }

  const btn = document.getElementById("btn-usdt-submit");
  btn.disabled = true; btn.textContent = "提交中...";
  try {
    const res = await fetch("/payments/usdt/submit", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({ tx_hash: txHash }),
    });
    const data = await res.json();
    if (res.ok) {
      errEl.style.color = "var(--green)";
      errEl.textContent = data.message;
      document.getElementById("usdt-tx-hash").value = "";
    } else {
      errEl.style.color = "#f85149";
      errEl.textContent = data.detail || "提交失败";
    }
  } catch {
    errEl.textContent = "网络错误，请重试";
  } finally {
    btn.disabled = false; btn.textContent = "提交审核";
  }
});

document.getElementById("close-paywall").addEventListener("click", hidePaywall);

// expose for app.js
window.showPaywall = showPaywall;
