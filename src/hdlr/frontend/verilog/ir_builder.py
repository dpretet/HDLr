#!/usr/bin/env python3
# coding: utf-8

# distributed under the mit license
# https://opensource.org/licenses/mit-license.php

from ..common.ir_builder_base import IRBuilder

from ...ir.module import Module
from ...ir.port import Port
from ...ir.signal import Signal
from ...ir.parameter import Parameter


class VerilogIRBuilder(IRBuilder):

    # ---------------------------------------------------------
    # Entry
    # ---------------------------------------------------------

    def build(self, tree):
        modules = []

        root = tree.root_node
        for child in root.children:
            if child.type == "module_declaration":
                modules.append(self._build_module(child))

        return modules

    # ---------------------------------------------------------
    # Module
    # ---------------------------------------------------------

    def _build_module(self, node):

        name = self._extract_module_name(node)
        module = Module(name=name)
        self._extract_parameters(node, module)
        self._extract_ports(node, module)

        return module

    def _extract_module_name(self, node):
        header = next(
            (c for c in node.children if c.type == "module_header"),
            None
        )

        if header is None:
            raise RuntimeError("module_header introuvable")

        name_node = next(
            (c for c in header.children if c.type == "simple_identifier"),
            None
        )

        if name_node is None:
            raise RuntimeError("Nom du module introuvable")

        return name_node.text.decode()

    # ---------------------------------------------------------
    # Ports (ANSI style)
    # ---------------------------------------------------------

    def _extract_ports(self, node, module):
        ansi_header = next(
            (c for c in node.children if c.type == "module_ansi_header"),
            None
        )

        if ansi_header is None:
            return

        port_list = next(
            (c for c in ansi_header.children if c.type == "list_of_port_declarations"),
            None
        )

        if port_list is None:
            return

        for port_decl in port_list.children:
            if port_decl.type == "ansi_port_declaration":
                port = self._build_ansi_port(port_decl)
                if port:
                    module.ports.append(port)

    def _build_ansi_port(self, node):
        direction = None
        width = None
        name = None

        for child in node.children:

            # direction + net type
            if child.type in ("net_port_header1", "variable_port_header"):
                direction = self._extract_direction(child)
                width = self._extract_width(child)

            # port name
            if child.type == "port_identifier":
                ident = next(
                    (c for c in child.children if c.type == "simple_identifier"),
                    None
                )
                if ident:
                    name = ident.text.decode()

        if name is None:
            return None

        return Port(
            name=name,
            direction=direction,
            width=width
        )

    def _extract_parameters(self, node, module):

        ansi_header = next(
            (c for c in node.children if c.type == "module_ansi_header"),
            None
        )

        if ansi_header is None:
            return

        param_port_list = next(
            (c for c in ansi_header.children if c.type == "parameter_port_list"),
            None
        )

        if param_port_list is None:
            return

        for param_port_decl in param_port_list.children:
            if param_port_decl.type != "parameter_port_declaration":
                continue

            param_decl = next(
                (c for c in param_port_decl.children if c.type == "parameter_declaration"),
                None
            )

            if param_decl is None:
                continue

            list_node = next(
                (c for c in param_decl.children if c.type == "list_of_param_assignments"),
                None
            )

            if list_node is None:
                continue

            for assignment in list_node.children:
                if assignment.type != "param_assignment":
                    continue

                name_node = next(
                    (c for c in assignment.children if c.type == "parameter_identifier"),
                    None
                )

                value_node = next(
                    (c for c in assignment.children if "expression" in c.type),
                    None
                )

                if name_node is None or value_node is None:
                    continue

                module.parameters.append(
                    Parameter(
                        name=name_node.text.decode(),
                        value=value_node.text.decode()
                    )
                )


    # ---------------------------------------------------------
    # Direction
    # ---------------------------------------------------------

    def _extract_direction(self, node):
        for child in node.children:
            if child.type == "port_direction":
                # child text = "input", "output", "inout"
                return child.text.decode()
        return None

    # ---------------------------------------------------------
    # Width extraction
    # ---------------------------------------------------------

    def _extract_width(self, node):
        """
        Cherche packed_dimension → constant_range
        Retourne tuple (msb, lsb) ou None
        """

        for child in node.children:
            if child.type == "data_type":
                return self._find_packed_dimension(child)

            if child.type.startswith("net_port_type"):
                return self._find_packed_dimension(child)

        return None

    def _find_packed_dimension(self, node):
        for child in node.children:
            if child.type == "packed_dimension":
                return self._extract_range(child)

            # récursif
            result = self._find_packed_dimension(child)
            if result:
                return result

        return None

    def _extract_range(self, node):
        """
        packed_dimension
            → constant_range
                → constant_expression
                → constant_expression
        """

        range_node = next(
            (c for c in node.children if c.type == "constant_range"),
            None
        )

        if range_node is None:
            return None

        exprs = [
            c for c in range_node.children
            if c.type == "constant_expression"
        ]

        if len(exprs) != 2:
            return None

        msb = exprs[0].text.decode()
        lsb = exprs[1].text.decode()

        return (msb, lsb)


