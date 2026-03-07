#!/usr/bin/env python3
# coding: utf-8

# distributed under the mit license
# https://opensource.org/licenses/mit-license.php

from dataclasses import dataclass

@dataclass
class Port:
    name: str
    direction: str | None = None
    width: tuple[str, str] | None = None

    def to_dict(self) -> dict:
        data = {}

        if self.direction is not None:
            data["direction"] = self.direction

        if self.width is not None:
            msb, lsb = self.width
            data["width"] = {
                "msb": msb,
                "lsb": lsb
            }

        return data
