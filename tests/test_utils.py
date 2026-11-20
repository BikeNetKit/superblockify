"""Tests for the utils module."""

from logging import DEBUG
from os.path import exists, join

import osmnx as ox
import pytest
from geopandas import GeoDataFrame
from networkx import Graph, MultiDiGraph
from numpy import array, array_equal, int32, int64, inf, nan, isnan
from osmnx._errors import CacheOnlyInterruptError
from shapely import MultiPolygon, Polygon

from superblockify.config import Config, set_log_level
from superblockify.utils import (
    load_graph_from_place,
    load_graphml_dtypes,
    preprocess_graph,
    has_pairwise_overlap,
    compare_dicts,
    __edge_to_1d,
    __edges_to_1d,
    percentual_increase,
    compare_components_and_partitions,
)


def _load_adliswil_graph():
    """Load the local Adliswil graph and make it suitable as a raw test graph."""
    graph = load_graphml_dtypes(
        join(Config.TEST_DATA_PATH, "cities", "Adliswil.graphml")
    )
    graph.graph["edge_population"] = False
    for _, _, data in graph.edges(data=True):
        data.setdefault("maxspeed", data.get("speed_kph", 30))
    return graph


def _boundary_wgs84(graph):
    """Return the graph boundary as a WGS84 GeoDataFrame."""
    return GeoDataFrame(
        geometry=[graph.graph["boundary"]],
        crs=graph.graph["boundary_crs"],
    ).to_crs("epsg:4326")


def _fake_add_population(graph):
    """Add minimal population attributes without reading a raster."""
    for _, _, data in graph.edges(data=True):
        data["population"] = 0.0
        data["area"] = 1.0
        data["cell_id"] = 0
    graph.graph["edge_population"] = True


def test_preprocess_graph():
    """Test that the preprocess_graph function works."""
    graph = _load_adliswil_graph()
    processed = preprocess_graph(graph.copy(), boundary=_boundary_wgs84(graph))
    assert processed.number_of_nodes() > 0
    assert processed.number_of_edges() > 0
    assert isinstance(processed.graph["boundary"], (MultiPolygon, Polygon))
    for _, _, data in processed.edges(data=True):
        assert "length" in data
        assert "speed_kph" in data
        assert "travel_time" in data


@pytest.mark.parametrize("only_cache", [True, False])
@pytest.mark.parametrize("max_nodes", [None, 100])
def test_load_graph_from_place(tmp_path, monkeypatch, only_cache, max_nodes):
    """Test that the load_graph_from_place function works without network access."""
    graph = _load_adliswil_graph()
    boundary = _boundary_wgs84(graph)

    monkeypatch.setattr("superblockify.utils.add_edge_population", _fake_add_population)
    monkeypatch.setattr(ox, "geocode_to_gdf", lambda *_args, **_kwargs: boundary.copy())

    def fake_graph_from_polygon(*_args, **_kwargs):
        if only_cache:
            raise CacheOnlyInterruptError("Only cache allowed.")
        return graph.copy()

    monkeypatch.setattr(ox, "graph_from_polygon", fake_graph_from_polygon)

    save_as = join(tmp_path, "Adliswil.graphml")
    result = load_graph_from_place(
        save_as,
        "Adliswil, Bezirk Horgen, Zürich, Switzerland",
        add_population=True,
        network_type="drive",
        only_cache=only_cache,
        max_nodes=max_nodes,
    )
    ox.settings.cache_only_mode = False

    if only_cache:
        assert result is None
    else:
        assert result is not None
        assert len(result) > 0
        assert result.size() > 0
        assert isinstance(result.graph["boundary"], (MultiPolygon, Polygon))
        assert exists(save_as)

        # check that every edge has the attribute'length', `speed_kph`,
        # and `travel_time`
        for _, _, data in result.edges(data=True):
            assert "length" in data
            assert "speed_kph" in data
            assert "travel_time" in data


