"""
controller_audit.py — Automated static-analysis audit for "Path to Moksha"
============================================================================
PURPOSE
-------
Reads every scene Python file under src/ and performs THREE layers of checks:

  Layer 1 – ATTRIBUTE VALIDITY
      Every `input_mgr.ATTR` or `inp.ATTR` reference is extracted via AST
      and compared against the full set of valid InputManager constants.
      Any reference to a non-existent attribute (e.g. FLY_UP, DOWN) is
      flagged as a CRASH risk.

  Layer 2 – SCENE NAME SAFETY
      Every `switch_to(SCENE_XXX)` call is extracted.  The script checks
      that SCENE_XXX is both defined in settings.py AND imported in the
      calling file.  Missing imports are NameError crashes at runtime.

  Layer 3 – AUDIT CHECKLIST COVERAGE
      A machine-readable checklist (derived from controller_audit.md) lists
      which InputManager constant each scene MUST reference for each task.
      The script verifies each expected constant actually appears in the
      scene's source text.

DESIGN PHILOSOPHY — "audit without human intervention"
------------------------------------------------------
A game cannot be *played* headlessly, but the controller contract is
expressed entirely in source code.  Static analysis lets us verify:
  • No invalid attribute names that would crash at runtime.
  • No missing imports that would raise NameError.
  • No gaps where a controller action exists but is never checked.

This is akin to a "contract test" — we don't run the game, we verify that
the code *could* handle controller input correctly for every task.

USAGE
-----
  python tools/controller_audit.py

OUTPUT
------
  Prints a colour-coded report to stdout and writes
  tools/controller_audit_report.txt for permanent record.
"""

import ast
import os
import sys
import re
import textwrap
from pathlib import Path
from datetime import datetime

# ── Paths ─────────────────────────────────────────────────────────────────────
SCRIPT_DIR  = Path(__file__).resolve().parent          # tools/
BASE_DIR    = SCRIPT_DIR.parent                         # version 1/
SRC_DIR     = BASE_DIR / "src"
REPORT_FILE = SCRIPT_DIR / "controller_audit_report.txt"

# ── Valid InputManager constants (from input_manager.py) ──────────────────────
VALID_INPUT_CONSTANTS = {
    "LEFT", "RIGHT", "UP", "JUMP", "ACTION", "BACK", "FULLSCREEN",
    "MENU_UP", "MENU_DOWN", "MENU_LEFT", "MENU_RIGHT",
    "MENU_SELECT", "MENU_BACK",
    # Non-constant attributes (methods / properties) — always valid
    "just_pressed", "actions", "mouse_x", "mouse_y",
    "has_gamepad", "gamepad_name", "draw_touch_controls",
}

# ── All SCENE_ constants defined in settings.py ───────────────────────────────
VALID_SCENE_CONSTANTS = {
    "SCENE_TITLE", "SCENE_OPTIONS", "SCENE_PLAYER_SELECT",
    "SCENE_LEADERBOARD", "SCENE_TUTORIAL", "SCENE_CHARACTER_SELECT",
    "SCENE_LEVEL", "SCENE_TRANSITION", "SCENE_VICTORY",
}

