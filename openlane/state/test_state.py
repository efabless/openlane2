import pytest
from typing import Dict


def test_create_by_type():
    from .state import State
    from .design_format import DesignFormat

    test_dict = {DesignFormat.NETLIST: "abc"}
    state = State(test_dict)
    assert state[DesignFormat.NETLIST] == "abc"


def test_create_by_id():
    from .state import State
    from .design_format import DesignFormat

    test_dict = {"nl": "abc"}
    state = State(test_dict)
    assert state[DesignFormat.NETLIST] == "abc"


def test_override_by_id():
    from .state import State
    from .design_format import DesignFormat

    test_dict = {"nl": "abc"}
    override = {"nl": "abcd"}
    state = State(test_dict, overrides=override)
    assert state[DesignFormat.NETLIST] == "abcd"


def test_override_by_type():
    from .state import State
    from .design_format import DesignFormat

    test_dict = {"nl": "abc"}
    override = {DesignFormat.NETLIST: "abcd"}
    state = State(test_dict, overrides=override)
    assert state[DesignFormat.NETLIST] == "abcd"


def test_immutable():
    from .state import State
    from .design_format import DesignFormat

    test_dict = {DesignFormat.NETLIST: "abc"}
    state = State(test_dict)
    with pytest.raises(TypeError, match="State is immutable"):
        state[DesignFormat.NETLIST] = "abcd"

    with pytest.raises(TypeError, match="State is immutable"):
        del state[DesignFormat.NETLIST]



def test_to_raw_dict():
    from .state import State
    from .design_format import DesignFormat

    test_dict = {DesignFormat.NETLIST: "abc"}
    metrics = {"metric": "a"}
    state = State(test_dict, metrics=metrics)
    raw_dict = state.to_raw_dict()

    assert isinstance(raw_dict, Dict)
    assert raw_dict["nl"] == "abc"
    assert raw_dict["metrics"]["metric"] == "a"


def test_metrics_access():
    from .state import State

    test_dict = {}
    metrics = {"metric": "a"}
    state = State(test_dict, metrics=metrics)
    assert state.metrics["metric"] == "a"


def test_metrics_mutate():
    from .state import State

    test_dict = {}
    metrics = {"metric": "a"}
    state = State(test_dict, metrics=metrics)
    with pytest.raises(TypeError, match="is immutable"):
        state.metrics["metric"] = "c"

    with pytest.raises(TypeError, match="is immutable"):
        del state.metrics["metric"]

    with pytest.raises(TypeError, match="is immutable"):
        del state.metrics

    with pytest.raises(TypeError, match="is immutable"):
        state.metrics = {"metric": "b"}


