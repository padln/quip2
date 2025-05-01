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