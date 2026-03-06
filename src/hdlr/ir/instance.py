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
