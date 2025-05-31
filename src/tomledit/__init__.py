import logging
from collections.abc import Iterable
from pathlib import Path
from typing import Annotated

import tomlkit
from cyclopts import App, Parameter
from rich.logging import RichHandler

from tomledit.navigate import add_value, del_key, get_mapping, set_or_add, set_value

app = App(help_format="markdown", usage="Usage: te [OPTIONS] ARGS")
logger = logging.getLogger(__name__)


def find_in_parents(name: str) -> Path:
    path = Path().absolute()
    while not (path / name).exists() and path.parents:
        path = path.parent
    file = path / name
    if file.exists():
        return file
    else:
        return Path(name)


class edit_toml:
    def __init__(self, filename: str | Path | None, backup: bool = False) -> None:
        self.backup = backup
        if filename is None:
            file = find_in_parents("pyproject.toml")
        elif not isinstance(filename, Path):
            file = Path(filename)
        else:
            file = Path(filename)
        self.file = file
        if self.file.exists():
            with self.file.open("rb") as f:
                self.doc = tomlkit.load(f)
        else:
            self.doc = tomlkit.TOMLDocument()

    def __enter__(self) -> tomlkit.TOMLDocument:
        return self.doc

    def __exit__(self, exc_type, exc_value, traceback):
        if self.backup and self.file.exists():
            backup_file = self.file.with_suffix(self.file.suffix + "~")
            if backup_file.exists():
                backup_file.unlink()
            self.file.rename(backup_file)
            logger.info("Backup created at %s", backup_file)
        with self.file.open("w", encoding="utf-8") as f:
            tomlkit.dump(self.doc, f)


def first[T](it: Iterable[T]) -> T:
    return next(iter(it))


def parse_key(src: str):
    structure = tomlkit.parse(f"[{src}]")
    keys = []
    while structure:
        key = first(structure)
        value = structure[key]
        if isinstance(value, dict):
            structure = value
        keys.append(key)
    return keys


@app.default()
def main(  # noqa: PLR0912
    *args: Annotated[str, Parameter(allow_leading_hyphen=True, required=True)],
    file: Annotated[Path | None, Parameter(["-f", "--file"])] = None,
    find: Annotated[str, Parameter(["-F", "--find"])] = "pyproject.toml",
    prefix: Annotated[str | None, Parameter(["-p", "--prefix"])] = None,
    backup: Annotated[bool, Parameter(["-b", "--backup"])] = False,
    verbose: Annotated[bool, Parameter(["-v", "--verbose"])] = False,
):
    """
    Edit a TOML file, by default `pyproject.toml`.

    The given arguments are interpreted as a series of key-value pairs or mode switches. The keys
    are expected to be in the same format as expected in the [] in a TOML file, e.g.,
    `super.sub."dotted.key"`. The values can be either plain strings or any valid TOML value.

    The mode switches are @, =, + and - and determine the interpretation of the following values
    until the next mode switch or the end of the arguments. The default mode is @ (auto). The modes
    work as follows:

    | switch | mode | arguments     | description |
    |--------|------|---------------|-------------|
    | @      | auto | key value ... | If the key points to a list, the value is appended. Otherwise, the entry at the key is set to the value, replacing any existing value. |
    | =      | set  | key value ... | The entry at the key is set to the value, replacing any existing value. |
    | +      | add  | key value ... | If the key points to a list, the value is appended. If the key does not exist, it is created as a list with the value. If the key exists and is not a list, it is converted to a list and the value is appended. |
    | -      | remove| key ...       | The entries at the given keys are removed. If the key points to a list, the value is removed from the list. |


    Args:
        args: mode switches, keys and values as outlined above.
        file: if present, the file on which to work.
        find: if _file_ is not given, find a file with this name in the current directory or its parents.
        prefix: if present (e.g., tool.uv), all keys are below this prefix.
        backup: if true, create a backup of the TOML file before writing changes.
        verbose: report on the operations performed
    """
    logging.basicConfig(
        level=logging.INFO if verbose else logging.WARNING,
        handlers=[RichHandler(show_time=False)],
        format="%(message)s",
    )
    mode_error = {
        "=": "Cannot set {key} to {value}: {reason}",
        "+": "Cannot append {value} to {key}: {reason}",
        "-": "Cannot remove {key}: {reason}",
        "@": "Cannot set or append value {value} for key {key}: {reason}",
    }

    if file is None:
        file = find_in_parents(find)

    with edit_toml(file, backup=backup) as doc:
        if prefix is not None:
            prefix_ = parse_key(prefix)
            root = get_mapping(doc, prefix_)
            logger.info("Editing %s, table %s", file, prefix)
        else:
            root = doc
            logger.info("Editing %s", file)

        mode = "@"
        commands = list(args)
        while commands:
            command = commands.pop(0)
            if command in ("@", "=", "+", "-"):
                mode = command
                continue

            key = parse_key(command)
            if mode == "-":
                value = ""
            elif commands:
                value = commands.pop(0)
            else:
                logger.error(
                    mode_error[mode].format(
                        key=command, value="(missing)", reason="no more arguments"
                    )
                )
                break

            try:
                match mode:
                    case "@":
                        set_or_add(root, key, value)
                    case "=":
                        set_value(root, key, value)
                    case "+":
                        add_value(root, key, value)
                    case "-":
                        del_key(root, key)
            except TypeError as e:
                logger.error(
                    mode_error[mode].format(key=command, value=value, reason=str(e))
                )
