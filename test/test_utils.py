from socksync.utils import dict_without_none


def test_dict_without_none_empty():
    assert dict_without_none({}) == {}


def test_dict_without_none_no_none():
    assert dict_without_none({"test": 1}) == {"test": 1}


def test_dict_without_none_with_none():
    assert dict_without_none({"test": None}) == {}


def test_dict_without_none_with_both():
    assert dict_without_none({"test": 1, "test2": None}) == {"test": 1}
