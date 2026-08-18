const form = document.querySelector("#scan-form");
const scanButton = document.querySelector("#scan-button");
const downloadButton = document.querySelector("#download-button");
const resultTitle = document.querySelector("#result-title");
const findingsBody = document.querySelector("#findings-body");

let lastResult = null;

function setText(id, value) {
  document.querySelector(id).textContent = value;
}

function renderResult(result) {
  lastResult = result;
  const findings = result.findings || [];
  const counts = result.counts || {};

  resultTitle.textContent = findings.length ? "Findings detected" : "No findings";
  setText("#files-count", result.files_scanned ?? 0);
  setText("#finding-count", findings.length);
  setText("#elapsed", `${result.elapsed_sec ?? 0}s`);
  setText("#critical-count", counts.Critical ?? 0);
  setText("#high-count", counts.High ?? 0);
  setText("#medium-count", counts.Medium ?? 0);
  setText("#low-count", counts.Low ?? 0);

  if (!findings.length) {
    findingsBody.innerHTML = '<tr><td colspan="6" class="empty">No matching credentials were found.</td></tr>';
  } else {
    findingsBody.innerHTML = findings.map((finding) => `
      <tr>
        <td>${escapeHtml(finding.severity || "")}</td>
        <td>${escapeHtml(finding.rule || "")}</td>
        <td>${escapeHtml(formatConfidence(finding.confidence))}</td>
        <td>${escapeHtml(finding.file || "")}</td>
        <td>${escapeHtml(finding.line || "")}</td>
        <td>${escapeHtml(finding.redacted || finding.value || "")}</td>
      </tr>
    `).join("");
  }

  downloadButton.disabled = false;
}

function formatConfidence(value) {
  if (value === undefined || value === null || value === "") return "";
  return `${Number(value)}%`;
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  scanButton.disabled = true;
  scanButton.textContent = "Scanning...";
  resultTitle.textContent = "Scanning";
  findingsBody.innerHTML = '<tr><td colspan="6" class="empty">Scanning uploaded evidence...</td></tr>';

  const data = new FormData(form);
  data.set("safe", form.safe.checked ? "true" : "false");

  try {
    const response = await fetch("/api/scan", { method: "POST", body: data });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.error || "Scan failed");
    renderResult(payload);
  } catch (error) {
    resultTitle.textContent = "Scan failed";
    findingsBody.innerHTML = `<tr><td colspan="6" class="empty">${escapeHtml(error.message)}</td></tr>`;
  } finally {
    scanButton.disabled = false;
    scanButton.textContent = "Run scan";
  }
});

downloadButton.addEventListener("click", () => {
  if (!lastResult) return;
  const blob = new Blob([JSON.stringify(lastResult, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = "credaudit-findings.json";
  anchor.click();
  URL.revokeObjectURL(url);
});
