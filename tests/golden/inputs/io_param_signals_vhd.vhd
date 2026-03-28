-- distributed under the mit license
-- https://opensource.org/licenses/mit-license.php

library IEEE;
use IEEE.STD_LOGIC_1164.ALL;

entity io_param_signals_sv is
    generic (
        NAME : integer := 0
    );
    port (
        aclk : in  STD_LOGIC;
        aresetn : in  STD_LOGIC;
        encoded : out STD_LOGIC;
        encoded1 : out STD_LOGIC_VECTOR(3 downto 0);
        encoded2 : out STD_LOGIC_VECTOR(3 downto 0)
    );
end io_param_signals_sv;

architecture rtl of io_param_signals_sv is
    signal register0 : STD_LOGIC;
    signal register1 : STD_LOGIC_VECTOR(31 downto 0);
    signal register2 : STD_LOGIC_VECTOR(31 downto 0);

begin
end rtl;