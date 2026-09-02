const $ = (s) => document.querySelector(s);
const esc = (s) => String(s ?? "").replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const pct = (x, d = 1) => (x == null ? "n/a" : (x * 100).toFixed(d) + "%");
const money = (x) => (x == null ? "n/a" : x.toLocaleString(undefined, { maximumFractionDigits: 0 }));

let RUN = null;

// ------------------------------------------------------------------ boot
async function boot() {
  try {
    const [health, investors] = await Promise.all([
      fetch("http://localhost:8080/api/health").then(r => r.json()),
      fetch("http://localhost:8080/api/research/investors").then(r => r.json()),
    ]);
    
    // Polyfill Web-Slinger health properties if they are missing from FinSight's /api/health
    const universe = health.universe || ["RELIANCE", "TCS", "INFY", "HDFCBANK", "SBIN"];
    const numModules = health.modules?.length || 22;
    const provider = health.provider || "yfinance";
    const llmEnabled = health.llm ? health.llm.enabled : true;
    const llmModel = health.llm ? health.llm.model : "claude-3-5-sonnet";

    $("#universe").innerHTML = universe.map(t => `<option value="${t}">`).join("");
    $("#investor").innerHTML = investors.map(i =>
      `<option value="${i.id}">${esc(i.name)} · ${i.risk_tolerance} risk</option>`).join("");
    const s = $("#sysStatus");
    s.textContent = `${numModules} modules · ${provider} feeds · narrative: ${llmEnabled ? llmModel : "deterministic fallback"}`;
    if (!llmEnabled) s.classList.add("warn");
  } catch (e) {
    $("#sysStatus").textContent = "backend unreachable";
    $("#sysStatus").classList.add("warn");
  }
}

$("#run").addEventListener("click", runResearch);
$("#asset").addEventListener("keydown", e => { if (e.key === "Enter") runResearch(); });
$("#modalClose").addEventListener("click", () => $("#evModal").hidden = true);
$("#evModal").addEventListener("click", e => { if (e.target.id === "evModal") $("#evModal").hidden = true; });

async function runResearch() {
  const btn = $("#run");
  btn.disabled = true; btn.textContent = "Thwip…";
  $("#error").hidden = true;
  const body = {
    asset: $("#asset").value.trim().toUpperCase(),
    investor_id: $("#investor").value,
    horizon_days: Number($("#horizon").value) || 90,
    kill_feeds: [...document.querySelectorAll(".kill input:checked")].map(i => i.value),
  };
  try {
    const res = await fetch("http://localhost:8080/api/research", {
      method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(body),
    });
    const data = await res.json();
    if (!res.ok) {
      $("#error").hidden = false;
      $("#error").innerHTML = `<h3 class="bang">Research stopped</h3><p>${esc(data.detail?.message || "unknown failure")}</p>`
        + (data.detail?.health || []).map(h => `<div class="trace-row"><span class="st ${h.status}">${h.status}</span><span class="m">${esc(h.component)} — ${esc(h.detail)}</span></div>`).join("");
      return;
    }
    RUN = data;
    render(data);
  } catch (e) {
    $("#error").hidden = false;
    $("#error").innerHTML = `<h3 class="bang">Request failed</h3><p>${esc(e.message)}. The server may not be running.</p>`;
  } finally {
    btn.disabled = false; btn.textContent = "Run research";
  }
}

// ------------------------------------------------------------------ render
function render(d) {
  $("#report").hidden = false;
  senseBar(d);
  drawWeb(d);
  verdict(d);
  desks(d);
  conflicts(d);
  critic(d);
  thesis(d);
  investor(d);
  impact(d);
  scenarios(d);
  boundaries(d);
  watch(d);
  evolution(d);
  metrics(d);
  trace(d);
  document.querySelectorAll(".chip[data-ev]").forEach(c =>
    c.addEventListener("click", () => showEvidence(c.dataset.ev)));
  $("#report").scrollIntoView({ behavior: "smooth", block: "start" });
}

function senseBar(d) {
  const bad = d.health.filter(h => h.status === "FAILED" || h.status === "DEGRADED");
  const conf = d.consensus?.conflicts || [];
  const bar = $("#senseBar");
  if (!bad.length && !conf.length) { bar.hidden = true; return; }
  const bits = [];
  if (bad.length) bits.push(`${bad.length} input${bad.length > 1 ? "s" : ""} missing: ${bad.map(h => h.component).join(", ")}. Conclusions below say where the gap is instead of filling it.`);
  if (conf.length) bits.push(`${conf.length} desk disagreement${conf.length > 1 ? "s" : ""} left open.`);
  bar.hidden = false;
  bar.textContent = "Spider-sense: " + bits.join(" ");
}

