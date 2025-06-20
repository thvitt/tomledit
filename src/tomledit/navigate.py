import logging
import re
from collections.abc import MutableMapping, Sequence
from typing import Any

import tomlkit

logger = logging.getLogger(__name__)


def format_key(key: Sequence[str]) -> str:
    return ".".join(
        part if re.match(r"^[A-Za-z0-9_-]+$", part) else f'"{part}"' for part in key
    )


class NoMappingError(TypeError):
    """Raised when a mapping is expected but not found."""

    key: Sequence[str]
    value: Any

    def __init__(self, key: Sequence[str], value: Any) -> None:
        self.key = key
        self.value = value
        super().__init__(
            f"Expected a mapping at key {format_key(key)}, but got {type(value).__name__}"
        )


class IntermediateNoMappingError(NoMappingError):
    """Raised when a NoMappingError occurs while navigating to the final key"""


def make_value(value: Any) -> Any:
    """
    Converts a value to a TOML-compatible value.

    Args:
        value (Any): The value to convert.

    Returns:
        Any: A TOML-compatible value.
    """
    try:
        return tomlkit.value(value)
    except ValueError:
        return value


def get_mapping(
    root: MutableMapping[str, Any], key: Sequence[str]
) -> MutableMapping[str, Any]:
    """
    Returns the mapping at the specified key in the root dictionary.

    Args:
        root (MutableMapping[str, Any]): A mapping, e.g., a TOML document or a dictionary.
        key (Sequence[str]): The dotted key as it would be used in a TOML document.

    Raises:
        IntermediateNoMappingError: If we should navigate through a mapping, but the intermediate key exists and is not a mapping

    Returns:
        MutableMapping[str, Any]: The mapping at the end of the key path
    """
    table = root
    for i, k in enumerate(key):
        if isinstance(table, MutableMapping):
            if k not in table:
                table[k] = {}
            table = table[k]
        else:
            raise IntermediateNoMappingError(key[:i], table)
    return table


def set_value(root: MutableMapping[str, Any], key: Sequence[str], value: str) -> None:
    """Sets the value at the specified key in the root dictionary."""
    mapping = get_mapping(root, key[:-1])
    if isinstance(mapping, MutableMapping):
        v = make_value(value)
        mapping[key[-1]] = v
        logger.info("Set %s = %s", format_key(key), v)
    else:
        raise NoMappingError(key[:-1], mapping)


def add_value(root: MutableMapping[str, Any], key: Sequence[str], value: str) -> None:
    """
    Adds a value to the list at the specified key in the root dictionary.

    If the key does not exist, it creates a new list with the value.
    If the key exists and is not a list, it converts the existing value into a list and appends the new value.
    """
    mapping = get_mapping(root, key[:-1])
    new_value = make_value(value)
    if key[-1] in mapping:
        current_value = mapping[key[-1]]
        if isinstance(current_value, list):
            current_value.append(new_value)
            logger.info("Appended %s to %s", new_value, format_key(key))
        else:
            mapping[key[-1]] = [current_value, new_value]
            logger.info(
                "At %s, converted %s to a list and added %s",
                format_key(key),
                current_value,
                new_value,
            )
    else:
        mapping[key[-1]] = [new_value]
        logger.info("Created new list at %s with value %s", format_key(key), new_value)


def set_or_add(root: MutableMapping[str, Any], key: Sequence[str], value: str) -> None:
    """
    If the value at the specified key in the root dictionary is a list, add the value to it,
    otherwise set the entry at the key to the value.
    """
    mapping = get_mapping(root, key[:-1])
    if key[-1] in mapping and isinstance(mapping[key[-1]], list):
        mapping[key[-1]].append(make_value(value))
        logger.info("Appended %s to %s", make_value(value), format_key(key))
    else:
        set_value(mapping, [key[-1]], value)


def del_key(root: MutableMapping[str, Any], key: Sequence[str]) -> None:
    """
    Deletes the specified key from the root dictionary.

    Args:
        root (MutableMapping[str, Any]): A mapping, e.g., a TOML document or a dictionary.
        key (Sequence[str]): The dotted key as it would be used in a TOML document.
    """
    mapping = get_mapping(root, key[:-1])
    if isinstance(mapping, MutableMapping) and key[-1] in mapping:
        old_value = mapping[key[-1]]
        del mapping[key[-1]]
        logger.info("Deleted %s = %s", format_key(key), old_value)
    else:
        raise NoMappingError(key[:-1], mapping)
