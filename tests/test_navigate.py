import pytest

from tomledit.navigate import (
    IntermediateNoMappingError,
    add_value,
    get_mapping,
    set_value,
)


def test_get_mapping_empty():
    root = {}
    key = []
    result = get_mapping(root, key)
    assert result is root


def test_get_mapping_single_key():
    root = {}
    key = ["a"]
    result = get_mapping(root, key)
    assert result == {}
    assert "a" in root
    assert isinstance(root["a"], dict)


def test_get_mapping_nested_keys():
    root = {"a": {}}
    key = ["a", "b", "c"]
    result = get_mapping(root, key)
    assert result == {}
    assert "b" in root["a"]
    assert isinstance(root["a"]["b"], dict)
    assert "c" in root["a"]["b"]
    assert isinstance(root["a"]["b"]["c"], dict)


def test_get_mapping_existing_path():
    root = {"a": {"b": {"c": {}}}}
    key = ["a", "b", "c", "d"]
    result = get_mapping(root, key)
    assert result == {}
    assert "d" in root["a"]["b"]["c"]
    assert isinstance(root["a"]["b"]["c"]["d"], dict)


def test_get_mapping_non_mapping_type():
    root = {"a": "not_a_dict"}
    key = ["a", "b"]
    with pytest.raises(IntermediateNoMappingError):
        get_mapping(root, key)


def test_get_mapping_non_existent_key():
    root = {}
    key = ["x", "y"]
    result = get_mapping(root, key)
    assert result == {}
    assert "x" in root
    assert isinstance(root["x"], dict)
    assert "y" in root["x"]
    assert isinstance(root["x"]["y"], dict)


def test_set_value():
    root = {}
    key = ["a", "b", "c"]
    value = "test_value"

    set_value(root, key, value)

    assert root["a"]["b"]["c"] == value


def test_add_value_to_list():
    root = {"a": ["b", "c"]}
    add_value(root, ["a"], "d")
    assert root["a"] == ["b", "c", "d"]


def test_add_value_to_value():
    root = {"a": {"b": {"c": "existing_value"}}}
    key = ["a", "b", "c"]
    value = "new_value"
    add_value(root, key, value)
    assert root["a"]["b"]["c"] == ["existing_value", value]


def test_add_value_new_list():
    root = {}
    key = ["a", "b"]
    value = "new_value"
    add_value(root, key, value)
    assert root["a"]["b"] == [value]
