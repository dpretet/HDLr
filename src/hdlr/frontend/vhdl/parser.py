#!/usr/bin/env python3
# coding: utf-8

# distributed under the mit license
# https://opensource.org/licenses/mit-license.php

"""
VHDL parser using tree-sitter.

This module provides parsing functionality for VHDL files using
the tree-sitter VHDL grammar. It converts source code to AST
and then builds the HDLr IR.
"""

import tree_sitter_vhdl
from tree_sitter import Language, Parser
from pathlib import Path
from .ir_builder import VhdlIRBuilder


# Initialize VHDL language and parser
VHDL_LANGUAGE = Language(tree_sitter_vhdl.language())
parser = Parser(VHDL_LANGUAGE)


def parse(input_data):
    """Parse VHDL source and return IR modules.
    
    Args:
        input_data: Either a Path object or string containing VHDL source
        
    Returns:
        List of Module objects extracted from the source
    """
    if isinstance(input_data, Path):
        source = input_data.read_text()
    else:
        source = input_data

    tree = parser.parse(source.encode("utf8"))
    builder = VhdlIRBuilder()
    modules = builder.build(tree)
    
    return modules