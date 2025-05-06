// content.js (main entry point)
chrome.runtime.sendMessage("resetCount");

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request === "resetCount") {
    chrome.storage.local.set({ aiCount: 0 });
  }
});

document.querySelectorAll("img").forEach(handleImage);
observeNewImages(handleImage);

window.addEventListener("scroll", debounce(() => {
  document.querySelectorAll("img").forEach(handleImage);
}, 300)); // debounce function to limit the number of times handleImage is called

function logToStorage(message) {
  chrome.storage.local.get(["quipLogs"], (data) => {
    const logs = data.quipLogs || [];
    logs.push(`[${new Date().toISOString()}] ${message}`);
    if (logs.length > 100) logs.shift(); // keep it small, storage limited to 5MB
    chrome.storage.local.set({ quipLogs: logs });
  });
}

fetch("http://localhost:5050/ping")
  .then(res => {
    if (res.ok) logToStorage("Server reachable.");
    else logToStorage("Server responded with error.");
  })
  .catch(() => logToStorage("Server unreachable."));