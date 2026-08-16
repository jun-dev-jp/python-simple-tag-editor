"""ID3 tag reader implementation for MP3 and AIFF files."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from mutagen.id3 import ID3Tags
from mutagen.id3 import error as ID3Error

from .audio_tag import SimpleAudioTag, b64encode
from .exceptions import TagReadError

logger = logging.getLogger(__name__)

__all__ = ["SimpleID3Tag"]


@dataclass(frozen=True)
class SimpleID3Tag(SimpleAudioTag):
    """Audio tag representation for ID3 metadata (used in MP3 and AIFF)."""

    @classmethod
    def from_ID3Tags(cls, id3_tags: ID3Tags) -> SimpleID3Tag:
        """Create a SimpleID3Tag instance from an ID3Tags object.

        Args:
            id3_tags: The mutagen ID3Tags object to read from.

        Returns:
            SimpleID3Tag: The extracted metadata.

        Raises:
            TagReadError: If an error occurs while reading the tags.
        """
        try:
            title = cls._get_tag(id3_tags, "TIT2")
            artist = cls._get_tag(id3_tags, "TPE1")
            album = cls._get_tag(id3_tags, "TALB")
            year = cls._get_tag(id3_tags, "TDRC") or cls._get_tag(id3_tags, "TYER")
            genre = cls._get_tag(id3_tags, "TCON")
            disk_number = cls._get_tag(id3_tags, "TPOS")
            track_number = cls._get_tag(id3_tags, "TRCK")
            lyrics = cls._get_lyrics(id3_tags)
            album_art = cls._get_album_art(id3_tags)
        except ID3Error as e:
            logger.error(f"Mutagen ID3Error while reading tags: {e}")
            raise TagReadError(f"Mutagen ID3Error: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error while reading ID3 tags: {e}")
            raise TagReadError(f"Unexpected error: {e}") from e

        return cls(
            title=title,
            artist=artist,
            album=album,
            year=year,
            genre=genre,
            disk_number=disk_number,
            track_number=track_number,
            lyrics=lyrics,
            album_art=album_art,
        )

    @staticmethod
    def _get_tag(id3_tags: ID3Tags, tag_name: str) -> str | None:
        """Extract text from an ID3 tag safely."""
        if tag_name not in id3_tags:
            logger.debug(f"Tag '{tag_name}' not found in ID3 tags.")
            return None

        frame = id3_tags[tag_name]
        text_list = getattr(frame, "text", None)
        if text_list and len(text_list) > 0:
            return str(text_list[0])
        return str(frame) if frame is not None else None

    @staticmethod
    def _get_lyrics(id3_tags: ID3Tags) -> str | None:
        """Extract lyrics text from USLT tag and normalize line endings.

        Supports the first USLT frame if multiple are present.
        """
        frames = id3_tags.getall("USLT")
        if not frames:
            logger.debug("Lyrics tag 'USLT' not found in ID3 tags.")
            return None

        lyrics_text = str(getattr(frames[0], "text", ""))
        if not lyrics_text:
            return None
        return lyrics_text.replace("\r\n", "\n").replace("\r", "\n")

    @staticmethod
    def _get_album_art(id3_tags: ID3Tags) -> str | None:
        """Extract album art from APIC tag and return as base64-encoded data URI string.

        Supports the first APIC frame if multiple are present.
        """
        frames = id3_tags.getall("APIC")
        if not frames:
            logger.debug("Album art tag 'APIC' not found in ID3 tags.")
            return None

        frame = frames[0]
        mime = getattr(frame, "mime", None)
        data = getattr(frame, "data", None)
        if not (data and mime):
            logger.warning("APIC frame contains no image data or MIME type.")
            return None

        try:
            return b64encode(str(mime), bytes(data))
        except ValueError as e:
            logger.error(f"APIC frame image data is invalid: {e}")
            return None
