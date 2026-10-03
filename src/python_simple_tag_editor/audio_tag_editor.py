"""Abstract base class for audio tag editors."""

from __future__ import annotations

import logging
import os
import re
import shutil
import tempfile
from abc import ABC, abstractmethod
from datetime import date, datetime
from os import PathLike
from pathlib import Path

from mutagen import MutagenError
from mutagen.aiff import AIFF
from mutagen.flac import FLAC, VCFLACDict
from mutagen.flac import error as FLACError
from mutagen.id3 import ID3Tags
from mutagen.id3 import error as ID3Error
from mutagen.mp3 import MP3
from mutagen.mp4 import MP4, MP4Tags
from mutagen.mp4 import error as MP4Error
from mutagen.oggopus import OggOpus, OggOpusVComment
from mutagen.oggopus import error as OggOpusError
from mutagen.wave import WAVE
from mutagen.wave import error as WaveError

from .exceptions import FileWriteError, InvalidTagValueError, TagWriteError

logger = logging.getLogger(__name__)

type SupportedAudio = MP3 | AIFF | WAVE | MP4 | FLAC | OggOpus
type SupportedTags = ID3Tags | MP4Tags | VCFLACDict | OggOpusVComment

__all__ = [
    "SimpleAudioTagEditor",
    "SupportedAudio",
    "SupportedTags",
    "validate_track_or_disk_number",
    "validate_year",
]


def validate_year(year: str) -> str:
    """Validate a year or date string.

    Accepted formats:
        - 'YYYY' (4-digit year, e.g., '2026')
        - 'YYYY-MM' (year and 2-digit month, e.g., '2026-10')
        - 'YYYY-MM-DD' (ISO 8601 calendar date, e.g., '2026-10-04')
        - ISO 8601 date-time (e.g., '2026-10-04T12:00:00Z')

    Args:
        year: The year or date string to validate.

    Returns:
        The validated year/date string.

    Raises:
        InvalidTagValueError: If year is not a valid year or date format.
    """
    if re.fullmatch(r"\d{4}", year):
        return year
    if re.fullmatch(r"\d{4}-(?:0[1-9]|1[0-2])", year):
        return year
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", year):
        try:
            date.fromisoformat(year)
            return year
        except ValueError as e:
            raise InvalidTagValueError(
                f"Invalid date: '{year}'. Calendar date is not valid."
            ) from e
    if "T" in year:
        try:
            datetime.fromisoformat(year)
            return year
        except ValueError as e:
            raise InvalidTagValueError(
                f"Invalid date-time: '{year}'. ISO 8601 date-time is not valid."
            ) from e
    raise InvalidTagValueError(
        f"Invalid year/date format: '{year}'. "
        "Expected 'YYYY', 'YYYY-MM', 'YYYY-MM-DD', or ISO 8601 format."
    )


def validate_track_or_disk_number(
    value: str, field_name: str = "track"
) -> tuple[int, int]:
    """Validate a track or disk number string.

    Accepted formats:
        - 'number' (e.g., '1', '50')
        - 'number/total' (e.g., '1/12', '55/60')

    Both number and total (if provided) must be positive integers between 1 and 65535
    without leading zeros.

    Args:
        value: The track or disk number string to validate.
        field_name: The name of the field for error messages ('track' or 'disk').

    Returns:
        tuple[int, int]: (number, total) where total is 0 if not specified.

    Raises:
        InvalidTagValueError: If value is not a valid track or disk number format.
    """
    match = re.fullmatch(r"([1-9]\d*)(?:/([1-9]\d*))?", value)
    if not match:
        raise InvalidTagValueError(
            f"Invalid {field_name} number format: '{value}'. "
            f"Expected a positive integer or 'number/total' (e.g., '1' or '1/10')."
        )

    num = int(match.group(1))
    total = int(match.group(2)) if match.group(2) else 0

    if num > 65535 or total > 65535:
        raise InvalidTagValueError(
            f"Invalid {field_name} number: values must not exceed 65535 (got '{value}')."
        )

    return num, total


