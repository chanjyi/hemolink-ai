/* HemoCare — personal blood health hub: Medical Knowledge + Medication History + Donation Preparation. */
const hc = { view: "home", jump: false, editing: null, showForm: false };
const HC_TABS = [["home", "Overview", "dashboard"], ["knowledge", "Medical Knowledge", "book"], ["meds", "Medication History", "pill"], ["prep", "Donation Preparation", "shield"]];
const HC_STATE = { hold: ["tag-amber", "Waiting period"], tell: ["tag-gray", "Tell the staff"], ok: ["tag-green", "No effect"] };

async function hemocarePage() {
  const v = hc.view;
  const tab = v.startsWith("article:") ? "knowledge" : v;
  const tabs = `<div class="hc-tabs" role="tablist">${HC_TABS.map(([k, label, ic]) => `<button class="hc-tab ${tab === k ? "on" : ""}" data-hc="tab" data-tab="${k}" role="tab">${icon(ic, "icon-sm")}<span>${label}</span></button>`).join("")}</div>`;
  let body;
  if (v.startsWith("article:")) body = await hcArticle(v.slice(8));
  else if (v === "knowledge") body = await hcKnowledge();
  else if (v === "meds") body = await hcMeds();
  else if (v === "prep") body = await hcPrep();
  else body = await hcHome();
  return heading("HemoCare", "Your personal blood health hub — understand blood conditions, keep your medicine list, and get ready for your next donation.", `<span class="tag tag-gray">${icon("book", "icon-sm")} Educational</span>`) + tabs + body;
}

const hcCard = (a) =>
  `<button class="hc-topic" data-hc-article="${e(a.id)}"><span class="hc-topic-icon">${icon(a.icon || "book", "icon-sm")}</span><span><b>${e(a.title)}</b><small>${e(a.short)}</small></span>${icon("chevron", "icon-sm hc-chev")}</button>`;

async function hcHome() {
  const o = await api("/api/hemocare/overview");
  const ins = o.insights;
  const hold = o.meds.hold;
  const tile = (tab, ic, title, text, status) =>
    `<button class="hc-feature" data-hc="tab" data-tab="${tab}"><span class="hc-feature-icon">${icon(ic)}</span><b>${title}</b><p>${text}</p>${status ? `<span class="hc-feature-status">${status}</span>` : ""}</button>`;
  const insightPanel = ins
    ? ins.findings.length
      ? `<div class="surface panel"><div class="panel-title"><h3>${icon("flask", "icon-sm")} HemoScan insights</h3><span class="tag tag-gray">Report ${dateLabel(ins.report_date)}</span></div>
 <p class="small muted" style="margin-bottom:12px">Your latest confirmed blood test flagged: ${ins.findings.map((f) => `<b>${e(f.title)}</b>`).join(" · ")}. These guides explain what that can mean.</p>
 <div class="hc-topic-grid">${ins.articles.map((a) => hcCard({ ...a, icon: "book" })).join("") || '<p class="muted small">No matching guides.</p>'}</div></div>`
      : `<div class="source-strip">${icon("check")} Your latest HemoScan report (${dateLabel(ins.report_date)}) had no patterns flagged.</div>`
    : `<div class="source-strip">${icon("flask")} Upload a blood test in HemoScan AI and HemoCare will suggest guides that match your results. <button class="link-btn" data-view="hemoscan">Open HemoScan</button></div>`;
  return `<div class="stack">
 <section class="surface panel hc-hub"><div class="panel-title"><h3>${icon("heart", "icon-sm")} Your blood health hub</h3></div>
 <div class="hc-feature-grid">
 ${tile("knowledge", "book", "Medical Knowledge", "Learn about blood conditions, symptoms, testing and what doctors may consider.", `${o.articles.length} guides`)}
 ${tile("meds", "pill", "Medication History", "Keep a private record of current and past medicines.", hold ? `<span class="danger-text">Waiting period ${hold.until ? "until " + dateLabel(hold.until) : "while taking"}</span>` : `${o.meds.current} current · ${o.meds.total} total`)}
 ${tile("knowledge", "flask", "HemoScan Insights", "Guides related to your confirmed blood test results.", ins ? `${ins.findings.length} pattern${ins.findings.length === 1 ? "" : "s"} · ${dateLabel(ins.report_date)}` : "No report yet")}
 ${tile("prep", "shield", "Donation Preparation", "Screening checklist and a summary to show the staff.", "Printable summary")}
 </div></section>
 ${insightPanel}
 <div class="surface panel"><div class="panel-title"><h3>Explore blood health topics</h3><span class="muted tiny">Educational content</span></div><div class="hc-topic-grid">${o.articles.map(hcCard).join("")}</div></div>
 <div class="disclaimer">${icon("shield", "icon-sm")} ${e(o.disclaimer)}</div></div>`;
}

