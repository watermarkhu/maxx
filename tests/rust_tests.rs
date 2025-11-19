/// Rust integration tests for the malt library
///
/// These tests verify the core Rust functionality without Python bindings

use malt::core::{
    collection::PathsCollection,
    enums::{AccessKind, ArgumentKind, Kind},
    objects::*,
    parser::{parse_file, FileParser},
};
use std::path::PathBuf;

fn test_files_dir() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("tests/files")
}

#[test]
fn test_parser_exists() {
    let test_file = test_files_dir().join("test_function.m");
    assert!(
        test_file.exists(),
        "Test file not found: {}",
        test_file.display()
    );
}

#[test]
fn test_parse_function() {
    let test_file = test_files_dir().join("test_function.m");
    let result = parse_file(test_file);

    assert!(result.is_ok(), "Failed to parse function: {:?}", result.err());

    let obj = result.unwrap();
    assert_eq!(obj.name(), "test_function");
    assert_eq!(obj.kind(), Kind::Function);
}

#[test]
fn test_parse_class() {
    let test_file = test_files_dir().join("MyClass.m");
    let result = parse_file(test_file);

    assert!(result.is_ok(), "Failed to parse class: {:?}", result.err());

    let obj = result.unwrap();
    assert_eq!(obj.name(), "MyClass");
    assert_eq!(obj.kind(), Kind::Class);
}

#[test]
fn test_parse_script() {
    let test_file = test_files_dir().join("my_script.m");
    let result = parse_file(test_file);

    assert!(result.is_ok(), "Failed to parse script: {:?}", result.err());

    let obj = result.unwrap();
    assert_eq!(obj.name(), "my_script");
    assert_eq!(obj.kind(), Kind::Script);
}

#[test]
fn test_file_parser_api() {
    let test_file = test_files_dir().join("test_function.m");
    let mut parser = FileParser::new(test_file.clone()).expect("Failed to create parser");

    let obj = parser.parse().expect("Failed to parse file");

    assert_eq!(obj.name(), "test_function");
    assert_eq!(obj.kind(), Kind::Function);
}

#[test]
fn test_multiple_files() {
    let test_files = vec!["test_function.m", "MyClass.m", "my_script.m"];

    for filename in test_files {
        let test_file = test_files_dir().join(filename);
        if !test_file.exists() {
            eprintln!("Skipping {}: file not found", filename);
            continue;
        }

        let result = parse_file(test_file.clone());
        assert!(
            result.is_ok(),
            "Failed to parse {}: {:?}",
            filename,
            result.err()
        );

        let obj = result.unwrap();
        println!("Parsed {}: {} ({:?})", filename, obj.name(), obj.kind());
    }
}

#[test]
fn test_enum_values() {
    // Test Kind enum
    assert_eq!(Kind::Function.as_str(), "function");
    assert_eq!(Kind::Class.as_str(), "class");
    assert_eq!(Kind::Script.as_str(), "script");
    assert_eq!(Kind::Property.as_str(), "property");

    // Test ArgumentKind enum
    assert_eq!(ArgumentKind::PositionalOnly.as_str(), "positional-only");
    assert_eq!(ArgumentKind::Optional.as_str(), "optional");
    assert_eq!(ArgumentKind::KeywordOnly.as_str(), "keyword-only");
    assert_eq!(ArgumentKind::Varargin.as_str(), "varargin");

    // Test AccessKind enum
    assert_eq!(AccessKind::Public.as_str(), "public");
    assert_eq!(AccessKind::Protected.as_str(), "protected");
    assert_eq!(AccessKind::Private.as_str(), "private");
    assert_eq!(AccessKind::Immutable.as_str(), "immutable");
}

#[test]
fn test_object_creation() {
    // Test Object creation
    let obj = Object::new("TestObject".to_string(), Kind::Function);
    assert_eq!(obj.name, "TestObject");
    assert_eq!(obj.kind, Kind::Function);
    assert_eq!(obj.lineno, None);
    assert_eq!(obj.endlineno, None);
    assert!(!obj.has_docstring());

    // Test Function creation
    let func = Function::new("TestFunction".to_string());
    assert_eq!(func.base.name, "TestFunction");
    assert_eq!(func.base.kind, Kind::Function);
    assert!(!func.is_method);
    assert!(!func.is_setter);
    assert!(!func.is_getter);

    // Test Class creation
    let class = Class::new("TestClass".to_string());
    assert_eq!(class.base.name, "TestClass");
    assert_eq!(class.base.kind, Kind::Class);
    assert_eq!(class.bases.len(), 0);
    assert_eq!(class.properties.len(), 0);
    assert_eq!(class.methods.len(), 0);

    // Test Argument creation
    let arg = Argument::new("test_arg".to_string());
    assert_eq!(arg.name, "test_arg");
    assert_eq!(arg.kind, None);
    assert!(arg.is_required());

    // Test Property creation
    let prop = Property::new("test_prop".to_string());
    assert_eq!(prop.name, "test_prop");
    assert_eq!(prop.access, None);
    assert!(!prop.constant);
    assert!(!prop.dependent);
}

#[test]
fn test_collection_basic() {
    let test_dir = test_files_dir().join("subdir");

    if !test_dir.exists() {
        eprintln!("Skipping collection test: subdir not found");
        return;
    }

    let result = PathsCollection::new(vec![test_dir.clone()], false);

    match result {
        Ok(collection) => {
            println!(
                "Successfully collected {} objects from {}",
                collection.len(),
                test_dir.display()
            );
            assert!(collection.len() > 0, "Collection should not be empty");

            // Test contains
            for key in collection.keys() {
                assert!(collection.contains(key), "Key {} not found", key);
            }
        }
        Err(e) => {
            eprintln!("Collection test failed: {}", e);
            panic!("Failed to create collection");
        }
    }
}

#[test]
fn test_error_handling() {
    // Test parsing non-existent file
    let nonexistent = test_files_dir().join("nonexistent.m");
    let result = parse_file(nonexistent);
    assert!(result.is_err(), "Should fail for non-existent file");

    // Test creating parser with non-existent file
    let nonexistent = test_files_dir().join("nonexistent.m");
    let result = FileParser::new(nonexistent);
    assert!(result.is_err(), "Should fail for non-existent file");
}

#[test]
fn test_matlab_object_enum() {
    // Test that MatlabObject enum methods work correctly
    let func = Function::new("test".to_string());
    let obj = MatlabObject::Function(func);

    assert_eq!(obj.name(), "test");
    assert_eq!(obj.kind(), Kind::Function);

    let class = Class::new("TestClass".to_string());
    let obj = MatlabObject::Class(class);

    assert_eq!(obj.name(), "TestClass");
    assert_eq!(obj.kind(), Kind::Class);
}

#[test]
fn test_serde_serialization() {
    // Test that objects can be serialized
    let func = Function::new("test_func".to_string());
    let json = serde_json::to_string(&func).expect("Failed to serialize");
    assert!(json.contains("test_func"));

    let class = Class::new("TestClass".to_string());
    let json = serde_json::to_string(&class).expect("Failed to serialize");
    assert!(json.contains("TestClass"));

    let arg = Argument::new("test_arg".to_string());
    let json = serde_json::to_string(&arg).expect("Failed to serialize");
    assert!(json.contains("test_arg"));
}

#[test]
fn test_kind_equality() {
    assert_eq!(Kind::Function, Kind::Function);
    assert_ne!(Kind::Function, Kind::Class);

    let obj = Object::new("test".to_string(), Kind::Function);
    assert!(obj.is_kind(Kind::Function));
    assert!(!obj.is_kind(Kind::Class));
}
