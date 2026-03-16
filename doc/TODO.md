# TODO Dev Plan

- [X] Support parameters, signals, module, instances
- [X] Support verilog
- [X] Support systemverilog
- [X] Ajouter une testsuite
    - [X] Unit tests
    - [X] Golden tests
- [/] Support des parameters dans le body et les localparam
    - deux sections ? body & header ? Voir comment resoudre les valeurs proprement
- [ ] Support des generate et des instances et parameter signaux dessous
- [ ] Support de signaux a deux dimensions
- [ ] Support VHDL
- [X] Add packaging for Github release
- [ ] Deploy in brew, pypi and CURL way
- [ ] Add instance drop command
- [ ] Extraire les horloges, reset et les assigner aux outputs et signaux
- [ ] CDC and RDC analysis
- [ ] Basic linter to check unknown signal (io ou signal unknown but used on instance connection)
- [ ] SystemVerilogParser extracts wire/reg in logic. TBD if can be an issue
