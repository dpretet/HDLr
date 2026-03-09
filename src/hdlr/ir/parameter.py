#!/usr/bin/env python3
# coding: utf-8

# distributed under the mit license
# https://opensource.org/licenses/mit-license.php

from dataclasses import dataclass

@dataclass
class Parameter:
    name: str
    value_str: str | None = None
    value_int: str | None = None

    def to_dict(self) -> dict:
        if self.value_int is not None:
            return {
                "name": self.name,
                "value": self.value_int
            }
        if self.value_str is not None:
            return {
                "name": self.name,
                "value": self.value_str
            }
