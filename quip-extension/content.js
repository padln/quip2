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
}, 300));

function logToStorage(message) {
  chrome.storage.local.get(["quipLogs"], (data) => {
    const logs = data.quipLogs || [];
    logs.push(`[${new Date().toISOString()}] ${message}`);
    if (logs.length > 100) logs.shift(); // keep it small
    chrome.storage.local.set({ quipLogs: logs });
  });
}