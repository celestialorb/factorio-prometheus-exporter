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
    """Returns the full artifact modname from the given version."""
    return f"{MODNAME}_{version}"


@click.group()
def cli() -> None:
    """Entrypoint for the project's CLI utility."""


@cli.command()
@click.option("--deploy", type=click.BOOL, default=False)
@click.option("--deploy-to", type=click.Path(exists=False))
@click.option("--version", type=click.STRING, default="0.0.0")
def package(deploy: bool, deploy_to: str, version: str) -> None:
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

        # If we're not instructed to deploy, simply return as we're done.
        if not deploy:
            return

        # Copy the zip archive to the server.
        destination = os.path.join(deploy_to, f"{modname(version)}.zip")
        shutil.copy(src=filename.name, dst=destination)
        shutil.chown(path=destination, user=845, group=845)


if __name__ == "__main__":
    cli()
