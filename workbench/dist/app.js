"use strict";

const byId = (name) => document.getElementById(name);
const panels = ["solve", "verify", "evidence", "review"];
const money = new Intl.NumberFormat("en-US");
let meta;
let cells = [];
let matrixRevision = 0;
let certificateRevision = 0;
let automaticCertificateRevision = -1;
let currentProof;

function node(tag, text, className) {
  const el = document.createElement(tag);
  if (text !== undefined) el.textContent = text;
  if (className) el.className = className;
  return el;
}

async function api(path, body) {
  const options = body === undefined ? undefined : {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body),
  };
  const response = await fetch(path, options);
  const result = await response.json();
  if (!response.ok) throw new Error(result.error || `Request failed (${response.status})`);
  return result;
}

function message(id, text, bad = false) {
  const box = byId(id);
  box.textContent = text;
  box.hidden = !text;
  box.classList.toggle("bad", bad);
}

function svgNode(name, attrs = {}, label) {
  const element = document.createElementNS("http://www.w3.org/2000/svg", name);
  for (const [key, value] of Object.entries(attrs)) element.setAttribute(key, value);
  if (label !== undefined) element.textContent = label;
  return element;
}

function drawMatching(rows, cols, proof) {
  const svg = byId("route-graph");
  const height = Math.max(152, 40 + Math.max(rows, cols) * 29);
  const y = (i, size) => 28 + (height - 42) * (i + 0.5) / size;
  const matched = new Set(proof?.selected || []);
  const items = [svgNode("text", { x: 16, y: 20, class: "graph-head" }, "JOBS"),
    svgNode("text", { x: 349, y: 20, class: "graph-head" }, "RESOURCES")];
  svg.setAttribute("viewBox", `0 0 435 ${height}`);
  svg.setAttribute("aria-label", proof ? `Assignments: ${proof.selected.map((c, r) => `job ${r} to resource ${c}`).join(", ")}` : `${rows} jobs and ${cols} resources`);
  for (let i = 0; i < rows; i += 1) {
    items.push(svgNode("path", { d: `M 66 ${y(i, rows)} H 346`, class: "guide" }));
  }
  proof?.selected.forEach((col, row) => {
    const left = y(row, rows);
    const right = y(col, cols);
    items.push(svgNode("path", { d: `M 66 ${left} C 158 ${left} 245 ${right} 346 ${right}`,
      class: row % 2 ? "route alt" : "route", pathLength: 1 }));
    const cost = proof.matrix[row][col];
    if (rows <= 6 && cost.length <= 8) {
      items.push(svgNode("text", { x: 148, y: left - 5, class: "route-cost" }, cost));
    }
  });
  for (let r = 0; r < rows; r += 1) {
    items.push(svgNode("text", { x: 16, y: y(r, rows) + 4 }, `J${r}`),
      svgNode("circle", { cx: 66, cy: y(r, rows), r: 5, class: `vertex${proof ? " matched" : ""}` }));
  }
  for (let c = 0; c < cols; c += 1) {
    const state = matched.has(c) ? " matched" : proof ? " unmatched" : "";
    items.push(svgNode("circle", { cx: 346, cy: y(c, cols), r: 5, class: `vertex${state}` }),
      svgNode("text", { x: 364, y: y(c, cols) + 4 }, `R${c}`));
  }
  svg.replaceChildren(...items);
}

function runStage(stage) {
  byId("run-steps").querySelectorAll("[data-step]").forEach((step, index) => {
    step.classList.toggle("done", index < stage);
    step.classList.toggle("active", index === stage && stage > 0);
  });
}

function updateSlack() {
  if (!currentProof) return;
  const r = Number(byId("proof-job").value);
  const c = Number(byId("proof-resource").value);
  const cost = BigInt(currentProof.matrix[r][c]);
  const potential = BigInt(currentProof.u[r]) + BigInt(currentProof.v[c]);
  const relation = currentProof.selected[r] === c ? " · selected edge" : "";
  message("edge-slack", `Cost ${cost} − potential ${potential} = slack ${cost - potential}${relation}`);
}

