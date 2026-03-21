#!/usr/bin/env python3
# coding: utf-8

# distributed under the mit license
# https://opensource.org/licenses/mit-license.php

"""Unit tests for HierarchyBuilder class."""

import pytest
from hdlr.ir.node import HierarchyBuilder, Design, Node
from hdlr.ir.module import Module
from hdlr.ir.parameter import Parameter
from hdlr.ir.instance import Instance


def test_simple_hierarchy():
    """Test building a simple hierarchy with one module."""
    # Create a simple module
    module = Module(name="top")
    
    # Create design and add module
    design = Design()
    design.add_module(module)
    
    # Build hierarchy
    builder = HierarchyBuilder(design)
    root = builder.build("top")
    
    # Verify result
    assert isinstance(root, Node)
    assert root.module_name == "top"
    assert root.instance_name is None
    assert root.parameters == {}
    assert len(root.children) == 0


def test_hierarchy_with_parameters():
    """Test building hierarchy with module parameters."""
    # Create module with parameters
    module = Module(
        name="top",
        parameters=[
            Parameter(name="WIDTH", value_int=32),
            Parameter(name="DEPTH", value_str="16")
        ]
    )
    
    # Create design and add module
    design = Design()
    design.add_module(module)
    
    # Build hierarchy
    builder = HierarchyBuilder(design)
    root = builder.build("top")
    
    # Verify result
    assert root.parameters == {"WIDTH": 32, "DEPTH": 16}


def test_hierarchy_with_child_instance():
    """Test building hierarchy with child instances."""
    # Create child module
    child_module = Module(name="adder")
    
    # Create parent module with instance
    parent_module = Module(
        name="top",
        instances=[
            Instance(name="u0", module_name="adder")
        ]
    )
    
    # Create design and add modules
    design = Design()
    design.add_module(child_module)
    design.add_module(parent_module)
    
    # Build hierarchy
    builder = HierarchyBuilder(design)
    root = builder.build("top")
    
    # Verify result
    assert len(root.children) == 1
    assert root.children[0].module_name == "adder"
    assert root.children[0].instance_name == "u0"


def test_parameter_inheritance():
    """Test parameter inheritance from parent to child."""
    # Create child module with parameter that uses parent parameter
    child_module = Module(
        name="child",
        parameters=[
            Parameter(name="CHILD_WIDTH", value_str="WIDTH * 2")
        ]
    )
    
    # Create parent module
    parent_module = Module(
        name="top",
        parameters=[
            Parameter(name="WIDTH", value_int=16)
        ],
        instances=[
            Instance(name="u0", module_name="child")
        ]
    )
    
    # Create design and add modules
    design = Design()
    design.add_module(child_module)
    design.add_module(parent_module)
    
    # Build hierarchy
    builder = HierarchyBuilder(design)
    root = builder.build("top")
    
    # Verify parent parameters
    assert root.parameters["WIDTH"] == 16
    
    # Verify child parameters (should inherit and calculate)
    assert len(root.children) == 1
    assert root.children[0].parameters["CHILD_WIDTH"] == 32  # 16 * 2


def test_parameter_override():
    """Test parameter override in instance."""
    # Create child module
    child_module = Module(
        name="fifo",
        parameters=[
            Parameter(name="DEPTH", value_int=8),
            Parameter(name="WIDTH", value_int=16)
        ]
    )
    
    # Create parent module with instance that overrides parameters
    parent_module = Module(
        name="top",
        instances=[
            Instance(
                name="u0",
                module_name="fifo",
                parameters={
                    "DEPTH": "32",  # Override default
                    "WIDTH": "64"   # Override default
                }
            )
        ]
    )
    
    # Create design and add modules
    design = Design()
    design.add_module(child_module)
    design.add_module(parent_module)
    
    # Build hierarchy
    builder = HierarchyBuilder(design)
    root = builder.build("top")
    
    # Verify child parameters are overridden
    assert len(root.children) == 1
    child = root.children[0]
    assert child.parameters["DEPTH"] == 32
    assert child.parameters["WIDTH"] == 64


def test_verilog_number_formats():
    """Test Verilog number format conversion in parameters."""
    # Create module with Verilog number formats
    module = Module(
        name="top",
        parameters=[
            Parameter(name="HEX_VAL", value_str="8'hFF"),
            Parameter(name="DEC_VAL", value_str="16'd42"),
            Parameter(name="BIN_VAL", value_str="8'b1010"),
            Parameter(name="OCT_VAL", value_str="8'o77")
        ]
    )
    
    # Create design and add module
    design = Design()
    design.add_module(module)
    
    # Build hierarchy
    builder = HierarchyBuilder(design)
    root = builder.build("top")
    
    # Verify number format conversions
    assert root.parameters["HEX_VAL"] == 255  # 0xFF
    assert root.parameters["DEC_VAL"] == 42   # 42
    assert root.parameters["BIN_VAL"] == 10   # 1010b
    assert root.parameters["OCT_VAL"] == 63   # 0o77


