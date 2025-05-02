# Most Important
- [ ] Implement MutationObserver for scrolling content  
*Detect and analyze newly loaded <img> elements dynamically.*  

- [ ] Implement Hive detection API  
*If an image’s p-hash is not in Redis, send it to Hive (or similar) for AI detection scoring.*  

- [ ] Implement actual warning overlay on images  
*Add a small visible badge/overlay (e.g., a red/yellow ⚠️ icon) in the corner of images over 200×200px when suspected of being AI-generated.*  

- [ ] Implement ScaNN / Hamming distance / BK-tree for p-hash similarity  
*Improve efficiency and robustness of near-duplicate p-hash lookups for fuzzy matching.*  

# Functionality
- [ ] Throttle or debounce API calls  
*Avoid spamming the Flask server with requests during scroll bursts.*  

- [ ] Add a cache of seen URLs on the frontend  
*Prevent duplicate checks for the same image URL in a session.*  

- [ ] Fallback for blob URLs or base64 images  
*Some sites load images without a src URL. Handle blobs or embedded images.*  

- [ ] Support iframe detection (optional)
*If you want to analyze images inside iframes (used on some sites).* 

# UX / Frontend polish
- [ ] Add a popup or badge to the Chrome extension   
*Let users toggle detection on/off, view logs, or customize thresholds.*  

- [ ] Add hover tooltips or detection scores to overlay  
*Users can hover over the warning badge to get info like “AI confidence: 92%”.*  

- [ ] Improve styling of overlays  
*Use transparent overlays or icons that adapt to light/dark images.*  

# Backend & Scaling
- [ ] Add persistent Redis storage  
*Use a volume or cloud Redis (right now, all keys disappear when the container stops).*  

- [ ] Move to a production Flask server (e.g., gunicorn + nginx)  
*For deployment outside local testing.*  

- [ ] Deploy the backend to a cloud host (e.g., Render, Fly.io, or Railway)  
*So users don’t need it running on localhost.*  