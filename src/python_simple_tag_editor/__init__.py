from __future__ import annotations

import logging
from os import R_OK, PathLike, access
from pathlib import Path

from mutagen import File as MutagenFile
from mutagen.aiff import AIFF
from mutagen.id3 import ID3
from mutagen.mp3 import MP3
from mutagen.mp4 import MP4, MP4Tags

logger = logging.getLogger(__name__)

from .audio_tag import SimpleAudioTag
from .exceptions import (
    UnsupportedAudioFormatError,
)
from .id3 import SimpleID3Tag
from .mp4 import SimpleMP4Tag

__all__ = [
    "SimpleAudioTag",
    "SimpleID3Tag",
    "SimpleMP4Tag",
    "UnsupportedAudioFormatError",
]


def read_tags(file_path: str | PathLike[str]) -> SimpleID3Tag | SimpleMP4Tag:
    """Detect file format using mutagen and extract tags using the appropriate parser.

    Args:
        file_path: Path to the audio file.

    Returns:
        SimpleAudioTag: Extracted audio metadata tags.

    Raises:
        FileNotFoundError: If the file does not exist.
        IsADirectoryError: If the path is a directory.
        PermissionError: If the file is not readable.
        UnsupportedAudioFormatError: If the audio format is not supported.
    """
    file_path = Path(file_path)

    if not file_path.exists():
        logger.error(f"Path does not exist: {file_path}")
        raise FileNotFoundError(f"Path does not exist: {file_path}")
    if not file_path.is_file():
        logger.error(f"Path is not a file, it is a directory: {file_path}")
        raise IsADirectoryError(f"Path is not a file, it is a directory: {file_path}")
    if not access(file_path, R_OK):
        logger.error(f"File is not readable: {file_path}")
        raise PermissionError(f"File is not readable: {file_path}")

    try:
        audio = MutagenFile(file_path)
    except Exception as e:
        logger.error(f"Failed to parse audio file with mutagen: {e}")
        raise UnsupportedAudioFormatError(f"Failed to parse audio file: {e}") from e
    if audio is None:
        raise UnsupportedAudioFormatError(
            "Unsupported or unrecognized audio file format."
        )

    if isinstance(audio, MP3 | AIFF):
        if isinstance(audio.tags, ID3):
            return SimpleID3Tag.from_ID3(audio.tags)
        elif audio.tags is None:
            return SimpleID3Tag()
        else:
            raise UnsupportedAudioFormatError(f"Format not supported: {type(audio)}")
    if isinstance(audio, MP4):
        if isinstance(audio.tags, MP4Tags):
            return SimpleMP4Tag.from_MP4Tags(audio.tags)
        elif audio.tags is None:
            return SimpleMP4Tag()
        else:
            raise UnsupportedAudioFormatError(f"Format not supported: {type(audio)}")

    raise UnsupportedAudioFormatError(f"Format not supported: {type(audio)}")
