import pytest
from yaml.constructor import ConstructorError

from converter.unique_key_loader import UniqueKeySafeLoader


class TestUniqueKeySafeLoader:
    def test_construct_mapping_rejects_top_level_duplicate(self) -> None:
        loader = UniqueKeySafeLoader("deny: [a]\ndeny: [b]\n")
        with pytest.raises(ConstructorError, match="found duplicate key 'deny'"):
            loader.get_single_data()

    def test_construct_mapping_rejects_nested_duplicate(self) -> None:
        loader = UniqueKeySafeLoader("permissions:\n  deny: [a]\n  deny: [b]\n")
        with pytest.raises(ConstructorError, match="found duplicate key 'deny'"):
            loader.get_single_data()

    def test_construct_mapping_accepts_same_key_in_different_mappings(self) -> None:
        loader = UniqueKeySafeLoader("first:\n  deny: [a]\nsecond:\n  deny: [b]\n")
        assert loader.get_single_data() == {"first": {"deny": ["a"]}, "second": {"deny": ["b"]}}

    def test_construct_mapping_accepts_merge_keys(self) -> None:
        loader = UniqueKeySafeLoader("base: &base\n  deny: [a]\nchild:\n  <<: *base\n  allow: [b]\n")
        assert loader.get_single_data()["child"] == {"deny": ["a"], "allow": ["b"]}
