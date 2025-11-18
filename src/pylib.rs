//! Python bindings for the malt library
//!
//! This module wraps the pure Rust core with Python-compatible types

use pyo3::prelude::*;
use pyo3::{create_exception, exceptions::PyException};
use std::path::PathBuf;

use crate::core;

// Create Python exception types
create_exception!(malt, MaltError, PyException);
create_exception!(malt, CyclicAliasError, MaltError);
create_exception!(malt, FilePathError, MaltError);
create_exception!(malt, NameResolutionError, MaltError);

// Convert Rust errors to Python errors
impl From<core::errors::MaltError> for PyErr {
    fn from(err: core::errors::MaltError) -> PyErr {
        match err {
            core::errors::MaltError::CyclicAlias { chain } => {
                let msg = format!("Cyclic aliases detected:\n  {}", chain.join("\n  "));
                CyclicAliasError::new_err(msg)
            }
            core::errors::MaltError::FilePath(msg) => FilePathError::new_err(msg),
            core::errors::MaltError::NameResolution(msg) => NameResolutionError::new_err(msg),
            _ => MaltError::new_err(err.to_string()),
        }
    }
}

// ===== Enums =====

#[pyclass]
#[derive(Clone)]
pub struct Kind(pub core::enums::Kind);

#[pymethods]
impl Kind {
    fn __str__(&self) -> &'static str {
        self.0.as_str()
    }

    fn __repr__(&self) -> String {
        format!("Kind.{:?}", self.0)
    }
}

#[pyclass]
#[derive(Clone)]
pub struct ArgumentKind(pub core::enums::ArgumentKind);

#[pymethods]
impl ArgumentKind {
    fn __str__(&self) -> &'static str {
        self.0.as_str()
    }

    fn __repr__(&self) -> String {
        format!("ArgumentKind.{:?}", self.0)
    }
}

#[pyclass]
#[derive(Clone)]
pub struct AccessKind(pub core::enums::AccessKind);

#[pymethods]
impl AccessKind {
    fn __str__(&self) -> &'static str {
        self.0.as_str()
    }

    fn __repr__(&self) -> String {
        format!("AccessKind.{:?}", self.0)
    }
}

// ===== Objects =====

#[pyclass]
pub struct MatlabObject(pub core::objects::MatlabObject);

#[pymethods]
impl MatlabObject {
    #[getter]
    fn name(&self) -> &str {
        self.0.name()
    }

    #[getter]
    fn kind(&self) -> Kind {
        Kind(self.0.kind())
    }

    fn __str__(&self) -> String {
        self.0.name().to_string()
    }

    fn __repr__(&self) -> String {
        format!("{:?}", self.0)
    }
}

// ===== Parser =====

#[pyclass]
pub struct FileParser {
    parser: core::parser::FileParser,
}

#[pymethods]
impl FileParser {
    #[new]
    fn new(filepath: PathBuf) -> PyResult<Self> {
        let parser = core::parser::FileParser::new(filepath)?;
        Ok(Self { parser })
    }

    fn parse(&mut self) -> PyResult<MatlabObject> {
        let obj = self.parser.parse()?;
        Ok(MatlabObject(obj))
    }

    fn __repr__(&self) -> String {
        "FileParser()".to_string()
    }
}

#[pyfunction]
pub fn parse_file(filepath: PathBuf) -> PyResult<MatlabObject> {
    let obj = core::parser::parse_file(filepath)?;
    Ok(MatlabObject(obj))
}

// ===== Collection =====

#[pyclass]
pub struct PathsCollection {
    collection: core::collection::PathsCollection,
}

#[pymethods]
impl PathsCollection {
    #[new]
    #[pyo3(signature = (paths, recursive=false))]
    fn new(paths: Vec<PathBuf>, recursive: bool) -> PyResult<Self> {
        let collection = core::collection::PathsCollection::new(paths, recursive)?;
        Ok(Self { collection })
    }

    fn __getitem__(&self, name: &str) -> PyResult<MatlabObject> {
        self.collection
            .get(name)
            .map(|obj| MatlabObject(obj.clone()))
            .ok_or_else(|| PyErr::new::<pyo3::exceptions::PyKeyError, _>(format!("Object '{}' not found", name)))
    }

    fn __contains__(&self, name: &str) -> bool {
        self.collection.contains(name)
    }

    fn __len__(&self) -> usize {
        self.collection.len()
    }

    fn keys(&self) -> Vec<String> {
        self.collection.keys().cloned().collect()
    }

    fn __repr__(&self) -> String {
        format!("PathsCollection({} objects)", self.collection.len())
    }
}

// ===== Linting =====

#[pyclass]
#[derive(Clone)]
pub struct Violation(pub core::lint::Violation);

#[pymethods]
impl Violation {
    #[getter]
    fn rule_id(&self) -> &str {
        &self.0.rule_id
    }

    #[getter]
    fn message(&self) -> &str {
        &self.0.message
    }

    #[getter]
    fn filepath(&self) -> PathBuf {
        self.0.filepath.clone()
    }

    #[getter]
    fn line(&self) -> usize {
        self.0.line
    }

    #[getter]
    fn column(&self) -> usize {
        self.0.column
    }

    #[getter]
    fn severity(&self) -> &str {
        &self.0.severity
    }

    fn __str__(&self) -> String {
        format!(
            "{}:{}:{}: {} [{}]",
            self.0.filepath.display(),
            self.0.line,
            self.0.column,
            self.0.message,
            self.0.rule_id
        )
    }

    fn __repr__(&self) -> String {
        format!(
            "Violation(rule_id='{}', line={}, column={})",
            self.0.rule_id, self.0.line, self.0.column
        )
    }
}

#[pyclass]
pub struct LintEngine {
    engine: core::lint::LintEngine,
}

#[pymethods]
impl LintEngine {
    #[new]
    fn new() -> PyResult<Self> {
        let engine = core::lint::LintEngine::new(None, None)?;
        Ok(Self { engine })
    }

    fn lint_file(&mut self, filepath: PathBuf) -> PyResult<Vec<Violation>> {
        let violations = self.engine.lint_file(filepath)?;
        Ok(violations.into_iter().map(Violation).collect())
    }

    fn lint_files(&mut self, filepaths: Vec<PathBuf>) -> PyResult<Vec<Violation>> {
        let violations = self.engine.lint_files(filepaths)?;
        Ok(violations.into_iter().map(Violation).collect())
    }

    fn __repr__(&self) -> String {
        "LintEngine()".to_string()
    }
}

/// Register exception types with Python module
pub fn register_exceptions(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add("MaltError", m.py().get_type_bound::<MaltError>())?;
    m.add("CyclicAliasError", m.py().get_type_bound::<CyclicAliasError>())?;
    m.add("FilePathError", m.py().get_type_bound::<FilePathError>())?;
    m.add("NameResolutionError", m.py().get_type_bound::<NameResolutionError>())?;
    Ok(())
}
