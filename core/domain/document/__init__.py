"""Compatibility document package for historical imports."""

from core.domain.document.reader import DocumentReader, clean_text
from core.domain.document.docx_codec import (
    export_raw_to_docx,
    export_script_to_docx,
    parse_raw_from_docx,
)

__all__ = [
    "DocumentReader",
    "clean_text",
    "export_raw_to_docx",
    "export_script_to_docx",
    "parse_raw_from_docx",
]

