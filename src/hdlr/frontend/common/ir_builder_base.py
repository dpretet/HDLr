#!/usr/bin/env python3
# coding: utf-8

# distributed under the mit license
# https://opensource.org/licenses/mit-license.php

"""
Base IR Builder class.

This module provides the base class and common utilities for IR builders.
It defines the interface that specific language builders (Verilog, SystemVerilog)
must implement and provides helper methods for tree traversal.
"""

class IRBuilder:
    """Base class for IR builders.

    Specific language builders should inherit from this class and implement
    the build method.
    """

    def build(self, tree):
        """Build IR from AST - to be implemented by subclasses.

        Args:
            tree: Tree-sitter AST root node

        Returns:
            List of Module objects

        Raises:
            NotImplementedError: Must be implemented by subclasses
        """
        raise NotImplementedError

    # --------------------------------------------------------------
    # Facilities to parse the tree
    # --------------------------------------------------------------

    def _first(self, node, type_name):
        """Get first named child of specified type.

        Args:
            node: Parent node to search
            type_name: Type name to find

        Returns:
            First child with matching type, or None if not found
        """
        return next(
            (c for c in node.named_children if c.type == type_name),
            None
        )

    def _all(self, node, type_name):
        """Get all named children of specified type.

        Args:
            node: Parent node to search
            type_name: Type name to find

        Returns:
            List of all children with matching type
        """
        return [c for c in node.named_children if c.type == type_name]

    # --------------------------------------------------------------
    # Generic text extraction utilities
    # --------------------------------------------------------------

    def _get_text(self, node):
        """Get text content from a node.

        Args:
            node: AST node

        Returns:
            Decoded text string, or empty string if node is None
        """
        if node:
            return node.text.decode("utf8")
        return ""

    def _get_identifier_text(self, node):
        """Get text from an identifier node.

        Args:
            node: Identifier node or parent node containing identifier

        Returns:
            Identifier text, or empty string if not found
        """
        if node and node.type == "identifier":
            return self._get_text(node)

        # Look for identifier child
        id_node = self._first(node, "identifier")
        if id_node:
            return self._get_text(id_node)

        return ""

    def _get_expression_text(self, node):
        """Get text from an expression node.

        Args:
            node: Expression node

        Returns:
            Expression text, or empty string if not found
        """
        if not node:
            return ""

        # Try to find the most specific expression child
        # Different languages may override this with their specific expression types
        expr_types = ["number", "identifier", "string_literal", "literal"]
        for expr_type in expr_types:
            expr_node = self._first(node, expr_type)
            if expr_node:
                return self._get_text(expr_node)

        # Fallback: return the whole node text
        return self._get_text(node)
