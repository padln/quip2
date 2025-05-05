document.addEventListener("DOMContentLoaded", () => {
  const countEl = document.getElementById("count");
  const resetBtn = document.getElementById("reset");
  const debugLogEl = document.getElementById("debugLog");

  // Load detection count
  chrome.storage.local.get(["aiCount"], (data) => {
    countEl.textContent = data.aiCount || 0;
  });

  // Reset button
  resetBtn.addEventListener("click", () => {
    chrome.storage.local.set({ aiCount: 0 }, () => {
      countEl.textContent = 0;
    });
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      chrome.tabs.sendMessage(tabs[0].id, "resetCount");
    });
  });

  // Load debug logs
  chrome.storage.local.get(["quipLogs"], (data) => {
    const logs = data.quipLogs || [];
    debugLogEl.textContent = logs.join("\n");
  });

  // Tab switching
  document.querySelectorAll(".tab").forEach(tab => {
    tab.addEventListener("click", () => {
      document.querySelectorAll(".tab").forEach(t => t.classList.remove("active"));
      document.querySelectorAll(".tab-content").forEach(c => c.classList.remove("active"));

      tab.classList.add("active");
      document.getElementById(tab.dataset.tab).classList.add("active");
    });
  });
});