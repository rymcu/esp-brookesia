"""Local wrapper for esp-docs run_doxygen with Windows path normalization.

esp-docs computes duplicate-header XML names from relative paths. On Windows
``os.path.relpath`` returns backslashes, but the upstream helper only encodes
forward slashes when mapping header names to Doxygen XML filenames. That makes
Sphinx look for nested ``xml/.../...`` paths that do not exist.
"""

from __future__ import annotations

from esp_docs.esp_extensions import run_doxygen as _run_doxygen

_orig_header_to_xml_path = _run_doxygen.header_to_xml_path


def header_to_xml_path(header_file, xml_directory_path):
    return _orig_header_to_xml_path(header_file.replace("\\", "/"), xml_directory_path)


_run_doxygen.header_to_xml_path = header_to_xml_path
setup = _run_doxygen.setup
