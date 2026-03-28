-- distributed under the mit license
-- https://opensource.org/licenses/mit-license.php

library IEEE;
use IEEE.STD_LOGIC_1164.ALL;

entity constants_in_arch is
    generic (
        WIDTH : integer := 8
    );
    port (
        clk : in  STD_LOGIC;
        data : out STD_LOGIC_VECTOR(WIDTH-1 downto 0)
    );
end constants_in_arch;

architecture rtl of constants_in_arch is
    -- Constants derived from generics
    constant DOUBLE_WIDTH : integer := WIDTH * 2;
    constant FIXED_DEPTH : integer := 16;
    
    -- Signals using constants
    signal internal_reg : STD_LOGIC_VECTOR(DOUBLE_WIDTH-1 downto 0);
    signal internal_mem : STD_LOGIC_VECTOR(FIXED_DEPTH-1 downto 0);
begin
    -- Assignments using parameters and constants
    data <= internal_reg(WIDTH-1 downto 0);
end rtl;
