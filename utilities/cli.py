#!/usr/bin/python
"""Module defining the entrypoint to the CLI utility for the project."""
import pathlib
import shutil
import tempfile
import zipfile

import click

MANIFEST = ["info.json", "control.lua"]
MODNAME = "factorio-prometheus-exporter"


def modname(version: str) -> str:
    """Return the full artifact modname from the given version."""
    return f"{MODNAME}_{version}"


@click.group()
def cli() -> None:
    """Entrypoint for the project's CLI utility."""


@cli.command()
@click.option("--deploy", type=click.BOOL, default=False)
@click.option("--deploy-to", type=click.Path(exists=False))
@click.option("--version", type=click.STRING, default="0.0.0")
def package(deploy: bool, deploy_to: pathlib.Path, version: str) -> None:  # noqa: FBT001
    """Package up the Factorio mod and deploy it to the local server."""
    with tempfile.NamedTemporaryFile(suffix=".zip") as filename:
        # Create a zip archive.
        path = pathlib.Path(filename.name)
        with zipfile.ZipFile(file=path.absolute, mode="w") as zip_file:
            for item in MANIFEST:
                archive_path = pathlib.Path(modname(version)) / item
                zip_file.write(
                    filename=item,
                    arcname=archive_path,
                )
            path.chmod(mode=0o644)

        # If we're not instructed to deploy, simply return as we're done.
        if not deploy:
            return

        # Copy the zip archive to the server.
        destination = deploy_to / f"{modname(version)}.zip"
        shutil.copy(src=filename.name, dst=destination)
        shutil.chown(path=destination, user=845, group=845)


if __name__ == "__main__":
    cli()
