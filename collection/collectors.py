"""Module defining the various metric collectors for Factorio."""

from __future__ import annotations

import datetime
import json
import pathlib
import threading
import time
from typing import TYPE_CHECKING, Any, Generator

import loguru
from prometheus_client.core import CollectorRegistry, CounterMetricFamily, GaugeMetricFamily
from prometheus_client.registry import Collector
from prometheus_client.twisted import MetricsResource
from watchdog.events import FileModifiedEvent, FileSystemEventHandler
from watchdog.observers import Observer

if TYPE_CHECKING:
    import os

    from factorio_rcon import RCONClient
    from twisted.web.resource import Resource

LUA_DIRECTORY = pathlib.Path(__file__).parent.absolute() / "lua"
LOGGER = loguru.logger.opt(colors=True)
RCON_CLIENT_LOCK = threading.Lock()


class FactorioCommander(FileSystemEventHandler):
    """An object that is tied to a specific Lua script that it can invoke via RCON."""

    client: RCONClient

    def __init__(self, client: RCONClient, script_path: os.PathLike) -> None:
        """Initialize our commander object by storing the client and building the RCON command."""
        self.client = client
        script_path = pathlib.Path(script_path).absolute()
        self._build_command(script_path=script_path)

        observer = Observer()
        observer.schedule(
            event_handler=self,
            path=script_path,
            recursive=False,
            event_filter=[FileModifiedEvent],
        )
        observer.start()
        self.on_modified(event=FileModifiedEvent(src_path=script_path))

    def _build_command(self, script_path: pathlib.Path) -> str:
        self.command = f"/silent-command {script_path.read_text(encoding='utf-8')}"

    def on_modified(self, event: FileModifiedEvent) -> None:
        """Reload the Lua metrics collection script on a file modification event."""
        LOGGER.info("statistics collection script update, reloading...")
        LOGGER.debug("event: {}", event)
        self._build_command(script_path=pathlib.Path(event.src_path).absolute())

    def send(self) -> str | None:
        """Send the built command to the Factorio server over RCON."""
        return self.client.send_command(command=self.command)


class FactorioAutopauser(FactorioCommander):
    """An object that will periodically send and execute an autopause script to the Factorio server."""

    interval: datetime.timedelta
    thread: threading.Thread

    def __init__(self, client: RCONClient, interval: datetime.timedelta | None = None) -> None:
        """Initialize our Factorio autopauser."""
        if interval is None:
            interval = datetime.timedelta(milliseconds=100)
        super().__init__(client=client, script_path=LUA_DIRECTORY / "autopauser.lua")
        self.interval = interval

    def start(self) -> None:
        """Start a background thread to periodically send the autopause script to the server."""
        self.thread = threading.Thread(group=None, target=self.run, daemon=True)
        self.thread.start()

    def run(self) -> None:
        """Periodically send the autopause script to the server."""
        while True:
            with RCON_CLIENT_LOCK:
                self.send()
            time.sleep(self.interval.seconds)


class FactorioCollector(FactorioCommander, Collector):
    """Collector for the Factorio metrics."""

    client: RCONClient
    command: str
    group: str
    registry: CollectorRegistry

    def __init__(self, client: RCONClient, group: str) -> None:
        """Initialize the Factorio metrics collector."""
        self.group = group
        super().__init__(client=client, script_path=LUA_DIRECTORY / f"{self.group}.lua")
        self.registry = CollectorRegistry()
        self.registry.register(self)

    def install(self, resource: Resource) -> None:
        """Installs the Prometheus endpoint as a child of the given Twisted resource."""
        LOGGER.info("[collector.{}] installing collector", self.group)
        resource.putChild(
            path=str.encode(self.group),
            child=MetricsResource(self.registry),
        )
        LOGGER.success("[collector.{}] successfully installed collector", self.group)

    @property
    def raw(self) -> str:
        """Return the latest metric data as collected from the RCON Lua script."""
        with RCON_CLIENT_LOCK:
            response = self.client.send_command(self.command)
        LOGGER.debug("raw response: {}", response)
        return response

    @property
    def response(self) -> dict:
        """Return the latest response data parsed with JSON from the RCON Lua script."""
        return json.loads(self.raw)

    @property
    def metrics(self) -> dict:
        """Return the latest metric data parsed with JSON from the RCON Lua script."""
        return self.response["metrics"]


class FactorioTimeCollector(FactorioCollector):
    """Represents a collector that collect metrics related to the time in the Factorio server."""

    def __init__(self, client: RCONClient) -> None:
        """Initialize the time metrics collector."""
        super().__init__(client=client, group="time")

    def collect(self: FactorioCollector) -> Generator[Any, Any, Any]:
        """Collect the metrics and store them in the Prometheus collector."""
        metrics = self.metrics
        yield GaugeMetricFamily(
            "factorio_game_tick",
            "The current tick of the running Factorio game.",
            value=metrics["time"]["ticks"]["current"],
        )
        yield GaugeMetricFamily(
            "factorio_game_ticks_played",
            "The number of ticks executed of the running Factorio game.",
            value=metrics["time"]["ticks"]["played"],
        )
        yield GaugeMetricFamily(
            "factorio_game_tick_paused",
            "Whether or not the game is currently paused.",
            value=metrics["time"]["ticks"]["paused"],
        )

        surface_ticks_per_day = GaugeMetricFamily(
            "factorio_surface_ticks_per_day",
            "The total number of ticks per day across the surface.",
            labels=["surface"],
        )

        for surface, surface_data in metrics["surfaces"].items():
            surface_ticks_per_day.add_metric(
                labels=[surface],
                value=surface_data["time"]["ticks_per_day"],
            )
        yield surface_ticks_per_day


