-- Lua script to be sent along as an RCON command to gather statistics and
-- report back metrics on the given world.
local response = {}
response["status"] = 200

local metrics = {}
metrics["forces"] = {}
metrics["forces"]["player"] = {}

for _, surface in pairs(game.surfaces) do

  -- Collect metrics on electric networks.
  metrics["forces"]["player"][surface.name] = {}
  -- Gather the electric pole type. Will return all poles type on the surface.
  local entities_planets = surface.find_entities_filtered({force = "player", type = {"electric-pole"}})

  -- Gather the platforms entities for space platforms electricity networks.
  local entities_platform = surface.find_entities_filtered({force = "player", type = {"space-platform-hub"}})

  -- Get the first electric pole type entity on the surface.
  if entities_planets[1] ~= nil then
    -- Every electric pole return the same electric network statistics on the surfaces.
    local electric_network = entities_planets[1].electric_network_statistics
    metrics["forces"]["player"][surface.name]["production"] = {}
    metrics["forces"]["player"][surface.name]["satisfaction"] = {}
    metrics["forces"]["player"][surface.name]["accumulator_charge"] = {}

    -- Collect the electric network statistics for the surface.
    for i, _ in pairs(electric_network.output_counts) do
      if i ~= nil then
        -- Returns the 10 minutes electric network production statistics. It returns the value for ticks, so you need to multiply it by 60 to get the value per minute.
        metrics["forces"]["player"][surface.name]["production"][i] = electric_network.get_flow_count{name=i, category="output", input=true, precision_index=defines.flow_precision_index.ten_minutes}
      end
    end
    for i, _ in pairs(electric_network.input_counts) do
      if i ~= nil then
        -- Returns the 10 minutes electric network satisfaction statistics. It returns the value for ticks, so you need to multiply it by 60 to get the value per minute.
        metrics["forces"]["player"][surface.name]["satisfaction"][i] = electric_network.get_flow_count{name=i, category="input", input=true, precision_index=defines.flow_precision_index.ten_minutes}
      end
    end
    for i, _ in pairs(electric_network.storage_counts) do
      if i ~= nil then
        -- Returns the 10 minutes electric network accumulator charge statistics. It returns the value for ticks, so you need to multiply it by 60 to get the value per minute.
        metrics["forces"]["player"][surface.name]["accumulator_charge"][i] = electric_network.get_flow_count{name=i, category="storage", input=true, precision_index=defines.flow_precision_index.ten_minutes}
      end
    end
  end

  -- Returns the samething as planets but for space platforms.
  if entities_platform[1] ~= nil then
    -- The network statistics is only accessible through the global electric network statistics.
    local electric_network = surface.global_electric_network_statistics
    metrics["forces"]["player"][surface.name]["production"] = {}
    metrics["forces"]["player"][surface.name]["satisfaction"] = {}
    metrics["forces"]["player"][surface.name]["accumulator_charge"] = {}
    for i, _ in pairs(electric_network.output_counts) do
      if i ~= nil then
        metrics["forces"]["player"][surface.name]["production"][i] = electric_network.get_flow_count{name=i, category="output", input=true, precision_index=defines.flow_precision_index.ten_minutes}
      end
    end
    for i, _ in pairs(electric_network.input_counts) do
      if i ~= nil then
        metrics["forces"]["player"][surface.name]["satisfaction"][i] = electric_network.get_flow_count{name=i, category="input", input=true, precision_index=defines.flow_precision_index.ten_minutes}
      end
    end
    for i, _ in pairs(electric_network.storage_counts) do
      if i ~= nil then
        metrics["forces"]["player"][surface.name]["accumulator_charge"][i] = electric_network.get_flow_count{name=i, category="storage", input=true, precision_index=defines.flow_precision_index.ten_minutes}
      end
    end
  end
end

response["metrics"] = metrics
rcon.print(helpers.table_to_json(response))