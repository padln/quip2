// wasm-loader.js
let wasm;

export async function initWasm() {
  if (!wasm) {
    const wasmModule = await import("./wasm/phash_wasm.js");
    await wasmModule.default(); // load wasm module
    wasm = wasmModule;
    wasm.initPanic(); // optional: sets up panic hook
  }
}

export async function phashImageBytes(bytes) {
  if (!wasm) throw new Error("WASM not initialized");
  return wasm.phash(bytes);
}