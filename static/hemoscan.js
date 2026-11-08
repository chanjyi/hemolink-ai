/* HemoScan AI — private FBC report reader (upload → check values → rules analysis → AI explanation → history). */
const hs = { id: null, catalog: null, metric: "hgb", chat: [], showPdf: false, extra: [], mode: "pdf", photo: null, stream: null };
iconPaths.file = '<path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"/><path d="M14 3v5h5M9 13h6M9 17h6"/>';
iconPaths.download = '<path d="M12 3v12m-5-5 5 5 5-5M4 21h16"/>';
iconPaths.camera = '<path d="M4 8h3l2-3h6l2 3h3a1 1 0 0 1 1 1v10a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V9a1 1 0 0 1 1-1z"/><circle cx="12" cy="13.5" r="3.5"/>';
iconPaths.edit = '<path d="M4 20h4L19 9l-4-4L4 16v4z"/><path d="m13.5 6.5 4 4"/>';
iconPaths.image = '<rect x="3" y="4" width="18" height="16" rx="2"/><circle cx="9" cy="10" r="2"/><path d="m21 16-5-5-9 9"/>';
iconPaths.trash = '<path d="M3 6h18M8 6V4h8v2M6 6l1 15h10l1-15"/>';

const HS_CORE = ["hgb", "rbc", "hct", "mcv", "mch", "mchc", "rdw", "wbc", "plt"];
const SEV_TAG = { urgent: "tag-red", attention: "tag-amber", review: "tag-amber", watch: "tag-gray", info: "tag-gray" };
const FLAG_TAG = { low: ["tag-amber", "Low"], high: ["tag-amber", "High"], normal: ["tag-green", "In range"] };
const fmt = (v) => (v === null || v === undefined || v === "" ? "" : Number(Number(v).toFixed(3)).toString());

async function hsCatalog() {
  if (!hs.catalog) hs.catalog = await api("/api/hemoscan/catalog");
  return hs.catalog;
}
const bioOf = (key) => hs.catalog.biomarkers.find((b) => b.key === key);

async function hemoscanPage() {
  await hsCatalog();
  if (hs.id) {
    const d = await api(`/api/hemoscan/reports/${hs.id}`);
    return d.report.status === "confirmed" ? hsAnalysis(d) : hsReview(d);
  }
  return hsHome();
}

/* ------------------------------------------------------------------ home: upload + history + trend */

