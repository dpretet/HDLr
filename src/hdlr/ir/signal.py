#!/usr/bin/env python3
# coding: utf-8

# distributed under the mit license
# https://opensource.org/licenses/mit-license.php

from dataclasses import dataclass

@dataclass
class Signal:
    name: str
    kind: str
    width: tuple[str, str] | None = None

    def to_dict(self) -> dict:
        data = {
            "kind": self.kind,
        }

        if self.width is not None:
            msb, lsb = self.width
            data["width"] = {
                "msb": msb,
                "lsb": lsb
            }

        return data
