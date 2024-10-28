#!/usr/bin/env python3
"""Module defining the entrypoint to the Prometheus exporter."""

from __future__ import annotations

import pathlib

import factorio_rcon
import loguru
import prometheus_client
import prometheus_client.core
import prometheus_client.registry
import prometheus_client.twisted
import rich_click as click
import tenacity
from twisted.internet import reactor
from twisted.web.resource import Resource
from twisted.web.server import Site

from collection.collectors import (
    FactorioAutopauser,
    FactorioEntityCollector,
    FactorioLaunchesCollector,
    FactorioPlayerCollector,
    FactorioPollutionCollector,
    FactorioProductionCollector,
    FactorioResearchCollector,
    FactorioTimeCollector,
)

LOGGER = loguru.logger.opt(colors=True)


@tenacity.retry(wait=tenacity.wait_fixed(1))
def _client(address: str, port: int, password: str) -> factorio_rcon.RCONClient:
    LOGGER.debug("attempting to connect to server via RCON...")
    return factorio_rcon.RCONClient(
        ip_address=address,
        port=port,
        password=password,
        connect_on_init=True,
    )


@click.group()
def cli() -> None:
    """Entrypoint for the Factorio Prometheus exporter."""


@cli.command()
@click.option(
    "--metrics-port",
    type=click.INT,
    default=9102,
    help="The port to expose the metrics endpoint on.",
)
@click.option(
    "--rcon-address",
    type=click.STRING,
    help="The address for the Factorio server.",
    default="localhost",
    required=False,
)
@click.option(
    "--rcon-port",
    type=click.INT,
    help="The RCON port for the Factorio server.",
    default=27015,
    required=False,
)
@click.option(
    "--rcon-password",
    type=click.STRING,
    help="The RCON password for the server.",
    required=False,
)
def run(metrics_port: int, rcon_address: str, rcon_port: int, rcon_password: str | None) -> None:
    """Start the Factorio Prometheus exporter."""
    LOGGER.info("starting exporter")

    # If we weren't supplied an RCON password, attempt to read it from the configuration.
    if rcon_password is None:
        LOGGER.info("attempting to pull RCON password from local config")
        rcon_password_path = pathlib.Path("/factorio/config/rconpw").absolute()
        rcon_password = rcon_password_path.read_text(encoding="utf-8").strip()

    # Unregister the default collectors.
    LOGGER.debug("deregistering default collectors")
    prometheus_client.core.REGISTRY.unregister(prometheus_client.GC_COLLECTOR)
    prometheus_client.core.REGISTRY.unregister(prometheus_client.PLATFORM_COLLECTOR)
    prometheus_client.core.REGISTRY.unregister(prometheus_client.PROCESS_COLLECTOR)

    client = _client(
        address=rcon_address,
        port=rcon_port,
        password=rcon_password,
    )

    autopauser = FactorioAutopauser(client=client)
    autopauser.start()

    # Register the Factorio collector.
    LOGGER.info("registering Factorio metrics collector")

    root = Resource()
    metrics = Resource()

    all_registry = prometheus_client.core.CollectorRegistry()

    collectors = [
        FactorioTimeCollector(client=client),
        FactorioPlayerCollector(client=client),
        FactorioLaunchesCollector(client=client),
        FactorioResearchCollector(client=client),
        FactorioProductionCollector(client=client),
        FactorioEntityCollector(client=client),
        FactorioPollutionCollector(client=client),
    ]

    for collector in collectors:
        all_registry.register(collector)
        collector.install(resource=metrics)

    metrics.putChild(
        path=str.encode("all"),
        child=prometheus_client.twisted.MetricsResource(all_registry),
    )

    # Start the Prometheus server in a thread.
    LOGGER.info("starting Prometheus HTTP server")
    root.putChild(path=str.encode("metrics"), child=metrics)

    reactor.listenTCP(metrics_port, Site(root))
    reactor.run()


if __name__ == "__main__":
    cli(
        auto_envvar_prefix="FACTORIO_PROMETHEUS_EXPORTER",
        prog_name="exporter.py",
    )
