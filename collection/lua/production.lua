-- Lua script to be sent along as an RCON command to gather statistics and
-- report back metrics on the given world.
local response = {}
response["status"] = 200

local metrics = {}
metrics["forces"] = {}

for _, force in pairs(game.forces) do
  metrics["forces"][force.name] = {}
  for _, surface in pairs(game.surfaces) do
    metrics["forces"][force.name][surface.name] = {}

    -- Collect metrics on production and consumption of item and fluid.
    metrics["forces"][force.name][surface.name]["prototypes"] = {}
    local production = game.forces[force.name].get_item_production_statistics(surface.name)
    local totals = production.input_counts
    for item_name, _ in pairs(totals) do
      metrics["forces"][force.name][surface.name]["prototypes"][item_name] = {}
      metrics["forces"][force.name][surface.name]["prototypes"][item_name]["production"] = production.get_input_count(item_name)
      metrics["forces"][force.name][surface.name]["prototypes"][item_name]["consumption"] = production.get_output_count(item_name)
    end
    local fluid_production = game.forces[force.name].get_fluid_production_statistics(surface.name)
    local fluid_totals = fluid_production.input_counts
    for item_name, _ in pairs(fluid_totals) do
      metrics["forces"][force.name][surface.name]["prototypes"][item_name] = {}
      metrics["forces"][force.name][surface.name]["prototypes"][item_name]["production"] = fluid_production.get_input_count(item_name)
      metrics["forces"][force.name][surface.name]["prototypes"][item_name]["consumption"] = fluid_production.get_output_count(item_name)
    end
  end
end

response["metrics"] = metrics
rcon.print(helpers.table_to_json(response))
