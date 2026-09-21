from typing import TYPE_CHECKING
from typing import Any

from yaml.constructor import ConstructorError
from yaml.loader import SafeLoader

if TYPE_CHECKING:
    from collections.abc import Hashable

    from yaml.nodes import MappingNode

MERGE_TAG = "tag:yaml.org,2002:merge"


class UniqueKeySafeLoader(SafeLoader):
    """Load YAML like ``SafeLoader``, but reject a mapping that repeats a key.

    ``SafeLoader`` keeps the last value of a repeated key without any warning, so a second ``deny:`` list would silently
    replace the first one in a permission file.
    """

    def construct_mapping(self, node: MappingNode, deep: bool = False) -> dict["Hashable", Any]:
        seen: set[Hashable] = set()
        for key_node, _ in node.value:
            if key_node.tag == MERGE_TAG:
                continue
            key = self.construct_object(key_node, deep=deep)
            if key in seen:
                message = f"found duplicate key {key!r}"
                raise ConstructorError("while constructing a mapping", node.start_mark, message, key_node.start_mark)
            seen.add(key)
        return super().construct_mapping(node, deep=deep)
