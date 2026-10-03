"""Vorbis comment tag reader implementation for FLAC and Ogg Opus audio files."""

from __future__ import annotations

import base64
import logging
from dataclasses import dataclass

from mutagen import MutagenError
from mutagen._vorbis import VCommentDict
from mutagen.flac import FLAC, Picture
from mutagen.flac import error as FLACError
from mutagen.oggopus import OggOpus
from mutagen.oggopus import error as OggOpusError

from .audio_tag import SimpleAudioTag, b64encode
from .exceptions import TagReadError

logger = logging.getLogger(__name__)

__all__ = ["SimpleFLACTag", "SimpleOpusTag", "SimpleVorbisTag"]


@dataclass(frozen=True)
class SimpleVorbisTag(SimpleAudioTag):
    """Audio tag representation for Vorbis comment metadata."""

    @staticmethod
    def _get_tag(tags: VCommentDict, tag_name: str) -> str | None:
        """Extract first text value for a tag name safely."""
        values = tags.get(tag_name)
        if values and len(values) > 0:
            return str(values[0])
        logger.debug(f"Tag '{tag_name}' not found in Vorbis comments.")
        return None

    @staticmethod
    def _get_track_number(tags: VCommentDict) -> str | None:
        """Extract track number and format as 'num' or 'num/total'."""
        values = tags.get("TRACKNUMBER")
        if not values or len(values) == 0:
            return None
        val = str(values[0]).strip()
        if "/" in val:
            return val
        total_values = tags.get("TRACKTOTAL") or tags.get("TOTALTRACKS")
        if total_values and len(total_values) > 0:
            total = str(total_values[0]).strip()
            if total and total != "0":
                return f"{val}/{total}"
        return val

    @staticmethod
    def _get_disk_number(tags: VCommentDict) -> str | None:
        """Extract disk number and format as 'num' or 'num/total'."""
        values = tags.get("DISCNUMBER") or tags.get("DISC")
        if not values or len(values) == 0:
            return None
        val = str(values[0]).strip()
        if "/" in val:
            return val
        total_values = tags.get("DISCTOTAL") or tags.get("TOTALDISCS")
        if total_values and len(total_values) > 0:
            total = str(total_values[0]).strip()
            if total and total != "0":
                return f"{val}/{total}"
        return val

    @staticmethod
    def _get_lyrics(tags: VCommentDict) -> str | None:
        """Extract lyrics text and normalize line endings."""
        values = tags.get("LYRICS") or tags.get("UNSYNCEDLYRICS")
        if values and len(values) > 0:
            return str(values[0]).replace("\r\n", "\n").replace("\r", "\n")
        return None


@dataclass(frozen=True)
class SimpleFLACTag(SimpleVorbisTag):
    """Audio tag representation for FLAC metadata."""

    @classmethod
    def from_FLAC(cls, flac_audio: FLAC) -> SimpleFLACTag:
        """Create a SimpleFLACTag instance from a FLAC audio object.

        Args:
            flac_audio: The mutagen FLAC object to read from.

        Returns:
            SimpleFLACTag: The extracted metadata.

        Raises:
            TagReadError: If an error occurs while reading the tags.
        """
        try:
            tags = (
                flac_audio.tags
                if isinstance(flac_audio.tags, VCommentDict)
                else VCommentDict()
            )
            title = cls._get_tag(tags, "TITLE")
            artist = cls._get_tag(tags, "ARTIST")
            album = cls._get_tag(tags, "ALBUM")
            year = cls._get_tag(tags, "DATE") or cls._get_tag(tags, "YEAR")
            genre = cls._get_tag(tags, "GENRE")
            track_number = cls._get_track_number(tags)
            disk_number = cls._get_disk_number(tags)
            lyrics = cls._get_lyrics(tags)
            album_art = cls._get_album_art(flac_audio)
        except (FLACError, MutagenError) as e:
            logger.error(f"Mutagen error while reading FLAC tags: {e}")
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
    def _get_album_art(flac_audio: FLAC) -> str | None:
        """Extract front cover artwork from FLAC pictures."""
        if not flac_audio.pictures:
            return None
        for pic in flac_audio.pictures:
            if pic.type == 3:  # Cover (front)
                return b64encode(pic.mime, pic.data)
        # Fallback to first picture
        first_pic = flac_audio.pictures[0]
        return b64encode(first_pic.mime, first_pic.data)


@dataclass(frozen=True)
class SimpleOpusTag(SimpleVorbisTag):
    """Audio tag representation for Ogg Opus metadata."""

    @classmethod
    def from_OggOpus(cls, opus_audio: OggOpus) -> SimpleOpusTag:
        """Create a SimpleOpusTag instance from an OggOpus audio object.

        Args:
            opus_audio: The mutagen OggOpus object to read from.

        Returns:
            SimpleOpusTag: The extracted metadata.

        Raises:
            TagReadError: If an error occurs while reading the tags.
        """
        try:
            tags = (
                opus_audio.tags
                if isinstance(opus_audio.tags, VCommentDict)
                else VCommentDict()
            )
            title = cls._get_tag(tags, "TITLE")
            artist = cls._get_tag(tags, "ARTIST")
            album = cls._get_tag(tags, "ALBUM")
            year = cls._get_tag(tags, "DATE") or cls._get_tag(tags, "YEAR")
            genre = cls._get_tag(tags, "GENRE")
            track_number = cls._get_track_number(tags)
            disk_number = cls._get_disk_number(tags)
            lyrics = cls._get_lyrics(tags)
            album_art = cls._get_album_art(opus_audio)
        except (OggOpusError, MutagenError) as e:
            logger.error(f"Mutagen error while reading Opus tags: {e}")
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
    def _get_album_art(opus_audio: OggOpus) -> str | None:
        """Extract artwork from METADATA_BLOCK_PICTURE in Opus comments."""
        if opus_audio.tags is None:
            return None
        values = opus_audio.tags.get("METADATA_BLOCK_PICTURE")
        if not values or len(values) == 0:
            return None
        try:
            raw_bytes = base64.b64decode(values[0])
            pic = Picture(raw_bytes)
            return b64encode(pic.mime, pic.data)
        except (ValueError, MutagenError) as e:
            logger.warning(f"Failed to decode Opus METADATA_BLOCK_PICTURE: {e}")
            return None
