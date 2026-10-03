"""MP4/M4A tag reader implementation for MP4 audio files."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from mutagen import MutagenError
from mutagen.mp4 import MP4Cover, MP4Tags
from mutagen.mp4 import error as MP4Error

from .audio_tag import SimpleAudioTag, b64encode
from .exceptions import TagReadError

logger = logging.getLogger(__name__)

__all__ = ["SimpleMP4Tag"]


@dataclass(frozen=True)
class SimpleMP4Tag(SimpleAudioTag):
    """Audio tag representation for MP4/M4A metadata."""

    @classmethod
    def from_MP4Tags(cls, mp4_tags: MP4Tags) -> SimpleMP4Tag:
        """Create a SimpleMP4Tag instance from an MP4Tags object.

        Args:
            mp4_tags: The mutagen MP4Tags object to read from.

        Returns:
            SimpleMP4Tag: The extracted metadata.

        Raises:
            TagReadError: If an error occurs while reading the tags.
        """
        try:
            title = cls._get_tag(mp4_tags, "©nam")
            artist = cls._get_tag(mp4_tags, "©ART")
            album = cls._get_tag(mp4_tags, "©alb")
            year = cls._get_tag(mp4_tags, "©day")
            genre = cls._get_tag(mp4_tags, "©gen")
            disk_number = cls._get_disk_number(mp4_tags)
            track_number = cls._get_track_number(mp4_tags)
            lyrics = cls._get_lyrics(mp4_tags)
            album_art = cls._get_album_art(mp4_tags)
        except (MP4Error, MutagenError) as e:
            logger.error(f"Mutagen error while reading MP4 tags: {e}")
            raise TagReadError(f"Mutagen error: {e}") from e

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
    def _get_tag(mp4_tags: MP4Tags, tag_name: str) -> str | None:
        """Extract text from MP4 tag safely."""
        values = mp4_tags.get(tag_name)
        if values and len(values) > 0:
            return str(values[0])
        logger.debug(f"Tag '{tag_name}' not found in MP4 tags.")
        return None

    @staticmethod
    def _get_disk_number(mp4_tags: MP4Tags) -> str | None:
        """Extract disk number from 'disk' tag."""
        values = mp4_tags.get("disk")
        if values and len(values) > 0:
            disk_info = values[0]
            if isinstance(disk_info, tuple) and len(disk_info) >= 2:
                disk_number, total_number = disk_info[0], disk_info[1]
                if total_number == 0:
                    return str(disk_number)
                return f"{disk_number}/{total_number}"

        logger.debug("Disk number tag 'disk' not found in MP4 tags.")
        return None

    @staticmethod
    def _get_track_number(mp4_tags: MP4Tags) -> str | None:
        """Extract track number from 'trkn' tag."""
        values = mp4_tags.get("trkn")
        if values and len(values) > 0:
            track_info = values[0]
            if isinstance(track_info, tuple) and len(track_info) >= 2:
                track_number, total_number = track_info[0], track_info[1]
                if total_number == 0:
                    return str(track_number)
                return f"{track_number}/{total_number}"

        logger.debug("Track number tag 'trkn' not found in MP4 tags.")
        return None

    @staticmethod
    def _get_lyrics(mp4_tags: MP4Tags) -> str | None:
        """Extract lyrics text from '©lyr' tag and normalize line endings."""
        values = mp4_tags.get("©lyr")
        if values and len(values) > 0:
            lyrics_text = str(values[0])
            return lyrics_text.replace("\r\n", "\n").replace("\r", "\n")

        logger.debug("Lyrics tag '©lyr' not found in MP4 tags.")
        return None

    @staticmethod
    def _get_album_art(mp4_tags: MP4Tags) -> str | None:
        """Extract album art from 'covr' tag."""
        covers = mp4_tags.get("covr")
        if not covers or len(covers) == 0:
            logger.debug("Album art tag 'covr' not found in MP4 tags.")
            return None

        cover = covers[0]
        imageformat = getattr(cover, "imageformat", None)
        if imageformat == MP4Cover.FORMAT_JPEG:
            mime = "image/jpeg"
        elif imageformat == MP4Cover.FORMAT_PNG:
            mime = "image/png"
        else:
            logger.warning(f"Unsupported album art image format: {imageformat}")
            return None

        try:
            return b64encode(mime, bytes(cover))
        except ValueError as e:
            logger.error(f"Failed to encode MP4 album art: {e}")
            return None
