-- distributed under the mit license
-- https://opensource.org/licenses/mit-license.php

library IEEE;
use IEEE.STD_LOGIC_1164.ALL;

entity multi_instance_sv is
    port (
        a : in  STD_LOGIC;
        b : in  STD_LOGIC;
        y : out STD_LOGIC
    );
end multi_instance_sv;

architecture rtl of multi_instance_sv is
    component submodule is
        generic (
            WIDTH : integer := 8
        );
        port (
            clk : in  STD_LOGIC;
            data : in  STD_LOGIC_VECTOR(WIDTH-1 downto 0)
        );
    end component;

    signal clk : STD_LOGIC;
    signal data : STD_LOGIC_VECTOR(7 downto 0);

begin
    u_sub1: submodule
        generic map (
            WIDTH => 8
        )
        port map (
            clk => clk,
            data => data
        );

    u_sub2: submodule
        generic map (
            WIDTH => 8
        )
        port map (
            clk => clk,
            data => data
        );

end rtl;