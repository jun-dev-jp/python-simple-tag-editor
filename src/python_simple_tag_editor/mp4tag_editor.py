"""MP4/M4A tag editor implementation."""

from __future__ import annotations

import logging
from typing import Final, cast, override

from mutagen.mp4 import MP4, MP4Cover, MP4Tags
from mutagen.mp4 import error as MP4Error

from .audio_tag import validate_album_art
from .audio_tag_editor import (
    SimpleAudioTagEditor,
    validate_track_or_disk_number,
    validate_year,
)
from .exceptions import TagWriteError

logger = logging.getLogger(__name__)

__all__ = ["SimpleMP4TagEditor"]


class SimpleMP4TagEditor(SimpleAudioTagEditor):
    """Tag editor for MP4/M4A audio files."""

    def __init__(self, audio: MP4, tags: MP4Tags) -> None:
        super().__init__(audio, tags)

    @property
    def _mp4_tags(self) -> MP4Tags:
        """Cast base _tags to MP4Tags for MP4 operations."""
        return cast(MP4Tags, self._tags)

    def _set_tag(self, key: str, tag_value: list[object], tag_name: str) -> None:
        """Helper to set an MP4 tag with error handling."""
        try:
            self._mp4_tags[key] = tag_value  # pyright: ignore[reportArgumentType]
        except MP4Error as e:
            logger.error(f"Failed to edit {tag_name} tag: {e}")
            raise TagWriteError(f"Failed to edit {tag_name} tag: {e}") from e

    def _clear_tag(self, key: str, tag_name: str) -> None:
        """Helper to clear an MP4 tag with error handling."""
        try:
            self._mp4_tags.pop(key, None)
        except MP4Error as e:
            logger.error(f"Failed to clear {tag_name} tag: {e}")
            raise TagWriteError(f"Failed to clear {tag_name} tag: {e}") from e

    @override
    def edit_title(self, new_title: str) -> None:
        """Edit the title tag (©nam).

        Args:
            new_title: The new title to set.

        Raises:
            TagWriteError: If the title tag cannot be edited.
        """
        self._set_tag("©nam", [new_title], "title")

    @override
    def clear_title(self) -> None:
        """Clear the title tag (©nam).

        Raises:
            TagWriteError: If the title tag cannot be cleared.
        """
        self._clear_tag("©nam", "title")

    @override
    def edit_artist(self, new_artist: str) -> None:
        """Edit the artist tag (©ART).

        Args:
            new_artist: The new artist to set.

        Raises:
            TagWriteError: If the artist tag cannot be edited.
        """
        self._set_tag("©ART", [new_artist], "artist")

    @override
    def clear_artist(self) -> None:
        """Clear the artist tag (©ART).

        Raises:
            TagWriteError: If the artist tag cannot be cleared.
        """
        self._clear_tag("©ART", "artist")

    @override
    def edit_album(self, new_album: str) -> None:
        """Edit the album tag (©alb).

        Args:
            new_album: The new album to set.

        Raises:
            TagWriteError: If the album tag cannot be edited.
        """
        self._set_tag("©alb", [new_album], "album")

    @override
    def clear_album(self) -> None:
        """Clear the album tag (©alb).

        Raises:
            TagWriteError: If the album tag cannot be cleared.
        """
        self._clear_tag("©alb", "album")

    @override
    def edit_year(self, new_year: str) -> None:
        """Edit the year tag (©day).

        Args:
            new_year: The new year to set (e.g., '2026', '2026-10', '2026-10-04').

        Raises:
            InvalidTagValueError: If the year format is invalid.
            TagWriteError: If the year tag cannot be edited.
        """
        validated_year = validate_year(new_year)
        self._set_tag("©day", [validated_year], "year")

    @override
    def clear_year(self) -> None:
        """Clear the year tag (©day).

        Raises:
            TagWriteError: If the year tag cannot be cleared.
        """
        self._clear_tag("©day", "year")

    @override
    def edit_genre(self, new_genre: str) -> None:
        """Edit the genre tag (©gen).

        Args:
            new_genre: The new genre to set.

        Raises:
            TagWriteError: If the genre tag cannot be edited.
        """
        self._set_tag("©gen", [new_genre], "genre")

    @override
    def clear_genre(self) -> None:
        """Clear the genre tag (©gen).

        Raises:
            TagWriteError: If the genre tag cannot be cleared.
        """
        self._clear_tag("©gen", "genre")

    @override
    def edit_disk_number(self, new_disk_number: str) -> None:
        """Edit the disk number tag (disk).

        Args:
            new_disk_number: The new disk number to set (e.g., '1' or '1/2').

        Raises:
            InvalidTagValueError: If the disk number format is invalid.
            TagWriteError: If the disk number tag cannot be edited.
        """
        num, total = validate_track_or_disk_number(new_disk_number, "disk")
        self._set_tag("disk", [(num, total)], "disk number")

    @override
    def clear_disk_number(self) -> None:
        """Clear the disk number tag (disk).

        Raises:
            TagWriteError: If the disk number tag cannot be cleared.
        """
        self._clear_tag("disk", "disk number")

    @override
    def edit_track_number(self, new_track_number: str) -> None:
        """Edit the track number tag (trkn).

        Args:
            new_track_number: The new track number to set (e.g., '1' or '1/10').

        Raises:
            InvalidTagValueError: If the track number format is invalid.
            TagWriteError: If the track number tag cannot be edited.
        """
        num, total = validate_track_or_disk_number(new_track_number, "track")
        self._set_tag("trkn", [(num, total)], "track number")

    @override
    def clear_track_number(self) -> None:
        """Clear the track number tag (trkn).

        Raises:
            TagWriteError: If the track number tag cannot be cleared.
        """
        self._clear_tag("trkn", "track number")

    @override
    def edit_lyrics(
        self, new_lyrics: str, lang: str = "eng", desc: str = "Lyrics"
    ) -> None:
        """Edit the lyrics tag (©lyr).

        Args:
            new_lyrics: The new lyrics text to set.
            lang: Language code (kept for interface consistency).
            desc: Description (kept for interface consistency).

        Raises:
            TagWriteError: If the lyrics tag cannot be edited.
        """
        _ = lang, desc
        self._set_tag("©lyr", [new_lyrics], "lyrics")

    @override
    def clear_lyrics(self) -> None:
        """Clear the lyrics tag (©lyr).

        Raises:
            TagWriteError: If the lyrics tag cannot be cleared.
        """
        self._clear_tag("©lyr", "lyrics")

    @override
    def edit_album_art(
        self, new_album_art: str, desc: str = "Front Cover", type: int = 3
    ) -> None:
        """Edit the album art tag (covr).

        Args:
            new_album_art: The album art as a base64-encoded data URI.
            desc: Description (kept for interface consistency).
            type: Picture type (kept for interface consistency).

        Raises:
            InvalidTagValueError: If the album art Data URI or image data is invalid.
            TagWriteError: If the album art tag cannot be edited.
        """
        _ = desc, type
        mime, album_art_bytes = validate_album_art(new_album_art)

        imageformat: Final = (
            MP4Cover.FORMAT_PNG if mime == "image/png" else MP4Cover.FORMAT_JPEG
        )

        try:
            cover = MP4Cover(album_art_bytes, imageformat=imageformat)
            self._mp4_tags["covr"] = [cover]
        except MP4Error as e:
            logger.error(f"Failed to edit album art tag: {e}")
            raise TagWriteError(f"Failed to edit album art tag: {e}") from e

    @override
    def clear_album_art(self) -> None:
        """Clear the album art tag (covr).

        Raises:
            TagWriteError: If the album art tag cannot be cleared.
        """
        self._clear_tag("covr", "album art")

    @override
    def clear_all_tags(self) -> None:
        """Clear all tags from the audio file.

        Raises:
            TagWriteError: If the tags cannot be cleared.
        """
        try:
            self._tags.clear()
        except MP4Error as e:
            logger.error(f"Failed to clear all tags: {e}")
            raise TagWriteError(f"Failed to clear all tags: {e}") from e
