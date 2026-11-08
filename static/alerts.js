/* Alerts: email / SMS / web-push settings (every role), push on this device, delivery log for admins. */

const urlB64ToBytes = (b64) => {
  const pad = "=".repeat((4 - (b64.length % 4)) % 4);
  const raw = atob((b64 + pad).replace(/-/g, "+").replace(/_/g, "/"));
  return Uint8Array.from([...raw].map((c) => c.charCodeAt(0)));
};
const pushSupported = () => "serviceWorker" in navigator && "PushManager" in window && "Notification" in window && window.isSecureContext;

async function registerSW() {
  if (!("serviceWorker" in navigator) || !window.isSecureContext) return null;
  try {
    return await navigator.serviceWorker.register("/sw.js");
  } catch (err) {
    return null;
  }
}
async function thisDeviceSub() {
  if (!pushSupported()) return null;
  const reg = await navigator.serviceWorker.getRegistration();
  return reg ? reg.pushManager.getSubscription() : null;
}
async function pushEnable(vapidKey) {
  if (!pushSupported())
    throw new Error("Push isn't available here. Use HTTPS (or localhost); on iPhone, add HemoLink to the Home Screen first.");
  if (!vapidKey) throw new Error("Push isn't set up on this server (pywebpush missing).");
  const perm = await Notification.requestPermission();
  if (perm !== "granted") throw new Error("Notifications are blocked for this site — allow them in your browser settings.");
  const reg = (await registerSW()) || (await navigator.serviceWorker.ready);
  await navigator.serviceWorker.ready;
  const sub = await reg.pushManager.subscribe({ userVisibleOnly: true, applicationServerKey: urlB64ToBytes(vapidKey) });
  const j = sub.toJSON();
  await send("/api/push/subscribe", { endpoint: j.endpoint, keys: j.keys, user_agent: navigator.userAgent.slice(0, 200) });
}
async function pushDisable() {
  const sub = await thisDeviceSub();
  if (!sub) return;
  await api("/api/push/subscribe", { method: "DELETE", body: JSON.stringify({ endpoint: sub.endpoint }) });
  await sub.unsubscribe();
}

