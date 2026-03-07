#!/usr/bin/env python3
# coding: utf-8

# distributed under the mit license
# https://opensource.org/licenses/mit-license.php

from dataclasses import dataclass

@dataclass
class Parameter:
    name: str
    value: str

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "value": self.value
        }
