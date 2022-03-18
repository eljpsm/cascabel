from enum import Enum


class RepositoryTypeError(Exception):
    """A repository specific error."""
    pass


class RepositoryTypes(Enum):
    """Repository types to evaluate for installation behaviour."""
    NONE = 1
    SHELL = 2
    STOW = 3
