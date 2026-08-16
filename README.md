# python-simple-tag-editor

A lightweight, robust, and format-agnostic audio metadata library for Python built on top of `mutagen`.

It provides a unified, intuitive API to read and edit metadata tags across **MP3**, **MP4/M4A**, and **AIFF** audio files without needing to know format-specific tagging internals (such as ID3 frames vs. MP4 atoms).

---

## Features

- **Unified Interface**: One consistent API for MP3, MP4 (M4A/AAC), and AIFF files.
- **Common Metadata Tags**:
  - Title (`title`)
  - Artist (`artist`)
  - Album (`album`)
  - Year (`year`)
  - Genre (`genre`)
  - Track Number (`track_number`, e.g. `"1"` or `"1/12"`)
  - Disk Number (`disk_number`, e.g. `"1"` or `"1/2"`)
  - Lyrics (`lyrics`)
  - Album Artwork (`album_art` as base64 Data URI, with helper for decoding/encoding)
- **Safe Error Handling**: Wraps low-level format and I/O errors into structured library exceptions.
- **Type Annotated**: Fully typed with `py.typed` marker for static type checkers (Pyright, Mypy).

---

## Installation & Setup

### Install from GitHub

```bash
# Using uv
uv add git+https://github.com/junpiyo/python-simple-tag-editor.git

# Or using pip
pip install git+https://github.com/junpiyo/python-simple-tag-editor.git
```

### Local Development Setup

```bash
# Clone the repository
git clone https://github.com/junpiyo/python-simple-tag-editor.git
cd python-simple-tag-editor

# Set up virtual environment and install dependencies with uv
uv sync
```

---

## Quickstart

### 1. Reading Metadata

```python
from python_simple_tag_editor import read_tags

# Read tags from any supported audio file
tags = read_tags("song.mp3")

print("Title       :", tags.title)
print("Artist      :", tags.artist)
print("Album       :", tags.album)
print("Year        :", tags.year)
print("Genre       :", tags.genre)
print("Track Number:", tags.track_number)
print("Disk Number :", tags.disk_number)
print("Lyrics      :", tags.lyrics)

# Extract album artwork
if tags.album_art:
    decoded = tags.b64decode_album_art()
    if decoded:
        mime, image_data = decoded
        print(f"Artwork: {mime}, {len(image_data)} bytes")
```

### 2. Editing Metadata

```python
from python_simple_tag_editor import get_tag_editor, b64encode

# Obtain an editor for the file
editor = get_tag_editor("input.m4a")

# Update tags
editor.edit_title("New Title")
editor.edit_artist("New Artist")
editor.edit_album("New Album")
editor.edit_year("2026")
editor.edit_genre("Pop")
editor.edit_track_number("1/10")
editor.edit_disk_number("1/1")
editor.edit_lyrics("These are the lyrics.")

# Set album art from an image file
with open("cover.jpg", "rb") as f:
    art_uri = b64encode("image/jpeg", f.read())
    editor.edit_album_art(art_uri)

# Save changes to a new file (or overwrite)
editor.save_to_file("output.m4a", overwrite=True)
```

### 3. Clearing Tags

```python
editor = get_tag_editor("song.aiff")

# Clear specific tags
editor.clear_lyrics()
editor.clear_album_art()

# Or clear all tags
editor.clear_all_tags()

editor.save_to_file("song_cleaned.aiff", overwrite=True)
```

---

## Exception Hierarchy

All custom exceptions inherit from `SimpleTagEditorError`:

```text
SimpleTagEditorError
 ├── FileReadError (IOError)
 ├── FileWriteError (IOError)
 ├── UnsupportedAudioFormatError (ValueError)
 ├── TagReadError (IOError)
 └── TagWriteError (IOError)
```

---

## Development & Testing

```bash
# Run linter
uv run ruff check

# Run formatter check
uv run ruff format --check

# Run test suite
uv run pytest
```

---

## License

MIT License. See [LICENSE](LICENSE) for details.
