"""Integration tests for reading tags from actual sample audio files (sample_03.aiff)."""

from __future__ import annotations

from pathlib import Path

from python_simple_tag_editor import read_tags


def test_read_sample_03_aiff_tags() -> None:
    """Test reading tags from samples/sample_03.aiff and verify all extracted metadata fields."""
    sample_path = Path("samples/sample_03.aiff")
    assert sample_path.exists(), f"Sample file not found: {sample_path}"

    tags = read_tags(sample_path)

    assert tags.title == "AIFFサンプル"
    assert tags.artist == "東進ブックス"
    assert tags.album == "TOEIC L&Rテスト上級英単語1500"
    assert tags.year == "1998"
    assert tags.genre == "Books & Spoken"
    assert tags.track_number == "50"
    assert tags.disk_number == "2"
    assert tags.lyrics is None
    assert tags.album_art is not None

    # Test album art decoding
    decoded = tags.b64decode_album_art()
    assert decoded is not None
    mime, data = decoded
    assert mime == "image/jpeg"
    assert len(data) == 103616
