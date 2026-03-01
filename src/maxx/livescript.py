"""Parsers for MATLAB live script files.

Supports two formats:

- Binary ``.mlx`` (ZIP / Office Open XML) — available since MATLAB R2016a.
- Plain-text live code (``.m``) — the new human-readable format introduced in
  MATLAB R2025a.  Files saved in this format can be recognised by MATLAB's own
  "Live Editor" but are otherwise indistinguishable from regular ``.m`` files
  by extension alone; callers are responsible for deciding when to invoke the
  plain-text parser.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path
from typing import TYPE_CHECKING

import charset_normalizer
from loguru import logger

from maxx.objects import LiveScript, LiveScriptSection

if TYPE_CHECKING:
    from maxx.collection import PathsCollection

__all__ = ["LiveScriptParser"]

# ---------------------------------------------------------------------------
# Namespace map used in the MATLAB Office Open XML document format
# ---------------------------------------------------------------------------
# The primary Word Processing ML namespace used inside matlab/document.xml
_W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
_W = f"{{{_W_NS}}}"

# Style value that MATLAB assigns to code paragraphs inside document.xml
_CODE_STYLE = "matlab-Code"


def _is_binary_mlx(path: Path) -> bool:
    """Return *True* when *path* is a binary (ZIP-based) ``.mlx`` file."""
    try:
        with open(path, "rb") as fh:
            magic = fh.read(2)
        return magic == b"PK"
    except OSError:
        return False


# ---------------------------------------------------------------------------
# Binary .mlx parser (ZIP / Office Open XML)
# ---------------------------------------------------------------------------


def _parse_binary_mlx(path: Path, paths_collection: PathsCollection | None = None) -> LiveScript:
    """Parse a binary ``.mlx`` file and return a :class:`~maxx.objects.LiveScript`.

    The binary format is a ZIP archive.  The primary content is stored in
    ``matlab/document.xml`` using an Office Open XML (OOXML) dialect.

    Code paragraphs carry the paragraph style ``matlab-Code``; everything else
    is treated as formatted text.

    Parameters:
        path: Path to the ``.mlx`` file.
        paths_collection: Optional paths collection for the object.

    Returns:
        A :class:`~maxx.objects.LiveScript` whose :attr:`sections` list
        contains the ordered code and text sections extracted from the file.

    Raises:
        ValueError: When the archive does not contain ``matlab/document.xml``.
    """
    logger.debug(f"Parsing binary .mlx file: {path}")

    try:
        with zipfile.ZipFile(path, "r") as zf:
            names = zf.namelist()
            # Locate document.xml – the path can vary slightly across releases
            doc_name = next(
                (n for n in names if n.endswith("document.xml")),
                None,
            )
            if doc_name is None:
                raise ValueError(f"Cannot find document.xml inside the .mlx archive: {path}")
            xml_bytes = zf.read(doc_name)
    except zipfile.BadZipFile as exc:
        raise ValueError(f"Not a valid .mlx (ZIP) file: {path}") from exc

    sections = _parse_document_xml(xml_bytes)

    live_script = LiveScript(
        path.stem,
        filepath=path,
        sections=sections,
        paths_collection=paths_collection,
    )
    logger.info(f"Parsed binary .mlx '{path.name}': {len(sections)} section(s)")
    return live_script


def _parse_document_xml(xml_bytes: bytes) -> list[LiveScriptSection]:
    """Extract ordered code / text sections from ``document.xml`` bytes.

    Parameters:
        xml_bytes: Raw bytes of ``document.xml``.

    Returns:
        An ordered list of :class:`~maxx.objects.LiveScriptSection` objects.
    """
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError as exc:
        logger.warning(f"Failed to parse document.xml XML: {exc}")
        return []

    body = root.find(f"{_W}body")
    if body is None:
        # Try without explicit namespace (some older releases omit it)
        body = root.find("body")
    if body is None:
        logger.warning("document.xml has no <body> element; returning empty sections")
        return []

    sections: list[LiveScriptSection] = []
    current_kind: str | None = None
    current_lines: list[str] = []

    def _flush() -> None:
        if current_kind is not None and current_lines:
            sections.append(LiveScriptSection(current_kind, "\n".join(current_lines)))

    for para in body.iter(f"{_W}p"):
        kind = _paragraph_kind(para)
        text = _paragraph_text(para)

        if kind != current_kind:
            _flush()
            current_kind = kind
            current_lines = [text] if text else []
        else:
            if text:
                current_lines.append(text)

    _flush()

    # Remove empty leading/trailing sections
    sections = [s for s in sections if s.content.strip()]
    return sections


def _paragraph_kind(para: ET.Element) -> str:
    """Return ``"code"`` or ``"text"`` for the given paragraph element."""
    ppr = para.find(f"{_W}pPr")
    if ppr is not None:
        style = ppr.find(f"{_W}pStyle")
        if style is not None:
            val = style.get(f"{_W}val") or style.get("val") or ""
            if val == _CODE_STYLE:
                return "code"
    return "text"


def _paragraph_text(para: ET.Element) -> str:
    """Concatenate all ``<w:t>`` text runs inside a paragraph."""
    parts: list[str] = []
    for run in para.iter(f"{_W}r"):
        for t_elem in run.iter(f"{_W}t"):
            if t_elem.text:
                parts.append(t_elem.text)
    return "".join(parts)


# ---------------------------------------------------------------------------
# Plain-text live code parser (R2025a .m format)
# ---------------------------------------------------------------------------
# In R2025a, MATLAB introduced a plain-text live code file format saved with
# the ``.m`` extension.  Sections are separated by ``%%`` lines (identical to
# regular MATLAB cell-mode scripts).  Text (narrative) sections are encoded as
# specially formatted block comments, whereas code sections contain executable
# MATLAB code.
#
# Heuristics used here:
#  - A line starting with ``%%`` (optionally followed by a title) marks the
#    beginning of a new section.
#  - A paragraph that consists *entirely* of ``%``-prefixed lines (and
#    contains no executable statements) is treated as a *text* section.
#  - Everything else is a *code* section.
#
# These heuristics are intentionally conservative: the R2025a format
# specification is not yet fully public, so we avoid hard-coding markers that
# may change.

_SECTION_RE = re.compile(r"^\s*%%(\s|$)")
_COMMENT_RE = re.compile(r"^\s*%")


def _parse_plaintext_live_code(
    path: Path, paths_collection: PathsCollection | None = None
) -> LiveScript:
    """Parse a plain-text live code ``.m`` file (R2025a format).

    Parameters:
        path: Path to the ``.m`` file.
        paths_collection: Optional paths collection.

    Returns:
        A :class:`~maxx.objects.LiveScript` with ordered sections.
    """
    logger.debug(f"Parsing plain-text live code file: {path}")

    result = charset_normalizer.from_path(path).best()
    encoding = result.encoding if result else "utf-8"
    with open(path, encoding=encoding, errors="replace") as fh:
        raw = fh.read()

    sections = _split_plaintext_sections(raw)

    live_script = LiveScript(
        path.stem,
        filepath=path,
        sections=sections,
        paths_collection=paths_collection,
    )
    logger.info(f"Parsed plain-text live code '{path.name}': {len(sections)} section(s)")
    return live_script


def _split_plaintext_sections(source: str) -> list[LiveScriptSection]:
    """Split *source* into an ordered list of live-script sections.

    Parameters:
        source: The raw text content of the ``.m`` live code file.

    Returns:
        An ordered list of :class:`~maxx.objects.LiveScriptSection` objects.
    """
    # Split on %% section markers
    raw_parts: list[str] = []
    current: list[str] = []

    for line in source.splitlines(keepends=True):
        if _SECTION_RE.match(line) and current:
            raw_parts.append("".join(current))
            current = [line]
        else:
            current.append(line)
    if current:
        raw_parts.append("".join(current))

    sections: list[LiveScriptSection] = []
    for part in raw_parts:
        part = part.strip()
        if not part:
            continue
        kind = _classify_plaintext_section(part)
        content = _strip_section_header(part)
        if content.strip():
            sections.append(LiveScriptSection(kind, content))
    return sections


def _classify_plaintext_section(text: str) -> str:
    """Return ``"text"`` when *text* is all comments, else ``"code"``."""
    lines = [ln for ln in text.splitlines() if ln.strip()]
    if not lines:
        return "text"
    # Skip the %% header line when present
    body_lines = lines[1:] if _SECTION_RE.match(lines[0]) else lines
    if not body_lines:
        return "text"
    if all(_COMMENT_RE.match(ln) for ln in body_lines):
        return "text"
    return "code"


def _strip_section_header(text: str) -> str:
    """Remove the leading ``%%`` section-divider line from *text*."""
    lines = text.splitlines(keepends=True)
    if lines and _SECTION_RE.match(lines[0]):
        return "".join(lines[1:]).strip()
    return text.strip()


# ---------------------------------------------------------------------------
# Public parser class
# ---------------------------------------------------------------------------


class LiveScriptParser:
    """Parse a MATLAB live script file into a :class:`~maxx.objects.LiveScript`.

    Two formats are supported:

    - Binary ``.mlx``: detected automatically via ZIP magic bytes.
    - Plain-text live code (``.m`` with R2025a markup): opt-in via
      :meth:`parse_plaintext`.

    Example::

        parser = LiveScriptParser(Path("demo.mlx"))
        live_script = parser.parse()
    """

    def __init__(
        self,
        filepath: Path,
        paths_collection: PathsCollection | None = None,
    ) -> None:
        """Initialise the parser.

        Parameters:
            filepath: Path to the live script file (``.mlx`` or ``.m``).
            paths_collection: Optional paths collection for the resulting
                :class:`~maxx.objects.LiveScript`.
        """
        self.filepath = filepath
        self.paths_collection = paths_collection

    def parse(self) -> LiveScript:
        """Parse the file and return a :class:`~maxx.objects.LiveScript`.

        For ``.mlx`` files the format is auto-detected (binary ZIP vs plain
        text).  For ``.m`` files the plain-text live-code parser is used.

        Returns:
            A :class:`~maxx.objects.LiveScript` instance.

        Raises:
            ValueError: When the file cannot be parsed.
        """
        path = self.filepath
        if path.suffix.lower() == ".mlx":
            if _is_binary_mlx(path):
                return _parse_binary_mlx(path, self.paths_collection)
            else:
                # Plain-text .mlx (future-proof; treat like R2025a .m format)
                return _parse_plaintext_live_code(path, self.paths_collection)
        else:
            return _parse_plaintext_live_code(path, self.paths_collection)

    def parse_plaintext(self) -> LiveScript:
        """Force plain-text live-code parsing regardless of file extension.

        Returns:
            A :class:`~maxx.objects.LiveScript` instance.
        """
        return _parse_plaintext_live_code(self.filepath, self.paths_collection)