async function hcKnowledge() {
  const o = await api("/api/hemocare/overview");
  const groups = [...new Set(o.articles.map((a) => a.group))];
  return `<div class="stack">${groups
    .map((g) => `<div class="surface panel"><div class="panel-title"><h3>${e(g)}</h3></div><div class="hc-guide-grid">${o.articles
      .filter((a) => a.group === g)
      .map((a) => `<button class="hc-guide" data-hc-article="${e(a.id)}"><span class="hc-topic-icon">${icon(a.icon, "icon-sm")}</span><b>${e(a.title)}</b><p>${e(a.summary)}</p><span class="link-btn">Read guide ${icon("arrow", "icon-sm")}</span></button>`)
      .join("")}</div></div>`)
    .join("")}<div class="disclaimer">${icon("shield", "icon-sm")} ${e(o.review)}. ${e(o.disclaimer)}</div></div>`;
}

async function hcArticle(id) {
  const a = await api(`/api/hemocare/articles/${encodeURIComponent(id)}`);
  return `<button class="link-btn" data-hc="tab" data-tab="knowledge" style="margin-bottom:12px">← All guides</button>
 <div class="stack hc-article">${state.lang === "ms" ? `<div class="i18n-note">${icon("info", "icon-sm")}<span>Panduan perubatan terperinci ini masih dalam Bahasa Inggeris supaya istilah klinikal kekal tepat.</span></div>` : ""}<section class="surface panel hc-article-head"><div class="hc-topic-icon big">${icon(a.icon, "icon-xl")}</div><div><div class="muted tiny semibold">${e(a.group.toUpperCase())}</div><h2>${e(a.title)}</h2><p>${e(a.summary)}</p></div></section>
 ${a.my_findings.length ? `<div class="source-strip demo">${icon("flask")} Your HemoScan report of ${dateLabel(a.my_report.date)} flagged: ${a.my_findings.map((f) => `<b>${e(f.title)}</b>`).join(" · ")}. <button class="link-btn" data-hs-open="${a.my_report.id}">Open report</button></div>` : ""}
 <div class="hc-sections">${a.sections.map((s) => `<div class="surface panel"><h3>${e(s.heading)}</h3><ul>${s.points.map((p) => `<li>${e(p)}</li>`).join("")}</ul></div>`).join("")}</div>
 <div class="hc-callouts"><div class="hc-callout donate"><h3>${icon("droplet", "icon-sm")} What it means for donating</h3><p>${e(a.donation)}</p></div>
 <div class="hc-callout urgent"><h3>${icon("alert", "icon-sm")} Get urgent care if you have</h3><ul>${a.urgent.map((x) => `<li>${e(x)}</li>`).join("")}</ul></div></div>
 ${a.related.length ? `<div class="filters"><span class="muted small">Related:</span>${a.related.map((r) => `<button class="hs-chip" data-hc-article="${e(r.id)}">${e(r.title)}</button>`).join("")}</div>` : ""}
 <div class="surface panel"><h3 style="margin-bottom:8px">References</h3><ul class="hc-refs">${a.refs.map((r) => `<li>${e(r)}</li>`).join("")}</ul><p class="muted tiny" style="margin-top:10px">${e(a.review)}</p></div>
 <div class="disclaimer">${icon("shield", "icon-sm")} ${e(a.disclaimer)}</div></div>`;
}

