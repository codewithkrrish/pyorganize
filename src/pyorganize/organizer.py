"""Core engine: scan a directory, build a move plan, apply it, undo it."""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

UNDO_FILENAME = ".pyorganize-undo.json"

DEFAULT_RULES: dict[str, list[str]] = {
    "Images": [".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".bmp", ".ico", ".tiff"],
    "Videos": [".mp4", ".mkv", ".avi", ".mov", ".webm", ".flv"],
    "Audio": [".mp3", ".wav", ".flac", ".ogg", ".m4a"],
    "Documents": [".pdf", ".doc", ".docx", ".txt", ".md", ".rtf", ".odt",
                  ".xls", ".xlsx", ".csv", ".ppt", ".pptx"],
    "Archives": [".zip", ".tar", ".gz", ".rar", ".7z"],
    "Code": [".py", ".js", ".ts", ".html", ".css", ".json", ".yaml", ".yml", ".sh"],
    "Apps": [".exe", ".msi", ".dmg", ".apk", ".deb"],
    "Fonts": [".ttf", ".otf", ".woff", ".woff2"],
}


def _normalize_ext(ext: str) -> str:
    ext = ext.lower()
    return ext if ext.startswith(".") else "." + ext


def load_rules(path: str | Path | None) -> dict[str, list[str]]:
    """Load rules, merging custom JSON rules over the defaults."""
    rules = {category: list(exts) for category, exts in DEFAULT_RULES.items()}
    if path is None:
        return rules
    custom = json.loads(Path(path).expanduser().read_text(encoding="utf-8"))
    if not isinstance(custom, dict):
        raise ValueError("Rules file must be a JSON object of category -> extensions")
    for category, exts in custom.items():
        rules[str(category)] = [_normalize_ext(e) for e in exts]
    return rules


def category_for(suffix: str, rules: dict[str, list[str]]) -> str:
    """Return the category a file extension belongs to, or 'Others'."""
    suffix = suffix.lower()
    for category, exts in rules.items():
        if suffix in exts:
            return category
    return "Others"


@dataclass
class Move:
    src: Path
    dest: Path


def _unique_dest(dest: Path) -> Path:
    """Avoid overwriting: photo.jpg -> photo (1).jpg when a clash exists."""
    if not dest.exists():
        return dest
    i = 1
    while True:
        candidate = dest.with_name(f"{dest.stem} ({i}){dest.suffix}")
        if not candidate.exists():
            return candidate
        i += 1


def plan_moves(
    directory: str | Path,
    rules: dict[str, list[str]] | None = None,
    recursive: bool = False,
    by: str = "type",
) -> list[Move]:
    """Scan a directory and return the list of moves that would organize it."""
    directory = Path(directory).expanduser().resolve()
    if not directory.is_dir():
        raise NotADirectoryError(f"Not a directory: {directory}")
    if by not in ("type", "date"):
        raise ValueError("by must be 'type' or 'date'")
    rules = rules or {c: list(e) for c, e in DEFAULT_RULES.items()}

    candidates = directory.rglob("*") if recursive else directory.iterdir()
    moves: list[Move] = []
    for path in candidates:
        if not path.is_file() or path.name.startswith(".") or path.name == UNDO_FILENAME:
            continue
        if by == "type":
            dest_dir = directory / category_for(path.suffix, rules)
        else:
            stamp = datetime.fromtimestamp(path.stat().st_mtime)
            dest_dir = directory / stamp.strftime("%Y-%m")
        if path.parent == dest_dir:
            continue  # already organized, leave it alone
        moves.append(Move(src=path, dest=_unique_dest(dest_dir / path.name)))
    return moves


def apply_moves(moves: list[Move], directory: str | Path) -> Path:
    """Execute a move plan and write an undo log. Returns the log path."""
    directory = Path(directory).expanduser().resolve()
    for move in moves:
        move.dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(move.src), str(move.dest))
    log_path = directory / UNDO_FILENAME
    log_path.write_text(
        json.dumps(
            [{"src": str(m.src), "dest": str(m.dest)} for m in moves],
            indent=2,
        ),
        encoding="utf-8",
    )
    return log_path


def undo(directory: str | Path, log_path: str | Path | None = None) -> int:
    """Restore files from the last organize operation. Returns files restored."""
    directory = Path(directory).expanduser().resolve()
    log_path = Path(log_path).expanduser() if log_path else directory / UNDO_FILENAME
    if not log_path.is_file():
        raise FileNotFoundError(f"No undo log found: {log_path}")
    entries = json.loads(log_path.read_text(encoding="utf-8"))

    restored = 0
    touched_dirs: set[Path] = set()
    for entry in entries:
        current = Path(entry["dest"])    # where the file is now
        original = Path(entry["src"])    # where it came from
        if current.is_file():
            original.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(current), str(original))
            touched_dirs.add(current.parent)
            restored += 1
    for d in touched_dirs:
        try:
            d.rmdir()  # remove the category folder if it is now empty
        except OSError:
            pass
    log_path.unlink(missing_ok=True)
    return restored
