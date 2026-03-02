"""Compatibility wrapper for ``core.domain.docx_transform``."""

from core.domain.docx_transform import (
    export_raw_to_docx,
    export_script_to_docx,
    parse_raw_from_docx,
)

__all__ = [
    "export_raw_to_docx",
    "export_script_to_docx",
    "parse_raw_from_docx",
]

