# Goal
- perceptual hash ensemble on the client  
- similarity search on a central server  
- fallback AI model for edge cases  

# Pipeline
1. Client computes 5 p-hashes (Mean, Gradient, DoubleGradient, BlockHash, DCT)  

2. Client sends to:  
` GET /results?phash_vector=... `

3. Server checks for nearest matches via SQLite + custom hamming extension  

4. If no matches:  
 - Client runs lightweight model  
 - Client sends:  
    - Model result  `POST /results`  
    - Hash contribution `POST /feedback`  
 - Server uses feedback to adjust per-hash weights

# Intelligence Split
- **Client:** Fast + local + privacy-preserving
- **Server:** Centralized memory + weight learning