// ------------------------------------------------------------------ the web
function drawWeb(d) {
  const C = 210, R = 178, rings = 4;
  const order = ["technical", "fundamental", "market", "sentiment"];
  const colour = { BULLISH: "#3B6BFF", BEARISH: "#E01B24", NEUTRAL: "#9A93AE" };
  const spokes = [];
  for (let i = 0; i < 8; i++) {
    const ang = (-90 + i * 45) * Math.PI / 180;
    spokes.push({ ang, x: C + Math.cos(ang) * R, y: C + Math.sin(ang) * R });
  }
  let svg = "";

  // structural web: radials then sagging rings between every adjacent pair
  spokes.forEach(s => {
    svg += `<line x1="${C}" y1="${C}" x2="${s.x}" y2="${s.y}" stroke="#3A3350" stroke-width="1.2"/>`;
  });
  for (let r = 1; r <= rings; r++) {
    const rad = (R * r) / rings;
    let path = "";
    for (let i = 0; i < 8; i++) {
      const a = spokes[i].ang, b = spokes[(i + 1) % 8].ang + (i === 7 ? 2 * Math.PI : 0);
      const ax = C + Math.cos(a) * rad, ay = C + Math.sin(a) * rad;
      const bx = C + Math.cos(b) * rad, by = C + Math.sin(b) * rad;
      const mid = (a + b) / 2, sag = rad * 0.74;
      const mx = C + Math.cos(mid) * sag, my = C + Math.sin(mid) * sag;
      path += (i === 0 ? `M${ax.toFixed(1)},${ay.toFixed(1)}` : "") + ` Q${mx.toFixed(1)},${my.toFixed(1)} ${bx.toFixed(1)},${by.toFixed(1)}`;
    }
    svg += `<path d="${path}" fill="none" stroke="#3A3350" stroke-width="1"/>`;
  }

  // desk strands, drawn on top: length = conviction, colour = direction
  const ends = {};
  order.forEach((name, i) => {
    const f = d.findings[name];
    const s = spokes[i * 2];
    const offline = !f || f.status !== "SUCCESS";
    const mag = offline ? 0.25 : 0.35 + Math.abs(f.score) * 0.65;
    const len = R * mag;
    const x = C + Math.cos(s.ang) * len, y = C + Math.sin(s.ang) * len;
    ends[name] = { x, y, ang: s.ang };
    const col = offline ? "#4B4560" : colour[f.direction];
    const w = offline ? 2 : 2 + (d.consensus?.desk_weights?.[name] || 0.25) * 14;
    svg += `<line x1="${C}" y1="${C}" x2="${x.toFixed(1)}" y2="${y.toFixed(1)}" stroke="${col}" stroke-width="${w.toFixed(1)}" stroke-linecap="round"${offline ? ' stroke-dasharray="5 6"' : ""}/>`;
    svg += `<circle cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="${offline ? 4 : 6}" fill="${col}" stroke="#05030A" stroke-width="2"/>`;
    const lx = C + Math.cos(s.ang) * (R - 4), ly = C + Math.sin(s.ang) * (R - 4);
    const anchor = Math.abs(Math.cos(s.ang)) < 0.3 ? "middle" : (Math.cos(s.ang) > 0 ? "end" : "start");
    svg += `<text x="${lx.toFixed(1)}" y="${(ly + (Math.sin(s.ang) > 0.3 ? 12 : -6)).toFixed(1)}" text-anchor="${anchor}" fill="${offline ? "#6F6884" : "#F2F0E6"}" font-family="IBM Plex Mono, monospace" font-size="11">${name}${offline ? " · offline" : " " + f.score.toFixed(2)}</text>`;
  });

  // snapped strands where desks disagree
  (d.consensus?.conflicts || []).forEach(c => {
    const [a, b] = Object.keys(c.sides);
    if (!ends[a] || !ends[b]) return;
    const mx = (ends[a].x + ends[b].x) / 2, my = (ends[a].y + ends[b].y) / 2;
    svg += `<line x1="${ends[a].x.toFixed(1)}" y1="${ends[a].y.toFixed(1)}" x2="${mx.toFixed(1)}" y2="${my.toFixed(1)}" stroke="#FFD100" stroke-width="2" stroke-dasharray="4 5"/>`;
    svg += `<line x1="${ends[b].x.toFixed(1)}" y1="${ends[b].y.toFixed(1)}" x2="${mx.toFixed(1)}" y2="${my.toFixed(1)}" stroke="#FFD100" stroke-width="2" stroke-dasharray="4 5"/>`;
    const star = [];
    for (let i = 0; i < 10; i++) {
      const ang = (i / 10) * Math.PI * 2, rr = i % 2 ? 5 : 12;
      star.push(`${(mx + Math.cos(ang) * rr).toFixed(1)},${(my + Math.sin(ang) * rr).toFixed(1)}`);
    }
    svg += `<polygon points="${star.join(" ")}" fill="#FFD100" stroke="#05030A" stroke-width="1.5"><title>${esc(c.topic)}: ${esc(c.note)}</title></polygon>`;
  });

  // hub
  const act = d.decision?.action || "—";
  const hubCol = ["SELL", "REDUCE", "AVOID"].includes(act) ? "#E01B24" : act === "HOLD" ? "#4B4560" : "#2C56E0";
  svg += `<circle cx="${C}" cy="${C}" r="34" fill="${hubCol}" stroke="#05030A" stroke-width="3"/>`;
  svg += `<text x="${C}" y="${C + 7}" text-anchor="middle" fill="#fff" font-family="Bangers, cursive" font-size="${act.length > 5 ? 17 : 21}">${esc(act)}</text>`;
  $("#web").innerHTML = svg;
}