@pytest.mark.parametrize(
    "search_string,expected_by_osmid",
    [
        ("Københavns Kommune, Region Hovedstaden, Danmark", False),
        (
            [
                "Københavns Kommune, Region Hovedstaden, Danmark",
                "Frederiksberg Kommune, Denmark",
            ],
            False,
        ),
        ("R2192363", True),
        (["R2192363", "R2186660"], True),
    ],
)
def test_load_graph_from_place_search_str_types(
    tmp_path, monkeypatch, search_string, expected_by_osmid
):
    """Test that the load_graph_from_place function handles search string types."""
    graph = _load_adliswil_graph()
    boundary = _boundary_wgs84(graph)
    by_osmid = []

    def fake_geocode(*_args, **kwargs):
        by_osmid.append(bool(kwargs.get("by_osmid")))
        return boundary.copy()

    monkeypatch.setattr(ox, "geocode_to_gdf", fake_geocode)
    monkeypatch.setattr(
        ox, "graph_from_polygon", lambda *_args, **_kwargs: graph.copy()
    )

    result = load_graph_from_place(
        save_as=join(tmp_path, "query_test.graphml"),
        search_string=search_string,
        network_type="drive",
    )
    assert result is not None
    assert len(result) > 0
    assert result.size() > 0
    assert isinstance(result.graph["boundary"], (MultiPolygon, Polygon))
    assert by_osmid == [expected_by_osmid]


@pytest.mark.parametrize(
    "lists,expected",
    [
        ([[]], array([[False]])),
        ([[1]], array([[True]])),
        ([[1, 2], [3, 4]], array([[True, False], [False, True]])),
        ([[1], [1]], array([[True, True], [True, True]])),
        ([[], []], array([[False, False], [False, False]])),
        (
            [[1, 2], [3, 4], [5, 6]],
            array([[True, False, False], [False, True, False], [False, False, True]]),
        ),
        (
            [[1], [1], [2]],
            array([[True, True, False], [True, True, False], [False, False, True]]),
        ),
        (
            [[1, 2], [3, 4], [5, 6], [1]],
            array(
                [
                    [True, False, False, True],
                    [False, True, False, False],
                    [False, False, True, False],
                    [True, False, False, True],
                ]
            ),
        ),
        # long list, range
        (
            [list(range(1000)), list(range(1000))],
            array([[True, True], [True, True]]),
        ),
        (
            [list(range(1000)), list(range(1000, 2000))],
            array([[True, False], [False, True]]),
        ),
        (
            [
                list(range(int(1e5))),
                list(range(int(1e5), int(2e5))),
                list(range(int(1.8e5), int(3e5))),
            ],
            array(
                [
                    [True, False, False],
                    [False, True, True],
                    [False, True, True],
                ],
            ),
        ),
    ],
)
@pytest.mark.filterwarnings("ignore:invalid value encountered")
def test_has_pairwise_overlap(lists, expected):
    """Test `_has_pairwise_overlap` by design."""
    # Check if ndarrays are equal
    # pylint: disable=protected-access
    assert array_equal(has_pairwise_overlap(lists), expected)


@pytest.mark.parametrize(
    "lists",
    [
        [],
        False,
        True,
        1,
        1.0,
        "a",
        None,
        array([]),
        array([[]]),
        array([1]),
        [1],
        [1, 2],
        [[1, 2], [3, 4], [5, 6], 1],
        [[1, 2], [3, 4], [5, 6], "a"],
    ],
)
def test_has_pairwise_overlap_exception(lists):
    """Test `_has_pairwise_overlap` exception handling."""
    with pytest.raises(ValueError):
        # pylint: disable=protected-access
        has_pairwise_overlap(lists)


