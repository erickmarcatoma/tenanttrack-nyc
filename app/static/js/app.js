// Register the service worker for offline support.
if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("/service-worker.js").catch(() => {});
  });
}

// Copy and download buttons on the letter page.
document.addEventListener("click", async (event) => {
  const copyBtn = event.target.closest("[data-copy]");
  if (copyBtn) {
    const field = document.querySelector(copyBtn.dataset.copy);
    const status = document.getElementById("letter-status");
    try {
      await navigator.clipboard.writeText(field.value);
    } catch {
      field.select();
      document.execCommand("copy");
    }
    if (status) status.textContent = copyBtn.dataset.copied || "Copied";
    return;
  }

  const dlBtn = event.target.closest("[data-download]");
  if (dlBtn) {
    const field = document.querySelector(dlBtn.dataset.download);
    const blob = new Blob([field.value], { type: "text/plain;charset=utf-8" });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = dlBtn.dataset.filename || "letter.txt";
    link.click();
    URL.revokeObjectURL(link.href);
  }
});
