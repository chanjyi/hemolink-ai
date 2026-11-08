/* HemoLink AI v2: dependency-free interactive frontend backed by FastAPI (v1 app + AI features). */
const el = document.getElementById("app");
const modalRoot = document.getElementById("modal-root");
const state = {
  user: null,
  view: "dashboard",
  authMode: "login",
  overview: null,
  campaigns: [],
  inventory: [],
  bookings: [],
  notifications: [],
  forecast: null,
  region: "Selangor",
  blood: "all",
  chat: [],
  search: "",
  outlook: null,
  outlookType: null,
  requestId: null,
  prefillType: null,
  eligResult: null,
};
const iconPaths = {
  heart:
    '<path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>',
  pulse: '<path d="M3 12h4l3-7 4 14 3-7h4"/>',
  download: '<path d="M12 3v12"/><path d="m7 10 5 5 5-5"/><path d="M5 21h14"/>',
  trash: '<path d="M3 6h18"/><path d="M8 6V4h8v2"/><path d="M6 6l1 14h10l1-14"/>',
  dashboard:
    '<rect x="3" y="3" width="7" height="9" rx="1"/><rect x="14" y="3" width="7" height="5" rx="1"/><rect x="14" y="12" width="7" height="9" rx="1"/><rect x="3" y="16" width="7" height="5" rx="1"/>',
  calendar:
    '<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M16 3v4M8 3v4M3 10h18"/><path d="m9 16 2 2 4-4"/>',
  chart: '<path d="M3 3v18h18"/><path d="m7 16 4-5 3 2 5-8"/>',
  droplet: '<path d="M12 22a8 8 0 0 0 8-8c0-5-8-12-8-12S4 9 4 14a8 8 0 0 0 8 8z"/>',
  users:
    '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"/>',
  bell: '<path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9M10 21h4"/>',
  bot: '<rect x="3" y="7" width="18" height="14" rx="3"/><path d="M12 3v4m-7 6h.01M19 13h.01"/><circle cx="9" cy="14" r="1"/><circle cx="15" cy="14" r="1"/><path d="M9 18h6"/>',
  user: '<circle cx="12" cy="8" r="4"/><path d="M4 21v-2a8 8 0 0 1 16 0v2"/>',
  logout: '<path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><path d="m16 17 5-5-5-5M21 12H9"/>',
  chevron: '<path d="m9 18 6-6-6-6"/>',
  arrow: '<path d="M5 12h14m-7-7 7 7-7 7"/>',
  plus: '<path d="M12 5v14M5 12h14"/>',
  pin: '<path d="M20 10c0 5-8 12-8 12S4 15 4 10a8 8 0 1 1 16 0z"/><circle cx="12" cy="10" r="3"/>',
  clock: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
  check: '<path d="m5 12 4 4L19 6"/>',
  close: '<path d="M18 6 6 18M6 6l12 12"/>',
  search: '<circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>',
  shield: '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><path d="m9 12 2 2 4-4"/>',
  info: '<circle cx="12" cy="12" r="10"/><path d="M12 11v5m0-8h.01"/>',
  alert:
    '<path d="m10.29 3.86-8.2 14.1A2 2 0 0 0 3.82 21h16.36a2 2 0 0 0 1.73-3.04l-8.2-14.1a2 2 0 0 0-3.42 0z"/><path d="M12 9v4m0 4h.01"/>',
  trend: '<path d="m3 17 6-6 4 4 8-8M15 7h6v6"/>',
  clipboard:
    '<rect x="5" y="5" width="14" height="16" rx="2"/><rect x="9" y="3" width="6" height="4" rx="1"/><path d="m9 14 2 2 4-4"/>',
  spark: '<path d="m12 3 1.7 5.3L19 10l-5.3 1.7L12 17l-1.7-5.3L5 10l5.3-1.7L12 3zM19 18v4m-2-2h4"/>',
  book: '<path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>',
  more: '<circle cx="5" cy="12" r="1"/><circle cx="12" cy="12" r="1"/><circle cx="19" cy="12" r="1"/>',
  send: '<path d="m22 2-7 20-4-9-9-4 20-7zM22 2 11 13"/>',
  mail: '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="m3 7 9 6 9-6"/>',
  lock: '<rect x="5" y="11" width="14" height="10" rx="2"/><path d="M8 11V7a4 4 0 0 1 8 0v4"/>',
  nav: '<path d="m3 11 18-8-8 18-2-8-8-2z"/>',
  locate: '<circle cx="12" cy="12" r="3"/><circle cx="12" cy="12" r="8"/><path d="M12 2v2m0 16v2M2 12h2m16 0h2"/>',
  map: '<path d="m9 4-6 2v14l6-2 6 2 6-2V4l-6 2-6-2z"/><path d="M9 4v14m6-12v14"/>',
  trophy: '<path d="M8 21h8m-4-4v4M7 4h10v5a5 5 0 0 1-10 0V4zM7 6H4a3 3 0 0 0 3 4m10-4h3a3 3 0 0 1-3 4"/>',
  pill: '<path d="M10.5 20.5a5 5 0 0 1-7.07-7.07l10-10a5 5 0 0 1 7.07 7.07z"/><path d="m8.5 8.5 7 7"/>',
  flask:
    '<path d="M9 3h6M10 3v6.5L4.6 18.4A1.8 1.8 0 0 0 6.1 21h11.8a1.8 1.8 0 0 0 1.5-2.6L14 9.5V3"/><path d="M7.4 15h9.2"/>',
  refresh: '<path d="M20 11a8 8 0 0 0-14-5L4 8m0-5v5h5M4 13a8 8 0 0 0 14 5l2-2m0 5v-5h-5"/>',
};
const icon = (name, extra = "") =>
  `<svg class="icon ${extra}" viewBox="0 0 24 24" aria-hidden="true">${iconPaths[name] || iconPaths.info}</svg>`;
