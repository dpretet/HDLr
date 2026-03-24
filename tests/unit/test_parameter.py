#!/usr/bin/env python3
# coding: utf-8

# distributed under the mit license
# https://opensource.org/licenses/mit-license.php

import pytest
from hdlr.ir.parameter import Parameter


def test_parameter_basic():
    p = Parameter(name="WIDTH", value_str="8")

    assert p.name == "WIDTH"
    assert p.value_str == "8"
    assert p.value_int is None


def test_parameter_with_int_value():
    p = Parameter(name="DEPTH", value_int=256)

    assert p.name == "DEPTH"
    assert p.value_int == 256
    assert p.value_str is None


def test_parameter_to_dict_with_str():
    p = Parameter(name="WIDTH", value_str="8")

    assert p.to_dict() == {
        "name": "WIDTH",
        "value": "8"
    }


def test_parameter_to_dict_with_int():
    p = Parameter(name="DEPTH", value_int=256)

    assert p.to_dict() == {
        "name": "DEPTH",
        "value": 256
    }


def test_parameter_to_dict_with_both_priority():
    """When both value_str and value_int are set, value_int should have priority"""
    p = Parameter(name="WIDTH", value_str="8", value_int=16)

    assert p.to_dict() == {
        "name": "WIDTH",
        "value": 16
    }


def test_parameter_equality():
    p1 = Parameter(name="WIDTH", value_str="8")
    p2 = Parameter(name="WIDTH", value_str="8")
    p3 = Parameter(name="DEPTH", value_str="8")

    assert p1 == p2
    assert p1 != p3
