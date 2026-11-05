import { postJson } from "../api/client";
import { mountPage, card } from "../components/page";
import { navigation } from "../components/navigation";

let loginInProgress = false;

export function render(el: HTMLElement): Promise<void> {
  // Login page doesn't show navigation
  const nav = document.querySelector("nav");
  if (nav) nav.innerHTML = "";

  return mountPage(el, "Login", async () => {
    return card(`
      <div style="max-width: 400px; margin: 40px auto;">
        <h2 style="text-align: center; margin-bottom: 24px;">Strategy Lab</h2>
        <form id="login-form">
          <div>
            <label for="username">Username</label>
            <input id="username" name="username" type="text" required autocomplete="username" style="width: 100%;">
          </div>
          <div style="margin-top: 12px;">
            <label for="password">Password</label>
            <input id="password" name="password" type="password" required autocomplete="current-password" style="width: 100%;">
          </div>
          <div id="login-error" class="error" style="display: none; margin-top: 12px;"></div>
          <button type="submit" id="login-btn" style="width: 100%; margin-top: 16px;">Login</button>
        </form>
        <p style="text-align: center; margin-top: 16px; color: var(--muted); font-size: 14px;">
          Session cookie (HttpOnly, SameSite=Strict) will be set on success.
        </p>
      </div>
    `);
  }).then(() => {
    const form = el.querySelector("#login-form") as HTMLFormElement;
    const errorEl = el.querySelector("#login-error") as HTMLElement;
    const btn = el.querySelector("#login-btn") as HTMLButtonElement;

    form?.addEventListener("submit", async (e) => {
      e.preventDefault();
      if (loginInProgress) return;
      loginInProgress = true;
      btn.disabled = true;
      btn.textContent = "Logging in...";
      errorEl.style.display = "none";

      const username = (form.querySelector("#username") as HTMLInputElement).value;
      const password = (form.querySelector("#password") as HTMLInputElement).value;

      try {
        await postJson("/auth/login", { username, password });
        location.hash = "#dashboard";
      } catch (err) {
        errorEl.textContent = String(err);
        errorEl.style.display = "block";
        btn.disabled = false;
        btn.textContent = "Login";
      } finally {
        loginInProgress = false;
      }
    });
  });
}