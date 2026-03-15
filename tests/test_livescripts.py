"""Tests for MATLAB live script parsing and collection."""

from __future__ import annotations

import zipfile
from pathlib import Path

import pytest

from maxx.collection import PathsCollection
from maxx.livescript import LiveScriptParser, _is_binary_mlx
from maxx.objects import LiveScript, LiveScriptSection

LIVESCRIPTS_DIR = Path(__file__).parent / "livescripts"


class TestLiveScriptSection:
    """Tests for the LiveScriptSection data class."""

    def test_init(self):
        section = LiveScriptSection("code", "x = 1;")
        assert section.kind == "code"
        assert section.content == "x = 1;"

    def test_repr(self):
        section = LiveScriptSection("text", "Hello world")
        assert "text" in repr(section)

    def test_long_content_repr_truncated(self):
        section = LiveScriptSection("code", "a" * 100)
        assert len(repr(section)) < 200


class TestLiveScriptObject:
    """Tests for the LiveScript data class."""

    def test_init_no_sections(self):
        ls = LiveScript("my_script", filepath=LIVESCRIPTS_DIR / "demo_live.m")
        assert ls.name == "my_script"
        assert ls.sections == []

    def test_init_with_sections(self):
        sections = [
            LiveScriptSection("text", "Description"),
            LiveScriptSection("code", "x = 1;"),
        ]
        ls = LiveScript("demo", filepath=LIVESCRIPTS_DIR / "demo_live.m", sections=sections)
        assert len(ls.sections) == 2
        assert ls.sections[0].kind == "text"
        assert ls.sections[1].kind == "code"

    def test_kind(self):
        from maxx.enums import Kind

        ls = LiveScript("demo", filepath=LIVESCRIPTS_DIR / "demo_live.m")
        assert ls.kind is Kind.LIVE_SCRIPT

    def test_is_live_script(self):
        ls = LiveScript("demo", filepath=LIVESCRIPTS_DIR / "demo_live.m")
        assert ls.is_live_script


class TestIsBinaryMlx:
    """Tests for the _is_binary_mlx helper."""

    def test_binary_file_detected(self):
        path = LIVESCRIPTS_DIR / "demo_binary.mlx"
        assert _is_binary_mlx(path) is True

    def test_text_file_not_binary(self, tmp_path):
        p = tmp_path / "plain.mlx"
        p.write_text("x = 1;\n", encoding="utf-8")
        assert _is_binary_mlx(p) is False

    def test_nonexistent_file(self, tmp_path):
        p = tmp_path / "ghost.mlx"
        assert _is_binary_mlx(p) is False


class TestPlaintextLiveScriptParser:
    """Tests for the plain-text live code parser."""

    def test_parse_sections_count(self):
        path = LIVESCRIPTS_DIR / "demo_live.m"
        parser = LiveScriptParser(path)
        ls = parser.parse_plaintext()
        assert isinstance(ls, LiveScript)
        assert len(ls.sections) >= 2

    def test_has_code_sections(self):
        path = LIVESCRIPTS_DIR / "demo_live.m"
        parser = LiveScriptParser(path)
        ls = parser.parse_plaintext()
        kinds = {s.kind for s in ls.sections}
        assert "code" in kinds

    def test_has_text_sections(self):
        path = LIVESCRIPTS_DIR / "demo_live.m"
        parser = LiveScriptParser(path)
        ls = parser.parse_plaintext()
        kinds = {s.kind for s in ls.sections}
        assert "text" in kinds

    def test_name_is_stem(self):
        path = LIVESCRIPTS_DIR / "demo_live.m"
        parser = LiveScriptParser(path)
        ls = parser.parse_plaintext()
        assert ls.name == "demo_live"

    def test_filepath(self):
        path = LIVESCRIPTS_DIR / "demo_live.m"
        parser = LiveScriptParser(path)
        ls = parser.parse_plaintext()
        assert ls.filepath == path

    def test_sections_not_empty(self):
        path = LIVESCRIPTS_DIR / "demo_live.m"
        parser = LiveScriptParser(path)
        ls = parser.parse_plaintext()
        for section in ls.sections:
            assert section.content.strip() != ""


