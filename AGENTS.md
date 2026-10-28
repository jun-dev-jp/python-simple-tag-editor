# python-simple-tag-editor

## Project Overview
This Python library reads and edits tags in MP3, MP4/M4A, and AIFF files using `mutagen`. The package source is in `src/python_simple_tag_editor/`.

## Design Principles and Requirements
1. **Dependencies**:
   - Keep `mutagen` as the only runtime dependency. Add development tools to dependency groups in `pyproject.toml`.
2. **Package and Environment Management**:
   - Use `uv` to manage dependencies and virtual environments, run tests, and invoke development tools.
   - Follow `requires-python` in `pyproject.toml` for the minimum supported Python version (currently **Python 3.12 or later**).
3. **Unified Interface**:
   - Use the common `SimpleAudioTag` data type for read results and the common `SimpleAudioTagEditor` base class for editing.
   - Use `SimpleID3Tag` / `SimpleID3TagEditor` and `SimpleMP4Tag` / `SimpleMP4TagEditor` for format-specific conversion and editing. MP3 and AIFF use the ID3 implementation; MP4/M4A uses the MP4 implementation.
   - The public API consists of `read_tags()` and `get_tag_editor()`. Detect supported formats based on the format identified by mutagen, not solely on the file extension.
4. **Common Tags**:
   - Provide a common attribute and editing API for title, artist, album, year, genre, track number, disk number, lyrics, and album artwork.
   - Represent album artwork as a base64 Data URI and use the shared utilities to encode and decode it.

## Error Handling
1. **Exception Definitions**:
   - Derive library-specific exceptions from `SimpleTagEditorError`. Use the existing `FileReadError`, `FileWriteError`, `UnsupportedAudioFormatError`, `TagReadError`, and `TagWriteError` as appropriate.
2. **Wrapping mutagen Exceptions**:
   - Wrap low-level exceptions raised by mutagen during reads and writes in the appropriate library-specific exception, preserving the original exception as the cause.
3. **Input Validation**:
   - Check that paths exist, refer to regular files, and are readable. Raise `UnsupportedAudioFormatError` for unsupported or unrecognized formats.
   - Use Pyright for static type checking, but do not omit necessary runtime validation, such as checking formats based on mutagen's return value.

## Development and Quality
- **Static Type Checking**: Use Pyright (`uv run pyright`). Strictly adhere to PEP 561 by including `py.typed` and providing type annotations.
- **Docstrings**: All public APIs (modules, classes, functions, and methods) must have Google-style docstrings, including applicable `Args`, `Returns`, and `Raises` sections.
- **Linting and Formatting**: Use `ruff` to maintain code quality and formatting (`uv run ruff check` / `uv run ruff format`).
- **Tests**: Run tests with `uv run pytest`. Add or update tests for related changes.
- **Testing & Token Conservation Policy**:
  - Run tests locally **only on Python 3.14** (`uv run pytest` or targeted tests). Do not test across multiple Python versions (e.g. 3.12, 3.13, 3.15) locally without explicit prior user confirmation.
  - Multi-version and multi-OS matrix testing is delegated to GitHub Actions CI to avoid excessive token consumption.
  - Prefer focused, minimal test runs (e.g. `uv run pytest tests/test_xxx.py -q`) during iterative development.