# ── Audit checklist ───────────────────────────────────────────────────────────
# Format: { scene_file: [ (task_description, [required_constant_strings]) ] }
# A task PASSES if ANY of its required constants appears anywhere in the file.
AUDIT_CHECKLIST = {
    "title_screen.py": [
        ("Navigate menu up",         ["MENU_UP", "UP"]),
        ("Navigate menu down",       ["MENU_DOWN"]),
        ("Select menu item",         ["ACTION", "MENU_SELECT"]),
        ("Back / Quit",              ["BACK", "MENU_BACK"]),
    ],
    "options_scene.py": [
        ("Navigate up/down",         ["MENU_UP", "MENU_DOWN"]),
        ("Cycle option left",        ["MENU_LEFT", "LEFT"]),
        ("Cycle option right",       ["MENU_RIGHT", "RIGHT"]),
        ("Confirm / Select",         ["ACTION", "MENU_SELECT"]),
        ("Back",                     ["BACK", "MENU_BACK"]),
        ("SCENE_OPTIONS imported",   ["SCENE_OPTIONS"]),
    ],
    "player_select_scene.py": [
        ("VKB navigate left",        ["MENU_LEFT"]),
        ("VKB navigate right",       ["MENU_RIGHT"]),
        ("VKB navigate up",          ["MENU_UP"]),
        ("VKB navigate down",        ["MENU_DOWN"]),
        ("VKB press key",            ["ACTION", "MENU_SELECT"]),
        ("Profile navigate up",      ["MENU_UP"]),
        ("Profile navigate down",    ["MENU_DOWN"]),
        ("Profile launch",           ["ACTION", "MENU_SELECT"]),
        ("Back to Title",            ["BACK", "MENU_BACK"]),
    ],
    "character_select.py": [
        ("Switch character left",    ["MENU_LEFT", "LEFT"]),
        ("Switch character right",   ["MENU_RIGHT", "RIGHT"]),
        ("Confirm character",        ["ACTION", "MENU_SELECT", "JUMP"]),
        ("Back",                     ["BACK", "MENU_BACK"]),
    ],
    "tutorial_scene.py": [
        ("Upper tab switch left / right",   ["MENU_LEFT", "LEFT", "MENU_RIGHT", "RIGHT"]),
        ("Focus zone move down to buttons", ["MENU_DOWN"]),
        ("Focus zone move up to tabs",     ["MENU_UP"]),
        ("Bottom button toggle left / right",["MENU_LEFT", "LEFT", "MENU_RIGHT", "RIGHT"]),
        ("Confirm selected button",        ["ACTION", "MENU_SELECT"]),
        ("Back to previous scene",         ["BACK", "MENU_BACK"]),
    ],
    "level_scene.py": [
        ("Walk left",                ["LEFT"]),
        ("Walk right",               ["RIGHT"]),
        ("Jump",                     ["JUMP", "UP"]),
        ("Fly up",                   ["MENU_UP", "UP", "JUMP"]),
        ("Fly down",                 ["MENU_DOWN", "fly_down"]),
        ("Fly top boundary clamp",   ["can_fly"]),
        ("Dismiss popup",            ["JUMP", "ACTION", "MENU_SELECT", "BACK", "MENU_BACK"]),
        ("Temple Gate entry",        ["ACTION", "MENU_SELECT"]),
        ("Monk answer up",           ["MENU_UP"]),
        ("Monk answer down",         ["MENU_DOWN", "JUMP"]),
        ("Confirm monk answer",      ["ACTION", "MENU_SELECT"]),
        ("Start monk dialogue",      ["ACTION", "MENU_SELECT", "MENU_UP"]),
        ("Open box",                 ["ACTION", "MENU_SELECT"]),
        ("Pause / back to title",    ["BACK", "MENU_BACK"]),
        ("Game Over Phase 1 dismiss",["MENU_SELECT", "MENU_BACK"]),
        ("Game Over Phase 2 left",   ["MENU_LEFT", "LEFT"]),
        ("Game Over Phase 2 right",  ["MENU_RIGHT", "RIGHT"]),
        ("Game Over Phase 2 confirm",["ACTION", "MENU_SELECT"]),
    ],
    "transition_scene.py": [
        ("Advance scene",            ["ACTION", "JUMP", "MENU_SELECT", "MENU_BACK"]),
    ],
    "victory_scene.py": [
        ("Go to leaderboard",        ["ACTION", "JUMP", "BACK", "MENU_SELECT", "MENU_BACK"]),
    ],
    "leaderboard_scene.py": [
        ("Button toggle left",       ["MENU_LEFT", "LEFT"]),
        ("Button toggle right",      ["MENU_RIGHT", "RIGHT"]),
        ("Page scroll up",           ["MENU_UP"]),
        ("Page scroll down",         ["MENU_DOWN"]),
        ("Confirm selected button",  ["ACTION", "MENU_SELECT"]),
        ("Back",                     ["BACK", "MENU_BACK"]),
    ],
}

# ── ANSI colours ──────────────────────────────────────────────────────────────
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

def _col(text, colour): return f"{colour}{text}{RESET}"


# ═══════════════════════════════════════════════════════════════════════════════
# Layer 1 — Attribute validity
# ═══════════════════════════════════════════════════════════════════════════════

