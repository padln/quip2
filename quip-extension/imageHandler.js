// imageHandler.js
function markAsAIGenerated(img) {
    if (img.width < 200 || img.height < 200) return;
  
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
  
    chrome.storage.local.get(["aiCount"], (data) => {
      const count = data.aiCount || 0;
      chrome.storage.local.set({ aiCount: count + 1 });
    });
  }
  
  function handleImage(img) {
    if (!img.src || img.dataset.quipChecked === "true") return;
  
    img.dataset.quipChecked = "true";
  
    fetchCheck(img.src)
      .then(data => {
        if (data.likely_ai) {
          markAsAIGenerated(img);
        }
      })
      .catch(err => console.error("Quip error checking image:", err));
  }