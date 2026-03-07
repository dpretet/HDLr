#!/usr/bin/env python3
# coding: utf-8

# distributed under the mit license
# https://opensource.org/licenses/mit-license.php

import pytest
from hdlr.ir.parameter import Parameter


def test_parameter_basic():
    p = Parameter(name="WIDTH", value="8")

    assert p.name == "WIDTH"
    assert p.value == "8"


def test_parameter_to_dict():
    p = Parameter(name="DEPTH", value="256")

    assert p.to_dict() == {
        "name": "DEPTH",
        "value": "256"
    }