function renderProof(proof, isLive) {
  currentProof = proof;
  const u = proof.u.map(BigInt);
  const v = proof.v.map(BigInt);
  const selected = new Set(proof.selected);
  const bound = [...u, ...v].reduce((sum, value) => sum + value, 0n);
  const allEdges = proof.u.length * proof.v.length;
  const feasible = proof.matrix.reduce((count, row, r) => count + row.filter((cost, c) => u[r] + v[c] <= BigInt(cost)).length, 0);
  const tight = proof.selected.filter((c, r) => u[r] + v[c] === BigInt(proof.matrix[r][c])).length;
  const nonpositive = v.filter((value) => value <= 0n).length;
  const unused = v.length - selected.size;
  const zeroUnused = v.filter((value, c) => !selected.has(c) && value === 0n).length;
  byId("bound").textContent = bound.toString();
  byId("bound-label").textContent = `Dual lower bound · selected cost ${proof.total}`;
  byId("proof-source").textContent = isLive ? "Certificate accepted by the Fe verifier." : "Recorded example. Run Verify to inspect a different certificate.";
  const checks = [[`${feasible}/${allEdges}`, "Feasible edges"], [`${tight}/${u.length}`, "Tight selected edges"],
    [`${nonpositive}/${v.length}`, "Nonpositive columns"], [`${zeroUnused}/${unused}`, "Unused columns at zero"]];
  byId("proof-checks").replaceChildren(...checks.map(([score, text]) => {
    const item = node("div");
    item.append(node("strong", score), node("span", text));
    return item;
  }));
  byId("proof-job").replaceChildren(...proof.u.map((_, i) => node("option", String(i))));
  byId("proof-resource").replaceChildren(...proof.v.map((_, i) => node("option", String(i))));
  byId("proof-resource").value = String(proof.selected[0]);
  byId("proof-edges").replaceChildren(...proof.selected.map((c, r) => {
    const edge = node("div", undefined, "edge-proof");
    edge.append(node("span", `J${r} → R${c}`), node("code", `${proof.u[r]} + (${proof.v[c]}) = ${proof.matrix[r][c]}`));
    return edge;
  }));
  updateSlack();
}

function clearResult() {
  matrixRevision += 1;
  const values = matrixValues();
  const recorded = meta && JSON.stringify(values) === JSON.stringify(meta.sample.matrix);
  byId("live-result").hidden = true;
  byId("sample-result").hidden = !recorded;
  byId("empty-result").hidden = Boolean(recorded);
  byId("result-label").textContent = recorded ? "RECORDED SAMPLE" : "AWAITING RUN";
  byId("result-label").classList.remove("live");
  cells.flat().forEach((input) => input.classList.remove("selected"));
  message("solve-error", "");
  byId("solve-status").textContent = "";
  runStage(0);
  drawMatching(values.length, values[0].length, recorded ? meta.sample : null);
}

function renderMatrix(values) {
  const table = byId("matrix");
  const header = node("thead");
  const top = node("tr");
  top.append(node("th", "Job / Resource"));
  const columns = values[0].length;
  for (let c = 0; c < columns; c += 1) {
    const th = node("th", `R${c}`);
    th.scope = "col";
    top.append(th);
  }
  header.append(top);
  const body = node("tbody");
  cells = values.map((row, r) => {
    const tr = node("tr");
    const th = node("th", `Job ${r}`);
    th.scope = "row";
    tr.append(th);
    const inputs = row.map((value, c) => {
      const input = node("input");
      input.type = "text";
      input.inputMode = "text";
      input.maxLength = 20;
      input.value = value;
      input.setAttribute("aria-label", `Cost from job ${r} to resource ${c}`);
      const td = node("td");
      td.append(input);
      tr.append(td);
      return input;
    });
    body.append(tr);
    return inputs;
  });
  table.querySelectorAll("thead,tbody").forEach((part) => part.remove());
  table.append(header, body);
  byId("rows").value = values.length;
  byId("cols").value = columns;
  byId("shape").textContent = `${values.length} × ${columns}`;
  clearResult();
}

function checkedCost(text) {
  if (!/^-?[0-9]{1,19}$/.test(text)) return false;
  const value = BigInt(text);
  return value >= -(2n ** 63n) && value < 2n ** 63n;
}

function matrixValues() {
  return cells.map((row) => row.map((input) => input.value.trim()));
}

function validShape(rows, columns) {
  return Number.isInteger(rows) && Number.isInteger(columns) && rows >= 1 && rows <= columns && columns <= 32;
}