const e = (x) =>
  String(x ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
const loc = () => (state.lang === "ms" ? "ms-MY" : "en-MY");
const dateLabel = (d) =>
  new Date(d + "T12:00:00").toLocaleDateString(loc(), { day: "numeric", month: "short", year: "numeric" });
const mon = (d) => new Date(d + "T12:00:00").toLocaleDateString(loc(), { month: "short" });
const day = (d) => new Date(d + "T12:00:00").getDate();
const short = (d) =>
  new Date(d + "T12:00:00").toLocaleDateString(loc(), { day: "numeric", month: "short" });
const capitalize = (s) => s.charAt(0).toUpperCase() + s.slice(1);
const number = (x) => Number(x || 0).toLocaleString("en-MY");
const roles = { donor: "Donor", organizer: "Drive Organizer", admin: "Blood Bank Admin" };
const bloodTypes = ["Unknown", "A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"];
// Roles (v3.1):
//  donor     – books slots, answers urgent alerts (in Notifications), eligibility, HemoScan AI
//  organizer – community drive organizer (university, company, NGO): runs campaigns, checks donors in, plans drives
//  admin     – blood bank staff: stock & shortage outlook, urgent requests + donor matching, trends, users, AI models
const navs = {
  donor: [
    ["dashboard", "Dashboard", "dashboard"],
    ["campaigns", "Find Campaigns", "calendar"],
    ["bookings", "My Appointments", "clipboard"],
    ["eligibility", "Eligibility Check", "shield"],
    ["hemoscan", "HemoScan AI", "flask"],
    ["hemocare", "HemoCare", "pulse"],
    ["notifications", "Notifications", "bell"],
    ["assistant", "Health Assistant", "bot"],
    ["profile", "My Profile", "user"],
  ],
  organizer: [
    ["dashboard", "Dashboard", "dashboard"],
    ["campaigns", "My Campaigns", "calendar"],
    ["bookings", "Bookings & Check-in", "clipboard"],
    ["reports", "Insights & Planner", "trend"],
    ["notifications", "Notifications", "bell"],
    ["assistant", "Help Assistant", "bot"],
    ["profile", "My Profile", "user"],
  ],
  admin: [
    ["dashboard", "Dashboard", "dashboard"],
    ["outlook", "Blood Stock", "droplet"],
    ["requests", "Urgent Requests", "alert"],
    ["forecast", "Donation Trends", "chart"],
    ["users", "Users & Organizers", "users"],
    ["models", "AI Models", "spark"],
    ["notifications", "Notifications", "bell"],
    ["assistant", "Help Assistant", "bot"],
    ["profile", "My Profile", "user"],
  ],
};
async function api(url, options = {}) {
  const res = await fetch(url, {
    credentials: "same-origin",
    ...options,
    headers: {
      "X-HemoLink-Request": "app",
      "X-HemoLink-Lang": state.lang === "ms" ? "ms" : "en",
      ...(options.body ? { "Content-Type": "application/json" } : {}),
      ...(options.headers || {}),
    },
  });
  const payload = await res.json().catch(() => ({ detail: "Unexpected server response" }));
  if (!res.ok) {
    if (res.status === 401 && !url.includes("login")) {
      state.user = null;
      renderAuth();
    }
    throw new Error(
      typeof payload.detail === "string"
        ? payload.detail
        : Array.isArray(payload.detail)
          ? "Please check: " + [...new Set(payload.detail.map((d) => (d.loc || []).filter((x) => typeof x === "string" && x !== "body").join(" ") + " " + (d.msg || "")))].slice(0, 3).join("; ")
          : "Request failed",
    );
  }
  return payload;
}
const send = (url, data, method = "POST") => api(url, { method, body: JSON.stringify(data) });
function toast(message, error = false) {
  const target = document.getElementById("toast-root");
  const item = document.createElement("div");
  item.className = "toast" + (error ? " error" : "");
  item.textContent = message;
  target.appendChild(item);
  setTimeout(() => item.remove(), 4300);
}
// Original HemoLink mascot: a friendly blood drop ("Titi"). kind: "flex" (holding a dumbbell) | "face"
let mascotN = 0;
function mascot(kind = "flex", size = 90) {
  const gid = `dropg${++mascotN}`; // unique id: a gradient inside a hidden element (phone sidebar) can't be shared
  const arms = kind === "flex"
    ? '<path d="M24 72 Q12 70 10 58" fill="none" stroke="#8e1824" stroke-width="5" stroke-linecap="round"/><path d="M78 72 Q90 66 92 54" fill="none" stroke="#8e1824" stroke-width="5" stroke-linecap="round"/><rect x="84" y="44" width="16" height="6" rx="2" fill="#3b2420"/><rect x="82" y="39" width="5" height="16" rx="2" fill="#3b2420"/><rect x="97" y="39" width="5" height="16" rx="2" fill="#3b2420"/>'
    : "";
  return `<svg class="mascot" width="${size}" height="${Math.round(size * 1.08)}" viewBox="0 0 104 112" aria-hidden="true"><defs><linearGradient id="${gid}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#e5404b"/><stop offset="1" stop-color="#a8161f"/></linearGradient></defs>
 ${arms}<path d="M52 6 C52 6 20 46 20 70 a32 32 0 0 0 64 0 C84 46 52 6 52 6 z" fill="url(#${gid})" stroke="#3b2420" stroke-width="3"/>
 <ellipse cx="38" cy="46" rx="6" ry="11" fill="#fff" opacity=".45" transform="rotate(25 38 46)"/>
 <ellipse cx="42" cy="68" rx="7" ry="8.5" fill="#fff"/><ellipse cx="62" cy="68" rx="7" ry="8.5" fill="#fff"/>
 <circle cx="43.5" cy="70" r="4" fill="#2a1a18"/><circle cx="63.5" cy="70" r="4" fill="#2a1a18"/><circle cx="45" cy="68.5" r="1.4" fill="#fff"/><circle cx="65" cy="68.5" r="1.4" fill="#fff"/>
 <ellipse cx="33" cy="80" rx="5" ry="3" fill="#ff8f9a" opacity=".7"/><ellipse cx="71" cy="80" rx="5" ry="3" fill="#ff8f9a" opacity=".7"/>
 <path d="M46 84 Q52 90 58 84" fill="none" stroke="#2a1a18" stroke-width="2.6" stroke-linecap="round"/></svg>`;
}
const heartPulse = (cls = "") =>
  `<svg class="heart-pulse ${cls}" viewBox="0 0 64 56" aria-hidden="true"><path d="M32 52S4 35 4 17A13 13 0 0 1 32 10a13 13 0 0 1 28 7c0 18-28 35-28 35z" fill="currentColor"/><path d="M8 28h12l4-8 6 16 5-12 3 4h18" fill="none" stroke="#fff" stroke-width="3.2" stroke-linecap="round" stroke-linejoin="round"/></svg>`;
const plusMark = (cls) => `<svg class="auth-cross ${cls}" viewBox="0 0 24 24" aria-hidden="true"><path d="M9 3h6v6h6v6h-6v6H9v-6H3V9h6z" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/></svg>`;
function authField(ic, label, input) {
  return `<label class="auth-field"><span class="auth-field-icon">${icon(ic)}</span><span class="auth-field-body"><small>${label}</small>${input}</span></label>`;
}
function renderAuth() {
  const signup = state.authMode === "signup";
  el.innerHTML = `<div class="auth"><section class="auth-art">
 <div class="auth-brand">${heartPulse()}<span>Hemo<b>Link</b></span></div>
 ${plusMark("c1")}${plusMark("c2")}${plusMark("c3")}
 <div class="auth-slogan"><h2>Every drop.<br>Every connection.<br>Every life.</h2><p>Book donations, answer urgent requests and understand your blood health — all in one place.</p></div>
 <svg class="auth-splash" viewBox="0 0 420 300" aria-hidden="true"><path d="M0 300V128c34-6 52 22 58 52 7 34 30 40 46 14 18-30 0-64 26-82 30-21 66 8 62 44-3 30-30 46-14 70 14 22 50 14 66-6 20-24 54-20 64 8 12 32-6 52 12 72H0z" fill="currentColor"/><circle cx="112" cy="150" r="13" fill="currentColor"/><circle cx="196" cy="120" r="8" fill="currentColor"/><circle cx="26" cy="110" r="8" fill="currentColor"/></svg>
 ${heartPulse("auth-heart-deco")}
 </section>
 <main class="auth-content"><div class="auth-panel">
 ${typeof langToggle === "function" ? `<div class="auth-lang">${langToggle()}</div>` : ""}
 <h1>HemoLink <span class="auth-bar">|</span> ${signup ? "Join as a donor" : "Sign in"}</h1>
 <p class="intro">${signup ? "Create your donor account to book slots, get matched to urgent requests and keep your blood health in one place." : "Donor · Drive organizer · Blood bank portal"}</p>
 <form class="auth-form" id="${signup ? "signup-form" : "login-form"}">
 ${signup ? authField("user", "Full name", '<input name="name" required minlength="2" placeholder="Your name" autocomplete="name"/>') : ""}
 ${authField(signup ? "mail" : "user", "Email address", '<input type="email" name="email" required placeholder="you@example.com" autocomplete="email"/>')}
 ${authField("lock", "Password", `<input type="password" name="password" required minlength="${signup ? 8 : 1}" placeholder="${signup ? "At least 8 characters" : "Enter your password"}" autocomplete="${signup ? "new-password" : "current-password"}"/>`)}
 ${signup ? `<div class="auth-two">${authField("droplet", "Blood type (optional)", `<select name="blood_type">${bloodTypes.map((x) => `<option>${x}</option>`).join("")}</select>`)}${authField("pin", "City (optional)", '<input name="city" placeholder="Cyberjaya"/>')}</div>
 <label class="auth-consent"><input type="checkbox" name="agree_privacy" required/><span>I have read the <a href="/static/privacy.html" target="_blank" rel="noopener">privacy notice</a> and agree to HemoLink storing my details to arrange donations.</span></label>` : ""}
 <button class="btn btn-primary auth-submit" type="submit">${signup ? "Create donor account" : "Sign in"} ${icon("arrow", "icon-sm")}</button></form>
 ${
   signup
     ? ""
     : `<div class="role-select"><div class="role-title">Role selection <span>· try a demo account</span></div><div class="role-tiles">${[
         ["donor", "Donor", "heart"],
         ["organizer", "Organizer", "users"],
         ["admin", "Admin", "shield"],
       ]
         .map((x) => `<button type="button" class="role-tile" data-action="demo-login" data-role="${x[0]}">${icon(x[2])}<span>${x[1]}</span></button>`)
         .join("")}</div></div>`
 }
 <p class="switch-link">${signup ? "Already have an account?" : "New to HemoLink?"} <button data-action="switch-auth" type="button">${signup ? "Sign in" : "Create a donor account"}</button></p>
 <div class="auth-foot">${icon("info", "icon-sm")} Hackathon prototype. Demo data only — no real clinical eligibility, live blood stock or emergency services.<br/><a href="/source" target="_blank" rel="noopener">Source code</a> · AGPL-3.0 · <a href="/static/privacy.html" target="_blank" rel="noopener">Privacy</a></div>
 </div></main></div>`;
}
function shell() {
  const items = navs[state.user.role];
  const unread = state.notifications.filter((n) => !n.is_read).length;
  const first = state.user.name
    .split(" ")
    .map((a) => a[0])
    .slice(0, 2)
    .join("")
    .toUpperCase();
  el.innerHTML = `<div class="layout"><aside class="sidebar"><div class="sidebar-top"><div class="logo"><div class="logo-mark">${icon("heart", "icon-xl")}</div><span>Hemo<b>Link</b></span></div><div class="logo-caption">HEALTH INTELLIGENCE</div></div>
 <div class="sidebar-scroll"><div class="sidebar-label">MAIN MENU</div><nav class="nav-links">${items
   .slice(0, -1)
   .map(
     ([v, label, ic]) =>
       `<button class="nav ${state.view === v ? "active" : ""}" data-view="${v}" title="${label}">${icon(ic)}<span>${label}</span>${v === "notifications" && unread ? `<b class="nav-count">${unread}</b>` : ""}</button>`,
   )
   .join("")}</nav>
 <div class="help-card"><div class="mini-icon">${icon("bot")}</div><strong>Need a little help?</strong><p>Ask about appointments or donation preparation.</p><button class="btn btn-primary" data-view="assistant">Ask the assistant ${icon("arrow", "icon-sm")}</button></div></div>
 <div class="sidebar-bottom"><div class="sidebar-label">ACCOUNT</div><nav class="nav-links"><button class="nav ${state.view === "profile" ? "active" : ""}" data-view="profile" title="My Profile">${icon("user")}<span>My Profile</span></button><button class="nav nav-logout" data-action="logout" title="Log out">${icon("logout")}<span>Log out</span></button></nav>
 <div class="side-profile" data-view="profile" title="Open my profile"><span class="avatar ${state.user.role === "donor" ? "avatar-mascot" : ""}">${state.user.role === "donor" ? mascot("face", 30) : first}</span><div><div class="name">${e(state.user.name)}</div><div class="role">${roles[state.user.role]}</div></div><span class="profile-chevron">${icon("chevron", "icon-sm")}</span></div></div>
 </aside><div class="main"><header class="topbar"><div class="breadcrumb">HemoLink AI ${icon("chevron", "icon-sm")} <strong id="crumb">${items.find((x) => x[0] === state.view)?.[1] || "Dashboard"}</strong></div><div class="top-actions">${typeof langToggle === "function" ? langToggle() : ""}<span class="date">${new Date().toLocaleDateString(loc(), { weekday: "short", month: "long", day: "numeric", year: "numeric" })}</span><button class="circle-button" data-view="notifications" aria-label="Notifications">${icon("bell")}${unread ? '<i class="bubble"></i>' : ""}</button><button class="avatar" style="border:0" data-view="profile" aria-label="My profile">${first}</button></div></header><main id="content" class="content"></main></div>${bottomNav(items, unread)}</div>`;
}
// Phone layout: app-style bottom tab bar (4 main pages + "More")
const BOTTOM = {
  donor: [["dashboard", "Home"], ["campaigns", "Campaigns"], ["hemoscan", "HemoScan"], ["notifications", "Alerts"]],
  organizer: [["dashboard", "Home"], ["campaigns", "Campaigns"], ["bookings", "Check-in"], ["notifications", "Alerts"]],
  admin: [["dashboard", "Home"], ["outlook", "Stock"], ["requests", "Urgent"], ["notifications", "Alerts"]],
};
function bottomNav(items, unread) {
  const tabs = BOTTOM[state.user.role].map(([v, label]) => {
    const ic = items.find((x) => x[0] === v)?.[2] || "dashboard";
    return `<button class="bnav ${state.view === v ? "active" : ""}" data-view="${v}">${icon(ic)}<span>${label}</span>${v === "notifications" && unread ? `<b class="bnav-dot">${unread}</b>` : ""}</button>`;
  });
  const inMore = !BOTTOM[state.user.role].some(([v]) => v === state.view);
  return `<nav class="bottom-nav" aria-label="Main">${tabs.join("")}<button class="bnav ${inMore ? "active" : ""}" data-action="more-menu">${icon("more")}<span>More</span></button></nav>`;
}
function moreMenu() {
  const items = navs[state.user.role];
  modal("Menu", `${e(state.user.name)} · ${e(roles[state.user.role])}`,
    `<div class="more-grid">${items.map(([v, label, ic]) => `<button class="more-item ${state.view === v ? "active" : ""}" data-view="${v}">${icon(ic)}<span>${label}</span></button>`).join("")}
 <button class="more-item" data-action="logout">${icon("logout")}<span>Log out</span></button></div>`);
}
function heading(title, description = "", actions = "") {
  return `<div class="page-heading"><div><div class="welcome-sub">HEMOLINK / ${e(roles[state.user.role].toUpperCase())} PORTAL</div><h1>${title}</h1><p>${description}</p></div>${actions}</div>`;
}
function stat(label, value, ic, note) {
  return `<div class="stat-card surface"><div class="stat-card-top"><span>${label}</span><span class="stat-icon">${icon(ic)}</span></div><div><div class="stat-number">${number(value)}</div><div class="stat-note">${note}</div></div></div>`;
}
function campaignMini(c) {
  return `<div class="campaign-mini"><div class="date-box"><strong>${day(c.event_date)}</strong><small>${mon(c.event_date)}</small></div><div class="info"><b>${e(c.title)}</b><span>${icon("pin", "icon-sm")} ${e(c.city)} · ${number(c.total_booked)}/${number(c.total_capacity)} booked</span></div><button class="link-btn" data-view="campaigns">View ${icon("chevron", "icon-sm")}</button></div>`;
}
function empty(ic, title, text, button = "") {
  return `<div class="empty"><div class="empty-icon">${icon(ic, "icon-xl")}</div><h3>${title}</h3><p>${text}</p>${button}</div>`;
}
async function render() {
  if (!state.user) {
    renderAuth();
    return;
  }
  try {
    state.notifications = await api("/api/notifications");
  } catch (err) {
    /* badge only */
  }
  if (typeof syncLangWithUser === "function") await syncLangWithUser();
  shell();
  await page();
}
const after = (fn) => (state.after = [...(state.after || []), fn]); // run once the page HTML is in the DOM
async function page() {
  const root = document.getElementById("content");
  if (!root) return;
  if (state.map) {
    state.map.remove();
    state.map = null;
  }
  state.after = [];
  root.innerHTML = '<div class="muted small" style="padding:35px">Loading your data...</div>';
  const bread = document.getElementById("crumb");
  if (bread) bread.textContent = navs[state.user.role].find((x) => x[0] === state.view)?.[1] || "Dashboard";
  try {
    let html = "";
    if (state.view === "dashboard") html = await dashboard();
    else if (state.view === "campaigns") html = await campaignsPage();
    else if (state.view === "bookings") html = await bookingsPage();
    else if (state.view === "inventory") html = await inventoryPage();
    else if (state.view === "outlook") html = await outlookPage();
    else if (state.view === "requests") html = await requestsPage();
    else if (state.view === "reports") html = await reportsPage();
    else if (state.view === "eligibility") html = await eligibilityPage();
    else if (state.view === "hemoscan") html = await hemoscanPage();
    else if (state.view === "hemocare") html = await hemocarePage();
    else if (state.view === "models") html = await modelsPage();
    else if (state.view === "users") html = await usersPage();
    else if (state.view === "forecast") html = await forecastPage();
    else if (state.view === "notifications") html = await notificationsPage();
    else if (state.view === "assistant") html = assistantPage();
    else if (state.view === "profile") html = profilePage();
    else {
      state.view = "dashboard";
      html = await dashboard();
    }
    if (document.getElementById("content") === root) {
      root.innerHTML = html;
      const fns = state.after || [];
      state.after = [];
      fns.forEach((f) => {
        try {
          Promise.resolve(f()).catch((err) => state.user && console.error(err));
        } catch (err) {
          console.error(err);
        }
      });
    }
  } catch (err) {
    if (!state.user) return; // logged out while this page was loading
    root.innerHTML = empty(
        "alert",
        "Something went wrong",
        e(err.message),
        '<button class="btn btn-light" data-action="retry">Try again</button>',
    );
    toast(err.message, true);
  }
}
async function goto(v) {
  if (!navs[state.user.role].some((x) => x[0] === v)) return;
  state.view = v;
  state.search = "";
  if (v === "requests") state.requestId = null;
  if (v === "eligibility") state.eligResult = null;
  if (v === "hemoscan" && typeof hs !== "undefined") {
    if (!hs.keep) hs.id = null;
    hs.keep = false;
  }
  if (v === "hemocare" && typeof hc !== "undefined") {
    if (!hc.jump) hc.view = "home";
    hc.jump = false;
  }
  shell();
  await page();
  window.scrollTo({ top: 0, behavior: "smooth" });
}
// ---------------------------------------------------------------- location helpers (dashboard + campaign map)
function haversineKm(a, b) {
  const r = (x) => (x * Math.PI) / 180;
  const dLat = r(b.lat - a.lat), dLng = r(b.lng - a.lng);
  const h = Math.sin(dLat / 2) ** 2 + Math.cos(r(a.lat)) * Math.cos(r(b.lat)) * Math.sin(dLng / 2) ** 2;
  return 6371 * 2 * Math.asin(Math.sqrt(h));
}
function myPlace() {
  // GPS position if the user shared it this session, otherwise their profile city
  if (state.loc) return state.loc;
  try {
    const saved = JSON.parse(sessionStorage.getItem("hl-loc") || "null");
    if (saved && Date.now() - saved.at < 30 * 60 * 1000) return (state.loc = saved);
  } catch (err) {
    /* storage unavailable */
  }
  return state.user.lat != null ? { lat: state.user.lat, lng: state.user.lng, source: "profile", label: state.user.city || "your profile city" } : null;
}
function withDistance(list) {
  const here = myPlace();
  return list.map((c) => {
    const km = here && c.lat != null ? haversineKm(here, c) : null;
    return { ...c, km, mins: km == null ? null : Math.max(5, Math.round((km * 1.3 / 35) * 60)) };
  });
}
const kmLabel = (km) => (km == null ? "" : km < 1 ? `${Math.round(km * 1000)} m` : `${km < 10 ? km.toFixed(1) : Math.round(km)} km`);
function directionsUrl(c) {
  const here = myPlace();
  return `https://www.google.com/maps/dir/?api=1${here ? `&origin=${here.lat},${here.lng}` : ""}&destination=${c.lat},${c.lng}`;
}
function locateMe() {
  return new Promise((ok, bad) => {
    if (!navigator.geolocation) return bad(new Error("GPS isn't available in this browser."));
    navigator.geolocation.getCurrentPosition(
      (p) => {
        state.loc = { lat: p.coords.latitude, lng: p.coords.longitude, accuracy: Math.round(p.coords.accuracy), source: "gps", at: Date.now() };
        try {
          sessionStorage.setItem("hl-loc", JSON.stringify(state.loc));
        } catch (err) {
          /* storage unavailable */
        }
        ok(state.loc);
      },
      (err) => bad(new Error(err.code === 1 ? "Location permission was denied — distances use your profile city instead." : "Couldn't get your location — distances use your profile city instead.")),
      { enableHighAccuracy: true, timeout: 12000, maximumAge: 60000 },
    );
  });
}

// ---------------------------------------------------------------- donor dashboard (v5 design)
const MILESTONES = [1, 3, 5, 10, 15, 20, 25, 30, 40, 50, 75, 100];
async function donorDashboard() {
  const [o, c, inv, notes, elig, care] = await Promise.all([
    api("/api/overview"),
    api("/api/campaigns"),
    api("/api/inventory"),
    api("/api/notifications"),
    api("/api/eligibility").catch(() => null),
    api("/api/hemocare/overview").catch(() => null),
  ]);
  state.overview = o;
  state.campaigns = c;
  state.notifications = notes;
  const first = e(state.user.name.split(" ")[0]);
  const total = o.my_donations;
  const next = MILESTONES.find((m) => m > total) || total + 25;
  const prev = [...MILESTONES].reverse().find((m) => m <= total) || 0;
  const pct = Math.round(((total - prev) / Math.max(1, next - prev)) * 100);
  const st = elig && elig.status;
  const okNow = st && (st.verdict === "eligible" || st.verdict === "eligible_after_meal");
  const daysTo = (d) => Math.max(0, Math.round((new Date(d + "T12:00:00") - new Date(todayISO() + "T12:00:00")) / 864e5));
  const eligBody = !st
    ? `<p class="dash-big">Complete your profile</p><p class="muted small">Add blood type, birth year and weight to see when you can donate.</p><button class="btn btn-primary btn-sm" data-view="profile">Open my profile</button>`
    : okNow
      ? `<p class="dash-label">You can donate</p><p class="dash-big ok">Today</p><p class="muted small">${st.days_since_last != null ? `Last donation ${st.days_since_last} days ago.` : "First-time donor — welcome!"}</p><button class="btn btn-primary btn-sm" data-view="eligibility">Check today's questions</button>`
      : st.verdict === "deferred" && st.eligible_from
        ? `<p class="dash-label">You can donate again on</p><p class="dash-big">${dateLabel(st.eligible_from)}</p><p class="muted small">In ${daysTo(st.eligible_from)} days · ${e(st.reasons[0] || "")}</p><button class="btn btn-light btn-sm" data-view="eligibility">Why?</button>`
        : `<p class="dash-label">${e(elig.labels[st.verdict])}</p><p class="muted small">${e(st.reasons.join(" "))}</p><button class="btn btn-light btn-sm" data-view="eligibility">Open eligibility check</button>`;
  const soon = withDistance(c).slice(0, 3);
  const low = inv.filter((x) => x.stock_status === "low").map((x) => x.blood_type);
  const mine = state.user.blood_type;
  const hb = elig && elig.hemoscan;
  const hold = care && care.meds.hold;
  const urgent = o.my_open_alerts
    ? `<section class="shortage-banner red slim"><div><div class="banner-tags"><span class="tag tag-red">${icon("alert", "icon-sm")} Urgent request</span></div><h2>A blood bank needs your help</h2><p>${o.my_open_alerts} urgent request${o.my_open_alerts > 1 ? "s are" : " is"} waiting for your reply.</p></div><button class="btn btn-primary" data-view="notifications">Reply in Notifications ${icon("arrow", "icon-sm")}</button></section>`
    : "";
  return heading(`Good ${hourGreeting()}, ${first} 👋`, "Find meaningful donation opportunities near you, all in one place.") +
    `<div class="stack">${urgent}
 <section class="gradient-hero"><div class="hero-body"><div class="mini">✦ CONNECTING PEOPLE THROUGH DATA</div><h2>Together, we can make a difference.</h2><p>HemoLink AI connects community donation events with thoughtful, data-informed decision support.</p><button class="btn btn-white" data-view="campaigns">Explore campaigns ${icon("arrow", "icon-sm")}</button></div><div class="hero-heart">${icon("heart")}</div></section>
 <section class="dash-grid">
 <article class="dash-card milestone"><div class="dash-card-head"><h3>Donor Milestones</h3>${mascot("flex", 86)}</div>
 <p class="dash-line">Total donations: <b>${total}</b></p><p class="dash-line">Next milestone: <b>${next} donations</b></p>
 <div class="dash-progress"><span style="width:${pct}%"></span></div><p class="muted tiny">${next - total} more to go · each donation can help up to 3 patients — up to <b>${total * 3}</b> so far</p></article>
 <article class="dash-card"><div class="dash-card-head"><h3>Next Eligibility Date</h3><span class="dash-icon">${icon("calendar")}</span></div>${eligBody}</article>
 <article class="dash-card"><div class="dash-card-head"><h3>Upcoming Campaigns</h3><span class="dash-icon">${icon("droplet")}</span></div>
 ${soon.length ? `<ul class="dash-camps">${soon.map((x) => `<li><span>${e(x.title)}<small>${e(x.city)}${x.km != null ? ` · ${kmLabel(x.km)}` : ""}</small></span><b>${short(x.event_date)}</b></li>`).join("")}</ul>` : '<p class="muted small">No upcoming campaigns yet.</p>'}
 <button class="btn btn-primary btn-sm" data-view="campaigns">${icon("map", "icon-sm")} Find a campaign</button></article>
 </section>
 <section class="dash-grid">
 <article class="dash-card"><div class="dash-card-head"><h3>My Blood Health</h3><span class="dash-icon">${icon("flask")}</span></div>
 ${hb ? `<p class="dash-line">Latest Hb: <b>${hb.hb} g/dL</b> <span class="tag ${hb.ok ? "tag-green" : "tag-amber"}">${hb.ok ? "OK to donate" : "Below minimum"}</span></p><p class="muted tiny">From your HemoScan report of ${dateLabel(hb.report_date)}</p>` : '<p class="muted small">Upload a blood test to track your haemoglobin.</p>'}
 ${hold ? `<p class="dash-line warn">${icon("pill", "icon-sm")} Medicine waiting period ${hold.until ? "until " + dateLabel(hold.until) : "while taking it"}</p>` : ""}
 <div class="filters"><button class="btn btn-light btn-sm" data-view="hemoscan">HemoScan AI</button><button class="btn btn-light btn-sm" data-view="hemocare">HemoCare</button></div></article>
 <article class="dash-card"><div class="dash-card-head"><h3>Blood Needed Now</h3><span class="dash-icon">${icon("heart")}</span></div>
 ${low.length ? `<div class="dash-types">${low.map((t) => `<span class="type-chip ${t === mine ? "mine" : ""}">${e(t)}</span>`).join("")}</div><p class="muted small">${low.includes(mine) ? `Your type <b>${e(mine)}</b> is running low — your donation really matters.` : "These blood types are below their safe level (demo stock)."}</p>` : '<p class="muted small">All blood types are above their safe level today.</p>'}</article>
 <article class="dash-card"><div class="dash-card-head"><h3>Latest Updates</h3><span class="dash-icon">${icon("bell")}</span></div>
 ${notes.length ? notes.slice(0, 3).map((n) => `<div class="dash-note"><b>${e(n.title)}</b><span>${e(n.body)}</span></div>`).join("") : '<p class="muted small">No notifications at the moment.</p>'}
 <button class="link-btn" data-view="notifications">All notifications ${icon("arrow", "icon-sm")}</button></article>
 </section>
 <div class="disclaimer">${icon("shield", "icon-sm")} Educational hackathon prototype. Stock levels, campaigns and other donors are fictional.</div></div>`;
}

async function dashboard() {
  if (state.user.role === "donor") return donorDashboard();
  const [o, c, i, notes] = await Promise.all([
    api("/api/overview"),
    api("/api/campaigns"),
    api("/api/inventory"),
    api("/api/notifications"),
  ]);
  state.overview = o;
  state.campaigns = c;
  state.inventory = i;
  state.notifications = notes;
  const role = state.user.role;
  const extra =
    role === "donor"
      ? o.my_open_alerts
        ? `<section class="shortage-banner red slim"><div><div class="banner-tags"><span class="tag tag-red">${icon("alert", "icon-sm")} Urgent request</span></div><h2>A blood bank needs your help</h2><p>${o.my_open_alerts} urgent request${o.my_open_alerts > 1 ? "s are" : " is"} waiting for your reply.</p></div><button class="btn btn-primary" data-view="notifications">Reply in Notifications ${icon("arrow", "icon-sm")}</button></section>`
        : ""
      : shortageBanner((await api("/api/outlook")).most_urgent);
  const first = e(state.user.name.split(" ")[0]);
  const intro =
    role === "donor"
      ? "Find meaningful donation opportunities near you, all in one place."
      : role === "organizer"
        ? "Run your blood drives, check donors in, and plan the next drive where blood is needed."
        : "Watch blood stock, act on shortages and oversee donors and organizers.";
  const heroTitle =
    role === "donor"
      ? "Together, we can make a difference."
      : role === "organizer"
        ? "Bring people together to give hope."
        : "Smarter planning, stronger communities.";
  const action = role === "donor" ? "campaigns" : role === "organizer" ? "campaigns" : "outlook";
  const actionName =
    role === "donor"
      ? "Explore campaigns"
      : role === "organizer"
        ? "Manage campaigns"
        : "Open blood stock";
  const low = i.filter((x) => x.stock_status === "low");
  const kpis =
    role === "donor"
      ? [
          stat("My appointments", o.my_bookings, "calendar", "Confirmed bookings"),
          stat("Upcoming events", o.active_campaigns, "heart", "Open donation campaigns"),
          stat("Community donors", o.total_donors, "users", "Demo platform accounts"),
          stat("My donations", o.my_donations, "droplet", "Recorded donations"),
        ]
      : role === "organizer"
        ? [
            stat("My campaigns", o.my_campaigns, "calendar", "Events created"),
            stat("Upcoming drives", o.my_upcoming_campaigns, "heart", "Still to run"),
            stat("Donors booked", o.my_campaign_bookings, "clipboard", "Across my campaigns"),
            stat("Average rating", o.my_rating ?? 0, "check", o.my_rating ? "From donor feedback (out of 5)" : "No ratings yet"),
          ]
        : [
            stat("Registered donors", o.total_donors, "users", "Demo accounts"),
            stat("Drive organizers", o.organizers, "calendar", "Approved organizers"),
            stat("Open urgent requests", o.open_requests, "alert", "Waiting for donors"),
            stat("Blood types below safe level", o.low_stock_groups, "droplet", "Simulated stock"),
          ];
  return (
    heading(`Good ${hourGreeting()}, ${first} 👋`, intro) +
    `<div class="stack">${extra}
 <section class="gradient-hero"><div class="hero-body"><div class="mini">✦ CONNECTING PEOPLE THROUGH DATA</div><h2>${heroTitle}</h2><p>HemoLink AI connects community donation events with thoughtful, data-informed decision support.</p><button class="btn btn-white" data-view="${action}">${actionName} ${icon("arrow", "icon-sm")}</button></div><div class="hero-heart">${icon("heart")}</div></section>
 <section class="kpi-grid">${kpis.join("")}</section>
 <section class="section-grid"><div class="surface panel"><div class="panel-title"><h3>Upcoming donation campaigns</h3><button class="link-btn" data-view="campaigns">View all ${icon("arrow", "icon-sm")}</button></div>
 ${c.length ? `<div class="campaign-list">${c.slice(0, 4).map(campaignMini).join("")}</div>` : empty("calendar", "No upcoming campaigns", "Organizers can create the first campaign.")}</div>
 <div class="surface panel"><div class="panel-title"><h3>${role === "donor" ? "Blood stock today" : "Inventory snapshot"}</h3><span class="tag tag-amber">Simulation</span></div><p class="muted small">${role === "donor" ? "Types running low need donors most — example levels, not a real hospital." : "Example stock levels, not connected to a hospital."}</p>
 ${i
   .slice(0, 5)
   .map(
     (x) =>
       `<div class="progress-row"><div class="progress-info"><b>${e(x.blood_type)} · red cells</b><span>${x.units} units ${x.stock_status === "low" ? "· low" : ""}</span></div><div class="track"><span class="${x.stock_status === "low" ? "low" : ""}" style="width:${Math.min(100, Math.round((x.units / Math.max(1, x.threshold * 2)) * 100))}%"></span></div></div>`,
   )
   .join("")}
 <button class="link-btn" data-view="${role === "admin" ? "outlook" : role === "organizer" ? "reports" : "campaigns"}">${role === "admin" ? "Manage blood stock" : role === "organizer" ? "Plan a drive for low types" : "Find a campaign near you"} ${icon("arrow", "icon-sm")}</button></div></section>
 <section class="section-grid"><div class="surface panel"><div class="panel-title"><h3>Latest updates</h3><button class="link-btn" data-view="notifications">All notifications ${icon("arrow", "icon-sm")}</button></div>
 ${
   notes.length
     ? notes
         .slice(0, 3)
         .map(
           (n) =>
             `<div class="activity"><div class="activity-icon">${icon("bell", "icon-sm")}</div><div><h4>${e(n.title)}</h4><p>${e(n.body)}</p></div></div>`,
         )
         .join("")
     : '<p class="muted small">No notifications at the moment.</p>'
 }</div>
 ${dashFeature(role)}</section>
 <div class="disclaimer">${icon("shield", "icon-sm")} Educational hackathon prototype. Inventory and demo users are fictional. Forecasts estimate collected donations, not clinical availability or patient requirements.</div>
 </div>`
  );
}
function dashFeature(role) {
  const f = {
    donor: ["HemoScan AI", "flask", "Understand your blood test", "Upload your full blood count report to see what is out of range, possible patterns and how it changes over time.", "hemoscan", "Open HemoScan"],
    organizer: ["Campaign planner", "trend", "Where and when to hold your next drive", "The planner picks the blood type that is running low, the area with the most eligible donors and the best weekday.", "reports", "Open planner"],
    admin: ["AI forecasting", "chart", "7-day donation outlook", "Explore expected donation counts, model metrics and data provenance.", "forecast", "Open forecasts"],
  }[role];
  return `<div class="surface panel"><div class="panel-title"><h3>${f[0]}</h3>${aiTag("AI")}</div><div style="padding:5px 0 20px;display:flex;gap:14px;align-items:center"><div class="stat-icon" style="width:58px;height:58px;flex:none">${icon(f[1], "icon-xl")}</div><div><h3 style="font-size:17px">${f[2]}</h3><p class="muted small" style="line-height:1.65;margin-top:5px">${f[3]}</p></div></div><button class="btn btn-outline" data-view="${f[4]}">${f[5]} ${icon("arrow", "icon-sm")}</button></div>`;
}
function hourGreeting() {
  const hour = new Date().getHours();
  return hour < 12 ? "morning" : hour < 17 ? "afternoon" : "evening";
}
async function campaignsPage() {
  const own = state.user.role === "organizer";
  const raw = await api(own ? "/api/organizer/campaigns" : "/api/campaigns");
  state.campaigns = raw;
  const here = myPlace();
  const radius = state.campRadius || 0;
  const sort = state.campSort || (here ? "near" : "soon");
  let list = withDistance(raw);
  const total = list.length;
  if (radius && here) list = list.filter((c) => c.km != null && c.km <= radius);
  list.sort((a, b) => (sort === "near" && a.km != null && b.km != null ? a.km - b.km : a.event_date.localeCompare(b.event_date)));
  const donor = state.user.role === "donor";
  const cards = list.map((c) => {
    const avail = c.slots.reduce((x, s) => x + s.remaining, 0);
    return `<article class="campaign-card surface" data-camp="${c.id}" data-filter-text="${e((c.title + " " + c.venue + " " + c.city).toLowerCase())}">
  <div class="campaign-body"><div class="camp-top"><span class="camp-date"><b>${day(c.event_date)}</b><small>${mon(c.event_date)}</small></span>
  <div class="camp-head"><h3>${e(c.title)}</h3><div class="camp-where">${icon("pin", "icon-sm")} ${e(c.venue)}, ${e(c.city)}</div></div>
  ${c.km != null ? `<span class="camp-dist" title="Straight-line distance; drive time is a rough estimate">${icon("nav", "icon-sm")} ${kmLabel(c.km)}<small>~${c.mins} min drive</small></span>` : ""}</div>
  <p class="description">${e(c.description || "Join the community and help make donation opportunities accessible.")}</p>
  <div class="campaign-meta"><div>${icon("calendar")} ${dateLabel(c.event_date)}</div><div>${icon("clock")} ${c.slots.map((s) => e(s.start_time)).join(" · ")}</div></div>
  <div class="campaign-bottom"><span class="slots"><b>${number(avail)}</b> slots left</span><div class="filters">
  ${c.lat != null ? `<button class="btn btn-light btn-sm" data-action="map-focus" data-id="${c.id}">${icon("map", "icon-sm")} Map</button><a class="btn btn-light btn-sm" href="${directionsUrl(c)}" target="_blank" rel="noopener">${icon("nav", "icon-sm")} Directions</a>` : ""}
  ${own ? `<button class="btn btn-light btn-sm" data-action="edit-location" data-id="${c.id}">${icon("pin", "icon-sm")} Edit location</button>` : ""}
  ${donor ? `<button class="btn btn-primary btn-sm" data-action="book-modal" data-id="${c.id}" ${avail === 0 ? "disabled" : ""}>Book a slot</button>` : `<span class="tag tag-gray">${number(c.total_booked)} bookings</span>`}</div></div></div></article>`;
  });
  const chip = (km, label) => `<button class="hs-chip ${radius === km ? "on" : ""}" data-action="camp-radius" data-km="${km}" ${!here && km ? "disabled" : ""}>${label}</button>`;
  const whereNote = !here
    ? "Share your location to see how far each campaign is."
    : here.source === "gps"
      ? `Distances from your current location (GPS, ±${here.accuracy || "?"} m).`
      : `Distances from ${e(here.label)} (your profile city). Use GPS for your exact location.`;
  after(() => initCampMap(list, here, radius));
  return (
    heading(
      own ? "My campaigns" : state.user.role === "admin" ? "Donation campaigns" : "Find a donation campaign",
      own ? "Manage the events you organize and coordinate available appointment slots." : "See drives near you on the map, how far they are, and book a slot.",
      own ? `<button class="btn btn-primary" data-action="new-campaign">${icon("plus")} Create campaign</button>` : "",
    ) +
    `<div class="camp-tools surface"><div class="search-field">${icon("search")}<input id="campaign-search" class="input" placeholder="Search campaigns, venues, cities..." value="${e(state.search)}" /></div>
 <button class="btn ${here && here.source === "gps" ? "btn-light" : "btn-primary"}" data-action="locate">${icon("locate", "icon-sm")} ${here && here.source === "gps" ? "Update my location" : "Use my location"}</button>
 <div class="hs-chips" style="margin:0">${chip(0, "All")}${chip(10, "≤ 10 km")}${chip(25, "≤ 25 km")}${chip(50, "≤ 50 km")}</div>
 <select class="select camp-sort" id="camp-sort" aria-label="Sort campaigns"><option value="near" ${sort === "near" ? "selected" : ""} ${here ? "" : "disabled"}>Nearest first</option><option value="soon" ${sort === "soon" ? "selected" : ""}>Soonest first</option></select></div>
 <p class="camp-note">${icon(here && here.source === "gps" ? "locate" : "info", "icon-sm")} ${whereNote} Showing ${list.length} of ${total} campaigns.</p>
 <div class="camp-layout"><div class="camp-map-wrap surface"><div id="camp-map" class="camp-map" role="region" aria-label="Map of donation campaigns"></div></div>
 <div class="campaign-grid" id="campaign-grid">${cards.join("")}</div></div>
 <div id="campaign-empty" class="hide" style="margin-top:15px">${empty("search", "No matching events", "Try another name, city or venue.")}</div>
 ${!cards.length ? empty("map", total ? "No campaigns within this distance" : "No campaigns yet", total ? "Try a larger distance." : own ? "Create a campaign to get started." : "Please check back for upcoming events.") : ""}
 <div class="disclaimer" style="margin-top:25px">Campaigns and venues are fictional demo records with approximate locations. Distances are straight-line; drive times are rough estimates. Map data © OpenStreetMap contributors.</div>`
  );
}

const DROP_PIN = `<svg viewBox="0 0 30 38" width="30" height="38"><path d="M15 2C15 2 3 16 3 24a12 12 0 0 0 24 0C27 16 15 2 15 2z" fill="#b3202e" stroke="#fff" stroke-width="2.5"/><circle cx="15" cy="24" r="4.5" fill="#fff"/></svg>`;
function initCampMap(list, here, radius) {
  const box = document.getElementById("camp-map");
  if (!box) return;
  if (typeof L === "undefined") {
    box.innerHTML = '<div class="map-off">Map unavailable</div>';
    return;
  }
  const map = L.map(box, { scrollWheelZoom: false, zoomControl: true }).setView([3.05, 101.65], 10);
  L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", { maxZoom: 18, attribution: "&copy; OpenStreetMap contributors" }).addTo(map);
  const pin = L.divIcon({ className: "camp-pin", html: DROP_PIN, iconSize: [30, 38], iconAnchor: [15, 36], popupAnchor: [0, -30] });
  const pts = [];
  state.markers = {};
  list.forEach((c) => {
    if (c.lat == null) return;
    const avail = c.slots.reduce((x, s) => x + s.remaining, 0);
    const m = L.marker([c.lat, c.lng], { icon: pin, title: c.title }).addTo(map).bindPopup(
      `<div class="map-pop"><b>${e(c.title)}</b><span>${e(c.venue)}, ${e(c.city)}</span><span>${dateLabel(c.event_date)} · ${avail} slots left</span>${c.km != null ? `<span>${kmLabel(c.km)} away · ~${c.mins} min drive</span>` : ""}
 <div class="map-pop-actions"><a href="${directionsUrl(c)}" target="_blank" rel="noopener">Directions</a>${state.user.role === "donor" && avail ? `<button data-action="book-modal" data-id="${c.id}">Book a slot</button>` : ""}</div></div>`,
    );
    m.on("click", () => document.querySelectorAll(".campaign-card.focus").forEach((x) => x.classList.remove("focus")));
    state.markers[c.id] = m;
    pts.push([c.lat, c.lng]);
  });
  if (here) {
    if (here.source === "gps" && here.accuracy && here.accuracy < 3000)
      L.circle([here.lat, here.lng], { radius: here.accuracy, color: "#2a7de1", weight: 1, fillOpacity: 0.08 }).addTo(map);
    L.circleMarker([here.lat, here.lng], { radius: 8, color: "#fff", weight: 3, fillColor: "#2a7de1", fillOpacity: 1 })
      .addTo(map)
      .bindPopup(here.source === "gps" ? "You are here" : `${e(here.label)} (profile city)`);
    if (radius) L.circle([here.lat, here.lng], { radius: radius * 1000, color: "#b3202e", weight: 1.5, dashArray: "6 6", fill: false }).addTo(map);
    pts.push([here.lat, here.lng]);
  }
  if (pts.length > 1) map.fitBounds(pts, { padding: [36, 36], maxZoom: 13 });
  else if (pts.length) map.setView(pts[0], 12);
  state.map = map;
}

async function bookingsPage() {
  const own = state.user.role === "organizer";
  const bookings = await api(own ? "/api/organizer/bookings" : "/api/bookings");
  state.bookings = bookings;
  return (
    heading(
      own ? "Campaign bookings" : "My appointments",
      own
        ? "Review donor reservations across your campaigns."
        : "Manage your confirmed donation appointments.",
      !own
        ? `<button class="btn btn-primary" data-view="campaigns">${icon("plus")} Find a campaign</button>`
        : "",
    ) +
    `<div class="surface panel"><div class="panel-title"><h3>${own ? "All reservations" : "Appointment history"}</h3><span class="tag tag-gray">${bookings.length} entries</span></div>
 ${
   bookings.length
     ? `<div class="table-wrap"><table class="data-table"><thead><tr><th>${own ? "Donor" : "Campaign"}</th><th>Event</th><th>Time</th><th>Status</th><th>Action</th></tr></thead><tbody>
 ${bookings.map((b) => `<tr><td><b>${e(own ? b.donor_name : b.title)}</b>${own ? `<div class="muted tiny" style="margin-top:5px">${e(b.blood_type)}</div>` : `<div class="muted tiny" style="margin-top:5px">${e(b.venue)}</div>`}</td><td>${dateLabel(b.event_date)}</td><td>${e(b.start_time)}</td><td>${bookingTag(b.status)}</td><td>${bookingAction(b, own)}</td></tr>`).join("")}</tbody></table></div>`
     : empty(
         "calendar",
         "No appointments yet",
         own
           ? "No one has booked your campaigns yet."
           : "Explore upcoming campaigns and reserve your first slot.",
         !own ? '<button class="btn btn-primary" data-view="campaigns">Browse campaigns</button>' : "",
       )
 }</div>`
  );
}
async function inventoryPage() {
  if (state.user.role !== "admin") return "";
  const items = await api("/api/inventory");
  state.inventory = items;
  const low = items.filter((x) => x.stock_status === "low");
  return (
    heading(
      "Blood inventory simulator",
      "Monitor and edit fictional blood-stock data for an operational planning scenario.",
      `<span class="tag tag-amber">${icon("info", "icon-sm")} Demo inventory · not live</span>`,
    ) +
    `<div class="source-strip demo" style="margin-bottom:21px">${icon("shield")} All figures on this screen are synthetic demo stock counts. They are NOT real blood bank availability and cannot be used to make clinical decisions.</div>
 <div class="kpi-grid" style="margin-bottom:22px">${[
   stat("Blood types tracked", items.length, "droplet", "Eight ABO/Rh groups"),
   stat(
     "Total demo units",
     items.reduce((s, x) => s + x.units, 0),
     "clipboard",
     "Red blood cells",
   ),
   stat("Low-stock scenarios", low.length, "alert", "Below configured thresholds"),
   stat("Above threshold", items.length - low.length, "check", "Scenario only"),
 ].join("")}</div>
 <div class="split" style="margin-bottom:14px"><h3>Stock by blood group</h3><span class="muted small">Click Edit to change the simulated values</span></div>
 <div class="inventory-grid">${items
   .map((x) => {
     const pct = Math.min(100, Math.round((x.units / Math.max(x.threshold * 2, 1)) * 100));
     return `<div class="blood-card surface"><div class="blood-heading"><span class="blood-label">${e(x.blood_type)}</span><span class="blood-badge">${icon("droplet")}</span></div><div><div class="blood-number">${number(x.units)} <small>units</small></div><div class="muted small" style="margin-top:6px">Demo stock balance</div></div><div class="track"><span class="${x.stock_status === "low" ? "low" : ""}" style="width:${pct}%"></span></div><div class="blood-footer"><span class="tag ${x.stock_status === "low" ? "tag-amber" : "tag-green"}">${x.stock_status === "low" ? "Below threshold" : "Within threshold"}</span><button class="link-btn" data-action="edit-inventory" data-id="${x.id}">Edit</button></div><div class="tiny muted">Configured threshold: ${x.threshold} units</div></div>`;
   })
   .join("")}</div>
 <div class="disclaimer" style="margin-top:24px">Inventory updates affect only the local demo SQLite database. Appointment bookings do not directly create new blood products.</div>`
  );
}
function lineChart(f) {
  const hist = f.history,
    future = f.future,
    data = [...hist, ...future];
  if (!data.length) return "";
  const W = 870,
    H = 278,
    L = 51,
    R = 15,
    T = 19,
    B = 35;
  const vals = data.map((d) => Number(d.donations));
  const max = Math.max(10, ...vals) * 1.18;
  const point = (n, index) => ({
    x: L + ((W - L - R) * index) / (data.length - 1),
    y: T + (H - T - B) * (1 - n / max),
  });
  const coord = (d, i) => {
    const a = point(d.donations, i);
    return a.x.toFixed(1) + "," + a.y.toFixed(1);
  };
  const historyPoints = hist.map(coord).join(" ");
  const futurePoints = [hist[hist.length - 1], ...future]
    .map((d, i) => coord(d, hist.length - 1 + i))
    .join(" ");
  const divX = point(0, hist.length - 1).x;
  const grid = Array.from({ length: 5 }, (_, i) => {
    const y = T + ((H - T - B) * i) / 4;
    const value = Math.round(max * (1 - i / 4));
    return `<line class="chart-grid" x1="${L}" y1="${y}" x2="${W - R}" y2="${y}"/><text class="chart-axis" x="${L - 13}" y="${y + 4}" text-anchor="end">${value}</text>`;
  }).join("");
  const labels = [0, 7, 14, hist.length - 1, hist.length + 2, data.length - 1]
    .filter((v, i, arr) => arr.indexOf(v) === i)
    .map((i) => {
      const p = point(0, i);
      return `<text class="chart-axis" text-anchor="middle" x="${p.x}" y="${H - 8}">${short(data[i].date)}</text>`;
    })
    .join("");
  return `<svg class="chart" viewBox="0 0 ${W} ${H}" role="img" aria-label="Historical donation counts and 7-day predicted donation counts">${grid}<line class="chart-divide" x1="${divX}" y1="${T}" x2="${divX}" y2="${H - B}"/><polyline class="chart-history" points="${historyPoints}"/><polyline class="chart-future" points="${futurePoints}"/>${future
    .map((d, i) => {
      const p = point(d.donations, hist.length + i);
      return `<circle cx="${p.x}" cy="${p.y}" r="4" fill="#d94c5c" stroke="white" stroke-width="2"/>`;
    })
    .join(
      "",
    )}${labels}<text class="chart-axis" x="${W - R - 6}" y="${T + 3}" text-anchor="end">Forecast</text></svg>`;
}
async function forecastPage() {
  const q = new URLSearchParams({ region: state.region, blood_type: state.blood });
  const f = await api("/api/forecast?" + q.toString());
  state.forecast = f;
  const mean = Math.round(f.future.reduce((s, x) => s + x.donations, 0) / f.future.length);
  const regionOptions = f.regions || [f.region];
  const M = f.metrics;
  const gain = M.baseline_mae ? Math.round(((M.baseline_mae - M.mae) / M.baseline_mae) * 100) : 0;
  const LBL = { seasonal_naive: "Same weekday last week", weekday_mean: "Average of last 4 same weekdays", rf: "Random Forest" };
  return (
    heading(
      "AI donation forecasting",
      "Explore 7-day predictions of collected blood donations using machine learning.",
      `<span class="tag ${f.official ? "tag-green" : "tag-amber"}">${icon("spark", "icon-sm")} ${f.official ? "Official dataset" : "Demo model"}</span>`,
    ) +
    `<div class="surface panel" style="margin-bottom:20px"><div class="split" style="align-items:flex-start;margin-bottom:20px;flex-wrap:wrap"><div><h3>Donation volume forecast</h3><p class="muted small" style="margin-top:7px">Historical counts and seven future daily predictions</p></div><div class="filters"><select class="select" id="forecast-region" aria-label="Region">${regionOptions.map((x) => `<option ${x === state.region ? "selected" : ""}>${e(x)}</option>`).join("")}</select><select class="select" id="forecast-blood" aria-label="Blood group">${["all", "A", "B", "AB", "O"].map((x) => `<option value="${x}" ${x === state.blood ? "selected" : ""}>${x === "all" ? "All blood groups" : "Group " + x}</option>`).join("")}</select></div></div>
 ${lineChart(f)}<div class="legend"><span>Observed history</span><span>Model prediction</span></div></div>
 <div class="forecast-summary" style="margin-bottom:20px"><div class="surface"><span>Average forecast / day</span><strong>${number(mean)}</strong><p class="muted tiny" style="margin-top:5px">Collected donations · next 7 days</p></div><div class="surface"><span>Error · ${e(LBL[M.selected] || M.selected)}</span><strong>±${M.mae}</strong><p class="muted tiny" style="margin-top:5px">Donations/day over 7-day forecasts</p></div><div class="surface"><span>vs. same weekday last week</span><strong class="${gain > 0 ? "success-text" : ""}">${gain > 0 ? gain + "% better" : "baseline"}</strong><p class="muted tiny" style="margin-top:5px">Baseline error ±${M.baseline_mae}</p></div></div>
 <div class="surface panel" style="margin-bottom:20px"><div class="panel-title"><h3>Which method won for this series</h3>${aiTag("Cross-validated")}</div><div class="cand-bars">${Object.entries(M.candidates || {})
   .sort((a, b) => a[1] - b[1])
   .map(([k, v]) => { const mx = Math.max(...Object.values(M.candidates)); return `<div class="cand ${k === M.selected ? "win" : ""}"><span>${e(LBL[k] || k)}${k === M.selected ? " ✓" : ""}</span><div class="cand-bar"><i style="width:${Math.max(4, (v / (mx || 1)) * 100)}%"></i></div><b>±${v}</b></div>`; })
   .join("")}</div><p class="muted tiny" style="margin-top:10px">Each method forecast 7 days blind from ${M.test_samples / 7} past cut-off dates; the lowest average error wins (simpler method if within 2%).</p></div>
 <div class="forecast-details"><div class="surface panel"><div class="panel-title"><h3>Forecast methodology</h3><span class="tag tag-gray">Transparent evaluation</span></div><div class="method-list"><div>${icon("chart", "icon-sm")} <strong>Algorithm:</strong> ${e(f.model)}</div><div>${icon("calendar", "icon-sm")} <strong>Validation:</strong> ${e(M.validation || "")}</div><div>${icon("trend", "icon-sm")} <strong>RMSE:</strong> ${M.rmse} donations · Predicts count, not demand</div><div>${icon("book", "icon-sm")} <strong>Latest source date:</strong> ${e(f.source_last_date)}</div></div></div>
 <div class="surface panel"><div class="panel-title"><h3>Data provenance</h3></div><p class="muted small" style="line-height:1.75">${e(f.source)}</p><div class="source-strip ${f.official ? "" : "demo"}" style="margin-top:15px">${icon(f.official ? "check" : "alert")} ${f.official ? "Public historical donation records. Report in CC BY 4.0 and attribute the Ministry of Health Malaysia." : "The local dataset is simulated until you run python scripts/download_data.py."}</div><a href="https://github.com/MoH-Malaysia/data-darah-public" target="_blank" rel="noopener noreferrer" class="link-btn" style="margin-top:18px;display:inline-flex">Government source ${icon("arrow", "icon-sm")}</a></div></div>
 <div class="disclaimer" style="margin-top:20px">${e(f.warning)} Official donation datasets do not show live blood-bank inventory or actual patient demand. Metrics describe retrospective count prediction only.</div>`
  );
}
async function notificationsPage() {
  const donor = state.user.role === "donor";
  const admin = state.user.role === "admin";
  if (admin) after(() => loadDeliveryLog().catch((err) => toast(err.message, true)));
  const [list, alerts] = await Promise.all([api("/api/notifications"), donor ? api("/api/my-alerts") : Promise.resolve([])]);
  state.notifications = list;
  const open = alerts.filter((a) => a.status === "open" || a.response === "yes");
  const urgent = donor
    ? `<div class="stack" style="margin-bottom:22px"><div class="split"><h3>Urgent requests for you</h3><span class="tag ${alerts.some((a) => a.response === null && a.status === "open") ? "tag-red" : "tag-gray"}">${alerts.filter((a) => a.response === null && a.status === "open").length} waiting for reply</span></div>
 ${open.length ? open.map(alertCard).join("") : `<div class="source-strip">${icon("check")} No urgent requests right now. When a blood bank needs your blood type nearby, it appears here first.</div>`}</div>`
    : "";
  return (
    heading(
      "Notifications",
      donor ? "Urgent requests from blood banks and updates about your appointments." : "Updates about your campaigns and activity.",
      list.some((x) => !x.is_read)
        ? `<button class="btn btn-light" data-action="read-notifications">${icon("check")} Mark all as read</button>`
        : "",
    ) +
    urgent + (admin ? `<div class="surface panel" id="delivery-log" style="margin-bottom:22px"><p class="muted small">Loading delivery log…</p></div><h3 style="margin-bottom:12px">My notifications</h3>` : "") + `${donor ? '<h3 style="margin-bottom:12px">Updates</h3>' : ""}<div class="surface panel">${list.length ? list.map((n) => `<div class="notice-row ${!n.is_read ? "unread" : ""}"><div class="notice-icon">${icon("bell")}</div><div><h4>${e(n.title)} ${!n.is_read ? '<span class="dot danger-text"></span>' : ""}</h4><p>${e(n.body)}</p><span class="tiny muted">${e(n.created_at)}</span></div></div>`).join("") : empty("bell", "All caught up", "You have no notifications right now.")}</div>`
  );
}
function assistantPage() {
  return (
    heading(
      "Donation help assistant",
      "Quick answers about using the platform and general donor preparation.",
    ) +
    `<div class="source-strip demo" style="margin-bottom:20px">${icon("info")} This is a curated FAQ assistant, not a generative medical chatbot or diagnostic system. Always consult clinical staff about eligibility and medical questions.</div>
 <div class="surface chat-box"><div id="chat-screen" class="chat-screen"><div class="message assistant">Hello! 👋 I can help with booking, preparing for a donation, urgent alerts, HemoScan and hosting a blood drive. What would you like to know?</div>
 ${state.chat.map((m) => `<div class="message ${m.type}">${e(m.text)}</div>`).join("")}</div><div class="panel" style="padding-bottom:0;padding-top:5px"><div class="suggested">${(state.user.role === "donor" ? ["How do I book an appointment?", "How should I prepare?", "What is HemoScan?"] : state.user.role === "organizer" ? ["How do I book an appointment?", "How should I prepare?", "How do I host a drive?"] : ["What does the forecast mean?", "How do urgent alerts work?", "How do I host a drive?"]).map((x) => `<button data-action="question" data-question="${e(x)}">${e(x)}</button>`).join("")}</div></div>
 <form id="assistant-form" class="chat-input"><input name="question" class="input" placeholder="Ask a question..." maxlength="500" required/><button class="btn btn-primary">${icon("send")} Send</button></form></div>`
  );
}
function profilePage() {
  after(() => loadAlertSettings().catch((err) => toast(err.message, true)));
  after(() => loadConsentLine().catch(() => {}));
  const u = state.user,
    initials = u.name
      .split(" ")
      .map((x) => x[0])
      .slice(0, 2)
      .join("")
      .toUpperCase();
  return (
    heading("My profile", "Manage your basic information and donation preferences.") +
    `<div class="surface profile-card"><div class="profile-top"><span class="avatar">${e(initials)}</span><div><h3>${e(u.name)}</h3><p>${e(roles[u.role])} · ${e(u.email)}</p></div></div>
 <form id="profile-form" class="form-grid"><div class="field full"><label>Full name</label><input class="input" name="name" value="${e(u.name)}" minlength="2" maxlength="90" required /></div><div class="field full"><label>Email address</label><input class="input" value="${e(u.email)}" disabled /></div>
 <div class="field"><label>Blood type ${u.role !== "donor" ? "(optional)" : ""}</label><select class="select" name="blood_type">${bloodTypes.map((x) => `<option ${x === u.blood_type ? "selected" : ""}>${x}</option>`).join("")}</select></div>
 <div class="field"><label>City</label><input class="input" name="city" value="${e(u.city)}" maxlength="80" placeholder="City or town"/></div>
 ${u.role === "donor" ? `<div class="field"><label>Birth year</label><input class="input" type="number" name="birth_year" min="1920" max="${new Date().getFullYear() - 16}" value="${e(u.birth_year ?? "")}" placeholder="e.g. 2001"/></div><div class="field"><label>Weight (kg)</label><input class="input" type="number" name="weight_kg" min="30" max="250" step="0.1" value="${e(u.weight_kg ?? "")}" placeholder="e.g. 55"/></div><div class="field"><label>Sex (optional)</label><select class="select" name="sex"><option value="" ${!u.sex ? "selected" : ""}>Prefer not to say</option><option value="female" ${u.sex === "female" ? "selected" : ""}>Female</option><option value="male" ${u.sex === "male" ? "selected" : ""}>Male</option></select><small class="muted tiny">Sets your donation gap: women every 4 months, men every 3.</small></div>` : ""}<div class="full"><div class="disclaimer">${icon("info", "icon-sm")} Blood type, birth year and weight are self-reported and used only for the eligibility check and donor matching. They are not medically verified — screening staff make the final decision.</div></div>
 <div class="profile-actions full"><button type="submit" class="btn btn-primary">${icon("check")} Save changes</button></div></form></div>
 <div class="surface panel profile-card" id="alerts-card" style="margin-top:20px"><p class="muted small">Loading alert settings…</p></div>
 <div class="surface panel profile-card" id="privacy-card" style="margin-top:20px"><div class="panel-title"><h3>${icon("shield", "icon-sm")} Your data &amp; privacy</h3></div>
 <p class="muted small">You control your personal data under Malaysia's Personal Data Protection Act 2010. Uploaded blood test files are encrypted, and only you can see your HemoScan reports and medicine list.</p>
 <div class="filters" style="margin-top:12px"><a class="btn btn-light" href="/api/me/export" download>${icon("download", "icon-sm")} Download my data</a><a class="btn btn-light" href="/static/privacy.html" target="_blank" rel="noopener">${icon("info", "icon-sm")} Privacy notice</a><a class="btn btn-light" href="/source" target="_blank" rel="noopener">${icon("book", "icon-sm")} Source code</a>${u.role === "donor" ? `<button type="button" class="btn btn-light danger-text" data-action="delete-account">${icon("trash", "icon-sm")} Delete my account</button>` : ""}</div>
 <p class="muted tiny" id="consent-line" style="margin-top:10px"></p></div>`
  );
}
async function loadConsentLine() {
  const el = document.getElementById("consent-line");
  if (!el) return;
  const c = await api("/api/me/consents");
  const p = c.items.find((x) => x.kind === "privacy_notice");
  el.textContent = p ? `You agreed to privacy notice version ${p.version} on ${dateLabel(p.created_at.slice(0, 10))}.` : `Privacy notice version ${c.current_version}.`;
}
function deleteAccountModal() {
  modal(
    "Delete my account",
    "This permanently removes your profile, bookings, donation history, HemoScan reports and medicine list. It can't be undone.",
    `<form id="delete-account-form" class="form-grid"><div class="field full"><label>Your password</label><input class="input" type="password" name="password" required autocomplete="current-password"/></div>
 <div class="field full"><label>Type DELETE to confirm</label><input class="input" name="confirm" required autocomplete="off" placeholder="DELETE"/></div>
 <div class="full source-strip demo">${icon("download", "icon-sm")} Want a copy first? <a href="/api/me/export" download>Download my data</a></div>
 <div class="full modal-footer"><button type="button" class="btn btn-light" data-action="close-modal">Cancel</button><button type="submit" class="btn btn-primary">${icon("trash", "icon-sm")} Delete permanently</button></div></form>`,
  );
}
/* ------------------------------------------------------------------ v2: AI feature screens */
const STATUS = { red: ["tag-red", "Critical"], amber: ["tag-amber", "Watch"], green: ["tag-green", "Healthy"] };
const statusTag = (s, label) => `<span class="tag ${STATUS[s][0]}">${label || STATUS[s][1]}</span>`;
const dos = (d) => (Number(d) >= 30 ? "30+" : Number(d).toFixed(1));
const aiTag = (t = "AI") => `<span class="tag tag-ai">${icon("spark", "icon-sm")} ${e(t)}</span>`;
const todayISO = () => new Date().toLocaleDateString("en-CA");
const addDay = (d, n) => {
  const x = new Date(d + "T12:00:00");
  x.setDate(x.getDate() + n);
  return x.toLocaleDateString("en-CA");
};
const miniStat = (label, value, note = "", cls = "") =>
  `<div class="stat-card surface"><div class="stat-card-top"><span>${label}</span></div><div><div class="stat-number ${cls}">${value}</div><div class="stat-note">${note}</div></div></div>`;

function shortageBanner(t) {
  if (!t || t.status === "green") return "";
  const when =
    t.days_until_unsafe === 0
      ? "is already below the safe level"
      : t.days_until_unsafe
        ? `falls below the safe level in ${t.days_until_unsafe} day${t.days_until_unsafe > 1 ? "s" : ""}`
        : "is running low";
  const action =
    state.user.role === "admin"
      ? `<button class="btn btn-primary" data-action="mobilise" data-type="${e(t.blood_type)}">Mobilise ${e(t.blood_type)} donors ${icon("arrow", "icon-sm")}</button>`
      : `<button class="btn btn-primary" data-view="reports">Plan a ${e(t.blood_type)} drive ${icon("arrow", "icon-sm")}</button>`;
  return `<section class="shortage-banner ${t.status}"><div><div class="banner-tags">${aiTag("Shortage forecast")} ${statusTag(t.status)}</div>
 <h2>${e(t.blood_type)} ${when}</h2><p>${number(t.units)} units in stock · about ${t.avg_daily_use} used per day · ${dos(t.days_of_supply)} days of supply${t.supply_trend_pct < -5 ? ` · donations down ${Math.abs(t.supply_trend_pct)}% over the last 2 weeks` : ""}.</p></div>${action}</section>`;
}

function alertCard(a) {
  let body;
  if (a.response === null)
    body = `<div class="alert-actions"><button class="btn btn-primary" data-action="respond-alert" data-id="${a.id}" data-response="yes">${icon("check", "icon-sm")} I can come</button><button class="btn btn-light" data-action="respond-alert" data-id="${a.id}" data-response="no">Can't make it this time</button></div>`;
  else if (a.response === "yes")
    body = `<div class="alert-ok"><b>Thank you!</b> Please go to ${e(a.centre_name)} (${e(a.centre_city)}) before ${dateLabel(a.needed_by)} and show code <b class="code">${e(a.code)}</b> at registration.${a.donated ? '<div class="success-text semibold" style="margin-top:8px">✓ Donation recorded — you helped close this shortage.</div>' : ""}</div>`;
  else body = `<p class="small muted" style="margin-top:12px">No problem — thanks for letting us know.</p>`;
  return `<section class="urgent-card surface"><div class="banner-tags"><span class="tag tag-red">${icon("alert", "icon-sm")} Urgent request</span>${aiTag("Matched to you")}</div>
 <h3>${e(a.centre_name)} needs ${a.units} units of ${e(a.blood_type)} by ${dateLabel(a.needed_by)}</h3>
 <p class="small muted">You were picked because: ${a.reasons.slice(0, 3).map(e).join(" · ")}.</p>${body}</section>`;
}

const BOOKING_LABEL = {
  confirmed: ["tag-green", "Confirmed"],
  cancelled: ["tag-gray", "Cancelled"],
  donated: ["tag-green", "Donated"],
  no_show: ["tag-amber", "No-show"],
};
const bookingTag = (s) => `<span class="tag ${(BOOKING_LABEL[s] || BOOKING_LABEL.cancelled)[0]}">${(BOOKING_LABEL[s] || [0, capitalize(s)])[1]}</span>`;

function bookingAction(b, own) {
  if (own)
    return b.status === "confirmed"
      ? `<button class="btn btn-outline btn-sm" data-action="booking-status" data-status="donated" data-id="${b.id}">Donated</button> <button class="btn btn-light btn-sm" data-action="booking-status" data-status="no_show" data-id="${b.id}">No-show</button>`
      : '<span class="muted small">—</span>';
  if (b.status === "confirmed" && b.event_date >= todayISO())
    return `<button class="btn btn-outline btn-sm" data-action="cancel-booking" data-id="${b.id}">Cancel</button>`;
  if (b.status === "donated")
    return b.my_rating
      ? `<span class="tag tag-green">★ ${b.my_rating}</span>`
      : `<button class="btn btn-outline btn-sm" data-action="rate" data-id="${b.id}" data-title="${e(b.title)}">Rate</button>`;
  return '<span class="muted small">—</span>';
}

function feedbackModal(id, title) {
  modal(
    "Rate this campaign",
    e(title || "Your donation"),
    `<form id="feedback-form"><input type="hidden" name="appointment_id" value="${Number(id)}"/>
 <div class="rating-row">${[1, 2, 3, 4, 5].map((n) => `<label><input type="radio" name="rating" value="${n}" ${n === 5 ? "checked" : ""}/><span>${n} ★</span></label>`).join("")}</div>
 <div class="field" style="margin-top:16px"><label>Anything we could do better? (optional)</label><textarea name="comment" class="textarea" maxlength="400"></textarea></div>
 <div class="modal-footer"><button type="button" class="btn btn-light" data-action="close-modal">Cancel</button><button type="submit" class="btn btn-primary">${icon("check", "icon-sm")} Send feedback</button></div></form>`,
  );
}

function stockChart(t) {
  // rebuild the last 14 days of stock backwards from today's units
  let s = t.units;
  const past = [];
  for (let i = t.recent.length - 1; i >= 0; i--) {
    past.unshift({ date: addDay(t.recent[i].date, 1), v: Math.max(0, Math.round(s)) });
    s = s - t.recent[i].collected + t.recent[i].used;
  }
  const future = t.points.map((p) => ({ date: addDay(p.date, 1), v: p.stock }));
  const data = [...past, ...future];
  const W = 870, H = 278, L = 51, R = 15, T = 19, B = 35;
  const max = Math.max(5, t.threshold, ...data.map((d) => d.v)) * 1.18;
  const pt = (v, i) => ({ x: L + ((W - L - R) * i) / (data.length - 1), y: T + (H - T - B) * (1 - v / max) });
  const coords = (arr, offset) => arr.map((d, i) => { const p = pt(d.v, i + offset); return p.x.toFixed(1) + "," + p.y.toFixed(1); }).join(" ");
  const grid = Array.from({ length: 5 }, (_, i) => {
    const y = T + ((H - T - B) * i) / 4;
    return `<line class="chart-grid" x1="${L}" y1="${y}" x2="${W - R}" y2="${y}"/><text class="chart-axis" x="${L - 13}" y="${y + 4}" text-anchor="end">${Math.round(max * (1 - i / 4))}</text>`;
  }).join("");
  const ty = pt(t.threshold, 0).y;
  const divX = pt(0, past.length - 1).x;
  const labels = [0, 5, 10, past.length - 1, data.length - 1]
    .filter((v, i, a) => a.indexOf(v) === i)
    .map((i) => `<text class="chart-axis" text-anchor="middle" x="${pt(0, i).x}" y="${H - 8}">${short(data[i].date)}</text>`)
    .join("");
  return `<svg class="chart" viewBox="0 0 ${W} ${H}" role="img" aria-label="${e(t.blood_type)} stock for the last 14 days and the 7-day projection">${grid}
 <line class="chart-threshold" x1="${L}" y1="${ty}" x2="${W - R}" y2="${ty}"/><text class="chart-axis threshold-label" x="${W - R - 4}" y="${ty - 6}" text-anchor="end">safe level ${t.threshold}</text>
 <line class="chart-divide" x1="${divX}" y1="${T}" x2="${divX}" y2="${H - B}"/><text class="chart-axis" x="${divX + 6}" y="${T + 10}">today</text>
 <polyline class="chart-stock" points="${coords(past, 0)}"/><polyline class="chart-future" points="${coords([past[past.length - 1], ...future], past.length - 1)}"/>
 ${future.map((d, i) => { const p = pt(d.v, past.length + i); return `<circle cx="${p.x}" cy="${p.y}" r="4" fill="#d94c5c" stroke="white" stroke-width="2"/>`; }).join("")}${labels}</svg>`;
}

async function outlookPage() {
  const [o, invs] = await Promise.all([api("/api/outlook"), api("/api/inventory")]);
  state.outlook = o;
  state.inventory = invs;
  const sel = o.types.find((t) => t.blood_type === state.outlookType) || o.most_urgent || o.types[0];
  const inv = sel && invs.find((x) => x.blood_type === sel.blood_type);
  if (!sel) return empty("chart", "No stock history yet", "Add daily stock movements to see the outlook.");
  const sum7 = (k) => Math.round(sel.points.reduce((s, p) => s + p[k], 0));
  const m = sel.metrics;
  return (
    heading("Blood stock & shortage outlook", "Current stock per blood type and which one runs out next — a 7-day projection from forecast donations and usage.", aiTag("Best model per type")) +
    `<div class="stack">${shortageBanner(o.most_urgent)}
 <div class="inventory-grid">${o.types
   .map(
     (t) =>
       `<button class="blood-card surface outlook-card ${t.blood_type === sel.blood_type ? "selected" : ""}" data-action="outlook-type" data-type="${e(t.blood_type)}"><div class="blood-heading"><span class="blood-label">${e(t.blood_type)}</span>${statusTag(t.status)}</div><div><div class="blood-number">${number(t.units)} <small>units</small></div><div class="muted small" style="margin-top:6px">${dos(t.days_of_supply)} days of supply · safe level ${t.threshold}</div></div></button>`,
   )
   .join("")}</div>
 <div class="surface panel"><div class="panel-title"><h3>${e(sel.blood_type)} stock: last 14 days and next 7</h3>${aiTag("7-day projection")}</div>${stockChart(sel)}
 <div class="legend stock-legend"><span>Stock (history)</span><span>Projected stock</span><span>Safe level</span></div></div>
 <div class="forecast-summary"><div class="surface"><span>Expected use · next 7 days</span><strong>${number(sum7("used"))}</strong><p class="muted tiny" style="margin-top:5px">${e(m.used.selected_label)} · error ±${m.used.mae}/day</p></div>
 <div class="surface"><span>Expected donations · next 7 days</span><strong>${number(sum7("collected"))}</strong><p class="muted tiny" style="margin-top:5px">${e(m.collected.selected_label)} · error ±${m.collected.mae}/day</p></div>
 <div class="surface"><span>Stock in 7 days</span><strong>${number(sel.points[6].stock)}</strong><p class="muted tiny" style="margin-top:5px">${sel.days_until_unsafe === null ? "Stays above the safe level" : sel.days_until_unsafe === 0 ? "Already below the safe level" : "Drops below the safe level on day " + sel.days_until_unsafe}</p></div></div>
 ${state.user.role === "admin" ? `<div class="filters"><button class="btn btn-primary" data-action="mobilise" data-type="${e(sel.blood_type)}">${icon("alert", "icon-sm")} Post an urgent request for ${e(sel.blood_type)}</button>${inv ? `<button class="btn btn-light" data-action="edit-inventory" data-id="${inv.id}">Edit ${e(sel.blood_type)} stock level</button>` : ""}</div>` : ""}
 <div class="source-strip demo">${icon("info")} ${e(o.note)} Model: ${e(o.model)}. Errors are from a chronological 80/20 test.</div></div>`
  );
}

async function requestsPage() {
  if (state.requestId) return requestDetail(state.requestId);
  const [list, o] = await Promise.all([api("/api/requests"), api("/api/outlook")]);
  const top = o.most_urgent;
  const pre = state.prefillType || (top && top.status !== "green" ? top.blood_type : "O+");
  state.prefillType = null;
  const preT = o.types.find((t) => t.blood_type === pre);
  const suggest = preT ? Math.max(2, Math.ceil(preT.threshold * 1.5 - preT.units)) : 4;
  const org = state.user.role === "admin";
  const form = org
    ? `<div class="surface panel"><div class="panel-title"><h3>Post an urgent request</h3>${aiTag("Smart matching")}</div>
 <form id="request-form" class="form-grid"><div class="field"><label>Blood type</label><select class="select" name="blood_type">${bloodTypes.slice(1).map((x) => `<option ${x === pre ? "selected" : ""}>${x}</option>`).join("")}</select></div>
 <div class="field"><label>Units needed</label><input class="input" type="number" name="units" min="1" max="100" value="${suggest}" required/></div>
 <div class="field"><label>Needed by</label><input class="input" type="date" name="needed_by" min="${todayISO()}" value="${addDay(todayISO(), 2)}" required/></div>
 <div class="field"><label>Note (optional)</label><input class="input" name="note" maxlength="200" placeholder="e.g. trauma cases this weekend"/></div>
 <div class="full"><button class="btn btn-primary" type="submit">${icon("search", "icon-sm")} Find matching donors</button><p class="muted tiny" style="margin-top:8px">Suggested ${suggest} units brings ${e(pre)} back above 1.5× its safe level.</p></div></form></div>`
    : "";
  const table = list.length
    ? `<div class="table-wrap"><table class="data-table"><thead><tr><th>Request</th><th>Needed by</th><th>Alerted</th><th>Said yes</th><th>Donated</th><th>Status</th><th></th></tr></thead><tbody>${list
        .map(
          (r) =>
            `<tr><td><b>${r.units} × ${e(r.blood_type)}</b><div class="muted tiny" style="margin-top:5px">${e(r.centre_name)}${r.note ? " · " + e(r.note) : ""}</div></td><td>${dateLabel(r.needed_by)}</td><td>${r.alerted}</td><td>${r.said_yes}</td><td>${r.donated}/${r.units}</td><td><span class="tag ${r.status === "open" ? "tag-red" : r.status === "fulfilled" ? "tag-green" : "tag-gray"}">${capitalize(r.status)}</span></td><td><button class="btn btn-outline btn-sm" data-action="open-request" data-id="${r.id}">Open</button></td></tr>`,
        )
        .join("")}</tbody></table></div>`
    : empty("alert", "No urgent requests yet", "Post one when the shortage outlook shows a blood type running low.");
  return (
    heading("Urgent requests", "Post a request and let the AI pick the donors most likely to come — not everyone.") +
    `<div class="stack">${form}<div class="surface panel"><div class="panel-title"><h3>Requests</h3><span class="tag tag-gray">${list.length} entries</span></div>${table}</div></div>`
  );
}

async function requestDetail(id) {
  const d = await api(`/api/requests/${id}`);
  const r = d.request, m = d.match, s = d.summary;
  const open = r.status === "open", org = state.user.role === "admin";
  const responses = d.alerts.length
    ? `<div class="surface panel"><div class="panel-title"><h3>Responses</h3>${open && org ? `<button class="btn btn-light btn-sm" data-action="simulate-replies">${icon("refresh", "icon-sm")} Simulate donor replies (demo)</button>` : ""}</div>
 <div class="kpi-grid" style="margin-bottom:16px">${miniStat("Alerted", s.alerted)}${miniStat("Said yes", s.yes, "", "success-text")}${miniStat("Said no", s.no)}${miniStat("Donated", `${s.donated}/${r.units}`, "", "danger-text")}</div>
 <div class="track" style="margin-bottom:18px"><span style="width:${Math.min(100, Math.round((s.donated / r.units) * 100))}%"></span></div>
 <div class="table-wrap"><table class="data-table"><thead><tr><th>Donor</th><th>Type</th><th>AI score</th><th>Reply</th><th></th></tr></thead><tbody>${d.alerts
   .map(
     (a) =>
       `<tr><td><b>${e(a.name)}</b>${a.is_synthetic ? '<div class="muted tiny" style="margin-top:4px">demo donor</div>' : ""}</td><td>${e(a.blood_type)}</td><td>${Math.round(a.score)}</td><td>${a.response === "yes" ? '<span class="tag tag-green">Coming</span>' : a.response === "no" ? '<span class="tag tag-gray">Can\'t</span>' : '<span class="muted small">waiting…</span>'}</td><td>${a.response === "yes" ? (a.donated ? '<span class="success-text semibold">✓ Donated</span>' : org ? `<button class="btn btn-outline btn-sm" data-action="mark-donated" data-id="${a.id}">Mark donated</button>` : "") : ""}</td></tr>`,
   )
   .join("")}</tbody></table></div></div>`
    : "";
  const ex = m.excluded;
  const matchPanel = open
    ? `<div class="surface panel"><div class="panel-title"><h3>${d.alerts.length ? "More donors you could alert" : "AI-ranked donors"}</h3>${aiTag("Smart matching")}</div>
 ${m.total_candidates
   ? `<p class="small" style="line-height:1.7">${m.total_candidates} compatible, eligible donors within 35 km${d.alerts.length ? " (not yet alerted)" : ""}. The model suggests alerting the top <b>${m.selected_count}</b>, who are expected to give about <b>${m.expected_yes}</b> yeses for ${r.units} units — not everyone, to avoid alert fatigue.</p>`
   : `<p class="small">Every compatible, eligible donor within 35 km has already been alerted.</p>`}
 <p class="muted tiny" style="margin:8px 0 14px">Excluded: ${ex.not_compatible} incompatible type · ${ex.not_eligible} not eligible yet (90-day rule, age or weight) · ${ex.too_far} too far · ${ex.already_alerted} already alerted</p>
 ${m.expected_yes < r.units ? `<div class="source-strip demo" style="margin-bottom:14px">${icon("alert")} Not enough likely donors in range for ${r.units} units. Consider a targeted campaign for ${e(r.blood_type)} or asking a nearby centre to transfer stock.</div>` : ""}
 ${m.candidates.length ? `<div class="table-wrap"><table class="data-table"><thead><tr><th>#</th><th>Donor</th><th>Type</th><th>Score</th><th>Chance of yes</th><th>Why</th></tr></thead><tbody>${m.candidates
   .map(
     (c, i) =>
       `<tr class="${c.selected ? "" : "dimmed"}"><td class="muted">${i + 1}</td><td><b>${e(c.name)}</b>${c.selected ? ' <span class="tag tag-red tag-xs">ALERT</span>' : ""}</td><td>${e(c.blood_type)}</td><td><div class="score"><div class="score-bar"><span style="width:${c.score}%"></span></div>${c.score}</div></td><td>${Math.round(c.p_yes * 100)}%</td><td class="tiny">${c.reasons.map(e).join(" · ")}</td></tr>`,
   )
   .join("")}</tbody></table></div>` : ""}
 ${org && m.selected_count ? `<button class="btn btn-primary" style="margin-top:16px" data-action="send-alerts">${icon("send", "icon-sm")} ${d.alerts.length ? `Alert ${m.selected_count} more donors` : `Send alerts to ${m.selected_count} donors`}</button>` : ""}</div>`
    : "";
  return (
    `<button class="link-btn" data-action="back-requests" style="margin-bottom:12px">← All requests</button>` +
    heading(
      `${r.units} × ${e(r.blood_type)} needed by ${dateLabel(r.needed_by)}`,
      `${e(r.centre_name)}${r.note ? " · " + e(r.note) : ""}`,
      `<div class="filters"><span class="tag ${open ? "tag-red" : r.status === "fulfilled" ? "tag-green" : "tag-gray"}">${capitalize(r.status)}</span>${open && org ? `<button class="btn btn-light btn-sm" data-action="close-request" data-id="${r.id}">Close request</button>` : ""}</div>`,
    ) +
    `<div class="stack">${responses}${matchPanel}</div>`
  );
}

