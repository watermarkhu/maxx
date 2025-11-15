"""Command-line interface for MATLAB linting."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from maxx.lint.config import LintConfig
from maxx.lint.engine import LintEngine
from maxx.lint.rule import RuleRegistry
from maxx.logger import logger


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser for the CLI.

    Returns:
        Argument parser instance
    """
    parser = argparse.ArgumentParser(
        prog="maxx",
        description="MATLAB linting tool with tree-sitter",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Add subcommands
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Lint command
    lint_parser = subparsers.add_parser(
        "lint",
        help="Lint MATLAB files",
        description="Lint MATLAB files using configured rules",
    )
    lint_parser.add_argument(
        "paths",
        nargs="*",
        type=Path,
        default=[Path.cwd()],
        help="Paths to lint (files or directories). Defaults to current directory.",
    )
    lint_parser.add_argument(
        "--config",
        type=Path,
        help="Path to matlab.toml configuration file",
    )
    lint_parser.add_argument(
        "--no-recursive",
        action="store_true",
        help="Don't recursively search directories",
    )
    lint_parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Show verbose output including node text",
    )
    lint_parser.add_argument(
        "--check",
        action="store_true",
        help="Exit with error code if violations are found",
    )
    lint_parser.add_argument(
        "--select",
        type=str,
        help="Comma-separated list of rule patterns to select (e.g., 'W*,E001')",
    )
    lint_parser.add_argument(
        "--ignore",
        type=str,
        help="Comma-separated list of rule IDs to ignore (e.g., 'W001,W002')",
    )
    lint_parser.add_argument(
        "--output",
        "-o",
        type=Path,
        help="Export violations to JSON file",
    )

    # Rules command
    rules_parser = subparsers.add_parser(
        "rules",
        help="List available linting rules",
        description="Display all available linting rules",
    )
    rules_parser.add_argument(
        "--all",
        action="store_true",
        help="Show all rules including disabled ones",
    )

    # Version command
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 0.6.0",
    )

    return parser


def cmd_lint(args: argparse.Namespace) -> int:
    """Execute the lint command.

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code (0 for success, 1 for violations found)
    """
    # Load configuration
    if args.config:
        config = LintConfig.from_toml(args.config)
    else:
        config = LintConfig.find_config()

    # Override config with CLI arguments
    if args.select:
        config.select = [s.strip() for s in args.select.split(",")]
    if args.ignore:
        config.ignore = [s.strip() for s in args.ignore.split(",")]

    # Initialize engine
    engine = LintEngine(config=config)

    # Lint the paths
    violations = engine.lint_paths(
        paths=args.paths,
        recursive=not args.no_recursive,
    )

    # Export to JSON if requested
    if args.output:
        engine.export_violations_to_json(violations, args.output)
        logger.info(f"Results exported to {args.output}")
    else:
        # Print violations to stdout
        engine.print_violations(violations, verbose=args.verbose)

    # Return appropriate exit code
    if args.check and violations:
        return 1
    return 0


def cmd_rules(args: argparse.Namespace) -> int:
    """Execute the rules command.

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code (always 0)
    """
    # Initialize registry and load rules
    registry = RuleRegistry()
    rules_dir = Path(__file__).parent.parent / "rules"
    if rules_dir.exists():
        registry.load_rules_from_directory(rules_dir)

    # Get rules to display
    if args.all:
        rules = registry.get_all_rules()
        print(f"All available rules ({len(rules)}):\n")
    else:
        rules = registry.get_enabled_rules()
        print(f"Enabled rules ({len(rules)}):\n")

    # Print rules in a table format
    if not rules:
        print("No rules found.")
        return 0

    # Find maximum widths for formatting
    max_id_len = max(len(rule.id) for rule in rules)
    max_name_len = max(len(rule.name) for rule in rules)
    max_severity_len = max(len(rule.severity) for rule in rules)

    # Print header
    header = f"{'ID':<{max_id_len}}  {'Name':<{max_name_len}}  {'Severity':<{max_severity_len}}  Description"
    print(header)
    print("-" * len(header))

    # Print each rule
    for rule in sorted(rules, key=lambda r: r.id):
        enabled_marker = "" if rule.enabled else " (disabled)"
        print(
            f"{rule.id:<{max_id_len}}  "
            f"{rule.name:<{max_name_len}}  "
            f"{rule.severity:<{max_severity_len}}  "
            f"{rule.description}{enabled_marker}"
        )

    return 0


def main() -> int:
    """Main entry point for the CLI.

    Returns:
        Exit code
    """
    parser = create_parser()
    args = parser.parse_args()

    # If no command specified, show help
    if not args.command:
        parser.print_help()
        return 0

    # Execute the appropriate command
    try:
        if args.command == "lint":
            return cmd_lint(args)
        elif args.command == "rules":
            return cmd_rules(args)
        else:
            parser.print_help()
            return 0
    except KeyboardInterrupt:
        logger.info("\nInterrupted by user")
        return 130
    except Exception as e:
        logger.error(f"Error: {e}")
        if args.verbose if hasattr(args, "verbose") else False:
            raise
        return 1


if __name__ == "__main__":
    sys.exit(main())