function resizeMatrix() {
  const rows = Number(byId("rows").value);
  const cols = Number(byId("cols").value);
  if (!validShape(rows, cols)) return message("solve-error", "Use 1 ≤ jobs ≤ resources ≤ 32.");
  const before = matrixValues();
  loadPreset(null, Array.from({ length: rows }, (_, r) => Array.from({ length: cols }, (_, c) => before[r]?.[c] ?? "0")));
}

function pasteMatrix() {
  const values = byId("matrix-text").value.trim().split(/\r?\n/).map((line) => line.trim().split(/[\t ,]+/));
  const cols = values[0].length;
  if (!validShape(values.length, cols) || values.some((row) => row.length !== cols || row.some((value) => !checkedCost(value)))) {
    return message("solve-error", "Use one row per line, with the same number of signed i64 costs in every row.");
  }
  loadPreset(null, values);
}

function certificateChanged() {
  certificateRevision += 1;
  message("verify-status", "");
  if (currentProof) byId("proof-source").textContent = "The diagram shows the last displayed valid proof. Run Verify to check the editor.";
}

function setCertificate(text) {
  byId("certificate").value = text;
  certificateChanged();
}

function showResult(result) {
  const { proof, verification } = result;
  const entries = proof.selected.map((col, row) => {
    cells[row][col].classList.add("selected");
    const line = node("div", undefined, "choice");
    line.append(node("span", `Job ${row} → Resource ${col}`), node("code", proof.matrix[row][col]));
    return line;
  });
  byId("total").textContent = proof.total;
  byId("assignment").replaceChildren(...entries);
  byId("sample-result").hidden = true;
  byId("empty-result").hidden = true;
  byId("live-result").hidden = false;
  byId("result-label").textContent = "LIVE FE RESULT";
  byId("result-label").classList.add("live");
  message("live-verification", verification.output.trim(), false);
  byId("solve-status").textContent = `Minimum cost ${proof.total}. Fe certificate verified. Load solver certificate to inspect the proof.`;
  drawMatching(proof.matrix.length, proof.matrix[0].length, proof);
  runStage(3);
  const loadSolvedCertificate = () => {
    setCertificate(result.output);
    automaticCertificateRevision = certificateRevision;
    renderProof(proof, true);
  };
  byId("open-certificate").onclick = (event) => {
    event.preventDefault();
    loadSolvedCertificate();
    location.hash = "verify";
    showPanel();
    byId("certificate").focus();
  };
  if (certificateRevision === automaticCertificateRevision) loadSolvedCertificate();
}

async function solve(event) {
  event.preventDefault();
  const button = byId("run");
  if (button.disabled || button.getAttribute("aria-disabled") === "true") return;
  const matrix = matrixValues();
  if (Number(byId("rows").value) !== matrix.length || Number(byId("cols").value) !== matrix[0].length) {
    return message("solve-error", "Apply the new dimensions with Resize before running.");
  }
  if (matrix.some((row) => row.some((value) => !checkedCost(value)))) {
    return message("solve-error", "Every cell needs a signed i64 integer (−9223372036854775808 through 9223372036854775807).");
  }
  clearResult();
  const revision = matrixRevision;
  button.setAttribute("aria-disabled", "true");
  const label = button.textContent;
  button.textContent = "Running Fe…";
  byId("solve-status").textContent = "Running Fe solver.";
  byId("result-label").textContent = "RUNNING FE";
  runStage(1);
  try {
    const result = await api("/api/solve", { matrix });
    if (revision !== matrixRevision) return;
    if (result.exitCode || result.verification?.exitCode !== 0) {
      throw new Error(result.diagnostic || result.verification?.diagnostic || "Fe could not produce a verified result.");
    }
    showResult(result);
  } catch (error) {
    if (revision === matrixRevision) {
      clearResult();
      message("solve-error", error.message);
    }
  } finally {
    button.textContent = label;
    button.removeAttribute("aria-disabled");
  }
}

