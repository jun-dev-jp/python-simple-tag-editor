"""Integration and unit tests for reading and editing tags across audio formats (MP3, M4A, AIFF)."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from mutagen import File as MutagenFile
from mutagen import MutagenError
from mutagen.id3 import ID3Tags
from mutagen.mp4 import MP4Tags

from python_simple_tag_editor import (
    SimpleAudioTag,
    SimpleID3Tag,
    SimpleMP4Tag,
    b64decode,
    b64encode,
    get_tag_editor,
    parse_base64_encoded_data_uri,
    read_tags,
)
from python_simple_tag_editor.exceptions import (
    FileReadError,
    FileWriteError,
    InvalidTagValueError,
    TagReadError,
    TagWriteError,
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

    with pytest.raises(InvalidTagValueError):
        _ = parse_base64_encoded_data_uri("invalid_uri")

    with pytest.raises(InvalidTagValueError):
        _ = b64decode("invalid_uri")


@pytest.mark.parametrize(
    "sample_filename",
    [
        "sample_01.mp3",
        "sample_02.m4a",
        "sample_03.aiff",
    ],
)
@pytest.mark.parametrize(
    "invalid_track",
    [
        "not-a-number",
        "0",
        "01",
        "1/0",
        "1/01",
        "0/1",
        "-1",
        "1/",
        "/1",
        "1/2/3",
        " 1 ",
        "",
        "65536",
        "1/65536",
    ],
)
def test_invalid_track_number_rejected(
    sample_filename: str, invalid_track: str
) -> None:
    """Test that invalid track numbers raise InvalidTagValueError and are not saved."""
    sample_path = SAMPLE_DIR / sample_filename
    editor = get_tag_editor(sample_path)
    with pytest.raises(InvalidTagValueError):
        editor.edit_track_number(invalid_track)


@pytest.mark.parametrize(
    "sample_filename",
    [
        "sample_01.mp3",
        "sample_02.m4a",
        "sample_03.aiff",
    ],
)
@pytest.mark.parametrize(
    "invalid_disk",
    [
        "not-a-number",
        "0",
        "01",
        "1/0",
        "1/01",
        "0/1",
        "-1",
        "1/",
        "/1",
        "1/2/3",
        " 1 ",
        "",
        "65536",
        "1/65536",
    ],
)
def test_invalid_disk_number_rejected(sample_filename: str, invalid_disk: str) -> None:
    """Test that invalid disk numbers raise InvalidTagValueError and are not saved."""
    sample_path = SAMPLE_DIR / sample_filename
    editor = get_tag_editor(sample_path)
    with pytest.raises(InvalidTagValueError):
        editor.edit_disk_number(invalid_disk)


@pytest.mark.parametrize(
    "sample_filename",
    [
        "sample_01.mp3",
        "sample_02.m4a",
        "sample_03.aiff",
    ],
)
@pytest.mark.parametrize(
    "invalid_year",
    [
        "not-a-year",
        "202",
        "20261",
        "2026-1",
        "2026-13",
        "2026-00",
        "2026-02-30",
        "2026-invalid",
        "2026abc",
        "",
        " 2026 ",
    ],
)
def test_invalid_year_rejected(sample_filename: str, invalid_year: str) -> None:
    """Test that malformed year/date values raise InvalidTagValueError."""
    sample_path = SAMPLE_DIR / sample_filename
    editor = get_tag_editor(sample_path)
    with pytest.raises(InvalidTagValueError):
        editor.edit_year(invalid_year)


@pytest.mark.parametrize(
    "sample_filename",
    [
        "sample_01.mp3",
        "sample_02.m4a",
        "sample_03.aiff",
    ],
)
@pytest.mark.parametrize(
    ("valid_track", "valid_disk"),
    [
        ("1", "1"),
        ("1/12", "1/2"),
        ("10/10", "2/2"),
    ],
)
def test_valid_track_and_disk_numbers_roundtrip(
    sample_filename: str, valid_track: str, valid_disk: str, tmp_path: Path
) -> None:
    """Test that valid track and disk numbers round-trip consistently across formats."""
    sample_path = SAMPLE_DIR / sample_filename
    output_path = tmp_path / f"edited_{sample_filename}"

    editor = get_tag_editor(sample_path)
    editor.edit_track_number(valid_track)
    editor.edit_disk_number(valid_disk)
    editor.save_to_file(output_path, overwrite=True)

    read_back = read_tags(output_path)
    assert read_back.track_number == valid_track
    assert read_back.disk_number == valid_disk


@pytest.mark.parametrize(
    "sample_filename",
    [
        "sample_01.mp3",
        "sample_02.m4a",
        "sample_03.aiff",
    ],
)
@pytest.mark.parametrize(
    "valid_year",
    [
        "2026",
        "2026-10",
        "2026-10-04",
    ],
)
def test_valid_year_formats_roundtrip(
    sample_filename: str, valid_year: str, tmp_path: Path
) -> None:
    """Test that valid year/date formats round-trip consistently across formats."""
    sample_path = SAMPLE_DIR / sample_filename
    output_path = tmp_path / f"edited_{sample_filename}"

    editor = get_tag_editor(sample_path)
    editor.edit_year(valid_year)
    editor.save_to_file(output_path, overwrite=True)

    read_back = read_tags(output_path)
    assert read_back.year == valid_year


@pytest.mark.parametrize(
    "sample_filename",
    [
        "sample_01.mp3",
        "sample_02.m4a",
        "sample_03.aiff",
    ],
)
def test_atomic_save_success_and_temp_file_cleanup(
    sample_filename: str, tmp_path: Path
) -> None:
    """Test that successful save atomically replaces destination and leaves no temp files."""
    sample_path = SAMPLE_DIR / sample_filename
    output_path = tmp_path / f"output_{sample_filename}"

    editor = get_tag_editor(sample_path)
    editor.edit_title("Atomic Title")
    editor.save_to_file(output_path, overwrite=True)

    read_back = read_tags(output_path)
    assert read_back.title == "Atomic Title"
    leftover_tmp_files = list(tmp_path.glob(".*.tmp")) + list(tmp_path.glob("*.tmp"))
    assert leftover_tmp_files == []


@pytest.mark.parametrize(
    "sample_filename",
    [
        "sample_01.mp3",
        "sample_02.m4a",
        "sample_03.aiff",
    ],
)
def test_atomic_save_mutagen_failure_preserves_destination_and_cleans_up(
    sample_filename: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test that a Mutagen write failure leaves existing destination and source untouched and cleans up temp files."""
    sample_path = SAMPLE_DIR / sample_filename
    dest_path = tmp_path / f"dest_{sample_filename}"
    original_content = b"ORIGINAL_DESTINATION_CONTENT_THAT_MUST_NOT_CHANGE"
    dest_path.write_bytes(original_content)

    editor = get_tag_editor(sample_path)
    editor.edit_title("New Title That Fails")

    def _failing_save(*_args: object, **_kwargs: object) -> None:
        raise MutagenError("Simulated mutagen save failure")

    monkeypatch.setattr(editor._audio, "save", _failing_save)

    with pytest.raises(TagWriteError) as exc_info:
        editor.save_to_file(dest_path, overwrite=True)

    assert "Simulated mutagen save failure" in str(exc_info.value)
    assert dest_path.read_bytes() == original_content
    leftover_tmp_files = list(tmp_path.glob(".*.tmp")) + list(tmp_path.glob("*.tmp"))
    assert leftover_tmp_files == []


