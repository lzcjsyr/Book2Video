"""CLI exports for project and input discovery.

Discovery belongs to the pipeline scanner; these aliases preserve the public
CLI import paths without maintaining a second implementation.
"""

from core.pipeline.scanner import scan_input_files, scan_output_projects

__all__ = ["scan_input_files", "scan_output_projects"]