function hcMedForm(m, categories) {
  const v = (k) => e(m?.[k] ?? "");
  return `<form data-hc-form="${m ? "edit" : "add"}" class="form-grid hc-med-form">${m ? `<input type="hidden" name="id" value="${m.id}"/>` : ""}
 <div class="field"><label>Medicine name</label><input class="input" name="name" required minlength="2" maxlength="80" value="${v("name")}" placeholder="e.g. Amoxicillin, Panadol, Ferrous fumarate"/></div>
 <div class="field"><label>Type</label><select class="select" name="category"><option value="auto">Detect from the name</option>${categories.map((c) => `<option value="${c.key}" ${m && m.category === c.key ? "selected" : ""}>${e(c.label)}</option>`).join("")}</select></div>
 <div class="field"><label>What it's for (optional)</label><input class="input" name="reason" maxlength="120" value="${v("reason")}" placeholder="e.g. throat infection"/></div>
 <div class="field"><label>As written on the label (optional)</label><input class="input" name="dose_note" maxlength="80" value="${v("dose_note")}" placeholder="e.g. 1 tablet twice a day"/></div>
 <div class="field"><label>Started</label><input class="input" type="date" name="start_date" max="${todayISO()}" value="${v("start_date")}"/></div>
 <div class="field"><label>Last dose <span class="muted tiny">(leave empty if still taking)</span></label><input class="input" type="date" name="end_date" value="${v("end_date")}"/></div>
 <div class="field full"><label>Notes (optional)</label><input class="input" name="notes" maxlength="300" value="${v("notes")}"/></div>
 <div class="full filters"><button class="btn btn-primary" type="submit">${icon("check", "icon-sm")} ${m ? "Save changes" : "Add medicine"}</button>${m ? '<button type="button" class="btn btn-light" data-action="close-modal">Cancel</button>' : '<button type="button" class="btn btn-light" data-hc="toggle-form">Cancel</button>'}</div></form>`;
}

