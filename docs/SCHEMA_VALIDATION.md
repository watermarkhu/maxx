# Configuration Schema Validation

This guide explains how to enable schema validation and autocomplete for `matlab.toml` configuration files in various editors.

## What is Schema Validation?

Schema validation provides:
- **Autocomplete**: Suggestions for configuration options as you type
- **Validation**: Real-time error checking for invalid values
- **Documentation**: Inline help for configuration fields

## Generating the Schema

The maxx linter includes a built-in command to generate a JSON schema:

```bash
# Print schema to stdout
maxx schema

# Save schema to a file
maxx schema -o matlab-lint-schema.json
```

The schema is also bundled with the package at:
```
<package-install-dir>/maxx/schemas/matlab-lint-config.json
```

## VSCode Setup

### Method 1: Using Even Better TOML Extension

1. **Install the extension**:
   - Open VSCode
   - Go to Extensions (Ctrl+Shift+X / Cmd+Shift+X)
   - Search for "Even Better TOML"
   - Install the extension by tamasfe

2. **Configure schema mapping**:
   - Open VSCode settings (Ctrl+, / Cmd+,)
   - Search for "even-better-toml.schema"
   - Click "Edit in settings.json"
   - Add the following configuration:

```json
{
  "evenBetterToml.schema.associations": {
    ".*matlab\\.toml$": {
      "keys": {
        "lint": "file:///path/to/matlab-lint-schema.json"
      }
    }
  }
}
```

3. **Generate and place the schema**:
```bash
# In your project root or a shared location
maxx schema -o ~/.config/maxx/matlab-lint-schema.json
```

4. **Update the path in settings.json** to point to your schema file location.

### Method 2: Using taplo Extension

1. **Install taplo**:
   - Open VSCode Extensions
   - Search for "Even Better TOML" or "taplo"
   - Install the extension

2. **Create a taplo configuration** (`.taplo.toml` in your project root):

```toml
[[rule]]
# Match matlab.toml files
name = "matlab-config"
include = ["**/matlab.toml"]

# Associate the lint section with the schema
[rule.schema]
path = "file:///path/to/matlab-lint-schema.json"
# For the [lint] section only
keys = ["lint"]
```

3. **Generate the schema**:
```bash
maxx schema -o .vscode/matlab-lint-schema.json
```

4. **Update the path** in `.taplo.toml` to match your schema location:
```toml
path = "file:///${workspaceFolder}/.vscode/matlab-lint-schema.json"
```

## Example matlab.toml with Validation

Once configured, your `matlab.toml` will have autocomplete and validation:

```toml
[lint]
# Auto-complete will suggest: enabled, select, ignore, exclude, rule_config
enabled = true

# Validation will check that these are arrays of strings
select = ["MW-*", "E001"]
ignore = ["MW-F001"]

# Validation will check that these are valid glob patterns
exclude = ["tests/**", "build/**"]

# Per-rule configuration
[lint.rule_config.MW-L001]
max_length = 100
```

## IntelliJ / PyCharm Setup

1. **Install TOML plugin** (if not already installed)
2. **Add schema mapping**:
   - Go to Settings → Languages & Frameworks → Schemas and DTDs → JSON Schema Mappings
   - Click "+" to add new mapping
   - Set:
     - Name: "MATLAB Lint Config"
     - Schema file: Browse to your generated schema file
     - Schema version: JSON Schema version 7
   - Add file path pattern: `**/matlab.toml` with scope "lint"

## Vim/Neovim Setup

### Using coc.nvim with coc-json

1. **Install coc-json**:
```vim
:CocInstall coc-json
```

2. **Configure schema** in `:CocConfig`:
```json
{
  "json.schemas": [
    {
      "fileMatch": ["**/matlab.toml"],
      "url": "file:///path/to/matlab-lint-schema.json"
    }
  ]
}
```

### Using yaml-language-server (for YAML)

If you prefer YAML configuration files, convert your matlab.toml to matlab.yaml and use yaml-language-server with schema validation.

## Validation Without IDE

You can also validate configuration files programmatically:

```python
from pathlib import Path
from maxx.lint.config import LintConfig
from pydantic import ValidationError

try:
    config = LintConfig.from_toml(Path("matlab.toml"))
    print("✓ Configuration is valid")
except ValidationError as e:
    print("✗ Configuration is invalid:")
    print(e)
```

## Schema Contents

The schema validates the `[lint]` section of `matlab.toml` with the following fields:

- **enabled** (boolean): Whether linting is globally enabled (default: true)
- **select** (array of strings): Rule patterns to enable (e.g., `["MW-*", "E001"]`)
- **ignore** (array of strings): Rule IDs to disable (e.g., `["MW-F001"]`)
- **exclude** (array of strings): File/directory patterns to exclude (e.g., `["tests/**"]`)
- **rule_config** (object): Per-rule configuration overrides

## Example Configurations

### Minimal Configuration
```toml
[lint]
enabled = true
```

### Select Specific Rules
```toml
[lint]
select = ["MW-N*", "MW-F*", "E001"]  # Only naming and function rules
ignore = ["MW-N007"]  # Except this one
```

### Exclude Directories
```toml
[lint]
exclude = [
  "tests/**",
  "build/**",
  "**/*_generated.m"
]
```

### Custom Rule Configuration
```toml
[lint]
# Customize line length limit
[lint.rule_config.MW-L001]
max_length = 120
```

## Troubleshooting

### Schema not working in VSCode

1. **Check extension is installed**: Ensure "Even Better TOML" is installed and enabled
2. **Verify file path**: Make sure the schema path in settings.json is correct and uses `file://` protocol
3. **Check file pattern**: Ensure the regex pattern matches your file name (e.g., `.*matlab\\.toml$`)
4. **Reload window**: Try reloading VSCode (Ctrl+Shift+P → "Reload Window")

### Schema path issues

- Use absolute paths: `file:///home/user/.config/maxx/schema.json`
- For workspace-relative paths: `file:///${workspaceFolder}/schema.json`
- On Windows: `file:///C:/Users/username/.config/maxx/schema.json`

### Validation not appearing

- Ensure you're editing the `[lint]` section specifically
- Check that the TOML file is valid (no syntax errors)
- Try saving the file to trigger re-validation

## Updating the Schema

When you update maxx, regenerate the schema to get the latest configuration options:

```bash
maxx schema -o ~/.config/maxx/matlab-lint-schema.json
```

Or use the bundled schema which is updated with each maxx release.