class FactorioPlayerCollector(FactorioCollector):
    """Represents a collector that collect metrics related to the players in the Factorio server."""

    def __init__(self, client: RCONClient) -> None:
        """Initialize the players metrics collector."""
        super().__init__(client=client, group="player")

    def collect(self) -> Generator[Any, Any, Any]:
        """Collect the metrics and store them in the Prometheus collector."""
        metrics = self.metrics
        player_connection_states = GaugeMetricFamily(
            "factorio_player_connected",
            "The current connection state of the player.",
            labels=["username"],
        )
        for username, state in metrics["players"].items():
            player_connection_states.add_metric(
                labels=[username],
                value=int(state["connected"]),
            )
        yield player_connection_states
        LOGGER.debug("collected player connection state metrics")


class FactorioLaunchesCollector(FactorioCollector):
    """Represents a collector that collect metrics related to rocket launches in the Factorio server."""

    def __init__(self, client: RCONClient) -> None:
        """Initialize the rocket launches metrics collector."""
        super().__init__(client=client, group="launches")

    def collect(self) -> Generator[Any, Any, Any]:
        """Collect the metrics and store them in the Prometheus collector."""
        metrics = self.metrics
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

        for force, launch_data in metrics["forces"].items():
            launches = launch_data["launches"]

            # Populate the rocket launch metrics.
            rockets_launched_count.add_metric(
                labels=[force],
                value=launches["count"],
            )
            for name, launched in launches["items"].items():
                items_launched_count.add_metric(
                    labels=[force, name],
                    value=launched,
                )
        yield rockets_launched_count
        yield items_launched_count


class FactorioResearchCollector(FactorioCollector):
    """Represents a collector that collect metrics related to research in the Factorio server."""

    def __init__(self, client: RCONClient) -> None:
        """Initialize the research metrics collector."""
        super().__init__(client=client, group="research")

    def collect(self) -> Generator[Any, Any, Any]:
        """Collect the metrics and store them in the Prometheus collector."""
        metrics = self.metrics
        force_research_progress = GaugeMetricFamily(
            name="factorio_force_research_progress",
            documentation="The current research progress percentage (0-1) for a force.",
            labels=["force"],
        )

        for force, force_data in metrics["forces"].items():
            force_research_progress.add_metric(
                labels=[force],
                value=force_data["research"]["progress"],
            )

        yield force_research_progress


class FactorioProductionCollector(FactorioCollector):
    """Represents a collector that collect metrics related to production in the Factorio server."""

    def __init__(self, client: RCONClient) -> None:
        """Initialize the production metrics collector."""
        super().__init__(client=client, group="production")

    def collect(self) -> Generator[Any, Any, Any]:
        """Collect the metrics and store them in the Prometheus collector."""
        metrics = self.metrics
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

        for force, force_data in metrics["forces"].items():
            for surface, surface_force_data in force_data.items():
                prototypes = surface_force_data["prototypes"]
                for prototype, prototype_data in prototypes.items():
                    force_consumption_stats.add_metric(
                        labels=[force, prototype, surface, prototype_data["type"]],
                        value=prototype_data["consumption"],
                    )
                    force_production_stats.add_metric(
                        labels=[force, prototype, surface, prototype_data["type"]],
                        value=prototype_data["production"],
                    )

        yield force_consumption_stats
        yield force_production_stats


class FactorioEntityCollector(FactorioCollector):
    """Represents a collector that collect metrics related to entities in the Factorio server."""

    def __init__(self, client: RCONClient) -> None:
        """Initialize the entities metrics collector."""
        super().__init__(client=client, group="entities")

    def collect(self) -> Generator[Any, Any, Any]:
        """Collect the metrics and store them in the Prometheus collector."""
        metrics = self.metrics
        entity_count_stats = GaugeMetricFamily(
            name="factorio_entity_count",
            documentation="The total number of entities.",
            labels=["force", "name", "surface"],
        )

        for force, force_data in metrics["forces"].items():
            for surface, surface_data in force_data.items():
                for entity, count in surface_data["entities"].items():
                    entity_count_stats.add_metric(
                        labels=[force, entity, surface],
                        value=count,
                    )
        yield entity_count_stats


class FactorioPollutionCollector(FactorioCollector):
    """Represents a collector that collect metrics related to pollution in the Factorio server."""

    def __init__(self, client: RCONClient) -> None:
        """Initialize the pollution metrics collector."""
        super().__init__(client=client, group="pollution")

    def collect(self) -> Generator[Any, Any, Any]:
        """Collect the metrics and store them in the Prometheus collector."""
        metrics = self.metrics
        surface_pollution_total_stats = GaugeMetricFamily(
            name="factorio_surface_pollution_total",
            documentation="The total pollution across the surface.",
            labels=["surface"],
        )
        surface_pollution_consumption = GaugeMetricFamily(
            name="factorio_pollution_consumption",
            documentation="The current pollution consumption total for a given source on a surface.",
            labels=["source", "surface"],
        )
        surface_pollution_production = GaugeMetricFamily(
            name="factorio_pollution_production",
            documentation="The current pollution production total for a given source on a surface.",
            labels=["source", "surface"],
        )

        for surface, surface_data in metrics["surfaces"].items():
            pollution_data = surface_data["pollution"]
            surface_pollution_total_stats.add_metric(
                labels=[surface],
                value=pollution_data["total"],
            )

            for entity, consumption in pollution_data["consumption"].items():
                surface_pollution_consumption.add_metric(
                    labels=[entity, surface],
                    value=consumption,
                )

            for entity, production in pollution_data["production"].items():
                surface_pollution_production.add_metric(
                    labels=[entity, surface],
                    value=production,
                )
        yield surface_pollution_total_stats
        yield surface_pollution_consumption
        yield surface_pollution_production
