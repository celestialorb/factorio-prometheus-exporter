# Factorio Prometheus Exporter

A mod for Factorio to produce a variety of Prometheus metrics.

## Design

The project produces a single artifact, a container image. This image will run
the Prometheus exporter which can then be scraped by Prometheus itself.

## Artifacts

[The container image](https://github.com/celestialorb/factorio-prometheus-exporter/pkgs/container/factorio-prometheus-exporter)
that sends RCON commands and reads the RCON responses is publicly available for download.

### Operating

Parameters can be supplied to the Prometheus exporter process via the CLI or by
environment variables. Usage of the CLI parameters is encouraged over
environment variables with the exception of the RCON password parameter.

Basic help with usage can be obtained via the `--help` flag:

`/opt/exporter/exporter.py --help` or `/opt/exporter/exporter.py run --help`

```text
$ /opt/exporter/exporter.py run --help
                                                                                                                              
 Usage: exporter.py run [OPTIONS]                                                                                             
                                                                                                                              
 Start the Factorio Prometheus exporter.                                                                                      
                                                                                                                              
╭─ Options ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --metrics-port     INTEGER  The port to expose the metrics endpoint on, defaults to 9102.                                  │
│ --rcon-address     TEXT     The address for the Factorio server, defaults to localhost.                                    │
│ --rcon-port        INTEGER  The RCON port for the Factorio server, defaults to 27015.                                      │
│ --rcon-password    TEXT     The RCON password for the server, defaults to attempting to read it from the local config.     │
│ --help                      Show this message and exit.                                                                    │
╰────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

#### Logging

This project makes use of [`loguru`](https://github.com/Delgan/loguru) as the
logging solution. The logging level can be controlled via the `LOGURU_LEVEL`
environment variable. For example, to set the logging level to `INFO`, simply
set `LOGURU_LEVEL=INFO` in your environment.

#### Example Usage

Run the Prometheus exporter exposed on `9103` that pulls metrics from the
Factorio server running at `factorio.example.org`.
```sh
/opt/exporter/exporter.py run --metrics-port 9103 --rcon-address factorio.example.org
```

The RCON password can be supplied via the environment variable
`FACTORIO_PROMETHEUS_EXPORTER_RUN_RCON_PASSWORD`
(or via the `--rcon-password` CLI argument).

## Metrics

Metrics are grouped by category onto various endpoints. There is an endpoint
that returns all metrics, but be warned that collecting all metrics at the same
time may result in performance issues.

### All Metrics

The endpoint that collects and returns all Prometheus metrics is located at
`/metrics/all`.

#### Time Metrics

The endpoint that returns time related metrics is located at `/metrics/time`.
Below is a table of time-related metrics returned by this endpoint.

| Metric                           | Labels    | Description                                                |
| -------------------------------- | --------- | ---------------------------------------------------------- |
| `factorio_game_tick`             | N/A       | The game tick the metrics were recorded at.                |
| `factorio_game_ticks_played`     | N/A       | The number of ticks executed of the running Factorio game. |
| `factorio_game_ticks_paused`     | N/A       | Whether or not the game is currently paused.               |
| `factorio_surface_ticks_per_day` | `surface` | The total number of ticks per day across the surface.      |

#### Player Metrics

The endpoint that returns player related metrics is located at `/metrics/player`.
Below is a table of player-related metrics returned by this endpoint.

| Metric                      | Labels     | Description                             |
| --------------------------- | ---------- | --------------------------------------- |
| `factorio_player_connected` | `username` | Whether or not the player is connected. |

#### Launch Metrics

The endpoint that returns rocket launch related metrics is located at `/metrics/launches`.
Below is a table of launch-related metrics returned by this endpoint.

| Metric                      | Labels          | Description                                       |
| --------------------------- | --------------- | ------------------------------------------------- |
| `factorio_items_launched`   | `force`, `name` | The total number of items launched for a force.   |
| `factorio_rockets_launched` | `force`         | The total number of rockets launched for a force. |

#### Research Metrics

The endpoint that returns research related metrics is located at `/metrics/research`.
Below is a table of research-related metrics returned by this endpoint.

| Metric                             | Labels  | Description                                                       |
| ---------------------------------- | ------- | ----------------------------------------------------------------- |
| `factorio_force_research_progress` | `force` | The current research progress percentage (0-1) for a given force. |

#### Production Metrics

The endpoint that returns production related metrics is located at `/metrics/production`.
Below is a table of production-related metrics returned by this endpoint.

| Metric                                       | Labels                                  | Description                                                   |
| -------------------------------------------- | --------------------------------------- | ------------------------------------------------------------- |
| `factorio_force_prototype_consumption_total` | `force`, `prototype`, `surface`, `type` | The total consumption of prototypes for a force for surface.  |
| `factorio_force_prototype_production_total`  | `force`, `prototype`, `surface`, `type` | The total production of prototypes for a force for a surface. |

#### Entity Metrics

The endpoint that returns entity related metrics is located at `/metrics/entity`.
Below is a table of entity-related metrics returned by this endpoint.

| Metric                  | Labels                     | Description                                            |
| ----------------------- | -------------------------- | ------------------------------------------------------ |
| `factorio_entity_count` | `force`, `name`, `surface` | The total number of entities for a force on a surface. |

#### Pollution Metrics

The endpoint that returns pollution related metrics is located at `/metrics/pollution`.
Below is a table of pollution-related metrics returned by this endpoint.

| Metric                             | Labels              | Description                                                              |
| ---------------------------------- | ------------------- | ------------------------------------------------------------------------ |
| `factorio_pollution_consumption`   | `source`, `surface` | The current pollution consumption total for a given source on a surface. |
| `factorio_pollution_production`    | `source`, `surface` | The current pollution production total for a given source on a surface.  |
| `factorio_surface_pollution_total` | `surface`           | The total pollution across the surface.                                  |
