#!/usr/bin/env python3
# coding: utf-8

# distributed under the mit license
# https://opensource.org/licenses/mit-license.php

from hdlr.frontend.systemverilog.parser import parse as parse_systemverilog
from hdlr.frontend.verilog.parser import parse as parse_verilog
from hdlr.frontend.vhdl.parser import parse as parse_vhdl


class VerilogFrontend:
    name = "verilog"
    def parse_file(self, path: str):
        return parse_verilog(path)

class SystemVerilogFrontend:
    name = "systemverilog"
    def parse_file(self, path: str):
        return parse_systemverilog(path)

class VhdlFrontend:
    name = "vhdl"
    def parse_file(self, path: str):
        return parse_vhdl(path)



_FRONTENDS = {
    "verilog": VerilogFrontend(),
    "systemverilog": SystemVerilogFrontend(),
    "vhdl": VhdlFrontend(),
}


def get_frontend(name: str):
    if name not in _FRONTENDS:
        raise ValueError(f"Unsupported language: {name}")
    return _FRONTENDS[name]