async function eligibilityPage() {
  const info = await api("/api/eligibility");
  const st = info.status;
  const statusCard = st
    ? `<div class="surface panel elig-status"><div class="elig-icon ${st.verdict === "eligible" ? "ok" : "wait"}">${icon(st.verdict === "eligible" ? "check" : "clock", "icon-xl")}</div><div><div class="muted tiny semibold">BASED ON YOUR RECORD</div><h3>${e(info.labels[st.verdict])}</h3><p class="muted small">${
        st.verdict === "eligible"
          ? (st.days_since_last !== null ? `Last donation ${st.days_since_last} days ago.` : "First-time donor.") + " Answer today's questions below before you go."
          : st.eligible_from
            ? `You can donate again from ${dateLabel(st.eligible_from)} (${info.interval_days} days between whole-blood donations).`
            : e(st.reasons.join(" "))
      }${st.checks.some((c) => c.label.startsWith("Medicines") && !c.ok) ? ' <button class="link-btn" data-view="hemocare">Open HemoCare</button>' : ""}</p></div></div>`
    : `<div class="source-strip demo">${icon("info")} Add your blood type, birth year and weight in My Profile to use the eligibility check. <button class="link-btn" data-view="profile">Open My Profile</button></div>`;
  let body = "";
  const res = state.eligResult;
  if (res) {
    const ok = res.result.verdict === "eligible" || res.result.verdict === "eligible_after_meal";
    body = `<div class="surface panel"><div class="muted tiny semibold ${ok ? "success-text" : ""}" style="${ok ? "" : "color:var(--amber)"}">TODAY'S RESULT</div><h2 style="margin:6px 0 4px">${e(res.label)}</h2>
 ${res.result.verdict === "deferred" && res.result.eligible_from ? `<p class="muted small">You can donate from ${dateLabel(res.result.eligible_from)}</p>` : ""}
 <div class="explain"><div class="banner-tags">${aiTag(res.used_llm ? "AI explanation" : "Explanation")}${res.used_llm ? "" : '<span class="muted tiny">demo mode (no LLM key)</span>'}</div><p>${e(res.explanation)}</p></div></div>
 <div class="surface panel"><div class="panel-title"><h3>How the rules engine decided</h3></div><div class="check-list">${res.result.checks
   .map((c) => `<div class="${c.ok ? "ok" : "bad"}">${icon(c.ok ? "check" : "close", "icon-sm")} <span><b>${e(c.label)}</b>${c.detail !== "OK" ? ` <span class="muted">— ${e(c.detail)}</span>` : ""}</span></div>`)
   .join("")}</div></div>
 <div class="filters">${ok ? `<button class="btn btn-primary" data-view="campaigns">${icon("calendar", "icon-sm")} Book a slot</button>` : ""}<button class="btn btn-light" data-action="elig-reset">Check again</button></div>`;
  } else if (st) {
    body = `<form id="eligibility-form" class="surface panel"><div class="panel-title"><h3>Today's health questions</h3><span class="tag tag-gray">${info.questions.length} questions</span></div>
 ${info.questions.map((q, i) => `<div class="question-row"><span><span class="muted">${i + 1}.</span> ${e(q.text)}</span><div class="yes-no"><label><input type="radio" name="${e(q.id)}" value="yes" required/><span>Yes</span></label><label><input type="radio" name="${e(q.id)}" value="no"/><span>No</span></label></div></div>`).join("")}
 <button class="btn btn-primary" type="submit" style="margin-top:18px">${icon("shield", "icon-sm")} See my result</button></form>`;
  }
  return (
    heading("Eligibility check", "One minute, fifteen quick questions. Our rules engine gives the verdict; AI explains it in plain language.") +
    `<div class="stack">${statusCard}${
      info.hemoscan
        ? `<div class="source-strip ${info.hemoscan.ok ? "" : "demo"}">${icon("flask")} ${e(info.hemoscan.message)} <button class="link-btn" data-view="hemoscan">Open HemoScan</button></div>`
        : ""
    }${body}<div class="disclaimer">${icon("shield", "icon-sm")} ${e(info.note)}${
      info.sources?.length
        ? `<details class="elig-sources"><summary>Sources (checked ${dateLabel(info.checked_on)})</summary><ul>${info.sources.map((x) => `<li><a href="${e(x.url)}" target="_blank" rel="noopener">${e(x.title)}</a></li>`).join("")}</ul></details>`
        : ""
    }</div></div>`
  );
}

