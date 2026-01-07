-- Lua script to be sent along as an RCON command to gather statistics and
-- report back metrics on the given world.
local response = {}
response["status"] = 200

local metrics = {}

-- Collect metrics on aspect of time in the game.
metrics["time"] = {}
metrics["time"]["ticks"] = {}
metrics["time"]["ticks"]["current"] = game.tick
metrics["time"]["ticks"]["played"] = game.ticks_played
metrics["time"]["ticks"]["paused"] = game.tick_paused

-- Collect metrics on time properties for the given surface.
metrics["surfaces"] = {}
for _, surface in pairs(game.surfaces) do
  metrics["surfaces"][surface.name] = {}
  metrics["surfaces"][surface.name]["time"] = {}
  metrics["surfaces"][surface.name]["time"]["ticks_per_day"] = surface.ticks_per_day
end

response["metrics"] = metrics
rcon.print(helpers.table_to_json(response))