async function hcMeds() {
  const d = await api("/api/hemocare/meds");
  hc.categories = d.categories;
  hc.meds = d.items;
  const card = (m) => {
    const s = m.status;
    const [cls, label] = HC_STATE[s.state];
    const dates = `${m.start_date ? "Started " + dateLabel(m.start_date) : "Start date not set"} · ${m.end_date ? "last dose " + dateLabel(m.end_date) : "still taking"}`;
    return `<div class="hc-med ${s.state}"><div class="hc-med-icon">${icon("pill", "icon-sm")}</div><div class="hc-med-body"><div class="hc-med-top"><b>${e(m.name)}</b><span class="tag ${cls}">${label}</span></div>
 <div class="muted tiny">${e(s.category_label)}${m.reason ? " · for " + e(m.reason) : ""}${m.dose_note ? " · " + e(m.dose_note) : ""}</div>
 <div class="muted tiny" style="margin-top:3px">${dates}</div><div class="hc-med-msg">${e(s.message)}</div></div>
 <div class="hc-med-actions">${s.ongoing && !m.end_date ? `<button class="btn btn-light btn-sm" data-hc="stop" data-id="${m.id}">Stopped today</button>` : ""}<button class="btn btn-light btn-sm" data-hc="edit" data-id="${m.id}">Edit</button><button class="btn btn-light btn-sm" data-hc="delete-med" data-id="${m.id}" title="Delete">${icon("trash", "icon-sm")}</button></div></div>`;
  };
  const current = d.items.filter((m) => m.status.ongoing);
  const past = d.items.filter((m) => !m.status.ongoing);
  return `<div class="stack">
 ${d.hold ? `<section class="shortage-banner amber slim"><div><div class="banner-tags"><span class="tag tag-amber">${icon("clock", "icon-sm")} Medicine waiting period</span></div><h2>${d.hold.until ? "You can donate again from " + dateLabel(d.hold.until) : "Not while you're taking " + e(d.hold.medicines.join(", "))}</h2><p>${e(d.hold.reason)} Urgent requests won't be sent to you until then.</p></div><button class="btn btn-light" data-view="eligibility">Eligibility check</button></section>` : ""}
 <div class="surface panel"><div class="panel-title"><h3>Add a medicine</h3>${hc.showForm ? "" : `<button class="btn btn-primary btn-sm" data-hc="toggle-form">${icon("plus", "icon-sm")} Add medicine</button>`}</div>
 ${hc.showForm ? hcMedForm(null, d.categories) : `<p class="muted small">Record what you take — prescriptions, supplements and over-the-counter medicines. HemoCare tells you whether each one affects donating.</p>`}</div>
 <div class="surface panel"><div class="panel-title"><h3>Taking now</h3><span class="tag tag-gray">${current.length}</span></div>${current.length ? `<div class="hc-med-list">${current.map(card).join("")}</div>` : '<p class="muted small">No current medicines recorded.</p>'}</div>
 <div class="surface panel"><div class="panel-title"><h3>Medicine history</h3><span class="tag tag-gray">${past.length}</span></div>${past.length ? `<div class="hc-med-list">${past.map(card).join("")}</div>` : '<p class="muted small">Medicines you have stopped appear here.</p>'}</div>
 <div class="source-strip demo">${icon("info")} ${e(d.note)} Never stop a prescribed medicine just to donate.</div>
 <div class="disclaimer">${icon("shield", "icon-sm")} Private to you — organizers and admins can't see this list. ${e(d.disclaimer)}</div></div>`;
}

async function hcPrep() {
  const d = await api("/api/hemocare/prep");
  const el = d.eligibility;
  const ok = el && (el.verdict === "eligible" || el.verdict === "eligible_after_meal");
  return `<div class="stack">
 <div class="hc-prep-grid">
 <div class="surface panel"><div class="muted tiny semibold">ELIGIBILITY (HEMOLINK CHECK)</div><h3 style="margin:6px 0">${el ? e(el.label) : "Complete your profile first"}</h3>
 <p class="small muted">${el ? (el.verdict === "deferred" && el.eligible_from ? `From ${dateLabel(el.eligible_from)}. ` : "") + e(el.reasons.join(" ")) : "Add blood type, birth year and weight in My Profile."}</p>
 <div class="filters" style="margin-top:10px"><button class="btn btn-light btn-sm" data-view="eligibility">Today's questions</button>${ok ? `<button class="btn btn-primary btn-sm" data-view="campaigns">Book a slot</button>` : ""}</div></div>
 <div class="surface panel"><div class="muted tiny semibold">LATEST BLOOD TEST</div><h3 style="margin:6px 0">${d.hemoscan ? `Hb ${d.hemoscan.hb} g/dL` : "No HemoScan report"}</h3>
 <p class="small muted">${d.hemoscan ? e(d.hemoscan.message) : "Upload a report in HemoScan AI to include it."}</p></div></div>
 <div class="surface panel"><div class="panel-title"><h3>Medicines to mention</h3><button class="btn btn-light btn-sm" data-hc="tab" data-tab="meds">Edit list</button></div>
 ${d.medicines.length ? `<div class="table-wrap"><table class="data-table"><thead><tr><th>Medicine</th><th>Last dose</th><th>What it means</th></tr></thead><tbody>${d.medicines.map((m) => `<tr><td><b>${e(m.name)}</b><div class="muted tiny">${e(m.status.category_label)}</div></td><td class="small">${m.end_date ? dateLabel(m.end_date) : "Still taking"}</td><td><span class="tag ${HC_STATE[m.status.state][0]}">${HC_STATE[m.status.state][1]}</span><div class="muted tiny" style="margin-top:4px">${e(m.status.message)}</div></td></tr>`).join("")}</tbody></table></div>` : '<p class="muted small">No medicines in the last 90 days.</p>'}</div>
 <div class="surface panel"><div class="panel-title"><h3>Before you donate</h3></div><ul class="hc-check">${d.checklist.map((x) => `<li>${icon("check", "icon-sm")} ${e(x)}</li>`).join("")}</ul>
 <a class="btn btn-primary" href="/api/hemocare/prep/summary" target="_blank" rel="noopener" style="margin-top:14px">${icon("file", "icon-sm")} Open printable screening summary</a></div>
 <div class="disclaimer">${icon("shield", "icon-sm")} ${e(d.disclaimer)}</div></div>`;
}