async function hsHome() {
  const [list, hist] = await Promise.all([api("/api/hemoscan/reports"), api("/api/hemoscan/history")]);
  const c = hs.catalog;
  const latest = list.find((r) => r.status === "confirmed");
  const drafts = list.filter((r) => r.status === "draft").length;
  const consent = `<label class="hs-consent"><input type="checkbox" name="consent" value="true" required/><span>I understand HemoScan explains number patterns and possible associations — <b>it is not a diagnosis</b> and does not replace a doctor.</span></label>`;
  const mode = (m, ic, title, sub, attrs) =>
    `<button type="button" class="hs-mode ${hs.mode === m ? "on" : ""}" ${attrs}><span class="hs-mode-icon">${icon(ic)}</span><span><b>${title}</b><small>${sub}</small></span></button>`;
  const pdfForm = `<form data-hs-form="upload" class="hs-drop"><label class="hs-file"><input type="file" name="file" accept="application/pdf,.pdf" required/>
 <span class="hs-file-icon">${icon("file", "icon-xl")}</span><b>Choose your FBC / CBC PDF</b><span class="muted small">From the lab or clinic portal · up to ${c.max_mb} MB</span><span class="hs-file-name muted tiny"></span></label>
 ${consent}<div class="filters"><button class="btn btn-primary" type="submit">${icon("spark", "icon-sm")} Read my report</button></div></form>`;
  const photoForm = `<form data-hs-form="photo" class="hs-drop"><div class="hs-photo-zone ${hs.photo ? "has-photo" : ""}">
 ${hs.photo ? `<img id="hs-photo-preview" src="${hs.photo.url}" alt="Photo of your report"/>` : `<span class="hs-file-icon">${icon("camera", "icon-xl")}</span><b>Photograph your paper report</b><span class="muted small">Flat page · good light · fill the frame · no glare</span>`}
 <div class="filters hs-photo-actions"><button type="button" class="btn btn-light btn-sm" data-hs="camera">${icon("camera", "icon-sm")} ${hs.photo ? "Retake" : "Open camera"}</button>
 <label class="btn btn-light btn-sm hs-pick">${icon("image", "icon-sm")} ${hs.photo ? "Choose another" : "Choose a photo"}<input type="file" accept="image/*" capture="environment" id="hs-photo-input"/></label></div></div>
 <p class="muted tiny hs-ocr-note">${icon("info", "icon-sm")} ${c.ocr ? `Values are read automatically (${e(c.ocr)}) and every one is marked “Check” for you to confirm.` : "No photo reader is installed, so you'll type the values in beside the photo — nothing is guessed."}</p>
 ${consent}<div class="filters"><button class="btn btn-primary" type="submit" ${hs.photo ? "" : "disabled"}>${icon("spark", "icon-sm")} Read my photo</button></div></form>`;
  const upload = `<div class="surface panel hs-upload"><div class="panel-title"><h3>Add a blood test report</h3>${aiTag(hs.mode === "photo" ? "Photo reader" : "PDF reader")}</div>
 <div class="hs-modes">${mode("pdf", "file", "Upload PDF", "From the lab portal", 'data-hs="mode" data-mode="pdf"')}${mode("photo", "camera", "Take a photo", "Paper report", 'data-hs="mode" data-mode="photo"')}${mode("manual", "edit", "Type it in", "Enter values yourself", 'data-hs="manual"')}</div>
 ${hs.mode === "photo" ? photoForm : pdfForm}
 <div class="hs-samples"><div class="hs-samples-title">No report handy? Try a fictional sample</div><div class="hs-sample-grid">${c.samples
   .map((x) => `<a class="hs-sample" href="/api/hemoscan/samples/${e(x.name)}" download><span class="hs-sample-icon">${icon(x.kind === "photo" ? "image" : "file", "icon-sm")}</span><span class="hs-sample-text"><b>${e(x.label)}</b><small>${e(x.sub)}</small></span>${icon("download", "icon-sm hs-sample-dl")}</a>`)
   .join("")}</div></div></div>`;

  const keys = hist.biomarkers.map((b) => b.key);
  if (!keys.includes(hs.metric) && keys.length) hs.metric = keys[0];
  const trend = keys.length
    ? `<div class="surface panel"><div class="panel-title"><h3>Your results over time</h3><a class="btn btn-light btn-sm" href="/api/hemoscan/export.csv" download>${icon("download", "icon-sm")} Export CSV</a></div>
 <div class="hs-chips">${hist.biomarkers.filter((b) => HS_CORE.includes(b.key)).map((b) => `<button class="hs-chip ${b.key === hs.metric ? "on" : ""}" data-hs="metric" data-key="${b.key}">${e(b.name.replace(/\s*\(.*\)/, ""))}</button>`).join("")}</div>
 ${hsTrendChart(hist.series[hs.metric] || [], bioOf(hs.metric))}
 <div class="legend hs-legend"><span class="band">Lab reference range</span><span class="pt-normal">In range</span><span class="pt-out">Out of range</span></div></div>`
    : "";

  const rows = list.length
    ? `<div class="table-wrap"><table class="data-table"><thead><tr><th>Report date</th><th>Source</th><th>Result</th><th>Main pattern</th><th></th></tr></thead><tbody>${list
        .map((r) => {
          const res = r.status === "draft"
            ? '<span class="tag tag-amber">Needs your check</span>'
            : r.urgent
              ? '<span class="tag tag-red">Urgent values</span>'
              : r.counts.low + r.counts.high
                ? `<span class="tag tag-amber">${r.counts.low + r.counts.high} out of range</span>`
                : '<span class="tag tag-green">All in range</span>';
          return `<tr><td><b>${r.report_date ? dateLabel(r.report_date) : "—"}</b><div class="muted tiny" style="margin-top:4px">${e(r.lab_name || "Lab not stated")}</div></td><td class="small">${r.photo ? icon("camera", "icon-sm") + " Photo" : r.source === "pdf" ? icon("file", "icon-sm") + " PDF" : "Typed in"}</td><td>${res}</td><td class="small">${e(r.top_finding || (r.status === "draft" ? "—" : "No pattern flagged"))}</td><td><button class="btn btn-outline btn-sm" data-hs="open" data-id="${r.id}">${r.status === "draft" ? "Check values" : "Open"}</button></td></tr>`;
        })
        .join("")}</tbody></table></div>`
    : empty("flask", "No reports yet", "Upload your first full blood count report to start your private history.");

  return (
    heading("HemoScan AI", "Read your full blood count report, see what is out of range, the patterns it may point to, and how it changes over time.", aiTag("Rules engine + AI")) +
    `<div class="stack">${latest && latest.urgent ? `<section class="shortage-banner red"><div><h2>Your latest report has values that may need prompt attention</h2><p>Please contact your doctor or clinic today. If you feel unwell, seek urgent care.</p></div><button class="btn btn-primary" data-hs="open" data-id="${latest.id}">Open report</button></section>` : ""}
 ${drafts ? `<div class="source-strip demo">${icon("info")} ${drafts} report${drafts > 1 ? "s are" : " is"} waiting for you to check the extracted values.</div>` : ""}
 <div class="hs-home-grid">${upload}<div class="surface panel hs-how"><div class="panel-title"><h3>How it works</h3></div><ol>
 <li><b>Read</b> — we pull each test, unit and lab range from your PDF, or from a photo with OCR. Nothing is used until you check it.</li>
 <li><b>Check</b> — you compare every value with the original and fix anything wrong. Low-confidence readings are highlighted.</li>
 <li><b>Analyse</b> — transparent rules find out-of-range values and known combinations, with the reason and reference shown.</li>
 <li><b>Explain</b> — AI (or a built-in template) explains the findings in plain language. Possible associations, never a diagnosis.</li></ol>
 <div class="muted tiny">${icon("shield", "icon-sm")} Private to you — organizers and admins can't see your reports. Delete any report at any time.</div></div></div>
 ${trend}<div class="surface panel"><div class="panel-title"><h3>Report history</h3><span class="tag tag-gray">${list.length} report${list.length === 1 ? "" : "s"}</span></div>${rows}</div>
 <div class="disclaimer">${icon("shield", "icon-sm")} ${e(c.disclaimer)}</div></div>`
  );
}

