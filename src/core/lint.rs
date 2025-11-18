//! Linting engine - pure Rust

use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::path::{Path, PathBuf};
use tree_sitter::Parser;

use super::errors::{MaltError, Result};
use super::parser::get_matlab_language;

/// Represents a linting violation
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Violation {
    pub rule_id: String,
    pub message: String,
    pub filepath: PathBuf,
    pub line: usize,
    pub column: usize,
    pub severity: String,
}

impl Violation {
    pub fn new(rule_id: String, message: String, filepath: PathBuf, line: usize, column: usize, severity: String) -> Self {
        Self {
            rule_id,
            message,
            filepath,
            line,
            column,
            severity,
        }
    }
}

/// Represents a linting rule
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Rule {
    pub id: String,
    pub name: String,
    pub description: String,
    pub severity: String,
    pub enabled: bool,
}

impl Rule {
    pub fn new(id: String, name: String, description: String) -> Self {
        Self {
            id,
            name,
            description,
            severity: "warning".to_string(),
            enabled: true,
        }
    }
}

/// Registry for linting rules
pub struct RuleRegistry {
    pub rules: HashMap<String, Rule>,
}

impl RuleRegistry {
    pub fn new() -> Self {
        Self {
            rules: HashMap::new(),
        }
    }

    pub fn register(&mut self, rule: Rule) {
        self.rules.insert(rule.id.clone(), rule);
    }

    pub fn get(&self, rule_id: &str) -> Option<&Rule> {
        self.rules.get(rule_id)
    }

    pub fn get_enabled_rules(&self) -> Vec<&Rule> {
        self.rules.values().filter(|r| r.enabled).collect()
    }

    pub fn enable_rule(&mut self, rule_id: &str) -> bool {
        if let Some(rule) = self.rules.get_mut(rule_id) {
            rule.enabled = true;
            true
        } else {
            false
        }
    }

    pub fn disable_rule(&mut self, rule_id: &str) -> bool {
        if let Some(rule) = self.rules.get_mut(rule_id) {
            rule.enabled = false;
            true
        } else {
            false
        }
    }

    pub fn rule_ids(&self) -> impl Iterator<Item = &String> {
        self.rules.keys()
    }

    pub fn len(&self) -> usize {
        self.rules.len()
    }

    pub fn is_empty(&self) -> bool {
        self.rules.is_empty()
    }
}

impl Default for RuleRegistry {
    fn default() -> Self {
        Self::new()
    }
}

/// Linting configuration
#[derive(Debug, Clone)]
pub struct LintConfig {
    pub enabled_rules: Vec<String>,
    pub disabled_rules: Vec<String>,
    pub exclude_paths: Vec<PathBuf>,
}

impl LintConfig {
    pub fn new() -> Self {
        Self {
            enabled_rules: Vec::new(),
            disabled_rules: Vec::new(),
            exclude_paths: Vec::new(),
        }
    }

    pub fn is_rule_enabled(&self, rule_id: &str) -> bool {
        if self.disabled_rules.contains(&rule_id.to_string()) {
            return false;
        }
        if self.enabled_rules.is_empty() {
            return true;
        }
        self.enabled_rules.contains(&rule_id.to_string())
    }

    pub fn is_path_excluded(&self, path: &Path) -> bool {
        for exclude_path in &self.exclude_paths {
            if path.starts_with(exclude_path) {
                return true;
            }
        }
        false
    }
}

impl Default for LintConfig {
    fn default() -> Self {
        Self::new()
    }
}

/// Main linting engine
pub struct LintEngine {
    pub registry: RuleRegistry,
    pub config: LintConfig,
    parser: Parser,
}

impl LintEngine {
    pub fn new(registry: Option<RuleRegistry>, config: Option<LintConfig>) -> Result<Self> {
        let mut parser = Parser::new();
        let language = get_matlab_language();
        parser
            .set_language(&language)
            .map_err(|e| MaltError::TreeSitter(format!("Language error: {}", e)))?;

        Ok(Self {
            registry: registry.unwrap_or_default(),
            config: config.unwrap_or_default(),
            parser,
        })
    }

    pub fn lint_file(&mut self, filepath: PathBuf) -> Result<Vec<Violation>> {
        let violations = Vec::new();

        // Check if file should be excluded
        if self.config.is_path_excluded(&filepath) {
            return Ok(violations);
        }

        // Read and parse the file
        let source = std::fs::read(&filepath)?;
        let _tree = self.parser.parse(&source, None)
            .ok_or_else(|| MaltError::Parse("Failed to parse file".to_string()))?;

        // Run enabled rules (simplified - actual implementation would run rules here)

        Ok(violations)
    }

    pub fn lint_files(&mut self, filepaths: Vec<PathBuf>) -> Result<Vec<Violation>> {
        let mut all_violations = Vec::new();

        for filepath in filepaths {
            let violations = self.lint_file(filepath)?;
            all_violations.extend(violations);
        }

        Ok(all_violations)
    }
}
