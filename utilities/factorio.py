"""Module defining an interface to the Factorio Mods API."""
from __future__ import annotations

import json
import os
import pathlib
import zipfile

import loguru
import requests

LOGGER = loguru.logger.opt(colors=True)

FACTORIO_MOD_MANIFEST = ["info.json", "control.lua"]
FACTORIO_MOD_PORTAL_URL = "https://mods.factorio.com"


class FactorioMod:
    """Class defining a single Factorio mod."""

    archive: pathlib.Path = None
    name: str = ""
    version: str = ""

    def __init__(
        self: FactorioMod,
        name: str,
        archive: pathlib.Path,
        version: str,
    ) -> None:
        """Initialize the Factorio mod."""
        self.archive = archive
        self.name = name
        self.version = version

    @property
    def fullname(self: FactorioMod) -> str:
        """Return the full name of the Factorio mod with version."""
        return f"{self.name}_{self.version}"

    def package(self: FactorioMod) -> None:
        """Package the Factorio mod into a zip archive."""
        # Prepare the info.json file first.
        info_file = pathlib.Path("info.json")
        with info_file.open(mode="r+", encoding="utf-8") as data_file:
            info = json.load(fp=data_file)
            info["version"] = self.version
            data_file.seek(0)
            data_file.truncate()
            data_file.write(json.dumps(info, indent=2) + "\n")

        # Create the Factorio mod zip archive.
        LOGGER.info("creating Factorio mod zip archive: {}", self.archive)
        with zipfile.ZipFile(file=self.archive, mode="w") as zip_file:
            for item in FACTORIO_MOD_MANIFEST:
                LOGGER.debug("adding file to zip archive: {}", item)
                archive_path = pathlib.Path(self.fullname) / item
                zip_file.write(
                    filename=item,
                    arcname=archive_path,
                )
            self.archive.chmod(mode=0o644)
        LOGGER.success("successfully created Factorio mod zip archive")

    def publish(
        self: FactorioMod,
        api_key: str = os.getenv("FACTORIO_MODS_API_KEY", None),
    ) -> None:
        """Publish the Factorio mod to the registry."""
        # Initialize the upload of our Factorio mod.
        LOGGER.info("initializing mod upload: {}", self.name)
        response = requests.post(
            url=f"{FACTORIO_MOD_PORTAL_URL}/api/v2/mods/releases/init_upload",
            data={"mod": self.name},
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=10,
        )

        # Ensure we successfully initialized the publication of the mod.
        if not response.ok:
            LOGGER.error(
                "unable to initialize upload of Factorio mod: {}",
                response.text,
            )
            return

        # Grab the upload URL from the initialization response and upload the mod data.
        upload_url = response.json()["upload_url"]
        LOGGER.info("attempting mod upload: {}", self.archive)
        with self.archive.open(mode="rb") as archive_file:
            response = requests.post(
                url=upload_url,
                files={"file": archive_file},
                timeout=60,
            )

        # Ensure we successfully published the mod.
        if not response.ok:
            LOGGER.error(
                "unable to upload the Factorio mod: {}",
                response.text,
            )
            return
        LOGGER.success("successfully uploaded Factorio mod")
