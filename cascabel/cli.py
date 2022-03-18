import shutil
import sys
from pathlib import Path
from typing import Optional

import click
from loguru import logger

from cascabel import __repository__
from cascabel.configuration.configuration_manager import global_manager, original_configuration_contents
from cascabel.installation import initialize_installer
from cascabel.installation.installer import InstallerError, Installer
from cascabel.repository import Repository
from cascabel.repository_types import RepositoryTypes, RepositoryTypeError

LOG_PATH = global_manager.directory_path.joinpath("logging.log")

# Output logs.
logger.add(LOG_PATH)


@click.group()
def main() -> None:
    """The main execution function."""
    try:
        # Try and find the necessary packages for operating cascabel.
        executables = {"git": shutil.which("git"), "stow": shutil.which("stow")}
        missing_executables = []
        for key in executables:
            if not executables[key]:
                missing_executables.append(key)
        if missing_executables:
            logger.warning(f"Missing executables {missing_executables}: please read the README at {__repository__}")
    except Exception as err:
        print(str(err))
        sys.exit(2)


@main.command()
@click.option("--url", "-u", type=click.Choice([r for r in original_configuration_contents]),
              help="Install an individual repository.")
@click.option("--exclude", "-e", type=click.Choice([r for r in original_configuration_contents]), multiple=True,
              help="Exclude a given repository.")
@click.option("--exclude-type", "-t", type=click.Choice([t.name for t in RepositoryTypes]), multiple=True,
              help="Exclude all repositories of a specified type.")
@click.option("--ignore-warnings", "-i", type=bool, default=False, help="Ignore any warning messages.")
def install(url: Optional[str], exclude: tuple[str], exclude_type: Optional[str],
            ignore_warnings: bool = False) -> None:
    """Clone or pull repositories and then install them."""
    if not url:
        # A repository has not been specified, so apply all configured repositories.
        logger.info(f"Installing all repositories listed in configuration {global_manager.configuration_file_path}")

        # Get a list of all the (confirmed) repositories to ignore.
        parsed_exclude = set()
        for repository_string in exclude:
            if repository_string in original_configuration_contents:
                logger.info(f"Excluding repository '{repository_string}'")
                parsed_exclude.add(repository_string)
            else:
                logger.warning(f"Repository '{repository_string}' not in configuration: skipping")

        # Create a list of only the actionable repositories.
        if exclude_type:
            # If any types are to be excluded, compile a list and exclude them.
            parsed_exclude_types = set()
            for type in exclude_type:
                # Get the type from the given key.
                if type in [type.name for type in RepositoryTypes]:
                    upper_type = type.upper()
                    logger.info(f"Excluding all repositories of type '{upper_type}'")
                    parsed_exclude_types.add(upper_type)
                else:
                    raise RepositoryTypeError(f"Repository type '{type}' not found")

            # Ignore any repositories of the given exclusion type.
            key_and_order_list = [{"url": url, "order-place": original_configuration_contents[url]["order_place"]} for
                                  url
                                  in
                                  original_configuration_contents if
                                  url not in parsed_exclude and original_configuration_contents[url][
                                      "type"] not in parsed_exclude_types]
        else:
            key_and_order_list = [{"url": url, "order-place": original_configuration_contents[url]["order_place"]} for
                                  url
                                  in
                                  original_configuration_contents if url not in parsed_exclude]

        # Sort the repositories by their order place.
        key_and_order_list.sort(key=lambda x: x["order-place"])
        actionable_repository_urls = [x["url"] for x in key_and_order_list]

        if not actionable_repository_urls:
            logger.info("No actionable repositories: returning")
            return

        for repository_url in actionable_repository_urls:
            # Create a repository dataclass from the dictionary.
            repository = Repository.repository_dictionary_to_repository(repository_url,
                                                                        original_configuration_contents[
                                                                            repository_url])

            try:
                installer = initialize_installer(repository, global_manager, not ignore_warnings)
                installer.install()
            except InstallerError as err:
                logger.error(f"{err}: skipping repository '{repository.url}'")
                continue

            pass

    else:
        # Otherwise, apply the specified repository.

        if exclude:
            # If an exclude list is specified, then ignore it.
            logger.warning("URL has been specified: skipping any ignored files")

        if exclude_type:
            # If a type to exclude is provided, then ignore it.
            logger.warning("URL has been specified: ignoring type exclusion")

        # Try and find it first.
        repository_string = original_configuration_contents[url]
        if not repository_string:
            logger.error(f"Could not find repository '{url}': exiting")

        logger.info(f"Applying repository '{url}'")


@main.command()
@click.argument("url", type=str)
@click.argument("type", type=click.Choice([t.name for t in RepositoryTypes]))
@click.argument("installation-directory", type=str)
@click.option("--order-place", "-p", type=int, default=-1,
              help="Specify the order in which this repository is executed in relation to others.")
@click.option("--branch", "-b", type=str, help="the branch to use")
@click.option("--current-hash", "-h", type=str, help="Specify the Desired hash of git repository to use.")
@click.option("--lock-hash", "-l", type=bool, default=False,
              help="Lock the specified hash and do not pull from newer versions.")
@click.option("--execution-directory", "-e", type=str, help="Set the directory to evaluate for configuration files.")
@click.option("--overwrite/--no-overwrite", "-o", type=bool, default=False, help="Overwrite any existing repository.")
def add(url: str, type: str, installation_directory: str, branch, current_hash: Optional[str],
        execution_directory: Optional[str],
        order_place: int = -1,
        lock_hash: bool = False,
        overwrite: bool = False) -> None:
    """Add a new repository configuration."""
    # Get the type from the given key.
    try:
        parsed_type = RepositoryTypes[type.upper()]
    except KeyError:
        raise RepositoryTypeError(f"Repository type '{type}' not found")

    if url in original_configuration_contents and overwrite is False:
        logger.warning(f"Repository {url} already exists: skipping repository")
    else:
        # Write the new repository to the configuration.
        global_manager.write_repository(
            Repository(url=url, type=parsed_type, installation_directory=installation_directory,
                       branch=branch,
                       order_place=order_place,
                       current_hash=current_hash,
                       lock_hash=lock_hash, execution_directory=execution_directory))
        global_manager.write_configuration()

        if overwrite and url in original_configuration_contents:
            logger.info(f"Overwrote '{url}' in configuration")
        else:
            logger.info(f"Wrote new repository '{url}' to configuration")


@main.command()
@click.option("--message", "-m", type=str, help="Change the commit message used.")
@click.option("--exclude", "-e", type=click.Choice([r for r in original_configuration_contents]), multiple=True,
              help="Exclude a given repository.")
def push(message: Optional[str], exclude: tuple[str]) -> None:
    """Push all repository changes."""
    repository_urls = [url for url in original_configuration_contents]

    expected_repository_paths = []
    try:
        expected_repository_paths = [original_configuration_contents[url]["installation_directory"] for url in
                                     repository_urls if url not in exclude]
    except KeyError as e:
        logger.error(f"Could not push repositories: {e}")

    if not expected_repository_paths:
        logger.info("No repositories to push changes: cancelling")
        return

    for path in expected_repository_paths:
        try:
            if message:
                Installer.push_changes(repository_path=Path(path), message=message)
            else:
                Installer.push_changes(repository_path=Path(path))

        except InstallerError as e:
            logger.error(f"{e}: cancelling any future push")

    logger.info("All repository changes have been pushed")


@main.command()
def list_all() -> None:
    """List all configured repositories."""
    print(global_manager.get_configuration())


if __name__ == "__main__":
    main()