function hsTrendChart(points, b) {
  if (!points.length || !b) return `<p class="muted small">No values yet.</p>`;
  const W = 870, H = 250, L = 52, R = 22, T = 18, B = 36;
  const last = points[points.length - 1];
  const lo = last.ref_low, hi = last.ref_high;
  const vals = points.map((p) => p.value).concat([lo, hi].filter((x) => x !== null));
  let min = Math.min(...vals), max = Math.max(...vals);
  const pad = (max - min || max || 1) * 0.18;
  min = Math.max(0, min - pad);
  max = max + pad;
  const t0 = new Date(points[0].date).getTime(), t1 = new Date(last.date).getTime();
  const x = (d) => (points.length === 1 ? (L + W - R) / 2 : L + ((W - L - R) * (new Date(d).getTime() - t0)) / (t1 - t0));
  const y = (v) => T + (H - T - B) * (1 - (v - min) / (max - min));
  const grid = Array.from({ length: 5 }, (_, i) => {
    const v = max - ((max - min) * i) / 4;
    return `<line class="chart-grid" x1="${L}" y1="${y(v)}" x2="${W - R}" y2="${y(v)}"/><text class="chart-axis" x="${L - 10}" y="${y(v) + 4}" text-anchor="end">${fmt(v.toPrecision(3))}</text>`;
  }).join("");
  const band = lo !== null && hi !== null ? `<rect class="hs-band" x="${L}" y="${y(hi)}" width="${W - L - R}" height="${y(lo) - y(hi)}"/>` : "";
  const line = points.map((p) => `${x(p.date).toFixed(1)},${y(p.value).toFixed(1)}`).join(" ");
  // only label points that have room (newest wins when reports are close together)
  const show = new Set();
  let lastX = Infinity;
  for (let i = points.length - 1; i >= 0; i--) {
    const px = x(points[i].date);
    if (lastX - px >= 64) { show.add(i); lastX = px; }
  }
  return `<svg class="chart" viewBox="0 0 ${W} ${H}" role="img" aria-label="${e(b.name)} over time">${band}${grid}
 <polyline class="chart-stock" points="${line}"/>${points
   .map((p, i) => `<g><circle cx="${x(p.date)}" cy="${y(p.value)}" r="5.5" class="${p.flag === "normal" ? "hs-pt-ok" : "hs-pt-out"}"/>${show.has(i) ? `<text class="chart-axis hs-val" x="${x(p.date)}" y="${y(p.value) - 11}" text-anchor="middle">${fmt(p.value)}</text>
 <text class="chart-axis" x="${x(p.date)}" y="${H - 10}" text-anchor="middle">${new Date(p.date + "T12:00:00").toLocaleDateString("en-MY", { month: "short", year: "numeric" })}</text>` : ""}<title>${e(b.name)} ${fmt(p.value)} ${e(b.unit)} on ${p.date}</title></g>`)
   .join("")}<text class="chart-axis" x="${L}" y="${T - 4}">${e(b.unit)}</text></svg>`;
}

/* ------------------------------------------------------------------ review: original beside editable values */

function hsRowsFor(d) {
  const ex = d.extraction;
  const items = ex.items || [];
  const have = new Set(items.map((i) => i.key));
  const rows = items.map((i) => ({ ...i, found: true }));
  for (const k of [...HS_CORE, ...hs.extra]) if (!have.has(k)) { rows.push({ key: k, found: false }); have.add(k); }
  return rows.sort((a, b) => hs.catalog.biomarkers.findIndex((x) => x.key === a.key) - hs.catalog.biomarkers.findIndex((x) => x.key === b.key));
}

function hsPages(d, highlight) {
  const ex = d.extraction;
  if (!d.report.has_file || !ex.pages || !ex.pages.length) return "";
  return ex.pages
    .map((pg, n) => {
      const boxes = (ex.items || [])
        .filter((i) => i.page === n && i.bbox)
        .map((i) => {
          const [x0, y0, x1, y1] = i.bbox;
          const cls = highlight ? highlight(i) : `conf-${i.confidence_level}`;
          if (!cls) return "";
          return `<span class="hs-box ${cls}" data-box="${i.key}" style="left:${(x0 / pg.width) * 100 - 0.6}%;top:${(y0 / pg.height) * 100 - 0.35}%;width:${((x1 - x0) / pg.width) * 100 + 1.2}%;height:${((y1 - y0) / pg.height) * 100 + 0.7}%"></span>`;
        })
        .join("");
      return `<div class="hs-page"><img src="/api/hemoscan/reports/${d.report.id}/page/${n}" alt="Page ${n + 1} of the original report" loading="lazy"/>${boxes}</div>`;
    })
    .join("");
}