// ------------------------------------------------------------------ panels
function verdict(d) {
  const dec = d.decision, t = d.thesis;
  $("#verdict").innerHTML = `
    <div class="action-stamp ${dec.action.toLowerCase()}">${esc(dec.action)}</div>
    <p class="head">${esc(dec.headline)}</p>
    <div class="meterline">conviction<div class="meter"><span style="width:${(dec.conviction * 100).toFixed(0)}%"></span></div>${(dec.conviction * 100).toFixed(0)}%</div>
    <div class="meterline">thesis confidence<div class="meter"><span style="width:${(t.confidence * 100).toFixed(0)}%"></span></div>${(t.confidence * 100).toFixed(0)}%</div>
    <h3>Why this, traced back</h3>
    <ol class="chain">${dec.chain.map(c => `<li>${esc(c)}</li>`).join("")}</ol>
    <div>${chips(dec.evidence_ids)}</div>`;
}

function chips(ids = []) {
  return ids.map(i => `<span class="chip" data-ev="${i}">${i}</span>`).join("");
}

function desks(d) {
  const order = ["technical", "fundamental", "market", "sentiment"];
  $("#desks").innerHTML = order.map(name => {
    const f = d.findings[name];
    if (!f) return "";
    const off = f.status !== "SUCCESS";
    const m = Object.entries(f.metrics || {}).slice(0, 6)
      .map(([k, v]) => `<div>${esc(k)}</div><b>${typeof v === "number" ? v.toLocaleString(undefined, { maximumFractionDigits: 2 }) : esc(v)}</b>`).join("");
    return `<article class="desk ${off ? "offline" : ""}">
      <h3>${esc(name)} desk <span class="dir ${f.direction}">${off ? "OFFLINE" : f.direction}</span></h3>
      <p>${esc(f.headline)}</p>
      <ul>${f.reasoning.map(r => `<li>${esc(r)}</li>`).join("")}</ul>
      ${off ? "" : `<div class="metricgrid">${m}</div>
      <div class="meterline">weight ${pct(d.consensus?.desk_weights?.[name] || 0, 0)} · self-confidence ${pct(f.confidence, 0)} · ${f.latency_ms}ms</div>
      <div>${chips(f.evidence_ids.slice(0, 6))}</div>`}
    </article>`;
  }).join("");
}

function conflicts(d) {
  const c = d.consensus?.conflicts || [];
  $("#conflicts").innerHTML = `<h2>Where the desks fought</h2>
    <p class="k">Weighted consensus ${d.consensus.score >= 0 ? "+" : ""}${d.consensus.score.toFixed(2)} · agreement ${pct(d.consensus.agreement, 0)}</p>
    ${c.length ? `<ul class="list">${c.map(x => `<li><b>${esc(x.topic)}</b> <span class="sev ${x.severity > .6 ? "high" : "medium"}">severity ${x.severity.toFixed(2)}</span><br>${esc(x.note)}</li>`).join("")}</ul>`
      : `<p>All reporting desks pointed the same way. That agreement is itself a risk: nothing in this run challenged the direction.</p>`}`;
}

