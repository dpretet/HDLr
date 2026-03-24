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
    assert p.width_str is None


# ✅ Avec direction
def test_port_with_direction():
    p = Port(name="rst", direction="input")

    assert p.name == "rst"
    assert p.direction == "input"
    assert p.width_str is None


# ✅ Avec width
def test_port_with_width():
    p = Port(name="data", width_str=("7", "0"))

    assert p.name == "data"
    assert p.width_str == ("7", "0")


# ✅ Avec width_int
def test_port_with_width_int():
    p = Port(name="addr", width_int=(15, 0))

    assert p.name == "addr"
    assert p.width_int == (15, 0)


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
    p = Port(name="data", width_str=("7", "0"))

    assert p.to_dict() == {
        "width": {
            "msb": "7",
            "lsb": "0"
        }
    }


# ✅ to_dict avec width_int
def test_port_to_dict_width_int():
    p = Port(name="addr", width_int=(15, 0))

    assert p.to_dict() == {
        "width": {
            "msb": 15,
            "lsb": 0
        }
    }


# ✅ to_dict complet
def test_port_to_dict_full():
    p = Port(name="data", direction="output", width_str=("15", "8"))

    assert p.to_dict() == {
        "direction": "output",
        "width": {
            "msb": "15",
            "lsb": "8"
        }
    }


# ✅ to_dict avec width_int et width_str (width_int prioritaire)
def test_port_to_dict_width_int_priority():
    p = Port(name="data", width_str=("7", "0"), width_int=(15, 0))

    assert p.to_dict() == {
        "width": {
            "msb": 15,
            "lsb": 0
        }
    }


# ✅ Test d'égalité
def test_port_equality():
    p1 = Port(name="clk", direction="input")
    p2 = Port(name="clk", direction="input")
    p3 = Port(name="rst", direction="input")

    assert p1 == p2
    assert p1 != p3


# ✅ Test edge case: seulement width_int sans width_str
def test_port_to_dict_only_width_int():
    """Test the edge case where only width_int is set (not width_str)"""
    p = Port(name="addr", width_int=(31, 0))

    assert p.to_dict() == {
        "width": {
            "msb": 31,
            "lsb": 0
        }
    }
