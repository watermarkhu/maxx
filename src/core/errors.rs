//! Error types - pure Rust

use thiserror::Error;

#[derive(Error, Debug)]
pub enum MaltError {
    #[error("Cyclic aliases detected: {chain:?}")]
    CyclicAlias { chain: Vec<String> },

    #[error("File path error: {0}")]
    FilePath(String),

    #[error("Name resolution error: {0}")]
    NameResolution(String),

    #[error("IO error: {0}")]
    Io(#[from] std::io::Error),

    #[error("Tree-sitter error: {0}")]
    TreeSitter(String),

    #[error("Parse error: {0}")]
    Parse(String),

    #[error("Config error: {0}")]
    Config(String),
}

pub type Result<T> = std::result::Result<T, MaltError>;
