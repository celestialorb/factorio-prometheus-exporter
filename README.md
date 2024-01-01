# factorio-prometheus-exporter

A mod for Factorio to produce a variety of Prometheus metrics.

## Design

This project produces two artifacts: the first being a ZIP archive of the
Factorio mod, and the second being a container image to read in the output of
the mod and expose Prometheus metrics on a web endpoint.

## Metrics

Below is a table of metrics that are exported in this version of the exporter.

| Metric                                       | Labels                       | Description                                                                             |
| -------------------------------------------- | ---------------------------- | --------------------------------------------------------------------------------------- |
| `factorio_entity_count`                      | `force`, `name`, `surface`   | The total number of entities for a force on a surface.                                  |
| `factorio_force_prototype_consumption_total` | `force`, `prototype`, `type` | The total consumption of prototypes for a force.                                        |
| `factorio_force_prototype_production_total`  | `force`, `prototype`, `type` | The total production of prototypes for a force.                                         |
| `factorio_force_research_progress`           | `force`                      | The current research progress percentage (0-1) for a given force.                       |
| `factorio_game_tick`                         | N/A                          | The game tick the metrics were recorded at.                                             |
| `factorio_player_connected`                  | `username`                   | Whether or not the player is connected.                                                 |
| `factorio_pollution_production`              | `source`                     | The current pollution production (or consumption if negative) total for a given source. |
| `factorio_surface_pollution_total`           | `surface`                    | The total pollution across the surface.                                                 |
| `factorio_surface_ticks_per_day`             | `surface`                    | The total number of ticks per day across the surface.                                   |
