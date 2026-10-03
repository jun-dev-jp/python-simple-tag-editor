"""Custom exceptions for python-simple-tag-editor."""

from __future__ import annotations

__all__ = [
    "FileReadError",
    "FileWriteError",
    "InvalidTagValueError",
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


class InvalidTagValueError(SimpleTagEditorError, ValueError):
    """Exception raised when a tag value has an invalid format or value."""


class TagReadError(SimpleTagEditorError, IOError):
    """Exception raised when reading audio metadata fails."""


class TagWriteError(SimpleTagEditorError, IOError):
    """Exception raised when writing or editing audio metadata fails."""
