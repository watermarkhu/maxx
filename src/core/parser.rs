//! Tree-sitter based MATLAB parser - pure Rust

use std::path::PathBuf;
use tree_sitter::{Language, Parser};

use super::errors::{MaltError, Result};
use super::objects::*;

/// Get the MATLAB tree-sitter language
pub fn get_matlab_language() -> Language {
    tree_sitter_matlab::LANGUAGE.into()
}

/// File parser for MATLAB files
pub struct FileParser {
    filepath: PathBuf,
    parser: Parser,
    source: Vec<u8>,
}

impl FileParser {
    pub fn new(filepath: PathBuf) -> Result<Self> {
        let mut parser = Parser::new();
        let language = get_matlab_language();
        parser
            .set_language(&language)
            .map_err(|e| MaltError::TreeSitter(format!("Language error: {}", e)))?;

        let source = std::fs::read(&filepath)?;

        Ok(Self {
            filepath,
            parser,
            source,
        })
    }

    pub fn parse(&mut self) -> Result<MatlabObject> {
        let tree = self.parser.parse(&self.source, None)
            .ok_or_else(|| MaltError::Parse("Failed to parse file".to_string()))?;

        let root_node = tree.root_node();
        self.parse_root_node(root_node)
    }

    fn parse_root_node(&self, node: tree_sitter::Node) -> Result<MatlabObject> {
        let mut cursor = node.walk();

        for child in node.children(&mut cursor) {
            match child.kind() {
                "function_definition" => {
                    return Ok(MatlabObject::Function(self.parse_function(child)?));
                }
                "class_definition" => {
                    return Ok(MatlabObject::Class(self.parse_class(child)?));
                }
                _ => {}
            }
        }

        // If no function or class found, it's a script
        Ok(MatlabObject::Script(self.parse_script(node)?))
    }

    fn parse_function(&self, node: tree_sitter::Node) -> Result<Function> {
        let name = self.extract_function_name(&node);
        let mut func = Function::new(name);
        func.base.lineno = Some(node.start_position().row + 1);
        func.base.endlineno = Some(node.end_position().row + 1);
        Ok(func)
    }

    fn parse_class(&self, node: tree_sitter::Node) -> Result<Class> {
        let name = self.extract_class_name(&node);
        let mut class = Class::new(name);
        class.base.lineno = Some(node.start_position().row + 1);
        class.base.endlineno = Some(node.end_position().row + 1);
        Ok(class)
    }

    fn parse_script(&self, _node: tree_sitter::Node) -> Result<Script> {
        let name = self.filepath
            .file_stem()
            .and_then(|s| s.to_str())
            .unwrap_or("script")
            .to_string();
        Ok(Script::new(name))
    }

    fn extract_function_name(&self, node: &tree_sitter::Node) -> String {
        let mut cursor = node.walk();
        for child in node.children(&mut cursor) {
            if child.kind() == "identifier" {
                return self.node_text(&child);
            }
        }
        "unnamed".to_string()
    }

    fn extract_class_name(&self, node: &tree_sitter::Node) -> String {
        let mut cursor = node.walk();
        for child in node.children(&mut cursor) {
            if child.kind() == "identifier" {
                return self.node_text(&child);
            }
        }
        "UnnamedClass".to_string()
    }

    fn node_text(&self, node: &tree_sitter::Node) -> String {
        node.utf8_text(&self.source)
            .unwrap_or("")
            .to_string()
    }
}

/// Parse a MATLAB file and return the parsed object
pub fn parse_file(filepath: PathBuf) -> Result<MatlabObject> {
    let mut parser = FileParser::new(filepath)?;
    parser.parse()
}
