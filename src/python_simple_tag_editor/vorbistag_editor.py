"""Vorbis comment tag editor implementation for FLAC and Ogg Opus audio files."""

from __future__ import annotations

import base64
import logging
from typing import cast, override

from mutagen import MutagenError
from mutagen._vorbis import VCommentDict
from mutagen.flac import FLAC, Picture, VCFLACDict
from mutagen.flac import error as FLACError
from mutagen.oggopus import OggOpus, OggOpusVComment
from mutagen.oggopus import error as OggOpusError

from .audio_tag import validate_album_art
from .audio_tag_editor import (
    SimpleAudioTagEditor,
    validate_track_or_disk_number,
    validate_year,
)
from .exceptions import TagWriteError

logger = logging.getLogger(__name__)

__all__ = [
    "SimpleFLACTagEditor",
    "SimpleOpusTagEditor",
    "SimpleVorbisTagEditor",
]


class SimpleVorbisTagEditor(SimpleAudioTagEditor):
    """Base tag editor for audio files using Vorbis comments."""

    def __init__(
        self,
        audio: FLAC | OggOpus,
        tags: VCFLACDict | OggOpusVComment,
    ) -> None:
        super().__init__(audio, tags)

    @property
    def _vorbis_tags(self) -> VCommentDict:
        """Cast base _tags to VCommentDict for Vorbis comment operations."""
        return cast(VCommentDict, self._tags)

    def _set_tag(self, key: str, tag_value: list[str], tag_name: str) -> None:
        """Helper to set a Vorbis tag with error handling."""
        try:
            self._vorbis_tags[key] = tag_value
        except MutagenError as e:
            logger.error(f"Failed to edit {tag_name} tag: {e}")
            raise TagWriteError(f"Failed to edit {tag_name} tag: {e}") from e

    def _clear_tag(self, key: str, tag_name: str) -> None:
        """Helper to clear a Vorbis tag with error handling."""
        try:
            if key in self._vorbis_tags:
                del self._vorbis_tags[key]
        except MutagenError as e:
            logger.error(f"Failed to clear {tag_name} tag: {e}")
            raise TagWriteError(f"Failed to clear {tag_name} tag: {e}") from e

    @override
    def edit_title(self, new_title: str) -> None:
        """Edit the title tag (TITLE)."""
        self._set_tag("TITLE", [new_title], "title")

    @override
    def clear_title(self) -> None:
        """Clear the title tag (TITLE)."""
        self._clear_tag("TITLE", "title")

    @override
    def edit_artist(self, new_artist: str) -> None:
        """Edit the artist tag (ARTIST)."""
        self._set_tag("ARTIST", [new_artist], "artist")

    @override
    def clear_artist(self) -> None:
        """Clear the artist tag (ARTIST)."""
        self._clear_tag("ARTIST", "artist")

    @override
    def edit_album(self, new_album: str) -> None:
        """Edit the album tag (ALBUM)."""
        self._set_tag("ALBUM", [new_album], "album")

    @override
    def clear_album(self) -> None:
        """Clear the album tag (ALBUM)."""
        self._clear_tag("ALBUM", "album")

    @override
    def edit_year(self, new_year: str) -> None:
        """Edit the year tag (DATE)."""
        valid_year = validate_year(new_year)
        self._set_tag("DATE", [valid_year], "year")

    @override
    def clear_year(self) -> None:
        """Clear the year tag (DATE and YEAR)."""
        self._clear_tag("DATE", "year")
        self._clear_tag("YEAR", "year")

    @override
    def edit_genre(self, new_genre: str) -> None:
        """Edit the genre tag (GENRE)."""
        self._set_tag("GENRE", [new_genre], "genre")

    @override
    def clear_genre(self) -> None:
        """Clear the genre tag (GENRE)."""
        self._clear_tag("GENRE", "genre")

    @override
    def edit_disk_number(self, new_disk_number: str) -> None:
        """Edit the disk number tag (DISCNUMBER and DISCTOTAL)."""
        num, total = validate_track_or_disk_number(new_disk_number, "disk")
        self._set_tag("DISCNUMBER", [str(num)], "disk number")
        if total > 0:
            self._set_tag("DISCTOTAL", [str(total)], "disk total")
        else:
            self._clear_tag("DISCTOTAL", "disk total")
            self._clear_tag("TOTALDISCS", "disk total")

    @override
    def clear_disk_number(self) -> None:
        """Clear the disk number tags."""
        self._clear_tag("DISCNUMBER", "disk number")
        self._clear_tag("DISC", "disk number")
        self._clear_tag("DISCTOTAL", "disk total")
        self._clear_tag("TOTALDISCS", "disk total")

    @override
    def edit_track_number(self, new_track_number: str) -> None:
        """Edit the track number tag (TRACKNUMBER and TRACKTOTAL)."""
        num, total = validate_track_or_disk_number(new_track_number, "track")
        self._set_tag("TRACKNUMBER", [str(num)], "track number")
        if total > 0:
            self._set_tag("TRACKTOTAL", [str(total)], "track total")
        else:
            self._clear_tag("TRACKTOTAL", "track total")
            self._clear_tag("TOTALTRACKS", "track total")

    @override
    def clear_track_number(self) -> None:
        """Clear the track number tags."""
        self._clear_tag("TRACKNUMBER", "track number")
        self._clear_tag("TRACKTOTAL", "track total")
        self._clear_tag("TOTALTRACKS", "track total")

    @override
    def edit_lyrics(
        self, new_lyrics: str, lang: str = "eng", desc: str = "Lyrics"
    ) -> None:
        """Edit the lyrics tag (LYRICS)."""
        normalized_lyrics = new_lyrics.replace("\r\n", "\n").replace("\r", "\n")
        self._set_tag("LYRICS", [normalized_lyrics], "lyrics")

    @override
    def clear_lyrics(self) -> None:
        """Clear the lyrics tag."""
        self._clear_tag("LYRICS", "lyrics")
        self._clear_tag("UNSYNCEDLYRICS", "lyrics")

    @override
    def clear_all_tags(self) -> None:
        """Clear all tags from the Vorbis comments."""
        try:
            self._tags.clear()
        except MutagenError as e:
            logger.error(f"Failed to clear all tags: {e}")
            raise TagWriteError(f"Failed to clear all tags: {e}") from e


