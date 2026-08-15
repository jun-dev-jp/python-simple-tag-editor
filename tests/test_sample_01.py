"""Integration tests for reading tags from actual sample audio files (sample_01.mp3)."""

from __future__ import annotations

from pathlib import Path

from python_simple_tag_editor import read_tags


def test_read_sample_01_mp3_tags() -> None:
    """Test reading tags from samples/sample_01.mp3 and verify all extracted metadata fields."""
    sample_path = Path("samples/sample_01.mp3")
    assert sample_path.exists(), f"Sample file not found: {sample_path}"

    tags = read_tags(sample_path)

    assert tags.title == "MP3サンプル"
    assert tags.artist == "東進ブックス"
    assert tags.album == "TOEIC L&Rテスト上級英単語1500"
    assert tags.year == "2000"
    assert tags.genre == "Books & Spoken"
    assert tags.track_number == "2/100"
    assert tags.disk_number == "1/2"
    assert tags.lyrics == "これはMP3のサンプルデータです。\nThis is a sample."
    assert tags.album_art is not None

    # Test album art decoding
    decoded = tags.b64decode_album_art()
    assert decoded is not None
    mime, data = decoded
    assert mime == "image/jpeg"
    assert len(data) == 103616
