"""Tests for argument parsing and decoding robustness."""

from pathlib import Path

from maxx.collection import PathsCollection
from maxx.enums import ArgumentKind
from maxx.expressions import Expr
from maxx.objects import Function
from maxx.treesitter import FileParser


def test_class_property_simple(tmp_path: Path):
    """Name-value arguments from a class property: `opts.?namespace.path.to.class`."""
    code = "function myFunc(opts)\narguments\n    opts.?namespace.path.to.class;\nend\nend\n"
    p = tmp_path / "myFunc.m"
    p.write_text(code, encoding="utf-8")
    obj = FileParser(p).parse()
    assert isinstance(obj, Function)
    assert obj.name == "myFunc"
    assert obj.arguments is not None
    assert len(obj.arguments) == 1
    arg = obj.arguments[0]
    assert arg.name == "opts"
    assert arg.kind == ArgumentKind.keyword_only
    assert isinstance(arg.type, Expr)
    assert str(arg.type) == "namespace.path.to.class"
    assert arg.type.doc == ""


def test_class_property_dotted(tmp_path: Path):
    code = "function myFunc(opts)\narguments\n    opts.?MyClass\nend\nend\n"
    p = tmp_path / "myFunc.m"
    p.write_text(code, encoding="utf-8")
    obj = FileParser(p).parse()
    assert isinstance(obj, Function)
    arg = next(a for a in obj.arguments if a.name == "opts")
    assert isinstance(arg.type, Expr)
    assert str(arg.type) == "MyClass"
    assert arg.kind == ArgumentKind.keyword_only


def test_class_property_with_mixed_args(tmp_path: Path):
    code = "function myFunc(opts, x)\narguments\n    x (1,:) double\n    opts.?MyClass\nend\nend\n"
    p = tmp_path / "myFunc.m"
    p.write_text(code, encoding="utf-8")
    obj = FileParser(p).parse()
    assert isinstance(obj, Function)
    names = {a.name for a in obj.arguments}
    assert names == {"x", "opts"}
    assert str(next(a for a in obj.arguments if a.name == "x").type) == "double"
    assert str(next(a for a in obj.arguments if a.name == "opts").type) == "MyClass"


def test_class_property_paths_collection_integration(tmp_path: Path):
    """Ensure PathsCollection.addpath does not throw on file with class_property."""
    ns_dir = tmp_path / "+namespace"
    ns_dir.mkdir()
    # Create a class for namespace.path.to.class ? Create folder +namespace/path
    sub = ns_dir / "+path"
    sub.mkdir()
    (sub / "to.m").write_text("classdef to\nend\n", encoding="utf-8")
    func = tmp_path / "myFunc.m"
    func.write_text(
        "function myFunc(opts)\narguments\n    opts.?namespace.path.to.to;\nend\nend\n",
        encoding="utf-8",
    )
    pc = PathsCollection([tmp_path], recursive=True)
    obj = pc["myFunc"]
    assert obj is not None
    assert obj.arguments is not None
    assert any(a.name == "opts" for a in obj.arguments)


def test_readme_non_utf8(tmp_path: Path):
    """README.md with invalid utf-8 must not throw."""
    (tmp_path / "README.md").write_bytes(b"# Title\nHello \xff\xfe world\n")
    (tmp_path / "foo.m").write_text("function foo; end", encoding="utf-8")
    pc = PathsCollection([tmp_path], working_directory=tmp_path)
    # _collect_readme_md is called lazily when resolving folder; call directly
    from maxx.collection import _PathResolver

    resolver = _PathResolver(tmp_path, pc)
    doc = resolver._collect_readme_md(tmp_path, parent=None)  # ty: ignore[invalid-argument-type]
    assert doc is not None
    assert "Hello" in doc.value
    assert "�" in doc.value  # replacement char


def test_fileparser_non_utf8_content_replace(tmp_path: Path):
    """FileParser.content with forced utf-8 invalid bytes uses replace."""
    p = tmp_path / "bad.m"
    p.write_bytes(b"function y=bad(x)\n% \x80 bad\n y=x;\nend\n")
    parser = FileParser(p)
    parser.encoding = "utf-8"
    assert "�" in parser.content
    # Expr iterate also uses replace
    from unittest.mock import MagicMock

    from maxx.expressions import Expr

    mock = MagicMock()
    mock.text = b"\xff\xfehello"
    expr = Expr(nodes=[mock], encoding="utf-8")
    assert "�" in str(expr)
