#!/usr/bin/env python3
"""Example script to read and display audio tags using python-simple-tag-editor."""

from __future__ import annotations

import argparse
import sys
import textwrap
from pathlib import Path

# Ensure src is in sys.path when running from examples/ directory or project root
script_dir = Path(__file__).resolve().parent
src_dir = script_dir.parent / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from python_simple_tag_editor import read_tags
from python_simple_tag_editor.exceptions import SimpleTagEditorError


def display_tags(file_path: str | Path) -> None:
    """Read and display tag information for a given audio file.

    Args:
        file_path: Path to the audio file.
    """
    path = Path(file_path)
    print(f"=== File: {path} ===")
    try:
        tags = read_tags(path)
        print(f"  Title        : {tags.title}")
        print(f"  Artist       : {tags.artist}")
        print(f"  Album        : {tags.album}")
        print(f"  Year         : {tags.year}")
        print(f"  Genre        : {tags.genre}")
        print(f"  Track Number : {tags.track_number}")
        print(f"  Disk Number  : {tags.disk_number}")

        if tags.lyrics:
            indented_lyrics = textwrap.indent(tags.lyrics, "    ")
            print(f"  Lyrics       :\n{indented_lyrics}")
        else:
            print("  Lyrics       : None")

        if tags.album_art:
            decoded = tags.b64decode_album_art()
            if decoded:
                mime, data = decoded
                print(f"  Album Art    : Present ({mime}, {len(data)} bytes)")
            else:
                print("  Album Art    : Present (failed to decode)")
        else:
            print("  Album Art    : None")

    except SimpleTagEditorError as e:
        print(f"Error reading tags from {path}: {e}", file=sys.stderr)
    except Exception as e:  # noqa: BLE001
        print(f"Unexpected error with {path}: {e}", file=sys.stderr)


def main() -> int:
    """Main entry point for the read_tags example script."""
    parser = argparse.ArgumentParser(
        description="Read and display metadata tags from audio files using python-simple-tag-editor."
    )
    _ = parser.add_argument(
        "path", help="Path to audio file(s) to read tags from.", type=Path
    )

    args = parser.parse_args()

    display_tags(args.path)

    return 0


if __name__ == "__main__":
    sys.exit(main())
