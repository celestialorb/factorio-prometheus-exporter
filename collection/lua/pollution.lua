-- Lua script to be sent along as an RCON command to gather statistics and
-- report back metrics on the given world.
local response = {}
response["status"] = 200

local metrics = {}

metrics["surfaces"] = {}
for _, surface in pairs(game.surfaces) do
  -- Collect metrics on pollution production.
  metrics["surfaces"][surface.name] = {}
  metrics["surfaces"][surface.name]["pollution"] = {}
  metrics["surfaces"][surface.name]["pollution"]["production"] = {}
  metrics["surfaces"][surface.name]["pollution"]["consumption"] = {}
  metrics["surfaces"][surface.name]["pollution"]["total"] = surface.get_total_pollution()

  local pollution_statistics = game.get_pollution_statistics(surface.name)
  for name, value in pairs(pollution_statistics.input_counts) do
    metrics["surfaces"][surface.name]["pollution"]["production"][name] = value
  end
  for name, value in pairs(pollution_statistics.output_counts) do
    metrics["surfaces"][surface.name]["pollution"]["consumption"][name] = value
  end
end

response["metrics"] = metrics
rcon.print(helpers.table_to_json(response))
