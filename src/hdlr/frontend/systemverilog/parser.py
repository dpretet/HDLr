#!/usr/bin/env python3
# coding: utf-8

# distributed under the mit license
# https://opensource.org/licenses/mit-license.php

import tree_sitter_systemverilog
from tree_sitter import Language, Parser
from pathlib import Path
from .ir_builder import SystemVerilogIRBuilder


SYSTEMVERILOG_LANGUAGE = Language(tree_sitter_systemverilog.language())
parser = Parser(SYSTEMVERILOG_LANGUAGE)

def parse(input_data):
    if isinstance(input_data, Path):
        source = input_data.read_text()
    else:
        source = input_data

    tree = parser.parse(source.encode("utf8"))
    builder = SystemVerilogIRBuilder()
    modules = builder.build(tree)

    return modules
