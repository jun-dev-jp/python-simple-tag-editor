"""python-simple-tag-editor: Simple and unified audio tag editor for MP3, MP4, and AIFF files."""

from __future__ import annotations

import logging
from os import R_OK, PathLike, access
from pathlib import Path

from mutagen import File as MutagenFile
from mutagen import FileType as MutagenFileType
from mutagen import MutagenError
from mutagen.aiff import AIFF
from mutagen.id3 import ID3Tags
from mutagen.mp3 import MP3
from mutagen.mp4 import MP4, MP4Tags

from .audio_tag import (
    SimpleAudioTag,
    b64decode,
    b64encode,
    parse_base64_encoded_data_uri,
)
from .audio_tag_editor import (
    SimpleAudioTagEditor,
    validate_track_or_disk_number,
    validate_year,
)
from .exceptions import (
    FileReadError,
    FileWriteError,
    InvalidTagValueError,
    SimpleTagEditorError,
    TagReadError,
    TagWriteError,
    UnsupportedAudioFormatError,
)
from .id3tag import SimpleID3Tag
from .id3tag_editor import SimpleID3TagEditor
from .mp4tag import SimpleMP4Tag
from .mp4tag_editor import SimpleMP4TagEditor

logger = logging.getLogger(__name__)

__all__ = [
    "FileReadError",
    "FileWriteError",
    "InvalidTagValueError",
    "SimpleAudioTag",
    "SimpleAudioTagEditor",
    "SimpleID3Tag",
    "SimpleID3TagEditor",
    "SimpleMP4Tag",
    "SimpleMP4TagEditor",
    "SimpleTagEditorError",
    "TagReadError",
    "TagWriteError",
    "UnsupportedAudioFormatError",
    "b64decode",
    "b64encode",
    "get_tag_editor",
    "parse_base64_encoded_data_uri",
    "read_tags",
    "validate_track_or_disk_number",
    "validate_year",
]


def _validate_and_open_audio(file_path: str | PathLike[str]) -> MutagenFileType:
    """Validate file path and open it using mutagen."""
    path = Path(file_path)

    if not path.exists():
        logger.error(f"Path does not exist: {path}")
        raise FileReadError(f"Path does not exist: {path}")
    if not path.is_file():
        logger.error(f"Path is not a file, it is a directory: {path}")
        raise FileReadError(f"Path is not a file, it is a directory: {path}")
    if not access(path, R_OK):
        logger.error(f"File is not readable: {path}")
        raise FileReadError(f"File is not readable: {path}")

    try:
        audio = MutagenFile(path)
    except MutagenError as e:
        logger.error(f"Failed to parse audio file with mutagen: {e}")
        raise UnsupportedAudioFormatError(f"Failed to parse audio file: {e}") from e

    if audio is None:
        raise UnsupportedAudioFormatError(
            "Unsupported or unrecognized audio file format."
        )

    return audio


def read_tags(file_path: str | PathLike[str]) -> SimpleAudioTag:
    """Detect file format and extract metadata tags using the appropriate parser.

    Args:
        file_path: Path to the audio file (MP3, MP4/M4A, AIFF).

    Returns:
        SimpleAudioTag: Extracted audio metadata tags.

    Raises:
        FileReadError: If the file does not exist, is a directory, or is not readable.
        UnsupportedAudioFormatError: If the audio format is not supported.
        TagReadError: If an error occurs while reading the tags.
    """
    audio = _validate_and_open_audio(file_path)

    if isinstance(audio, (MP3, AIFF)):
        if audio.tags is None:
            return SimpleID3Tag()
        if isinstance(audio.tags, ID3Tags):
            return SimpleID3Tag.from_ID3Tags(audio.tags)
        raise UnsupportedAudioFormatError(f"Format not supported: {type(audio)}")

    if isinstance(audio, MP4):
        if audio.tags is None:
            return SimpleMP4Tag()
        if isinstance(audio.tags, MP4Tags):
            return SimpleMP4Tag.from_MP4Tags(audio.tags)
        raise UnsupportedAudioFormatError(f"Format not supported: {type(audio)}")

    raise UnsupportedAudioFormatError(f"Format not supported: {type(audio)}")


def get_tag_editor(file_path: str | PathLike[str]) -> SimpleAudioTagEditor:
    """Detect file format and return an appropriate tag editor instance.

    Args:
        file_path: Path to the audio file (MP3, MP4/M4A, AIFF).

    Returns:
        SimpleAudioTagEditor: Unified tag editor interface.

    Raises:
        FileReadError: If the file does not exist, is a directory, or is not readable.
        UnsupportedAudioFormatError: If the audio format is not supported.
    """
    audio = _validate_and_open_audio(file_path)

    if isinstance(audio, (MP3, AIFF)):
        if audio.tags is None:
            audio.add_tags()
        if isinstance(audio.tags, ID3Tags):
            return SimpleID3TagEditor(audio, audio.tags)
        raise UnsupportedAudioFormatError(f"Format not supported: {type(audio)}")

    if isinstance(audio, MP4):
        mp4tags = audio.tags if isinstance(audio.tags, MP4Tags) else MP4Tags()
        return SimpleMP4TagEditor(audio, mp4tags)

    raise UnsupportedAudioFormatError(f"Format not supported: {type(audio)}")
