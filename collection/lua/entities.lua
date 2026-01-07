-- Lua script to be sent along as an RCON command to gather statistics and
-- report back metrics on the given world.
local response = {}
response["status"] = 200

local metrics = {}
metrics["forces"] = {}
metrics["forces"]["player"] = {}

-- Collect entities for the ONLY player force for each surface.
-- We only want to collect for the player force because collecting entities for
-- standard forces (like the neutral force) is very process intensive.
for _, surface in pairs(game.surfaces) do
  metrics["forces"]["player"][surface.name] = {}
  local entities = surface.find_entities_filtered({force = "player"})
  metrics["forces"]["player"][surface.name]["entities"] = {}
  setmetatable(metrics["forces"]["player"][surface.name]["entities"], { __index = function() return 0 end })
  for _, entity in pairs(entities) do
    metrics["forces"]["player"][surface.name]["entities"][entity.name] = 1 + metrics["forces"]["player"][surface.name]["entities"][entity.name]
  end
end

response["metrics"] = metrics
rcon.print(helpers.table_to_json(response))