function hsReview(d) {
  const ex = d.extraction, r = d.report;
  const rows = hsRowsFor(d);
  const unitOpts = (b, cur) => {
    const opts = [...b.units];
    if (cur && !opts.includes(cur)) opts.push(cur);
    return `<option value="">— unit —</option>` + opts.map((u) => `<option ${u === cur ? "selected" : ""}>${e(u)}</option>`).join("");
  };
  const body = rows
    .map((i) => {
      const b = bioOf(i.key);
      const lvl = i.found ? i.confidence_level : "missing";
      const noUnit = i.found && !i.unit;
      const conf = i.found
        ? `<span class="hs-conf ${lvl}">${lvl === "high" ? "High" : lvl === "medium" ? "Check" : "Low"} confidence</span>`
        : `<span class="hs-conf missing">Not found</span>`;
      const probs = (i.problems || []).map((p) => `<div class="hs-problem">${icon("alert", "icon-sm")} ${e(p)}</div>`).join("");
      return `<tr class="hs-row lvl-${lvl}" data-key="${i.key}" data-orig="${fmt(i.value)}" data-conf="${i.confidence ?? ""}">
 <td${i.raw_text ? ` title="Read from report: ${e(i.raw_text)}"` : ""}><b>${e(b.name)}</b><div style="margin-top:4px">${conf}</div>${probs}</td>
 <td><input class="input hs-in" name="value" type="number" step="any" min="0" value="${fmt(i.value)}" placeholder="${i.found ? "" : "optional"}" aria-label="${e(b.name)} value"/></td>
 <td><select class="select hs-in ${noUnit ? "hs-need" : ""}" name="unit" aria-label="${e(b.name)} unit">${unitOpts(b, i.found ? i.unit : b.unit)}</select></td>
 <td class="hs-range"><input class="input hs-in" name="ref_low" type="number" step="any" value="${fmt(i.ref_low)}" placeholder="low" aria-label="reference low"/><span>–</span><input class="input hs-in" name="ref_high" type="number" step="any" value="${fmt(i.ref_high)}" placeholder="high" aria-label="reference high"/></td></tr>`;
    })
    .join("");
  const addable = hs.catalog.biomarkers.filter((b) => !rows.some((x) => x.key === b.key));
  const counts = { low: rows.filter((x) => x.found && x.confidence_level === "low").length, medium: rows.filter((x) => x.found && x.confidence_level === "medium").length, missing: rows.filter((x) => !x.found && HS_CORE.includes(x.key)).length };
  const pages = hsPages(d);
  const warn = (ex.warnings || []).map((w) => `<div class="source-strip demo">${icon("alert")} ${e(w)}</div>`).join("");
  const form = `<form data-hs-form="confirm" class="surface panel hs-review-form"><div class="panel-title"><h3>${pages ? "Extracted values" : "Enter your values"}</h3><span class="tag tag-gray">${rows.filter((x) => x.found).length} found</span></div>
 <div class="form-grid hs-meta"><div class="field"><label>Report / collection date</label><input class="input" type="date" name="report_date" max="${todayISO()}" required value="${e(r.report_date || "")}"/></div>
 <div class="field"><label>Sex (for typical ranges)</label><select class="select" name="sex" required><option value="">Choose…</option><option value="female" ${r.sex === "female" ? "selected" : ""}>Female</option><option value="male" ${r.sex === "male" ? "selected" : ""}>Male</option></select></div>
 <div class="field full"><label>Laboratory (optional)</label><input class="input" name="lab_name" maxlength="120" value="${e(r.lab_name || "")}"/></div></div>
 ${counts.low + counts.medium + counts.missing ? `<div class="hs-legend-row"><span class="hs-conf low">Low</span> ${counts.low} low-confidence · <span class="hs-conf medium">Check</span> ${counts.medium} to check · <span class="hs-conf missing">Not found</span> ${counts.missing} core tests not found</div>` : ""}
 <div class="table-wrap"><table class="data-table hs-table"><thead><tr><th>Test</th><th>Value</th><th>Unit</th><th>Lab range</th></tr></thead><tbody>${body}</tbody></table></div>
 ${addable.length ? `<div class="hs-add"><select class="select" id="hs-add-select"><option value="">Add another test from your report…</option>${addable.map((b) => `<option value="${b.key}">${e(b.name)}</option>`).join("")}</select><button type="button" class="btn btn-light btn-sm" data-hs="add-row">${icon("plus", "icon-sm")} Add</button></div>` : ""}
 <p class="muted tiny">Leave the range empty if your report has none — a typical adult range will be used and labelled. Blank values are skipped.</p>
 <label class="hs-consent strong"><input type="checkbox" name="checked" value="true" required/><span>I have checked these values and units against my original report.</span></label>
 <div class="filters"><button class="btn btn-primary" type="submit">${icon("check", "icon-sm")} Confirm and analyse</button><button type="button" class="btn btn-light" data-hs="delete" data-id="${r.id}">${icon("trash", "icon-sm")} Discard</button></div></form>`;
  return (
    `<button class="link-btn" data-hs="home" style="margin-bottom:12px">← All reports</button>` +
    heading(pages ? "Check the extracted values" : "Enter your blood count", pages ? "Compare each value with your original report. Highlighted boxes show where each number was read." : "Type the values exactly as printed on your report, with the unit and the lab range.", aiTag("Step 2 of 3")) +
    `<div class="stack">${warn}${pages ? `<div class="hs-split"><div class="surface panel hs-original"><div class="panel-title"><h3>${ex.photo ? "Your photo" : "Original report"}</h3><a class="link-btn" href="/api/hemoscan/reports/${r.id}/file" target="_blank" rel="noopener">Open ${ex.photo ? "full size" : "PDF"} ↗</a></div>${pages}
 <div class="legend hs-box-legend"><span class="b-high">High confidence</span><span class="b-medium">Check</span><span class="b-low">Low confidence</span></div></div>${form}</div>` : form}</div>`
  );
}

/* ------------------------------------------------------------------ analysis */

