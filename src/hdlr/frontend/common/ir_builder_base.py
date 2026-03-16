#!/usr/bin/env python3
# coding: utf-8

# distributed under the mit license
# https://opensource.org/licenses/mit-license.php

class IRBuilder:

    def build(self, tree):
        raise NotImplementedError

    # --------------------------------------------------------------
    # Facilities to parse the tree
    # --------------------------------------------------------------

    def _first(self, node, type_name):
        return next(
            (c for c in node.named_children if c.type == type_name),
            None
        )

    def _all(self, node, type_name):
        return [
            c for c in node.named_children
            if c.type == type_name
        ]
