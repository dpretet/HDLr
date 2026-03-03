#!/usr/bin/env python3
# coding: utf-8

# distributed under the mit license
# https://opensource.org/licenses/mit-license.php

"""
Verilog parser
"""


from tree_sitter import Parser, Language
import tree_sitter_verilog

from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class Port:
    name: str
    direction: str
    width: Optional[str] = None


@dataclass
class Module:
    name: str
    ports: List[Port] = field(default_factory=list)


VERILOG_LANGUAGE = Language(tree_sitter_verilog.language())

def get_text(node, source):
    """ Grab text from a node """
    return source[node.start_byte:node.end_byte].decode()


def walk(node, source, modules):
    """ Parse a node """
    if node.type == "module_declaration":
        module_name = None
        ports = []

        # --- Module name ---
        header = next((c for c in node.children if c.type == "module_header"), None)
        if header:
            name_node = next(
                (c for c in header.children if c.type == "simple_identifier"),
                None
            )
            if name_node:
                module_name = get_text(name_node, source)

        # --- ANSI Ports ---
        ansi_header = next(
            (c for c in node.children if c.type == "module_ansi_header"),
            None
        )

        if ansi_header:
            port_list = next(
                (c for c in ansi_header.children if c.type == "list_of_port_declarations"),
                None
            )

            if port_list:
                for port_decl in port_list.children:
                    if port_decl.type == "ansi_port_declaration":
                        direction = None
                        name = None

                        for part in port_decl.children:
                            # direction
                            if part.type == "net_port_header1":
                                dir_node = next(
                                    (c for c in part.children if c.type == "port_direction"),
                                    None
                                )
                                if dir_node:
                                    direction = get_text(dir_node, source)

                            # name
                            if part.type == "port_identifier":
                                id_node = next(
                                    (c for c in part.children if c.type == "simple_identifier"),
                                    None
                                )
                                if id_node:
                                    name = get_text(id_node, source)

                        if name:
                            ports.append((direction, name))

        module_obj = Module(name=module_name)
        for direction, name in ports:
            module_obj.ports.append(
                Port(name=name, direction=direction)
            )
        modules.append(module_obj)

    # recurse
    for child in node.children:
        walk(child, source, modules)


def parse_verilog(path):
    parser = Parser()
    parser.language = VERILOG_LANGUAGE

    with open(path, "rb") as f:
        source = f.read()

    tree = parser.parse(source)
    root = tree.root_node

    modules = []

    walk(root, source, modules)

    return modules
