const $ = (selector) => document.querySelector(selector);
let savedOnly = false;
let query = "";
let timer;

const escapeHtml = (value) => String(value || "").replace(/[&<>"']/g, (char) => ({
  "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
}[char]));

function toast(message) {
  const element = $("#toast");
  element.textContent = message;
  element.classList.add("show");
  setTimeout(() => element.classList.remove("show"), 2600);
}

function formatDate(value) {
  if (!value) return "Date unavailable";
  const date = new Date(value);
  return Number.isNaN(+date) ? "Date unavailable" : new Intl.DateTimeFormat("en-GB", {
    day: "numeric", month: "short", year: "numeric",
  }).format(date);
}

async function api(url, body) {
  const response = await fetch(url, body ? {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body),
  } : {});
  const result = await response.json();
  if (!response.ok) throw Error(result.error || result.detail || "Request failed");
  return result;
}

async function load() {
  try {
    const result = await api(`/api/datasets?q=${encodeURIComponent(query)}&saved=${savedOnly}`);
    render(result.items);
    $("#total").textContent = result.stats.total;
    $("#saved").textContent = result.stats.saved;
    $("#savedNav").textContent = result.stats.saved;
    $("#updated").textContent = result.stats.updated ? formatDate(result.stats.updated) : "Not yet";
  } catch (error) { toast(error.message); }
}

function render(items) {
  $("#countLabel").textContent = `${items.length} dataset${items.length === 1 ? "" : "s"}${query ? " matching your search" : ""}`;
  $("#empty").style.display = items.length ? "none" : "block";
  $("#items").innerHTML = items.map((item) => `<article class="card"><div>
    <div class="card-top"><span class="tag">${escapeHtml(item.category || "Open data")}</span><span class="date">Updated ${formatDate(item.modified)}</span></div>
    <h3>${escapeHtml(item.title)}</h3><p>${escapeHtml(item.description || "This dataset is available through Poland’s public open data catalogue. Explore the source for full documentation and available resources.")}</p>
    <div class="card-foot"><span>Publisher ID: ${escapeHtml(item.organization || "Public catalogue")}</span>${JSON.parse(item.keywords || "[]").slice(0, 3).map((word) => `<span>· ${escapeHtml(word)}</span>`).join("")}</div>
    </div><div class="card-actions"><button class="icon-button ${item.saved ? "saved" : ""}" title="Save signal" onclick="save('${escapeHtml(item.id)}',${!item.saved})">${item.saved ? "◆" : "◇"}</button>
    <button class="ai-button" onclick="analyze('${escapeHtml(item.id)}',this)">✳ Analyze</button><a class="icon-button" style="display:grid;place-items:center;text-decoration:none" title="Open source" href="${escapeHtml(item.url)}" target="_blank" rel="noreferrer">↗</a></div>
    ${item.analysis ? `<div class="analysis">${escapeHtml(item.analysis)}</div>` : ""}</article>`).join("");
}

async function save(id, saved) {
  try { await api("/api/save", { id, saved }); await load(); }
  catch (error) { toast(error.message); }
}

async function analyze(id, button) {
  button.disabled = true;
  button.textContent = "Thinking…";
  try { await api("/api/analyze", { id }); toast("Evidence review saved"); await load(); }
  catch (error) { toast(error.message); }
  finally { button.disabled = false; button.textContent = "✳ Analyze"; }
}

$("#sync").onclick = async () => {
  const button = $("#sync");
  button.disabled = true;
  button.innerHTML = "<span>⟳</span> Searching catalogue…";
  try {
    const result = await api("/api/sync", { query });
    toast(`Loaded ${result.count} public datasets`);
    await load();
  } catch (error) { toast(error.message); }
  finally { button.disabled = false; button.innerHTML = "<span>⟳</span> Refresh signals"; }
};

$("#investigateButton").onclick = async () => {
  const input = $("#investigateQuery");
  const output = $("#investigationResult");
  const button = $("#investigateButton");
  if (input.value.trim().length < 3) { toast("Enter a question with at least 3 characters"); return; }
  button.disabled = true;
  button.textContent = "Retrieving evidence…";
  output.hidden = false;
  output.textContent = "Finding relevant public records and preparing a cited brief…";
  try {
    const result = await api("/api/investigate", { query: input.value.trim(), top_k: 5 });
    output.innerHTML = `<div class="investigation-report">${escapeHtml(result.report).replace(/\n/g, "<br>")}</div>
      <div class="investigation-sources"><strong>Retrieved sources</strong>${result.sources.map((source, index) =>
      `<a href="${escapeHtml(source.url)}" target="_blank" rel="noreferrer">[${index + 1}] ${escapeHtml(source.title)} · similarity ${source.similarity.toFixed(2)} ↗</a>`).join("")}</div>`;
  } catch (error) { output.textContent = error.message; toast(error.message); }
  finally { button.disabled = false; button.innerHTML = "Investigate <span>→</span>"; }
};

$("#search").oninput = (event) => {
  query = event.target.value;
  clearTimeout(timer);
  timer = setTimeout(load, 350);
};
$("#allFilter").onclick = () => setFilter(false);
$("#savedFilter").onclick = () => setFilter(true);
function setFilter(value) {
  savedOnly = value;
  $("#allFilter").classList.toggle("active", !value);
  $("#savedFilter").classList.toggle("active", value);
  $("#listTitle").textContent = value ? "Saved signals" : "Latest public signals";
  load();
}
document.querySelectorAll(".nav").forEach((button) => button.onclick = () => setFilter(button.dataset.view === "saved"));
document.addEventListener("keydown", (event) => {
  if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
    event.preventDefault(); $("#search").focus();
  }
});
load();