async function reportsPage() {
  const r = await api("/api/reports");
  state.suggestion = r.suggestion;
  const t = r.turnout, m = r.model, s = r.suggestion;
  const msg = r.at_risk[0];
  return (
    heading("Insights & campaign planner", `Your completed drives, donor feedback, donors to re-invite, and where to hold the next drive.`) +
    `<div class="stack"><section class="kpi-grid">${miniStat("Donations at campaigns", number(t.donated), "Recorded at check-in")}${miniStat("No-show rate", Math.round(t.no_show_rate * 100) + "%", `${t.no_show} of ${t.total} bookings`)}${miniStat("Average rating", r.ratings.average ? "★ " + r.ratings.average.toFixed(1) : "—", `${r.ratings.count} reviews`)}${miniStat("Donors drifting away", r.at_risk.length, "Within 25 km of your centre")}</section>
 ${s ? `<section class="shortage-banner amber"><div><div class="banner-tags">${aiTag("Campaign planner")}</div><h2>Hold a drive for ${e(s.blood_type)} in ${e(s.city)} on ${dateLabel(s.date)}</h2><p>${s.eligible_donors} donors who can give to ${e(s.blood_type)} patients are eligible there now, and ${e(s.best_day)} bring in the most donations (last 8 weeks). ${e(s.blood_type)} has ${dos(s.days_of_supply)} days of supply left.</p></div><button class="btn btn-primary" data-action="suggest-campaign">${icon("plus", "icon-sm")} Create this campaign</button></section>` : ""}
 <section class="section-grid"><div class="surface panel"><div class="panel-title"><h3>Regular donors drifting away</h3>${aiTag("Return prediction")}</div>
 <p class="muted small" style="margin-bottom:12px">Donors with 2+ donations whose chance of donating again in the next 6 months is below 40%.</p>
 ${r.at_risk.length ? `<div class="table-wrap"><table class="data-table"><thead><tr><th>Donor</th><th>Type</th><th>Donations</th><th>Last</th><th>Return</th></tr></thead><tbody>${r.at_risk
   .map((x) => `<tr><td><b>${e(x.name)}</b><div class="muted tiny" style="margin-top:4px">Main factor: ${e(x.top_factor.toLowerCase())}</div></td><td>${e(x.blood_type)}</td><td>${x.donations}</td><td>${x.days_since_last}d ago</td><td><span class="tag ${x.p_return < 0.2 ? "tag-red" : "tag-amber"}">${Math.round(x.p_return * 100)}%</span></td></tr>`)
   .join("")}</tbody></table></div>` : empty("users", "No drifting donors", "Everyone nearby looks likely to return.")}
 ${msg ? `<div class="explain"><div class="banner-tags">${aiTag("Suggested message")}</div><p><i>“Hi ${e(msg.name.split(" ")[0])}, it's been a while — thank you for your ${msg.donations} donations so far! ${e(msg.blood_type)} blood is needed at ${e(r.centre.name)} this month. Book a 30-minute slot in HemoLink.”</i></p></div>` : ""}</div>
 <div class="stack"><div class="surface panel"><div class="panel-title"><h3>Model card</h3><span class="tag tag-gray">Logistic regression</span></div><div class="method-list">
 <div>${icon("users", "icon-sm")} <strong>Trained on:</strong> ${m.train_size} donors · tested on ${m.test_size} held out</div>
 <div>${icon("trend", "icon-sm")} <strong>AUC:</strong> ${m.auc.toFixed(2)} · <strong>Accuracy:</strong> ${Math.round(m.accuracy * 100)}%</div></div>
 <div class="weights">${m.feature_names.map((f, i) => `<div><span>${e(f)}</span><b class="${m.model.weights[i] >= 0 ? "success-text" : "danger-text"}">${m.model.weights[i] >= 0 ? "+" : ""}${m.model.weights[i].toFixed(2)}</b></div>`).join("")}</div>
 <p class="muted tiny" style="margin-top:12px">Trained on synthetic demo history — retrain on real records before drawing conclusions.</p></div>
 <div class="surface panel"><div class="panel-title"><h3>Latest feedback</h3></div>${r.ratings.latest.length ? r.ratings.latest.map((f) => `<div class="activity"><div class="activity-icon">★</div><div><h4>${f.rating} · ${e(f.title)}</h4><p>${e(f.comment || "—")}</p></div></div>`).join("") : '<p class="muted small">No feedback yet.</p>'}</div></div></section></div>`
  );
}

async function usersPage() {
  const q = new URLSearchParams({ q: state.userQ || "", role: state.userRole || "" });
  const d = await api("/api/admin/users?" + q.toString());
  const c = d.counts;
  const chip = (v, label) => `<button class="hs-chip ${(state.userRole || "") === v ? "on" : ""}" data-action="user-role-filter" data-role="${v}">${label}</button>`;
  const ROLE_TAG = { donor: "tag-gray", organizer: "tag-green", admin: "tag-ai" };
  const rowsHtml = d.users
    .map((u) => {
      const act =
        u.role === "donor"
          ? `<button class="btn btn-outline btn-sm" data-action="set-role" data-id="${u.id}" data-role="organizer" data-name="${e(u.name)}">Approve as organizer</button>`
          : u.role === "organizer"
            ? `<button class="btn btn-light btn-sm" data-action="set-role" data-id="${u.id}" data-role="donor" data-name="${e(u.name)}">Change to donor</button>`
            : '<span class="muted tiny">—</span>';
      return `<tr><td><b>${e(u.name)}</b><div class="muted tiny" style="margin-top:4px">${e(u.email)}</div></td><td><span class="tag ${ROLE_TAG[u.role]}">${e(roles[u.role])}</span></td><td>${e(u.blood_type)}</td><td>${e(u.city || "—")}</td><td>${u.role === "organizer" ? `${u.campaigns} campaigns` : `${u.donations} donations`}</td><td class="small">${e(String(u.created_at).slice(0, 10))}</td><td>${act}</td></tr>`;
    })
    .join("");
  return (
    heading("Users & organizers", "Everyone signs up as a donor. Approve community groups (universities, companies, NGOs) as drive organizers here.") +
    `<div class="stack"><div class="kpi-grid">${miniStat("Donors", number(c.donor))}${miniStat("Drive organizers", number(c.organizer), "", "success-text")}${miniStat("Blood bank admins", number(c.admin))}${miniStat("Synthetic demo donors", number(c.synthetic), "Used by the AI, cannot log in")}</div>
 <div class="surface panel"><div class="panel-title"><h3>Accounts</h3><span class="tag tag-gray">${d.users.length} shown</span></div>
 <div class="filters" style="margin-bottom:14px;justify-content:space-between"><div class="hs-chips" style="margin:0">${chip("", "All")}${chip("donor", "Donors")}${chip("organizer", "Organizers")}${chip("admin", "Admins")}</div>
 <form id="user-search-form" class="search-field" style="max-width:300px">${icon("search")}<input class="input" name="q" placeholder="Search name or email" value="${e(state.userQ || "")}"/></form></div>
 ${d.users.length ? `<div class="table-wrap"><table class="data-table"><thead><tr><th>Name</th><th>Role</th><th>Blood</th><th>City</th><th>Activity</th><th>Joined</th><th></th></tr></thead><tbody>${rowsHtml}</tbody></table></div>` : empty("users", "No matching accounts", "Try another name or filter.")}</div>
 <div class="disclaimer">${icon("shield", "icon-sm")} Organizers can create campaigns and check donors in, but cannot see stock, urgent requests or anyone's HemoScan reports.</div></div>`
  );
}

