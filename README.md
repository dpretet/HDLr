# HDLr - Hardware Design Language Parser & Elaborator

[![GitHub license](https://img.shields.io/github/license/dpretet/hdlr)](https://github.com/dpretet/hdlr/blob/master/LICENSE)
![Github Actions](https://github.com/dpretet/hdlr/actions/workflows/tests.yml/badge.svg)
[![GitHub issues](https://img.shields.io/github/issues/dpretet/hdlr)](https://github.com/dpretet/hdlr/issues)
[![GitHub stars](https://img.shields.io/github/stars/dpretet/hdlr)](https://github.com/dpretet/hdlr/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/dpretet/hdlr)](https://github.com/dpretet/hdlr/network)

![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![Lint](https://img.shields.io/badge/lint-ruff-blueviolet)

HDLr is a powerful tool for parsing and elaborating SystemVerilog and Verilog designs. Built on Tree-Sitter for robust parsing, HDLr provides deep insights into your hardware design hierarchy.

## Features

✅ **Dual Language Support**: Parse both SystemVerilog and Verilog files
✅ **Hierarchy Analysis**: Build complete design hierarchies with resolved parameters
✅ **Parameter Extraction**: Extract and display module parameters and localparams
✅ **Port Analysis**: Detailed port direction and width information
✅ **Instance Tracking**: Identify module instantiations and connections
✅ **Signal Detection**: Extract internal signals and their types

## Installation

### Ready-to-use Binary
Grab a pre-built binary from the [releases page](https://github.com/dpretet/HDLr/releases)

### Python Installation
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -e .
```

## Usage

### Scan Modules
```bash
hdlr scan <files_or_directories>
```

Discover all modules in your design files with detailed information about:
- Parameters and localparams
- Input/output ports with width specifications
- Internal signals
- Module instances and their connections

### Elaborate Design Hierarchy
```bash
hdlr elaborate <files_or_directories> --top <top_module_name>
```

Build and visualize the complete design hierarchy starting from your top module, showing:
- Module instantiation tree
- Parameter values at each level
- Port connections between modules

## Examples

### Basic Module Scan
```bash
hdlr scan ./rtl/design.sv
```

### Design Elaboration
```bash
hdlr elaborate ./rtl/ --top cpu_core
```

### Batch Processing
```bash
hdlr scan ./src/verilog/ ./src/systemverilog/
```

## Architecture

```
HDL Source Files → Tree-Sitter Parser → IR Builder → Design Analysis
                    (SystemVerilog/Verilog)      (Modules, Ports,
                                              Parameters,
                                              Instances)
```

## Supported Constructs

- **Modules**: ANSI and non-ANSI style module definitions
- **Parameters**: Module parameters and localparams
- **Ports**: Input/output ports with width specifications
- **Instances**: Module instantiations with parameter overrides
- **Signals**: Internal wire/reg/logic declarations
- **Generate Blocks**: Basic generate construct support

## Roadmap

- ✅ Verilog support
- ✅ SystemVerilog support
- ✅ Parameter extraction
- ✅ Instance hierarchy building
- ✅ Rich terminal visualization
- 🚧 VHDL support (planned)
- 🚧 Clock domain crossing analysis

## License

MIT License - See [LICENSE](LICENSE) for details

