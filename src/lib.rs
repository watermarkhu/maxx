//! MALT (MATLAB Language Tools) - Rust implementation
//!
//! A pure Rust library for parsing and analyzing MATLAB code, with optional Python bindings.
//!
//! # Architecture
//!
//! - `core`: Pure Rust implementation with no Python dependencies
//! - `pylib`: Python bindings layer (only compiled when building for Python)

// Core Rust library - always available
pub mod core;

// Python bindings - only when building with PyO3
#[cfg(feature = "python")]
mod pylib;

#[cfg(feature = "python")]
use pyo3::prelude::*;

/// Python module definition
#[cfg(feature = "python")]
#[pymodule]
fn malt(py: Python<'_>, m: &Bound<'_, PyModule>) -> PyResult<()> {
    // Module metadata
    m.add("__doc__", "MALT (MATLAB Language Tools) - Rust implementation for parsing and analyzing MATLAB code")?;
    m.add("__version__", env!("CARGO_PKG_VERSION"))?;

    // Register exceptions
    pylib::register_exceptions(m)?;

    // Register enums
    m.add_class::<pylib::Kind>()?;
    m.add_class::<pylib::ArgumentKind>()?;
    m.add_class::<pylib::AccessKind>()?;

    // Register objects
    m.add_class::<pylib::MatlabObject>()?;

    // Register parser
    m.add_class::<pylib::FileParser>()?;
    m.add_function(wrap_pyfunction!(pylib::parse_file, m)?)?;

    // Register collection
    m.add_class::<pylib::PathsCollection>()?;

    // Register linting
    m.add_class::<pylib::Violation>()?;
    m.add_class::<pylib::LintEngine>()?;

    // Create submodules for organization
    let treesitter_module = PyModule::new_bound(py, "treesitter")?;
    treesitter_module.add_class::<pylib::FileParser>()?;
    treesitter_module.add_function(wrap_pyfunction!(pylib::parse_file, &treesitter_module)?)?;
    m.add_submodule(&treesitter_module)?;

    let collection_module = PyModule::new_bound(py, "collection")?;
    collection_module.add_class::<pylib::PathsCollection>()?;
    m.add_submodule(&collection_module)?;

    let lint_module = PyModule::new_bound(py, "lint")?;
    lint_module.add_class::<pylib::Violation>()?;
    lint_module.add_class::<pylib::LintEngine>()?;
    m.add_submodule(&lint_module)?;

    Ok(())
}
