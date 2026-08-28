from more_itertools.recipes import flatten

from app.models.request.PathTrees import MetadataPathTree


def pathTreeToList(pathTree: dict) -> list:
    """
    Transforms a nested dictionary into a list of paths,
    preserving the order [Root, Child, Grandchild].
    """
    if not isinstance(pathTree, dict):
        raise TypeError("Input must be a dictionary")

    subkeys = []

    for key, value in pathTree.items():
        if isinstance(value, dict) and value:
            # Recurse: get the paths from the children
            children_paths = pathTreeToList(value)

            # Prepend the current key to each path returned from deeper levels
            for path in children_paths:
                subkeys.append([key] + path)
        else:
            # Leaf node or empty dict: start a new path list
            subkeys.append([key])

    return subkeys

def conditionTreeToList(conditionTree: dict) -> list[tuple[list[str], str]]:
    """
    Transforms a nested condition dictionary into a list of
    (path, condition) pairs, preserving [Root, Child, Grandchild] order.
    """
    if not isinstance(conditionTree, dict):
        raise TypeError("Input must be a dictionary")

    entries = []
    for key, value in conditionTree.items():
        if isinstance(value, dict):
            children = conditionTreeToList(value)
            for path, condition in children:
                entries.append(([key] + path, condition))
        elif isinstance(value, str):
            entries.append(([key], value))
        else:
            raise TypeError(f"leaf must be str, got {type(value).__name__}")
    return entries




if __name__ == '__main__':
    # A testing nested dictionary
    pathTree = {
        "Root": {
            "Child 1": {
                "Child 2": "something else"
            }
        }
    }

    print(conditionTreeToList(pathTree))