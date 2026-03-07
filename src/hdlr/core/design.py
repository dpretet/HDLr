#!/usr/bin/env python3
# coding: utf-8

# distributed under the mit license
# https://opensource.org/licenses/mit-license.php

"""
The design representation based in the IR
"""

class Design:
    def __init__(self):
        self.modules = {}

    def add_module(self, module):
        if module.name in self.modules:
            raise ValueError(f"Duplicate module {module.name}")
        self.modules[module.name] = module

    def get(self, name):
        return self.modules.get(name)
