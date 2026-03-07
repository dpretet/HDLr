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
    assert sig.width is None


def test_signal_with_width():
    sig = Signal(name="data", kind="wire", width=("7", "0"))

    assert sig.name == "data"
    assert sig.kind == "wire"
    assert sig.width == ("7", "0")


def test_signal_to_dict_without_width():
    sig = Signal(name="clk", kind="logic")

    d = sig.to_dict()

    assert d == {
        "kind": "logic"
    }


def test_signal_to_dict_with_width():
    sig = Signal(name="data", kind="wire", width=("7", "0"))

    d = sig.to_dict()

    assert d == {
        "kind": "wire",
        "width": {
            "msb": "7",
            "lsb": "0"
        }
    }

