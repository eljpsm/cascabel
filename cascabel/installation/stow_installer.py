import subprocess
from pathlib import Path

from loguru import logger

from cascabel.installation.installer import Installer, InstallerError
from cascabel.repository_types import RepositoryTypes


class StowInstaller(Installer):
    """A GNU stow specific installer."""
    installation_type = RepositoryTypes.STOW

    def install(self) -> None:
        """
        Install the repository.
        :return: None.
        """
        # Initialize the repository.
        super().set_up()

        logger.info(f"Running stow installer for repository {self.repository.url}")
        self.stow_directories()

        # Clean up after installation.
        super().clean_up()

    def stow_directories(self) -> None:
        """
        Stow the directories.
        :return: None.
        """
        try:
            for path in Path(self.working_directory).iterdir():
                # Ignore any hidden directories.
                if path.is_dir() and path.name[0] != ".":
                    logger.debug(f"Stowing directory '{path.name}'")
                    subprocess.run(["stow", path.name])
        except Exception as e:
            raise InstallerError(f"Could not stow directories in '{self.repository.installation_directory}': {e}")
