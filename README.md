# cascabel

A simple workstation configuration manager that uses Git repositories.

## Installation

You can install cascabel with [pip](https://pip.pypa.io/en/stable/).

```bash
pip install .
```

## Usage

```text
> cascabel --help
Usage: cascabel [OPTIONS] COMMAND [ARGS]...

  The main execution function.

Options:
  --help  Show this message and exit.

Commands:
  add       Add a new repository configuration.
  install   Clone or pull repositories and then install them.
  list-all  List all configured repositories.
  push      Push all repository changes.
```

Repositories can be added with the `add` command.

```text
> cascabel add --help
Usage: cascabel add [OPTIONS] URL {NONE|SHELL|STOW} INSTALLATION_DIRECTORY

  Add a new repository configuration.

Options:
  -p, --order-place INTEGER       Specify the order in which this repository
                                  is executed in relation to others.
  -b, --branch TEXT               the branch to use
  -h, --current-hash TEXT         Specify the Desired hash of git repository
                                  to use.
  -l, --lock-hash BOOLEAN         Lock the specified hash and do not pull from
                                  newer versions.
  -e, --execution-directory TEXT  Set the directory to evaluate for
                                  configuration files.
  -o, --overwrite / --no-overwrite
                                  Overwrite any existing repository.
  --help                          Show this message and exit.
```

They can then can be listed with the `list-all` command.

```text
> cascabel list-all --help
Usage: cascabel list-all [OPTIONS]

  List all configured repositories.

Options:
  --help  Show this message and exit.
```

You can then install all repositories (or a single specified repository) with the `install` command.

```text
> cascabel install --help
Usage: cascabel install [OPTIONS]

  Clone or pull repositories and then install them.

Options:
  -u, --url [git@github.com:elijahjpassmore/.dotfiles.git|git@github.com:elijahjpassmore/.packages.git]
                                  Install an individual repository.
  -e, --exclude [git@github.com:elijahjpassmore/.dotfiles.git|git@github.com:elijahjpassmore/.packages.git]
                                  Exclude a given repository.
  -t, --exclude-type [NONE|SHELL|STOW]
                                  Exclude all repositories of a specified
                                  type.
  -i, --ignore-warnings BOOLEAN   Ignore any warning messages.
  --help                          Show this message and exit.
```

If you desire to push all repository changes at once, you can do so with the `push` command.

```text
> cascabel push --help
Usage: cascabel push [OPTIONS]

  Push all repository changes.

Options:
  -m, --message TEXT              Change the commit message used.
  -e, --exclude [git@github.com:elijahjpassmore/.dotfiles.git|git@github.com:elijahjpassmore/.packages.git]
                                  Exclude a given repository.
  --help                          Show this message and exit.
```

## Configuration

Configuration is located within `~/.config/cascabel/repositories.yml` in the following format:

```yaml
git@github.com:elijahjpassmore/.dotfiles.git:
  branch: null
  current_hash: d1da8c35d3f5afe0b0916b65a02fc0d4de6dea0c
  execution_directory: null
  installation_directory: /home/elijahjpassmore/.dotfiles
  lock_hash: false
  order_place: -1
  type: STOW
```

Logging can be found within `~/.config/cascabel/logging.log`.