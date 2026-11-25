from __future__ import annotations

from typing import Any


def pathTreeToList(pathTree: dict[str, Any]) -> list[list[str]]:
    """
    Transforms a nested dictionary into a list of paths,
    preserving the order [Root, Child, Grandchild].
    """
    if not isinstance(pathTree, dict):
        raise TypeError("Input must be a dictionary")

    subkeys: list[list[str]] = []

    for key, value in pathTree.items():
        if isinstance(value, dict) and value:
            children_paths = pathTreeToList(value)
            for path in children_paths:
                subkeys.append([key] + path)
        elif isinstance(value, dict):
            subkeys.append([key])
        else:
            raise TypeError(
                f"Path tree leaves must be empty dicts, got {type(value).__name__} at '{key}'"
            )

    return subkeys


def conditionTreeToList(conditionTree: dict[str, Any]) -> list[tuple[list[str], str]]:
    """
    Transforms a nested condition dictionary into a list of
    (path, condition) pairs, preserving [Root, Child, Grandchild] order.
    """
    if not isinstance(conditionTree, dict):
        raise TypeError("Input must be a dictionary")

    entries: list[tuple[list[str], str]] = []
    for key, value in conditionTree.items():
        if isinstance(value, dict):
            if not value:
                raise TypeError(f"Condition tree object at '{key}' cannot be empty")
            children = conditionTreeToList(value)
            for path, condition in children:
                entries.append(([key] + path, condition))
        elif isinstance(value, str):
            entries.append(([key], value))
        else:
            raise TypeError(f"leaf must be str, got {type(value).__name__}")
    return entries
