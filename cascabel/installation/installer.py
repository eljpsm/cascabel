import datetime
import os
from pathlib import Path
from typing import Union

import git
from git import Repo, Commit  # type: ignore
from loguru import logger

from cascabel.configuration.configuration_manager import ConfigurationManager
from cascabel.repository import Repository
from cascabel.repository_types import RepositoryTypeError, RepositoryTypes


class InstallerError(Exception):
    """An error which occurred during installation logic."""
    pass


class Installer:
    """
    A repository installer.

    Each installer has a type associated with it, intended to offer
    different functionality, depending on the preferred installation
    method. The installation type "RepositoryTypes.NONE" can be used
    as a wildcard to apply to any repository type.
    """
    installation_type: RepositoryTypes = RepositoryTypes.NONE

    def __init__(self, repository: Repository, configuration_manager: ConfigurationManager,
                 show_warning_messages: bool = True):
        """
        Initialize the installer.
        :param repository: The repository to initialize.
        :param configuration_manager: The configuration manager used.
        :param show_warning_messages: Show potential warnings for risky actions.
        """
        if repository.type is not self.installation_type and self.installation_type is not RepositoryTypes.NONE:
            raise RepositoryTypeError(
                f"Installation type {repository.type} does not belong to {Installer.installation_type}")

        self.repository = repository
        self.configuration_manager = configuration_manager
        self.show_warning_messages = show_warning_messages

        self.git_repository: Union[Repo, None] = None

        self.init_cwd = os.getcwd()
        self.working_directory = self.repository.execution_directory or self.repository.installation_directory

    def __initialize_repository(self) -> Repo:
        """
        Initialize the repository.
        :return: The git repository.
        """
        logger.info(f"Initializing repository {self.repository.url}")
        git_repository = Installer.get_repository(Path(self.repository.installation_directory))
        if not git_repository:
            # Repository does not exist.

            # Clone the repository.
            logger.debug(
                f"Recursively cloning repository '{self.repository.url}' to '{self.repository.installation_directory}'")
            try:
                git_repository = Repo.clone_from(self.repository.url, self.repository.installation_directory,
                                                 recursive=True)
            except Exception as e:
                raise InstallerError(f"Unable to clone: {e}")
            logger.debug(
                f"Repository '{self.repository.url}' cloned to directory '{self.repository.installation_directory}'")

        else:
            # Repository exists.
            logger.debug(
                f"Repository is already cloned at {self.repository.installation_directory}")

            # If expected, then update the repository.
            if self.repository.lock_hash:
                logger.debug(f"Repository has hash locked: skipping pull")
            else:
                # If a branch is specified, change to it now.
                if self.repository.branch:
                    try:
                        git_repository.git.checkout(self.repository.branch)
                        logger.debug(f"Switched to branch '{self.repository.branch}'")
                    except Exception as e:
                        raise InstallerError(f"Unable to checkout branch '{self.repository.branch}': {e}")

                active_branch = git_repository.active_branch

                # Get the latest local commit.
                commits = git_repository.iter_commits()
                latest_local_commit: Commit = commits.__next__()

                # Get the latest remote commit.
                logger.debug(f"Getting latest origin commit on branch '{active_branch}'")
                latest_origin_commit = ""
                remote_heads = git.cmd.Git().ls_remote(self.repository.url, heads=True)
                heads_list = remote_heads.split()
                for index, element in enumerate(heads_list):
                    if element == f"refs/heads/{active_branch}":
                        latest_origin_commit = heads_list[index - 1]

                # If there is no latest origin commit, then assume that the branch is only local.
                if not latest_origin_commit:
                    logger.warning(
                        f"Remote origin does not exist on branch '{active_branch}': skipping pull evaluation")

                # If there is an origin commit, and it is not the same as the latest local commit, then attempt to get
                # the latest origin commit.
                if latest_local_commit.hexsha != latest_origin_commit:
                    logger.debug(f"Pulling latest commit '{latest_origin_commit}'")
                    git.Git(self.repository.installation_directory).pull("origin", active_branch)

                else:
                    logger.debug(f"Branch already at latest commit '{latest_origin_commit}'")

                if not self.repository.current_hash or self.repository.current_hash != latest_origin_commit:
                    # Update the commit hash in the configuration.
                    self.repository.current_hash = latest_origin_commit
                    self.configuration_manager.write_repository(self.repository)
                    self.configuration_manager.write_configuration()
                    logger.debug("Updated current_hash value")

        self.git_repository = git_repository
        return git_repository

    def set_up(self) -> None:
        """
        Set up the installer.
        :return: None.
        """
        self.__initialize_repository()

        # Go to either the execution directory (if specified), or the installation directory.
        os.chdir(self.working_directory)

    def clean_up(self) -> None:
        """
        Clean up the installer.
        :return: None.
        """
        # Change back to the original directory.
        os.chdir(self.init_cwd)

    @staticmethod
    def get_repository(repository_path: Path) -> Union[Repo, None]:
        """
        Get a repository at the given path.
        :return: Either a repository if it exists, or None.
        """
        if not repository_path.exists() or repository_path.is_dir() is False:
            logger.warning(
                f"Installation directory '{repository_path} does not exist: creating directory'")
            repository_path.mkdir(parents=True, exist_ok=True)

        try:
            expected_repository = Repo(repository_path)
        except:
            # Repository is not present.
            return None

        return expected_repository

    @staticmethod
    def push_changes(repository_path: Path,
                     message: str = f"Update via cascabel at {datetime.datetime.now().isoformat()}") -> None:

        """
        Push changes made to a repository at the specified path.
        :param repository_path: The expected repository path.
        :param message: The commit message.
        :return: None.
        """
        expected_repository = Installer.get_repository(repository_path)
        if not expected_repository:
            raise InstallerError(f"No git repository at '{repository_path.absolute()}' to push changes")

        # Check for both diff and if there are any untrack files.
        if not expected_repository.index.diff("HEAD") and not expected_repository.untracked_files:
            logger.info(f"No changes to repository located at '{repository_path.absolute()}': skipping")
            return

        try:
            # Add all the files when pushing.
            expected_repository.git.add(all=True)
            expected_repository.index.commit(message)
            origin = expected_repository.remote(name="origin")
            origin.push()
        except Exception as e:
            raise InstallerError(f"Could not push changes: {e}")
