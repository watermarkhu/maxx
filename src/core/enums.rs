//! Core enumerations - pure Rust, no Python dependencies

use serde::{Deserialize, Serialize};

/// Different kinds of MATLAB code elements
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum Kind {
    Folder,
    Namespace,
    Class,
    Enumeration,
    Function,
    Script,
    Property,
    Alias,
    Builtin,
}

impl Kind {
    pub fn as_str(&self) -> &'static str {
        match self {
            Kind::Folder => "folder",
            Kind::Namespace => "namespace",
            Kind::Class => "class",
            Kind::Enumeration => "enumeration",
            Kind::Function => "function",
            Kind::Script => "script",
            Kind::Property => "property",
            Kind::Alias => "alias",
            Kind::Builtin => "builtin",
        }
    }
}

/// Different kinds of function arguments
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum ArgumentKind {
    PositionalOnly,
    Optional,
    KeywordOnly,
    Varargin,
}

impl ArgumentKind {
    pub fn as_str(&self) -> &'static str {
        match self {
            ArgumentKind::PositionalOnly => "positional-only",
            ArgumentKind::Optional => "optional",
            ArgumentKind::KeywordOnly => "keyword-only",
            ArgumentKind::Varargin => "varargin",
        }
    }
}

/// Access levels for MATLAB code elements
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum AccessKind {
    Public,
    Protected,
    Private,
    Immutable,
}

impl AccessKind {
    pub fn as_str(&self) -> &'static str {
        match self {
            AccessKind::Public => "public",
            AccessKind::Protected => "protected",
            AccessKind::Private => "private",
            AccessKind::Immutable => "immutable",
        }
    }
}
