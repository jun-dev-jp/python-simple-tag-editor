"""audio_tag.py"""

import base64
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SimpleAudioTag:
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
        """
        Decode the base64-encoded album art data URI.

        Returns:
            tuple[str, bytes] | None: A tuple containing the MIME type and base64-encoded data, or None if decoding fails.
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
    """
    Parse a data URI into its MIME type and base64-encoded data.

    Args:
        data_uri (str): The data URI encoded in base64 to parse.

    Returns:
        tuple[str, str]: A tuple containing the MIME type and base64-encoded data.

    Raises:
        ValueError: If the data URI is not in the expected format.
    """
    if (
        not data_uri.startswith("data:")
        or "," not in data_uri
        or "base64" not in data_uri
    ):
        logger.error("Invalid data URI format")
        raise ValueError("Invalid data URI format")

    header, data = data_uri.split(",", 1)
    mime = header.replace("data:", "").split(";")[0]
    return (mime, data)


def b64encode(mime: str, data: bytes) -> str:
    """
    Encode binary data into a base64-encoded data URI.

    Args:
        mime (str): The MIME type of the data.
        data (bytes): The binary data to encode.

    Returns:
        str: The base64-encoded data URI.
    """
    try:
        data_b64 = base64.b64encode(data).decode("utf-8")
        data_uri = f"data:{mime};base64," + data_b64
        return data_uri
    except ValueError as e:
        logger.error(f"Failed to encode data: {e}")
        raise ValueError(f"Failed to encode data: {e}")


def b64decode(data_uri: str) -> tuple[str, bytes]:
    """
    Decode a base64-encoded data URI into its MIME type and raw data.

    Args:
        data_uri (str): The data URI encoded in base64 to decode.

    Returns:
        tuple[str, bytes]: A tuple containing the MIME type and raw data.

    Raises:
        ValueError: If the data URI is not in the expected format or decoding fails.
    """
    try:
        mime, data = parse_base64_encoded_data_uri(data_uri)
        return (mime, base64.b64decode(data))
    except ValueError as e:
        logger.error(f"Failed to decode base64 data: {e}")
        raise ValueError(f"Failed to decode base64 data: {e}")
