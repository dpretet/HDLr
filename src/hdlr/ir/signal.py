#!/usr/bin/env python3
# coding: utf-8

# distributed under the mit license
# https://opensource.org/licenses/mit-license.php

from dataclasses import dataclass


@dataclass
class Signal:
    name: str
    kind: str
    width_str: tuple[str, str] | None = None
    width_int: tuple[int, int] | None = None
    condition: str | None = None  # Condition for generate blocks

    def to_dict(self) -> dict:
        data = {
            "kind": self.kind,
        }

        if self.width_str is not None:
            msb, lsb = self.width_str
            data["width"] = {
                "msb": msb,
                "lsb": lsb
            }

        if self.width_int is not None:
            msb, lsb = self.width_int
            data["width"] = {
                "msb": msb,
                "lsb": lsb
            }
        return data
