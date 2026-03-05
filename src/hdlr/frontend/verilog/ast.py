#!/usr/bin/env python3
# coding: utf-8

# distributed under the mit license
# https://opensource.org/licenses/mit-license.php

from frontend.common.ast_base import ASTNode

class VerilogNode(ASTNode):

    def name(self):
        node = self.child_by_field("name")
        return self._text(node) if node else None

    def _text(self, node):
        return self.source[node.start_byte:node.end_byte].decode()

