#!/usr/bin/env python3
# coding: utf-8

# distributed under the mit license
# https://opensource.org/licenses/mit-license.php

from hdlr.ir.module import Module
from hdlr.ir.port import Port
from hdlr.ir.parameter import Parameter
from hdlr.ir.instance import Instance


def test_module_empty():
    m = Module(name="top")

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
            Parameter(name="WIDTH", value="8"),
            Parameter(name="DEPTH", value="16"),
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