function hsRangeBar(x) {
  const lo = x.ref_low, hi = x.ref_high, span = hi - lo || 1;
  const min = lo - span * 0.5, max = hi + span * 0.5;
  const pos = Math.min(100, Math.max(0, ((x.value - min) / (max - min)) * 100));
  return `<div class="hs-bar" title="Range ${fmt(lo)}–${fmt(hi)}"><span class="hs-bar-band"></span><i class="${x.flag}" style="left:${pos}%"></i></div>`;
}

function hsAnalysis(d) {
  const a = d.analysis, r = d.report;
  const core = a.results.filter((x) => !bioOf(x.key).percent);
  const pct = a.results.filter((x) => bioOf(x.key).percent);
  const groups = [...new Set(core.map((x) => bioOf(x.key).group))];
  const resultTable = groups
    .map(
      (g) => `<tr class="hs-group"><td colspan="4">${e(g)}</td></tr>` +
        core.filter((x) => bioOf(x.key).group === g)
          .map((x) => `<tr class="${x.flag !== "normal" ? "hs-out" : ""}"><td><b>${e(x.name)}</b><div class="muted tiny hs-explain">${e(bioOf(x.key).explain)}</div></td><td class="hs-value"><b>${fmt(x.value)}</b> <span class="muted tiny">${e(x.unit)}</span>${x.edited ? '<div class="muted tiny">edited by you</div>' : ""}</td><td>${hsRangeBar(x)}<div class="muted tiny" style="margin-top:6px">${fmt(x.ref_low)} – ${fmt(x.ref_high)}${x.ref_source === "lab" ? "" : " · typical*"}</div></td><td><span class="tag ${FLAG_TAG[x.flag][0]}">${FLAG_TAG[x.flag][1]}</span></td></tr>`)
          .join(""),
    )
    .join("");
  const findings = a.findings.length
    ? a.findings
        .map((f) => `<div class="hs-finding sev-${f.severity}"><div class="hs-f-head"><span class="tag ${SEV_TAG[f.severity] || "tag-gray"}">${e(f.severity_label)}</span><h4>${e(f.title)}</h4></div>
 <div class="hs-f-grid"><div><div class="hs-f-label">Why it was flagged</div><ul>${f.why.map((w) => `<li>${e(w)}</li>`).join("")}</ul>${f.detail ? `<p class="small">${e(f.detail)}</p>` : ""}</div>
 <div><div class="hs-f-label">Can be associated with <span class="muted">(not a diagnosis)</span></div><ul>${f.associations.map((x) => `<li>${e(x)}</li>`).join("")}</ul></div>
 <div><div class="hs-f-label">Usual next steps a doctor may consider</div><ul>${f.next_steps.map((x) => `<li>${e(x)}</li>`).join("")}</ul></div></div>
 <div class="hs-refs">${icon("book", "icon-sm")} ${f.references.map((x) => e(x)).join(" · ")}</div>
 ${(hs.catalog.learn[f.id] || []).length ? `<div class="hs-learn"><span>${icon("pulse", "icon-sm")} Learn more in HemoCare:</span>${hs.catalog.learn[f.id].map((a) => `<button class="hs-chip" data-hc-article="${e(a.id)}">${e(a.title)}</button>`).join("")}</div>` : ""}</div>`)
        .join("")
    : `<div class="hs-allclear">${icon("check", "icon-xl")}<div><b>No pattern rules were triggered.</b><p class="muted small">All recognised values are within range. A blood count can't rule out every condition — keep any symptoms in mind.</p></div></div>`;
  const trends = a.trends.length
    ? `<div class="surface panel"><div class="panel-title"><h3>Since your previous report</h3><span class="tag tag-gray">${a.trends[0].previous_date ? dateLabel(a.trends[0].previous_date) : ""} → ${dateLabel(r.report_date)}</span></div>
 <div class="hs-trends">${a.trends.map((t) => `<div class="hs-trend ${t.note ? "noted" : ""}"><span class="muted tiny">${e(t.name.replace(/\s*\(.*\)/, ""))}</span><b>${fmt(t.previous)} → ${fmt(t.current)}</b><span class="tiny ${t.direction}">${t.direction === "up" ? "▲" : t.direction === "down" ? "▼" : "•"} ${t.change > 0 ? "+" : ""}${fmt(t.change)} ${e(t.unit)}</span></div>`).join("")}</div>
 ${a.trends.filter((t) => t.note).map((t) => `<div class="source-strip demo" style="margin-top:12px">${icon("trend")} ${e(t.note)}</div>`).join("")}</div>`
    : "";
  const don = a.donation
    ? `<div class="surface panel hs-donation ${a.donation.ok ? "ok" : "no"}"><div class="panel-title"><h3>${icon("droplet", "icon-sm")} What this means for donating</h3></div><p class="small">${e(a.donation.message)}</p>${a.donation.frequent_donor_note ? `<p class="small" style="margin-top:8px"><b>Frequent donor:</b> ${e(a.donation.frequent_donor_note)}</p>` : ""}<p class="muted tiny" style="margin-top:8px">${e(a.donation.threshold_note)}</p></div>`
    : "";
  const highlight = (i) => {
    const x = a.results.find((y) => y.key === i.key);
    return x && x.flag !== "normal" ? "flag-out" : null;
  };
  const pages = hsPages(d, highlight);
  const chat = hs.chat.filter((m) => m.id === r.id);
  const SRC = { llm: "AI", faq: "FAQ", guardrail: "Safety" };
  const ask = `<div class="surface panel"><div class="panel-title"><h3>Ask about this report</h3>${aiTag("Report assistant")}</div>
 <div class="hs-chat">${chat.map((m) => `<div class="message user">${e(m.q)}</div><div class="message assistant">${e(m.a)}<div class="muted tiny" style="margin-top:6px">Source: ${SRC[m.source] || m.source}</div></div>`).join("") || '<p class="muted small">Ask what a value means, why a pattern was flagged, or what to ask your doctor. The assistant only uses your confirmed values and can\'t diagnose or recommend treatment.</p>'}</div>
 <div class="suggested">${["What is MCV?", "Does this mean I have anaemia?", "Can I still donate blood?", "Why do lab ranges differ?"].map((q) => `<button data-hs="ask" data-q="${e(q)}">${e(q)}</button>`).join("")}</div>
 <form data-hs-form="ask" class="hs-ask"><input class="input" name="question" maxlength="500" required placeholder="Type a question about this report…"/><button class="btn btn-primary" type="submit">${icon("send", "icon-sm")}</button></form></div>`;
  return (
    `<button class="link-btn" data-hs="home" style="margin-bottom:12px">← All reports</button>` +
    heading(`Blood count · ${dateLabel(r.report_date)}`, `${e(r.lab_name || "Lab not stated")} · ranges for ${e(r.sex)} · ${r.source === "pdf" ? "read from PDF and checked by you" : "typed in by you"}`,
      `<div class="filters"><a class="btn btn-primary" href="/api/hemoscan/reports/${r.id}/summary" target="_blank" rel="noopener">${icon("file", "icon-sm")} Summary for my doctor</a>${r.has_file ? `<a class="btn btn-light" href="/api/hemoscan/reports/${r.id}/file" target="_blank" rel="noopener">View PDF</a>` : ""}<button class="btn btn-light" data-hs="reopen" data-id="${r.id}">Edit values</button><button class="btn btn-light" data-hs="delete" data-id="${r.id}" title="Delete report">${icon("trash", "icon-sm")}</button></div>`) +
    `<div class="stack">${a.urgent.length ? `<section class="shortage-banner red"><div><h2>Some values may need prompt attention</h2><p>${a.urgent.map((u) => e(u.message)).join(" ")} Please contact your doctor or clinic today. If you feel unwell, seek urgent care.</p></div></section>` : ""}
 ${state.lang === "ms" ? `<div class="i18n-note">${icon("info", "icon-sm")}<span>Nama ujian dan penemuan klinikal dipaparkan dalam Bahasa Inggeris seperti dalam laporan makmal anda.</span></div>` : ""}<div class="kpi-grid">${miniStat("In range", a.counts.normal, "", "success-text")}${miniStat("Low", a.counts.low, "", a.counts.low ? "danger-text" : "")}${miniStat("High", a.counts.high, "", a.counts.high ? "danger-text" : "")}${miniStat("Patterns flagged", a.findings.length)}</div>
 <div class="surface panel"><div class="panel-title"><h3>Plain-language explanation</h3><div class="banner-tags">${aiTag(r.used_llm ? "AI explanation" : "Explanation")}${r.used_llm ? "" : '<span class="muted tiny">template mode (no LLM key)</span>'}</div></div><div class="explain hs-explanation">${e(r.explanation)}</div>
 ${a.doctor_questions && a.doctor_questions.length ? `<div class="hs-f-label" style="margin-top:16px">Questions to ask your doctor</div><ul class="hs-questions">${a.doctor_questions.map((q) => `<li>${e(q)}</li>`).join("")}</ul>` : ""}</div>
 <div class="surface panel"><div class="panel-title"><h3>Patterns found</h3><span class="tag tag-gray">Rules ${e(a.rules_version)} · ${e(a.review.status)}</span></div>${findings}</div>
 ${trends}
 <div class="hs-split wide-left"><div class="surface panel"><div class="panel-title"><h3>Your results</h3><span class="tag tag-gray">${core.length} tests</span></div><div class="table-wrap"><table class="data-table hs-results"><thead><tr><th>Test</th><th>Value</th><th>Reference range</th><th></th></tr></thead><tbody>${resultTable}</tbody></table></div>
 ${pct.length ? `<p class="muted tiny" style="margin-top:10px">Differential %: ${pct.map((x) => `${e(x.name)} ${fmt(x.value)}%`).join(" · ")} (shown for reference; rules use absolute counts)</p>` : ""}
 ${core.some((x) => x.ref_source !== "lab") ? '<p class="muted tiny" style="margin-top:6px">* Typical adult range used because the report had none.</p>' : ""}</div>
 ${pages ? `<div class="surface panel hs-original"><div class="panel-title"><h3>Original report</h3><a class="link-btn" href="/api/hemoscan/reports/${r.id}/file" target="_blank" rel="noopener">Open PDF ↗</a></div>${pages}<div class="legend hs-box-legend"><span class="b-out">Out-of-range value</span></div></div>` : ""}</div>
 ${don}${ask}
 <div class="surface panel"><div class="panel-title"><h3>Limitations</h3></div><ul class="hs-limits">${a.limitations.map((x) => `<li>${e(x)}</li>`).join("")}</ul>
 <p class="muted tiny" style="margin-top:10px">Rules version ${e(a.rules_version)} · ${e(a.review.status)}. Thresholds marked “placeholder” must be confirmed by a clinician before real use.</p></div>
 <div class="disclaimer">${icon("shield", "icon-sm")} ${e(d.disclaimer)}</div></div>`
  );
}

