"use strict";
let data, active;
const $ = (id) => document.getElementById(id);
function el(tag, text, cls) {
  const e = document.createElement(tag);
  if (text !== undefined) e.textContent = text;
  if (cls) e.className = cls;
  return e;
}
function badge(state) {
  return el("span", state.replaceAll("_", " "), "badge " + state);
}
function detail(title, value) {
  const d = el("details"),
    pre = el("pre", JSON.stringify(value, null, 2));
  pre.tabIndex = 0;
  d.append(el("summary", title), pre);
  return d;
}
function option(select, value, text) {
  const o = el("option", text);
  o.value = value;
  select.append(o);
}
function renderResults(target, assessment) {
  target.replaceChildren();
  for (const [key, r] of Object.entries(assessment.requirements)) {
    const row = el("tr"),
      name = el("td"),
      before = el("td"),
      after = el("td"),
      proof = el("td");
    name.append(el("strong", r.label), el("div", key, "hint"));
    before.append(badge(r.before));
    after.append(badge(r.state));
    proof.append(
      detail("Witness chain", r.witness),
      detail("Typed inputs & source claims", r.inputs),
    );
    row.append(name, before, after, proof);
    target.append(row);
  }
}
function graph() {
  const req = $("requirement").value,
    facts = data.snapshot.facts,
    svg = $("graph");
  svg.replaceChildren();
  const positions = new Map(),
    edges = [],
    layers = [[], [], []];
  function visit(id, depth, ancestors) {
    if (positions.has(id)) return;
    const col = Math.min(depth, 2);
    positions.set(id, col);
    layers[col].push(id);
    if (ancestors.has(id)) return;
    const f = facts["requirement:" + id];
    if (!f || !f.value) return;
    for (const input of f.value.inputs) {
      const edge = facts[input];
      if (!edge?.value) continue;
      const target = edge.value.provider.split(":").slice(1).join(":");
      edges.push([id, target]);
      visit(target, depth + 1, new Set([...ancestors, id]));
    }
  }
  visit(req, 0, new Set());
  const coords = new Map();
  layers.forEach((list, col) =>
    list.forEach((id, i) =>
      coords.set(id, [25 + (2 - col) * 257, 30 + i * 78]),
    ),
  );
  const height = Math.max(250, ...layers.map((l) => l.length * 78 + 45));
  svg.style.height = height + "px";
  function s(tag, attrs, text) {
    const e = document.createElementNS("http://www.w3.org/2000/svg", tag);
    for (const [k, v] of Object.entries(attrs)) e.setAttribute(k, v);
    if (text) e.textContent = text;
    return e;
  }
  const lines = s("svg", {
    viewBox: `0 0 795 ${height}`,
    "aria-hidden": "true",
  });
  svg.append(lines);
  edges.forEach(([a, b]) => {
    const [x, y] = coords.get(a),
      [u, v] = coords.get(b);
    lines.append(
      s("line", { x1: x + 110, y1: y + 25, x2: u + 110, y2: v + 25 }),
    );
  });
  for (const [id, [x, y]] of coords) {
    const f =
      facts["system:" + id] ||
      facts["requirement:" + id] ||
      facts["integration:" + id];
    const prefix =
      f?.kind === "system"
        ? "sys:"
        : f?.kind === "integration"
          ? "int:"
          : "req:";
    const state = active.node_states[prefix + id] || "UNKNOWN";
    const g = el("button", undefined, "graph-node " + state);
    g.setAttribute("aria-label", "Inspect " + id);
    g.style.left = x + "px";
    g.style.top = y + "px";
    g.append(el("span", id), el("small", state));
    const inspect = () => {
      const d = $("node-detail");
      d.replaceChildren(
        el("strong", id),
        el("div", f?.kind || "Missing evidence"),
        detail(
          "Authoritative claim & assertion IDs",
          f || {
            state: "UNKNOWN",
            reason: "Declared identity without collected inventory",
          },
        ),
      );
    };
    g.addEventListener("click", inspect);
    svg.append(g);
  }
}
function impact() {
  active = data.versions.find((v) => v.id === $("system").value);
  if (!active) return;
  const a = active.assessment;
  const box = $("impact-summary");
  box.replaceChildren();
  const supported = Object.values(a.requirements).filter(
    (r) => r.state === "SUPPORTED",
  ).length;
  for (const [n, label] of [
    [a.failed_requirements.length, "Unsupported requirements"],
    [a.unknown_requirements.length, "Unknown requirements"],
    [supported, "Supported within scope"],
  ]) {
    const d = el("div");
    d.append(el("strong", String(n)), el("p", label));
    box.append(d);
  }
  renderResults($("requirements"), a);
  $("requirement").replaceChildren();
  for (const [id, r] of Object.entries(a.requirements))
    option($("requirement"), id, r.label);
  graph();
}
function review() {
  const v = data.versions[Number($("proposal").value)],
    root = $("review");
  root.replaceChildren();
  const card = el("div", undefined, "panel");
  card.append(
    badge(v.state),
    el("h2", v.proposal.title),
    el(
      "p",
      `Revision ${v.revision} · ${v.proposal.change_kind} · ${v.proposal.companies.join(" / ")}`,
      "hint",
    ),
  );
  const gates = el("div", undefined, "gate-list");
  for (const [k, value] of Object.entries(v.gates.checks)) {
    const g = el("div", undefined, "gate");
    g.append(
      el("span", k.replaceAll("_", " ")),
      badge(value ? "PASS" : "FAIL"),
    );
    gates.append(g);
  }
  card.append(
    gates,
    detail("Gate findings", v.gates),
    detail("Exact proposed architecture changes", v.proposal.actions),
  );
  const history = el("div", undefined, "panel");
  history.append(el("h2", "Recorded review history"));
  if (!v.decisions.length)
    history.append(
      el(
        "p",
        "No decision recorded. Browser visitors cannot submit approvals.",
        "hint",
      ),
    );
  else
    for (const d of v.decisions)
      history.append(
        badge(d.decision === "ACCEPT" ? "ACCEPTED" : "REJECTED"),
        el("p", d.reason),
        el("p", d.principal + " · " + d.recorded_at, "hint"),
      );
  history.append(
    el(
      "p",
      "A new evidence snapshot, expired evidence or a later revision invalidates the current acceptance. Prior decisions remain in the ledger.",
      "hint",
    ),
  );
  const panel = el("div", undefined, "panel");
  panel.append(el("h2", "Requirement outcomes"));
  const wrap = el("div", undefined, "table-scroll"),
    t = el("table"),
    head = el("thead"),
    tr = el("tr");
  ["Requirement", "Before", "After", "Proof"].forEach((x) =>
    tr.append(el("th", x)),
  );
  head.append(tr);
  const body = el("tbody");
  renderResults(body, v.assessment);
  t.append(head, body);
  wrap.append(t);
  panel.append(
    wrap,
    detail("Persisted assessment with content identity", v.assessment),
  );
  root.append(card, history, panel);
}
function evidence() {
  const grid = el("div", undefined, "source-grid");
  for (const a of data.snapshot.artifacts) {
    const card = el("div", undefined, "panel");
    card.append(
      el("h3", a.source.toUpperCase()),
      badge(a.status === "complete" ? "SUPPORTED" : "UNKNOWN"),
      el("p", `Revision ${a.revision} · collected ${a.collected_at}`),
      el("p", "Scope: " + a.scope.join(" / ")),
      el(
        "p",
        "Authority: " +
          Object.entries(data.snapshot.policy.types)
            .filter(([, v]) => v.sources.includes(a.source))
            .map(([k]) => k)
            .join(", "),
      ),
      detail("Artifact identity and collection metadata", a),
    );
    grid.append(card);
  }
  $("sources").replaceChildren(grid);
  for (const [key, f] of Object.entries(data.snapshot.facts)) {
    if (f.state === "UNKNOWN")
      $("conflicts").append(
        detail(key, {
          ...f,
          assertions: data.snapshot.assertions.filter((a) =>
            f.evidence.includes(a.id),
          ),
        }),
      );
  }
  $("conflicts").append(
    detail(
      "Collection coverage and seasonal exclusions",
      data.snapshot.manifests,
    ),
  );
}
document.querySelectorAll("[data-tab]").forEach((b) =>
  b.addEventListener("click", () => {
    document.body.dataset.view = b.dataset.tab;
    document
      .querySelectorAll(".tab")
      .forEach((s) => (s.hidden = s.id !== b.dataset.tab));
    document
      .querySelectorAll("[data-tab]")
      .forEach((x) => x.setAttribute("aria-pressed", String(x === b)));
  }),
);
$("system").addEventListener("change", impact);
$("requirement").addEventListener("change", graph);
$("proposal").addEventListener("change", review);
$("download").addEventListener("click", () => {
  const blob = new Blob([JSON.stringify(data, null, 2)], {
      type: "application/json",
    }),
    url = URL.createObjectURL(blob),
    a = el("a");
  a.href = url;
  a.download = "synthetic-estate-record.json";
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
});
fetch("/api/estate")
  .then((r) => {
    if (!r.ok) throw new Error("unavailable");
    return r.json();
  })
  .then((d) => {
    data = d;
    $("status").textContent =
      `Published snapshot ${d.snapshot.id.slice(0, 16)} · ${d.evidence_current ? "Evidence within review period" : "Evidence expired: all reviews stale"} · immutable source lineage`;
    const facts = Object.values(d.snapshot.facts);
    for (const [n, label] of [
      [facts.filter((f) => f.kind === "system").length, "Collected systems"],
      [
        facts.filter((f) => f.kind === "requirement").length,
        "Business requirements",
      ],
      [
        facts.filter((f) => f.state === "UNKNOWN").length,
        "Unresolved fact groups",
      ],
      [
        d.versions.filter((v) => !v.id.startsWith("explore:")).length,
        "Proposal revisions",
      ],
    ]) {
      const c = el("div", undefined, "metric");
      c.append(el("strong", String(n)), el("span", label));
      $("metrics").append(c);
    }
    d.versions.forEach((v, i) => {
      if (v.id.startsWith("explore:"))
        option(
          $("system"),
          v.id,
          v.proposal.title.replace("Retirement impact: ", ""),
        );
      else
        option(
          $("proposal"),
          String(i),
          `${v.proposal.title} · v${v.revision}`,
        );
    });
    $("system").value = "explore:atlas/workbench";
    impact();
    review();
    evidence();
  })
  .catch(() => {
    document.querySelectorAll(".tab").forEach((s) => (s.hidden = true));
    document.querySelectorAll("[data-tab]").forEach((b) => (b.disabled = true));
    $("status").textContent =
      "Evidence unavailable. No readiness conclusion can be established.";
  });
