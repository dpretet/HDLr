#!/usr/bin/env python3
# coding: utf-8

# distributed under the mit license
# https://opensource.org/licenses/mit-license.php

"""
Module representation for HDLr Intermediate Representation (IR).

This module defines the Module class which represents a hardware module
with its ports, parameters, signals, and instances.
"""

from dataclasses import dataclass, field


@dataclass
class Module:
    """Represents a hardware module in the IR.
    
    Attributes:
        name: Module name
        ports: List of port objects
        parameters: List of parameter objects
        signals: List of signal objects
        instances: List of instance objects
    """
    name: str
    ports: list = field(default_factory=list)
    parameters: list = field(default_factory=list)
    signals: list = field(default_factory=list)
    instances: list = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert module to dictionary representation.
        
        Returns:
            Dictionary with module name and sorted collections of
            parameters, ports, signals, and instances
        """
        return {
            "name": self.name,
            "parameters": {
                p.name: p.to_dict()
                for p in sorted(self.parameters, key=lambda x: x.name)
            } if self.parameters else {},

            "ports": {
                p.name: p.to_dict()
                for p in sorted(self.ports, key=lambda x: x.name)
            } if self.ports else {},

            "signals": {
                s.name: s.to_dict()
                for s in sorted(self.signals, key=lambda x: x.name)
            } if self.signals else {},

            "instances": {
                i.name: i.to_dict()
                for i in sorted(self.instances, key=lambda x: x.name)
            } if self.instances else {}

        }
