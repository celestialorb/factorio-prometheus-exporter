-- Lua script to be sent along as an RCON command to gather statistics and
-- report back metrics on the given world.
local response = {}
response["status"] = 200

local metrics = {}
metrics["forces"] = {}

for _, force in pairs(game.forces) do
  metrics["forces"][force.name] = {}
  for _, surface in pairs(game.surfaces) do
    -- Collect metrics on prototype production and consumption for the given force and surface.
    metrics["forces"][force.name][surface.name] = {}
    metrics["forces"][force.name][surface.name]["prototypes"] = {}
    local production = game.forces[force.name].get_item_production_statistics(surface.name)
    for _, item in pairs(prototypes.item) do
      metrics["forces"][force.name][surface.name]["prototypes"][item.name] = {}
      metrics["forces"][force.name][surface.name]["prototypes"][item.name]["production"] = production.get_input_count(item.name)
      metrics["forces"][force.name][surface.name]["prototypes"][item.name]["consumption"] = production.get_output_count(item.name)
      metrics["forces"][force.name][surface.name]["prototypes"][item.name]["type"] = item.type
    end
  end
end

response["metrics"] = metrics
rcon.print(helpers.table_to_json(response))
