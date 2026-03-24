from __future__ import annotations

import argparse
import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

# Project name variants to remove from all copied content/paths in destination.
OLD_TERMS = [
    "EY_Techathon_Retail_agent",
    "EY_yechathon_retail_agent",  # typo variant requested by user
    "ey_techathon_retail_agent",
    "ey_yechathon_retail_agent",
]
NEW_TERM = "google_agentic"

# DB files that must exist in destination after migration.
REQUIRED_DB_FILES = ["retail_agnet.db", "chat_history.db"]

# Text-like files that are safe to rewrite in-place.
TEXT_EXTS = {
    ".py",
    ".pyi",
    ".txt",
    ".md",
    ".rst",
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".ini",
    ".cfg",
    ".env",
    ".csv",
    ".sql",
    ".xml",
    ".html",
    ".htm",
    ".css",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".sh",
    ".bat",
    ".ps1",
    ".gitignore",
    ".dockerignore",
    ".editorconfig",
    ".code-workspace",
}


@dataclass
class MigrationStats:
    copied: bool = False
    renamed_paths: int = 0
    rewritten_files: int = 0
    copied_required_db: int = 0


def replace_terms(text: str) -> str:
    out = text
    for term in OLD_TERMS:
        out = out.replace(term, NEW_TERM)
    return out


def is_probably_text_file(path: Path) -> bool:
    if path.suffix.lower() in TEXT_EXTS:
        return True
    # Extensionless files can still be text config/scripts.
    return path.suffix == ""


def rename_paths(root: Path) -> int:
    changed = 0
    all_paths = sorted(root.rglob(
        "*"), key=lambda p: len(str(p)), reverse=True)

    for path_obj in all_paths:
        new_name = replace_terms(path_obj.name)
        if new_name == path_obj.name:
            continue

        target = path_obj.with_name(new_name)
        if target.exists():
            # Skip collisions safely.
            continue

        path_obj.rename(target)
        changed += 1

    return changed


def rewrite_text_files(root: Path) -> int:
    changed = 0

    for file_path in root.rglob("*"):
        if not file_path.is_file() or not is_probably_text_file(file_path):
            continue

        try:
            raw = file_path.read_bytes()
            if b"\x00" in raw:
                # Likely binary
                continue
            text = raw.decode("utf-8")
        except Exception:
            continue

        new_text = replace_terms(text)
        if new_text != text:
            file_path.write_text(new_text, encoding="utf-8", newline="")
            changed += 1

    return changed


def find_files_by_name(root: Path, filename: str) -> list[Path]:
    filename_lower = filename.lower()
    return [p for p in root.rglob("*") if p.is_file() and p.name.lower() == filename_lower]


def copy_file_preserving_relative_path(src_file: Path, src_root: Path, dest_root: Path) -> Path:
    relative = src_file.relative_to(src_root)
    dest_file = dest_root / relative
    dest_file.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src_file, dest_file)
    return dest_file


def ensure_required_databases(source: Path, destination: Path, required_db_files: Iterable[str]) -> tuple[int, dict[str, list[str]]]:
    copied = 0
    status: dict[str, list[str]] = {}

    for db_name in required_db_files:
        src_matches = find_files_by_name(source, db_name)
        dst_matches = find_files_by_name(destination, db_name)

        if dst_matches:
            status[db_name] = [str(p) for p in dst_matches]
            continue

        if not src_matches:
            status[db_name] = []
            continue

        copied_paths = []
        for src_file in src_matches:
            copied_file = copy_file_preserving_relative_path(
                src_file, source, destination)
            copied_paths.append(str(copied_file))
            copied += 1

        status[db_name] = copied_paths

    return copied, status


def create_workspace_file(destination: Path) -> None:
    workspace_data = {"folders": [{"path": "."}], "settings": {}}
    ws_file = destination / "google_agentic.code-workspace"
    ws_file.write_text(json.dumps(workspace_data, indent=2), encoding="utf-8")


def migrate(source: Path, destination: Path, overwrite: bool = False) -> MigrationStats:
    stats = MigrationStats()

    if not source.exists() or not source.is_dir():
        raise FileNotFoundError(f"Invalid source path: {source}")

    if destination.exists() and not overwrite:
        raise FileExistsError(
            f"Destination already exists: {destination}\n"
            "Use --overwrite to merge/overwrite into existing destination."
        )

    shutil.copytree(source, destination, dirs_exist_ok=overwrite)
    stats.copied = True

    stats.renamed_paths = rename_paths(destination)
    stats.rewritten_files = rewrite_text_files(destination)

    copied_db_count, db_status = ensure_required_databases(
        source, destination, REQUIRED_DB_FILES)
    stats.copied_required_db = copied_db_count

    create_workspace_file(destination)

    print("\n=== Migration Summary ===")
    print(f"Source: {source}")
    print(f"Destination: {destination}")
    print(f"Renamed paths: {stats.renamed_paths}")
    print(f"Rewritten text files: {stats.rewritten_files}")
    print(f"Required DB files copied explicitly: {stats.copied_required_db}")

    print("\nRequired DB status:")
    for db_name in REQUIRED_DB_FILES:
        matches = db_status.get(db_name, [])
        if matches:
            print(f"  [OK] {db_name}")
            for m in matches:
                print(f"       - {m}")
        else:
            print(f"  [MISSING IN SOURCE] {db_name}")

    print(
        f"\nWorkspace file created: {destination / 'google_agentic.code-workspace'}")

    return stats


def parse_args() -> argparse.Namespace:
    default_source = Path(__file__).resolve().parents[2]  # workspace root
    parser = argparse.ArgumentParser(
        description="Create a new Google_Agentic workspace by cloning current project and sanitizing project-name references."
    )
    parser.add_argument(
        "--source",
        default=str(default_source),
        help="Source workspace path (default: current workspace root).",
    )
    parser.add_argument(
        "--dest",
        default=r"C:\Users\sayan\Google_Agentic",
        help=r"Destination path (default: C:\Users\sayan\Google_Agentic).",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Allow overwrite/merge if destination already exists.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    source = Path(args.source).resolve()
    destination = Path(args.dest).resolve()

    migrate(source=source, destination=destination, overwrite=args.overwrite)


if __name__ == "__main__":
    main()
