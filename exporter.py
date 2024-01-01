#!/usr/local/bin/python
"""Module defining the entrypoint to the Prometheus exporter."""
from __future__ import annotations

import json
import pathlib
import time

import click
import prometheus_client
import prometheus_client.core
import prometheus_client.metrics_core
import prometheus_client.registry


class FactorioCollector(prometheus_client.registry.Collector):
    """Collector for the Factorio metrics."""

    metrics_path: str = ""

    def __init__(self: FactorioCollector, metrics_path: str) -> None:
        self.metrics_path = metrics_path

    def collect(self: FactorioCollector) -> None:
        """Collects the Factorio metrics from the mod's output file."""
        with open(file=self.metrics_path, mode="r", encoding="utf-8") as f:
            data = json.load(f)

        # Collect the current game tick.
        yield prometheus_client.metrics_core.GaugeMetricFamily(
            "factorio_game_tick",
            "The current tick of the running Factorio game.",
            value=data["game"]["time"]["tick"],
        )

        # Collect the player states.
        player_connection_states = prometheus_client.metrics_core.GaugeMetricFamily(
            "factorio_player_connected",
            "The current connection state of the player.",
            labels=["username"],
        )
        for username, state in data["players"].items():
            player_connection_states.add_metric(
                labels=[username],
                value=int(state["connected"]),
            )
        yield player_connection_states

        # Collect the force statistics.
        force_consumption_stats = prometheus_client.metrics_core.CounterMetricFamily(
            name="factorio_force_prototype_consumption",
            documentation="The total consumption of a given prototype for a force.",
            labels=["force", "prototype", "type"],
        )
        force_production_stats = prometheus_client.metrics_core.CounterMetricFamily(
            name="factorio_force_prototype_production",
            documentation="The total production of a given prototype for a force.",
            labels=["force", "prototype", "type"],
        )
        force_research_progress = prometheus_client.metrics_core.GaugeMetricFamily(
            name="factorio_force_research_progress",
            documentation="The current research progress percentage (0-1) for a force.",
            labels=["force"],
        )
        for force_name, force_data in data["forces"].items():
            for type_name, prototypes in force_data.items():
                if type_name == "research":
                    force_research_progress.add_metric(
                        labels=[force_name],
                        value=force_data["research"]["progress"],
                    )

                if type_name in {"fluids", "items"}:
                    for prototype_name, production in prototypes.items():
                        force_consumption_stats.add_metric(
                            labels=[force_name, prototype_name, type_name],
                            value=production["consumption"],
                        )
                        force_production_stats.add_metric(
                            labels=[force_name, prototype_name, type_name],
                            value=production["production"],
                        )
        yield force_consumption_stats
        yield force_production_stats
        yield force_research_progress

        # Collect the pollution production statistics.
        pollution_production_stats = prometheus_client.metrics_core.GaugeMetricFamily(
            name="factorio_pollution_production",
            documentation="The pollution produced or consumed from various sources.",
            labels=["source"],
        )
        for source, pollution in data["pollution"].items():
            pollution_production_stats.add_metric(labels=[source], value=pollution)
        yield pollution_production_stats

        # Collect the surface metrics.
        surface_pollution_total = prometheus_client.metrics_core.GaugeMetricFamily(
            name="factorio_surface_pollution_total",
            documentation="The total pollution on a given surface.",
            labels=["surface"],
        )
        surface_ticks_per_day = prometheus_client.metrics_core.GaugeMetricFamily(
            name="factorio_surface_ticks_per_day",
            documentation="The number of ticks per day on a given surface.",
            labels=["surface"],
        )
        for name, surface in data["surfaces"].items():
            surface_pollution_total.add_metric(
                labels=[name],
                value=surface["pollution"],
            )
            surface_ticks_per_day.add_metric(
                labels=[name],
                value=surface["ticks_per_day"],
            )
        yield surface_pollution_total
        yield surface_ticks_per_day

        # Collect the entity count metrics.
        entity_count_stats = prometheus_client.metrics_core.GaugeMetricFamily(
            name="factorio_entity_count",
            documentation="The total number of entities.",
            labels=["force", "name", "surface"],
        )
        for surface_name, surface in data["surfaces"].items():
            for entity_name, count in surface["entities"].items():
                entity_count_stats.add_metric(
                    labels=["player", entity_name, surface_name],
                    value=count,
                )
        yield entity_count_stats


@click.group()
def cli() -> None:
    """Entrypoint for the Prometheus exporter."""


@cli.command()
@click.option(
    "--metrics-path",
    default="/factorio/script-output/metrics.json",
    help="Path to watch.",
)
@click.option(
    "--metrics-port",
    type=click.INT,
    default=9102,
    help="The port to expose the metrics endpoint on.",
)
def run(metrics_path: str, metrics_port: int) -> None:
    """Starts the Factorio Prometheus exporter."""
    # Unregister the default collectors.
    prometheus_client.core.REGISTRY.unregister(prometheus_client.GC_COLLECTOR)
    prometheus_client.core.REGISTRY.unregister(prometheus_client.PLATFORM_COLLECTOR)
    prometheus_client.core.REGISTRY.unregister(prometheus_client.PROCESS_COLLECTOR)

    # Register the Factorio collector.
    prometheus_client.core.REGISTRY.register(
        FactorioCollector(metrics_path=metrics_path),
    )

    # Start the Prometheus server in a thread.
    prometheus_client.start_http_server(metrics_port)

    # Keep looping until we receive an interruption.
    try:
        while True:
            time.sleep(1)
    finally:
        pass


if __name__ == "__main__":
    cli()