class SimpleFLACTagEditor(SimpleVorbisTagEditor):
    """Tag editor for FLAC audio files."""

    def __init__(self, audio: FLAC, tags: VCFLACDict) -> None:
        super().__init__(audio, tags)

    @property
    def _flac_audio(self) -> FLAC:
        """Cast base _audio to FLAC for picture operations."""
        return cast(FLAC, self._audio)

    @override
    def edit_album_art(
        self, new_album_art: str, desc: str = "Front Cover", type: int = 3
    ) -> None:
        """Edit the album art (FLAC Picture metadata block)."""
        mime, album_art_bytes = validate_album_art(new_album_art)
        pic = Picture()
        pic.type = type
        pic.mime = mime
        pic.desc = desc
        pic.data = album_art_bytes

        try:
            self._flac_audio.clear_pictures()
            self._flac_audio.add_picture(pic)
        except (FLACError, MutagenError) as e:
            logger.error(f"Failed to edit FLAC album art: {e}")
            raise TagWriteError(f"Failed to edit album art: {e}") from e

    @override
    def clear_album_art(self) -> None:
        """Clear the album art pictures from the FLAC file."""
        try:
            self._flac_audio.clear_pictures()
        except (FLACError, MutagenError) as e:
            logger.error(f"Failed to clear FLAC album art: {e}")
            raise TagWriteError(f"Failed to clear album art: {e}") from e

    @override
    def clear_all_tags(self) -> None:
        """Clear all Vorbis tags and pictures from the FLAC file."""
        super().clear_all_tags()
        self.clear_album_art()


class SimpleOpusTagEditor(SimpleVorbisTagEditor):
    """Tag editor for Ogg Opus audio files."""

    def __init__(self, audio: OggOpus, tags: OggOpusVComment) -> None:
        super().__init__(audio, tags)

    @override
    def edit_album_art(
        self, new_album_art: str, desc: str = "Front Cover", type: int = 3
    ) -> None:
        """Edit the album art (METADATA_BLOCK_PICTURE in Opus tags)."""
        mime, album_art_bytes = validate_album_art(new_album_art)
        pic = Picture()
        pic.type = type
        pic.mime = mime
        pic.desc = desc
        pic.data = album_art_bytes

        try:
            serialized = pic.write()
            b64_block = base64.b64encode(serialized).decode("ascii")
            self._vorbis_tags["METADATA_BLOCK_PICTURE"] = [b64_block]
        except (OggOpusError, MutagenError) as e:
            logger.error(f"Failed to edit Opus album art: {e}")
            raise TagWriteError(f"Failed to edit album art: {e}") from e

    @override
    def clear_album_art(self) -> None:
        """Clear the METADATA_BLOCK_PICTURE tag from the Opus file."""
        self._clear_tag("METADATA_BLOCK_PICTURE", "album art")