def test_clog2_function():
    """Test $clog2 function in parameter expressions."""
    # Create module with $clog2 expressions
    module = Module(
        name="top",
        parameters=[
            Parameter(name="ADDR_WIDTH", value_str="$clog2(256)"),
            Parameter(name="DATA_WIDTH", value_str="$clog2(16)")
        ]
    )
    
    # Create design and add module
    design = Design()
    design.add_module(module)
    
    # Build hierarchy
    builder = HierarchyBuilder(design)
    root = builder.build("top")
    
    # Verify $clog2 calculations
    assert root.parameters["ADDR_WIDTH"] == 8   # log2(256) = 8
    assert root.parameters["DATA_WIDTH"] == 4   # log2(16) = 4


def test_ternary_operator():
    """Test ternary operator in parameter expressions."""
    # Create module with ternary expressions
    module = Module(
        name="top",
        parameters=[
            Parameter(name="WIDTH", value_int=32),
            Parameter(name="SIZE", value_str="(WIDTH > 16) ? 64 : 32")
        ]
    )
    
    # Create design and add module
    design = Design()
    design.add_module(module)
    
    # Build hierarchy
    builder = HierarchyBuilder(design)
    root = builder.build("top")
    
    # Verify ternary operator evaluation
    assert root.parameters["WIDTH"] == 32
    assert root.parameters["SIZE"] == 64  # 32 > 16, so 64


def test_complex_expression():
    """Test complex parameter expressions."""
    # Create module with complex expressions
    module = Module(
        name="top",
        parameters=[
            Parameter(name="BASE", value_int=8),
            Parameter(name="FACTOR", value_int=4),
            Parameter(name="RESULT", value_str="BASE * FACTOR + $clog2(BASE)")
        ]
    )
    
    # Create design and add module
    design = Design()
    design.add_module(module)
    
    # Build hierarchy
    builder = HierarchyBuilder(design)
    root = builder.build("top")
    
    # Verify complex expression: 8 * 4 + log2(8) = 32 + 3 = 35
    assert root.parameters["RESULT"] == 35


def test_missing_module_error():
    """Test error handling for missing module."""
    # Create design without the module
    design = Design()
    
    # Create builder and try to build non-existent module
    builder = HierarchyBuilder(design)
    
    # Should raise KeyError
    with pytest.raises(KeyError):
        builder.build("non_existent_module")


def test_duplicate_module_error():
    """Test error handling for duplicate modules."""
    # Create design
    design = Design()
    
    # Add same module twice
    module1 = Module(name="top")
    module2 = Module(name="top")
    
    design.add_module(module1)
    
    # Should raise ValueError for duplicate
    with pytest.raises(ValueError):
        design.add_module(module2)


def test_deep_hierarchy():
    """Test building a deep hierarchy."""
    # Create leaf module
    leaf_module = Module(name="leaf")
    
    # Create middle module
    middle_module = Module(
        name="middle",
        instances=[
            Instance(name="leaf1", module_name="leaf"),
            Instance(name="leaf2", module_name="leaf")
        ]
    )
    
    # Create top module
    top_module = Module(
        name="top",
        instances=[
            Instance(name="mid1", module_name="middle"),
            Instance(name="mid2", module_name="middle")
        ]
    )
    
    # Create design and add modules
    design = Design()
    design.add_module(leaf_module)
    design.add_module(middle_module)
    design.add_module(top_module)
    
    # Build hierarchy
    builder = HierarchyBuilder(design)
    root = builder.build("top")
    
    # Verify deep hierarchy structure
    assert len(root.children) == 2  # mid1 and mid2
    for child in root.children:
        assert child.module_name == "middle"
        assert len(child.children) == 2  # leaf1 and leaf2
        for grandchild in child.children:
            assert grandchild.module_name == "leaf"


def test_parameter_override_with_dependent_params():
    """Test parameter override with dependent parameters."""
    # Create FIFO module with dependent parameter
    fifo_module = Module(
        name="fifo",
        parameters=[
            Parameter(name="DEPTH", value_int=8),
            Parameter(name="WIDTH", value_int=16),
            Parameter(name="ADDR_WIDTH", value_str="$clog2(DEPTH)")
        ]
    )
    
    # Create top module with FIFO instance that overrides DEPTH
    top_module = Module(
        name="top",
        instances=[
            Instance(
                name="u0",
                module_name="fifo",
                parameters={
                    "DEPTH": "256",  # Override default
                    "WIDTH": "64"   # Override default
                }
            )
        ]
    )
    
    # Create design and add modules
    design = Design()
    design.add_module(fifo_module)
    design.add_module(top_module)
    
    # Build hierarchy
    builder = HierarchyBuilder(design)
    root = builder.build("top")
    
    # Verify child parameters
    assert len(root.children) == 1
    child = root.children[0]
    assert child.parameters["DEPTH"] == 256  # Overridden value
    assert child.parameters["WIDTH"] == 64   # Overridden value
    assert child.parameters["ADDR_WIDTH"] == 8  # Recalculated: log2(256) = 8
