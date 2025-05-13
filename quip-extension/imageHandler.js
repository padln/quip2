// imageHandler.js
import { phashImageBytes } from "./wasm-loader.js";

export async function handleImage(img) {
  try {
    // Skip if already processed
    if (img.dataset.quipProcessed) return;
    img.dataset.quipProcessed = "true";

    const res = await fetch(img.src, { mode: "cors" });
    const blob = await res.blob();
    const bytes = new Uint8Array(await blob.arrayBuffer());

    const phash = await phashImageBytes(bytes);

    const resultRes = await fetch(`http://localhost:5050/results?phash=${encodeURIComponent(phash)}`);
    const resultData = await resultRes.json();

    if (resultData.error) {
      console.warn("Server responded with error:", resultData.error);
      return;
    }

    // Simple decision rule
    const isAI = resultData.p_yes > resultData.p_no;

    // Annotate the image
    annotateImage(img, isAI, resultData);
  } catch (err) {
    console.error("Error in handleImage:", err);
  }
}

function annotateImage(img, isAI, data) {
  img.style.border = isAI ? "3px solid red" : "3px solid green";
  const label = document.createElement("div");
  label.textContent = isAI ? "AI-Generated?" : "Real?";
  label.style.position = "absolute";
  label.style.background = "rgba(0,0,0,0.6)";
  label.style.color = "white";
  label.style.fontSize = "12px";
  label.style.padding = "2px 4px";
  label.style.zIndex = 9999;
  label.style.pointerEvents = "none";

  // Insert above the image
  const wrapper = document.createElement("div");
  wrapper.style.position = "relative";
  img.parentNode.insertBefore(wrapper, img);
  wrapper.appendChild(img);
  wrapper.appendChild(label);
}