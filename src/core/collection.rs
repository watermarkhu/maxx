//! Collection of MATLAB objects from paths - pure Rust

use std::collections::HashMap;
use std::path::{Path, PathBuf};
use walkdir::WalkDir;

use super::errors::{MaltError, Result};
use super::objects::MatlabObject;
use super::parser::FileParser;

const MFILE_SUFFIX: &str = ".m";
const CLASSFOLDER_PREFIX: char = '@';
const NAMESPACE_PREFIX: char = '+';
const PRIVATE_FOLDER: &str = "private";
const CONTENTS_FILE: &str = "Contents.m";

/// Collection of MATLAB objects from one or more paths
pub struct PathsCollection {
    pub paths: Vec<PathBuf>,
    pub objects: HashMap<String, MatlabObject>,
}

impl PathsCollection {
    pub fn new(paths: Vec<PathBuf>, recursive: bool) -> Result<Self> {
        let mut collection = Self {
            paths: paths.clone(),
            objects: HashMap::new(),
        };

        for path in paths {
            collection.collect_path(&path, recursive)?;
        }

        Ok(collection)
    }

    pub fn get(&self, name: &str) -> Option<&MatlabObject> {
        self.objects.get(name)
    }

    pub fn contains(&self, name: &str) -> bool {
        self.objects.contains_key(name)
    }

    pub fn len(&self) -> usize {
        self.objects.len()
    }

    pub fn is_empty(&self) -> bool {
        self.objects.is_empty()
    }

    pub fn keys(&self) -> impl Iterator<Item = &String> {
        self.objects.keys()
    }

    pub fn values(&self) -> impl Iterator<Item = &MatlabObject> {
        self.objects.values()
    }

    fn collect_path(&mut self, path: &Path, recursive: bool) -> Result<()> {
        if !path.exists() {
            return Err(MaltError::FilePath(format!("Path does not exist: {}", path.display())));
        }

        if path.is_file() {
            self.collect_file(path)?;
        } else if path.is_dir() {
            self.collect_directory(path, recursive)?;
        }

        Ok(())
    }

    fn collect_file(&mut self, path: &Path) -> Result<()> {
        if path.extension().and_then(|s| s.to_str()) != Some("m") {
            return Ok(());
        }

        if path.file_name().and_then(|s| s.to_str()) == Some(CONTENTS_FILE) {
            return Ok(());
        }

        let mut parser = FileParser::new(path.to_path_buf())?;
        let obj = parser.parse()?;

        let name = obj.name().to_string();
        self.objects.insert(name, obj);

        Ok(())
    }

    fn collect_directory(&mut self, path: &Path, recursive: bool) -> Result<()> {
        let walker = if recursive {
            WalkDir::new(path)
        } else {
            WalkDir::new(path).max_depth(1)
        };

        for entry in walker {
            let entry = entry.map_err(|e| MaltError::Io(std::io::Error::other(e.to_string())))?;
            let entry_path = entry.path();

            // Skip private folders
            if entry_path.components().any(|c| c.as_os_str() == PRIVATE_FOLDER) {
                continue;
            }

            // Process .m files
            if entry_path.is_file() && entry_path.extension().and_then(|s| s.to_str()) == Some("m") {
                self.collect_file(entry_path)?;
            }
        }

        Ok(())
    }
}

/// Helper to determine if a path is a namespace
pub fn is_namespace(path: &Path) -> bool {
    path.file_name()
        .and_then(|s| s.to_str())
        .map(|s| s.starts_with(NAMESPACE_PREFIX))
        .unwrap_or(false)
}

/// Helper to determine if a path is a class folder
pub fn is_class_folder(path: &Path) -> bool {
    path.file_name()
        .and_then(|s| s.to_str())
        .map(|s| s.starts_with(CLASSFOLDER_PREFIX))
        .unwrap_or(false)
}