async function modelsPage() {
  const m = await api("/api/models");
  const rm = m.return_model;
  const w = m.matching_weights;
  const ev = m.evaluation;
  const r = ev.return_model;
  const mt = ev.matching;
  const tr = m.training;
  const LBL = { seasonal_naive: "Same weekday last week", weekday_mean: "Weekday average", rf: "Random Forest" };
  const pct = (x) => (x == null ? "–" : Math.round(x * 100) + "%");
  const pick = (x) => `<span class="tag ${x.selected === "rf" ? "tag-ai" : "tag-gray"}">${e(LBL[x.selected] || x.selected)}</span>`;
  const llmCard = `<div class="surface panel"><div class="panel-title"><h3>${icon("bot", "icon-sm")} Language model (AI explanations)</h3><span class="tag ${m.llm.configured ? "tag-green" : "tag-amber"}">${m.llm.configured ? "Key set" : "Not set — using templates"}</span></div>
 <div class="method-list"><div><strong>Provider:</strong> ${e(m.llm.provider)} · <strong>Model:</strong> ${e(m.llm.model)}</div><div><strong>Used for:</strong> HemoScan explanations and Q&amp;A, eligibility explanations, the health assistant. Rules always decide; the model only explains.</div>${m.llm.last_error ? `<div class="danger-text"><strong>Last error:</strong> ${e(m.llm.last_error)} (${e(m.llm.last_error_at)})</div>` : ""}</div>
 <div class="filters" style="margin-top:12px"><button class="btn btn-primary btn-sm" data-action="llm-test">${icon("spark", "icon-sm")} Test AI connection</button><span id="llm-test-result" class="small"></span></div>
 <p class="muted tiny" style="margin-top:10px">To turn it on, put <code>ANTHROPIC_API_KEY=…</code> (or OpenAI / Gemini) in the <code>.env</code> file and restart. The key stays on the server and is never shown here.</p></div>`;
  const trainCard = tr
    ? `<div class="surface panel"><div class="panel-title"><h3>${icon("chart", "icon-sm")} Training run</h3><span class="tag tag-green">${e(tr.trained)}</span></div>
 <div class="kpi-grid">${miniStat("Series trained", tr.series, tr.data_file ? "Official MOH data" : "Synthetic data")}${miniStat("Random Forest chosen", tr.chosen.rf)}${miniStat("Simpler method chosen", tr.chosen.weekday_mean + tr.chosen.seasonal_naive)}${miniStat("Better than baseline", tr.avg_gain + "%", "average error reduction", "success-text")}</div>
 <p class="muted tiny" style="margin-top:10px">Re-run with <code>python scripts/train_models.py</code> — saves models/ and writes docs/MODEL_REPORT.md.</p></div>`
    : `<div class="source-strip demo">${icon("info")} Models are trained on start-up. Run <code>python scripts/train_models.py</code> to train every series, save the models and write docs/MODEL_REPORT.md.</div>`;
  return (
    heading("AI models", "How each AI feature works, how it was validated, and whether it treats donors fairly.", `<span class="tag ${m.official_data.present ? "tag-green" : "tag-amber"}">${icon("book", "icon-sm")} ${m.official_data.present ? "Official MOH data loaded" : "Official data not imported"}</span>`) +
    `<div class="stack">${trainCard}
 <div class="surface panel"><div class="panel-title"><h3>1 · Shortage outlook — best method per blood type</h3><span class="tag tag-gray">Rolling cross-validation · 4 × 7 days</span></div>
 <div class="table-wrap"><table class="data-table"><thead><tr><th>Type</th><th>Usage → chosen</th><th>Error</th><th>Donations → chosen</th><th>Error</th><th>Naive error (use / don.)</th></tr></thead><tbody>${m.forecast
   .map((f) => `<tr><td><b>${e(f.blood_type)}</b></td><td>${pick(f.used)}</td><td>±${f.used.mae}</td><td>${pick(f.collected)}</td><td>±${f.collected.mae}</td><td class="muted">±${f.used.baseline_mae} / ±${f.collected.baseline_mae}</td></tr>`)
   .join("")}</tbody></table></div><p class="muted tiny" style="margin-top:10px">Units per day; lower is better. Three methods compete per series; rare types often pick a simple method because their daily counts are too small for a Random Forest to help. Stock data is simulated.</p></div>
 <section class="section-grid"><div class="surface panel"><div class="panel-title"><h3>2 · Donor return prediction</h3><span class="tag tag-gray">5-fold CV</span></div>
 ${r.available ? `<div class="kpi-grid kpi-3">${miniStat("AUC", r.auc.toFixed(2), "± " + r.auc_sd.toFixed(2))}${miniStat("Accuracy", pct(r.accuracy), "base rate " + pct(r.base_rate))}${miniStat("Brier score", r.brier, "baseline " + r.brier_baseline)}</div>
 <h4 class="sub-h">Calibration (predicted vs actual)</h4><div class="calib">${r.calibration.filter((c) => c.n).map((c) => `<div><span>${c.bin}</span><div class="calib-bars"><i class="p" style="width:${(c.predicted || 0) * 100}%"></i><i class="a" style="width:${(c.actual || 0) * 100}%"></i></div><b>${pct(c.predicted)} / ${pct(c.actual)}</b></div>`).join("")}</div><div class="legend"><span class="lg-p">Predicted</span><span class="lg-a">Actual</span></div>` : `<p class="muted">${e(r.reason)}</p>`}
 <h4 class="sub-h">What drives the score</h4><div class="weights">${rm.feature_names.map((f, i) => `<div><span>${e(f)}</span><b class="${rm.model.weights[i] >= 0 ? "success-text" : "danger-text"}">${rm.model.weights[i] >= 0 ? "+" : ""}${rm.model.weights[i].toFixed(2)}</b></div>`).join("")}</div></div>
 <div class="surface panel"><div class="panel-title"><h3>3 · Smart donor matching</h3><span class="tag tag-gray">Scoring rules</span></div><div class="weights">
 <div><span>Distance (closer is better)</span><b>${w.distance}</b></div><div><span>Past reply rate</span><b>${w.responseRate}</b></div><div><span>Exact blood type</span><b>${w.exactType}</b></div><div><span>Regular donor</span><b>${w.regular}</b></div><div><span>Ready (120+ days since last)</span><b>${w.ready}</b></div><div><span>Alerted in last 7 days</span><b class="danger-text">−${w.fatiguePenalty}</b></div><div><span>Search radius</span><b>${w.maxKm} km</b></div></div></div></section>
 <div class="surface panel"><div class="panel-title"><h3>4 · Fairness check</h3><span class="tag ${mt.age_flags.length ? "tag-amber" : "tag-green"}">${mt.age_flags.length ? mt.age_flags.length + " group(s) to review" : "No age gaps flagged"}</span></div>
 <p class="small muted" style="margin-bottom:12px">${mt.requests_simulated} urgent requests simulated (every blood type × every centre). Who gets alerted, among eligible compatible donors? Groups below 80% of the best group's rate are flagged (four-fifths rule).</p>
 <section class="section-grid"><div><h4 class="sub-h">Matching · by age band</h4><div class="table-wrap"><table class="data-table"><thead><tr><th>Age</th><th>Eligible</th><th>Alerted</th><th>vs best</th><th>Avg km</th></tr></thead><tbody>${mt.by_age.map((g) => `<tr><td>${e(g.group)}</td><td>${g.eligible}</td><td>${pct(g.rate)}</td><td>${g.flag ? `<span class="tag tag-amber">${g.ratio}</span>` : g.ratio}</td><td>${g.avg_km}</td></tr>`).join("")}</tbody></table></div></div>
 <div><h4 class="sub-h">Return prediction · by age band</h4><div class="table-wrap"><table class="data-table"><thead><tr><th>Age</th><th>n</th><th>Actual</th><th>Predicted</th><th>AUC</th></tr></thead><tbody>${r.available ? r.by_age.map((g) => `<tr><td>${e(g.group)}</td><td>${g.n}</td><td>${pct(g.actual_rate)}</td><td>${pct(g.predicted_rate)}</td><td>${g.auc ?? "–"}</td></tr>`).join("") : ""}</tbody></table></div></div></section>
 <div class="source-strip ${mt.age_flags.length ? "demo" : ""}" style="margin-top:14px">${icon(mt.age_flags.length ? "alert" : "check")} ${e(mt.explanation)}</div>
 <p class="muted tiny" style="margin-top:10px">${e(mt.note)}</p></div>
 ${llmCard}
 <div class="surface panel"><div class="panel-title"><h3>5 · Eligibility rules in use</h3></div><div class="source-strip demo" style="margin-bottom:14px">${icon("alert")} ${e(m.rules.sourceNote)}</div>
 <div class="filters" style="margin-bottom:12px"><span class="tag tag-gray">Age ${m.rules.minAge}–${m.rules.maxAge} (first time ≤ ${m.rules.firstTimeMaxAge}; ${m.rules.maxAge + 1}–${m.rules.absoluteMaxAge} with check-up)</span><span class="tag tag-gray">Weight ≥ ${m.rules.minWeightKg} kg</span><span class="tag tag-gray">Hb ≥ ${m.rules.hbMinGdl} g/dL</span><span class="tag tag-gray">Men every ${m.rules.intervalDaysMale} days · women every ${m.rules.intervalDaysFemale} days</span></div>
 <div class="table-wrap"><table class="data-table"><tbody>${m.rules.questions.map((q) => `<tr><td>${e(q.text)}</td><td class="muted small" style="white-space:nowrap">${q.action === "defer" ? `wait ${q.deferDays} day${q.deferDays === 1 ? "" : "s"}` : q.action === "staff" ? "staff check" : "eat first"}</td></tr>`).join("")}</tbody></table></div></div>
 <div class="source-strip demo">${icon("info")} ${e(m.note)}</div></div>`
  );
}

