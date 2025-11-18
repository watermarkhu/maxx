//! Expression handling - pure Rust

use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::sync::OnceLock;

const MATHWORKS_DOC_URL: &str = "https://www.mathworks.com/help/matlab";

static MATLAB_BUILTINS: OnceLock<HashMap<String, String>> = OnceLock::new();

pub fn get_matlab_builtins() -> &'static HashMap<String, String> {
    MATLAB_BUILTINS.get_or_init(HashMap::new)
}

pub fn init_matlab_builtins(builtins: HashMap<String, String>) {
    MATLAB_BUILTINS.set(builtins).ok();
}

/// Represents a MATLAB expression
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct Expr {
    pub text: String,
}

impl Expr {
    pub fn new(text: String) -> Self {
        Self { text }
    }

    /// Get documentation URL if this expression references a builtin
    pub fn doc_url(&self) -> Option<String> {
        let builtins = get_matlab_builtins();
        for token in self.text.split_whitespace() {
            if let Some(doc_path) = builtins.get(token) {
                return Some(format!("{}/{}", MATHWORKS_DOC_URL, doc_path));
            }
        }
        None
    }
}

impl std::fmt::Display for Expr {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "{}", self.text)
    }
}
