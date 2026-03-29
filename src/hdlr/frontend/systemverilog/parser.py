#!/usr/bin/env python3
# coding: utf-8

# distributed under the mit license
# https://opensource.org/licenses/mit-license.php

"""
SystemVerilog parser using tree-sitter.

This module provides parsing functionality for SystemVerilog files using
the tree-sitter SystemVerilog grammar. It converts source code to AST
and then builds the HDLr IR.
"""

import tree_sitter_systemverilog
from tree_sitter import Language, Parser
from pathlib import Path
from .ir_builder import SystemVerilogIRBuilder


# Initialize SystemVerilog language and parser
SYSTEMVERILOG_LANGUAGE = Language(tree_sitter_systemverilog.language())
parser = Parser(SYSTEMVERILOG_LANGUAGE)


def parse(input_data):
    """Parse SystemVerilog source and return IR modules.

    Args:
        input_data: Either a Path object or string containing SystemVerilog source

    Returns:
        List of Module objects extracted from the source
    """
    if isinstance(input_data, Path):
        source = input_data.read_text()
    else:
        source = input_data

    tree = parser.parse(source.encode("utf8"))
    builder = SystemVerilogIRBuilder()
    modules = builder.build(tree)

    return modules
