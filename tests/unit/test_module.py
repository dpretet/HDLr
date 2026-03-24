#!/usr/bin/env python3
# coding: utf-8

# distributed under the mit license
# https://opensource.org/licenses/mit-license.php

from hdlr.ir.module import Module
from hdlr.ir.port import Port
from hdlr.ir.parameter import Parameter
from hdlr.ir.instance import Instance
from hdlr.ir.signal import Signal


def test_module_empty():
    m = Module(name="top")

    assert m.name == "top"
    assert m.ports == []
    assert m.parameters == []
    assert m.signals == []
    assert m.instances == []

    assert m.to_dict() == {
        "name": "top",
        "parameters": {},
        "ports": {},
        "signals": {},
        "instances": {},
    }


def test_module_with_ports_sorted():
    m = Module(
        name="top",
        ports=[
            Port(name="b"),
            Port(name="a"),
        ]
    )

    d = m.to_dict()

    assert list(d["ports"].keys()) == ["a", "b"]


def test_module_with_parameters_sorted():
    m = Module(
        name="top",
        parameters=[
            Parameter(name="WIDTH", value_str="8"),
            Parameter(name="DEPTH", value_str="16"),
        ]
    )

    d = m.to_dict()

    assert list(d["parameters"].keys()) == ["DEPTH", "WIDTH"]


def test_module_with_instance():
    inst = Instance(name="u0", module_name="adder")

    m = Module(
        name="top",
        instances=[inst]
    )

    d = m.to_dict()

    assert "u0" in d["instances"]
    assert d["instances"]["u0"]["module"] == "adder"


def test_module_with_signals_sorted():
    m = Module(
        name="top",
        signals=[
            Signal(name="b", kind="wire"),
            Signal(name="a", kind="reg"),
        ]
    )

    d = m.to_dict()

    assert list(d["signals"].keys()) == ["a", "b"]


def test_module_full():
    """Test module with all components"""
    m = Module(
        name="top",
        parameters=[
            Parameter(name="WIDTH", value_str="8"),
        ],
        ports=[
            Port(name="clk", direction="input"),
            Port(name="data", direction="output", width_str=("7", "0")),
        ],
        signals=[
            Signal(name="internal", kind="logic"),
        ],
        instances=[
            Instance(name="u0", module_name="adder"),
        ]
    )

    d = m.to_dict()

    assert d["name"] == "top"
    assert "WIDTH" in d["parameters"]
    assert "clk" in d["ports"]
    assert "data" in d["ports"]
    assert "internal" in d["signals"]
    assert "u0" in d["instances"]


def test_module_equality():
    m1 = Module(name="top", ports=[Port(name="clk")])
    m2 = Module(name="top", ports=[Port(name="clk")])
    m3 = Module(name="other")

    assert m1 == m2
    assert m1 != m3
