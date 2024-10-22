-- Define a variable containing all of the metric data.
local metrics = {}
metrics["game"] = {}
metrics["game"]["time"] = {}
metrics["game"]["time"]["tick"] = nil
metrics["game"]["time"]["paused"] = nil
metrics["players"] = {}
metrics["forces"] = {}
metrics["forces"]["player"] = {}
metrics["pollution"] = {}
metrics["surfaces"] = {}


local function write_metrics()
    local filename = "metrics.json"
    local json = helpers.table_to_json(metrics)
    helpers.write_file(filename, json .. "\n")
end

local function update_time_metrics()
    metrics["game"]["time"]["tick"] = game.tick
    metrics["game"]["time"]["paused"] = game.tick_paused
end

local function update_rocket_launch_metrics()
    metrics["forces"]["player"]["rockets"] = {}
    metrics["forces"]["player"]["rockets"]["items"] = {}
    metrics["forces"]["player"]["rockets"]["launches"] = game.forces["player"].rockets_launched
    for item, count in pairs(game.forces["player"].items_launched) do
        metrics["forces"]["player"]["rockets"]["items"][item] = count
    end
end

local function update_research_metrics()
    metrics["forces"]["player"]["research"] = {}
    metrics["forces"]["player"]["research"]["progress"] = game.forces["player"].research_progress
end

local function update_fluid_metrics()
    metrics["forces"]["player"]["fluids"] = {}
    for surface, _ in pairs(game.surfaces) do
        metrics["forces"]["player"]["fluids"][surface] = {}
        for name, _ in pairs(prototypes.fluid) do
            metrics["forces"]["player"]["fluids"][surface][name] = {}
            metrics["forces"]["player"]["fluids"][surface][name]["consumption"] = game.forces["player"]
                .get_fluid_production_statistics(surface)
                .get_output_count(name)
            metrics["forces"]["player"]["fluids"][surface][name]["production"] = game.forces["player"]
                .get_fluid_production_statistics(surface)
                .get_input_count(name)
        end
    end
end

local function update_item_metrics()
    metrics["forces"]["player"]["items"] = {}
    for surface, _ in pairs(game.surfaces) do
        metrics["forces"]["player"]["items"][surface] = {}
        for name, _ in pairs(prototypes.item) do
            metrics["forces"]["player"]["items"][surface][name] = {}
            metrics["forces"]["player"]["items"][surface][name]["consumption"] = game.forces["player"]
                .get_item_production_statistics(surface)
                .get_output_count(
                    name)
            metrics["forces"]["player"]["items"][surface][name]["production"] = game.forces["player"]
                .get_item_production_statistics(surface)
                .get_input_count(
                    name)
        end
    end
end

local function update_player_metrics()
    for id, player in pairs(game.players) do
        metrics["players"][player.name] = {}
        metrics["players"][player.name]["connected"] = player.connected
    end

    update_time_metrics()

    write_metrics()
end

local function update_pollution_metrics()
    for surface, _ in pairs(game.surfaces) do
        metrics["pollution"][surface] = {}
        local pollution_statistics = game.get_pollution_statistics(surface)
        for name, value in pairs(pollution_statistics.output_counts) do
            metrics["pollution"][surface][name] = -pollution_statistics.get_output_count(name)
        end
        for name, value in pairs(pollution_statistics.input_counts) do
            metrics["pollution"][surface][name] = pollution_statistics.get_input_count(name)
        end
    end
end

local function update_surface_metrics()
    for name, surface in pairs(game.surfaces) do
        metrics["surfaces"][name] = {}
        metrics["surfaces"][name]["pollution"] = surface.get_total_pollution()
        metrics["surfaces"][name]["ticks_per_day"] = surface.ticks_per_day

        metrics["surfaces"][name]["entities"] = {}
        setmetatable(metrics["surfaces"][name]["entities"], { __index = function() return 0 end })
        for _, entity in pairs(surface.find_entities_filtered { force = "player" }) do
            metrics["surfaces"][name]["entities"][entity.name] = 1 + metrics["surfaces"][name]["entities"][entity.name]
        end
    end
end

local function update_metrics()
    update_time_metrics()
    update_player_metrics()
    update_item_metrics()
    update_fluid_metrics()
    update_pollution_metrics()
    update_surface_metrics()
    update_research_metrics()
    update_rocket_launch_metrics()

    write_metrics()
end

log("prometheus exporter mod setup starting")

script.on_event(defines.events.on_player_joined_game, update_player_metrics)
script.on_event(defines.events.on_player_left_game, update_player_metrics)
script.on_event(defines.events.on_player_created, update_player_metrics)
script.on_event(defines.events.on_player_removed, update_player_metrics)
script.on_init(update_metrics)

local update_rate = settings.startup["prometheus-exporter-metrics-update-every-nth-tick"].value
script.on_nth_tick(update_rate, update_metrics)
log("prometheus exporter mod setup completed")
