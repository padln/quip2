document.addEventListener("DOMContentLoaded", () => {
    const statusEl = document.getElementById("status");
    const toggleBtn = document.getElementById("toggle");
    const countEl = document.getElementById("ai-count");
  
    chrome.storage.local.get(["detectionEnabled", "aiCount"], (data) => {
      const enabled = data.detectionEnabled !== false;
      statusEl.textContent = enabled ? "Extension is active" : "Extension is disabled";
      toggleBtn.textContent = enabled ? "Disable Detection" : "Enable Detection";
      countEl.textContent = data.aiCount || 0;
    });
  
    toggleBtn.addEventListener("click", () => {
      chrome.storage.local.get(["detectionEnabled"], (data) => {
        const newState = !(data.detectionEnabled !== false);
        chrome.storage.local.set({ detectionEnabled: newState }, () => {
          statusEl.textContent = newState ? "Extension is active" : "Extension is disabled";
          toggleBtn.textContent = newState ? "Disable Detection" : "Enable Detection";
        });
      });
    });
  });