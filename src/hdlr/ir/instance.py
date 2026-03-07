#!/usr/bin/env python3
# coding: utf-8

# distributed under the mit license
# https://opensource.org/licenses/mit-license.php

from dataclasses import dataclass, field

@dataclass
class Instance:
    name: str
    module_name: str
    parameters: dict[str, str] = field(default_factory=dict)
    connections: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict:
        data = {
            "module": self.module_name,
        }

        if self.parameters:
            data["parameters"] = dict(sorted(self.parameters.items()))

        if self.connections:
            data["connections"] = dict(sorted(self.connections.items()))

        return data