def _extract_input_attr_refs(src_text: str) -> list[tuple[int, str]]:
    """
    Walk the AST of src_text and return (line_no, attr_name) for every
    Attribute access on a node whose value is a Name called 'input_mgr' or 'inp'.
    Also catches just_pressed[input_mgr.ATTR] key patterns.
    """
    results = []
    try:
        tree = ast.parse(src_text)
    except SyntaxError:
        return results

    for node in ast.walk(tree):
        # Direct: input_mgr.ATTR  or  inp.ATTR
        if isinstance(node, ast.Attribute):
            if isinstance(node.value, ast.Name) and node.value.id in ("input_mgr", "inp"):
                results.append((node.col_offset, node.attr))
            # Subscript key: input_mgr.just_pressed[input_mgr.ATTR]
        if isinstance(node, ast.Subscript):
            sl = node.slice
            if isinstance(sl, ast.Attribute):
                if isinstance(sl.value, ast.Name) and sl.value.id in ("input_mgr", "inp"):
                    results.append((getattr(sl, "lineno", 0), sl.attr))
    return results


def layer1_attribute_validity(src_files: list[Path]) -> tuple[list, list]:
    """Returns (issues, summary_rows)."""
    issues = []
    rows   = []

    for path in src_files:
        src = path.read_text(encoding="utf-8", errors="replace")
        refs = _extract_input_attr_refs(src)

        # Also do a simple regex scan for input_mgr.WORD  (catches dynamic strings)
        regex_refs = set(re.findall(r"(?:input_mgr|inp)\.([A-Z_]+)", src))
        all_attrs  = {attr for _, attr in refs} | regex_refs

        bad = [a for a in all_attrs if a not in VALID_INPUT_CONSTANTS]
        status = _col("✅ PASS", GREEN) if not bad else _col("❌ FAIL", RED)
        rows.append(f"  {status}  {path.name}")
        for b in bad:
            msg = f"      ⚠  {path.name}: invalid attribute 'input_mgr.{b}' → runtime AttributeError"
            rows.append(_col(msg, RED))
            issues.append({"file": path.name, "attr": b})

    return issues, rows


# ═══════════════════════════════════════════════════════════════════════════════
# Layer 2 — Scene name safety
# ═══════════════════════════════════════════════════════════════════════════════

def _extract_used_scene_names(src_text: str) -> set[str]:
    """Find all SCENE_XXX identifiers actually *used* in the file."""
    return set(re.findall(r"\bSCENE_[A-Z_]+\b", src_text))


def _extract_imported_names(src_text: str) -> set[str]:
    """Find all names that are imported in the file (from ... import NAME)."""
    imported = set()
    try:
        tree = ast.parse(src_text)
    except SyntaxError:
        return imported
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            for alias in node.names:
                imported.add(alias.asname if alias.asname else alias.name)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                imported.add(alias.asname if alias.asname else alias.name)
    return imported


def layer2_scene_name_safety(src_files: list[Path]) -> tuple[list, list]:
    issues = []
    rows   = []

    for path in src_files:
        src = path.read_text(encoding="utf-8", errors="replace")
        used     = _extract_used_scene_names(src)
        imported = _extract_imported_names(src)

        file_issues = []
        for name in sorted(used):
            if name not in VALID_SCENE_CONSTANTS:
                file_issues.append((name, "not defined in settings.py"))
            elif name not in imported:
                # Check if it's imported via a wildcard or local assignment
                # (allow if it's defined inline via assignment in the file)
                if f"{name} =" not in src and f"{name}=" not in src:
                    file_issues.append((name, "used but NOT imported → NameError"))

        status = _col("✅ PASS", GREEN) if not file_issues else _col("❌ FAIL", RED)
        rows.append(f"  {status}  {path.name}")
        for name, reason in file_issues:
            msg = f"      ⚠  {path.name}: '{name}' — {reason}"
            rows.append(_col(msg, RED))
            issues.append({"file": path.name, "name": name, "reason": reason})

    return issues, rows


# ═══════════════════════════════════════════════════════════════════════════════
# Layer 3 — Audit checklist coverage
# ═══════════════════════════════════════════════════════════════════════════════

