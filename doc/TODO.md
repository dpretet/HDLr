# TODO Dev Plan
- [/] Support Rich API
- [ ] Review the vide coded parsers and clean them up
- [ ] Ajouter les tests de la commande elaboration
- [ ] Support de signaux a deux dimensions
- [ ] Support VHDL
- [ ] Add instance drop command
- [ ] Deploy in brew, pypi and w/ CURL way
- [ ] Extraire les horloges, reset et les assigner aux outputs et signaux
- [ ] CDC analysis

# Backlog
- [ ] SystemVerilogParser extracts wire/reg in logic. TBD if can be an issue
- [ ] Basic linter to check unknown signal (io ou signal unknown but used on instance connection)
- [ ] RDC analysis

# Done
- [X] Ajouter un test pour les operateurs ternaires
- [X] Support des generate et des instances et parameter signaux dessous
- [X] Add packaging for Github release
- [X] Support parameters, signals, module, instances
- [X] Support verilog
- [X] Support systemverilog
- [X] Ajouter une testsuite
    - [X] Unit tests
    - [X] Golden tests
- [X] Support des parameters dans le body et les localparam