/* ------------------------------------------------------------------ camera / photo */

async function hsShrink(blob) {
  // downscale big phone photos (faster upload + OCR); drawing to a canvas also applies the EXIF rotation
  const url = URL.createObjectURL(blob);
  try {
    const img = await new Promise((ok, bad) => { const i = new Image(); i.onload = () => ok(i); i.onerror = () => bad(new Error("This photo could not be opened.")); i.src = url; });
    const k = Math.min(1, 2000 / Math.max(img.naturalWidth, img.naturalHeight));
    const cv = document.createElement("canvas");
    cv.width = Math.round(img.naturalWidth * k);
    cv.height = Math.round(img.naturalHeight * k);
    cv.getContext("2d").drawImage(img, 0, 0, cv.width, cv.height);
    return await new Promise((ok) => cv.toBlob(ok, "image/jpeg", 0.9));
  } finally {
    URL.revokeObjectURL(url);
  }
}
async function hsSetPhoto(blob) {
  const small = await hsShrink(blob);
  if (hs.photo) URL.revokeObjectURL(hs.photo.url);
  hs.photo = { blob: small, url: URL.createObjectURL(small) };
  const consentOn = document.querySelector('[data-hs-form="photo"] [name=consent]')?.checked;
  await page();
  if (consentOn) document.querySelector('[data-hs-form="photo"] [name=consent]').checked = true;
}
function hsStopCamera() {
  if (hs.stream) hs.stream.getTracks().forEach((t) => t.stop());
  hs.stream = null;
}
async function hsOpenCamera() {
  if (!navigator.mediaDevices?.getUserMedia) {
    toast("Live camera isn't available here — use “Choose a photo” (on a phone it opens the camera).", true);
    return;
  }
  modal("Take a photo of your report", "Lay the page flat in good light and fill the frame.",
    `<div class="hs-cam"><video id="hs-video" autoplay playsinline muted></video><div class="hs-cam-guide"></div></div>
 <div class="modal-footer"><button type="button" class="btn btn-light" data-action="close-modal">Cancel</button><button type="button" class="btn btn-primary" data-hs="snap">${icon("camera", "icon-sm")} Capture</button></div>`);
  try {
    hs.stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: { ideal: "environment" }, width: { ideal: 1920 }, height: { ideal: 1440 } }, audio: false });
    const v = document.getElementById("hs-video");
    if (v) v.srcObject = hs.stream;
    else hsStopCamera();
  } catch (err) {
    closeModal();
    toast("Couldn't open the camera (permission denied or no camera). Use “Choose a photo” instead.", true);
  }
}
async function hsSnap() {
  const v = document.getElementById("hs-video");
  if (!v || !v.videoWidth) return toast("The camera is still starting — try again in a second.", true);
  const cv = document.createElement("canvas");
  cv.width = v.videoWidth;
  cv.height = v.videoHeight;
  cv.getContext("2d").drawImage(v, 0, 0);
  const blob = await new Promise((ok) => cv.toBlob(ok, "image/jpeg", 0.92));
  hsStopCamera();
  closeModal();
  await hsSetPhoto(blob);
}