def layer3_checklist_coverage(src_files: list[Path]) -> tuple[list, list]:
    issues = []
    rows   = []

    file_map = {p.name: p for p in src_files}

    for scene_file, tasks in AUDIT_CHECKLIST.items():
        path = file_map.get(scene_file)
        if path is None:
            rows.append(_col(f"  ⚠  {scene_file} — FILE NOT FOUND", YELLOW))
            issues.append({"file": scene_file, "task": "ALL", "reason": "file missing"})
            continue

        src = path.read_text(encoding="utf-8", errors="replace")
        rows.append(f"\n  {_col(scene_file, BOLD)}")

        for task_name, required_any in tasks:
            # Task passes if at least ONE required token appears anywhere in src
            found = [tok for tok in required_any if tok in src]
            if found:
                rows.append(f"    {_col('✅', GREEN)}  {task_name}")
            else:
                rows.append(f"    {_col('❌', RED)}  {task_name}  "
                            f"— none of {required_any} found in {scene_file}")
                issues.append({
                    "file": scene_file,
                    "task": task_name,
                    "expected_any": required_any,
                })

    return issues, rows


# ═══════════════════════════════════════════════════════════════════════════════
# Main runner
# ═══════════════════════════════════════════════════════════════════════════════

def _section(title: str) -> str:
    bar = "═" * 72
    return f"\n{_col(bar, CYAN)}\n{_col('  ' + title, BOLD + CYAN)}\n{_col(bar, CYAN)}"


def run_audit():
    src_files = sorted(SRC_DIR.glob("*.py"))
    if not src_files:
        print(_col(f"ERROR: no Python files found in {SRC_DIR}", RED))
        sys.exit(1)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = []

    lines.append(_col("\n" + "═" * 72, CYAN))
    lines.append(_col("  CONTROLLER AUDIT — Path to Moksha", BOLD + CYAN))
    lines.append(_col(f"  Run at: {timestamp}", CYAN))
    lines.append(_col("═" * 72, CYAN))

    all_issues = []

    # ── Layer 1 ────────────────────────────────────────────────────────────────
    lines.append(_section("LAYER 1: Input Attribute Validity"))
    lines.append("  Checks every input_mgr.ATTR reference against known InputManager constants.")
    l1_issues, l1_rows = layer1_attribute_validity(src_files)
    lines.extend(l1_rows)
    all_issues.extend([{"layer": 1, **i} for i in l1_issues])

    # ── Layer 2 ────────────────────────────────────────────────────────────────
    lines.append(_section("LAYER 2: Scene Name Safety (NameError prevention)"))
    lines.append("  Checks every SCENE_XXX used in switch_to() is imported in the file.")
    l2_issues, l2_rows = layer2_scene_name_safety(src_files)
    lines.extend(l2_rows)
    all_issues.extend([{"layer": 2, **i} for i in l2_issues])

    # ── Layer 3 ────────────────────────────────────────────────────────────────
    lines.append(_section("LAYER 3: Controller Checklist Coverage"))
    lines.append("  Verifies each expected controller action appears in the scene source.")
    l3_issues, l3_rows = layer3_checklist_coverage(src_files)
    lines.extend(l3_rows)
    all_issues.extend([{"layer": 3, **i} for i in l3_issues])

    # ── Summary ────────────────────────────────────────────────────────────────
    lines.append(_section("SUMMARY"))
    total  = len(all_issues)
    l1_cnt = sum(1 for i in all_issues if i["layer"] == 1)
    l2_cnt = sum(1 for i in all_issues if i["layer"] == 2)
    l3_cnt = sum(1 for i in all_issues if i["layer"] == 3)

    if total == 0:
        lines.append(_col("  ✅  ALL CHECKS PASSED — controller is fully mapped", GREEN + BOLD))
    else:
        lines.append(_col(f"  ❌  {total} issue(s) found:", RED + BOLD))
        lines.append(_col(f"       Layer 1 (Attribute crashes)   : {l1_cnt}", RED if l1_cnt else GREEN))
        lines.append(_col(f"       Layer 2 (NameError crashes)   : {l2_cnt}", RED if l2_cnt else GREEN))
        lines.append(_col(f"       Layer 3 (Missing coverage)    : {l3_cnt}", YELLOW if l3_cnt else GREEN))

    lines.append(_col("\n" + "═" * 72 + "\n", CYAN))

    # ── Print & save ──────────────────────────────────────────────────────────
    output = "\n".join(lines)
    print(output)

    # Strip ANSI for the saved report
    plain = re.sub(r"\033\[[0-9;]*m", "", output)
    REPORT_FILE.write_text(plain, encoding="utf-8")
    print(_col(f"  Report saved → {REPORT_FILE}", CYAN))

    return total


if __name__ == "__main__":
    issues_found = run_audit()
    sys.exit(0 if issues_found == 0 else 1)
