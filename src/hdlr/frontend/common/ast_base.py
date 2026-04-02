#!/usr/bin/env python3
# coding: utf-8

# distributed under the mit license
# https://opensource.org/licenses/mit-license.php

from typing import Any


class ASTNode:
    node: Any
    source: bytes

    @property
    def type(self):
        return self.node.type

    @property
    def text(self) -> str:
        return self.source[self.node.start_byte:self.node.end_byte].decode()

    def children(self):
        return self.node.children

    def child_by_field(self, name: str):
        return self.node.child_by_field_name(name)
