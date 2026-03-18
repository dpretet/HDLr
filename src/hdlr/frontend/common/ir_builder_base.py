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
