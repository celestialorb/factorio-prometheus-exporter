#!/usr/bin/python
"""Module defining the entrypoint to the CLI utility for the project."""
import click
import os
import shutil
import tempfile
import zipfile

MANIFEST = ["info.json", "control.lua"]
MODNAME = "factorio-prometheus-exporter"


def modname(version: str) -> str:
    return f"{MODNAME}_{version}"


@click.group()
def cli() -> None:
    pass


@cli.command()
@click.option("--version", type=click.STRING, default="0.0.0")
def package(version: str) -> None:
    """Package up the Factorio mod and deploy it to the local server."""
    with tempfile.NamedTemporaryFile(suffix=".zip") as filename:
        # Create a zip archive.
        with zipfile.ZipFile(file=filename, mode="w") as zip_file:
            for item in MANIFEST:
                zip_file.write(
                    filename=item,
                    arcname=os.path.join(modname(version), item),
                )
        os.chmod(path=filename.name, mode=0o644)

        # Copy the zip archive to the server.
        destination = f"/mnt/external/games/factorio/mods/{modname(version)}.zip"
        shutil.copy(src=filename.name, dst=destination)
        shutil.chown(path=destination, user=845, group=845)


if __name__ == "__main__":
    cli()
