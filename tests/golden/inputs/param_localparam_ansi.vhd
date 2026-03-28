-- distributed under the mit license
-- https://opensource.org/licenses/mit-license.php

library IEEE;
use IEEE.STD_LOGIC_1164.ALL;

entity param_localparam_ansi is
    generic (
        NAME : integer := 0;
        WIDE : integer := 4;
        WIDTH : integer := 8;
        DEPTH : integer := 16
    );
    port (
        a : in  STD_LOGIC;
        b : out STD_LOGIC
    );
end param_localparam_ansi;

architecture rtl of param_localparam_ansi is
begin
end rtl;
