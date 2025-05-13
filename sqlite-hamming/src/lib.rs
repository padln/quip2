use std::ops::BitXor;
use std::os::raw::{c_char, c_int};

use anyhow::anyhow;
use rusqlite::functions::FunctionFlags;
use rusqlite::{Connection, Result};
use rusqlite::{Error, ffi};

/// Entry point for SQLite to load the extension.
/// See <https://sqlite.org/c3ref/load_extension.html> on this function's name and usage.
/// # Safety
/// This function is called by SQLite and must be safe to call.
#[unsafe(no_mangle)]
pub unsafe extern "C" fn sqlite3_extension_init(
    db: *mut ffi::sqlite3,
    pz_err_msg: *mut *mut c_char,
    p_api: *mut ffi::sqlite3_api_routines,
) -> c_int {
    unsafe { Connection::extension_init2(db, pz_err_msg, p_api, extension_init) }
}

fn extension_init(db: Connection) -> Result<bool> {
    db.create_scalar_function("hamming", 2, FunctionFlags::SQLITE_DETERMINISTIC, |ctx| {
        let a = ctx.get::<Vec<u8>>(0)?;
        let b = ctx.get::<Vec<u8>>(1)?;
        if a.len() != b.len() {
            return Err(Error::UserFunctionError(
                anyhow!("arguments must be the same size").into(),
            ));
        }
        let dist = a
            .into_iter()
            .zip(b.into_iter())
            .map(|(a, b)| a.bitxor(b).count_ones())
            .sum::<u32>();
        Ok(dist)
    })?;
    rusqlite::trace::log(ffi::SQLITE_WARNING, "sqlite-hamming extension initialized");
    Ok(false)
}
