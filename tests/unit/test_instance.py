#!/usr/bin/env python3
# coding: utf-8

# distributed under the mit license
# https://opensource.org/licenses/mit-license.php

import pytest
from hdlr.ir.instance import Instance


def test_instance_basic():
    inst = Instance(name="u0", module_name="adder")

    assert inst.name == "u0"
    assert inst.module_name == "adder"
    assert inst.parameters == {}
    assert inst.connections == {}


def test_instance_with_parameters():
    inst = Instance(
        name="u1",
        module_name="fifo",
        parameters={"DEPTH": "16", "WIDTH": "8"},
    )

    assert inst.parameters["DEPTH"] == "16"
    assert inst.parameters["WIDTH"] == "8"


def test_instance_with_connections():
    inst = Instance(
        name="u2",
        module_name="adder",
        connections={"a": "sig_a", "b": "sig_b"},
    )

    assert inst.connections["a"] == "sig_a"
    assert inst.connections["b"] == "sig_b"


def test_instance_to_dict_minimal():
    inst = Instance(name="u0", module_name="adder")

    assert inst.to_dict() == {
        "module": "adder"
    }


def test_instance_to_dict_with_parameters_sorted():
    inst = Instance(
        name="u1",
        module_name="fifo",
        parameters={"WIDTH": "8", "DEPTH": "16"},
    )

    # Doit être trié alphabétiquement
    assert inst.to_dict() == {
        "module": "fifo",
        "parameters": {
            "DEPTH": "16",
            "WIDTH": "8",
        }
    }


def test_instance_to_dict_with_connections_sorted():
    inst = Instance(
        name="u2",
        module_name="adder",
        connections={"b": "sig_b", "a": "sig_a"},
    )

    assert inst.to_dict() == {
        "module": "adder",
        "connections": {
            "a": "sig_a",
            "b": "sig_b",
        }
    }


def test_instance_to_dict_full():
    inst = Instance(
        name="u3",
        module_name="fifo",
        parameters={"WIDTH": "8"},
        connections={"clk": "clk_i"},
    )

    assert inst.to_dict() == {
        "module": "fifo",
        "parameters": {
            "WIDTH": "8"
        },
        "connections": {
            "clk": "clk_i"
        }
    }