class SimpleAudioTagEditor(ABC):
    """Unified abstract interface for editing metadata tags across various audio formats."""

    def __init__(self, audio: SupportedAudio, tags: SupportedTags) -> None:
        self._audio: SupportedAudio = audio
        self._tags: SupportedTags = tags

    def save_to_file(
        self, output_path: str | PathLike[str], overwrite: bool = True
    ) -> None:
        """Save the modified audio file and its metadata to the specified path.

        Args:
            output_path: Path where the audio file should be saved.
            overwrite: Whether to overwrite if the output file already exists (default: True).

        Raises:
            FileWriteError: If the output path is a directory, or if the file exists and overwrite is False,
                or if file creation/copy fails.
            TagWriteError: If saving tags to the audio file fails.
        """
        path = Path(output_path)
        source_path = getattr(self._audio, "filename", None)

        if path.exists():
            if not path.is_file():
                logger.error(f"Output path is not a file: {path}")
                raise FileWriteError(f"Output path is not a file: {path}")
            if not overwrite:
                logger.error(
                    f"Output file already exists and overwrite is False: {path}"
                )
                raise FileWriteError(f"Output file already exists: {path}")
            logger.debug(f"Overwriting existing output file: {path}")

        tmp_path: Path | None = None
        try:
            dest_dir = path.parent
            with tempfile.NamedTemporaryFile(
                dir=dest_dir,
                prefix=f".{path.name}.",
                suffix=".tmp",
                delete=False,
            ) as tmp_file:
                tmp_path = Path(tmp_file.name)

            if source_path:
                shutil.copyfile(source_path, tmp_path)
                try:
                    if path.exists():
                        shutil.copymode(path, tmp_path)
                    else:
                        shutil.copymode(source_path, tmp_path)
                except OSError:
                    pass
            elif path.exists():
                shutil.copyfile(path, tmp_path)
                try:
                    shutil.copymode(path, tmp_path)
                except OSError:
                    pass

            self._audio.save(tmp_path)
            os.replace(tmp_path, path)
            tmp_path = None
        except (
            ID3Error,
            MP4Error,
            FLACError,
            OggOpusError,
            WaveError,
            MutagenError,
        ) as e:
            logger.error(f"Failed to write tags to {path}: {e}")
            raise TagWriteError(f"Failed to write tags: {e}") from e
        except OSError as e:
            logger.error(f"File write error for {path}: {e}")
            raise FileWriteError(f"File write error: {e}") from e
        finally:
            if tmp_path is not None and tmp_path.exists():
                try:
                    tmp_path.unlink()
                except OSError:
                    pass

    @abstractmethod
    def edit_title(self, new_title: str) -> None:
        """Edit the title tag."""

    @abstractmethod
    def clear_title(self) -> None:
        """Clear the title tag."""

    @abstractmethod
    def edit_artist(self, new_artist: str) -> None:
        """Edit the artist tag."""

    @abstractmethod
    def clear_artist(self) -> None:
        """Clear the artist tag."""

    @abstractmethod
    def edit_album(self, new_album: str) -> None:
        """Edit the album tag."""

    @abstractmethod
    def clear_album(self) -> None:
        """Clear the album tag."""

    @abstractmethod
    def edit_year(self, new_year: str) -> None:
        """Edit the year tag.

        Args:
            new_year: The new year to set (e.g., '2026', '2026-10', '2026-10-04').

        Raises:
            InvalidTagValueError: If the year format is invalid.
            TagWriteError: If the year tag cannot be edited.
        """

    @abstractmethod
    def clear_year(self) -> None:
        """Clear the year tag."""

    @abstractmethod
    def edit_genre(self, new_genre: str) -> None:
        """Edit the genre tag."""

    @abstractmethod
    def clear_genre(self) -> None:
        """Clear the genre tag."""

    @abstractmethod
    def edit_disk_number(self, new_disk_number: str) -> None:
        """Edit the disk number tag.

        Args:
            new_disk_number: The new disk number to set (e.g., '1' or '1/2').

        Raises:
            InvalidTagValueError: If the disk number format is invalid.
            TagWriteError: If the disk number tag cannot be edited.
        """

    @abstractmethod
    def clear_disk_number(self) -> None:
        """Clear the disk number tag."""

    @abstractmethod
    def edit_track_number(self, new_track_number: str) -> None:
        """Edit the track number tag.

        Args:
            new_track_number: The new track number to set (e.g., '1' or '1/10').

        Raises:
            InvalidTagValueError: If the track number format is invalid.
            TagWriteError: If the track number tag cannot be edited.
        """

    @abstractmethod
    def clear_track_number(self) -> None:
        """Clear the track number tag."""

    @abstractmethod
    def edit_lyrics(
        self, new_lyrics: str, lang: str = "eng", desc: str = "Lyrics"
    ) -> None:
        """Edit the lyrics tag."""

    @abstractmethod
    def clear_lyrics(self) -> None:
        """Clear the lyrics tag."""

    @abstractmethod
    def edit_album_art(
        self, new_album_art: str, desc: str = "Front Cover", type: int = 3
    ) -> None:
        """Edit the album art tag.

        Args:
            new_album_art: The album art as a base64-encoded Data URI.
            desc: Description of the album art (default: 'Front Cover').
            type: Picture type as defined in ID3v2 (default: 3 = Cover (front)).

        Raises:
            InvalidTagValueError: If the Data URI format is invalid, base64 payload is corrupt,
                MIME type is unsupported, or image data does not match the MIME type.
            TagWriteError: If the album art tag cannot be edited.
        """

    @abstractmethod
    def clear_album_art(self) -> None:
        """Clear the album art tag."""

    @abstractmethod
    def clear_all_tags(self) -> None:
        """Clear all audio tags from the loaded audio."""
