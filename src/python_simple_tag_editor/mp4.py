import logging
from dataclasses import dataclass

from mutagen.mp4 import MP4Cover, MP4Tags

from .audio_tag import SimpleAudioTag, b64encode
from .exceptions import TagReadError

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SimpleMP4Tag(SimpleAudioTag):
    @classmethod
    def from_MP4Tags(cls, mp4_tags: MP4Tags) -> SimpleMP4Tag:
        """Create a SimpleMP4Tag from an MP4 tags object."""
        try:
            album_art = SimpleMP4Tag._get_album_art(mp4_tags)
            title = SimpleMP4Tag._get_tag(mp4_tags, "©nam")
            artist = SimpleMP4Tag._get_tag(mp4_tags, "©ART")
            album = SimpleMP4Tag._get_tag(mp4_tags, "©alb")
            year = SimpleMP4Tag._get_tag(mp4_tags, "©day")
            genre = SimpleMP4Tag._get_tag(mp4_tags, "©gen")
            disk_number = SimpleMP4Tag._get_disk_number(mp4_tags)
            track_number = SimpleMP4Tag._get_track_number(mp4_tags)
            lyrics = SimpleMP4Tag._get_lyrics(mp4_tags)
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise TagReadError(f"Unexpected error: {e}") from e

        return SimpleMP4Tag(
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
    def _get_tag(mp4_tags: MP4Tags, tag_name: str) -> str | None:
        """Extract text from MP4 tag safely."""
        if mp4_tags.get(tag_name):
            return str(mp4_tags[tag_name][0])
        else:
            logger.warning(f"Tag '{tag_name}' not found in MP4 tags.")
            return None

    @staticmethod
    def _get_disk_number(mp4_tags: MP4Tags) -> str | None:
        """Extract disk number from 'disk' tag."""
        if mp4_tags.get("disk"):
            disk_info = mp4_tags["disk"][0]
            if isinstance(disk_info, tuple) and len(disk_info) == 2:
                disk_number, total_number = disk_info[0], disk_info[1]
                if total_number == 0:
                    return str(disk_number)
                return str(disk_number) + "/" + str(total_number)

        logger.warning("Disk number tag 'disk' not found or invalid in MP4 tags.")
        return None

    @staticmethod
    def _get_track_number(mp4_tags: MP4Tags) -> str | None:
        """Extract track number from 'trkn' tag."""
        if mp4_tags.get("trkn"):
            track_info = mp4_tags["trkn"][0]
            if isinstance(track_info, tuple) and len(track_info) == 2:
                track_number, total_number = track_info[0], track_info[1]
                if total_number == 0:
                    return str(track_number)
                return str(track_number) + "/" + str(total_number)

        logger.warning("Track number tag 'trkn' not found or invalid in MP4 tags.")
        return None

    @staticmethod
    def _get_lyrics(mp4_tags: MP4Tags) -> str | None:
        """Extract lyrics text from '©lyr' tag."""
        if mp4_tags.get("©lyr"):
            lyrics_text = str(mp4_tags["©lyr"][0])
            return lyrics_text.replace("\r\n", "\n").replace("\r", "\n")
        else:
            logger.warning("Lyrics tag '©lyr' not found in MP4 tags.")
            return None

    @staticmethod
    def _get_album_art(mp4_tags: MP4Tags) -> str | None:
        """Extract album art from 'covr' tag."""
        if "covr" not in mp4_tags or not mp4_tags["covr"]:
            logger.warning("Album art tag 'covr' not found in MP4 tags.")
            return None

        album_art: MP4Cover = mp4_tags["covr"][0]
        imageformat = album_art.imageformat
        if imageformat == MP4Cover.FORMAT_JPEG:
            mime = "image/jpeg"
        elif imageformat == MP4Cover.FORMAT_PNG:
            mime = "image/png"
        else:
            logger.warning(f"Unsupported album art image format: {imageformat}")
            return None

        try:
            return b64encode(mime, album_art)
        except ValueError as e:
            logger.error(f"Failed to encode album art: {e}")
            return None
