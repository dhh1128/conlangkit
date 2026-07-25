#!/usr/bin/env python3
"""Reject dangerous invisible / bidirectional Unicode in source files.

This guards against the "Trojan Source" (CVE-2021-42574) and GlassWorm classes
of supply-chain attack, where bidi-control or zero-width codepoints make source
render differently than it compiles/executes.

Usage:
    python3 scripts/check_unicode.py [PATH ...]

With no arguments it scans the git-tracked files in the repo. Exits non-zero and
prints every offending location if any disallowed codepoint is found.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

# Codepoints that have no legitimate business in source and are the vector for
# visual-spoofing attacks: bidirectional controls, zero-width characters, and a
# few other invisibles. Named for the report.
DISALLOWED: dict[int, str] = {
    0x202A: "LEFT-TO-RIGHT EMBEDDING",
    0x202B: "RIGHT-TO-LEFT EMBEDDING",
    0x202C: "POP DIRECTIONAL FORMATTING",
    0x202D: "LEFT-TO-RIGHT OVERRIDE",
    0x202E: "RIGHT-TO-LEFT OVERRIDE",
    0x2066: "LEFT-TO-RIGHT ISOLATE",
    0x2067: "RIGHT-TO-LEFT ISOLATE",
    0x2068: "FIRST STRONG ISOLATE",
    0x2069: "POP DIRECTIONAL ISOLATE",
    0x061C: "ARABIC LETTER MARK",
    0x200E: "LEFT-TO-RIGHT MARK",
    0x200F: "RIGHT-TO-LEFT MARK",
    0x200B: "ZERO WIDTH SPACE",
    0x200C: "ZERO WIDTH NON-JOINER",
    0x200D: "ZERO WIDTH JOINER",
    0x2060: "WORD JOINER",
    0xFEFF: "ZERO WIDTH NO-BREAK SPACE (BOM)",
    0x00AD: "SOFT HYPHEN",
    0x180E: "MONGOLIAN VOWEL SEPARATOR",
    0x2028: "LINE SEPARATOR",
    0x2029: "PARAGRAPH SEPARATOR",
}

# Only scan text/source we author. Binary and data blobs are skipped.
TEXT_SUFFIXES = {
    ".py",
    ".pyi",
    ".toml",
    ".cfg",
    ".ini",
    ".yml",
    ".yaml",
    ".json",
    ".md",
    ".txt",
    ".sh",
    ".js",
    ".ts",
    ".editorconfig",
    ".rst",
}


def tracked_files() -> list[Path]:
    try:
        out = subprocess.run(["git", "ls-files"], capture_output=True, text=True, check=True).stdout
    except (subprocess.CalledProcessError, FileNotFoundError):
        return [p for p in Path(".").rglob("*") if p.is_file()]
    return [Path(line) for line in out.splitlines() if line]


def should_scan(path: Path) -> bool:
    return path.suffix in TEXT_SUFFIXES or path.name in {".editorconfig"}


def scan(path: Path) -> list[tuple[int, int, int, str]]:
    findings: list[tuple[int, int, int, str]] = []
    try:
        text = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return findings
    for lineno, line in enumerate(text.splitlines(), start=1):
        for col, ch in enumerate(line, start=1):
            name = DISALLOWED.get(ord(ch))
            if name is not None:
                findings.append((lineno, col, ord(ch), name))
    return findings


def main(argv: list[str]) -> int:
    if argv:
        targets = [Path(a) for a in argv]
    else:
        targets = [p for p in tracked_files() if should_scan(p)]

    total = 0
    for path in targets:
        if not path.is_file():
            continue
        for lineno, col, cp, name in scan(path):
            total += 1
            print(f"{path}:{lineno}:{col}: disallowed U+{cp:04X} {name}")

    if total:
        print(f"\nFound {total} disallowed Unicode codepoint(s).", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
