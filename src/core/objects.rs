//! MATLAB object model - pure Rust, no Python dependencies

use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::path::PathBuf;

use super::enums::{AccessKind, ArgumentKind, Kind};
use super::expressions::Expr;

/// Represents a validatable element (argument or property)
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Validatable {
    pub name: String,
    pub type_: Option<String>,
    pub dimensions: Option<Vec<String>>,
    pub default: Option<String>,
    pub validators: Option<String>,
    pub docstring: Option<String>,
}

impl Validatable {
    pub fn new(name: String) -> Self {
        Self {
            name,
            type_: None,
            dimensions: None,
            default: None,
            validators: None,
            docstring: None,
        }
    }

    pub fn has_docstring(&self) -> bool {
        self.docstring.is_some()
    }
}

/// Represents a function argument
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Argument {
    pub name: String,
    pub kind: Option<ArgumentKind>,
    pub type_: Option<String>,
    pub default: Option<String>,
    pub docstring: Option<String>,
}

impl Argument {
    pub fn new(name: String) -> Self {
        Self {
            name,
            kind: None,
            type_: None,
            default: None,
            docstring: None,
        }
    }

    pub fn is_required(&self) -> bool {
        self.default.is_none()
    }
}

/// Base MATLAB object
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Object {
    pub name: String,
    pub kind: Kind,
    pub lineno: Option<usize>,
    pub endlineno: Option<usize>,
    pub docstring: Option<String>,
    pub public: Option<bool>,
    pub members: HashMap<String, Box<Object>>,
    pub attributes: Vec<String>,
}

impl Object {
    pub fn new(name: String, kind: Kind) -> Self {
        Self {
            name,
            kind,
            lineno: None,
            endlineno: None,
            docstring: None,
            public: None,
            members: HashMap::new(),
            attributes: Vec::new(),
        }
    }

    pub fn has_docstring(&self) -> bool {
        self.docstring.is_some()
    }

    pub fn is_kind(&self, kind: Kind) -> bool {
        self.kind == kind
    }

    pub fn member_count(&self) -> usize {
        self.members.len()
    }
}

/// Represents a MATLAB function
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Function {
    pub base: Object,
    pub arguments: Vec<Argument>,
    pub outputs: Vec<String>,
    pub is_method: bool,
    pub is_setter: bool,
    pub is_getter: bool,
}

impl Function {
    pub fn new(name: String) -> Self {
        Self {
            base: Object::new(name, Kind::Function),
            arguments: Vec::new(),
            outputs: Vec::new(),
            is_method: false,
            is_setter: false,
            is_getter: false,
        }
    }
}

/// Represents a MATLAB class
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Class {
    pub base: Object,
    pub bases: Vec<String>,
    pub properties: HashMap<String, Property>,
    pub methods: HashMap<String, Function>,
}

impl Class {
    pub fn new(name: String) -> Self {
        Self {
            base: Object::new(name, Kind::Class),
            bases: Vec::new(),
            properties: HashMap::new(),
            methods: HashMap::new(),
        }
    }
}

/// Represents a MATLAB property
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Property {
    pub name: String,
    pub access: Option<AccessKind>,
    pub constant: bool,
    pub dependent: bool,
    pub type_: Option<String>,
    pub default: Option<String>,
    pub docstring: Option<String>,
}

impl Property {
    pub fn new(name: String) -> Self {
        Self {
            name,
            access: None,
            constant: false,
            dependent: false,
            type_: None,
            default: None,
            docstring: None,
        }
    }
}

/// Represents a MATLAB script
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Script {
    pub base: Object,
}

impl Script {
    pub fn new(name: String) -> Self {
        Self {
            base: Object::new(name, Kind::Script),
        }
    }
}

/// Represents a MATLAB namespace
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Namespace {
    pub base: Object,
    pub path: Option<PathBuf>,
}

impl Namespace {
    pub fn new(name: String) -> Self {
        Self {
            base: Object::new(name, Kind::Namespace),
            path: None,
        }
    }
}

/// Represents a MATLAB folder
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Folder {
    pub base: Object,
    pub path: Option<PathBuf>,
}

impl Folder {
    pub fn new(name: String) -> Self {
        Self {
            base: Object::new(name, Kind::Folder),
            path: None,
        }
    }
}

/// Represents an alias to another object
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Alias {
    pub name: String,
    pub target_path: String,
}

impl Alias {
    pub fn new(name: String, target_path: String) -> Self {
        Self { name, target_path }
    }
}

/// Represents docstring information
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Docstring {
    pub value: String,
    pub lineno: Option<usize>,
    pub endlineno: Option<usize>,
}

impl Docstring {
    pub fn new(value: String) -> Self {
        Self {
            value,
            lineno: None,
            endlineno: None,
        }
    }
}

/// Enum to represent any MATLAB object type
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum MatlabObject {
    Object(Object),
    Function(Function),
    Class(Class),
    Property(Property),
    Script(Script),
    Namespace(Namespace),
    Folder(Folder),
    Alias(Alias),
}

impl MatlabObject {
    pub fn name(&self) -> &str {
        match self {
            MatlabObject::Object(o) => &o.name,
            MatlabObject::Function(f) => &f.base.name,
            MatlabObject::Class(c) => &c.base.name,
            MatlabObject::Property(p) => &p.name,
            MatlabObject::Script(s) => &s.base.name,
            MatlabObject::Namespace(n) => &n.base.name,
            MatlabObject::Folder(f) => &f.base.name,
            MatlabObject::Alias(a) => &a.name,
        }
    }

    pub fn kind(&self) -> Kind {
        match self {
            MatlabObject::Object(o) => o.kind,
            MatlabObject::Function(_) => Kind::Function,
            MatlabObject::Class(_) => Kind::Class,
            MatlabObject::Property(_) => Kind::Property,
            MatlabObject::Script(_) => Kind::Script,
            MatlabObject::Namespace(_) => Kind::Namespace,
            MatlabObject::Folder(_) => Kind::Folder,
            MatlabObject::Alias(_) => Kind::Alias,
        }
    }
}
