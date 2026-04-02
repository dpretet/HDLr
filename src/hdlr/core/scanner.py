#!/usr/bin/env python3
# coding: utf-8

# distributed under the mit license
# https://opensource.org/licenses/mit-license.php

"""
File and directory scanner for HDL source files.

This module provides functionality to recursively scan directories
and collect SystemVerilog/Verilog/VHDL files for processing.
"""

from pathlib import Path


def collect_files(inputs):
    """Collect SystemVerilog and Verilog files from input paths.

    Args:
        inputs: List of file/directory paths to scan

    Returns:
        List of Path objects for all found .v and .sv files
    """
    files = []

    for item in inputs:
        p = Path(item)

        if p.is_file():
            files.append(p)

        elif p.is_dir():
            for ext in ("*.v", "*.sv", "*.vhd"):
                files.extend(p.rglob(ext))

    return files
