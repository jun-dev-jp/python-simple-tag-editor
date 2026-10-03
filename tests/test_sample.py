"""Integration and unit tests for reading and editing tags across audio formats (MP3, M4A, AIFF)."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from mutagen import File as MutagenFile

from python_simple_tag_editor import (
    SimpleAudioTag,
    b64decode,
    b64encode,
    get_tag_editor,
    parse_base64_encoded_data_uri,
    read_tags,
)
from python_simple_tag_editor.exceptions import (
    FileReadError,
    FileWriteError,
    UnsupportedAudioFormatError,
)

SAMPLE_DIR = Path("samples")


@pytest.mark.parametrize(
    (
        "sample_filename",
        "expected_title",
        "expected_artist",
        "expected_album",
        "expected_year",
        "expected_genre",
        "expected_track_number",
        "expected_disk_number",
        "expected_lyrics",
        "expected_art_mime",
        "expected_art_len",
    ),
    [
        (
            "sample_01.mp3",
            "MP3サンプル",
            "東進ブックス",
            "TOEIC L&Rテスト上級英単語1500",
            "2000",
            "Books & Spoken",
            "2/100",
            "1/2",
            "これはMP3のサンプルデータです。\nThis is a sample.",
            "image/jpeg",
            103616,
        ),
        (
            "sample_02.m4a",
            "M4Aサンプル",
            "東進ブックス",
            "TOEIC L&Rテスト上級英単語1500",
            "2010",
            "Books & Spoken",
            "55/60",
            "1/1",
            "これはM4Aのサンプルです。\nThis is a sample.",
            "image/png",
            503312,
        ),
        (
            "sample_03.aiff",
            "AIFFサンプル",
            "東進ブックス",
            "TOEIC L&Rテスト上級英単語1500",
            "1998",
            "Books & Spoken",
            "50",
            "2",
            None,
            "image/jpeg",
            103616,
        ),
    ],
)
def test_read_sample_tags(
    sample_filename: str,
    expected_title: str,
    expected_artist: str,
    expected_album: str,
    expected_year: str,
    expected_genre: str,
    expected_track_number: str,
    expected_disk_number: str,
    expected_lyrics: str | None,
    expected_art_mime: str,
    expected_art_len: int,
) -> None:
    """Test reading tags from various sample audio files and verify extracted metadata fields."""
    sample_path = SAMPLE_DIR / sample_filename
    assert sample_path.exists(), f"Sample file not found: {sample_path}"
    tags = read_tags(sample_path)
    assert tags.title == expected_title
    assert tags.artist == expected_artist
    assert tags.album == expected_album
    assert tags.year == expected_year
    assert tags.genre == expected_genre
    assert tags.track_number == expected_track_number
    assert tags.disk_number == expected_disk_number
    assert tags.lyrics == expected_lyrics
    assert tags.album_art is not None

    decoded = tags.b64decode_album_art()
    assert decoded is not None
    mime, data = decoded
    assert mime == expected_art_mime
    assert len(data) == expected_art_len


@pytest.mark.parametrize(
    "sample_filename",
    [
        "sample_01.mp3",
        "sample_02.m4a",
        "sample_03.aiff",
    ],
)
def test_edit_and_save_sample_tags(sample_filename: str, tmp_path: Path) -> None:
    """Test editing all metadata tags and saving to a new file using common editor interface."""
    sample_path = SAMPLE_DIR / sample_filename
    assert sample_path.exists(), f"Sample file not found: {sample_path}"
    output_path = tmp_path / f"edited_{sample_filename}"

    editor = get_tag_editor(sample_path)
    editor.edit_title("新しいタイトル")
    editor.edit_artist("新しいアーティスト")
    editor.edit_album("新しいアルバム")
    editor.edit_year("2026")
    editor.edit_genre("Podcast")
    editor.edit_track_number("3/12")
    editor.edit_disk_number("1/1")
    editor.edit_lyrics("更新された歌詞です。")

    dummy_art = b64encode("image/png", b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR")
    editor.edit_album_art(dummy_art)

    editor.save_to_file(output_path, overwrite=True)
    assert output_path.exists()

    updated_tags = read_tags(output_path)
    assert updated_tags.title == "新しいタイトル"
    assert updated_tags.artist == "新しいアーティスト"
    assert updated_tags.album == "新しいアルバム"
    assert updated_tags.year == "2026"
    assert updated_tags.genre == "Podcast"
    assert updated_tags.track_number == "3/12"
    assert updated_tags.disk_number == "1/1"
    assert updated_tags.lyrics == "更新された歌詞です。"
    assert updated_tags.album_art is not None


@pytest.mark.parametrize("sample_filename", ["sample_01.mp3", "sample_03.aiff"])
def test_edit_and_save_untagged_id3_audio(sample_filename: str, tmp_path: Path) -> None:
    """Test that edits to untagged MP3 and AIFF files are saved without changing the source."""
    sample_path = SAMPLE_DIR / sample_filename
    source_path = tmp_path / f"untagged_{sample_filename}"
    output_path = tmp_path / f"edited_{sample_filename}"
    shutil.copyfile(sample_path, source_path)

    audio = MutagenFile(source_path)
    assert audio is not None
    audio.delete()
    assert read_tags(source_path).title is None

    editor = get_tag_editor(source_path)
    editor.edit_title("新しいタイトル")
    editor.save_to_file(output_path)

    assert read_tags(output_path).title == "新しいタイトル"
    assert read_tags(source_path).title is None


@pytest.mark.parametrize(
    "sample_filename",
    [
        "sample_01.mp3",
        "sample_02.m4a",
        "sample_03.aiff",
    ],
)
def test_clear_all_tags(sample_filename: str, tmp_path: Path) -> None:
    """Test clearing all tags and verifying the result."""
    sample_path = SAMPLE_DIR / sample_filename
    assert sample_path.exists()
    output_path = tmp_path / f"cleared_{sample_filename}"

    editor = get_tag_editor(sample_path)
    editor.clear_all_tags()
    editor.save_to_file(output_path, overwrite=True)

    cleared_tags = read_tags(output_path)
    assert cleared_tags.title is None
    assert cleared_tags.artist is None
    assert cleared_tags.album is None


@pytest.mark.parametrize(
    "sample_filename",
    [
        "sample_01.mp3",
        "sample_02.m4a",
        "sample_03.aiff",
    ],
)
def test_clear_individual_tags(sample_filename: str, tmp_path: Path) -> None:
    """Test clearing individual tags."""
    sample_path = SAMPLE_DIR / sample_filename
    assert sample_path.exists()
    output_path = tmp_path / f"cleared_ind_{sample_filename}"

    editor = get_tag_editor(sample_path)
    editor.clear_title()
    editor.clear_artist()
    editor.clear_album()
    editor.clear_year()
    editor.clear_genre()
    editor.clear_disk_number()
    editor.clear_track_number()
    editor.clear_lyrics()
    editor.clear_album_art()
    editor.save_to_file(output_path, overwrite=True)

    tags = read_tags(output_path)
    assert tags.title is None
    assert tags.artist is None
    assert tags.album is None
    assert tags.year is None
    assert tags.genre is None
    assert tags.disk_number is None
    assert tags.track_number is None
    assert tags.lyrics is None
    assert tags.album_art is None


def test_save_overwrite_false(tmp_path: Path) -> None:
    """Test that save_to_file raises FileWriteError when overwrite=False and file exists."""
    sample_path = SAMPLE_DIR / "sample_01.mp3"
    dest_path = tmp_path / "existing.mp3"
    dest_path.touch()

    editor = get_tag_editor(sample_path)
    editor.edit_title("テスト")
    with pytest.raises(FileWriteError):
        editor.save_to_file(dest_path, overwrite=False)


def test_save_to_directory_raises_error(tmp_path: Path) -> None:
    """Test that save_to_file raises FileWriteError when output path is a directory."""
    sample_path = SAMPLE_DIR / "sample_01.mp3"
    editor = get_tag_editor(sample_path)
    with pytest.raises(FileWriteError):
        editor.save_to_file(tmp_path, overwrite=True)


def test_read_errors() -> None:
    """Test error handling for non-existent files or directories."""
    non_existent = SAMPLE_DIR / "non_existent.mp3"
    with pytest.raises(FileReadError):
        _ = read_tags(non_existent)
    with pytest.raises(FileReadError):
        _ = read_tags(SAMPLE_DIR)


def test_unsupported_format(tmp_path: Path) -> None:
    """Test error handling for unsupported or non-audio file formats."""
    dummy_file = tmp_path / "dummy.txt"
    _ = dummy_file.write_text("not an audio file", encoding="utf-8")
    with pytest.raises(UnsupportedAudioFormatError):
        _ = read_tags(dummy_file)
    with pytest.raises(UnsupportedAudioFormatError):
        _ = get_tag_editor(dummy_file)


def test_audio_tag_utilities() -> None:
    """Test base64 encoding and decoding utilities in audio_tag."""
    tag_empty = SimpleAudioTag()
    assert tag_empty.b64decode_album_art() is None

    test_data = b"Hello, Audio Tag!"
    data_uri = b64encode("image/jpeg", test_data)
    assert data_uri.startswith("data:image/jpeg;base64,")

    mime, raw_data = b64decode(data_uri)
    assert mime == "image/jpeg"
    assert raw_data == test_data

    mime_parsed, b64_parsed = parse_base64_encoded_data_uri(data_uri)
    assert mime_parsed == "image/jpeg"
    assert len(b64_parsed) > 0

    with pytest.raises(ValueError):
        _ = parse_base64_encoded_data_uri("invalid_uri")

    with pytest.raises(ValueError):
        _ = b64decode("invalid_uri")