function modal(title, subtitle, content) {
  modalRoot.innerHTML = `<div class="modal-backdrop" data-action="overlay-close"><div class="modal"><div class="modal-header"><div><h2>${title}</h2><p>${subtitle}</p></div><button data-action="close-modal" aria-label="Close">${icon("close")}</button></div><div class="modal-body">${content}</div></div></div>`;
}
function closeModal() {
  if (state.pickMap) {
    state.pickMap.remove();
    state.pickMap = null;
    state.pickPin = null;
  }
  modalRoot.innerHTML = "";
}
function bookModal(id) {
  const c = state.campaigns.find((x) => x.id === Number(id));
  if (!c) return;
  const available = c.slots.filter((x) => x.remaining > 0);
  modal(
    "Book an appointment",
    `${e(c.title)} · ${dateLabel(c.event_date)}`,
    `<form id="booking-form"><input type="hidden" name="campaign_id" value="${c.id}"/><p class="muted small" style="margin-bottom:18px">Choose one available appointment time.</p>
 ${available.map((s, i) => `<label class="booking-slot"><span><input type="radio" name="slot_id" value="${s.id}" ${i === 0 ? "checked" : ""} required/> &nbsp; <b>${e(s.start_time)}</b></span><span class="tag tag-green">${s.remaining} left</span></label>`).join("")}
 <div class="modal-footer"><button type="button" class="btn btn-light" data-action="close-modal">Cancel</button><button type="submit" class="btn btn-primary">${icon("calendar", "icon-sm")} Confirm booking</button></div></form>`,
  );
}
function campaignModal(pre = {}) {
  const today = new Date().toLocaleDateString("en-CA");
  modal(
    "Create a campaign",
    "Plan a donation event with bookable time slots.",
    `<form id="new-campaign-form" class="form-grid">
 <div class="field full"><label>Campaign name</label><input name="title" class="input" minlength="4" maxlength="120" required placeholder="e.g. Community Heroes Blood Drive" value="${e(pre.title || "")}"/></div>
 <div class="field full"><label>Venue</label><input name="venue" class="input" required minlength="4" placeholder="e.g. Community Hall, Putrajaya" value="${e(pre.venue || "")}"/></div>
 <div class="field"><label>City</label><input name="city" class="input" required minlength="2" placeholder="Putrajaya" value="${e(pre.city || "")}"/></div><div class="field"><label>Event date</label><input name="event_date" class="input" required type="date" min="${today}" value="${e(pre.date || "")}"/></div>
 <div class="field"><label>Time slots (comma separated)</label><input name="times" class="input" required placeholder="09:00, 11:00, 14:00" value="09:00, 11:00"/></div>
 <div class="field"><label>Capacity per slot</label><input name="capacity" class="input" required type="number" min="1" max="250" value="20"/></div>
 <div class="field full"><label>Event description</label><textarea name="description" class="textarea" maxlength="900" placeholder="Tell donors about the event and its purpose">${e(pre.description || "")}</textarea></div>
 ${pickerField()}
 <div class="full modal-footer"><button type="button" class="btn btn-light" data-action="close-modal">Cancel</button><button type="submit" class="btn btn-primary">${icon("plus", "icon-sm")} Create event</button></div></form>`,
  );
  initPicker(null);
}

