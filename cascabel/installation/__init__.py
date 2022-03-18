from cascabel.configuration.configuration_manager import ConfigurationManager
from cascabel.installation.shell_installer import ShellInstaller
from cascabel.installation.stow_installer import StowInstaller
from cascabel.repository import Repository

# A list of all installers available.
all_installers = [StowInstaller, ShellInstaller]

# A map of installation type to installer.
installation_map = {}
for installer in all_installers:
    installation_map[installer.installation_type.value] = installer


def initialize_installer(repository: Repository, configuration_manager: ConfigurationManager,
                         show_warning_messages: bool = True):
    """Get the relevant installer by repository type."""
    return installation_map[repository.type.value](repository, configuration_manager, show_warning_messages)
