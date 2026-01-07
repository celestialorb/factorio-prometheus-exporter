-- Lua script to be sent along as an RCON command to gather statistics and
-- report back metrics on the given world.
local response = {}
response["status"] = 200

local metrics = {}

-- Collect metrics on players in the game.
metrics["players"] = {}
for _, player in pairs(game.players) do
  metrics["players"][player.name] = {}
  metrics["players"][player.name]["connected"] = player.connected
end

response["metrics"] = metrics
rcon.print(helpers.table_to_json(response))
