import subprocess
from pathlib import Path

import click
from loguru import logger

from cascabel.installation.installer import Installer, InstallerError
from cascabel.repository_types import RepositoryTypes

SHELL_SUFFIX = ".sh"


class ShellInstaller(Installer):
    """A shell script specific installer."""
    installation_type = RepositoryTypes.SHELL

    def install(self) -> None:
        """
        Install the repository.
        :return: None.
        """
        # Initialize the repository.
        super().set_up()

        logger.info(f"Running shell installer for repository {self.repository.url}")
        self.evaluate_shell_scripts()

        # Clean up after installation.
        super().clean_up()

    def evaluate_shell_scripts(self) -> None:
        """
        Evaluate shell scripts within the working directory.
        :return: None.
        """
        for path in Path(self.working_directory).iterdir():
            if path.suffix == SHELL_SUFFIX:
                if self.show_warning_messages:
                    if click.confirm(f"Are you sure you want to execute '{path.name}'?"):
                        self.execute_script(path)
                else:
                    self.execute_script(path)

    @staticmethod
    def execute_script(path: Path) -> None:
        """
        Execute a shell script.
        :param path: The path to the shell script.
        :return: None.
        """
        try:
            logger.debug(f"Executing script '{path.name}'")
            # This works because during the set-up process within Installer, we are dropped into the working directory.
            subprocess.call(["sh", f"./{path.name}"])
        except Exception as e:
            raise InstallerError(f"Could not execute shell script '{path.name}': {e}")
