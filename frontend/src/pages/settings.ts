import { getJson, postJson } from "../api/client";
import { mountPage, card } from "../components/page";

interface BrokerStatus {
  broker: string;
  connected: boolean;
  expires_at: number | null;
  expires_in_hours: number | null;
  error: string | null;
}

async function fetchFyersStatus(): Promise<BrokerStatus> {
  return getJson<BrokerStatus>("/brokers/fyers/status");
}

async function getAuthUrl(): Promise<{ auth_url: string }> {
  return getJson<{ auth_url: string }>("/brokers/fyers/auth-url");
}

async function connectFyers(redirectUrl: string): Promise<{ ok: boolean; message: string }> {
  return postJson<{ ok: boolean; message: string }>("/brokers/fyers/connect", { redirect_url: redirectUrl });
}

async function refreshFyers(): Promise<{ ok: boolean; message: string; expires_at?: number }> {
  return postJson<{ ok: boolean; message: string; expires_at?: number }>("/brokers/fyers/refresh", {});
}

async function disconnectFyers(): Promise<{ ok: boolean; message: string }> {
  return postJson<{ ok: boolean; message: string }>("/brokers/fyers/disconnect", {});
}

function formatExpiry(expiresAt: number | null): string {
  if (!expiresAt) return "—";
  const now = Date.now() / 1000;
  const diff = expiresAt - now;
  if (diff <= 0) return "Expired";
  const hours = Math.floor(diff / 3600);
  const days = Math.floor(hours / 24);
  if (days > 0) return `${days}d ${hours % 24}h`;
  return `${hours}h`;
}

function renderBrokerCard(status: BrokerStatus): string {
  const connected = status.connected;
  const badgeClass = connected ? "badge ok" : "badge fail";
  const statusText = connected ? "Connected" : "Not connected";
  const expiresText = formatExpiry(status.expires_at);
  const errorText = status.error ? `<p class="error">${status.error}</p>` : "";

  return `
    <div class="card">
      <h3>Fyers</h3>
      <p>Status: <span class="badge ${badgeClass}">${statusText}</span></p>
      <p>Token expires: <b>${expiresText}</b></p>
      ${errorText}
      <div id="fyers-actions">
        ${connected ? `
          <button id="fyers-refresh" ${!status.expires_at ? "disabled" : ""}>Refresh Token</button>
          <button id="fyers-disconnect" style="background: var(--red); margin-left: 8px;">Disconnect</button>
        ` : `
          <button id="fyers-connect">Connect Fyers</button>
        `}
      </div>
      <div id="fyers-connect-form" style="display: none; margin-top: 12px;">
        <p>1. <a id="fyers-auth-link" href="#" target="_blank">Click here to login to Fyers</a></p>
        <p>2. After login, paste the <b>full redirect URL</b> here:</p>
        <input id="fyers-redirect-url" type="text" placeholder="https://trade.fyers.in/...auth_code=...&state=..." style="width: 100%;">
        <button id="fyers-submit-connect" style="margin-top: 8px;">Submit</button>
        <button id="fyers-cancel-connect" style="margin-top: 8px; background: var(--muted);">Cancel</button>
      </div>
    </div>
  `;
}

export function render(el: HTMLElement): Promise<void> {
  return mountPage(el, "Settings", async () => {
    let html = `
      <h3>Brokers</h3>
      <div id="brokers-container">Loading...</div>
    `;
    return html;
  }).then(() => {
    // Brokers
    const container = el.querySelector("#brokers-container") as HTMLElement;

    async function loadBrokerStatus() {
      try {
        const status = await fetchFyersStatus();
        container.innerHTML = renderBrokerCard(status);
        attachBrokerHandlers();
      } catch (e) {
        container.innerHTML = `<div class="error">Failed to load broker status: ${e}</div>`;
      }
    }

    function attachBrokerHandlers() {
      // Connect
      const connectBtn = el.querySelector("#fyers-connect") as HTMLButtonElement | null;
      connectBtn?.addEventListener("click", async () => {
        try {
          const { auth_url } = await getAuthUrl();
          const link = el.querySelector("#fyers-auth-link") as HTMLAnchorElement;
          link.href = auth_url;
          link.textContent = "Open Fyers Login";
          (el.querySelector("#fyers-actions") as HTMLElement).style.display = "none";
          (el.querySelector("#fyers-connect-form") as HTMLElement).style.display = "block";
        } catch (e) {
          alert(`Failed to get auth URL: ${e}`);
        }
      });

      // Submit connect
      const submitBtn = el.querySelector("#fyers-submit-connect") as HTMLButtonElement | null;
      submitBtn?.addEventListener("click", async () => {
        const redirectUrl = (el.querySelector("#fyers-redirect-url") as HTMLInputElement).value.trim();
        if (!redirectUrl) { alert("Paste the redirect URL"); return; }
        submitBtn.disabled = true;
        submitBtn.textContent = "Connecting...";
        try {
          await connectFyers(redirectUrl);
          await loadBrokerStatus();
        } catch (e) {
          alert(`Connect failed: ${e}`);
          submitBtn.disabled = false;
          submitBtn.textContent = "Submit";
        }
      });

      // Cancel connect
      const cancelBtn = el.querySelector("#fyers-cancel-connect") as HTMLButtonElement | null;
      cancelBtn?.addEventListener("click", () => {
        (el.querySelector("#fyers-connect-form") as HTMLElement).style.display = "none";
        (el.querySelector("#fyers-actions") as HTMLElement).style.display = "block";
      });

      // Refresh
      const refreshBtn = el.querySelector("#fyers-refresh") as HTMLButtonElement | null;
      refreshBtn?.addEventListener("click", async () => {
        refreshBtn.disabled = true;
        refreshBtn.textContent = "Refreshing...";
        try {
          await refreshFyers();
          await loadBrokerStatus();
        } catch (e) {
          alert(`Refresh failed: ${e}`);
          refreshBtn.disabled = false;
          refreshBtn.textContent = "Refresh Token";
        }
      });

      // Disconnect
      const disconnectBtn = el.querySelector("#fyers-disconnect") as HTMLButtonElement | null;
      disconnectBtn?.addEventListener("click", async () => {
        if (!confirm("Disconnect Fyers? This will delete the saved token.")) return;
        disconnectBtn.disabled = true;
        disconnectBtn.textContent = "Disconnecting...";
        try {
          await disconnectFyers();
          await loadBrokerStatus();
        } catch (e) {
          alert(`Disconnect failed: ${e}`);
          disconnectBtn.disabled = false;
          disconnectBtn.textContent = "Disconnect";
        }
      });
    }

    loadBrokerStatus();
  });
}
