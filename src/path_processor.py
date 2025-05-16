"""
Path processing utilities.
"""

from typing import List


class PathProcessor:
    """
    Utility class for processing file paths with different separators.
    """

    def __init__(self, path_string: str):
        """
        Initialize the path processor.

        Args:
            path_string: The path string to process
        """
        self.path_string = path_string

    def split_paths(self) -> List[str]:
        """
        Split a path string by colon, preserving Windows drive letters.

        Returns:
            List of path strings
        """
        temp_path = self.path_string

        i = 0
        while i < len(temp_path) - 2:
            is_drive_letter = (
                temp_path[i].isalpha()
                and temp_path[i + 1] == ":"
                and (temp_path[i + 2] == "\\" or temp_path[i + 2] == "/")
            )

            if is_drive_letter:
                temp_path = temp_path[: i + 1] + "@" + temp_path[i + 2:]
            i += 1

        parts = temp_path.split(":")

        result = []
        for part in parts:
            if "@" in part:
                result.append(part.replace("@", ":"))
            elif part:
                result.append(part)

        if not result and self.path_string:
            result = [self.path_string]

        return result