@pytest.mark.parametrize(
    "dict1,dict2,expected",
    [
        ({}, {}, True),
        ({}, {"a": 1}, False),  # missing key
        ({"a": 1}, {}, False),  # missing key
        ({"a": 1}, {"a": 1}, True),
        ({"a": 1}, {"a": 2}, False),  # different value
        ({"a": 1}, {"b": 1}, False),  # different key
        ({"a": 1, "b": 2}, {"a": 1, "b": 2}, True),
        ({"a": 1, "b": 2}, {"a": 1, "b": 3}, False),  # different value
        ({"a": 1, "b": 2}, {"a": 1, "c": 2}, False),  # different key
        ({"a": 1, "b": 2}, {"a": 1, "b": 2, "c": 3}, False),  # missing key
        ({"a": 1, "b": 2, "c": 3}, {"a": 1, "b": 2}, False),  # missing key
        ({(1, 2): 1}, {(1, 2): 1}, True),
        ({(1, 2): 1}, {(1, 2): 2}, False),  # different value
        ({"a": array([1, 2])}, {"a": array([1, 2])}, True),
        ({"a": array([1, 2])}, {"a": array([1, 3])}, False),  # different value
        ({"a": array([])}, {"a": array([])}, True),
        ({"a": array([])}, {"a": array([1])}, False),  # different value
        ({"a": array([1])}, {"a": [1]}, False),  # different type
        ({"a": array([[1, 2], [3, 4]])}, {"a": array([[1, 2], [3, 4]])}, True),
        ({"a": array([[1, 2], [3, 4]])}, {"a": array([[1, 2], [3, 5]])}, False),
        ({"a": array([[1, 2], [3, 4]])}, {"a": array([[1, 2], [3, 4], [5, 6]])}, False),
        # differing types
        ({}, None, False),  # None
        ({}, set(), False),  # set
        ({}, [], False),  # list
        ({}, array([]), False),  # ndarray
        ({}, array([[]]), False),  # ndarray
        ({}, tuple(), False),  # tuple
        # nested dicts
        ({"a": {"b": 1}}, {"a": {"b": 1}}, True),
        ({"a": {"b": 1}}, {"a": {"b": 2}}, False),
        (
            {"a": {"a": [1]}, "b": {"b": array([1])}},
            {"a": {"a": [1]}, "b": {"b": array([1])}},
            True,
        ),
        (
            {"a": {"a": [1]}, "b": {"b": array([1])}, "c": {"c": 1}},
            {"a": {"a": [1]}, "b": {"b": array([1])}},
            False,
        ),
        (
            {"a": {"a": {"a": {"a": array([1])}}}},
            {"a": {"a": {"a": {"a": array([1])}}}},
            True,
        ),
    ],
)
def test_compare_dicts(dict1, dict2, expected):
    """Test `compare_dicts`."""
    assert compare_dicts(dict1, dict2) == expected


@pytest.mark.parametrize(
    "u_idx,v_idx,max_len,expected",
    [
        (0, 0, 1, "00"),
        (0, 1, 1, "01"),
        (1, 0, 1, "10"),
        (1, 1, 1, "11"),
        (0, 0, 2, "000"),
        (12, 34, 2, "1234"),
        (12, 34, 3, "12034"),
        (12, 34, 4, "120034"),
        (789, 12345, 5, "0078912345"),
        (50, 50, 0, "100"),  # unintended use case
        (50, 50, 1, "550"),  # unintended use case
    ],
)
def test___edge_to_1d(u_idx, v_idx, max_len, expected):
    """Test `_edge_to_1d`."""
    assert __edge_to_1d(u_idx, v_idx, max_len) == int(expected)


@pytest.mark.parametrize(
    "u_idx,v_idx,max_len,expected",
    [
        ([0], [0], 1, [0]),
        ([0], [1], 1, [1]),
        ([1, 1], [1, 0], 1, [11, 10]),
        ([12, 9, 8], [34, 7, 6], 2, [1234, 907, 806]),
        ([787, 789], [12345, 12345], 5, [78712345, 78912345]),
    ],
)
def test___edges_to_1d(u_idx, v_idx, max_len, expected):
    """Test `_edges_to_1d`."""
    assert array_equal(
        __edges_to_1d(array(u_idx, dtype=int32), array(v_idx, dtype=int32), max_len),
        array(expected, dtype=int64),
    )


