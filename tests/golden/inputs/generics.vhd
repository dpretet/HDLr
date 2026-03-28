-- distributed under the mit license
-- https://opensource.org/licenses/mit-license.php

library IEEE;
use IEEE.STD_LOGIC_1164.ALL;

entity generics is
    generic (
        NAME : integer := 0;
        WIDE : integer := 4;
        WIDTH : integer := 8
    );
    port (
        a : in  STD_LOGIC;
        b : out STD_LOGIC
    );
end generics;

architecture rtl of generics is
    -- Additional generics in architecture
    constant DEPTH : integer := 16;  -- Moved from entity to architecture
begin
end rtl;
