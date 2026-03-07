#!/usr/bin/env python3
# coding: utf-8

# distributed under the mit license
# https://opensource.org/licenses/mit-license.php

"""
Doc string to describe the module
"""

import pytest
from hdlr.ir.port import Port


# ✅ Construction minimale
def test_port_minimal():
    p = Port(name="clk")

    assert p.name == "clk"
    assert p.direction is None
    assert p.width is None


# ✅ Avec direction
def test_port_with_direction():
    p = Port(name="rst", direction="input")

    assert p.name == "rst"
    assert p.direction == "input"
    assert p.width is None


# ✅ Avec width
def test_port_with_width():
    p = Port(name="data", width=("7", "0"))

    assert p.name == "data"
    assert p.width == ("7", "0")


# ✅ to_dict sans rien
def test_port_to_dict_empty():
    p = Port(name="clk")

    assert p.to_dict() == {}


# ✅ to_dict avec direction
def test_port_to_dict_direction():
    p = Port(name="rst", direction="input")

    assert p.to_dict() == {
        "direction": "input"
    }


# ✅ to_dict avec width
def test_port_to_dict_width():
    p = Port(name="data", width=("7", "0"))

    assert p.to_dict() == {
        "width": {
            "msb": "7",
            "lsb": "0"
        }
    }


# ✅ to_dict complet
def test_port_to_dict_full():
    p = Port(name="data", direction="output", width=("15", "8"))

    assert p.to_dict() == {
        "direction": "output",
        "width": {
            "msb": "15",
            "lsb": "8"
        }
    }
