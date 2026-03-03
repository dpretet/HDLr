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


# ============================================================
# IR STRUCTURES
# ============================================================

@dataclass
class Parameter:
    name: str
    value: str


@dataclass
class Port:
    name: str
    direction: Optional[str]
    width: Optional[str] = None


@dataclass
class Module:
    name: str
    parameters: List[Parameter] = field(default_factory=list)
    ports: List[Port] = field(default_factory=list)


# ============================================================
# TREE-SITTER INIT
# ============================================================

VERILOG_LANGUAGE = Language(tree_sitter_verilog.language())


# ============================================================
# UTILS
# ============================================================

def get_text(node, source):
    """Grab text from a node"""
    return source[node.start_byte:node.end_byte].decode()


# ============================================================
# AST WALKER
# ============================================================

def walk(node, source, modules):
    """Parse a node"""

    if node.type == "module_declaration":

        module_name = None
        module_obj = None

        # ----------------------------------------------------
        # Module name
        # ----------------------------------------------------

        header = next((c for c in node.children if c.type == "module_header"), None)

        if header:
            name_node = next(
                (c for c in header.children if c.type == "simple_identifier"),
                None
            )
            if name_node:
                module_name = get_text(name_node, source)

        if not module_name:
            return

        module_obj = Module(name=module_name)

        # ----------------------------------------------------
        # PARAMETERS
        # ----------------------------------------------------

        param_list = next(
            (c for c in node.children if c.type == "parameter_port_list"),
            None
        )

        if param_list:
            for param_decl in param_list.children:
                if param_decl.type == "parameter_declaration":

                    for assign in param_decl.children:
                        if assign.type == "param_assignment":

                            name = None
                            value = None

                            for part in assign.children:
                                if part.type == "simple_identifier":
                                    name = get_text(part, source)

                                # everything after '=' is value
                                if part.type not in (
                                    "simple_identifier",
                                    "=",
                                ):
                                    value = get_text(part, source)

                            if name and value:
                                module_obj.parameters.append(
                                    Parameter(name=name, value=value)
                                )

        # ----------------------------------------------------
        # ANSI PORTS
        # ----------------------------------------------------

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
                        width = None

                        # explore recursively all children
                        stack = [port_decl]

                        while stack:
                            current = stack.pop()

                            # direction
                            if current.type == "port_direction":
                                direction = get_text(current, source)

                            # width
                            if current.type == "packed_dimension":
                                width = get_text(current, source)

                            # identifier
                            if current.type == "simple_identifier":
                                name = get_text(current, source)

                            stack.extend(current.children)

                        if name:
                            module_obj.ports.append(
                                Port(
                                    name=name,
                                    direction=direction,
                                    width=width
                                )
                            )

        modules.append(module_obj)

    # --------------------------------------------------------
    # RECURSION
    # --------------------------------------------------------

    for child in node.children:
        walk(child, source, modules)


# ============================================================
# ENTRY POINT
# ============================================================

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

