#!/usr/bin/python
"""Module defining the entrypoint to the CLI utility for the project."""
from __future__ import annotations

import pathlib
import tempfile

import click
import docker
import factorio
import git
import loguru

LOGGER = loguru.logger.opt(colors=True)
MANIFEST = ["info.json", "control.lua"]
MODNAME = "factorio-prometheus-exporter"
REPOSITORY = git.Repo(path=__file__, search_parent_directories=True)
ROOT = pathlib.Path(REPOSITORY.git.rev_parse("--show-toplevel"))


def imagename(version: str) -> str:
    """Return the container image name from the given version."""
    return f"docker.io/celestialorb/factorio-prometheus-exporter:v{version}"


def modname(version: str) -> str:
    """Return the full artifact modname from the given version."""
    return f"{MODNAME}_{version}"


@click.group()
def cli() -> None:
    """Entrypoint for the project's CLI utility."""


def package(version: str) -> tuple[pathlib.Path, str]:
    """Create the artifacts for the given version."""
    LOGGER.info("packaging artifacts for v{}", version)

    # Create the Factorio mod zip archive.
    with tempfile.NamedTemporaryFile(
        dir=tempfile.gettempdir(),
        suffix=".zip",
        delete=False,
    ) as filename:
        mod_path = pathlib.Path(filename.name)
        mod = factorio.FactorioMod(name=MODNAME, version=version, archive=mod_path)
        mod.package()

    # Create the Prometheus exporter container image.
    client = docker.from_env()
    name = imagename(version=version)
    LOGGER.info("building container image: {}", name)
    client.images.build(
        dockerfile="Dockerfile",
        path=str(ROOT),
        tag=name,
    )
    LOGGER.info("<g>successfully built container image</g>")

    # Return the artifacts.
    return (mod_path, name)


@cli.command(name="package")
@click.option(
    "--version",
    type=click.STRING,
    help="The semantic version of the artifacts.",
    default="0.0.0",
)
def package_cmd(version: str) -> None:
    """Package the artifacts for the Factorio mod."""
    package(version=version)


@cli.command()
@click.option(
    "--version",
    type=click.STRING,
    help="The semantic version of the artifacts.",
    default="0.0.0",
)
@click.option(
    "--container-image",
    is_flag=True,
    type=click.BOOL,
    help="Whether or not to publish the container image.",
    default=False,
)
@click.option(
    "--factorio-mod",
    is_flag=True,
    type=click.BOOL,
    help="Whether or not to publish the Factorio mod.",
    default=False,
)
def publish(
    version: str,
    container_image: bool,
    factorio_mod: bool,
) -> None:
    """Publish the packaged artifacts."""
    version = version.strip("v")
    (packaged_mod, image) = package(version=version)

    # Publish the container image to Docker Hub.
    if container_image:
        client = docker.from_env()
        LOGGER.info("pushing container image: {}", image)
        client.images.push(repository=image)
        LOGGER.info("<g>successfully pushed container image: {}</g>", image)

    # Publish the zip archive to Factorio mods.
    if factorio_mod:
        mod = factorio.FactorioMod(name=MODNAME, version=version, archive=packaged_mod)
        mod.publish()


if __name__ == "__main__":
    cli()