/* ------------------------------------------------------------------ events */

async function hcGo(view) {
  hc.view = view;
  hc.showForm = false;
  await page();
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function hcBody(form) {
  const o = Object.fromEntries(new FormData(form).entries());
  return { name: o.name, category: o.category || "auto", reason: o.reason || "", dose_note: o.dose_note || "", start_date: o.start_date || null, end_date: o.end_date || null, notes: o.notes || "" };
}

document.addEventListener("click", async (ev) => {
  const art = ev.target.closest("[data-hc-article]");
  const hsOpen = ev.target.closest("[data-hs-open]");
  const b = ev.target.closest("[data-hc]");
  if (!art && !b && !hsOpen) return;
  ev.preventDefault();
  try {
    if (hsOpen) {
      hs.id = Number(hsOpen.dataset.hsOpen);
      hs.keep = true;
      return await goto("hemoscan");
    }
    if (art) {
      if (state.view !== "hemocare") {
        hc.jump = true;
        hc.view = "article:" + art.dataset.hcArticle;
        return await goto("hemocare");
      }
      return await hcGo("article:" + art.dataset.hcArticle);
    }
    const act = b.dataset.hc;
    if (act === "tab") await hcGo(b.dataset.tab);
    if (act === "toggle-form") {
      hc.showForm = !hc.showForm;
      await page();
    }
    if (act === "edit") {
      const m = (hc.meds || []).find((x) => x.id === Number(b.dataset.id));
      if (m) modal("Edit medicine", "Changes update your donation status straight away.", hcMedForm(m, hc.categories));
    }
    if (act === "stop") {
      await send(`/api/hemocare/meds/${Number(b.dataset.id)}/stop`, { end_date: todayISO() });
      toast("Marked as stopped today");
      await page();
    }
    if (act === "delete-med" && confirm("Delete this medicine from your list?")) {
      await api(`/api/hemocare/meds/${Number(b.dataset.id)}`, { method: "DELETE" });
      toast("Medicine deleted");
      await page();
    }
  } catch (err) {
    toast(err.message, true);
  }
});

document.addEventListener("submit", async (ev) => {
  const form = ev.target;
  const kind = form.dataset.hcForm;
  if (!kind) return;
  ev.preventDefault();
  const btn = form.querySelector('[type="submit"]');
  if (btn) btn.disabled = true;
  try {
    if (kind === "add") {
      const r = await send("/api/hemocare/meds", hcBody(form));
      hc.showForm = false;
      toast(r.status.state === "hold" ? `Added — ${r.status.message}` : "Medicine added");
      await page();
    }
    if (kind === "edit") {
      const id = Number(new FormData(form).get("id"));
      await send(`/api/hemocare/meds/${id}`, hcBody(form), "PUT");
      closeModal();
      toast("Medicine updated");
      await page();
    }
  } catch (err) {
    toast(err.message, true);
  } finally {
    if (btn && btn.isConnected) btn.disabled = false;
  }
});
