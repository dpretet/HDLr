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


class VerilogIRBuilder(IRBuilder):
    """ Verilog Class to buidl the IR """

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
        self._extract_signals(node, module)
        self._extract_instances(node, module)

        return module

    def _extract_module_name(self, node):

        header = self._first(node, "module_header")

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

    # ---------------------------------------------------------
    # Parameters (ANSI style)
    # ---------------------------------------------------------

    def _extract_parameters(self, node, module):

        ansi_header = self._first(node, "module_ansi_header")

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


    # ---------------------------------------------------------
    # Internal Signals
    # ---------------------------------------------------------

    def _extract_signals(self, node, module):

        for item in node.children:

            if item.type != "module_or_generate_item":
                continue

            for pkg_decl in item.children:

                if pkg_decl.type != "package_or_generate_item_declaration":
                    continue

                # -------------------------
                # data_declaration
                # -------------------------
                for child in pkg_decl.children:

                    if child.type == "data_declaration":
                        self._handle_data_declaration(child, module)

                    elif child.type == "net_declaration":
                        self._handle_net_declaration(child, module)


    def _handle_data_declaration(self, node, module):

        kind = None
        width = None

        # ✅ récupérer data_type_or_implicit1
        dtype_wrapper = next(
            (c for c in node.children if c.type.startswith("data_type_or_implicit")),
            None
        )

        if dtype_wrapper:
            data_type = next(
                (c for c in dtype_wrapper.children if c.type == "data_type"),
                None
            )

            if data_type:
                # type (logic, reg, etc.)
                base_type = next(
                    (c for c in data_type.children
                    if c.type in ("integer_vector_type", "net_type")),
                    None
                )

                if base_type:
                    kind = base_type.text.decode()

                # width
                packed_dim = next(
                    (c for c in data_type.children
                    if c.type == "packed_dimension"),
                    None
                )

                if packed_dim:
                    width = self._extract_range(packed_dim)

        # ✅ variables
        list_node = next(
            (c for c in node.children
            if c.type == "list_of_variable_decl_assignments"),
            None
        )

        if list_node is None:
            return

        for var_decl in list_node.children:

            if var_decl.type != "variable_decl_assignment":
                continue

            ident = next(
                (c for c in var_decl.children
                if c.type == "simple_identifier"),
                None
            )

            if ident is None:
                continue

            module.signals.append(
                Signal(
                    name=ident.text.decode(),
                    kind=kind,
                    width=width
                )
            )

    def _handle_net_declaration(self, node, module):

        kind = None
        width = None

        # -------------------------
        # net_type (wire, tri, etc.)
        # -------------------------
        net_type_node = next(
            (c for c in node.children if c.type == "net_type"),
            None
        )

        if net_type_node:
            kind = net_type_node.text.decode()

        # -------------------------
        # packed_dimension (width)
        # -------------------------
        dtype_wrapper = next(
            (c for c in node.children
            if c.type.startswith("data_type_or_implicit")),
            None
        )

        if dtype_wrapper:
            width = self._find_packed_dimension(dtype_wrapper)

        # -------------------------
        # list_of_net_decl_assignments
        # -------------------------
        list_node = next(
            (c for c in node.children
            if c.type == "list_of_net_decl_assignments"),
            None
        )

        if not list_node:
            return

        for decl in list_node.children:

            if decl.type != "net_decl_assignment":
                continue

            ident = next(
                (c for c in decl.children
                if c.type == "simple_identifier"),
                None
            )

            if not ident:
                continue

            module.signals.append(
                Signal(
                    name=ident.text.decode(),
                    kind=kind,   # "wire"
                    width=width
                )
            )


    def _extract_instances(self, node, module):

        for item in node.children:

            if item.type != "module_or_generate_item":
                continue

            for inst_node in self._all(item, "module_instantiation"):
                self._handle_module_instantiation(inst_node, module)

    def _handle_module_instantiation(self, node, module):

        # -------------------------
        # Module name
        # -------------------------
        module_name_node = next(
            (c for c in node.children
            if c.type == "simple_identifier"),
            None
        )

        if not module_name_node:
            return

        module_name = module_name_node.text.decode()

        # -------------------------
        # Parameter override
        # -------------------------
        param_node = next(
            (c for c in node.children
            if c.type == "parameter_value_assignment"),
            None
        )

        parameters = self._extract_param_override(param_node)

        # -------------------------
        # Instance (TON AST → hierarchical_instance)
        # -------------------------

        for hier_node in self._all(node, "hierarchical_instance"):
            instance = self._build_instance_from_hier(
                hier_node,
                module_name,
                parameters
            )
            if instance:
                module.instances.append(instance)


    def _build_instance_from_hier(self, node, module_name, parameters):

        # Instance name
        name_node = next(
            (c for c in node.children
            if c.type == "name_of_instance"),
            None
        )

        if not name_node:
            return None

        instance_name = name_node.text.decode()

        connections = {}

        port_list = next(
            (c for c in node.children
            if c.type == "list_of_port_connections"),
            None
        )

        if port_list:
            for conn in port_list.children:

                if conn.type != "named_port_connection":
                    continue

                port = next(
                    (c for c in conn.children
                    if c.type == "port_identifier"),
                    None
                )

                expr = next(
                    (c for c in conn.children
                    if "expression" in c.type),
                    None
                )

                if port and expr:
                    connections[port.text.decode()] = expr.text.decode()

        return Instance(
            name=instance_name,
            module_name=module_name,
            parameters=parameters.copy(),
            connections=connections
        )

    def _extract_param_override(self, node):

        if not node:
            return {}

        parameters = {}

        # Descend vers list_of_parameter_assignments
        list_node = next(
            (c for c in node.children
            if c.type == "list_of_parameter_assignments"),
            None
        )

        if not list_node:
            return parameters

        for child in list_node.children:

            if child.type != "named_parameter_assignment":
                continue

            # Nom du parameter
            name_node = next(
                (c for c in child.children
                if c.type == "parameter_identifier"),
                None
            )

            # Valeur
            value_node = next(
                (c for c in child.children
                if "expression" in c.type),
                None
            )

            if name_node and value_node:
                parameters[name_node.text.decode()] = value_node.text.decode()

        return parameters

    def _first(self, node, type_name):
        return next((c for c in node.children if c.type == type_name), None)

    def _all(self, node, type_name):
        return [c for c in node.children if c.type == type_name]
