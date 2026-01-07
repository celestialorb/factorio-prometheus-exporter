-- Lua script to be sent along as an RCON command to determine if the game
-- should be paused so metrics can be collected when without advancing the game
-- state.

-- If no one is online, simply pause the game.
game.tick_paused = (#game.connected_players <= 0)
