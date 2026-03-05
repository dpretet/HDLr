#!/usr/bin/env python3
# coding: utf-8

# distributed under the mit license
# https://opensource.org/licenses/mit-license.php

from dataclasses import dataclass, field

@dataclass
class Module:
    name: str
    ports: list = field(default_factory=list)
    parameters: list = field(default_factory=list)
    signals: list = field(default_factory=list)
    instances: list = field(default_factory=list)
