#!/usr/bin/env python3
"""Export selected paths from a JSON OpenAPI document.

Edit EXPORTED_PATHS below to control which OpenAPI paths are included.
Only Python's standard library is required.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


# Paths are exported in this order. Replace these examples with the paths you need.
EXPORTED_PATHS: list[str] = [
    "/auth/getToken",
    "/auth/getMyPower",
    "/workflow/seedanceAiVideo",
    "/workflow/liveAiVideo",
    "/workflow/getResult",
    "/workflow/aiVideo",
    "/workflow/seedanceDiscount",
    "/workflow/seedanceDiscountChannel1"
]


def load_openapi(source: Path) -> dict[str, Any]:
    try:
        with source.open("r", encoding="utf-8") as file:
            document = json.load(file)
    except FileNotFoundError as error:
        raise ValueError(f"Source file does not exist: {source}") from error
    except json.JSONDecodeError as error:
        raise ValueError(
            f"Source file is not valid JSON: line {error.lineno}, "
            f"column {error.colno}: {error.msg}"
        ) from error

    if not isinstance(document, dict):
        raise ValueError("The OpenAPI document root must be a JSON object.")
    if not isinstance(document.get("paths"), dict):
        raise ValueError("The OpenAPI document must contain a 'paths' object.")
    return document


def export_paths(
    document: dict[str, Any], selected_paths: list[str]
) -> dict[str, Any]:
    if not selected_paths:
        raise ValueError("EXPORTED_PATHS is empty; add at least one path to export.")

    duplicates = sorted(
        path for path in set(selected_paths) if selected_paths.count(path) > 1
    )
    if duplicates:
        raise ValueError(f"Duplicate paths in EXPORTED_PATHS: {', '.join(duplicates)}")

    source_paths: dict[str, Any] = document["paths"]
    missing_paths = [path for path in selected_paths if path not in source_paths]
    if missing_paths:
        available = "\n  ".join(sorted(source_paths))
        missing = ", ".join(missing_paths)
        raise ValueError(
            f"Unknown path(s) in EXPORTED_PATHS: {missing}\n"
            f"Available paths:\n  {available}"
        )

    # A shallow copy is sufficient because the source document is not modified.
    exported = dict(document)
    exported["paths"] = {path: source_paths[path] for path in selected_paths}
    return exported


def write_json(document: dict[str, Any], destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    try:
        with temporary.open("w", encoding="utf-8", newline="\n") as file:
            json.dump(document, file, ensure_ascii=False, indent=2)
            file.write("\n")
        temporary.replace(destination)
    finally:
        temporary.unlink(missing_ok=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export the paths listed in EXPORTED_PATHS to a new OpenAPI file."
    )
    parser.add_argument("source", type=Path, help="Source OpenAPI JSON file")
    parser.add_argument("output", type=Path, help="Destination OpenAPI JSON file")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        source_document = load_openapi(args.source)
        exported_document = export_paths(source_document, EXPORTED_PATHS)
        write_json(exported_document, args.output)
    except (OSError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1

    print(f"Exported {len(EXPORTED_PATHS)} path(s) to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
