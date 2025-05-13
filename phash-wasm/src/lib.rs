use wasm_bindgen::prelude::*;
use image_hasher::{HasherConfig, HashAlg};
use std::fmt::Write;

#[wasm_bindgen]
pub fn init_panic() {
    console_error_panic_hook::set_once();
}

#[wasm_bindgen]
pub fn phash(bytes: &[u8]) -> Result<String, JsValue> {
    let img = image::load_from_memory(bytes)
        .map_err(|e| JsValue::from_str(&format!("Image load failed: {}", e)))?;
    
    let hasher = HasherConfig::new()
        .hash_alg(HashAlg::Gradient) // or Median, Mean, etc.
        .to_hasher();

    let hash = hasher.hash_image(&img);
    
    // Return as base64 string
    Ok(hash.to_base64())
}