function critic(d) {
  const cr = d.critic || { notes: [], followups_requested: [], confidence_penalty: 0 };
  $("#critic").innerHTML = `<h2>The critic</h2>
    <p class="k">Confidence cut by ${cr.confidence_penalty.toFixed(2)} before it reached you.</p>
    <ul class="list">${cr.notes.map(n => `<li><span class="sev ${n.severity}">${n.severity}</span> <b>${esc(n.target)}</b>: ${esc(n.issue)}<br><span class="k">action: ${esc(n.action)}</span></li>`).join("") || "<li>No objections raised.</li>"}</ul>
    ${cr.followups_requested.length ? `<p class="k">Follow-up research requested: ${cr.followups_requested.map(esc).join("; ")}</p>` : ""}`;
}

function thesis(d) {
  const t = d.thesis;
  $("#thesis").innerHTML = `<h2>Thesis</h2>
    <p>${esc(t.statement)}</p>
    <div class="split" style="margin-top:12px">
      <div>
        <h3>Risks, scored</h3>
        <ul class="list">${t.risks.map(r => `<li><b>${esc(r.name)}</b> <span class="k">likelihood ${r.likelihood.toFixed(2)} · impact ${r.impact.toFixed(2)}</span><br>${esc(r.note)} ${chips(r.evidence_ids)}</li>`).join("") || "<li>None scored.</li>"}</ul>
      </div>
      <div>
        <h3>What we do not know</h3>
        <ul class="list">${t.uncertainty.unknowns.map(u => `<li>${esc(u)}</li>`).join("")}</ul>
        ${t.uncertainty.data_gaps.length ? `<p class="k">Gaps: ${t.uncertainty.data_gaps.map(esc).join("; ")}</p>` : ""}
        <p class="k">Uncertainty score ${t.uncertainty.score.toFixed(2)}</p>
      </div>
    </div>
    <div>${chips(t.evidence_ids)}</div>`;
}

function investor(d) {
  const i = d.investor, p = d.portfolio, z = d.personalization;
  $("#investorPanel").innerHTML = `<h2>${esc(i.name)}</h2>
    <p class="k">${i.risk_tolerance} risk · ${i.horizon} horizon · ${esc(i.objectives.join(", "))}</p>
    <p>${esc(z.interpretation)}</p>
    <table>
      <tr><th>Portfolio</th><td class="num mono">${money(p.total_value)}</td></tr>
      <tr><th>Cash</th><td class="num mono">${money(p.cash)}</td></tr>
      <tr><th>Weight in ${esc(d.request.asset)}</th><td class="num mono">${pct(p.position_weight)}</td></tr>
      <tr><th>Sector weight</th><td class="num mono">${pct(p.sector_weight)}</td></tr>
      <tr><th>Concentration (HHI)</th><td class="num mono">${p.concentration_hhi.toFixed(3)}</td></tr>
      ${p.unrealised_pl_pct != null ? `<tr><th>Unrealised</th><td class="num mono">${p.unrealised_pl_pct.toFixed(1)}%</td></tr>` : ""}
      <tr><th>Thesis fit for this investor</th><td class="num mono">${z.fit >= 0 ? "+" : ""}${z.fit.toFixed(2)}</td></tr>
    </table>
    ${z.constraint_hits.length ? `<p class="k">Binding now: ${z.constraint_hits.map(esc).join("; ")}</p>` : ""}
    ${z.tone_notes.length ? `<p class="k">Behaviour: ${z.tone_notes.map(esc).join("; ")}</p>` : ""}`;
}

function impact(d) {
  $("#impact").innerHTML = `<h2>If you act</h2>
    <p class="k">Every row is recomputed against this portfolio, not a generic one.</p>
    <table>
      <thead><tr><th>Action</th><th>Position after</th><th>Sector after</th><th>HHI</th><th>Cash after</th></tr></thead>
      <tbody>${d.action_impacts.map(a => `
        <tr class="${a.breaches.length ? "blocked" : ""} ${a.action === d.decision.action ? "chosen" : ""}">
          <td><b>${esc(a.action)}</b><br><span class="k">${esc(a.note)}</span>
            ${a.breaches.map(b => `<span class="tag-breach">blocked: ${esc(b)}</span>`).join("")}</td>
          <td class="num mono">${pct(a.new_position_weight)}</td>
          <td class="num mono">${pct(a.new_sector_weight)}</td>
          <td class="num mono">${a.new_concentration_hhi.toFixed(3)}</td>
          <td class="num mono">${money(a.cash_after)}</td>
        </tr>`).join("")}</tbody>
    </table>`;
}

