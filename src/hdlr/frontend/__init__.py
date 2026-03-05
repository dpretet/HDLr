#!/usr/bin/env python3
# coding: utf-8

# distributed under the mit license
# https://opensource.org/licenses/mit-license.php

from hdlr.frontend.verilog.parser import parse as parse_verilog

class VerilogFrontend:
    name = "verilog"

    def parse_file(self, path: str):
        return parse_verilog(path)


_FRONTENDS = {
    "verilog": VerilogFrontend(),
}


def get_frontend(name: str):
    if name not in _FRONTENDS:
        raise ValueError(f"Unsupported language: {name}")
    return _FRONTENDS[name]

