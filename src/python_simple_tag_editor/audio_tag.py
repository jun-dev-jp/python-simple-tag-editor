"""Core data model and utilities for audio metadata tags."""

from __future__ import annotations

import base64
import binascii
import logging
import re
from dataclasses import dataclass
from typing import Final

from .exceptions import InvalidTagValueError

logger = logging.getLogger(__name__)

SUPPORTED_ALBUM_ART_MIME_TYPES: Final[tuple[str, ...]] = (
    "image/jpeg",
    "image/jpg",
    "image/png",
)

_DATA_URI_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"^data:(image/[a-zA-Z0-9.+-]+);base64,([A-Za-z0-9+/=]+)$"
)

JPEG_MAGIC: Final[bytes] = b"\xff\xd8\xff"
PNG_MAGIC: Final[bytes] = b"\x89PNG\r\n\x1a\n"

__all__ = [
    "JPEG_MAGIC",
    "PNG_MAGIC",
    "SUPPORTED_ALBUM_ART_MIME_TYPES",
    "SimpleAudioTag",
    "b64decode",
    "b64encode",
    "parse_base64_encoded_data_uri",
    "validate_album_art",
]


@dataclass(frozen=True)
class SimpleAudioTag:
    """Immutable representation of audio file metadata tags."""

    title: str | None = None
    artist: str | None = None
    album: str | None = None
    year: str | None = None
    genre: str | None = None
    disk_number: str | None = None
    track_number: str | None = None
    lyrics: str | None = None
    album_art: str | None = None

    def b64decode_album_art(self) -> tuple[str, bytes] | None:
        """Decode the base64-encoded album art data URI.

        Returns:
            tuple[str, bytes] | None: A tuple containing the MIME type and raw image bytes,
                or None if no album art is present or decoding fails.
        """
        if self.album_art is None:
            logger.warning("album_art is None")
            return None
        try:
            return b64decode(self.album_art)
        except ValueError as e:
            logger.error(f"Failed to decode album_art: {e}")
            return None


def parse_base64_encoded_data_uri(data_uri: str) -> tuple[str, str]:
    """Parse a data URI into its MIME type and base64-encoded data string.

    Args:
        data_uri: The data URI to parse (e.g., 'data:image/jpeg;base64,...').

    Returns:
        tuple[str, str]: A tuple of (mime_type, base64_data).

    Raises:
        InvalidTagValueError: If the data URI is not in the expected format.
    """
    match = _DATA_URI_PATTERN.fullmatch(data_uri)
    if not match:
        logger.error(f"Invalid data URI format: {data_uri[:50]}...")
        raise InvalidTagValueError(
            f"Invalid album art data URI format: '{data_uri[:50]}...'. "
            "Expected 'data:<mime-type>;base64,<base64-data>'."
        )

    mime = match.group(1).lower()
    data = match.group(2)
    return (mime, data)


def b64encode(mime: str, data: bytes) -> str:
    """Encode binary data into a base64-encoded data URI.

    Args:
        mime: The MIME type of the data (e.g., 'image/jpeg').
        data: The binary data to encode.

    Returns:
        str: The base64-encoded data URI string.

    Raises:
        ValueError: If encoding fails.
    """
    try:
        data_b64 = base64.b64encode(data).decode("utf-8")
        return f"data:{mime};base64,{data_b64}"
    except (TypeError, ValueError) as e:
        logger.error(f"Failed to encode data: {e}")
        raise ValueError(f"Failed to encode data: {e}") from e


def b64decode(data_uri: str) -> tuple[str, bytes]:
    """Decode a base64-encoded data URI into its MIME type and raw bytes.

    Strictly validates the Data URI structure and base64 payload.

    Args:
        data_uri: The base64-encoded data URI to decode.

    Returns:
        tuple[str, bytes]: A tuple of (mime_type, raw_bytes).

    Raises:
        InvalidTagValueError: If the data URI format is invalid or decoding fails.
    """
    mime, data = parse_base64_encoded_data_uri(data_uri)
    try:
        raw_bytes = base64.b64decode(data, validate=True)
    except (binascii.Error, ValueError) as e:
        logger.error(f"Failed to decode base64 data: {e}")
        raise InvalidTagValueError(f"Invalid base64 payload in album art: {e}") from e
    return (mime, raw_bytes)


def validate_album_art(data_uri: str) -> tuple[str, bytes]:
    """Validate and decode album art data URI.

    Validates:
        1. Strict Data URI structure and base64 payload.
        2. MIME type is supported ('image/jpeg', 'image/jpg', 'image/png').
        3. Binary payload magic bytes match the specified MIME type.

    Args:
        data_uri: The base64-encoded album art Data URI.

    Returns:
        tuple[str, bytes]: (normalized_mime, image_bytes) where 'image/jpg'
            is normalized to 'image/jpeg'.

    Raises:
        InvalidTagValueError: If the Data URI format is invalid, base64 payload is corrupt,
            MIME type is unsupported, or image magic bytes do not match the MIME type.
    """
    mime, raw_bytes = b64decode(data_uri)

    if mime not in SUPPORTED_ALBUM_ART_MIME_TYPES:
        raise InvalidTagValueError(
            f"Unsupported album art MIME type: '{mime}'. "
            f"Supported types are: {', '.join(SUPPORTED_ALBUM_ART_MIME_TYPES)}."
        )

    # Normalize image/jpg to image/jpeg
    normalized_mime = "image/jpeg" if mime == "image/jpg" else mime

    if normalized_mime == "image/jpeg":
        if not raw_bytes.startswith(JPEG_MAGIC):
            raise InvalidTagValueError(
                f"Album art MIME type is '{mime}', but image data is not valid JPEG."
            )
    elif normalized_mime == "image/png":
        if not raw_bytes.startswith(PNG_MAGIC):
            raise InvalidTagValueError(
                f"Album art MIME type is '{mime}', but image data is not valid PNG."
            )

    return normalized_mime, raw_bytes
