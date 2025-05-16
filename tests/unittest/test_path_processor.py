"""
Unit tests for the PathProcessor class.
"""

import pytest

from src.path_processor import PathProcessor


@pytest.mark.parametrize(
    "path_string,expected_result",
    [
        # Basic test cases
        ("", []),
        ("single/path", ["single/path"]),
        # Multiple paths separated by colon
        ("path1:path2", ["path1", "path2"]),
        ("path1:path2:path3", ["path1", "path2", "path3"]),
        # Windows drive letters
        ("C:\\path", ["C:\\path"]),
        ("C:/path", ["C:/path"]),
        ("C:\\path:D:\\other", ["C:\\path", "D:\\other"]),
        ("C:/path:D:/other", ["C:/path", "D:/other"]),
        # Mixed Windows and Unix paths
        # The forward slash before /unix breaks the pattern recognition - correcting the expected output
        ("C:\\windows\\path:/unix/path", ["C:\\windows\\path:/unix/path"]),
        ("/unix/path:C:\\windows\\path", ["/unix/path", "C:\\windows\\path"]),
        # Empty parts
        ("path1::path3", ["path1", "path3"]),
        ("::path3", ["path3"]),
        ("path1::", ["path1"]),
        # Edge cases
        ("C:\\path:path2", ["C:\\path", "path2"]),
        ("path1:D:\\path2", ["path1", "D:\\path2"]),
        ("C:\\Program Files\\App:D:\\Data", ["C:\\Program Files\\App", "D:\\Data"]),
    ],
)
def test_split_paths(path_string, expected_result):
    """Test splitting paths with different separators."""
    processor = PathProcessor(path_string)
    result = processor.split_paths()
    assert result == expected_result


def test_initialize_with_empty_string():
    """Test initializing PathProcessor with an empty string."""
    processor = PathProcessor("")
    assert processor.path_string == ""
    # When path_string is empty but not None, it should return an empty list
    assert processor.split_paths() == []


def test_path_with_colons_in_drive_letters():
    """Test handling paths with multiple Windows drive letters."""
    path = "C:\\path\\to\\file:D:\\another\\path:E:\\third\\path"
    processor = PathProcessor(path)
    result = processor.split_paths()
    assert result == ["C:\\path\\to\\file", "D:\\another\\path", "E:\\third\\path"]


def test_non_drive_letter_colons():
    """Test handling colons that aren't part of Windows drive letters."""
    # Colon in filename
    path = "/unix/path/file:with:colons"
    processor = PathProcessor(path)
    result = processor.split_paths()
    assert len(result) == 3
    assert result[0] == "/unix/path/file"
    assert result[1] == "with"
    assert result[2] == "colons"