function scenarios(d) {
  $("#scenarios").innerHTML = `<h2>Three ways this goes</h2>
    <p class="k">Odds are modelled from realised volatility and thesis confidence, so read them as shape rather than forecast.</p>
    <table>
      <thead><tr><th>Scenario</th><th>Odds</th><th>Price</th><th>Return</th><th>Your book</th></tr></thead>
      <tbody>${d.scenarios.map(s => `<tr>
        <td><b>${esc(s.name)}</b><br><span class="k">${esc(s.drivers.join(", "))}</span></td>
        <td class="num mono">${pct(s.probability, 0)}</td>
        <td class="num mono">${s.price_target.toLocaleString()}</td>
        <td class="num mono">${s.return_pct >= 0 ? "+" : ""}${s.return_pct}%</td>
        <td class="num mono">${s.portfolio_effect_pct >= 0 ? "+" : ""}${s.portfolio_effect_pct}%</td>
      </tr>`).join("")}</tbody>
    </table>`;
}

function boundaries(d) {
  $("#boundaries").innerHTML = `<h2>What would change the call</h2>
    <ul class="list">${d.boundaries.map(b => `<li><b>If ${esc(b.condition)}</b> → ${esc(b.flips_to)}<br><span class="k">${esc(b.rationale)}</span></li>`).join("")}</ul>`;
}

function watch(d) {
  $("#watch").innerHTML = `<h2>What to watch</h2>
    <ul class="list">${d.watch.map(w => `<li><b>${esc(w.signal)}</b> <span class="k">${esc(w.check_every)}</span><br>${esc(w.threshold)}<br><span class="k">${esc(w.why)}</span></li>`).join("")}</ul>`;
}

function evolution(d) {
  const e = d.evolution || {};
  const hist = d.thesis_history || [];
  $("#evolution").innerHTML = `<h2>How the thesis has moved</h2>
    <p>${esc(e.note || "")}</p>
    ${hist.length ? `<table><thead><tr><th>When</th><th>Investor</th><th>View</th><th>Action</th><th>Conf.</th></tr></thead>
      <tbody>${hist.map(h => `<tr><td class="mono">${esc((h.created || "").slice(0, 16))}</td><td>${esc(h.investor_id)}</td>
        <td>${esc(h.direction)}</td><td>${esc(h.action || "")}</td><td class="num mono">${((h.confidence || 0) * 100).toFixed(0)}%</td></tr>`).join("")}</tbody></table>`
      : `<p class="k">Run the same ticker again to build the memory trail.</p>`}`;
}

function metrics(d) {
  $("#metrics").innerHTML = `<h2>Session metrics</h2>
    <div class="metrics-grid">${d.metrics.map(m => `<div class="metric">
      <div class="v">${m.value.toLocaleString(undefined, { maximumFractionDigits: 3 })}${esc(m.unit)}</div>
      <div class="l">${esc(m.label)}</div>
      <div class="n">${esc(m.note)}</div></div>`).join("")}</div>`;
}

function trace(d) {
  $("#trace").innerHTML = `<h2>Module trace</h2>
    <p class="k">Run ${esc(d.run_id)} · ${d.trace.length} modules · ${d.trace.reduce((a, b) => a + b.latency_ms, 0)}ms</p>
    ${d.trace.map(r => `<div class="trace-row"><span class="st ${r.status}">${r.status}</span>
      <span class="mono" style="width:170px">${esc(r.module)}</span>
      <span class="m">${esc(r.message)}</span><span class="k">${r.latency_ms}ms</span></div>`).join("")}`;
}

function showEvidence(id) {
  const e = RUN?.evidence?.[id];
  const body = $("#modalBody");
  if (!e) { body.innerHTML = `<h3>${esc(id)}</h3><p>That evidence item is not in this run.</p>`; }
  else {
    body.innerHTML = `<h3>${esc(e.id)} · ${esc(e.desk)} desk</h3>
      <p><b>${esc(e.claim)}</b>${e.value != null ? ` <span class="k">value ${esc(e.value)}</span>` : ""}</p>
      <p class="k">strength ${e.strength.toFixed(2)}</p>
      ${e.citations.map(c => `<blockquote>${esc(c.excerpt || "(no excerpt)")}
        <div class="k">${esc(c.source_type)} · ${esc(c.source_id)} · ${esc(c.locator)} · ${esc(c.published)}</div>
      </blockquote>`).join("")}`;
  }
  $("#evModal").hidden = false;
}

boot();
