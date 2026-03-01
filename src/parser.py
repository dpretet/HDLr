#!/usr/bin/env python3
# coding: utf-8

# distributed under the mit license
# https://opensource.org/licenses/mit-license.php

"""
The HDL Parser of the project, manipulating HDLParse
"""

from hdlparse.verilog_parser import parse_verilog_file, VerilogObject, VerilogParameter
from hdlparse.vhdl_parser import parse_vhdl_file, VhdlObject, VhdlParameter
from hdlparse.minilexer import MiniLexer

def main():

    objects = parse_verilog_file("test.v")
    for obj in objects:
        print(obj.__dict__)

    objects = parse_verilog_file("test.sv")
    for obj in objects:
        print(obj.__dict__)

if __name__ == "__main__":
    main()
