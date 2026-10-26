"""Helpers for tests that read the source rather than run it.

Several guards here are about which abstract action a scene listens to, or which
keyword it routes with. Those read better as a check on the code than as a
headless replay of a button press — and they run on the dependency-free CI worker,
where pygame is not installed.

Comments have to be stripped first: the lines explaining why an action is *absent*
name it too, so an unstripped search matches its own rationale.
"""

from __future__ import annotations

import ast
from pathlib import Path


def strip_comments(source: str) -> str:
    """The same source with `#` comments removed, quotes respected."""
    out = []
    for line in source.splitlines():
        quote = None
        cut = len(line)
        for i, ch in enumerate(line):
            if quote:
                if ch == quote:
                    quote = None
            elif ch in "\"'":
                quote = ch
            elif ch == "#":
                cut = i
                break
        out.append(line[:cut])
    return "\n".join(out)


def function_source(path: Path, name: str) -> str:
    """The code of one function or method, by name, with comments removed."""
    text = path.read_text(encoding="utf-8")
    for node in ast.walk(ast.parse(text)):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            return strip_comments(ast.get_source_segment(text, node) or "")
    raise AssertionError(f"{name} not found in {path.name}")
