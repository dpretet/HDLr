#!/usr/bin/env python3
# coding: utf-8

"""Unit tests for VHDL IR Builder methods."""

import pytest
from hdlr.frontend.vhdl.ir_builder import VhdlIRBuilder
from hdlr.ir.module import Module
from hdlr.ir.port import Port
from hdlr.ir.signal import Signal
from hdlr.ir.parameter import Parameter
from hdlr.ir.instance import Instance
import tree_sitter_vhdl
from tree_sitter import Language, Parser


# Initialize VHDL parser for testing
VHDL_LANGUAGE = Language(tree_sitter_vhdl.language())


def parse_vhdl(code):
    """Helper function to parse VHDL code."""
    parser = Parser(VHDL_LANGUAGE)
    tree = parser.parse(bytes(code, 'utf8'))
    builder = VhdlIRBuilder()
    return builder.build(tree)


class TestVhdlIRBuilder:
    """Test VHDL IR Builder methods."""
    
    def test_extract_entity_name(self):
        """Test entity name extraction."""
        code = """
        entity test_entity is
        end test_entity;
        """
        modules = parse_vhdl(code)
        assert len(modules) == 1
        assert modules[0].name == "test_entity"
    
    def test_extract_simple_port(self):
        """Test simple port extraction."""
        code = """
        entity simple_ports is
            port (
                clk : in STD_LOGIC;
                reset : in STD_LOGIC
            );
        end simple_ports;
        """
        modules = parse_vhdl(code)
        entity = modules[0]
        
        assert len(entity.ports) == 2
        port_names = [p.name for p in entity.ports]
        assert "clk" in port_names
        assert "reset" in port_names
        
        # Check directions
        clk_port = next(p for p in entity.ports if p.name == "clk")
        assert clk_port.direction == "input"
    
    def test_extract_port_with_width(self):
        """Test port extraction with width."""
        code = """
        entity ports_with_width is
            port (
                data : in STD_LOGIC_VECTOR(7 downto 0)
            );
        end ports_with_width;
        """
        modules = parse_vhdl(code)
        entity = modules[0]
        
        assert len(entity.ports) == 1
        data_port = entity.ports[0]
        assert data_port.name == "data"
        assert data_port.width_str == ("7", "0")
    
    def test_extract_parameter(self):
        """Test parameter extraction."""
        code = """
        entity with_params is
            generic (
                WIDTH : integer := 8;
                DEPTH : integer := 4
            );
            port (
                clk : in STD_LOGIC
            );
        end with_params;
        """
        modules = parse_vhdl(code)
        entity = modules[0]
        
        assert len(entity.parameters) == 2
        param_names = [p.name for p in entity.parameters]
        assert "WIDTH" in param_names
        assert "DEPTH" in param_names
        
        # Check values
        width_param = next(p for p in entity.parameters if p.name == "WIDTH")
        assert width_param.value_str == "8"
    
    def test_extract_signal(self):
        """Test signal extraction from architecture."""
        code = """
        library IEEE;
        use IEEE.STD_LOGIC_1164.ALL;
        
        entity test_signals is
        end test_signals;
        
        architecture rtl of test_signals is
            signal clk : STD_LOGIC;
            signal data : STD_LOGIC_VECTOR(7 downto 0);
        begin
        end rtl;
        """
        modules = parse_vhdl(code)
        entity = modules[0]
        
        assert len(entity.signals) == 2
        signal_names = [s.name for s in entity.signals]
        assert "clk" in signal_names
        assert "data" in signal_names
        
        # Check widths
        data_signal = next(s for s in entity.signals if s.name == "data")
        assert data_signal.width_str == ("7", "0")
    
    def test_extract_instance(self):
        """Test instance extraction."""
        code = """
        library IEEE;
        use IEEE.STD_LOGIC_1164.ALL;
        
        entity top is
        end top;
        
        architecture rtl of top is
            component submodule is
                port (
                    clk : in STD_LOGIC;
                    data : in STD_LOGIC_VECTOR(7 downto 0)
                );
            end component;
        begin
            u_sub: submodule
                port map (
                    clk => clk,
                    data => data
                );
        end rtl;
        
        entity submodule is
            port (
                clk : in STD_LOGIC;
                data : in STD_LOGIC_VECTOR(7 downto 0)
            );
        end submodule;
        """
        modules = parse_vhdl(code)
        top = next(m for m in modules if m.name == "top")
        
        assert len(top.instances) == 1
        instance = top.instances[0]
        assert instance.name == "u_sub"
        assert instance.module_name == "submodule"
        assert len(instance.connections) == 2
        assert "clk" in instance.connections
        assert "data" in instance.connections
    
    def test_extract_instance_with_parameters(self):
        """Test instance extraction with parameters."""
        code = """
        library IEEE;
        use IEEE.STD_LOGIC_1164.ALL;
        
        entity top is
        end top;
        
        architecture rtl of top is
            component submodule is
                generic (
                    WIDTH : integer := 8
                );
                port (
                    clk : in STD_LOGIC
                );
            end component;
        begin
            u_sub: submodule
                generic map (
                    WIDTH => 16
                )
                port map (
                    clk => clk
                );
        end rtl;
        
        entity submodule is
            generic (
                WIDTH : integer := 8
            );
            port (
                clk : in STD_LOGIC
            );
        end submodule;
        """
        modules = parse_vhdl(code)
        top = next(m for m in modules if m.name == "top")
        
        assert len(top.instances) == 1
        instance = top.instances[0]
        assert instance.name == "u_sub"
        assert "WIDTH" in instance.parameters
        assert instance.parameters["WIDTH"] == "16"
    
    def test_for_generate_with_instance(self):
        """Test for generate statement with instance."""
        code = """
        library IEEE;
        use IEEE.STD_LOGIC_1164.ALL;
        
        entity top is
        end top;
        
        architecture rtl of top is
        begin
            gen_block: for i in 0 to 3 generate
                u_sub: entity work.sub
                    port map (
                        clk => clk
                    );
            end generate;
        end rtl;
        
        entity sub is
            port (
                clk : in STD_LOGIC
            );
        end sub;
        """
        modules = parse_vhdl(code)
        top = next(m for m in modules if m.name == "top")
        
        assert len(top.instances) == 1
        instance = top.instances[0]
        assert instance.name == "u_sub"
        assert instance.condition == "i < 3"  # for i in 0 to 3 generates i < 3 condition
    
    def test_signal_in_generate_block(self):
        """Test signal declared inside generate block."""
        code = """
        library IEEE;
        use IEEE.STD_LOGIC_1164.ALL;
        
        entity top is
        end top;
        
        architecture rtl of top is
        begin
            gen_block: for i in 0 to 3 generate
                signal reg : STD_LOGIC_VECTOR(7 downto 0);
            end generate;
        end rtl;
        """
        modules = parse_vhdl(code)
        top = next(m for m in modules if m.name == "top")
        
        assert len(top.signals) == 1
        signal = top.signals[0]
        assert signal.name == "reg"
        assert signal.condition == "i < 3"  # for i in 0 to 3 generates i < 3 condition
        assert signal.width_str == ("7", "0")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
