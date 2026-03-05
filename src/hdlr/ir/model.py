#!/usr/bin/env python3
# coding: utf-8

# distributed under the mit license
# https://opensource.org/licenses/mit-license.php

"""
Language-agnostic Intermediate Representation (IR).

This IR must NOT depend on tree-sitter or any specific HDL.
It is shared between Verilog, SystemVerilog and future VHDL frontends.
"""

from dataclasses import dataclass, field
from typing import List, Optional


# ---------------------------------------------------------
# Parameters
# ---------------------------------------------------------

@dataclass
class Parameter:
    name: str
    value: Optional[str] = None


# ---------------------------------------------------------
# Ports
# ---------------------------------------------------------

@dataclass
class Port:
    name: str
    direction: Optional[str] = None
    width: Optional[str] = None


# ---------------------------------------------------------
# Signals
# ---------------------------------------------------------

@dataclass
class Signal:
    name: str
    kind: str                         # wire, reg, logic, bit, etc.
    width: Optional[str] = None
    clock: Optional[str] = None       # Future clock domain resolution
    reset: Optional[str] = None       # Future reset tracking
    drivers: List[str] = field(default_factory=list)


# ---------------------------------------------------------
# Instances
# ---------------------------------------------------------

@dataclass
class Instance:
    name: str
    module_name: str
    parameters: List[Parameter] = field(default_factory=list)
    connections: List[Port] = field(default_factory=list)


# ---------------------------------------------------------
# Module
# ---------------------------------------------------------

@dataclass
class Module:
    name: str
    parameters: List[Parameter] = field(default_factory=list)
    ports: List[Port] = field(default_factory=list)
    signals: List[Signal] = field(default_factory=list)
    instances: List[Instance] = field(default_factory=list)
