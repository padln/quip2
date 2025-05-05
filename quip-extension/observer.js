
// observer.js
function observeNewImages(processImageCallback) {
    const observer = new MutationObserver((mutations) => {
      for (const mutation of mutations) {
        for (const node of mutation.addedNodes) {
          if (node.nodeType === 1) {
            if (node.tagName === "IMG") {
              processImageCallback(node);
            }
  
            const imgs = node.querySelectorAll?.("img");
            imgs?.forEach(img => processImageCallback(img));
          }
        }
      }
    });
  
    observer.observe(document.body, {
      childList: true,
      subtree: true,
    });
  }