class TestBinaryMlxParser:
    """Tests for the binary .mlx parser."""

    def test_parse_returns_live_script(self):
        path = LIVESCRIPTS_DIR / "demo_binary.mlx"
        parser = LiveScriptParser(path)
        ls = parser.parse()
        assert isinstance(ls, LiveScript)

    def test_name_is_stem(self):
        path = LIVESCRIPTS_DIR / "demo_binary.mlx"
        parser = LiveScriptParser(path)
        ls = parser.parse()
        assert ls.name == "demo_binary"

    def test_sections_present(self):
        path = LIVESCRIPTS_DIR / "demo_binary.mlx"
        parser = LiveScriptParser(path)
        ls = parser.parse()
        assert len(ls.sections) >= 1

    def test_code_sections_present(self):
        path = LIVESCRIPTS_DIR / "demo_binary.mlx"
        parser = LiveScriptParser(path)
        ls = parser.parse()
        code_sections = [s for s in ls.sections if s.kind == "code"]
        assert len(code_sections) >= 1

    def test_text_sections_present(self):
        path = LIVESCRIPTS_DIR / "demo_binary.mlx"
        parser = LiveScriptParser(path)
        ls = parser.parse()
        text_sections = [s for s in ls.sections if s.kind == "text"]
        assert len(text_sections) >= 1

    def test_code_content(self):
        path = LIVESCRIPTS_DIR / "demo_binary.mlx"
        parser = LiveScriptParser(path)
        ls = parser.parse()
        all_code = "\n".join(s.content for s in ls.sections if s.kind == "code")
        assert "x = 1:10;" in all_code

    def test_invalid_zip_raises(self, tmp_path):
        p = tmp_path / "bad.mlx"
        p.write_bytes(b"PK this is not a real zip")
        with pytest.raises(ValueError, match="Not a valid .mlx"):
            LiveScriptParser(p).parse()

    def test_missing_document_xml_raises(self, tmp_path):
        p = tmp_path / "noxml.mlx"
        with zipfile.ZipFile(p, "w") as zf:
            zf.writestr("some_other_file.txt", "content")
        with pytest.raises(ValueError, match="Cannot find document.xml"):
            LiveScriptParser(p).parse()


class TestPathsCollectionLiveScripts:
    """Tests for PathsCollection with live script support."""

    def test_live_scripts_excluded_by_default(self):
        """Live scripts are NOT collected when parse_live_scripts=False (default)."""
        collection = PathsCollection(
            [LIVESCRIPTS_DIR],
            parse_live_scripts=False,
        )
        # demo_binary.mlx should not appear
        assert "demo_binary" not in collection

    def test_live_scripts_included_when_enabled(self):
        """Live scripts ARE collected when parse_live_scripts=True."""
        collection = PathsCollection(
            [LIVESCRIPTS_DIR],
            parse_live_scripts=True,
        )
        assert "demo_binary" in collection

    def test_live_script_object_type(self):
        """Collected live script yields a LiveScript object."""
        collection = PathsCollection(
            [LIVESCRIPTS_DIR],
            parse_live_scripts=True,
        )
        obj = collection["demo_binary"]
        assert isinstance(obj, LiveScript)

    def test_live_script_sections_populated(self):
        """Collected LiveScript has sections."""
        collection = PathsCollection(
            [LIVESCRIPTS_DIR],
            parse_live_scripts=True,
        )
        obj = collection["demo_binary"]
        assert isinstance(obj, LiveScript)
        assert len(obj.sections) >= 1

    def test_regular_m_file_still_collected(self):
        """Regular .m files in the same directory are still collected."""
        collection = PathsCollection(
            [LIVESCRIPTS_DIR],
            parse_live_scripts=True,
        )
        # demo_live.m is a plain .m file (treated as script by default)
        assert "demo_live" in collection
