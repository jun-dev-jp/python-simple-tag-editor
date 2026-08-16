"""Custom exceptions for python-simple-tag-editor."""

from __future__ import annotations

__all__ = [
    "FileReadError",
    "FileWriteError",
    "SimpleTagEditorError",
    "TagReadError",
    "TagWriteError",
    "UnsupportedAudioFormatError",
]


class SimpleTagEditorError(Exception):
    """Base exception class for all errors in python-simple-tag-editor."""


class FileReadError(SimpleTagEditorError, IOError):
    """Exception raised when reading audio file fails."""


class FileWriteError(SimpleTagEditorError, IOError):
    """Exception raised when writing audio file fails."""


class UnsupportedAudioFormatError(SimpleTagEditorError, ValueError):
    """Exception raised when an unsupported or unparseable audio format is specified."""


class TagReadError(SimpleTagEditorError, IOError):
    """Exception raised when reading audio metadata fails."""


class TagWriteError(SimpleTagEditorError, IOError):
    """Exception raised when writing or editing audio metadata fails."""