@pytest.mark.parametrize(
    "val_1,val_2,expected",
    [
        (0, 0, 0),
        (0, 1, inf),
        (1, 0, -inf),
        (1, 1, 0),
        (1, 2, 1),
        (2, 1, -1 / 2),
        (2, 2, 0),
        (2, 3, 1 / 2),
        (3, 2, -1 / 3),
        (-1, 1, -2),
        (1, -1, -2),
        (-1, -1, 0),
        (30, 87, 87 / 30 - 1),
        (40, 60, 1 / 2),
        (0, inf, inf),
        (1, inf, inf),
        (-1, inf, -inf),
        (inf, 0, -inf),
        (inf, 1, -inf),
        (inf, -1, -inf),
        (inf, inf, 0),
        (0, -inf, -inf),
        (1, -inf, -inf),
        (-1, -inf, inf),
        (-inf, 0, -inf),
        (-inf, 1, -inf),
        (-inf, -1, -inf),
        (-inf, -inf, 0),
        (inf, -inf, nan),
        (-inf, inf, nan),
    ],
)
def test_percentual_increase(val_1, val_2, expected):
    """Test `percentual_increase` by design."""

    if expected is nan:
        assert isnan(percentual_increase(val_1, val_2))
    else:
        assert pytest.approx(percentual_increase(val_1, val_2), 1e-6) == expected


@pytest.mark.parametrize(
    "list1,list2,expected",
    [
        # equal
        ([], None, True),
        ([{}], None, True),
        ([{}, {}], None, True),
        ([{}, {}, {}], None, True),
        ([{"a": 1}], None, True),
        # graphs
        ([{"a": 1, "graph": Graph()}], None, True),
        ([{"a": 1, "graph": Graph([(1, 2)])}], None, True),
        # isomorphism
        (
            [{"a": 1, "graph": Graph([(1, 2), (2, 3), (3, 4)])}],
            [{"a": 1, "graph": Graph([(4, 3), (3, 2), (2, 1)])}],
            True,
        ),
        (
            [{"a": 1, "graph": Graph([(1, 2), (2, 3), (3, 4)])}],
            [{"a": 1, "graph": Graph(MultiDiGraph([(4, 3), (3, 2), (2, 1)]))}],
            True,
        ),
        # different keys
        ([{"a": 1}], [{"b": 1}], False),
        # different values
        ([{"a": 1}, {"a": 1}], [{"a": 1}, {"a": 2}], False),
        ([{"b": 1}, {"a": 1}], [{"b": 1}, {"a": 2}], False),
        # different length
        ([], [{}], False),
        # different graphs
        (
            [{"a": 1, "graph": Graph([(1, 2)])}],
            [{"a": 1, "graph": Graph([(1, 3), (3, 2)])}],
            False,
        ),
    ],
)
def test_compare_components_and_partitions(list1, list2, expected):
    """Test `compare_components_and_partitions`.
    Compares two lists of dicts, where the dicts need to have the same keys and
    especially checks if the values in the dict are equal or isomorphic if type is
    Graph.
    """
    if list2 is None:
        assert compare_components_and_partitions(list1, list1) is True
    else:
        assert compare_components_and_partitions(list1, list2) == expected


@pytest.mark.parametrize(
    "level",
    [
        10,
        20,
        30,
        40,
        50,
        "DEBUG",
        "INFO",
        "WARNING",
        "ERROR",
        DEBUG,
    ],
)
def test_set_level(level):
    """Test `set_log_level`."""
    set_log_level(level)


@pytest.mark.parametrize("level", ["DEBUG1", ""])
def test_set_level_value_error(level):
    """Test `set_log_level` exception handling."""
    with pytest.raises(ValueError):
        set_log_level(level)


def test_set_level_type_error():
    """Test `set_log_level` exception handling."""
    with pytest.raises(TypeError):
        set_log_level(None)  # type: ignore
