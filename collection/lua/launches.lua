-- Lua script to be sent along as an RCON command to gather statistics and
-- report back metrics on the given world.
local response = {}
response["status"] = 200

local metrics = {}
metrics["forces"] = {}
for _, force in pairs(game.forces) do
  metrics["forces"][force.name] = {}

  -- Collect metrics on rocket launches for the given force.
  metrics["forces"][force.name]["launches"] = {}
  metrics["forces"][force.name]["launches"]["count"] = game.forces[force.name].rockets_launched  
  metrics["forces"][force.name]["launches"]["items"] = {}
  for _, item in pairs(game.forces[force.name].items_launched) do
    metrics["forces"][force.name]["launches"]["items"][item.name] = item.count
  end
end

response["metrics"] = metrics
rcon.print(helpers.table_to_json(response))
