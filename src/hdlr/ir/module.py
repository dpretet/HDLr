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

    def to_dict(self) -> dict:
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