/* ------------------------------------------------------------------ events */

async function hsGo(id) {
  hs.id = id;
  hs.extra = [];
  await page();
  window.scrollTo({ top: 0, behavior: "smooth" });
}

async function hsAsk(q) {
  const id = hs.id;
  hs.chat.push({ id, q, a: "…", source: "" });
  await page();
  try {
    const r = await send(`/api/hemoscan/reports/${id}/ask`, { question: q });
    Object.assign(hs.chat[hs.chat.length - 1], { a: r.answer, source: r.source });
  } catch (err) {
    hs.chat.pop();
    toast(err.message, true);
  }
  await page();
  document.querySelector(".hs-ask input")?.focus();
}

document.addEventListener("click", async (ev) => {
  if (hs.stream && ev.target.closest('[data-action="close-modal"],[data-action="overlay-close"]')) hsStopCamera();
  const b = ev.target.closest("[data-hs]");
  if (!b) return;
  ev.preventDefault();
  const act = b.dataset.hs;
  try {
    if (act === "home") await hsGo(null);
    if (act === "mode") {
      hs.mode = b.dataset.mode;
      await page();
    }
    if (act === "camera") await hsOpenCamera();
    if (act === "snap") await hsSnap();
    if (act === "open") await hsGo(Number(b.dataset.id));
    if (act === "metric") {
      hs.metric = b.dataset.key;
      await page();
    }
    if (act === "manual") {
      const r = await send("/api/hemoscan/reports/manual", {});
      await hsGo(r.id);
    }
    if (act === "add-row") {
      const k = document.getElementById("hs-add-select").value;
      if (k) {
        hs.extra.push(k);
        const keep = hsCollect();
        await page();
        hsRestore(keep);
      }
    }
    if (act === "reopen") {
      await send(`/api/hemoscan/reports/${Number(b.dataset.id)}/reopen`, {});
      toast("Values reopened for editing");
      await page();
    }
    if (act === "delete" && confirm("Delete this report and its results permanently?")) {
      await api(`/api/hemoscan/reports/${Number(b.dataset.id)}`, { method: "DELETE" });
      toast("Report deleted");
      await hsGo(null);
    }
    if (act === "ask") await hsAsk(b.dataset.q);
  } catch (err) {
    toast(err.message, true);
  }
});

