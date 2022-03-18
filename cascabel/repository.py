from dataclasses import dataclass
from typing import Optional

from cascabel.repository_types import RepositoryTypes


@dataclass
class Repository:
    """An abstract configuration repository."""
    url: str
    type: RepositoryTypes
    installation_directory: str
    branch: Optional[str]
    current_hash: Optional[str]
    execution_directory: Optional[str]
    order_place: int = -1
    lock_hash: bool = False

    @staticmethod
    def repository_dictionary_to_repository(repository_url, repository_info: dict):
        # Overwrite the string representation of the type as the proper enum type.
        repository_info["type"] = RepositoryTypes[repository_info["type"]]

        return Repository(repository_url, **repository_info)
