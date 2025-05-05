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
