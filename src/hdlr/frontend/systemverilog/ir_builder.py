#!/usr/bin/env python3
# coding: utf-8

# distributed under the mit license
# https://opensource.org/licenses/mit-license.php

from ..common.ir_builder_base import IRBuilder

from ...ir.module import Module
from ...ir.port import Port
from ...ir.signal import Signal
from ...ir.parameter import Parameter
from ...ir.instance import Instance


class SystemVerilogIRBuilder(IRBuilder):
    """ SystemVerilog Class to buidl the IR """

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

    def _build_module(self, node):

        name = self._extract_module_name(node)
        module = Module(name=name)
        self._extract_parameters(node, module)
        self._extract_ports(node, module)
        self._extract_signals(node, module)
        self._extract_instances(node, module)

        return module

    def _extract_module_name(self, node):

        header = self._first(node, "module_ansi_header")

        if header is None:
            header = self._first(node, "module_nonansi_header")

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

        ansi_header = self._first(node, "module_ansi_header")

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

        # -------------------------
        # Nom
        # -------------------------
        name_node = node.child_by_field_name("port_name")
        if not name_node:
            return None

        name = name_node.text.decode()

        # -------------------------
        # Header
        # -------------------------
        header = next(
            (c for c in node.children
            if c.type in ("net_port_header", "variable_port_header")),
            None
        )

        if not header:
            return Port(name=name)

        # -------------------------
        # Direction
        # -------------------------
        direction_node = next(
            (c for c in header.children
            if c.type == "port_direction"),
            None
        )

        direction = direction_node.text.decode() if direction_node else None

        # -------------------------
        # Width (recursive)
        # -------------------------
        width = self._find_packed_dimension(header)

        return Port(
            name=name,
            direction=direction,
            width_str=width
        )

    # ---------------------------------------------------------
    # Parameters (ANSI style)
    # ---------------------------------------------------------

    def _extract_parameters(self, node, module):

        # =========================================================
        # 1️⃣ HEADER PARAMETERS (ANSI + NON ANSI)
        # =========================================================

        header = self._first(node, "module_ansi_header")

        if header is None:
            header = self._first(node, "module_nonansi_header")

        if header:
            param_port_list = self._first(header, "parameter_port_list")

            if param_port_list:
                for param_port_decl in param_port_list.named_children:

                    if param_port_decl.type != "parameter_port_declaration":
                        continue

                    param_decl = self._first(
                        param_port_decl,
                        "parameter_declaration"
                    )

                    if param_decl:
                        self._handle_parameter_declaration(param_decl, module)

        # =========================================================
        # 2️⃣ BODY PARAMETERS
        # =========================================================

        for item in node.named_children:

            # Handle module_item wrapped parameters (non-ANSI style)
            if item.type == "module_item":
                param_decl = self._first(item, "parameter_declaration")
                if param_decl:
                    self._handle_parameter_declaration(param_decl, module)

                localparam_decl = self._first(item, "local_parameter_declaration")
                if localparam_decl:
                    self._handle_parameter_declaration(localparam_decl, module)

            # Handle direct parameter declarations (ANSI style)
            elif item.type == "parameter_declaration":
                self._handle_parameter_declaration(item, module)

            elif item.type == "local_parameter_declaration":
                self._handle_parameter_declaration(item, module)

    def _handle_parameter_declaration(self, node, module):

        list_node = self._first(node, "list_of_param_assignments")

        if not list_node:
            return

        for assignment in list_node.named_children:

            if assignment.type != "param_assignment":
                continue

            name_node = None
            value_node = None

            for child in assignment.named_children:

                if child.type == "simple_identifier":
                    name_node = child

                elif "expression" in child.type:
                    value_node = child

            if not name_node:
                continue

            module.parameters.append(
                Parameter(
                    name=name_node.text.decode(),
                    value_str=value_node.text.decode() if value_node else None
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


    # ---------------------------------------------------------
    # Internal Signals
    # ---------------------------------------------------------

    def _extract_signals(self, node, module):

        for item in node.children:
            # -------------------------
            # data_declaration
            # -------------------------

            if item.type == "data_declaration":
                self._build_data_declaration(item, module)

            elif item.type == "net_declaration":
                self._build_net_declaration(item, module)


    def _build_net_declaration(self, node, module):


        width = self._find_packed_dimension(node)

        for child in node.children:
            if child.type == "list_of_net_identifiers":
                for ident in child.named_children:

                    if ident.type == "net_identifier":
                        name = ident.text.decode()

                        module.signals.append(
                            Signal(
                                name=name,
                                kind="wire",
                                width_str=width
                            )
                        )

    def _build_data_declaration(self, node, module):

        width = self._find_packed_dimension(node)

        for child in node.children:
            if child.type == "list_of_variable_decl_assignments":
                for var in child.named_children:
                    if var.type != "variable_decl_assignment":
                        continue

                    name_node = var.child_by_field_name("name")

                    if not name_node:
                        continue

                    name = name_node.text.decode()

                    module.signals.append(
                        Signal(
                            name=name,
                            kind="logic",   # tu peux raffiner plus tard
                            width_str=width
                        )
                    )


    # ---------------------------------------------------------
    # Instances
    # ---------------------------------------------------------

    def _extract_instances(self, node, module):


        for item in node.named_children:

            if item.type == "module_instantiation":
                self._handle_module_instantiation(item, module)


    def _handle_module_instantiation(self, node, module):

        param_node = self._first(node, "parameter_value_assignment")

        module_name_node = node.child_by_field_name("instance_type")

        if not module_name_node:
            return

        module_name = module_name_node.text.decode()

        param_node = self._first(node, "parameter_value_assignment")
        parameters = self._extract_param_override(param_node)

        for hier_node in self._all(node, "hierarchical_instance"):

            instance = self._build_instance_from_hier(
                hier_node,
                module_name,
                parameters
            )

            if instance:
                module.instances.append(instance)


    def _build_instance_from_hier(self, node, module_name, parameters):

        # 1️⃣ récupérer le bloc name_of_instance
        name_block = self._first(node, "name_of_instance")

        if not name_block:
            return None

        # 2️⃣ récupérer le field instance_name
        name_node = name_block.child_by_field_name("instance_name")

        if not name_node:
            return None

        instance_name = name_node.text.decode()

        # -------------------------
        # Connexions
        # -------------------------
        connections = {}

        port_list = self._first(node, "list_of_port_connections")

        if port_list:
            for conn in port_list.named_children:

                if conn.type != "named_port_connection":
                    continue

                port_node = conn.child_by_field_name("port_name")
                expr_node = conn.child_by_field_name("connection")

                if port_node and expr_node:
                    connections[
                        port_node.text.decode()
                    ] = expr_node.text.decode()

        return Instance(
            name=instance_name,
            module_name=module_name,
            parameters=parameters.copy(),
            connections=connections
        )

    def _extract_param_override(self, node):

        if not node:
            return {}

        params = {}

        # (list_of_parameter_value_assignments ...)
        list_node = next(
            (c for c in node.named_children
            if c.type == "list_of_parameter_value_assignments"),
            None
        )

        if not list_node:
            return {}

        for param in list_node.named_children:

            if param.type != "named_parameter_assignment":
                continue

            # Structure exacte :
            # (named_parameter_assignment
            #    (simple_identifier)
            #    (param_expression ...))

            name_node = None
            value_node = None

            for child in param.named_children:

                if child.type == "simple_identifier":
                    name_node = child

                elif child.type == "param_expression":
                    value_node = child

            if name_node and value_node:
                name = name_node.text.decode()
                value = value_node.text.decode()
                params[name] = value

        return params



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