// ---------- "pick location on map" for organizers (create + edit)
const PICK_DEFAULT = [3.139, 101.6869]; // Kuala Lumpur
const inMalaysia = (lat, lng) => lat >= 0.5 && lat <= 7.5 && lng >= 99.5 && lng <= 119.5;
function pickerField() {
  return `<div class="field full"><label>Campaign location</label>
 <div class="pick-tools"><button type="button" class="btn btn-light btn-sm" data-action="pick-find">${icon("search", "icon-sm")} Find venue on map</button><button type="button" class="btn btn-light btn-sm" data-action="pick-gps">${icon("locate", "icon-sm")} Use my location</button></div>
 <div id="pick-map" class="pick-map" role="region" aria-label="Pick the campaign location"></div>
 <input type="hidden" name="lat"/><input type="hidden" name="lng"/>
 <p class="muted tiny pick-status" id="pick-status">Click the map or drag the pin to the venue entrance. If you skip this, we place it from the venue and city.</p></div>`;
}
function setPick(lat, lng, note) {
  const f = document.querySelector("#pick-map")?.closest("form");
  if (!f || !state.pickMap) return;
  lat = Math.round(lat * 1e6) / 1e6;
  lng = Math.round(lng * 1e6) / 1e6;
  const ok = inMalaysia(lat, lng);
  f.elements.lat.value = ok ? lat : "";
  f.elements.lng.value = ok ? lng : "";
  if (!state.pickPin) {
    const pin = L.divIcon({ className: "camp-pin", html: DROP_PIN, iconSize: [30, 38], iconAnchor: [15, 36] });
    state.pickPin = L.marker([lat, lng], { icon: pin, draggable: true, autoPan: true }).addTo(state.pickMap);
    state.pickPin.on("dragend", () => {
      const p = state.pickPin.getLatLng();
      setPick(p.lat, p.lng, "Pin moved");
    });
  } else state.pickPin.setLatLng([lat, lng]);
  const st = document.getElementById("pick-status");
  if (st)
    st.innerHTML = ok
      ? `${icon("pin", "icon-sm")} <b>${note || "Pinned"}</b><span data-no-i18n>· ${lat.toFixed(5)}, ${lng.toFixed(5)}</span><span>— drag the pin to fine-tune.</span>`
      : `<span class="danger-text">That point is outside Malaysia — please pick a place in Malaysia.</span>`;
}
function initPicker(start) {
  const box = document.getElementById("pick-map");
  if (!box) return;
  if (typeof L === "undefined") {
    box.innerHTML = '<div class="map-off">Map unavailable — the location will be placed from the venue and city.</div>';
    return;
  }
  if (state.pickMap) state.pickMap.remove();
  state.pickPin = null;
  const centre = start ? [start.lat, start.lng] : state.user.lat != null ? [state.user.lat, state.user.lng] : PICK_DEFAULT;
  state.pickMap = L.map(box, { scrollWheelZoom: false }).setView(centre, start ? 16 : 12);
  L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", { maxZoom: 19, attribution: "&copy; OpenStreetMap contributors" }).addTo(state.pickMap);
  state.pickMap.on("click", (ev) => setPick(ev.latlng.lat, ev.latlng.lng, "Pinned"));
  if (start) setPick(start.lat, start.lng, "Current pin");
  setTimeout(() => state.pickMap && state.pickMap.invalidateSize(), 60); // modal finished laying out
}
async function pickFind(button) {
  const f = button.closest("form");
  const venue = f.elements.venue?.value.trim() || "";
  const city = f.elements.city?.value.trim() || "";
  const q = [venue, city].filter(Boolean).join(", ");
  if (q.length < 3) throw new Error("Type the venue and city first, then press Find.");
  const url = `https://nominatim.openstreetmap.org/search?format=jsonv2&limit=1&countrycodes=my&q=${encodeURIComponent(q)}`;
  let hit = null;
  try {
    const r = await fetch(url, { headers: { Accept: "application/json" } });
    hit = (await r.json())[0];
  } catch (err) {
    throw new Error("Address search isn't reachable right now — click the map to place the pin instead.");
  }
  if (!hit) throw new Error(`Couldn't find "${q}" — click the map to place the pin instead.`);
  state.pickMap.setView([+hit.lat, +hit.lon], 16);
  setPick(+hit.lat, +hit.lon, "Found");
}
function pickGps() {
  return new Promise((resolve, reject) => {
    if (!navigator.geolocation) return reject(new Error("This browser can't share its location."));
    navigator.geolocation.getCurrentPosition(
      (p) => {
        state.pickMap.setView([p.coords.latitude, p.coords.longitude], 16);
        setPick(p.coords.latitude, p.coords.longitude, "Your location");
        resolve();
      },
      (err) => reject(new Error(err.code === 1 ? "Location permission was denied." : "Couldn't get your location.")),
      { enableHighAccuracy: true, timeout: 10000, maximumAge: 60000 },
    );
  });
}
function locationModal(id) {
  const c = state.campaigns.find((x) => x.id === Number(id));
  if (!c) return;
  modal(
    "Edit location",
    `${e(c.title)} · ${e(c.venue)}, ${e(c.city)}`,
    `<form id="location-form" class="form-grid"><input type="hidden" name="id" value="${c.id}"/><input type="hidden" name="venue" value="${e(c.venue)}"/><input type="hidden" name="city" value="${e(c.city)}"/>
 ${pickerField()}
 <div class="full modal-footer"><button type="button" class="btn btn-light" data-action="close-modal">Cancel</button><button type="submit" class="btn btn-primary">${icon("check", "icon-sm")} Save location</button></div></form>`,
  );
  initPicker(c.lat != null ? { lat: c.lat, lng: c.lng } : null);
}
function inventoryModal(id) {
  const i = state.inventory.find((x) => x.id === Number(id));
  if (!i) return;
  modal(
    `Update ${e(i.blood_type)} scenario`,
    "Modify simulated inventory levels only.",
    `<form id="inventory-form" class="form-grid"><input type="hidden" name="id" value="${i.id}"/><div class="field"><label>Units (demo)</label><input class="input" type="number" name="units" min="0" max="100000" required value="${i.units}"/></div><div class="field"><label>Alert threshold</label><input class="input" type="number" name="threshold" min="0" max="100000" required value="${i.threshold}"/></div><div class="full disclaimer">These changes are local to this demonstration and have no connection to hospital inventory.</div><div class="modal-footer full"><button type="button" class="btn btn-light" data-action="close-modal">Cancel</button><button type="submit" class="btn btn-primary">${icon("check", "icon-sm")} Save changes</button></div></form>`,
  );
}
async function loginAs(email, password) {
  await send("/api/login", { email, password });
  state.user = await api("/api/me");
  state.view = "dashboard";
  state.notifications = [];
  state.chat = [];
  render();
}
async function submitQuestion(q) {
  if (!q.trim()) return;
  state.chat.push({ type: "user", text: q });
  state.chat.push({ type: "assistant", text: "Thinking..." });
  document.getElementById("content").innerHTML = assistantPage();
  scrollChat();
  try {
    const response = await send("/api/assistant", { question: q });
    state.chat[state.chat.length - 1].text = response.answer;
  } catch (err) {
    state.chat[state.chat.length - 1].text = "Unable to reach the server. " + err.message;
  }
  if (state.view === "assistant") {
    document.getElementById("content").innerHTML = assistantPage();
    scrollChat();
  }
}
function scrollChat() {
  const c = document.getElementById("chat-screen");
  if (c) c.scrollTop = c.scrollHeight;
}
// One delegated handler retains functionality after each page render.
document.addEventListener("click", async (ev) => {
  const b = ev.target.closest("[data-view]");
  if (b && state.user) {
    ev.preventDefault();
    if (modalRoot.innerHTML) closeModal();
    goto(b.dataset.view);
    return;
  }
  const button = ev.target.closest("[data-action]");
  if (!button) return;
  const action = button.dataset.action;
  if (action === "overlay-close" && ev.target !== button) return;
  ev.preventDefault();
  try {
    if (action === "switch-auth") {
      state.authMode = state.authMode === "login" ? "signup" : "login";
      renderAuth();
    }
    if (action === "demo-login") await loginAs(`${button.dataset.role}@demo.com`, "Demo123!");
    if (action === "logout") {
      await send("/api/logout", {});
      state.user = null;
      state.authMode = "login";
      renderAuth();
    }
    if (action === "new-campaign") campaignModal();
    if (action === "edit-location") locationModal(button.dataset.id);
    if (action === "delete-account") deleteAccountModal();
    if (action === "pick-find" || action === "pick-gps") {
      button.disabled = true;
      try {
        await (action === "pick-find" ? pickFind(button) : pickGps());
      } catch (err) {
        toast(err.message, true);
      } finally {
        button.disabled = false;
      }
    }
    if (action === "book-modal") bookModal(button.dataset.id);
    if (action === "edit-inventory") inventoryModal(button.dataset.id);
    if (action === "close-modal" || action === "overlay-close") closeModal();
    if (action === "cancel-booking") {
      if (confirm("Cancel this donation appointment?")) {
        await send(`/api/bookings/${Number(button.dataset.id)}/cancel`, {});
        toast("Appointment cancelled");
        await render();
      }
    }
    if (action === "read-notifications") {
      await send("/api/notifications/read", {});
      toast("Notifications marked as read");
      await render();
    }
    if (action === "question") submitQuestion(button.dataset.question);
    if (action === "outlook-type") {
      state.outlookType = button.dataset.type;
      await page();
    }
    if (action === "mobilise") {
      state.prefillType = button.dataset.type;
      await goto("requests");
    }
    if (action === "open-request") {
      state.requestId = Number(button.dataset.id);
      await page();
      window.scrollTo({ top: 0, behavior: "smooth" });
    }
    if (action === "back-requests") {
      state.requestId = null;
      await page();
    }
    if (action === "send-alerts") {
      const r = await send(`/api/requests/${state.requestId}/alerts`, {});
      toast(`Alerts sent to ${r.sent} matched donors`);
      await page();
    }
    if (action === "simulate-replies") {
      const r = await send(`/api/requests/${state.requestId}/simulate`, {});
      toast(`${r.replied} demo donors replied`);
      await page();
    }
    if (action === "close-request" && confirm("Close this urgent request?")) {
      await send(`/api/requests/${Number(button.dataset.id)}/close`, {});
      toast("Request closed");
      await page();
    }
    if (action === "mark-donated") {
      await send(`/api/alerts/${Number(button.dataset.id)}/donated`, {});
      toast("Donation recorded · stock updated");
      await page();
    }
    if (action === "respond-alert") {
      await send(`/api/alerts/${Number(button.dataset.id)}/respond`, { response: button.dataset.response });
      toast(button.dataset.response === "yes" ? "Thank you! The blood bank has been told you're coming." : "Thanks for letting us know.");
      await render();
    }
    if (action === "booking-status") {
      await send(`/api/organizer/bookings/${Number(button.dataset.id)}/status`, { status: button.dataset.status });
      toast(button.dataset.status === "donated" ? "Donation recorded · stock updated" : "Marked as no-show");
      await page();
    }
    if (action === "rate") feedbackModal(button.dataset.id, button.dataset.title);
    if (action === "elig-reset") {
      state.eligResult = null;
      await page();
    }
    if (action === "suggest-campaign") {
      const s = state.suggestion;
      if (s)
        campaignModal({
          title: `${s.blood_type} Priority Blood Drive`,
          venue: `${s.city} Community Hall`,
          city: s.city,
          date: s.date,
          description: `Priority drive for ${s.blood_type}-compatible donors. Suggested by the HemoLink campaign planner.`,
        });
    }
    if (action === "locate") {
      button.disabled = true;
      button.innerHTML = "Finding you…";
      try {
        await locateMe();
        state.campSort = "near";
        toast("Location found — campaigns sorted by distance");
      } catch (err) {
        toast(err.message, true);
      }
      await page();
    }
    if (action === "camp-radius") {
      state.campRadius = Number(button.dataset.km);
      await page();
    }
    if (action === "map-focus") {
      const m = state.markers && state.markers[Number(button.dataset.id)];
      if (m && state.map) {
        document.getElementById("camp-map").scrollIntoView({ behavior: "smooth", block: "center" });
        state.map.flyTo(m.getLatLng(), 14, { duration: 0.6 });
        setTimeout(() => m.openPopup(), 650);
        document.querySelectorAll(".campaign-card.focus").forEach((x) => x.classList.remove("focus"));
        button.closest(".campaign-card")?.classList.add("focus");
      }
    }
    if (action === "more-menu") moreMenu();
    if (action === "llm-test") {
      const out = document.getElementById("llm-test-result");
      button.disabled = true;
      if (out) out.textContent = "Testing…";
      try {
        const t = await send("/api/admin/llm/test", {});
        if (out) {
          out.textContent = t.message;
          out.className = "small " + (t.ok ? "success-text" : "danger-text");
        }
      } finally {
        button.disabled = false;
      }
    }
    if (action === "logout" && modalRoot.innerHTML) closeModal();
    if (action === "user-role-filter") {
      state.userRole = button.dataset.role;
      await page();
    }
    if (action === "set-role") {
      const to = button.dataset.role;
      if (confirm(to === "organizer" ? `Approve ${button.dataset.name} as a drive organizer?` : `Change ${button.dataset.name} back to a donor account?`)) {
        await send(`/api/admin/users/${Number(button.dataset.id)}/role`, { role: to }, "PATCH");
        toast(to === "organizer" ? "Approved as drive organizer" : "Changed to donor");
        await page();
      }
    }
    if (action === "retry") page();
  } catch (err) {
    toast(err.message, true);
  }
});
document.addEventListener("submit", async (ev) => {
  const form = ev.target;
  const formId = form.getAttribute("id"); // not form.id: a hidden input named "id" shadows that property
  if (!formId) return;
  ev.preventDefault();
  const fd = new FormData(form);
  const o = Object.fromEntries(fd.entries());
  const submitBtn = form.querySelector('[type="submit"]');
  if (submitBtn) submitBtn.disabled = true;
  try {
    if (formId === "login-form") await loginAs(o.email, o.password);
    if (formId === "signup-form") {
      await send("/api/signup", { ...o, agree_privacy: o.agree_privacy === "on" });
      state.authMode = "login"; // after logging out later, show the sign-in screen
      state.user = await api("/api/me");
      state.view = "dashboard";
      toast("Your donor account has been created");
      await render();
    }
    if (formId === "booking-form") {
      await send("/api/bookings", { slot_id: Number(o.slot_id) });
      closeModal();
      toast("Booking confirmed! See My Appointments.");
      await goto("bookings");
    }
    if (formId === "new-campaign-form") {
      const { lat, lng, ...rest } = o;
      const r = await send("/api/campaigns", {
        ...rest,
        ...(lat && lng ? { lat: Number(lat), lng: Number(lng) } : {}),
        capacity: Number(o.capacity),
        times: o.times.split(",").map((x) => x.trim()),
      });
      closeModal();
      toast(r.nearby_notified ? `Campaign created · ${r.nearby_notified} nearby donor(s) notified` : "Campaign created successfully");
      await goto("campaigns");
    }
    if (formId === "delete-account-form") {
      await api("/api/me", { method: "DELETE", body: JSON.stringify({ password: o.password, confirm: o.confirm }) });
      closeModal();
      state.user = null;
      state.authMode = "login";
      toast("Your account and data have been deleted");
      renderAuth();
      return;
    }
    if (formId === "location-form") {
      if (!o.lat || !o.lng) throw new Error("Click the map to place the pin first.");
      await send(`/api/campaigns/${Number(o.id)}/location`, { lat: Number(o.lat), lng: Number(o.lng) }, "PATCH");
      closeModal();
      toast("Location saved — donors now see the new pin");
      await page();
    }
    if (formId === "inventory-form") {
      await send(
        `/api/inventory/${Number(o.id)}`,
        { units: Number(o.units), threshold: Number(o.threshold) },
        "PATCH",
      );
      closeModal();
      toast("Demo inventory updated");
      await page();
    }
    if (formId === "profile-form") {
      await send(
        "/api/me",
        { ...o, birth_year: o.birth_year ? Number(o.birth_year) : null, weight_kg: o.weight_kg ? Number(o.weight_kg) : null, sex: o.sex || null },
        "PATCH",
      );
      state.user = await api("/api/me");
      toast("Profile saved successfully");
      await render();
    }
    if (formId === "assistant-form") await submitQuestion(o.question);
    if (formId === "user-search-form") {
      state.userQ = o.q || "";
      await page();
    }
    if (formId === "request-form") {
      const r = await send("/api/requests", { ...o, units: Number(o.units) });
      toast("Request created — review the AI-ranked donors");
      state.requestId = r.id;
      await page();
    }
    if (formId === "eligibility-form") {
      const answers = {};
      for (const [k, v] of fd.entries()) answers[k] = v === "yes";
      state.eligResult = await send("/api/eligibility/check", { answers });
      await page();
      window.scrollTo({ top: 0, behavior: "smooth" });
    }
    if (formId === "feedback-form") {
      await send("/api/feedback", { appointment_id: Number(o.appointment_id), rating: Number(o.rating), comment: o.comment || "" });
      closeModal();
      toast("Thanks for your feedback!");
      await page();
    }
  } catch (err) {
    toast(err.message, true);
  } finally {
    if (submitBtn && submitBtn.isConnected) submitBtn.disabled = false;
  }
});
document.addEventListener("input", (ev) => {
  if (ev.target.id === "campaign-search") {
    state.search = ev.target.value.toLowerCase();
    let visible = 0;
    document.querySelectorAll("[data-filter-text]").forEach((card) => {
      const match = card.dataset.filterText.includes(state.search);
      card.classList.toggle("hide", !match);
      if (match) visible++;
    });
    const no = document.getElementById("campaign-empty");
    if (no) no.classList.toggle("hide", visible !== 0);
  }
});
document.addEventListener("change", async (ev) => {
  if (ev.target.id === "camp-sort") {
    state.campSort = ev.target.value;
    await page();
  }
  if (ev.target.id === "forecast-region" || ev.target.id === "forecast-blood") {
    state.region = document.getElementById("forecast-region").value;
    state.blood = document.getElementById("forecast-blood").value;
    await page();
  }
});
// Donors: check for new urgent alerts every 15 s (production: replace with web push)
let lastAlerts = null;
setInterval(async () => {
  if (!state.user || state.user.role !== "donor" || document.hidden) return;
  try {
    const o = await api("/api/overview");
    if (lastAlerts !== null && o.my_open_alerts > lastAlerts) {
      toast("New urgent request — a blood bank needs your help");
      state.notifications = await api("/api/notifications");
      if (state.view === "dashboard" || state.view === "notifications") await render();
      else shell();
    }
    lastAlerts = o.my_open_alerts;
  } catch (err) {
    /* ignore — try again next tick */
  }
}, 15000);
(async () => {
  try {
    state.user = await api("/api/me");
    await render();
  } catch (err) {
    state.user = null;
    renderAuth();
  }
})();