// outbox times are stored in UTC by SQLite — show them in the viewer's time zone
const whenLocal = (t) => {
  const d = new Date(String(t).replace(" ", "T") + "Z");
  return isNaN(d) ? String(t) : d.toLocaleString(state.lang === "ms" ? "ms-MY" : "en-MY", { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" });
};
const liveTag = (ch) => `<span class="tag ${ch.live ? "tag-green" : "tag-gray"}">${ch.live ? "Live" : "Demo mode"}</span>`;

async function loadAlertSettings() {
  const box = document.getElementById("alerts-card");
  if (!box) return;
  const [s, sub] = await Promise.all([api("/api/notify/settings"), thisDeviceSub().catch(() => null)]);
  const ch = s.channels;
  const donor = state.user.role === "donor";
  const sw = (name, on, title, sub2, extra = "") =>
    `<label class="al-row"><span class="al-switch"><input type="checkbox" name="${name}" ${on ? "checked" : ""}/><i></i></span><span class="al-text"><b>${title}</b><small>${sub2}</small></span>${extra}</label>`;
  box.innerHTML = `<div class="panel-title"><h3>${icon("bell", "icon-sm")} Alerts &amp; language</h3></div>
 <form data-alerts-form class="al-form">
 <div class="al-lang"><span class="muted small semibold">Language · Bahasa</span><div class="seg">
 <label><input type="radio" name="lang" value="en" ${s.lang !== "ms" ? "checked" : ""}/><span>English</span></label>
 <label><input type="radio" name="lang" value="ms" ${s.lang === "ms" ? "checked" : ""}/><span>Bahasa Melayu</span></label></div></div>
 ${sw("notify_email", s.notify_email, "Email", `To ${e(state.user.email)}`, liveTag(ch.email))}
 ${sw("notify_sms", s.notify_sms, "SMS", donor ? "Urgent requests and appointment reminders only" : "Important updates only", liveTag(ch.sms))}
 <div class="field al-phone"><label>Mobile number (for SMS)</label><input class="input" name="phone" value="${e(s.phone)}" placeholder="012-345 6789" maxlength="24" inputmode="tel"/></div>
 ${sw("notify_push", s.notify_push, "Push notifications", sub ? "On for this device ✓" : s.push_devices ? `On for ${s.push_devices} other device(s)` : "Pop-up alerts on your phone or computer",
   `<button type="button" class="btn btn-light btn-sm" data-action="${sub ? "push-off" : "push-on"}">${sub ? "Turn off here" : "Enable on this device"}</button>`)}
 ${donor ? sw("notify_nearby", s.notify_nearby, "New drives near me", "When a campaign opens within 25 km of your city") : ""}
 <div class="filters" style="margin-top:6px"><button class="btn btn-primary" type="submit">${icon("check", "icon-sm")} Save alert settings</button><button type="button" class="btn btn-light" data-action="notify-test">Send me a test alert</button></div>
 ${!ch.email.live || !ch.sms.live ? `<p class="muted tiny" style="margin-top:6px">${icon("info", "icon-sm")} Demo mode: ${[!ch.email.live && "email", !ch.sms.live && "SMS"].filter(Boolean).join(" and ")} aren't connected on this server yet, so those messages are recorded in the admin's delivery log instead of being sent.</p>` : ""}
 </form>`;
  box.dataset.vapid = s.vapid_public_key || "";
}

async function loadDeliveryLog() {
  const box = document.getElementById("delivery-log");
  if (!box) return;
  const d = await api("/api/admin/outbox");
  const c = d.channels;
  const card = (title, ch, extra) => `<div class="dl-ch"><div><b>${title}</b>${liveTag(ch)}</div><small>${e(ch.detail)}${extra ? " · " + extra : ""}</small></div>`;
  const ST = { sent: "tag-green", simulated: "tag-gray", failed: "tag-red", skipped: "tag-amber" };
  box.innerHTML = `<div class="panel-title"><h3>${icon("send", "icon-sm")} Message delivery</h3><div class="filters"><button class="btn btn-light btn-sm" data-action="run-jobs">${icon("clock", "icon-sm")} Run reminders now</button><button class="btn btn-light btn-sm" data-action="notify-test">Send me a test</button></div></div>
 <div class="dl-channels">${card("Email", c.email)}${card("SMS", c.sms)}${card("Push", c.push, `${d.push_devices} device(s)`)}<div class="dl-ch"><div><b>Last 7 days</b></div><small>${Object.entries(d.counts_7d).map(([k, v]) => `${v} ${k}`).join(" · ") || "nothing yet"}</small></div></div>
 ${d.items.length ? `<div class="table-wrap"><table class="data-table"><thead><tr><th>When</th><th>To</th><th>Event</th><th>Channel</th><th>Status</th></tr></thead><tbody>${d.items
   .map((i) => `<tr><td class="small">${e(whenLocal(i.created_at))}</td><td><b>${e(i.user_name || "–")}</b><div class="muted tiny">${e(i.to_addr || "")}</div></td><td class="small">${e(i.subject)}<div class="muted tiny">${e(i.event)}</div></td><td class="small">${e(i.channel)}</td><td><span class="tag ${ST[i.status] || "tag-gray"}">${e(i.status)}</span>${i.error ? `<div class="muted tiny">${e(i.error)}</div>` : ""}</td></tr>`)
   .join("")}</tbody></table></div>` : `<p class="muted small">No outside messages yet. They appear here when donors are alerted, book, or get reminders.</p>`}
 <p class="muted tiny" style="margin-top:10px">Recipients are masked. "Demo mode" channels are recorded here instead of being sent — add SMTP / Twilio settings to the .env file to send for real. Reminders run every 15 minutes while the app is running${d.scheduler ? "" : " (scheduler is switched off)"}.</p>`;
}

document.addEventListener("click", async (ev) => {
  const b = ev.target.closest("[data-action]");
  if (!b) return;
  const act = b.dataset.action;
  if (!["push-on", "push-off", "notify-test", "run-jobs"].includes(act)) return;
  ev.preventDefault();
  b.disabled = true;
  try {
    if (act === "push-on") {
      await pushEnable(document.getElementById("alerts-card")?.dataset.vapid);
      toast("Push notifications are on for this device");
      await loadAlertSettings();
    }
    if (act === "push-off") {
      await pushDisable();
      toast("Push notifications turned off for this device");
      await loadAlertSettings();
    }
    if (act === "notify-test") {
      await send("/api/notify/test", {});
      toast("Test alert sent — check your email, phone and notifications");
      if (state.view === "notifications") setTimeout(() => loadDeliveryLog().catch(() => {}), 1500);
    }
    if (act === "run-jobs") {
      const r = await send("/api/admin/jobs/run", {});
      toast(`${r.reminders} reminder(s) and ${r.eligible_again} "donate again" alert(s) sent`);
      await loadDeliveryLog();
    }
  } catch (err) {
    toast(err.message, true);
  } finally {
    if (b.isConnected) b.disabled = false;
  }
});

document.addEventListener("submit", async (ev) => {
  const form = ev.target;
  if (!form.matches("[data-alerts-form]")) return;
  ev.preventDefault();
  const f = new FormData(form);
  const body = {
    lang: f.get("lang") || "en",
    phone: (f.get("phone") || "").trim(),
    notify_email: f.has("notify_email"),
    notify_sms: f.has("notify_sms"),
    notify_push: f.has("notify_push"),
    notify_nearby: f.has("notify_nearby"),
  };
  try {
    await send("/api/notify/settings", body, "PUT");
    const langChanged = (state.lang || "en") !== body.lang;
    if (typeof setLang === "function") setLang(body.lang);
    toast(body.lang === "ms" ? "Tetapan makluman disimpan" : "Alert settings saved");
    if (langChanged) await render();
    else await loadAlertSettings();
  } catch (err) {
    toast(err.message, true);
  }
});

registerSW(); // lets the app show push alerts and be installed on phones
