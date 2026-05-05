const fileApiBase = "http://localhost:8000";

const dropZone = document.getElementById("dropZone");
const fileInput = document.getElementById("fileInput");
const uploadStatus = document.getElementById("uploadStatus");
const resultSection = document.getElementById("resultSection");
const resultFilename = document.getElementById("resultFilename");
const resultStatus = document.getElementById("resultStatus");
const driveLink = document.getElementById("driveLink");
const driveLinkHref = document.getElementById("driveLinkHref");
const resultError = document.getElementById("resultError");
const resetBtn = document.getElementById("resetBtn");
const statusLine = document.getElementById("statusLine");
const reportsTbody = document.getElementById("reportsTbody");
let isProcessing = false;

// ────────────────────────────────────────────────────────────────────────────
// Drag & Drop Handlers
// ────────────────────────────────────────────────────────────────────────────

dropZone.addEventListener("click", () => fileInput.click());

dropZone.addEventListener("dragover", (e) => {
  e.preventDefault();
  dropZone.classList.add("drag-over");
});

dropZone.addEventListener("dragleave", () => {
  dropZone.classList.remove("drag-over");
});

dropZone.addEventListener("drop", (e) => {
  e.preventDefault();
  dropZone.classList.remove("drag-over");
  const files = e.dataTransfer.files;
  if (files.length > 0) {
    handleFileSelect(files[0]);
  }
});

fileInput.addEventListener("change", (e) => {
  if (e.target.files.length > 0) {
    handleFileSelect(e.target.files[0]);
  }
});

// ────────────────────────────────────────────────────────────────────────────
// File Processing
// ────────────────────────────────────────────────────────────────────────────

async function handleFileSelect(file) {
  if (isProcessing) {
    return;
  }
  const validTypes = [".pdf", ".docx", ".xlsx", ".xls", ".txt"];
  const ext = "." + file.name.split(".").pop().toLowerCase();

  if (!validTypes.includes(ext)) {
    showUploadStatus("error", `❌ Invalid file type. Supported: PDF, DOCX, XLSX, XLS, TXT`);
    return;
  }

  isProcessing = true;
  setBusyState(true);
  resultSection.classList.add("hidden");
  showUploadStatus("loading", "📤 Uploading file...");

  try {
    // Upload file
    const formData = new FormData();
    formData.append("file", file);

    const uploadResp = await fetch(`${fileApiBase}/upload`, {
      method: "POST",
      body: formData,
    });

    if (!uploadResp.ok) {
      throw new Error(`Upload failed: ${uploadResp.statusText}`);
    }

    const uploadData = await uploadResp.json();
    if (!uploadData.success) {
      throw new Error(uploadData.error || "Upload failed");
    }

    showUploadStatus("loading", "⚙️ Processing with SOW agent... (this may take 30-60 seconds)");

    // Process the uploaded file
    const processResp = await fetch(`${fileApiBase}/process`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        temp_path: uploadData.temp_path,
        file_type: uploadData.file_type,
      }),
    });

    if (!processResp.ok) {
      throw new Error(`Processing failed: ${processResp.statusText}`);
    }

    const result = await processResp.json();

    if (result.success && result.google_sheet_url) {
      showUploadStatus("success", "✅ Report generated successfully.");
      showResult(file.name, result.google_sheet_url);
      fetchReports();
    } else {
      showError(result.error || "Processing failed - no result returned");
    }
  } catch (error) {
    showError(error.message);
  } finally {
    isProcessing = false;
    setBusyState(false);
  }
}

function showUploadStatus(type, message) {
  uploadStatus.className = `status-banner ${type}`;
  uploadStatus.textContent = message;
  uploadStatus.classList.remove("hidden");
}

function showResult(filename, driveUrl) {
  resultFilename.textContent = filename;
  resultStatus.textContent = "✅ Successfully generated";
  driveLinkHref.href = driveUrl;
  driveLink.classList.remove("hidden");
  resultError.classList.add("hidden");
  resultSection.classList.remove("hidden");
  window.scrollTo({ top: resultSection.offsetTop - 100, behavior: "smooth" });
}

function showError(message) {
  resultError.textContent = `❌ ${message}`;
  resultError.classList.remove("hidden");
  driveLink.classList.add("hidden");
  resultSection.classList.remove("hidden");
  showUploadStatus("error", `❌ ${message}`);
}

function setBusyState(busy) {
  dropZone.classList.toggle("busy", busy);
  fileInput.disabled = busy;
}

resetBtn.addEventListener("click", () => {
  fileInput.value = "";
  resultSection.classList.add("hidden");
  uploadStatus.classList.add("hidden");
  dropZone.focus();
});

// ────────────────────────────────────────────────────────────────────────────
// Reports Table
// ────────────────────────────────────────────────────────────────────────────

function renderRows(files) {
  reportsTbody.innerHTML = "";
  if (!files.length) {
    const tr = document.createElement("tr");
    tr.innerHTML = '<td colspan="3" style="text-align: center; color: #999;">No reports yet.</td>';
    reportsTbody.appendChild(tr);
    return;
  }

  for (const file of files) {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${file.name}</td>
      <td>${file.size_kb}</td>
      <td><a href="${file.download_url}" target="_blank" rel="noreferrer">📥 Download</a></td>
    `;
    reportsTbody.appendChild(tr);
  }
}

async function fetchReports() {
  statusLine.textContent = "Loading...";
  try {
    const response = await fetch(`${fileApiBase}/list`);
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    const data = await response.json();
    statusLine.textContent = `✅ ${data.count} report(s) available`;
    renderRows(data.files || []);
  } catch (error) {
    statusLine.textContent = `⚠️ Could not reach file server (${error.message})`;
    renderRows([]);
  }
}

// ────────────────────────────────────────────────────────────────────────────
// Init & Polling
// ────────────────────────────────────────────────────────────────────────────

fetchReports();
setInterval(fetchReports, 15000);
