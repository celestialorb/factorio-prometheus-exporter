-- Lua script to be sent along as an RCON command to gather statistics and
-- report back metrics on the given world.
local response = {}
response["status"] = 200

local metrics = {}

-- Collect metrics on players in the game.
metrics["forces"] = {}
for _, force in pairs(game.forces) do
  metrics["forces"][force.name] = {}

  -- Collect metrics on research progress for the given force.
  metrics["forces"][force.name]["research"] = {}
  metrics["forces"][force.name]["research"]["progress"] = game.forces[force.name].research_progress
end

response["metrics"] = metrics
rcon.print(helpers.table_to_json(response))