async function verify(event) {
  event.preventDefault();
  const button = byId("verify-button");
  if (button.disabled || button.getAttribute("aria-disabled") === "true") return;
  const revision = certificateRevision;
  button.setAttribute("aria-disabled", "true");
  message("verify-status", "Checking with Fe…");
  try {
    const result = await api("/api/verify", { certificate: byId("certificate").value });
    if (revision !== certificateRevision) return;
    const output = result.exitCode ? `Rejected (exit ${result.exitCode}) · ${result.diagnostic}` : result.output.trim();
    message("verify-status", output, result.exitCode !== 0);
    if (result.exitCode === 0) renderProof(result.proof, true);
  } catch (error) {
    if (revision === certificateRevision) message("verify-status", error.message, true);
  } finally {
    button.removeAttribute("aria-disabled");
  }
}

const receiptNames = { deploy: "Deploy board", "invalid-certificate": "Duplicate column", "different-matrix": "Different problem", "record-result": "Record result", repeat: "Repeat result" };

function renderEvidence() {
  const s = meta.summary;
  const full = meta.runMode === "full";
  const failures = meta.receipts.filter((receipt) => receipt.stateUnchanged).length;
  const values = full ? [[meta.stages, "Reproduction stages"], [2 * s.common_fe_functions_per_backend + s.evm_board_functions, "Fe function passes"],
    [s.roundtrips, "Certificate roundtrips"], [s.demo_transactions + s.full32_campaign_transactions + s.abi_campaign_transactions, "Local receipts"]] :
    [[meta.receipts.length, "Demo receipts"], [failures, "State-preserving rejections"], [Number(meta.sample.total), "Certified example cost"], [meta.greedy, "Row-order greedy cost"]];
  byId("run-mode").textContent = full ? "Complete reproduction" : "Verified normal demo";
  byId("run-record-label").textContent = full ? "Full reproduction record" : "Normal demo record";
  byId("evidence-scope").textContent = full ? "Normal demo receipts from the complete reproduction. Each rejection preserved all 34 observed storage slots." :
    "These receipts come from the normal demo. Each rejection preserved all 34 observed storage slots. The reproduction guide covers the broader checks.";
  byId("metrics").replaceChildren(...values.map(([value, text]) => {
    const card = node("div", undefined, "metric");
    card.append(node("strong", money.format(value)), node("span", text));
    return card;
  }));
  byId("receipts").replaceChildren(...meta.receipts.flatMap((receipt, index) => {
    const tr = node("tr");
    const action = node("td");
    const button = node("button", `${receiptNames[receipt.label] || receipt.label} ▾`, "receipt-action");
    button.type = "button";
    button.setAttribute("aria-expanded", "false");
    const details = node("tr", undefined, "receipt-detail");
    details.id = `receipt-detail-${index}`;
    details.hidden = true;
    button.setAttribute("aria-controls", details.id);
    const cell = node("td");
    cell.colSpan = 4;
    cell.append(node("strong", "Local transaction hash"), node("code", receipt.hash));
    details.append(cell);
    button.addEventListener("click", () => {
      details.hidden = !details.hidden;
      button.setAttribute("aria-expanded", String(!details.hidden));
    });
    action.append(button);
    tr.append(action,
      node("td", receipt.status ? "Accepted" : "Reverted", receipt.status ? "accepted" : "reverted"),
      node("td", money.format(receipt.gas)), node("td", receipt.stateUnchanged ? "34 slots unchanged" : "—"));
    return [tr, details];
  }));
}

async function refreshNotes() {
  try {
    const { notes } = await api("/api/feedback");
    const items = notes.slice().reverse().map((note) => {
      const article = node("article", undefined, "note");
      const time = node("time", `${new Date(note.recordedUtc).toLocaleString()} · ${note.sourceCommit.slice(0, 7)}`);
      time.dateTime = note.recordedUtc;
      const text = node("p", note.text);
      text.dir = "auto";
      article.append(node("strong", note.topic), time, text);
      return article;
    });
    byId("notes").replaceChildren(...(items.length ? items : [node("p", "No review notes yet.", "muted")]));
  } catch (error) {
    byId("notes").replaceChildren(node("p", error.message, "alert"));
  }
}

async function saveNote(event) {
  event.preventDefault();
  const button = byId("save-note");
  if (button.disabled || button.getAttribute("aria-disabled") === "true") return;
  const text = byId("feedback").value.trim();
  if (!text) return message("note-status", "Write a review finding first.", true);
  button.setAttribute("aria-disabled", "true");
  message("note-status", "Saving locally…");
  try {
    await api("/api/feedback", { topic: byId("topic").value, text });
    if (byId("feedback").value.trim() === text) byId("feedback").value = "";
    message("note-status", "Review note saved on this device.");
    await refreshNotes();
  } catch (error) {
    message("note-status", error.message, true);
  } finally {
    button.removeAttribute("aria-disabled");
  }
}

