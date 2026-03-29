#!/usr/bin/env python3
# coding: utf-8

# distributed under the mit license
# https://opensource.org/licenses/mit-license.php

"""
Verilog parser using tree-sitter.

This module provides parsing functionality for Verilog files using
the tree-sitter Verilog grammar. It converts source code to AST
and then builds the HDLr IR.
"""

import tree_sitter_verilog
from tree_sitter import Language, Parser
from pathlib import Path
from .ir_builder import VerilogIRBuilder


# Initialize Verilog language and parser
VERILOG_LANGUAGE = Language(tree_sitter_verilog.language())
parser = Parser(VERILOG_LANGUAGE)


def parse(input_data):
    """Parse Verilog source and return IR modules.

    Args:
        input_data: Either a Path object or string containing Verilog source

    Returns:
        List of Module objects extracted from the source
    """
    if isinstance(input_data, Path):
        source = input_data.read_text()
    else:
        source = input_data

    tree = parser.parse(source.encode("utf8"))
    builder = VerilogIRBuilder()
    modules = builder.build(tree)

    return modules
