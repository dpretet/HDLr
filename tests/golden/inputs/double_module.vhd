-- distributed under the mit license
-- https://opensource.org/licenses/mit-license.php

library IEEE;
use IEEE.STD_LOGIC_1164.ALL;

entity alu is
    port (
        a : in  STD_LOGIC;
        b : in  STD_LOGIC;
        c : out STD_LOGIC
    );
end alu;

entity top is
    port (
        x : in  STD_LOGIC;
        y : in  STD_LOGIC;
        z : out STD_LOGIC
    );
end top;
