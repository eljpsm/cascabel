from pathlib import Path
from typing import Any, Union

import yaml
from loguru import logger

from cascabel.repository import Repository

CONFIG_FILE_NAME = "repositories.yml"
DEFAULT_CONFIG_PATH = Path.home().joinpath(".config").joinpath("cascabel")


class ConfigurationManager:
    """A manager for the main configuration file."""

    def __init__(self, directory_path: Path = DEFAULT_CONFIG_PATH) -> None:
        """
        Initialize the configuration manager.
        :param directory_path: The directory to initialize the configuration.
        """
        self.directory_path = directory_path
        self.configuration_file_path = directory_path.joinpath(CONFIG_FILE_NAME)
        self.configuration_contents: dict[str, Any] = {}

        # Create the expected directory path structure.
        self.directory_path.mkdir(parents=True, exist_ok=True)

        # Create the configuration file.
        self.configuration_file_path.touch(exist_ok=True)

        # Read the configuration contents.
        #
        # At the same time, save the original contents when first read (in case the user needs to go back to the
        # original version.
        self.original_configuration_contents = self.read_configuration()

    def write_configuration(self) -> None:
        """
        Write a configuration to the configuration file.
        :return: None.
        """
        with open(self.configuration_file_path.absolute(), "w") as stream:
            try:
                # If the contents consist of an empty dictionary, then delete the file contents.
                if not self.configuration_contents:
                    stream.truncate(0)
                else:
                    yaml.safe_dump(self.configuration_contents, stream)
            except Exception as e:
                logger.error(f"Error writing to configuration: {e}")
                # If an exception occurs, try and write the original contents.
                yaml.safe_dump(self.original_configuration_contents, stream)

    def read_configuration(self) -> dict:
        """
        Read the configuration from the configuration file.
        :return: The configuration as a dictionary.
        """
        with open(self.configuration_file_path.absolute(), "r") as stream:
            # Read the contents.
            #
            # If there is nothing to read, then consider the contents to be an empty dictionary.
            contents = yaml.safe_load(stream)
            if contents is None:
                contents = {}

            self.configuration_contents = contents
            return contents

    def write_repository(self, repository: Repository) -> None:
        """
        Write a repository to the configuration.
        :param repository: The repository to write.
        :return:  None.
        """
        self.configuration_contents[repository.url] = {
            "type": repository.type.name,
            "installation_directory": repository.installation_directory,
            "order_place": repository.order_place or -1,
            "branch": repository.branch,
            "current_hash": repository.current_hash or None,
            "lock_hash": repository.lock_hash or False,
            "execution_directory": repository.execution_directory or None
        }

    def remove_repository_by_object(self, repository: Repository) -> None:
        """
        Remove a repository by the repository object.
        :param repository: The repository.
        :return: None.
        """
        self.configuration_contents.pop(repository.url)

    def remove_repository_by_url(self, url: str) -> None:
        """
        Remove a repository by the URL.
        :param url: The repository URL.
        :return: None.
        """
        self.configuration_contents.pop(url)

    def get_configuration(self, as_string: bool = True) -> Union[dict, str]:
        """
        Get the current configuration.
        :param as_string: Return the configuration as a string.
        :return: The configuration either as a string, or a dictionary.
        """
        with open(self.configuration_file_path.absolute(), "r") as stream:
            yaml_contents = yaml.safe_load(stream)
            if as_string:
                return yaml.safe_dump(yaml_contents)

            return yaml_contents


# Create an instance that acts as a singleton and allows the CLI to read current contents for hints.
global_manager = ConfigurationManager()
original_configuration_contents = global_manager.original_configuration_contents
