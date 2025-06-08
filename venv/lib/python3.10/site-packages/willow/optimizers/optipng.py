from typing import ClassVar

from .base import OptimizerBase

__all__ = ["Optipng"]


class Optipng(OptimizerBase):
    """https://optipng.sourceforge.net/"""

    library_name: ClassVar[str] = "optipng"
    image_format: ClassVar[str] = "png"

    @classmethod
    def get_command_arguments(cls, file_path: str) -> list[str]:
        return [
            "-quiet",
            "-o2",  # optimization level 2 (out of 7)
            "-i0",  # non-interlaced, progressive scanned image
            file_path,  # the file
        ]