function hsCollect() {
  const out = {};
  document.querySelectorAll(".hs-row").forEach((tr) => {
    out[tr.dataset.key] = Object.fromEntries([...tr.querySelectorAll(".hs-in")].map((i) => [i.name, i.value]));
  });
  return out;
}
function hsRestore(saved) {
  document.querySelectorAll(".hs-row").forEach((tr) => {
    const s = saved[tr.dataset.key];
    if (s) tr.querySelectorAll(".hs-in").forEach((i) => (i.value = s[i.name] ?? i.value));
  });
}

document.addEventListener("submit", async (ev) => {
  const form = ev.target;
  const kind = form.dataset.hsForm;
  if (!kind) return;
  ev.preventDefault();
  const btn = form.querySelector('[type="submit"]');
  if (btn) btn.disabled = true;
  try {
    if (kind === "upload") {
      if (btn) btn.innerHTML = "Reading your report…";
      const fd = new FormData(form);
      const res = await fetch("/api/hemoscan/reports/upload", { method: "POST", body: fd, credentials: "same-origin", headers: { "X-HemoLink-Request": "app", "X-HemoLink-Lang": state.lang === "ms" ? "ms" : "en" } });
      const out = await res.json().catch(() => ({ detail: "Upload failed" }));
      if (!res.ok) throw new Error(typeof out.detail === "string" ? out.detail : "Upload failed");
      toast(out.needs_manual ? "No values could be read — please type them in" : out.ocr ? `Read ${out.found} tests with OCR — please check each one` : `Found ${out.found} tests — please check them`);
      await hsGo(out.id);
    }
    if (kind === "photo") {
      if (!hs.photo) throw new Error("Take or choose a photo first.");
      if (btn) btn.innerHTML = "Reading your photo… (a few seconds)";
      const fd = new FormData();
      fd.append("file", hs.photo.blob, "report-photo.jpg");
      fd.append("consent", new FormData(form).get("consent") || "false");
      const res = await fetch("/api/hemoscan/reports/photo", { method: "POST", body: fd, credentials: "same-origin", headers: { "X-HemoLink-Request": "app", "X-HemoLink-Lang": state.lang === "ms" ? "ms" : "en" } });
      const out = await res.json().catch(() => ({ detail: "Upload failed" }));
      if (!res.ok) throw new Error(typeof out.detail === "string" ? out.detail : "Upload failed");
      URL.revokeObjectURL(hs.photo.url);
      hs.photo = null;
      toast(out.found ? `Read ${out.found} tests from your photo — please check each one` : "Couldn't read values from the photo — please type them in beside it");
      await hsGo(out.id);
    }
    if (kind === "confirm") {
      const fd = new FormData(form);
      const results = [...form.querySelectorAll(".hs-row")]
        .map((tr) => {
          const v = (n) => tr.querySelector(`[name="${n}"]`).value.trim();
          const num = (n) => (v(n) === "" ? null : Number(v(n)));
          return { key: tr.dataset.key, value: num("value"), unit: v("unit") || null, ref_low: num("ref_low"), ref_high: num("ref_high"),
            edited: tr.dataset.orig !== "" && v("value") !== "" && Number(v("value")) !== Number(tr.dataset.orig), confidence: tr.dataset.conf === "" ? null : Number(tr.dataset.conf) };
        })
        .filter((x) => x.value !== null);
      const r = await send(`/api/hemoscan/reports/${hs.id}/confirm`, { report_date: fd.get("report_date"), sex: fd.get("sex"), lab_name: fd.get("lab_name") || "", checked: fd.get("checked") === "true", results });
      toast(r.urgent ? "Analysis ready — some values may need prompt attention" : `Analysis ready · ${r.findings} pattern${r.findings === 1 ? "" : "s"} flagged`);
      await page();
      window.scrollTo({ top: 0, behavior: "smooth" });
    }
    if (kind === "ask") {
      const q = new FormData(form).get("question");
      await hsAsk(q);
    }
  } catch (err) {
    toast(err.message, true);
  } finally {
    if (btn && btn.isConnected) {
      btn.disabled = false;
      if (kind === "upload") btn.innerHTML = `${icon("spark", "icon-sm")} Read my report`;
      if (kind === "photo") btn.innerHTML = `${icon("spark", "icon-sm")} Read my photo`;
    }
  }
});

document.addEventListener("change", (ev) => {
  if (ev.target.matches('.hs-file input[type="file"]')) {
    const f = ev.target.files[0];
    const label = document.querySelector(".hs-file-name");
    if (label) label.textContent = f ? `${f.name} · ${(f.size / 1024).toFixed(0)} KB` : "";
    ev.target.closest(".hs-file").classList.toggle("has-file", !!f);
  }
  if (ev.target.id === "hs-photo-input" && ev.target.files[0]) hsSetPhoto(ev.target.files[0]).catch((err) => toast(err.message, true));
  if (ev.target.matches(".hs-row select[name=unit]")) ev.target.classList.toggle("hs-need", !ev.target.value);
});

// Hover a row in the review table → highlight where it was read on the original page
document.addEventListener("mouseover", (ev) => {
  const tr = ev.target.closest?.(".hs-row");
  document.querySelectorAll(".hs-box.focus").forEach((x) => x.classList.remove("focus"));
  if (tr) document.querySelectorAll(`.hs-box[data-box="${tr.dataset.key}"]`).forEach((x) => x.classList.add("focus"));
});
