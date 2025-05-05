async function queryServerByUrl(imgUrl) {
  const encodedUrl = encodeURIComponent(imgUrl);
  const res = await fetch(`http://localhost:5050/check?url=${encodedUrl}`);
  return res.json();
}

async function addWarningOverlay(img) {
  const warning = document.createElement("div");
  warning.textContent = "⚠️ AI?";
  warning.style.position = "absolute";
  warning.style.background = "rgba(255,0,0,0.7)";
  warning.style.color = "white";
  warning.style.padding = "2px 4px";
  warning.style.fontSize = "12px";
  warning.style.zIndex = "9999";
  warning.style.top = "0";
  warning.style.left = "0";
  warning.style.pointerEvents = "none";
  warning.style.borderRadius = "3px";

  img.style.position = "relative";
  img.parentElement.style.position = "relative";
  img.parentElement.appendChild(warning);
}

(async function () {
  const images = document.querySelectorAll("img");

  for (const img of images) {
    const src = img.src;

    if (!src.startsWith("http")) continue; // Skip inline/base64

    try {
      const result = await queryServerByUrl(src);

      if (!result.cached || result.result === "ai") {
        await addWarningOverlay(img);
      }
    } catch (e) {
      console.error("Image check failed:", e);
    }
  }
})();

// This function should be called when an image is detected as AI-generated
function markAsAIGenerated(img) {
  // You can skip very small images
  if (img.width < 200 || img.height < 200) return;

  // Add visual mark (example)
  const overlay = document.createElement("div");
  overlay.textContent = "⚠️";
  overlay.style.position = "absolute";
  overlay.style.top = "5px";
  overlay.style.right = "5px";
  overlay.style.zIndex = "9999";
  overlay.style.fontSize = "18px";
  img.style.position = "relative";
  img.parentElement.style.position = "relative";
  img.parentElement.appendChild(overlay);

  // Increment the count in chrome.storage
  chrome.storage.local.get(["aiCount"], (data) => {
    const count = data.aiCount || 0;
    chrome.storage.local.set({ aiCount: count + 1 });
  });
}

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request === "resetCount") {
    chrome.storage.local.set({ aiCount: 0 });
  }
});

chrome.runtime.sendMessage("resetCount");