@pytest.mark.parametrize(
    "sample_filename",
    [
        "sample_01.mp3",
        "sample_02.m4a",
        "sample_03.aiff",
    ],
)
def test_atomic_save_mutagen_failure_leaves_nonexistent_destination_absent(
    sample_filename: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test that a failure when saving to a new destination leaves no destination file or temp files."""
    sample_path = SAMPLE_DIR / sample_filename
    dest_path = tmp_path / f"new_{sample_filename}"

    editor = get_tag_editor(sample_path)
    editor.edit_title("New Title")

    def _failing_save(*_args: object, **_kwargs: object) -> None:
        raise MutagenError("Simulated mutagen save failure")

    monkeypatch.setattr(editor._audio, "save", _failing_save)

    with pytest.raises(TagWriteError):
        editor.save_to_file(dest_path, overwrite=True)

    assert not dest_path.exists()
    leftover_tmp_files = list(tmp_path.glob(".*.tmp")) + list(tmp_path.glob("*.tmp"))
    assert leftover_tmp_files == []


@pytest.mark.parametrize(
    "sample_filename",
    [
        "sample_01.mp3",
        "sample_02.m4a",
        "sample_03.aiff",
    ],
)
def test_atomic_save_inplace_failure_preserves_source_audio(
    sample_filename: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test that in-place save failure preserves original source audio file and cleans up temp files."""
    sample_path = SAMPLE_DIR / sample_filename
    in_place_path = tmp_path / f"in_place_{sample_filename}"
    shutil.copyfile(sample_path, in_place_path)
    original_bytes = in_place_path.read_bytes()

    editor = get_tag_editor(in_place_path)
    editor.edit_title("In-place Edit That Fails")

    def _failing_save(*_args: object, **_kwargs: object) -> None:
        raise MutagenError("Simulated in-place save failure")

    monkeypatch.setattr(editor._audio, "save", _failing_save)

    with pytest.raises(TagWriteError):
        editor.save_to_file(in_place_path, overwrite=True)

    assert in_place_path.read_bytes() == original_bytes
    leftover_tmp_files = list(tmp_path.glob(".*.tmp")) + list(tmp_path.glob("*.tmp"))
    assert leftover_tmp_files == []


@pytest.mark.parametrize(
    "sample_filename",
    [
        "sample_01.mp3",
        "sample_02.m4a",
        "sample_03.aiff",
    ],
)
def test_atomic_save_os_error_preserves_destination_and_cleans_up(
    sample_filename: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test that filesystem error during replace preserves destination and cleans up temp files."""
    sample_path = SAMPLE_DIR / sample_filename
    dest_path = tmp_path / f"os_err_{sample_filename}"
    original_content = b"PROTECTED_CONTENT"
    dest_path.write_bytes(original_content)

    editor = get_tag_editor(sample_path)
    editor.edit_title("Title")

    import os

    def _failing_replace(_src: object, _dst: object) -> None:
        raise OSError("Simulated replace filesystem error")

    monkeypatch.setattr(os, "replace", _failing_replace)

    with pytest.raises(FileWriteError):
        editor.save_to_file(dest_path, overwrite=True)

    assert dest_path.read_bytes() == original_content
    leftover_tmp_files = list(tmp_path.glob(".*.tmp")) + list(tmp_path.glob("*.tmp"))
    assert leftover_tmp_files == []


@pytest.mark.parametrize(
    "sample_filename",
    [
        "sample_01.mp3",
        "sample_02.m4a",
        "sample_03.aiff",
    ],
)
@pytest.mark.parametrize(
    "invalid_album_art",
    [
        "not-a-data-uri",
        "data:image/jpeg;base64",
        "data:image/jpeg,notbase64",
        "data:image/jpeg;base64,!!!",
        "data:text/plain;base64,SGVsbG8=",
        "data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7",
        "data:image/webp;base64,UklGRh4AAABXRUJQVlA4TBEAAAAvAAAAAAfQ//73v/+BiOh/AAA=",
        # Mismatched MIME: header is image/jpeg, but payload is PNG
        "data:image/jpeg;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
        # Mismatched MIME: header is image/png, but payload is JPEG
        "data:image/png;base64,/9j/4AAQSkZJRgABAQEASABIAAD/2wBDAP//////////////////////////////////////////////////////////////////////////////////////wgALCAABAAEBAREA/8QAFBABAAAAAAAAAAAAAAAAAAAAAP/aAAgBAQABPxA=",
        # Corrupted payload with invalid base64 padding/characters
        "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEASABIAAD/2wBDAP====",
    ],
)
def test_invalid_album_art_rejected(
    sample_filename: str, invalid_album_art: str
) -> None:
    """Test that malformed Data URIs, invalid base64, unsupported MIME, or mismatched images raise InvalidTagValueError."""
    sample_path = SAMPLE_DIR / sample_filename
    editor = get_tag_editor(sample_path)
    with pytest.raises(InvalidTagValueError):
        editor.edit_album_art(invalid_album_art)


@pytest.mark.parametrize(
    "sample_filename",
    [
        "sample_01.mp3",
        "sample_02.m4a",
        "sample_03.aiff",
    ],
)
@pytest.mark.parametrize(
    ("mime_type", "image_bytes"),
    [
        (
            "image/jpeg",
            # Minimal 1x1 JPEG bytes
            b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.' \",#\x1c\x1c(7),01444\x1f'9=82<.342\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00\xff\xc4\x00\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\xff\xda\x00\x08\x01\x01\x00\x00?\x00\xbf\x00\xff\xd9",
        ),
        (
            "image/png",
            # Minimal 1x1 PNG bytes
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\rIDATx\x9cc`\x00\x00\x00\x02\x00\x01H\xaf\xa4q\x00\x00\x00\x00IEND\xaeB`\x82",
        ),
    ],
)
def test_valid_album_art_roundtrip(
    sample_filename: str, mime_type: str, image_bytes: bytes, tmp_path: Path
) -> None:
    """Test that supported JPEG and PNG artwork round-trips with correct MIME type and bytes across formats."""
    sample_path = SAMPLE_DIR / sample_filename
    output_path = tmp_path / f"art_{sample_filename}"

    data_uri = b64encode(mime_type, image_bytes)
    editor = get_tag_editor(sample_path)
    editor.edit_album_art(data_uri)
    editor.save_to_file(output_path, overwrite=True)

    read_back = read_tags(output_path)
    assert read_back.album_art is not None
    decoded = read_back.b64decode_album_art()
    assert decoded is not None
    read_mime, read_bytes = decoded
    assert read_mime == mime_type
    assert read_bytes == image_bytes


def test_tag_read_error_wraps_mutagen_and_preserves_cause(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that Mutagen errors during ID3/MP4 tag reading are wrapped as TagReadError with cause preserved."""

    def mock_id3_mutagen_error(id3_tags: ID3Tags, tag_name: str) -> str | None:
        raise MutagenError("Simulated Mutagen failure reading ID3")

    monkeypatch.setattr(SimpleID3Tag, "_get_tag", staticmethod(mock_id3_mutagen_error))
    with pytest.raises(TagReadError) as id3_exc_info:
        SimpleID3Tag.from_ID3Tags(ID3Tags())
    assert isinstance(id3_exc_info.value.__cause__, MutagenError)
    assert "Simulated Mutagen failure" in str(id3_exc_info.value.__cause__)

    def mock_mp4_mutagen_error(mp4_tags: MP4Tags, tag_name: str) -> str | None:
        raise MutagenError("Simulated Mutagen failure reading MP4")

    monkeypatch.setattr(SimpleMP4Tag, "_get_tag", staticmethod(mock_mp4_mutagen_error))
    with pytest.raises(TagReadError) as mp4_exc_info:
        SimpleMP4Tag.from_MP4Tags(MP4Tags())
    assert isinstance(mp4_exc_info.value.__cause__, MutagenError)
    assert "Simulated Mutagen failure" in str(mp4_exc_info.value.__cause__)


def test_tag_read_unexpected_error_not_wrapped(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that unexpected programming errors (e.g. TypeError, AttributeError) are not wrapped as TagReadError."""

    def mock_type_error(*args: object, **kwargs: object) -> str | None:
        raise TypeError("Unexpected programming bug")

    monkeypatch.setattr(SimpleID3Tag, "_get_tag", staticmethod(mock_type_error))
    with pytest.raises(TypeError, match="Unexpected programming bug"):
        SimpleID3Tag.from_ID3Tags(ID3Tags())

    monkeypatch.setattr(SimpleMP4Tag, "_get_tag", staticmethod(mock_type_error))
    with pytest.raises(TypeError, match="Unexpected programming bug"):
        SimpleMP4Tag.from_MP4Tags(MP4Tags())


def test_tag_write_error_wraps_mutagen_and_preserves_cause(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Test that Mutagen errors during save_to_file are wrapped as TagWriteError with cause preserved."""
    sample_path = SAMPLE_DIR / "sample_01.mp3"
    editor = get_tag_editor(sample_path)
    output_path = tmp_path / "output.mp3"

    def mock_save_error(path: Path) -> None:
        raise MutagenError("Simulated Mutagen failure saving tags")

    monkeypatch.setattr(editor._audio, "save", mock_save_error)
    with pytest.raises(TagWriteError) as exc_info:
        editor.save_to_file(output_path)
    assert isinstance(exc_info.value.__cause__, MutagenError)
    assert "Simulated Mutagen failure" in str(exc_info.value.__cause__)


def test_tag_write_unexpected_error_not_wrapped(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Test that unexpected errors (e.g. ValueError, TypeError) during save_to_file are not wrapped as TagWriteError."""
    sample_path = SAMPLE_DIR / "sample_01.mp3"
    editor = get_tag_editor(sample_path)
    output_path = tmp_path / "output.mp3"

    def mock_unexpected_error(path: Path) -> None:
        raise RuntimeError("Unexpected runtime bug")

    monkeypatch.setattr(editor._audio, "save", mock_unexpected_error)
    with pytest.raises(RuntimeError, match="Unexpected runtime bug"):
        editor.save_to_file(output_path)
