#!/usr/bin/env python3
# coding: utf-8

# distributed under the mit license
# https://opensource.org/licenses/mit-license.php

from .verilog.parser import VerilogParser
from .systemverilog.parser import SystemVerilogParser

def get_frontend(file):
    if file.suffix == ".v":
        return VerilogParser()
    elif file.suffix == ".sv":
        return SystemVerilogParser()
    else:
        raise ValueError(f"Unsupported file type {file}")
