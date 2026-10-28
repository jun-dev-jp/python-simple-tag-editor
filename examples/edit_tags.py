#!/usr/bin/env python3
"""Example script demonstrating how to edit audio tags using python-simple-tag-editor."""

from __future__ import annotations

import argparse
import sys
from io import TextIOWrapper
from pathlib import Path
from typing import cast

# Ensure src is in sys.path when running from examples/ directory or project root
script_dir = Path(__file__).resolve().parent
src_dir = script_dir.parent / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from python_simple_tag_editor import (
    JPEG_MAGIC,
    PNG_MAGIC,
    b64encode,
    get_tag_editor,
    read_tags,
)
from python_simple_tag_editor.exceptions import (
    FileReadError,
    InvalidTagValueError,
    SimpleTagEditorError,
)


def _read_album_art_as_data_uri(image_path: Path) -> str:
    """Read a JPEG or PNG image and encode it as an album art data URI.

    Args:
        image_path: Path to the album art image.

    Returns:
        The image encoded as a base64 data URI.

    Raises:
        FileReadError: If the image path cannot be read.
        InvalidTagValueError: If the image is not a JPEG or PNG.
    """
    if not image_path.exists():
        raise FileReadError(f"Album art file does not exist: {image_path}")
    if not image_path.is_file():
        raise FileReadError(f"Album art path is not a file: {image_path}")

    try:
        image_data = image_path.read_bytes()
    except OSError as e:
        raise FileReadError(f"Failed to read album art file {image_path}: {e}") from e

    if image_data.startswith(JPEG_MAGIC):
        mime_type = "image/jpeg"
    elif image_data.startswith(PNG_MAGIC):
        mime_type = "image/png"
    else:
        raise InvalidTagValueError(
            f"Album art must be a JPEG or PNG image: {image_path}"
        )

    return b64encode(mime_type, image_data)


def main() -> int:
    """Main entry point for the edit_tags example script."""
    if isinstance(sys.stdout, TextIOWrapper):
        # Redirected Windows output may use an encoding that cannot display tags.
        sys.stdout.reconfigure(errors="backslashreplace")

    parser = argparse.ArgumentParser(
        description="Edit metadata tags in an audio file using python-simple-tag-editor."
    )
    _ = parser.add_argument("input_path", help="Source audio file path.", type=Path)
    _ = parser.add_argument(
        "--output",
        "-o",
        help="Destination audio file path (defaults to the input file).",
        type=Path,
        default=None,
    )
    _ = parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Allow overwriting the destination file (disabled by default).",
    )
    _ = parser.add_argument("--title", help="New title tag value.", type=str)
    _ = parser.add_argument("--artist", help="New artist tag value.", type=str)
    _ = parser.add_argument("--album", help="New album tag value.", type=str)
    _ = parser.add_argument("--year", help="New year tag value (e.g. 2026).", type=str)
    _ = parser.add_argument("--genre", help="New genre tag value.", type=str)
    _ = parser.add_argument(
        "--track", help="New track number (e.g. 1 or 1/10).", type=str
    )
    _ = parser.add_argument("--disk", help="New disk number (e.g. 1 or 1/2).", type=str)
    _ = parser.add_argument("--lyrics", help="New lyrics text.", type=str)
    _ = parser.add_argument(
        "--album-art",
        help="Path to a JPEG or PNG image to use as album art.",
        type=Path,
    )

    args = parser.parse_args()
    input_path = cast(Path, args.input_path)
    output_path = cast(Path, args.output) if args.output is not None else input_path

    try:
        editor = get_tag_editor(input_path)
        if args.title is not None:
            editor.edit_title(cast(str, args.title))
        if args.artist is not None:
            editor.edit_artist(cast(str, args.artist))
        if args.album is not None:
            editor.edit_album(cast(str, args.album))
        if args.year is not None:
            editor.edit_year(cast(str, args.year))
        if args.genre is not None:
            editor.edit_genre(cast(str, args.genre))
        if args.track is not None:
            editor.edit_track_number(cast(str, args.track))
        if args.disk is not None:
            editor.edit_disk_number(cast(str, args.disk))
        if args.lyrics is not None:
            editor.edit_lyrics(cast(str, args.lyrics))
        if args.album_art is not None:
            editor.edit_album_art(
                _read_album_art_as_data_uri(cast(Path, args.album_art))
            )

        editor.save_to_file(output_path, overwrite=cast(bool, args.overwrite))
        print(f"Successfully saved updated tags to {output_path}")

        updated_tags = read_tags(output_path)
        print(f"  Title : {updated_tags.title}")
        print(f"  Artist: {updated_tags.artist}")
        print(f"  Album : {updated_tags.album}")
        print(f"  Year  : {updated_tags.year}")
        print(f"  Genre : {updated_tags.genre}")
        print(f"  Track : {updated_tags.track_number}")
        print(f"  Disk  : {updated_tags.disk_number}")
        print(f"  Lyrics: {updated_tags.lyrics}")
    except SimpleTagEditorError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
