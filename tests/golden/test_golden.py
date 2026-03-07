#!/usr/bin/env python3
# coding: utf-8

# distributed under the mit license
# https://opensource.org/licenses/mit-license.php

"""
Doc string to describe the module
"""

import json
from pathlib import Path

from ir.module import Module
from ir.port import Port


def load_ref(name):
    path = Path(__file__).parent / "refs" / name
    return json.loads(path.read_text())


def test_simple_module_golden():
    m = Module(name="simple")
    m.ports.append(Port("clk", "input"))

    result = m.to_dict()

    assert result == load_ref("simple_module.json")
