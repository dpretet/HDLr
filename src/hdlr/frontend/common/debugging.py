#!/usr/bin/env python3
# coding: utf-8

# distributed under the mit license
# https://opensource.org/licenses/mit-license.php

def ts_print(node, level=0):

    indent = "  " * level
    field = ""

    if node.parent is not None:
        parent = node.parent

        # trouver l'index du node dans les enfants du parent
        for i, child in enumerate(parent.children):
            if child is node:
                field_name = parent.field_name_for_child(i)
                if field_name:
                    field = f" ({field_name})"
                break

    print(f"{indent}{node.type}{field}")

    for child in node.children:
        if child.is_named:
            ts_print(child, level + 1)