function showPanel() {
  const hash = location.hash.slice(1);
  const panel = panels.includes(hash) ? hash : "solve";
  for (const name of panels) {
    byId(`view-${name}`).hidden = name !== panel;
    const link = document.querySelector(`.nav a[href="#${name}"]`);
    if (name === panel) link.setAttribute("aria-current", "page");
    else link.removeAttribute("aria-current");
  }
  if (panel === "review") refreshNotes();
}

function loadPreset(id, matrix) {
  document.querySelectorAll(".preset").forEach((button) => {
    button.setAttribute("aria-pressed", String(button.id === id));
  });
  renderMatrix(matrix);
}

async function init() {
  renderMatrix([["1", "2", "9"], ["1", "100", "3"]]);
  const initialMatrixRevision = matrixRevision;
  showPanel();
  window.addEventListener("hashchange", showPanel);
  const motion = byId("motion");
  motion.addEventListener("click", () => {
    const paused = document.documentElement.toggleAttribute("data-motion-paused");
    motion.setAttribute("aria-pressed", String(paused));
    motion.textContent = paused ? "Resume motion" : "Pause motion";
  });
  byId("matrix").addEventListener("input", () => {
    document.querySelectorAll(".preset").forEach((button) => button.setAttribute("aria-pressed", "false"));
    clearResult();
  });
  byId("resize").addEventListener("click", resizeMatrix);
  byId("apply-paste").addEventListener("click", pasteMatrix);
  byId("solve-form").addEventListener("submit", solve);
  byId("verify-form").addEventListener("submit", verify);
  byId("feedback-form").addEventListener("submit", saveNote);
  byId("proof-job").addEventListener("change", updateSlack);
  byId("proof-resource").addEventListener("change", updateSlack);
  byId("certificate").addEventListener("input", certificateChanged);
  byId("copy").addEventListener("click", async () => {
    try {
      await navigator.clipboard.writeText(byId("certificate").value);
      message("verify-status", "Certificate copied.");
    } catch {
      byId("certificate").focus();
      byId("certificate").select();
      message("verify-status", "Certificate selected. Use your browser’s copy command.");
    }
  });
  try {
    meta = await api("/api/meta");
    byId("commit").textContent = meta.commit.slice(0, 7);
    byId("commit").title = meta.commit;
    byId("compiler").textContent = meta.compiler;
    byId("sample-total").textContent = meta.sample.total;
    byId("greedy").textContent = meta.greedy;
    if (matrixRevision === initialMatrixRevision) renderMatrix(meta.sample.matrix);
    if (certificateRevision === 0 && !byId("certificate").value) {
      setCertificate(meta.certificate);
      automaticCertificateRevision = certificateRevision;
    }
    renderProof(meta.sample, false);
    renderEvidence();
    byId("packet-link").hidden = !meta.packageSha256;
    byId("sample").addEventListener("click", () => loadPreset("sample", meta.sample.matrix));
    byId("rectangular").addEventListener("click", () => loadPreset("rectangular", [["7", "2", "5", "3"], ["4", "6", "1", "8"], ["2", "7", "3", "6"]]));
    byId("signed").addEventListener("click", () => loadPreset("signed", [["-9223372036854775808", "9223372036854775807"], ["9223372036854775807", "-9223372036854775808"]]));
    byId("load-certificate").addEventListener("click", () => setCertificate(meta.certificate));
    byId("break-certificate").addEventListener("click", () => {
      const lines = meta.certificate.trimEnd().split("\n");
      const selectedLine = 2 + meta.sample.matrix.length;
      lines[selectedLine] = Array(meta.sample.matrix.length).fill(meta.sample.selected[0]).join(" ");
      setCertificate(lines.join("\n") + "\n");
      message("verify-status", "Example modified: two jobs now select the same column. Verify to test it.");
    });
    ["run", "verify-button", "save-note"].forEach((id) => { byId(id).disabled = false; });
  } catch (error) {
    message("load-error", `Could not load the validated candidate. ${error.message}`);
  }
}

init();
