"""Abstract base class for audio tag editors."""

from __future__ import annotations

import logging
import shutil
from abc import ABC, abstractmethod
from os import PathLike
from pathlib import Path

from mutagen import MutagenError
from mutagen.aiff import AIFF
from mutagen.id3 import ID3Tags
from mutagen.id3 import error as ID3Error
from mutagen.mp3 import MP3
from mutagen.mp4 import MP4, MP4Tags
from mutagen.mp4 import error as MP4Error

from .exceptions import FileWriteError, TagWriteError

logger = logging.getLogger(__name__)

__all__ = ["SimpleAudioTagEditor"]


class SimpleAudioTagEditor(ABC):
    """Unified abstract interface for editing metadata tags across various audio formats."""

    def __init__(self, audio: MP3 | AIFF | MP4, tags: ID3Tags | MP4Tags) -> None:
        self._audio: MP3 | AIFF | MP4 = audio
        self._tags: ID3Tags | MP4Tags = tags

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

        try:
            if source_path and Path(source_path).resolve() != path.resolve():
                shutil.copyfile(source_path, path)
            elif not path.exists():
                path.touch()

            self._audio.save(path)
        except (ID3Error, MP4Error, MutagenError) as e:
            logger.error(f"Failed to write tags to {path}: {e}")
            raise TagWriteError(f"Failed to write tags: {e}") from e
        except OSError as e:
            logger.error(f"File write error for {path}: {e}")
            raise FileWriteError(f"File write error: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error while writing tags to {path}: {e}")
            raise TagWriteError(f"Unexpected error: {e}") from e

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
        """Edit the year tag."""

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
        """Edit the disk number tag."""

    @abstractmethod
    def clear_disk_number(self) -> None:
        """Clear the disk number tag."""

    @abstractmethod
    def edit_track_number(self, new_track_number: str) -> None:
        """Edit the track number tag."""

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
        """Edit the album art tag."""

    @abstractmethod
    def clear_album_art(self) -> None:
        """Clear the album art tag."""

    @abstractmethod
    def clear_all_tags(self) -> None:
        """Clear all audio tags from the loaded audio."""
