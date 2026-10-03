"""ID3 tag editor implementation for MP3 and AIFF files."""

from __future__ import annotations

import logging
import re
from typing import cast, override

from mutagen.aiff import AIFF
from mutagen.id3 import (
    APIC,
    TALB,
    TCON,
    TDRC,
    TIT2,
    TPE1,
    TPOS,
    TRCK,
    TYER,
    USLT,
    Frame,
    ID3Tags,
)
from mutagen.id3 import error as ID3Error
from mutagen.mp3 import MP3

from .audio_tag import validate_album_art
from .audio_tag_editor import (
    SimpleAudioTagEditor,
    validate_track_or_disk_number,
    validate_year,
)
from .exceptions import TagWriteError

logger = logging.getLogger(__name__)

__all__ = ["SimpleID3TagEditor"]


class SimpleID3TagEditor(SimpleAudioTagEditor):
    """Tag editor for ID3-tagged audio files (MP3 and AIFF)."""

    def __init__(self, audio: MP3 | AIFF, tags: ID3Tags) -> None:
        super().__init__(audio, tags)

    @property
    def _id3_tags(self) -> ID3Tags:
        """Cast base _tags to ID3Tags for ID3/AIFF operations."""
        return cast(ID3Tags, self._tags)

    def _set_tag(self, key: str, tag_obj: Frame, tag_name: str) -> None:
        """Helper to set an ID3 tag with error handling."""
        try:
            self._id3_tags[key] = tag_obj
        except ID3Error as e:
            logger.error(f"Failed to edit {tag_name} tag: {e}")
            raise TagWriteError(f"Failed to edit {tag_name} tag: {e}") from e

    def _clear_tag(self, key: str, tag_name: str) -> None:
        """Helper to clear an ID3 tag with error handling."""
        try:
            self._id3_tags.pop(key, None)
        except ID3Error as e:
            logger.error(f"Failed to clear {tag_name} tag: {e}")
            raise TagWriteError(f"Failed to clear {tag_name} tag: {e}") from e

    @override
    def edit_title(self, new_title: str) -> None:
        """Edit the title tag (TIT2).

        Args:
            new_title: The new title to set.

        Raises:
            TagWriteError: If the title tag cannot be edited.
        """
        self._set_tag("TIT2", TIT2(encoding=3, text=new_title), "title")

    @override
    def clear_title(self) -> None:
        """Clear the title tag (TIT2).

        Raises:
            TagWriteError: If the title tag cannot be cleared.
        """
        self._clear_tag("TIT2", "title")

    @override
    def edit_artist(self, new_artist: str) -> None:
        """Edit the artist tag (TPE1).

        Args:
            new_artist: The new artist to set.

        Raises:
            TagWriteError: If the artist tag cannot be edited.
        """
        self._set_tag("TPE1", TPE1(encoding=3, text=new_artist), "artist")

    @override
    def clear_artist(self) -> None:
        """Clear the artist tag (TPE1).

        Raises:
            TagWriteError: If the artist tag cannot be cleared.
        """
        self._clear_tag("TPE1", "artist")

    @override
    def edit_album(self, new_album: str) -> None:
        """Edit the album tag (TALB).

        Args:
            new_album: The new album to set.

        Raises:
            TagWriteError: If the album tag cannot be edited.
        """
        self._set_tag("TALB", TALB(encoding=3, text=new_album), "album")

    @override
    def clear_album(self) -> None:
        """Clear the album tag (TALB).

        Raises:
            TagWriteError: If the album tag cannot be cleared.
        """
        self._clear_tag("TALB", "album")

    @override
    def edit_year(self, new_year: str) -> None:
        """Edit the year tag (TDRC and TYER).

        Args:
            new_year: The new year to set (e.g., '2026', '2026-10', '2026-10-04').

        Raises:
            InvalidTagValueError: If the year format is invalid.
            TagWriteError: If the year tag cannot be edited.
        """
        validated_year = validate_year(new_year)
        try:
            self._id3_tags["TDRC"] = TDRC(encoding=3, text=validated_year)
            self._id3_tags["TYER"] = TYER(encoding=3, text=validated_year)
        except ID3Error as e:
            logger.error(f"Failed to edit year tag: {e}")
            raise TagWriteError(f"Failed to edit year tag: {e}") from e

    @override
    def clear_year(self) -> None:
        """Clear the year tag (TDRC and TYER).

        Raises:
            TagWriteError: If the year tag cannot be cleared.
        """
        try:
            self._id3_tags.pop("TDRC", None)
            self._id3_tags.pop("TYER", None)
        except ID3Error as e:
            logger.error(f"Failed to clear year tag: {e}")
            raise TagWriteError(f"Failed to clear year tag: {e}") from e

    @override
    def edit_genre(self, new_genre: str) -> None:
        """Edit the genre tag (TCON).

        Args:
            new_genre: The new genre to set.

        Raises:
            TagWriteError: If the genre tag cannot be edited.
        """
        self._set_tag("TCON", TCON(encoding=3, text=new_genre), "genre")

    @override
    def clear_genre(self) -> None:
        """Clear the genre tag (TCON).

        Raises:
            TagWriteError: If the genre tag cannot be cleared.
        """
        self._clear_tag("TCON", "genre")

    @override
    def edit_disk_number(self, new_disk_number: str) -> None:
        """Edit the disk number tag (TPOS).

        Args:
            new_disk_number: The new disk number to set (e.g., '1' or '1/2').

        Raises:
            InvalidTagValueError: If the disk number format is invalid.
            TagWriteError: If the disk number tag cannot be edited.
        """
        validate_track_or_disk_number(new_disk_number, "disk")
        self._set_tag("TPOS", TPOS(encoding=3, text=new_disk_number), "disk number")

    @override
    def clear_disk_number(self) -> None:
        """Clear the disk number tag (TPOS).

        Raises:
            TagWriteError: If the disk number tag cannot be cleared.
        """
        self._clear_tag("TPOS", "disk number")

    @override
    def edit_track_number(self, new_track_number: str) -> None:
        """Edit the track number tag (TRCK).

        Args:
            new_track_number: The new track number to set (e.g., '1' or '1/10').

        Raises:
            InvalidTagValueError: If the track number format is invalid.
            TagWriteError: If the track number tag cannot be edited.
        """
        validate_track_or_disk_number(new_track_number, "track")
        self._set_tag("TRCK", TRCK(encoding=3, text=new_track_number), "track number")

    @override
    def clear_track_number(self) -> None:
        """Clear the track number tag (TRCK).

        Raises:
            TagWriteError: If the track number tag cannot be cleared.
        """
        self._clear_tag("TRCK", "track number")

    @override
    def edit_lyrics(
        self, new_lyrics: str, lang: str = "eng", desc: str = "Lyrics"
    ) -> None:
        """Edit the lyrics tag (USLT).

        Args:
            new_lyrics: The new lyrics text to set.
            lang: The 3-letter language code (default: 'eng').
            desc: Description of the lyrics (default: 'Lyrics').

        Raises:
            TagWriteError: If the lyrics tag cannot be edited.
        """
        if not re.match(r"^[a-z]{3}$", lang):
            logger.warning(
                f"Invalid language code: '{lang}'. Expected a 3-letter lowercase ISO code (e.g., 'eng')."
            )

        normalized_lyrics = new_lyrics.replace("\r\n", "\r").replace("\n", "\r")

        try:
            self._id3_tags.delall("USLT")
            self._id3_tags["USLT"] = USLT(
                encoding=3, text=normalized_lyrics, lang=lang, desc=desc
            )
        except ID3Error as e:
            logger.error(f"Failed to edit lyrics tag: {e}")
            raise TagWriteError(f"Failed to edit lyrics tag: {e}") from e

    @override
    def clear_lyrics(self) -> None:
        """Clear the lyrics tag (USLT).

        Raises:
            TagWriteError: If the lyrics tag cannot be cleared.
        """
        try:
            self._id3_tags.delall("USLT")
        except ID3Error as e:
            logger.error(f"Failed to clear lyrics tag: {e}")
            raise TagWriteError(f"Failed to clear lyrics tag: {e}") from e

    @override
    def edit_album_art(
        self, new_album_art: str, desc: str = "Front Cover", type: int = 3
    ) -> None:
        """Edit the album art tag (APIC).

        Args:
            new_album_art: The album art as a base64-encoded data URI.
            desc: Description of the album art (default: 'Front Cover').
            type: Picture type as defined in ID3v2 (default: 3 = Cover (front)).

        Raises:
            InvalidTagValueError: If the album art Data URI or image data is invalid.
            TagWriteError: If the album art tag cannot be edited.
        """
        mime, album_art_bytes = validate_album_art(new_album_art)

        try:
            self._id3_tags.delall("APIC")
            self._id3_tags["APIC"] = APIC(
                encoding=3, mime=mime, type=type, desc=desc, data=album_art_bytes
            )
        except ID3Error as e:
            logger.error(f"Failed to edit album art tag: {e}")
            raise TagWriteError(f"Failed to edit album art tag: {e}") from e

    @override
    def clear_album_art(self) -> None:
        """Clear the album art tag (APIC).

        Raises:
            TagWriteError: If the album art tag cannot be cleared.
        """
        try:
            self._id3_tags.delall("APIC")
        except ID3Error as e:
            logger.error(f"Failed to clear album art tag: {e}")
            raise TagWriteError(f"Failed to clear album art tag: {e}") from e

    @override
    def clear_all_tags(self) -> None:
        """Clear all tags from the audio file.

        Raises:
            TagWriteError: If the tags cannot be cleared.
        """
        try:
            self._tags.clear()
        except ID3Error as e:
            logger.error(f"Failed to clear all tags: {e}")
            raise TagWriteError(f"Failed to clear all tags: {e}") from e
