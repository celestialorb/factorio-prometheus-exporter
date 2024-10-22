#!/usr/local/bin/python
"""Module defining the entrypoint to the Prometheus exporter."""

from __future__ import annotations

import json
import pathlib
import threading
import time
from typing import Any, Generator

import click
import loguru
import prometheus_client
import prometheus_client.core
import prometheus_client.registry
from prometheus_client.metrics_core import CounterMetricFamily, GaugeMetricFamily

LOGGER = loguru.logger.opt(colors=True)


class FactorioCollector(prometheus_client.registry.Collector):
    """Collector for the Factorio metrics."""

    metrics_data: dict
    metrics_lock: threading.Lock
    metrics_path: pathlib.Path

    def __init__(self: FactorioCollector, metrics_path: pathlib.Path) -> None:
        """Initialize the collector with the path to the metrics file."""
        self.metrics_data = {}
        self.metrics_lock = threading.Lock()
        self.metrics_path = metrics_path

    @staticmethod
    def __get_exporter_error_metric(*, successful: bool) -> GaugeMetricFamily:
        return prometheus_client.metrics_core.GaugeMetricFamily(
            "factorio_exporter_error",
            "Indicates if there was an error collecting Factorio metrics.",
            value=int(not successful),
        )

    def __load_metrics_data(self: FactorioCollector) -> bool:
        """Read in the Factorio metric data produced by the mod.

        Returns a boolean value indicating whether or not it was able to read and parse the data.
        """
        LOGGER.info("attempting to load metrics file output from mod: {}", self.metrics_path)
        try:
            with self.metrics_path.open(mode="r", encoding="utf-8") as buffer:
                with self.metrics_lock:
                    self.metrics_data = json.load(buffer)
                LOGGER.success("loaded metrics file output from mod")
                return True
        except FileNotFoundError:
            LOGGER.exception("metrics file not found: {}", self.metrics_path)
            return False
        except PermissionError:
            LOGGER.exception("permission denied while reading file: {}", self.metrics_path)
            return False
        except json.JSONDecodeError:
            LOGGER.exception("error while parsing JSON in metrics file: {}", self.metrics_path)
            return False

    def __collect_time_metrics(self: FactorioCollector) -> Generator[Any, Any, Any]:
        """Collect metrics on game time."""
        LOGGER.debug("collecting game tick")
        current_game_tick = self.metrics_data["game"]["time"]["tick"]
        yield GaugeMetricFamily(
            "factorio_game_tick",
            "The current tick of the running Factorio game.",
            value=current_game_tick,
        )
        LOGGER.success("collected game tick")

    def __collect_player_state_metrics(self: FactorioCollector) -> Generator[Any, Any, Any]:
        """Collect metrics on player states."""
        player_connection_states = GaugeMetricFamily(
            "factorio_player_connected",
            "The current connection state of the player.",
            labels=["username"],
        )
        for username, state in self.metrics_data["players"].items():
            player_connection_states.add_metric(
                labels=[username],
                value=int(state["connected"]),
            )
        yield player_connection_states
        LOGGER.debug("collected player connection state metrics")

    def __collect_force_metrics(self: FactorioCollector) -> Generator[Any, Any, Any]:
        """Collect metrics on prototype production and consumption and research per force."""
        force_consumption_stats = CounterMetricFamily(
            name="factorio_force_prototype_consumption",
            documentation="The total consumption of a given prototype for a force.",
            labels=["force", "prototype", "surface", "type"],
        )
        force_production_stats = CounterMetricFamily(
            name="factorio_force_prototype_production",
            documentation="The total production of a given prototype for a force.",
            labels=["force", "prototype", "surface", "type"],
        )
        force_research_progress = GaugeMetricFamily(
            name="factorio_force_research_progress",
            documentation="The current research progress percentage (0-1) for a force.",
            labels=["force"],
        )
        for surface_name in self.metrics_data["surfaces"]:
            for force_name, force_data in self.metrics_data["forces"].items():
                for type_name, prototypes in force_data.items():
                    if type_name == "research":
                        force_research_progress.add_metric(
                            labels=[force_name],
                            value=force_data["research"]["progress"],
                        )

                    if type_name in {"fluids", "items"}:
                        for prototype_name, production in prototypes[surface_name].items():
                            force_consumption_stats.add_metric(
                                labels=[force_name, prototype_name, surface_name, type_name],
                                value=production["consumption"],
                            )
                            force_production_stats.add_metric(
                                labels=[force_name, prototype_name, surface_name, type_name],
                                value=production["production"],
                            )
        yield force_consumption_stats
        LOGGER.debug("collected force consumption metrics")
        yield force_production_stats
        LOGGER.debug("collected force production metrics")
        yield force_research_progress
        LOGGER.debug("collected force research metrics")

    def __collect_pollution_metrics(self: FactorioCollector) -> Generator[Any, Any, Any]:
        """Collect metrics on pollution production from entities per surface."""
        pollution_production_stats = GaugeMetricFamily(
            name="factorio_pollution_production",
            documentation="The pollution produced or consumed from various sources.",
            labels=["source", "surface"],
        )
        for surface, surface_data in self.metrics_data["pollution"].items():
            for entity, pollution in surface_data.items():
                pollution_production_stats.add_metric(labels=[entity, surface], value=pollution)
        yield pollution_production_stats
        LOGGER.debug("collected pollution production metrics")

    def __collect_surface_metrics(self: FactorioCollector) -> Generator[Any, Any, Any]:
        """Collect metrics on total surface pollution and properties."""
        surface_pollution_total = GaugeMetricFamily(
            name="factorio_surface_pollution_total",
            documentation="The total pollution on a given surface.",
            labels=["surface"],
        )
        surface_ticks_per_day = GaugeMetricFamily(
            name="factorio_surface_ticks_per_day",
            documentation="The number of ticks per day on a given surface.",
            labels=["surface"],
        )
        for name, surface in self.metrics_data["surfaces"].items():
            surface_pollution_total.add_metric(
                labels=[name],
                value=surface["pollution"],
            )
            surface_ticks_per_day.add_metric(
                labels=[name],
                value=surface["ticks_per_day"],
            )
        yield surface_pollution_total
        LOGGER.debug("collected surface pollution metrics")
        yield surface_ticks_per_day
        LOGGER.debug("collected surface tick metrics")

    def __collect_entity_metrics(self: FactorioCollector) -> Generator[Any, Any, Any]:
        """Collect metrics on total count of entities."""
        entity_count_stats = GaugeMetricFamily(
            name="factorio_entity_count",
            documentation="The total number of entities.",
            labels=["force", "name", "surface"],
        )
        for surface_name, surface in self.metrics_data["surfaces"].items():
            for entity_name, count in surface["entities"].items():
                entity_count_stats.add_metric(
                    labels=["player", entity_name, surface_name],
                    value=count,
                )
        yield entity_count_stats
        LOGGER.debug("collected entity count metrics")

    def __collect_rocket_metrics(self: FactorioCollector) -> Generator[Any, Any, Any]:
        """Collect the rocket launch metrics."""
        # Declare the rocket launch metrics.
        rockets_launched_count = GaugeMetricFamily(
            name="factorio_rockets_launched",
            documentation="The total number of rockets launched.",
            labels=["force"],
        )
        items_launched_count = GaugeMetricFamily(
            name="factorio_items_launched",
            documentation="The total number of items launched in rockets.",
            labels=["force", "name"],
        )

        # Populate the rocket launch metrics.
        rockets_launched_count.add_metric(
            labels=["player"],
            value=self.metrics_data["forces"]["player"]["rockets"]["launches"],
        )
        for name, launched in self.metrics_data["forces"]["player"]["rockets"]["items"].items():
            items_launched_count.add_metric(
                labels=["player", name],
                value=launched,
            )
        yield rockets_launched_count
        yield items_launched_count

    def collect(self: FactorioCollector) -> Generator[Any, Any, Any]:
        """Collect the Factorio metrics from the mod's output file."""
        # Attempt to load and parse the metric data produced by the mod.
        success = self.__load_metrics_data()
        yield self.__get_exporter_error_metric(successful=success)

        LOGGER.debug("locking metrics data")
        with self.metrics_lock:
            LOGGER.debug("collecting metrics")
            yield from self.__collect_time_metrics()
            yield from self.__collect_player_state_metrics()
            yield from self.__collect_force_metrics()
            yield from self.__collect_pollution_metrics()
            yield from self.__collect_surface_metrics()
            yield from self.__collect_entity_metrics()
            yield from self.__collect_rocket_metrics()
            LOGGER.debug("collected metrics")


@click.group()
def cli() -> None:
    """Entrypoint for the Prometheus exporter."""


@cli.command()
@click.option(
    "--metrics-path",
    type=click.Path(exists=False),
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
    """Start the Factorio Prometheus exporter."""
    # Unregister the default collectors.
    prometheus_client.core.REGISTRY.unregister(prometheus_client.GC_COLLECTOR)
    prometheus_client.core.REGISTRY.unregister(prometheus_client.PLATFORM_COLLECTOR)
    prometheus_client.core.REGISTRY.unregister(prometheus_client.PROCESS_COLLECTOR)

    # Register the Factorio collector.
    LOGGER.info("registering Factorio metrics collector")
    prometheus_client.core.REGISTRY.register(
        FactorioCollector(metrics_path=pathlib.Path(metrics_path)),
    )

    # Start the Prometheus server in a thread.
    LOGGER.info("starting Prometheus HTTP server")
    prometheus_client.start_http_server(metrics_port)

    LOGGER.info("Prometheus HTTP server started, waiting for interruption")
    # Keep looping until we receive an interruption.
    try:
        while True:
            time.sleep(1)
    finally:
        pass


if __name__ == "__main__":
    cli()
