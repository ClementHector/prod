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
        # Handle Windows drive letters (C:\) by temporarily replacing colons in them
        temp_path = self.path_string

        # Find all potential drive letters (e.g., C:\ or D:/)
        i = 0
        while i < len(temp_path) - 2:
            # Check if current position is a Windows drive letter (e.g., C:\)
            is_drive_letter = (
                temp_path[i].isalpha()
                and temp_path[i + 1] == ":"
                and (temp_path[i + 2] == "\\" or temp_path[i + 2] == "/")
            )

            if is_drive_letter:
                # Replace C: with C@ to avoid splitting on drive letter colons
                temp_path = temp_path[: i + 1] + "@" + temp_path[i + 2 :]
            i += 1

        # Now split by colons
        parts = temp_path.split(":")

        # Process and restore the original paths
        result = []
        for part in parts:
            if "@" in part:
                # Restore the colon in the drive letter
                fixed_part = part.replace("@", ":")
                result.append(fixed_part)
            else:
                if part:  # Skip empty parts
                    result.append(part)

        # If we didn't split anything, just use the original path
        if not result and self.path_string:
            result = [self.path_string]

        return result
