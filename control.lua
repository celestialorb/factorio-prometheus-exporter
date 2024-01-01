-- Define a global variable containing all of the metric data.
metrics = {}
metrics["game"] = {}
metrics["game"]["time"] = {}
metrics["game"]["time"]["tick"] = nil
metrics["game"]["time"]["paused"] = nil
metrics["players"] = {}
metrics["forces"] = {}
metrics["forces"]["player"] = {}
metrics["pollution"] = {}
metrics["surfaces"] = {}


function write_metrics()
    local filename = "metrics.json"
    local json = game.table_to_json(metrics)
    game.write_file(filename, json .. "\n")
end

function update_research_metrics()
    metrics["forces"]["player"]["research"] = {}
    metrics["forces"]["player"]["research"]["progress"] = game.forces["player"].research_progress
end

function update_fluid_metrics()
    metrics["forces"]["player"]["fluids"] = {}
    for name, prototype in pairs(game.fluid_prototypes) do
        metrics["forces"]["player"]["fluids"][name] = {}
        metrics["forces"]["player"]["fluids"][name]["consumption"] = game.forces["player"].fluid_production_statistics
            .get_output_count(name)
        metrics["forces"]["player"]["fluids"][name]["production"] = game.forces["player"].fluid_production_statistics
            .get_input_count(name)
    end
end

function update_item_metrics()
    metrics["forces"]["player"]["items"] = {}
    for name, prototype in pairs(game.item_prototypes) do
        metrics["forces"]["player"]["items"][name] = {}
        metrics["forces"]["player"]["items"][name]["consumption"] = game.forces["player"].item_production_statistics
            .get_output_count(
                name)
        metrics["forces"]["player"]["items"][name]["production"] = game.forces["player"].item_production_statistics
            .get_input_count(
                name)
    end
end

function update_player_metrics()
    for id, player in pairs(game.players) do
        metrics["players"][player.name] = {}
        metrics["players"][player.name]["connected"] = player.connected
    end

    update_time_metrics()

    write_metrics()
end

function update_pollution_metrics()
    for name, value in pairs(game.pollution_statistics.output_counts) do
        metrics["pollution"][name] = -game.pollution_statistics.get_output_count(name)
    end
    for name, value in pairs(game.pollution_statistics.input_counts) do
        metrics["pollution"][name] = game.pollution_statistics.get_input_count(name)
    end
end

function update_time_metrics()
    metrics["game"]["time"]["tick"] = game.tick
    metrics["game"]["time"]["paused"] = game.tick_paused
end

function update_surface_metrics()
    for name, surface in pairs(game.surfaces) do
        metrics["surfaces"][name] = {}
        metrics["surfaces"][name]["pollution"] = surface.get_total_pollution()
        metrics["surfaces"][name]["ticks_per_day"] = surface.ticks_per_day

        metrics["surfaces"][name]["entities"] = {}
        setmetatable(metrics["surfaces"][name]["entities"], { __index = function() return 0 end })
        for id, entity in pairs(surface.find_entities_filtered { force = "player" }) do
            metrics["surfaces"][name]["entities"][entity.name] = 1 + metrics["surfaces"][name]["entities"][entity.name]
        end
    end
end

function update_metrics()
    update_time_metrics()
    update_item_metrics()
    update_fluid_metrics()
    update_pollution_metrics()
    update_surface_metrics()
    update_research_metrics()

    write_metrics()
end

script.on_event(defines.events.on_player_joined_game, update_player_metrics)
script.on_event(defines.events.on_player_left_game, update_player_metrics)

-- TODO: configurable interval
script.on_nth_tick(60 * 1, update_metrics)
