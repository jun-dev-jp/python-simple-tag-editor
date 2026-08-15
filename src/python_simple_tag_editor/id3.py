import logging
from dataclasses import dataclass

from mutagen.id3 import ID3

from .audio_tag import SimpleAudioTag, b64encode
from .exceptions import TagReadError

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SimpleID3Tag(SimpleAudioTag):
    @classmethod
    def from_ID3(cls, id3_tags: ID3) -> SimpleID3Tag:
        """Create a SimpleID3Tag from an ID3 tags object."""
        try:
            title = SimpleID3Tag._get_tag(id3_tags, "TIT2")
            artist = SimpleID3Tag._get_tag(id3_tags, "TPE1")
            album = SimpleID3Tag._get_tag(id3_tags, "TALB")
            year = SimpleID3Tag._get_tag(id3_tags, "TDRC") or SimpleID3Tag._get_tag(
                id3_tags, "TYER"
            )
            genre = SimpleID3Tag._get_tag(id3_tags, "TCON")
            disk_number = SimpleID3Tag._get_tag(id3_tags, "TPOS")
            track_number = SimpleID3Tag._get_tag(id3_tags, "TRCK")
            lyrics = SimpleID3Tag._get_lyrics(id3_tags)
            album_art = SimpleID3Tag._get_album_art(id3_tags)
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise TagReadError(f"Unexpected error: {e}") from e

        return SimpleID3Tag(
            title,
            artist,
            album,
            year,
            genre,
            disk_number,
            track_number,
            lyrics,
            album_art,
        )

    @staticmethod
    def _get_tag(id3_tags: ID3, tag_name: str) -> str | None:
        """Extract text from ID3 tag."""
        if tag_name not in id3_tags:
            logger.warning(f"Tag '{tag_name}' not found in ID3 tags.")
            return None

        return str(id3_tags[tag_name].text[0])

    @staticmethod
    def _get_lyrics(id3_tags: ID3) -> str | None:
        """
        Extract lyrics text from USLT tag and replace carriage returns if needed.
        Note: this method only supports the first USLT frame if multiple are present.
        """
        frames = id3_tags.getall("USLT")
        if not frames:
            logger.warning("Lyrics tag 'USLT' not found in ID3 tags.")
            return None

        lyrics_text = str(frames[0].text)
        normalized_lyrics = lyrics_text.replace("\r\n", "\n").replace("\r", "\n")

        return normalized_lyrics

    @staticmethod
    def _get_album_art(id3_tags: ID3) -> str | None:
        """
        Extract album art from APIC tag and return as base64-encoded data URI string.
        Note: this method only supports the first APIC frame if multiple are present.
        """
        frames = id3_tags.getall("APIC")
        if not frames:
            logger.warning("Album art tag 'APIC' not found in ID3 tags.")
            return None

        frame = frames[0]
        mime = getattr(frame, "mime", None)
        data = getattr(frame, "data", None)
        if not (data and mime):
            logger.warning("APIC frame contains no image data.")
            return None

        try:
            return b64encode(mime, data)
        except ValueError as e:
            logger.error(f"APIC frame is invalid: {e}")
            return None
