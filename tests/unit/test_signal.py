#!/usr/bin/env python3
# coding: utf-8

# distributed under the mit license
# https://opensource.org/licenses/mit-license.php

import pytest
from hdlr.ir.signal import Signal


def test_signal_basic():
    sig = Signal(name="clk", kind="logic")

    assert sig.name == "clk"
    assert sig.kind == "logic"
    assert sig.width_str is None
    assert sig.condition is None


def test_signal_with_width():
    sig = Signal(name="data", kind="wire", width_str=("7", "0"))

    assert sig.name == "data"
    assert sig.kind == "wire"
    assert sig.width_str == ("7", "0")


def test_signal_with_width_int():
    sig = Signal(name="addr", kind="reg", width_int=(15, 0))

    assert sig.name == "addr"
    assert sig.kind == "reg"
    assert sig.width_int == (15, 0)


def test_signal_with_condition():
    sig = Signal(name="en", kind="logic", condition="ENABLE_FEATURE")

    assert sig.name == "en"
    assert sig.kind == "logic"
    assert sig.condition == "ENABLE_FEATURE"


def test_signal_to_dict_without_width():
    sig = Signal(name="clk", kind="logic")

    d = sig.to_dict()

    assert d == {
        "kind": "logic"
    }


def test_signal_to_dict_with_width():
    sig = Signal(name="data", kind="wire", width_str=("7", "0"))

    d = sig.to_dict()

    assert d == {
        "kind": "wire",
        "width": {
            "msb": "7",
            "lsb": "0"
        }
    }


def test_signal_to_dict_with_width_int():
    sig = Signal(name="addr", kind="reg", width_int=(15, 0))

    d = sig.to_dict()

    assert d == {
        "kind": "reg",
        "width": {
            "msb": 15,
            "lsb": 0
        }
    }


def test_signal_to_dict_with_condition():
    sig = Signal(name="en", kind="logic", condition="ENABLE_FEATURE")

    d = sig.to_dict()

    assert d == {
        "kind": "logic"
    }
    # Condition is not included in to_dict() output


def test_signal_to_dict_width_int_priority():
    sig = Signal(name="data", kind="wire", width_str=("7", "0"), width_int=(15, 0))

    d = sig.to_dict()

    assert d == {
        "kind": "wire",
        "width": {
            "msb": 15,
            "lsb": 0
        }
    }


def test_signal_equality():
    sig1 = Signal(name="clk", kind="logic")
    sig2 = Signal(name="clk", kind="logic")
    sig3 = Signal(name="rst", kind="logic")

    assert sig1 == sig2
    assert sig1 != sig3


# ✅ Test edge case: seulement width_int sans width_str
def test_signal_to_dict_only_width_int():
    """Test the edge case where only width_int is set (not width_str)"""
    sig = Signal(name="addr", kind="reg", width_int=(31, 0))

    d = sig.to_dict()

    assert d == {
        "kind": "reg",
        "width": {
            "msb": 31,
            "lsb": 0
        }
    }

